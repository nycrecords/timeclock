"""
For generating timesheet pdf with appropriate styling.
"""
from flask import session
from flask_login import current_user
from datetime import datetime
from ..models import User

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
    :param email_input: The email of the employee whose information should be added.
    :return:
    """
    print("SESSION EMAIL: " + session['email'])
    if session['email'] is None or session['email'] == '':
        u = User.query.filter_by(email=current_user.email).first()
    else:
        u = User.query.filter_by(email=session['email']).first()
    print(session['email'])
    canvas_field.setFont('Courier', 10)
    canvas_field.drawString(25, length - 60, 'Employee Name: ' + u.first_name + ' ' + u.last_name)
    canvas_field.drawString(25, length - 80, 'Position: ' + (u.tag if u.tag else "None"))
    canvas_field.drawString(300, length - 60, 'From: ' + session['first_date'].strftime("%b %d, %Y %l:%M:%S %p"))
    canvas_field.drawString(300, length - 80, 'To:   ' + session['last_date'].strftime("%b %d, %Y %l:%M:%S %p"))



def generate_footer(canvas_field):
    """
    Creates the footer for timesheet form.
    :param canvas_field: The canvas to add the footer to.
    :return: None
    """
    canvas_field.setFont('Courier', 8)
    canvas_field.drawString(25, 20, 'Generated by ' + current_user.first_name + ' ' + current_user.last_name)
    canvas_field.drawString(470, 20, datetime.now().strftime("%b %d, %Y %l:%M:%S %p"))
    canvas_field.line(25, 30, width-25, 30)

