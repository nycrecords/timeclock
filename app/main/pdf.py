"""
For generating timesheet pdf with appropriate styling.
"""
from flask import session, flash
from flask_login import current_user
from datetime import datetime, timedelta
from ..models import User
from .modules import get_day_of_week

from reportlab.lib.pagesizes import letter
width, length = letter


def set_defaults(canvas_field):
    """
    Sets timesheet defaults.
    :param canvas_field: The canvas whose styles will be modified.
    :return: None
    """
    canvas_field.setFont('Courier', 12)


def generate_header(canvas_field):
    """
    Creates the footer for timesheet form.
    :param canvas_field: The canvas to add the header to.
    :return: None
    """
    canvas_field.setFont('Courier', 8)
    canvas_field.drawString(25, length-30, 'The City of New York - DORIS')
    canvas_field.drawString(470, 20, datetime.now().strftime("%b %d, %Y %l:%M:%S %p"))
    canvas_field.line(25, 30, width - 25, 30)


def generate_employee_info(canvas_field):
    """
    Generates portion of pdf that contains employee information.
    :param canvas_field: The canvas to add the employee information to.
    :return:None.
    """
    if session['email'] is None or session['email'] == '':
        u = User.query.filter_by(email=current_user.email).first()
    else:
        u = User.query.filter_by(email=session['email']).first()

    first_date = session['first_date']
    last_date = session['last_date']
    if (last_date-first_date).days > 7:
        last_date = first_date + timedelta(days=7)
        flash('Max date range for a timesheet is one week. Timesheet generated from ' +
              first_date.strftime("%b %d, %Y %l:%M:%S %p") + ' to ' + last_date.strftime("%b %d, %Y %l:%M:%S %p"))

    print(session['email'])
    canvas_field.setFont('Courier', 10)
    canvas_field.drawString(25, length - 60, 'Employee Name: ' + u.first_name + ' ' + u.last_name)
    canvas_field.drawString(25, length - 80, 'Position: ' + (u.tag.name if u.tag else "None"))
    canvas_field.drawString(300, length - 60, 'From: ' + first_date.strftime("%b %d, %Y %l:%M:%S %p"))
    canvas_field.drawString(300, length - 80, 'To:   ' + last_date.strftime("%b %d, %Y %l:%M:%S %p"))


def generate_timetable(canvas_field, events):
    """
    Generates timetable for a week for a given user.
    :param canvas_field: The canvas to add the timetable to.
    :param events: Events to write to the timetable.
    :return: None.
    """
    timetable_top = length - 150  # Top of the time_table area
    PADDING = 10
    index = 1
    total_hours = 0

    canvas_field.drawString(50, timetable_top, 'DATE')
    canvas_field.drawString(150, timetable_top,  'TIME IN')
    canvas_field.drawString(250, timetable_top, 'TIME OUT')
    canvas_field.drawString(330, timetable_top, 'HOURS')
    canvas_field.drawString(390, timetable_top, 'NOTE IN')
    canvas_field.drawString(450, timetable_top, 'NOTE OUT')

    events = sorted(events)
    if not len(events) % 2 == 0:
        events.pop()

    for x in range(0, len(events), 2):
        event = events[x]
        next_event = events[x + 1]
        canvas_field.setFont('Courier', 8)
        time_in = event[:event.index('|') - 1]
        event = event[(event.index('|') + 2):]
        name = event[:event.index('|')]
        event = event[(event.index('|') + 2):]
        note_in = event[(event.index('|') + 2):]

        time_out = next_event[:next_event.index('|') - 1]
        next_event = next_event[(next_event.index('|') + 2):]
        next_event = next_event[(next_event.index('|') + 2):]
        note_out = next_event[next_event.index('|') + 2:]

        time_in_datetime = datetime.strptime(time_in, "%b %d, %Y %H:%M:%S %p")
        time_out_datetime = datetime.strptime(time_out, "%b %d, %Y %H:%M:%S %p")

        date = get_day_of_week(time_in_datetime)[:3]
        print(time_out_datetime, time_in_datetime)
        hours_this_day = (time_out_datetime - time_in_datetime).seconds/3600
        total_hours += hours_this_day
        print("HOURS", hours_this_day)

        canvas_field.drawString(50, timetable_top - (PADDING * index), date + ' ' + time_in[:13])
        canvas_field.drawString(150, timetable_top - (PADDING * index), time_in[13:])
        canvas_field.drawString(250, timetable_top - (PADDING * index), time_out[13:])
        canvas_field.drawString(330, timetable_top - (PADDING * index), str(hours_this_day))
        canvas_field.drawString(490, timetable_top - (PADDING * index), note_in)
        canvas_field.drawString(450, timetable_top - (PADDING * index), note_out)

        # For testing
        canvas_field.drawString(500, timetable_top - (PADDING * index), name) # TODO: DELETE BEFORE PRODUCTION

        index += 1

    canvas_field.drawString(330, timetable_top - (PADDING * index + 5), 'TOTAL:' + str(total_hours))


def generate_signature_template(canvas_field):
    """
    Creates a signature form at the bottom of the pdf.
    :param canvas_field: The canvas to add the signature template to.
    :return: None.
    """

    # Conditions of submission
    canvas_field.setFont('Courier', 6)
    canvas_field.drawString(45, 200, 'I hereby certify the following:')
    canvas_field.drawString(45, 185, 'The time shown correctly represents my attendance and activities for the week'
                                     'indicated. If I am an employee eligible to earn overtime compensation')
    canvas_field.drawString(45, 175, 'under the FLSA and/or a collective bargaining agreement,I also certify that I'
                                     'have requested compensation for any time that I worked in '
                                     'excess of')
    canvas_field.drawString(45, 165, 'my scheduled hours and that any time outside my scheduled hours, i.e. '
                                     'when I may have logged in/out earlier/later than my scheduled time, for which')
    canvas_field.drawString(45, 155, 'I have not requested compensation, was time not worked')

    # Signature section
    canvas_field.setFont('Courier', 8)
    canvas_field.line(45, 85, 215, 85)
    canvas_field.drawString(60, 70, 'Employee Signature')

    canvas_field.line(225, 85, 285, 85)
    canvas_field.drawString(240, 70, 'Date')

    canvas_field.line(325, 85, 495, 85)
    canvas_field.drawString(340, 70, 'Approver Signature')

    canvas_field.line(505, 85, 565, 85)
    canvas_field.drawString(520, 70, 'Date')


def generate_footer(canvas_field):
    """
    Creates the footer for timesheet form.
    :param canvas_field: The canvas to add the footer to.
    :return: None.
    """
    canvas_field.setFont('Courier', 8)
    canvas_field.drawString(25, 20, 'Generated by ' + current_user.first_name + ' ' + current_user.last_name)
    canvas_field.drawString(470, 20, datetime.now().strftime("%b %d, %Y %l:%M:%S %p"))
    canvas_field.line(25, 30, width-25, 30)
