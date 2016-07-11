from .. import db
from ..models import User, Event, Tag
from datetime import datetime, timedelta, time, date
import dateutil.relativedelta
from flask_login import current_user
import sqlalchemy
from flask import session


def process_clock(note_data, ip=None):
    """
    Creates an Event and writes it to the database when a user clocks in
        or out.
    :param note_data: The note associated with a ClockInForm or ClockOutForm
        [string]
    :return: None
    """

    event = Event(type=not get_last_clock_type(user_id=current_user.id),
                  time=datetime.now(),
                  user_id=current_user.id,
                  note=note_data, ip=ip)
    db.session.add(current_user)
    db.session.add(event)
    db.session.commit()


def set_clock_form():
    from .forms import ClockInForm, ClockOutForm
    """
    For use in main/views.py: Determine the type of form to be rendered to index.html.
    :return: ClockInForm if user is clocked out. ClockOutForm if user is clocked in.
    """
    # User.query.filter_by(user_id)
    if is_clocked():
        form = ClockOutForm()
    else:
        form = ClockInForm()
    return form

def is_clocked(user_id=None):
    '''
    checks if the user is clocked in
    :return: True if the user is clocked in, False if user is clocked out
    '''

    if user_id:
        event = Event.query.filter_by(user_id=user_id).order_by(sqlalchemy.desc(Event.time)).first()
    else:
        event = Event.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Event.time)).first()
    if event != None:
        return event.type
    else:
        return None

def get_last_clock():
    """
    Obtains the last clock in or clock out instance created by this user.
    :return: Formatted time of last clock event
    """
    if Event.query.filter_by(user_id=current_user.id).first() is not None:
        return Event.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Event.time)).first().time.strftime("%b %d, %Y | %H:%M:%S")


def get_events_by_date():
    """
    Filters the Events table for events granted by an (optional) user from an (optional) begin_date to an (optional)
    end date.
    :param email_input: username to search for
    :param first_date: the start date to return queries from
    :param last_date: the end date to query (must be after first date)
    :param tag_input: tag to filter by
    :return: QUERY of Event objects from a given user between two given dates
    """
    if 'first_date' not in session:
        session['first_date'] = get_time_period('w')[0]
        session['last_date'] = get_time_period('w')[1]
    first_date = session['first_date']
    last_date = session['last_date']

    if 'tag_input' not in session:
        session['tag_input'] = 0
    tag_input = session['tag_input']

    if 'email' not in session:
        session['email'] = current_user.email
    email_input = session['email']

    # What to do if form date fields are left blank
    if first_date is None:
        first_date = get_time_period('w')[0]   # First possible clock-in date
    if last_date is None:
        last_date = get_time_period('w')[1]          # Last possible clock-in date

    events_query = Event.query.filter(
        Event.time >= first_date,
        Event.time <= last_date + timedelta(days=1))

    # Tag processing - This takes a while
    if tag_input != 0:
        tag = Tag.query.filter_by(id=tag_input).first()
        users = tag.users.all()
        events_query = events_query.filter(Event.user_id.in_(u.id for u in users))

    # User processing
    if email_input is not None and User.query.filter_by(email=email_input).first() is not None:
        user_id = User.query.filter_by(email=email_input).first().id
        events_query = events_query.filter(Event.user_id == user_id)

    events_query = events_query.order_by(sqlalchemy.desc(Event.time))
    return events_query


def get_time_period(period='d'):
    """
    Get's the start and end date of a given time period.
    :param period: Time periods. Accepted values are:
        d (today)
        w (this week)
        m (this month)
        ld (last day i.e. yesterday)
        lw (last week)
        lm (last month)
    :return: A two-element array containing a start and end date
    """
    today = date.today()
    first_of_month = today.replace(day=1)
    first_of_last_month = first_of_month + dateutil.relativedelta.relativedelta(months=-1)
    end_of_last_month = (first_of_month + dateutil.relativedelta.relativedelta(days=-1))
    if period == 'd':
        return [(today + dateutil.relativedelta.relativedelta(days=-1)), today]
    elif period == 'w':
        dt = today
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=7)
        return [start, end]
    elif period == 'm':
        return [first_of_month, today]
    elif period == 'ld':
        yesterday = today + dateutil.relativedelta.relativedelta(days=-1)
        return [yesterday, yesterday]
    elif period == 'lw':
        dt = today + timedelta(days=-7)
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=7)
        return [start, end]
    elif period == 'lm':
        return [first_of_last_month, end_of_last_month]
    else:
        return [today - timedelta(days=today.weekday()), datetime.today() + dateutil.relativedelta.relativedelta(days=1)]


def process_time_periods(form):
    """
    Runs through the possible submit buttons on AdminFilterEventsForms and UserFilterEventsForms.
    :param form: AdminFilterEventsForm or UserFilterEventsForm
    :return: A two-element array containing a start and end date
    """
    if 'first_date' in form:  # This is the case where we have an AdminForm
        time_period = [form.first_date.data, form.last_date.data]
    if 'this_day' in form:
        if form.this_day.data:
            time_period = get_time_period('d')
    if 'this_week' in form:
        if form.this_week.data:
            time_period = get_time_period('w')
    if 'this_month' in form:
        if form.this_month.data:
            time_period = get_time_period('m')
    if 'last_day' in form:
        if form.last_day.data:
            time_period = get_time_period('ld')
    if 'last_week' in form:
        if form.last_week.data:
            time_period = get_time_period('lw')
    if 'last_month' in form:
        if form.last_month.data:
            time_period = get_time_period('lm')
    return time_period


def get_clocked_in_users():
    """
    :return: An array of all currently clocked in users.
    """
    users = User.query.all()
    clocked_in_users=[]
    for user in users:
        event = Event.query.filter_by(user_id=user.id).order_by(sqlalchemy.desc(Event.time)).first()
        if event is not None and event.type == True and user not in clocked_in_users:
            clocked_in_users.append(user)
        else:
            continue
    return clocked_in_users


def get_all_tags():
    return Tag.query.all()

def get_last_clock_type(user_id=None):
    event = Event.query.filter_by(user_id=user_id).order_by(sqlalchemy.desc(Event.time)).first()
    if event:
        return event.type
    else:
        return None
