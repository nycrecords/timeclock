from flask import render_template, flash, request, make_response
from ..models import Event
from . import main
from flask_login import login_required, current_user
from .modules import process_clock, set_clock_form, get_last_clock, get_events_by_date, get_clocked_in_users, \
     process_time_periods
from ..decorators import admin_required
from .forms import AdminFilterEventsForm, UserFilterEventsForm
import sqlalchemy


@main.route('/', methods=['GET', 'POST'])
def index():
    """
    View function for index page.
    :return: index.html contents
    """
    if not current_user.is_authenticated:  # Don't pass a form
        return render_template('index.html')

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
    form = AdminFilterEventsForm()
    events_query = Event.query.order_by(sqlalchemy.desc(Event.time))
    page = request.args.get('page', 1, type=int)
    if form.validate_on_submit():
        time_period = process_time_periods(form)
        events_query = get_events_by_date(form.email.data, time_period[0], time_period[1])
        page = 1

    # Pagination code
    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items
    print(events_query)
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
    form = UserFilterEventsForm()
    events = Event.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Event.time)).all()
    if form.validate_on_submit():
        time_period = process_time_periods(form)
        events = get_events_by_date(current_user.email, time_period[0], time_period[1])
    return render_template('history.html', events=events, form=form)


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


