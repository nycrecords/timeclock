from flask import render_template, flash, request, make_response
from datetime import datetime
from .. import db
from ..models import User, Event
from ..email import send_email
from . import main
from flask_login import login_required, current_user
from .modules import process_clock, set_clock_form, get_last_clock, get_events_by_date, get_clocked_in_users, \
     process_time_periods
from ..decorators import admin_required, permission_required
from ..models import Permission
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
    events = Event.query.order_by(sqlalchemy.desc(Event.time)).all()
    if form.validate_on_submit():
        time_period = process_time_periods(form)
        events = get_events_by_date(form.email.data, time_period[0], time_period[1])
    return render_template('all_history.html', events=events, form=form)


@main.route('/download', methods=['GET', 'POST'])
def download():
    events = request.values
    print(events)
    output = ""
    for event in sorted(events):
        output = output + event + "\n"

    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=invoice.txt"
    print(response)
    return response


@main.route('/history', methods=['GET', 'POST'])    # User history
@login_required
def history():
    """
    Shows a user their own history.
    TODO: Make filterable by date.
    :return: An html page that contains user history, sorted (if applicable) with a form for further filtering.
    """
    form = UserFilterEventsForm()
    events = Event.query.order_by(sqlalchemy.desc(Event.time)).all()
    if form.validate_on_submit():
        time_period = process_time_periods(form)
        events = get_events_by_date(current_user.email, time_period[0], time_period[1])
    return render_template('history.html', events=events, form=form)


