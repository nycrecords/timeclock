"""
.. module:: main.views.

   :synopsis: Handles all core URL endpoints for the timeclock application
"""

from flask import (
    render_template,
    flash,
    request,
    make_response,
    url_for,
    redirect,
    session
)
from . import main
from flask_login import login_required, current_user
from .modules import (
    process_clock,
    set_clock_form,
    get_last_clock,
    get_events_by_date,
    get_clocked_in_users,
    get_time_period,
    process_time_periods,
    get_all_tags,
    get_last_clock_type
)
from ..decorators import admin_required
from .forms import AdminFilterEventsForm, UserFilterEventsForm, CreatePayRateForm
from .pdf import (
    generate_header,
    generate_footer,
    generate_employee_info,
    generate_timetable,
    generate_signature_template
)
from datetime import datetime
from flask import current_app
from ..models import Pay, User
from .. import db
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

@main.route('/', methods=['GET', 'POST'])
def index():
    """
    View function for index page. Reroutes to login if user is not logged in.
    :return: index.html contents
    """
    current_app.logger.info('Start function index() [VIEW]')
    if not current_user.is_authenticated:  # Don't pass a form
        current_app.logger.error('Anonymous user visited index. Redirecting to /auth/login...')
        return redirect(url_for('auth.login'))

    if not current_user.validated:
        current_app.logger.info('{} visited index but is not validated. Redirecting to /auth/change_password'.
                                format(current_user.email))
        current_app.logger.info('End function index')
        return redirect(url_for('auth.change_password'))

    form = set_clock_form()
    if form.validate_on_submit():
        if form.note.data is not None and len(form.note.data) > 60:
            flash("Your note cannot exceed 60 characters", category='warning')
            current_app.logger.error('{} submitted a note that exceeded 60 characters'.format(current_user.email))

        else:
            ip = request.environ['REMOTE_ADDR']
            time = datetime.now()

            # Stores the time and the ip clocked in form
            process_clock(form.note.data, ip)
            current_app.logger.info('%s clocked %s at %s' % (
                current_user.email,
                'in' if get_last_clock_type(current_user.id) else 'out',
                time)
            )

    form = set_clock_form()
    last_event = get_last_clock()
    last_clock_event = get_last_clock_type(current_user.id)

    current_app.logger.info('End function index')
    return render_template('index.html',
                           form=form,
                           last_event=last_event,
                           clocked_in_users=get_clocked_in_users(),
                           last_clock_event=last_clock_event
                           )


@main.route('/all_history',  methods=['GET', 'POST'])
@login_required
@admin_required
def all_history():
    """
    View function for url/all_history page.
    Contains a form for sorting by username, start date, and end date.
    :return: All user history, sorted (if applicable) with a form for further
    filtering.
    """
    current_app.logger.info('Start function all_history() [VIEW]')
    if 'first_date' not in session:
        current_app.logger.info('\'first_date\' not found in session. Setting to defaults.')
        session['first_date'] = get_time_period('w')[0]
        session['last_date'] = get_time_period('w')[1]
    if 'email' not in session:
        current_app.logger.info('\'email\' not found in session. Setting to defaults.')
        session['email'] = None
    if 'tag_input' not in session:
        current_app.logger.info('\'tag_input\' not found in session. Setting to defaults.')
        session['tag_input'] = 0

    if request.referrer:
        current_app.logger.info('User is visiting from another page. Setting session[\'email\'] to None')
        session['email'] = None

    form = AdminFilterEventsForm()
    page = request.args.get('page', 1, type=int)

    if form.validate_on_submit():
        time_period = process_time_periods(form)
        session['first_date'] = time_period[0]
        session['last_date'] = time_period[1]
        session['email'] = form.email.data
        session['tag_input'] = form.tag.data
        page = 1

    current_app.logger.info('Querying (calling get_events_by_date)')
    events_query = get_events_by_date()
    current_app.logger.info('Finished querying')

    # Pagination code
    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items

    current_app.logger.info('Querying (calling get_all_tags)')
    tags = get_all_tags()
    current_app.logger.info('Finished querying')

    current_app.logger.info('End function all_history()')
    return render_template('all_history.html',
                           events=events,
                           form=form,
                           pagination=pagination,
                           tags=tags,
                           generation_events=events_query.all()
                           )


@main.route('/history', methods=['GET', 'POST'])    # User history
@login_required
def history():
    """
    Shows a user their own history.
    TODO: Make filterable by date.
    :return: An html page that contains user history, sorted (if applicable)
    with a form for further filtering.
    """
    current_app.logger.info('Start function all_history()')
    if not current_user.validated:
        current_app.logger.info('{} is not validated. Redirecting to /auth/change_password...'
                                .format(current_user.email))
        return redirect(url_for('auth.change_password'))

    session['email'] = current_user.email

    form = UserFilterEventsForm()
    page = request.args.get('page', 1, type=int)
    if form.validate_on_submit():
        time_period = process_time_periods(form)
        session['first_date'] = time_period[0]
        session['last_date'] = time_period[1]
        page = 1
    else:  # Set a default session['first_date'] and ['last_date']
        session['first_date'] = get_time_period('w')[0]
        session['last_date'] = get_time_period('w')[1]

    current_app.logger.info('Querying (calling get_events_by_date)')
    events_query = get_events_by_date()
    current_app.logger.info('Finished querying')

    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items

    current_app.logger.info('Querying (calling get_all_tags)')
    tags = get_all_tags()
    current_app.logger.info('Finished querying')

    return render_template('history.html',
                           events=events,
                           form=form,
                           pagination=pagination,
                           generation_events=events_query.all(),
                           tags=tags)


@main.route('/download_timesheet', methods=['GET', 'POST'])
@login_required
def download():
    """
    Created a link to download a timesheet containing the given filtered data.
    :return: A directive to download a file timesheet.txt, which contains
    timesheet data
    """
    current_app.logger.info('Start function download()')
    errors = []
    if 'email' not in session or session['email'] is None or session['email'] == '':
        # This will only happen for admin searches, so we only need to
        # redirect to the admin page
        current_app.logger.error('User {} tried to generate a timesheet but '
                                 'did not specify a user'
                                 .format(current_user.email)
                                 )
        errors.append('You must specify a user.')
    if (session['last_date']-session['first_date']).days > 8:
        current_app.logger.error('User {} tried to generate a timesheet but '
                                 'exceeded maximum duration (one week)'
                                 .format(current_user.email)
                                 )
        errors.append('Maximum timesheet duration is a week. '
                      'Please refine your filters')
    if errors:
        for error in errors:
            flash(error, 'warning')
        last_page = request.referrer.split('/')[3]
        current_app.logger.error('Errors occurred while generating timesheet (end function download().'
                                 ' Redirecting to {}...'.format(last_page))
        return redirect(url_for('main.' + last_page))

    events = request.form.getlist('event')
    # ^gets event data - we can similarly pass in other data
    # (i.e. time start, oend)

    current_app.logger.info('Beginning to generate timesheet pdf...')
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
    current_app.logger.info('Finished generating timesheet PDF')

    response = make_response(pdf_out)
    response.headers['Content-Disposition'] = \
        "attachment; filename='timesheet.pdf"
    response.mimetype = 'application/pdf'
    current_app.logger.info('%s downloaded timesheet for user %s '
                            'beginning at %s' %
                            (current_user.email,
                             session['email'],
                             session['first_date'].strftime("%b %d, %Y %H:%M:%S %p")
                             )
                            )
    current_app.logger.info('End function download')
    return response


@login_required
@main.route('/clear_filter', methods=['GET', 'POST'])
def clear():
    current_app.logger.info('Start function clear()')
    session.pop('first_date', None)
    session.pop('last_date', None)
    session.pop('email', None)
    session.pop('tag_input', None)
    current_app.logger.info('User %s cleared their admin history filter.' %
                            current_user.email)
    current_app.logger.info('End function clear()')
    return redirect(url_for('main.all_history'))


@login_required
@main.route('/user_clear_filter', methods=['GET', 'POST'])
def user_clear():
    current_app.logger.info('Start function user_clear()')
    session.pop('first_date', None)
    session.pop('last_date', None)
    session.pop('email', None)
    session.pop('tag_input', None)
    current_app.logger.info('User %s cleared their history filter.' %
                            current_user.email)
    current_app.logger.info('End function user_clear()')
    return redirect(url_for('main.history'))


@main.route('/create_payrate', methods=['GET', 'POST'])
@login_required
@admin_required
def pay():
    current_app.logger.info('Start function pay()')
    form = CreatePayRateForm()
    if form.validate_on_submit():
        current_app.logger.info('Querying for user with email {}'.format(form.email.data))
        u = User.query.filter_by(email=form.email.data).first()
        current_app.logger.info('Finished querying for user')
        if not u:
            current_app.logger.error('Tried creating pay for {}. A user with this email does not exist.'.
                                     format(form.email.data))
            flash('No such user exists', category='warning')
        else:
            p = Pay(start=form.start_date.data, end=form.end_date.data, rate=form.rate.data, user=u)
            db.session.add(p)
            db.session.commit()
            current_app.logger.info('Administrator {} created new pay rate for user {}'
                                    .format(current_user.email, u.email))
            flash('Pay rate successfully created', category='success')
    current_app.logger.info('End function pay')
    return render_template('create_payrate.html', form=form, pays=Pay.query.all())




# FOR TESTING ONLY - creates dummy data to propagate database
@main.route('/dummy_data')
def create_dumb_data():
    current_app.logger.info('def create_dumb_date()')
    from ..models import Role, Tag, User, Event
    Role.insert_roles()
    Tag.insert_tags()
    User.generate_fake(20)
    Event.generate_fake(500)
    current_app.logger.info('Someone generated dummy data.')
    return redirect(url_for('main.index'))
