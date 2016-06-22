from flask import render_template, flash, request, make_response, url_for, redirect, session
from . import main
from flask_login import login_required, current_user
from .modules import process_clock, set_clock_form, get_last_clock, get_events_by_date, get_clocked_in_users, \
     process_time_periods
from ..decorators import admin_required
from .forms import AdminFilterEventsForm, UserFilterEventsForm
from datetime import datetime


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
    else:
        if form.note.data is not None and len(form.note.data) > 120:
            flash("Your note cannot exceed 120 characters")

    form = set_clock_form()
    last_event = get_last_clock()

    return render_template('index.html', form=form, last_event=last_event, clocked_in_users=get_clocked_in_users())


@main.route('/all_history',  methods=['GET', 'POST'])
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

    events_query = get_events_by_date(session['email'],
                                      session['first_date'],
                                      session['last_date'],
                                      session['tag_input'])

    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items

    return render_template('history.html', events=events, form=form, pagination=pagination)


@main.route('/download_timesheet', methods=['GET', 'POST'])
def download():
    """
    Created a link to download a timesheet containing the given filtered data.
    :return: A directive to download a file timesheet.txt, which contains timesheet data
    """
    events = request.values
    output = ""
    for event in sorted(events):
        output = output + event + "\n"

    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=timesheet.txt"
    return response


@main.route('/clear_filter', methods=['GET', 'POST'])
def clear():
    session.pop('first_date', None)
    session.pop('last_date', None)
    session.pop('email', None)
    session.pop('tag_input', None)
    return redirect(url_for('main.all_history'))


@main.route('/user_clear_filter', methods=['GET', 'POST'])
def user_clear():
    session.pop('first_date', None)
    session.pop('last_date', None)
    session.pop('email', None)
    session.pop('tag_input', None)
    return redirect(url_for('main.history'))


# FOR TESTING ONLY
@main.route('/dummy_data')
def create_dumb_data():
    from .modules import User, Event
    User.generate_fake(20)
    Event.generate_fake(500)
    return redirect(url_for('main.index'))

