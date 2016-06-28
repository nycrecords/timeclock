from flask import render_template, flash, request, make_response, url_for, redirect, session
from . import main
from flask_login import login_required, current_user
from .modules import process_clock, set_clock_form, get_last_clock, get_events_by_date, get_clocked_in_users, \
     process_time_periods
from ..decorators import admin_required
from .forms import AdminFilterEventsForm, UserFilterEventsForm
from .pdf import generate_header, generate_footer, generate_employee_info, generate_timetable, generate_signature_template
from datetime import datetime
from flask import current_app
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


@main.route('/', methods=['GET', 'POST'])
def index():
    """
    View function for index page. Reroutes to login if user is not logged in.
    :return: index.html contents
    """
    if not current_user.is_authenticated:  # Don't pass a form
        return redirect(url_for('auth.login'))

    if not current_user.validated:
        return redirect(url_for('auth.unconfirmed'))

    form = set_clock_form()
    if form.validate_on_submit():
        process_clock(form.note.data)
        current_app.logger.info(current_user.email + 'clocked ' + 'in' if current_user.clocked_in else 'out')
    else:
        if form.note.data is not None and len(form.note.data) > 120:
            flash("Your note cannot exceed 120 characters")

    form = set_clock_form()
    last_event = get_last_clock()

    return render_template('index.html', form=form, last_event=last_event, clocked_in_users=get_clocked_in_users())


@main.route('/all_history',  methods=['GET', 'POST'])
@login_required
@admin_required
def all_history():
    """
    View function for url/all_history page.
    Contains a form for sorting by username, start date, and end date.
    :return: All user history, sorted (if applicable) with a form for further filtering.
    """
    if 'first_date' not in session:
        session['first_date'] = datetime(2004, 1, 1)
        session['last_date'] = datetime.now()
    if 'email' not in session:
        session['email'] = None
    if 'tag_input' not in session:
        session['tag_input'] = 0

    if request.referrer:
        session['email'] = None

    form = AdminFilterEventsForm()
    page = request.args.get('page', 1, type=int)

    if form.validate_on_submit():
        time_period = process_time_periods(form)
        session['first_date'] = time_period[0]
        session['last_date'] = time_period[1]
        session['email'] = form.email.data
        session['tag_input'] = form.tag.data
        print('form.tag.data', form.tag.data)
        page = 1

    events_query = get_events_by_date(session['email'],
                                      session['first_date'],
                                      session['last_date'],
                                      session['tag_input'])

    # Pagination code
    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items
    # print(events_query)
    return render_template('all_history.html', events=events, form=form, pagination=pagination,
                           generation_events=events)
    # EVENTUALLY MUST SET GENERATION_EVENTS=EVENTS_QUERY.ALL(),
    #  NOT DOING THAT RIGHT NOW TO AVOID OVERHEAD DURING DEVELOPMENT


@main.route('/history', methods=['GET', 'POST'])    # User history
@login_required
def history():
    """
    Shows a user their own history.
    TODO: Make filterable by date.
    :return: An html page that contains user history, sorted (if applicable) with a form for further filtering.
    """
    session['email'] = current_user.email

    if not current_user.validated:
        return redirect(url_for('auth.unconfirmed'))

    form = UserFilterEventsForm()
    page = request.args.get('page', 1, type=int)
    if form.validate_on_submit():
        time_period = process_time_periods(form)
        session['first_date'] = time_period[0]
        session['last_date'] = time_period[1]
        page = 1
    else:                   # Set a default session['first_date'] and ['last_date']
        session['first_date'] = datetime(2004, 1, 1)
        session['last_date'] = datetime.now()

    events_query = get_events_by_date(session['email'],
                                      session['first_date'],
                                      session['last_date'],
                                      None)

    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items

    return render_template('history.html', events=events, form=form, pagination=pagination)


@main.route('/download_timesheet', methods=['GET', 'POST'])
@login_required
def download():
    """
    Created a link to download a timesheet containing the given filtered data.
    :return: A directive to download a file timesheet.txt, which contains timesheet data
    """

    if 'email' not in session or session['email'] is None:
        # This will only happen for admin searches, so we only need to redirect to the admin page
        flash('You must specify a user.')
        return redirect(url_for('main.all_history'))

    events = request.form.getlist('event')
    # ^gets event data - we can similarly pass in other data (i.e. time start, end)
    # output = ""
    # for event in sorted(events):
    #     output = output + event + "\n"
    import io
    output = io.BytesIO()

    c = canvas.Canvas(output, pagesize=letter)
    width, height = letter

    generate_header(c)
    generate_employee_info(c)
    generate_timetable(c, events)
    generate_signature_template(c)
    generate_footer(c)
    c.showPage()
    c.save()
    pdf_out = output.getvalue()
    output.close()
    response = make_response(pdf_out)
    response.headers['Content-Disposition'] = "attachment; filename='timesheet.pdf"
    response.mimetype = 'application/pdf'
    current_app.logger.info(current_user.email + ' downloaded timesheet')  # TODO: Determine if we want to store what info was downloaded
    return response


@login_required
@main.route('/clear_filter', methods=['GET', 'POST'])
def clear():
    session.pop('first_date', None)
    session.pop('last_date', None)
    session.pop('email', None)
    session.pop('tag_input', None)
    return redirect(url_for('main.all_history'))


@login_required
@main.route('/user_clear_filter', methods=['GET', 'POST'])
def user_clear():
    session.pop('first_date', None)
    session.pop('last_date', None)
    session.pop('email', None)
    session.pop('tag_input', None)
    return redirect(url_for('main.history'))


# FOR TESTING ONLY - creates dummy data to propagate database
@main.route('/dummy_data')
def create_dumb_data():
    from ..models import Role, Tag, User, Event
    Role.insert_roles()
    Tag.insert_tags()
    User.generate_fake(20)
    Event.generate_fake(500)
    return redirect(url_for('main.index'))

