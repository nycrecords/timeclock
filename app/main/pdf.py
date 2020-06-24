"""
For generating timesheet pdf with appropriate styling.
"""
from datetime import datetime

from flask import session, current_app
from flask_login import current_user
from reportlab.lib.pagesizes import letter

from app.models import User

# Global: Set width and length to values corresponding to normal paper size
width, length = letter


def set_defaults(canvas_field):
    """
    Sets timesheet defaults.
    :param canvas_field: The canvas whose styles will be modified.
    :return: None
    """
    current_app.logger.info("PDF: Setting defaults...")
    canvas_field.setFont("Courier", 12)
    current_app.logger.info("PDF: Finished setting defaults")


def generate_header(canvas_field):
    """
    Creates the footer for timesheet form.
    :param canvas_field: The canvas to add the header to.
    :return: None
    """
    current_app.logger.info("PDF: Generating header...")
    canvas_field.setFont("Courier", 8)
    canvas_field.drawString(
        25,
        length - 30,
        "The City of New York - Department of Records and Information Services",
    )
    canvas_field.line(25, 30, width - 25, 30)
    current_app.logger.info("PDF: Finished generating header")


def generate_employee_info(canvas_field):
    """
    Generates portion of pdf that contains employee information.
    :param canvas_field: The canvas to add the employee information to.
    :return:None.
    """
    current_app.logger.info("PDF: Generating employee info...")
    if session["email"] is None or session["email"] == "":
        u = User.query.filter_by(email=current_user.email.lower()).first()
    else:
        u = User.query.filter_by(email=session["email"].lower()).first()
    first_date = session["first_date"]
    last_date = session["last_date"]

    canvas_field.setFont("Courier", 10)
    canvas_field.drawString(
        25, length - 60, "Employee Name: " + u.first_name + " " + u.last_name
    )
    canvas_field.drawString(
        25, length - 70, "Position: " + (u.tag.name if u.tag else "None")
    )
    canvas_field.drawString(25, length - 80, "Division: " + str(u.division))
    canvas_field.drawString(
        270, length - 60, "From: " + first_date.strftime("%b %d, %Y %l:%M:%S %p")
    )
    canvas_field.drawString(
        270, length - 70, "To:   " + last_date.strftime("%b %d, %Y %l:%M:%S %p")
    )
    current_app.logger.info("PDF: Finished generating employee info")


def generate_timetable(canvas_field, events):
    """
    Generates timetable for a week for a given user.
    :param canvas_field: The canvas to add the timetable to.
    :param events: Events to write to the timetable.
    :return: None.
    """
    current_app.logger.info("PDF: Generating timetable...")
    timetable_top = length - 150  # Top of the time_table area
    index = 1
    total_hours = 0

    canvas_field.setFont("Courier-Bold", 10)
    canvas_field.drawString(55, timetable_top - 5, "DATE")
    canvas_field.drawString(135, timetable_top - 5, "TIME IN")
    canvas_field.drawString(222, timetable_top - 5, "TIME OUT")
    canvas_field.drawString(310, timetable_top - 5, "HOURS")
    canvas_field.drawString(370, timetable_top - 5, "NOTE IN")
    canvas_field.drawString(480, timetable_top - 5, "NOTE OUT")
    canvas_field.line(20, timetable_top - 10, 600, timetable_top - 10)

    canvas_field.setFont("Courier", 10)
    if len(events) % 2 != 0:
        events.pop(0)
    events = sorted(events)
    next_line = timetable_top
    # Looping through events table to determine values to input on pdf
    for x in range(0, len(events), 2):
        if next_line <= 100:
            canvas_field.showPage()
            next_line = length - 40
        event = events[x]
        next_event = events[x + 1]
        canvas_field.setFont("Courier", 8)
        time_in = event[: event.index("|") - 1]
        event = event[(event.index("|") + 2) :]
        event = event[(event.index("|") + 2) :]
        note_in = event[(event.index("|") + 2) :]

        time_out = next_event[: next_event.index("|") - 1]
        next_event = next_event[(next_event.index("|") + 2) :]
        next_event = next_event[(next_event.index("|") + 2) :]
        note_out = next_event[(event.index("|") + 3) :]

        if note_in or note_out:
            if len(note_in) > len(note_out):
                max_note_length = len(note_in)
            else:
                max_note_length = len(note_out)
        else:
            max_note_length = 20

        # Dynamically adjust padding (space provided for the row) according to note length
        padding = 25 + max_note_length / 7

        time_in_datetime = datetime.strptime(time_in, "%b %d, %Y %H:%M:%S %p")
        time_out_datetime = datetime.strptime(time_out, "%b %d, %Y %H:%M:%S %p")

        date = time_in_datetime.strftime("%a %b %d, %Y")
        hours_this_day = (time_out_datetime - time_in_datetime).seconds / float(3600)
        hours_this_day = hours_this_day - 1 if hours_this_day >= 5 else hours_this_day
        total_hours += hours_this_day

        next_line -= padding

        # Begin drawing here
        canvas_field.drawString(30, next_line, date)
        canvas_field.drawString(130, next_line, time_in_datetime.strftime("%H:%M:%S"))
        canvas_field.drawString(220, next_line, time_out_datetime.strftime("%H:%M:%S"))
        canvas_field.drawString(310, next_line, "{0:.2f}".format(hours_this_day))

        # Provide 7 pixels of space between note lines: (10, 3, -4, -11, etc.)
        canvas_field.drawString(
            370, next_line + max_note_length / padding + 10, note_in[0:20]
        )
        canvas_field.drawString(
            370, next_line + max_note_length / padding + 3, note_in[20:40]
        )
        canvas_field.drawString(
            370, next_line + max_note_length / padding - 4, note_in[40:60]
        )
        canvas_field.drawString(
            370, next_line + max_note_length / padding - 11, note_in[60:80]
        )
        canvas_field.drawString(
            370, next_line + max_note_length / padding - 18, note_in[80:100]
        )
        canvas_field.drawString(
            370, next_line + max_note_length / padding - 25, note_in[100:120]
        )
        canvas_field.drawString(
            480, next_line + max_note_length / padding + 10, note_out[0:20]
        )
        canvas_field.drawString(
            480, next_line + max_note_length / padding + 3, note_out[20:40]
        )
        canvas_field.drawString(
            480, next_line + max_note_length / padding - 4, note_out[40:60]
        )
        canvas_field.drawString(
            480, next_line + max_note_length / padding - 11, note_out[60:80]
        )
        canvas_field.drawString(
            480, next_line + max_note_length / padding - 18, note_out[80:100]
        )
        canvas_field.drawString(
            480, next_line + max_note_length / padding - 25, note_out[100:120]
        )
        next_line -= max_note_length / padding
        canvas_field.setLineWidth(0.5)
        canvas_field.line(20, next_line - 10, 600, next_line - 10)

        index += 1

    canvas_field.drawString(
        50, next_line - 25, "TOTAL: " + "{0:.2f}".format(total_hours)
    )

    canvas_field.setLineWidth(1)  # Reset line width
    current_app.logger.info("PDF: Finished generating timetable...")


def generate_signature_template(canvas_field):
    """
    Creates a signature form at the bottom of the pdf.
    :param canvas_field: The canvas to add the signature template to.
    :return: None.
    """
    current_app.logger.info("PDF: Generating signature template...")
    # Conditions of submission
    canvas_field.setFont("Courier", 6)
    canvas_field.drawString(45, 200, "I hereby certify the following:")
    canvas_field.drawString(
        45,
        185,
        "The time shown correctly represents my attendance and activities for the week"
        " indicated. If I am an employee eligible to earn overtime compensation",
    )
    canvas_field.drawString(
        45,
        175,
        "under the FLSA and/or a collective bargaining agreement, I also certify that I"
        " have requested compensation for any time that I worked in "
        "excess of",
    )
    canvas_field.drawString(
        45,
        165,
        "my scheduled hours and that any time outside my scheduled hours, i.e. "
        "when I may have logged in/out earlier/later than my scheduled time, for which",
    )
    canvas_field.drawString(
        45, 155, "I have not requested compensation, was time not worked."
    )

    # Signature section
    canvas_field.setFont("Courier", 8)
    canvas_field.line(45, 85, 215, 85)
    canvas_field.drawString(60, 70, "Employee Signature")

    canvas_field.line(225, 85, 285, 85)
    canvas_field.drawString(240, 70, "Date")

    canvas_field.line(325, 85, 495, 85)
    canvas_field.drawString(340, 70, "Approver Signature")

    canvas_field.line(505, 85, 565, 85)
    canvas_field.drawString(520, 70, "Date")
    current_app.logger.info("PDF: Finished generating signature template")


def generate_footer(canvas_field):
    """
    Creates the footer for timesheet form.
    :param canvas_field: The canvas to add the footer to.
    :return: None.
    """
    current_app.logger.info("PDF: Generating footer...")
    canvas_field.setFont("Courier", 8)
    canvas_field.drawString(
        25, 20, "Generated by " + current_user.first_name + " " + current_user.last_name
    )
    canvas_field.drawString(470, 20, datetime.now().strftime("%b %d, %Y %l:%M:%S %p"))
    canvas_field.line(25, 30, width - 25, 30)
    current_app.logger.info("PDF: Finished generating footer...")


def generate_health_screen_confirmation(canvas_field, name, division, date, report_to_work):
    canvas_field.setFont("Times-Bold", 14)
    canvas_field.drawString(
        220,
        length - 52,
        "Employee Health Screening"
    )

    canvas_field.setFont("Times-Bold", 12)
    canvas_field.drawString(
        110,
        length - 66,
        "Please answer the questions below and click the Submit button when done."
    )

    canvas_field.setFont("Times-Roman", 12)
    canvas_field.drawString(
        70,
        length - 110,
        "Name: " + name
    )

    canvas_field.drawString(
        70,
        length - 140,
        "Division: " + division
    )

    canvas_field.drawString(
        70,
        length - 170,
        "Date: " + date
    )

    canvas_field.drawString(
        70,
        length - 200,
        "1.   Click here to confirm you completed the entire questionnaire."
    )

    canvas_field.acroForm.checkbox(checked=True,
                                   size=13,
                                   x=385,
                                   y=length - 202)

    if report_to_work == 'Yes':
        checked_yes = True
        checked_no = False
    else:
        checked_yes = False
        checked_no = True

    canvas_field.drawString(
        70,
        length - 230,
        "2.   Based on your questionnaire results, you may report to work yes or no."
    )

    canvas_field.drawString(
        435,
        length - 230,
        "Yes"
    )
    canvas_field.acroForm.checkbox(checked=checked_yes,
                                   size=13,
                                   x=455,
                                   y=length - 232)

    canvas_field.drawString(
        472,
        length - 230,
        "No"
    )
    canvas_field.acroForm.checkbox(checked=checked_no,
                                   size=13,
                                   x=489,
                                   y=length - 232)

    canvas_field.drawString(
        89,
        length - 245,
        "If your response is “no”, please contact healthcheck@records.nyc.gov in Human Resources."
    )
