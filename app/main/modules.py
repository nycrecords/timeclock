from .. import db
from ..models import User, Event, Tag, Role
from datetime import datetime, timedelta, date
import dateutil.relativedelta
from flask_login import current_user
import sqlalchemy
from flask import session, current_app


def process_clock(note_data, ip=None):
    """
    Creates an Event and writes it to the database when a user clocks in
        or out.
    :param note_data: The note associated with a ClockInForm or ClockOutForm
        [string]
    :param ip: The ip of the user that triggered the function
    :return: None
    """
    current_app.logger.info('Start function process_clock({},{})'.format(note_data, ip))
    current_app.logger.info('Creating new clock event for {}'.format(current_user.email))

    event = Event(type=not get_last_clock_type(user_id=current_user.id),
                  time=datetime.now(),
                  user_id=current_user.id,
                  note=note_data, ip=ip)
    current_app.logger.info('Saving new event to database')
    db.session.add(current_user)  # TODO: do we still need this after eliminating clocked_in from db?
    db.session.add(event)
    db.session.commit()
    current_app.logger.info('Saved new event to database')
    current_app.logger.info('End function process_clock()')


def set_clock_form():
    """
    For use in main/views.py: Determine the type of form to be rendered to index.html.
    :return: ClockInForm if user is clocked out. ClockOutForm if user is clocked in.
    """
    from .forms import ClockInForm, ClockOutForm
    current_app.logger.info('Start function get_clock_form()')
    if is_clocked():
        current_app.logger.info('Setting clock form to: clock out')
        form = ClockOutForm()
    else:
        current_app.logger.info('Setting clock form to: clock in')
        form = ClockInForm()
    current_app.logger.info('End function get_clock_form()')
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
    if event is not None:
        return event.type
    else:
        return None

def get_last_clock():
    """
    Obtains the last clock in or clock out instance created by this user.
    :return: Formatted time of last clock event
    """
    current_app.logger.info('Start function get_last_clock()')
    current_app.logger.info('Querying for last clock of {}'.format(current_user.email))
    try:
        current_app.logger.info('Querying for most recent clock event for user {}'.format(current_user.email))
        if Event.query.filter_by(user_id=current_user.id).first() is not None:
            recent_event = Event.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Event.time)).\
                first().time.strftime("%b %d, %Y | %H:%M")
            current_app.logger.info('Finished querying for most recent clock event')
            current_app.logger.info('End function get_last_clock()')
            return recent_event
        else:
            current_app.logger.info('Failed to find most recent clock event for {}: user probably does not have'
                                    'any clock events yet'.format(current_user.email))
            current_app.logger.info('End function get_last_clock()')

    except:
        current_app.logger.error('EXCEPTION: Failed to query {}\'s last event'.format(current_user.email))
        return None


def get_events_by_date(email=None, first_date_input=None, last_date_input=None, division_input=None):
    """
    Filters the Events table for events granted by an (optional) user from an (optional) begin_date to an (optional)
    end date.

    :return: QUERY of Event objects from a given user between two given dates
    """
    current_app.logger.info('Start function get_events_by_date')
    if 'first_date' not in session:
        current_app.logger.info('First date not in session, setting to defaults')
        session['first_date'] = get_time_period('w')[0]
        session['last_date'] = get_time_period('w')[1]
    first_date = session['first_date']
    last_date = session['last_date']

    if 'tag_input' not in session:
        current_app.logger.info('Tag not in session, setting to defaults')
        session['tag_input'] = 0
    tag_input = session['tag_input']

    if 'division' not in session:
        current_app.logger.info('Tag not in session, setting to defaults')
        session['division'] = None
    division = session['division']

    if 'email' not in session:
        current_app.logger.info('Email not in session, setting to defaults')
        session['email'] = current_user.email
    email_input = session['email']

    # For manual getting events (ignoring session variables)
    if email:
        email_input = email
    if first_date_input:
        first_date = first_date_input
    if last_date_input:
        last_date = last_date_input
    if division_input:
        division = division_input


    current_app.logger.info('Start function get_events_by_date with '
                            'start: {}, end: {}, email: {},tag: {}'
                            .format(session['first_date'], session['last_date'],
                                    session['email'], session['tag_input'], session['division'])
                            )
    # What to do if form date fields are left blank
    # TODO: This is extraneous code. Ensure this is true during code review and then remove - Sarvar
    if first_date is None:
        first_date = get_time_period('w')[0]   # First possible clock-in date
    if last_date is None:
        last_date = get_time_period('w')[1]          # Last possible clock-in date

    current_app.logger.info('Querying for all events between provided dates ({},{})'.
                            format(session['first_date'], session['last_date']))
    events_query = Event.query.filter(
        Event.time >= first_date,
        Event.time <= last_date + timedelta(days=1))
    current_app.logger.info('Finished querying for all events between provided dates')

    # Tag processing - This takes a while
    if tag_input != 0:
        current_app.logger.info('Querying for events with users with given tag: {}'.format(session['tag_input']))
        tag = Tag.query.filter_by(id=tag_input).first()
        users = tag.users.all()
        events_query = events_query.filter(Event.user_id.in_(u.id for u in users))
        current_app.logger.info('Finished querying for events with users with given tag')

    # User processing
    if email_input is not None and User.query.filter_by(email=email_input).first() is not None:
        current_app.logger.info('Querying for events with given user: {}'.format(email_input))
        user_id = User.query.filter_by(email=email_input).first().id
        events_query = events_query.filter(Event.user_id == user_id)
        current_app.logger.info('Finished querying for events with given user.')

    # Eliminate unapproved timepunches
    events_query = events_query.filter_by(approved=True)

    if division:
        current_app.logger.info('Querying for events with users with given division: {}'.format(session['division']))
        events_query = events_query.join(User).filter_by(division=division)
        current_app.logger.info('Finished querying for events with users with given tag')

    current_app.logger.info('Sorting query results be time (desc)')
    events_query = events_query.order_by(sqlalchemy.desc(Event.time))
    current_app.logger.info('Finished sorting query results')
    current_app.logger.info('End function get_events_by_date()')
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
        interval = [today, today]
    elif period == 'w':
        dt = today
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=7)
        interval = [start, end]
    elif period == 'm':
        interval = [first_of_month, today]
    elif period == 'ld':
        yesterday = today + dateutil.relativedelta.relativedelta(days=-1)
        interval = [yesterday, yesterday]
    elif period == 'lw':
        dt = today + timedelta(days=-7)
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)
        interval = [start, end]
    elif period == 'lm':
        interval = [first_of_last_month, end_of_last_month]
    else:
        interval = [today - timedelta(days=today.weekday()), datetime.today() + dateutil.relativedelta.relativedelta(days=1)]
    return interval


def process_time_periods(form):
    """
    Runs through the possible submit buttons on AdminFilterEventsForms and UserFilterEventsForms.
    :param form: AdminFilterEventsForm or UserFilterEventsForm
    :return: A two-element array containing a start and end date
    """
    current_app.logger.info('Start function process_time_periods()')
    if 'first_date' in form:  # This is the case where we have an AdminForm
        current_app.logger.info('Time period is: custom ({} to {})'.
                                format(form.first_date.data, form.last_date.data))
        time_period = [form.first_date.data, form.last_date.data]
    if 'this_day' in form:
        if form.this_day.data:
            current_app.logger.info('Time period is: today')
            time_period = get_time_period('d')
    if 'this_week' in form:
        if form.this_week.data:
            current_app.logger.info('Time period is: this week')
            time_period = get_time_period('w')
    if 'this_month' in form:
        if form.this_month.data:
            current_app.logger.info('Time period is: this month')
            time_period = get_time_period('m')
    if 'last_day' in form:
        if form.last_day.data:
            current_app.logger.info('Time period is: yesterday')
            time_period = get_time_period('ld')
    if 'last_week' in form:
        if form.last_week.data:
            current_app.logger.info('Time period is: last week')
            time_period = get_time_period('lw')
    if 'last_month' in form:
        if form.last_month.data:
            current_app.logger.info('Time period is: last_month')
            time_period = get_time_period('lm')
    current_app.logger.info('End function process_time_periods()')
    return time_period


def get_clocked_in_users():
    """
    :return: An array of all currently clocked in users.
    """
    current_app.logger.info('Start function get_clocked_in_users()')
    current_app.logger.info('Querying for all clocked in users...')
    users = User.query.order_by(User.division).all()
    current_app.logger.info('Finished querying for all clocked in users...')
    clocked_in_users = []
    for user in users:
        event = Event.query.filter_by(user_id=user.id).order_by(sqlalchemy.desc(Event.time)).first()
        if event is not None and event.type is True and user not in clocked_in_users:
            clocked_in_users.append(user)
        else:
            continue
    current_app.logger.info('End function get_clocked_in_users()')
    return clocked_in_users


def get_all_tags():
    """
    Returns all the tags
    :return:
    """
    current_app.logger.info('Start function get_all_tags()')
    current_app.logger.info('Querying for all tags...')
    tags = Tag.query.all()
    current_app.logger.info('Finished querying for all tags...')
    current_app.logger.info('End function get_all_tags()')
    return tags


def get_last_clock_type(user_id=None):
    current_app.logger.info('Start function get_last_clock_type()')
    event = Event.query.filter_by(user_id=user_id).order_by(sqlalchemy.desc(Event.time)).first()
    if event:
        current_app.logger.info('End function get_last_clock_type')
        return event.type
    else:
        current_app.logger.info('End function get_last_clock_type')
        return None


def get_event_by_id(event_id):
    return Event.query.filter_by(id=event_id).first()

def update_user_information(user,
                            first_name_input,
                            last_name_input,
                            division_input,
                            tag_input,
                            supervisor_email_input,
                            role_input):
    """
    To be used in the user_profile view function to update a user's information in the database.
    :param user: The user whose information to update (must be a user object)
    :param first_name_input: New first name for user.
    :param last_name_input: New last name for user.
    :param division_input: New division for user.
    :param tag_input: New tag for user.
    :param supervisor_email: Email of the user's new supervisor.
    :return: None
    """
    current_app.logger.info('Start function update_user_information for {}'.format(user.email))
    if first_name_input and first_name_input != '':
        user.first_name = first_name_input

    if last_name_input and last_name_input != '':
        user.last_name = last_name_input

    if division_input and division_input != '':
        user.division = division_input

    if tag_input:
        user.tag_id = tag_input

    if supervisor_email_input and supervisor_email_input != '':
        sup = User.query.filter_by(email=supervisor_email_input).first()
        user.supervisor = sup

    if role_input:
        user.role = Role.query.filter_by(name=role_input).first()

    db.session.add(user)
    db.session.commit()
    current_app.logger.info('End function update_user_information')
