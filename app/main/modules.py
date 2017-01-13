from datetime import datetime, timedelta, date

import dateutil.relativedelta
import sqlalchemy
from flask import session, current_app, send_file, make_response
from flask_login import current_user

from .pdf import generate_header, generate_employee_info, generate_timetable, generate_signature_template, \
    generate_footer
from .. import db
from ..email_notification import send_email
from ..models import User, Event, Tag, Role, ChangeLog, Vacation
from ..utils import tags


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

    # Send email if employee has worked for over seven hours
    if get_last_clock() and get_last_clock_type(current_user.id):
        # If the last clock is an IN
        # TODO: ADJUST EMAIL TO PROPER ADMIN EMAIL BEFORE DEPLOYING
        # CURRENT EMAIL IS BRIAN'S FOR QA TESTING
        if (datetime.now() - get_last_clock().time).seconds / float(3600) >= 8:
            send_email('bwaite@records.nyc.gov', 'Overtime - {}'.format(current_user.email),
                       '/main/email/employee_overtime', email=current_user.email)

    # Create clock event
    event = Event(type=not get_last_clock_type(user_id=current_user.id),
                  time=datetime.now(),
                  user_id=current_user.id,
                  note=note_data, ip=ip)
    current_app.logger.info('Saving new event to database')
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
    """
    Checks if the user with given user_id is clocked in.
    :param user_id: id of the user to check for.
    :return: True if the user is clocked in, False if user is clocked out
    """

    if user_id:
        event = Event.query.filter_by(user_id=user_id).order_by(sqlalchemy.desc(Event.time)).first()
    else:
        event = Event.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Event.time)).first()
    if event is not None:
        return event.type
    else:
        return None


# def get_last_clock():
#     """
#     Obtains the last clock in or clock out instance created by this user.
#     :return: Formatted time of last clock event
#     """
#     current_app.logger.info('Start function get_last_clock()')
#     current_app.logger.info('Querying for last clock of {}'.format(current_user.email))
#     try:
#         current_app.logger.info('Querying for most recent clock event for user {}'.format(current_user.email))
#         if Event.query.filter_by(user_id=current_user.id).first() is not None:
#             # If the user has clock events (at least one), find the most recent clock event.
#             recent_event = Event.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Event.time)). \
#                 first().time.strftime("%b %d, %Y | %H:%M")
#             current_app.logger.info('Finished querying for most recent clock event')
#             current_app.logger.info('End function get_last_clock()')
#             return recent_event
#         else:
#             # Because the user has no clock events, we can't search for the most recent one.
#             current_app.logger.info('Failed to find most recent clock event for {}: user probably does not have'
#                                     'any clock events yet'.format(current_user.email))
#             current_app.logger.info('End function get_last_clock()')
#     except:
#         current_app.logger.error('EXCEPTION: Failed to query {}\'s last event'.format(current_user.email))
#         return None


def get_last_clock(user=current_user, time=datetime.now()):
    """
    gets the last valid clock for a user before the given time
    :param user: The user whose clocks to query
    :param time: The time
    :return: The time of the event
    """
    current_app.logger.info('Start function get_last_clock()')
    current_app.logger.info('Querying for last clock of {}'.format(current_user.email))
    try:
        current_app.logger.info('Querying for most recent clock event for user {}'.format(current_user.email))
        if Event.query.filter_by(user_id=user.id).first() is not None:
            # If the user has clock events (at least one), find the most recent clock event.
            recent_event = Event.query.filter_by(user_id=user.id). \
                filter_by(approved=True). \
                filter(Event.time <= time).order_by(
                sqlalchemy.desc(Event.time)). \
                first()
            current_app.logger.info('Finished querying for most recent clock event')
            current_app.logger.info('End function get_last_clock()')
            return recent_event
        else:
            # Because the user has no clock events, we can't search for the most recent one.
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

    # Ensure session variables exist
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

    if email_input and email_input.find('@') == -1:
        # If the email input by the user does not contain the @records.nyc.gov portion, add it in
        email_input += '@records.nyc.gov'

    # Insert parameters into this function to manually search for events, disregarding session variables
    # This is used when querying for timepunches for supervisor review
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
        if tag:
            users = tag.users.all()
            events_query = events_query.filter(Event.user_id.in_(u.id for u in users))
        current_app.logger.info('Finished querying for events with users with given tag')

    # User processing
    if email_input is not None:
        if User.query.filter_by(email=email_input).first() is not None:
            current_app.logger.info('Querying for events with given user: {}'.format(email_input))
            user_id = User.query.filter_by(email=email_input).first().id
            events_query = events_query.filter(Event.user_id == user_id)
            current_app.logger.info('Finished querying for events with given user.')
        elif email_input != '':
            # The user doesn't exist, so set events_query to something we know
            # will return an empty query.
            events_query = events_query.filter(Event.user_id == -1)

    # Eliminate unapproved timepunches to avoid showing them in the history pages and rendering them in Timesheets
    # and invoices
    events_query = events_query.filter_by(approved=True)

    # Division processing
    if division:
        current_app.logger.info('Querying for events with users with given division: {}'.format(session['division']))
        events_query = events_query.join(User).filter_by(division=division)
        current_app.logger.info(
            'Finished querying for events with users with given tag: {}'.format(session['tag_input']))

    current_app.logger.info('Sorting query results by time (desc)')
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
        # Set the default interval to this week
        interval = [today - timedelta(days=today.weekday()),
                    datetime.today() + dateutil.relativedelta.relativedelta(days=1)]
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
    Obtains a list of clocked in users.
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
    current_app.logger.info('End function get_clocked_in_users()')
    return clocked_in_users


def get_all_tags():
    """
    Fetches all the tags in the database.
    :return: A list of all tags.
    """
    current_app.logger.info('Start function get_all_tags()')
    current_app.logger.info('Querying for all tags...')
    tags = Tag.query.all()
    current_app.logger.info('Finished querying for all tags...')
    current_app.logger.info('End function get_all_tags()')
    return tags


def get_last_clock_type(user_id=None):
    """
    Obtains the type of a user's last clock.
    :param user_id: The id of the user whose clocks are being queried.
    :return: [Boolean] Type of user's last clock (True for IN, False for OUT)
    """
    current_app.logger.info('Start function get_last_clock_type()')
    event = Event.query.filter_by(user_id=user_id).order_by(sqlalchemy.desc(Event.time)).first()
    if event:
        current_app.logger.info('End function get_last_clock_type')
        return event.type
    else:
        current_app.logger.info('End function get_last_clock_type')
        return None


def get_event_by_id(event_id):
    """
    Obtains an event by its id.
    :param event_id: The id of the event to fetch.
    :return: [Event] An Event object.
    """
    return Event.query.filter_by(id=event_id).first()


def get_vacation_by_id(vac_id):
    """
    Obtains an event by its id.
    :param event_id: The id of the event to fetch.
    :return: [Event] An Event object.
    """
    return Vacation.query.filter_by(id=vac_id).first()


def update_user_information(user,
                            first_name_input,
                            last_name_input,
                            division_input,
                            tag_input,
                            supervisor_email_input,
                            is_supervisor_input,
                            role_input,
                            budget_code_input,
                            object_code_input,
                            object_name_input
                            ):
    """
    To be used in the user_profile view function to update a user's information in the database.
    :param user: The user whose information to update (must be a user object)
    :param first_name_input: New first name for user.
    :param last_name_input: New last name for user.
    :param division_input: New division for user.
    :param tag_input: New tag for user.
    :param supervisor_email_input: Email of the user's new supervisor.
    :param is_supervisor_input: Whether or not the user is a supervisor
    :return: None
    """
    current_app.logger.info('Start function update_user_information for {}'.format(user.email))
    if first_name_input and first_name_input != '' and (user.first_name != first_name_input):
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='FIRST NAME',
                           old=user.first_name,
                           new=first_name_input)
        db.session.add(change)
        db.session.commit()
        user.first_name = first_name_input

    if last_name_input and last_name_input != '' and (user.last_name != last_name_input):
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='LAST NAME',
                           old=user.last_name,
                           new=last_name_input)
        db.session.add(change)
        db.session.commit()
        user.last_name = last_name_input

    if division_input and division_input != '' and (user.division != division_input):
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='DIVISION',
                           old=user.division,
                           new=division_input)
        db.session.add(change)
        db.session.commit()
        user.division = division_input

    if tag_input and user.tag_id != tag_input:
        if user.tag_id:
            old_tag = tags[user.tag_id][1]
        else:
            old_tag = 'None'
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='TAG_INPUT',
                           old=old_tag,
                           new=tags[tag_input][1])
        db.session.add(change)
        db.session.commit()
        user.tag_id = tag_input

    if supervisor_email_input and supervisor_email_input != '' and user.supervisor.email != supervisor_email_input:
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='SUPERVISOR',
                           old=user.supervisor.email,
                           new=supervisor_email_input)
        db.session.add(change)
        db.session.commit()
        sup = User.query.filter_by(email=supervisor_email_input).first()
        user.supervisor = sup

    if is_supervisor_input and (user.is_supervisor != is_supervisor_input):
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='IS SUPERVISOR',
                           old=user.is_supervisor,
                           new=is_supervisor_input)
        db.session.add(change)
        db.session.commit()
        user.is_supervisor = is_supervisor_input

    if budget_code_input and budget_code_input != '' and user.budget_code != budget_code_input:
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='BUDGET CODE',
                           old=user.budget_code,
                           new=budget_code_input)
        db.session.add(change)
        db.session.commit()
        user.budget_code = budget_code_input

    if object_code_input and object_code_input != '' and user.object_code != object_code_input:
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='OBJECT CODE',
                           old=user.object_code,
                           new=object_code_input)
        db.session.add(change)
        db.session.commit()
        user.object_code = object_code_input

    if object_name_input and object_name_input != '' and user.object_name != object_name_input:
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='OBJECT NAME',
                           old=user.object_name,
                           new=object_name_input)
        db.session.add(change)
        db.session.commit()
        user.object_name = object_name_input

    if role_input:
        new_role = Role.query.filter_by(name=role_input).first()
        if user.role != new_role:
            change = ChangeLog(changer_id=current_user.id,
                               user_id=user.id,
                               timestamp=datetime.now(),
                               category='ROLE',
                               old=user.role.name,
                               new=role_input)
            db.session.add(change)
            db.session.commit()
            user.role = Role.query.filter_by(name=role_input).first()

    db.session.add(user)
    db.session.commit()
    current_app.logger.info('End function update_user_information')


def get_changelog_by_user_id(id):
    """
    Obtains a changelog based on a user's id.
    :param id: The id of the user whose changelog is being queried for.
    :return: [BaseQuery] A ChangeLog query. We return a query to leverage the pagination macro.
    """
    current_app.logger.info('Start function get_changelog_by_user_id()')
    current_app.logger.info('Querying for changes made to user with id {}'.format(id))
    changes = ChangeLog.query.filter_by(user_id=id).order_by(sqlalchemy.desc(ChangeLog.timestamp))
    current_app.logger.info('End function get_changelog_by_user_id()')
    return changes


def check_total_clock_count(events):
    """
    Calculates the amount of clock-ins and clock-outs from a list of clock events and makes sure that each clock in
    has a matching clock out
    :param events: list containing clock-ins and clock-outs events
    :return: True if there are matching clock outs for each clock in, otherwise False
    """
    current_app.logger.info('Start function check_total_clock_count()')
    clock_in_list = []
    clock_out_list = []
    # loop through all events and count the number of clock-ins and clock-outs in separate lists
    for event in events:
        if 'OUT' in event:
            clock_out_list.append(event)
        elif 'IN' in event:
            clock_in_list.append(event)
        else:
            continue
    if len(clock_out_list) == len(clock_in_list):
        return True
    else:
        return False


def add_event(user_id, time, type):
    """
    Adds an event to the database
    :param user_id: The user id to be associated with the event
    :param time: Time of the event
    :param type: The type of the event: True is a clock in, False is a clock out [boolean]
    :return: None
    """
    e = Event(type=type, user_id=user_id, time=time)
    db.session.add(e)
    db.session.commit()
    current_app.logger.info(
        '{} added clock event with id {} for user with id {}'.format(current_user.email, e.id, user_id))


def delete_event(event_id):
    """
    Removes an event from the database
    :param event_id: The id of the event to be removes
    :return: None
    """
    e = Event.query.filter_by(id=event_id).first()
    current_app.logger.info(
        '{} deleted clock event with id {} for user with id {}'.format(current_user.email, e.id, e.user.id))
    db.session.delete(e)
    db.session.commit()


# This breaks very very badly when there are too many clock events in the period, and doesn't create new pages
def generate_timesheet(events):
    """
    Creates a Bytes object timesheet
    :param events: List of events to be included in the timesheet
    :return: Timesheet (as a Bytes obj)
    """
    current_app.logger.info('Beginning to generate timesheet pdf...')
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    import io
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)

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
    return pdf_out


def generate_timesheets(emails, start, end):
    """
    Creates a zipfile that contains individual timesheets for each email between the start and end dates.
    :param emails: List of users' emails
    :param start: Start date for timesheet [datetime]
    :param end: End date for timesheet [datetime]
    :return: Response containing a zipfile
    """
    import tempfile
    import os
    import io
    import shutil
    import zipfile
    dirpath = tempfile.mkdtemp(dir=os.path.dirname(os.path.realpath(__file__)))
    for email in emails:
        events = get_events_by_date(email, start, end).all()
        output_file_name = email
        f = open(dirpath + '/' + output_file_name + '.pdf', 'wb')
        output = generate_timesheet(events)
        f.write(output)
        f.close()
    memoryfile = io.BytesIO()
    with zipfile.ZipFile(memoryfile, 'w') as zip:
        for root, dirs, files in os.walk(dirpath + '/'):
            for file in files:
                zip.write(dirpath + '/' + file, arcname=file)
    memoryfile.seek(0)
    shutil.rmtree(dirpath)
    return send_file(memoryfile,
                     mimetype='zip',
                     attachment_filename='timesheets.zip',
                     as_attachment=True)


def create_csv():
    """
    Creates a csv file that contains all of the event data in the database
    :return: CSV file
    """
    import csv
    import io
    si = io.StringIO()
    writer = csv.writer(si)
    events = Event.query.order_by(sqlalchemy.desc(Event.time)).all()
    writer.writerow(['id', 'email', 'first name', 'last name', 'time', 'note', 'ip'])
    for event in events:
        writer.writerow([event.id, event.user.email, event.user.first_name, event.user.last_name,
                         event.time.strftime("%b %d, %Y %H:%M"), event.note, event.ip])
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output
