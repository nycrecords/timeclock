from datetime import datetime, timedelta, date
from dateutil.relativedelta import *
import dateutil.relativedelta
import sqlalchemy
from flask import session, current_app, send_file, make_response
from flask_login import current_user

from .pdf import (
    generate_header,
    generate_employee_info,
    generate_timetable,
    generate_signature_template,
    generate_footer,
    generate_health_screen_confirmation,
)
from .. import db
from ..email_notification import send_email, send_health_screen_confirmation_email
from ..models import User, Event, Tag, Vacation
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pytz import timezone


def process_clock(note_data, ip=None):
    """
    Creates an Event and writes it to the database when a user clocks in
        or out.
    :param note_data: The note associated with a ClockInForm or ClockOutForm
        [string]
    :param ip: The ip of the user that triggered the function
    :return: None
    """
    current_app.logger.info("Start function process_clock({},{})".format(note_data, ip))
    current_app.logger.info(
        "Creating new clock event for {}".format(current_user.email)
    )

    last = get_last_clock()
    # Send email if employee has worked for over seven hours
    if last and last.type:
        # If the last clock is an IN
        # TODO: ADJUST EMAIL TO PROPER ADMIN EMAIL BEFORE DEPLOYING
        # CURRENT EMAIL IS BRIAN'S FOR QA TESTING
        if (datetime.now() - get_last_clock().time).seconds / float(3600) >= 8:
            send_email(
                "bwaite@records.nyc.gov",
                "Overtime - {}".format(current_user.email),
                "/main/email/employee_overtime",
                email=current_user.email,
            )

    # Create clock event
    typ = True if not last else not last.type
    event = Event(
        type=typ, time=datetime.now(), user_id=current_user.id, note=note_data, ip=ip
    )
    current_app.logger.info("Saving new event to database")
    db.session.add(event)
    db.session.commit()
    current_app.logger.info("Saved new event to database")
    current_app.logger.info("End function process_clock()")


def set_clock_form():
    """
    For use in main/views.py: Determine the type of form to be rendered to index.html.
    :return: ClockInForm if user is clocked out. ClockOutForm if user is clocked in.
    """
    from .forms import ClockInForm, ClockOutForm

    current_app.logger.info("Start function get_clock_form()")
    last = get_last_clock()
    if last and last.type:
        current_app.logger.info("Setting clock form to: clock out")
        form = ClockOutForm()
    else:
        current_app.logger.info("Setting clock form to: clock in")
        form = ClockInForm()
    current_app.logger.info("End function get_clock_form()")
    return form


def get_last_clock(user=current_user, time=None):
    """
    gets the last valid clock for a user before the given time
    :param user: The user whose clocks to query
    :param time: The time
    :return: The time of the event
    """
    current_app.logger.info("Start function get_last_clock()")
    current_app.logger.info("Querying for last clock of {}".format(current_user.email))
    try:
        current_app.logger.info(
            "Querying for most recent clock event for user {}".format(
                current_user.email
            )
        )
        if Event.query.filter_by(user_id=user.id).first() is not None:
            # If the user has clock events (at least one), find the most recent clock event.
            recent_query = (
                Event.query.filter_by(user_id=user.id)
                .filter_by(approved=True)
                .order_by(sqlalchemy.desc(Event.time))
            )
            if time:
                recent_query = recent_query.filter(Event.time <= time)
            recent_event = recent_query.first()
            current_app.logger.info("Finished querying for most recent clock event")
            current_app.logger.info("End function get_last_clock()")
            return recent_event
        else:
            # Because the user has no clock events, we can't search for the most recent one.
            current_app.logger.info(
                "Failed to find most recent clock event for {}: user probably does not have"
                "any clock events yet".format(current_user.email)
            )
            current_app.logger.info("End function get_last_clock()")
    except:
        current_app.logger.error(
            "EXCEPTION: Failed to query {}'s last event".format(current_user.email)
        )
        return None


def get_events_by_date(
    email=None, first_date_input=None, last_date_input=None, division_input=None
):
    """
    Filters the Events table for events granted by an (optional) user from an (optional) begin_date to an (optional)
    end date.

    :return: QUERY of Event objects from a given user between two given dates
    """
    current_app.logger.info("Start function get_events_by_date")

    # Ensure session variables exist
    if "first_date" not in session:
        current_app.logger.info("First date not in session, setting to defaults")
        session["first_date"] = get_time_period("w")[0]
        session["last_date"] = get_time_period("w")[1]
    first_date = session["first_date"]
    last_date = session["last_date"]

    if "tag_input" not in session:
        current_app.logger.info("Tag not in session, setting to defaults")
        session["tag_input"] = 0
    tag_input = session["tag_input"]

    if "division" not in session:
        current_app.logger.info("Tag not in session, setting to defaults")
        session["division"] = None
    division = session["division"]

    if "email" not in session:
        current_app.logger.info("Email not in session, setting to defaults")
        session["email"] = current_user.email
    email_input = session["email"]

    if email_input and email_input.find("@") == -1:
        # If the email input by the user does not contain the @records.nyc.gov portion, add it in
        email_input += "@records.nyc.gov"

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

    current_app.logger.info(
        "Start function get_events_by_date with "
        "start: {}, end: {}, email: {},tag: {}".format(
            session["first_date"],
            session["last_date"],
            session["email"],
            session["tag_input"],
            session["division"],
        )
    )

    current_app.logger.info(
        "Querying for all events between provided dates ({},{})".format(
            session["first_date"], session["last_date"]
        )
    )
    events_query = Event.query.filter(
        Event.time >= first_date, Event.time <= last_date + timedelta(days=1)
    )
    current_app.logger.info("Finished querying for all events between provided dates")

    # Tag processing - This takes a while
    if tag_input != 0:
        current_app.logger.info(
            "Querying for events with users with given tag: {}".format(
                session["tag_input"]
            )
        )
        tag = Tag.query.filter_by(id=tag_input).first()
        if tag:
            users = tag.users.all()
            events_query = events_query.filter(Event.user_id.in_(u.id for u in users))
        current_app.logger.info(
            "Finished querying for events with users with given tag"
        )

    # User processing
    if email_input is not None:
        if User.query.filter_by(email=email_input.lower()).first() is not None:
            current_app.logger.info(
                "Querying for events with given user: {}".format(email_input)
            )
            user_id = User.query.filter_by(email=email_input.lower()).first().id
            events_query = events_query.filter(Event.user_id == user_id)
            current_app.logger.info("Finished querying for events with given user.")
        elif email_input != "":
            # The user doesn't exist, so set events_query to something we know
            # will return an empty query.
            events_query = events_query.filter(Event.user_id == -1)

    # Eliminate unapproved timepunches to avoid showing them in the history pages and rendering them in Timesheets
    # and invoices
    events_query = events_query.filter_by(approved=True)

    # Division processing
    if division:
        current_app.logger.info(
            "Querying for events with users with given division: {}".format(
                session["division"]
            )
        )
        events_query = events_query.join(User).filter_by(division=division)
        current_app.logger.info(
            "Finished querying for events with users with given tag: {}".format(
                session["tag_input"]
            )
        )

    current_app.logger.info("Sorting query results by time (desc)")
    events_query = events_query.order_by(sqlalchemy.desc(Event.time))
    current_app.logger.info("Finished sorting query results")
    current_app.logger.info("End function get_events_by_date()")
    return events_query


def get_time_period(period="d"):
    """
    Get's the start and end date of a given time period.
    :param period: Time periods. Accepted values are:
        d (today)
        w (this week)
        m (this month)
        ld (last day i.e. yesterday)
        lw (last week)
        l2w (last 2 weeks i.e last week and the week before)
        lm (last month)
    :return: A two-element array containing a start and end date
    """
    today = date.today()
    first_of_month = today.replace(day=1)
    first_of_last_month = first_of_month + dateutil.relativedelta.relativedelta(
        months=-1
    )
    end_of_last_month = first_of_month + dateutil.relativedelta.relativedelta(days=-1)
    if period == "d":
        interval = [today, today]
    elif period == "w":
        dt = today
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=7)
        interval = [start, end]
    elif period == "m":
        interval = [first_of_month, today]
    elif period == "ld":
        yesterday = today + dateutil.relativedelta.relativedelta(days=-1)
        interval = [yesterday, yesterday]
    elif period == "lw":
        dt = today + timedelta(days=-7)
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=6)
        interval = [start, end]
    elif period == "l2w":
        dt = today + relativedelta(weeks=-2)
        start = dt - timedelta(days=dt.weekday())
        end = start + timedelta(days=13)
        interval = [start, end]
    elif period == "lm":
        interval = [first_of_last_month, end_of_last_month]
    else:
        # Set the default interval to this week
        interval = [
            today - timedelta(days=today.weekday()),
            datetime.today() + dateutil.relativedelta.relativedelta(days=1),
        ]
    return interval


def process_time_periods(form):
    """
    Runs through the possible submit buttons on AdminFilterEventsForms and UserFilterEventsForms.
    :param form: AdminFilterEventsForm or UserFilterEventsForm
    :return: A two-element array containing a start and end date
    """
    current_app.logger.info("Start function process_time_periods()")
    if "first_date" in form:  # This is the case where we have an AdminForm
        current_app.logger.info(
            "Time period is: custom ({} to {})".format(
                form.first_date.data, form.last_date.data
            )
        )
        time_period = [form.first_date.data, form.last_date.data]
    if "this_day" in form:
        if form.this_day.data:
            current_app.logger.info("Time period is: today")
            time_period = get_time_period("d")
    if "this_week" in form:
        if form.this_week.data:
            current_app.logger.info("Time period is: this week")
            time_period = get_time_period("w")
    if "this_month" in form:
        if form.this_month.data:
            current_app.logger.info("Time period is: this month")
            time_period = get_time_period("m")
    if "last_day" in form:
        if form.last_day.data:
            current_app.logger.info("Time period is: yesterday")
            time_period = get_time_period("ld")
    if "last_week" in form:
        if form.last_week.data:
            current_app.logger.info("Time period is: last week")
            time_period = get_time_period("lw")
    if "last_2weeks" in form:
        if form.last_2weeks.data:
            current_app.logger.info("Time period is: last 2 weeks")
            time_period = get_time_period("l2w")
    if "last_month" in form:
        if form.last_month.data:
            current_app.logger.info("Time period is: last_month")
            time_period = get_time_period("lm")
    current_app.logger.info("End function process_time_periods()")
    return time_period


def get_clocked_in_users():
    """
    Obtains a list of clocked in users.
    :return: An array of all currently clocked in users.
    """
    current_app.logger.info("Start function get_clocked_in_users()")
    current_app.logger.info("Querying for all clocked in users...")
    users = User.query.order_by(User.division).all()
    current_app.logger.info("Finished querying for all clocked in users...")
    today = datetime.now(timezone("America/New_York"))
    clocked_in_users = []
    clocked_in_users_today = []
    for user in users:
        event = (
            Event.query.filter_by(user_id=user.id, approved=True)
            .order_by(sqlalchemy.desc(Event.time))
            .first()
        )
        if event is not None and event.type is True and user not in clocked_in_users:
            clocked_in_users.append(user)
            if event.time.date() == today.date():
                clocked_in_users_today.append(user)
    current_app.logger.info("End function get_clocked_in_users()")
    return clocked_in_users, clocked_in_users_today


def get_all_tags():
    """
    Fetches all the tags in the database.
    :return: A list of all tags.
    """
    current_app.logger.info("Start function get_all_tags()")
    current_app.logger.info("Querying for all tags...")
    tags = Tag.query.all()
    current_app.logger.info("Finished querying for all tags...")
    current_app.logger.info("End function get_all_tags()")
    return tags


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


def check_total_clock_count(events):
    """
    Calculates the amount of clock-ins and clock-outs from a list of clock events and makes sure that each clock in
    has a matching clock out
    :param events: list containing clock-ins and clock-outs events
    :return: True if there are matching clock outs for each clock in, otherwise False
    """
    current_app.logger.info("Start function check_total_clock_count()")
    if len(events) % 2 != 0:
        return False
    # Each clock in must have corresponding clock out i.e There should be no two consecutive ones of the same type.
    last_type_clock = "IN"
    for event in events:
        event = str(event)
        if last_type_clock in event:
            return False
        elif last_type_clock == "OUT":
            last_type_clock = "IN"
        else:
            last_type_clock = "OUT"
    return True


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
        "{} added clock event with id {} for user with id {}".format(
            current_user.email, e.id, user_id
        )
    )


def delete_event(event_id):
    """
    Removes an event from the database
    :param event_id: The id of the event to be removes
    :return: None
    """
    e = Event.query.filter_by(id=event_id).first()
    current_app.logger.info(
        "{} deleted clock event with id {} for user with id {}".format(
            current_user.email, e.id, e.user.id
        )
    )
    db.session.delete(e)
    db.session.commit()


# This breaks very very badly when there are too many clock events in the period, and doesn't create new pages
def generate_timesheet(events):
    """
    Creates a Bytes object timesheet
    :param events: List of events to be included in the timesheet
    :return: Timesheet (as a Bytes obj)
    """
    current_app.logger.info("Beginning to generate timesheet pdf...")
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
    current_app.logger.info("Finished generating timesheet PDF")
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
        f = open(dirpath + "/" + output_file_name + ".pdf", "wb")
        output = generate_timesheet(events)
        f.write(output)
        f.close()
    memoryfile = io.BytesIO()
    with zipfile.ZipFile(memoryfile, "w") as zip:
        for root, dirs, files in os.walk(dirpath + "/"):
            for file in files:
                zip.write(dirpath + "/" + file, arcname=file)
    memoryfile.seek(0)
    shutil.rmtree(dirpath)
    return send_file(
        memoryfile,
        mimetype="zip",
        attachment_filename="timesheets.zip",
        as_attachment=True,
    )


def create_csv(events=None):
    """
    Creates a csv file that contains all of the event data in the database
    :return: CSV file
    """
    import csv
    import io

    si = io.StringIO()
    writer = csv.writer(si)
    if not events:
        events = Event.query.order_by(sqlalchemy.desc(Event.time)).all()
    writer.writerow(
        ["id", "email", "first name", "last name", "time", "type", "note", "ip"]
    )
    for event in events:
        writer.writerow(
            [
                event.id,
                event.user.email,
                event.user.first_name,
                event.user.last_name,
                event.time.strftime("%b %d, %Y %H:%M"),
                "IN" if event.type else "OUT",
                event.note,
                event.ip,
            ]
        )
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


def process_health_screen_confirmation(
    name, email, division, date, questionnaire_confirmation, report_to_work
):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    generate_health_screen_confirmation(
        c, name, division, date, questionnaire_confirmation, report_to_work
    )
    c.save()
    pdf = buffer.getvalue()
    buffer.close()

    filename = "{username}-health-check-report_to_work-{report_to_work}-{date}.pdf".format(
        username=email.split("@")[0],
        report_to_work=report_to_work.lower(),
        date=datetime.strptime(date, "%m/%d/%Y").strftime("%Y-%m-%d"),
    )
    send_health_screen_confirmation_email(
        ["healthcheck@records.nyc.gov"],
        [email],
        "(Report to Work: {report_to_work} - {date}) Health Screening Confirmation - {name}".format(report_to_work=report_to_work, date=date, name=name),
        filename,
        pdf,
        name,
    )
