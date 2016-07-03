from flask_wtf import Form
from wtforms import StringField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, Optional, Length
from datetime import date
from ..utils import tags, divisions


class ClockInForm(Form):
    """
    Form for clocked out users.
    """
    note = StringField("Note: ", validators=[Length(min=0, max=120)])
    submit = SubmitField("Clock In")


class ClockOutForm(Form):
    """
    Form for clocked in users.
    """
    note = StringField("Note: ", validators=[Length(min=0, max=120)])
    submit = SubmitField("Clock Out")


class TimePunchForm(Form):
    """
    Form for requesting a time punch.
    """
    punch_type = SelectField("Punch Type", validators=[DataRequired()], choices=[(0, 'In'), (1, 'Out')])
    note = StringField("Note: ", validators=[DataRequired(), Length(min=0, max=120)])
    submit = SubmitField("Submit Request")


class AdminFilterEventsForm(Form):
    """
    Form for Administrators to filter all clock events.
    Administrators can search users by email.
    Administrators can search for clock events between first_date and last_date.
    Administrators can search for clock events created by a given user between first_date and second_date.
    """
    email = StringField("Email", validators=[Optional()])
    first_date = DateField("From", default=date(2004, 1, 1), validators=[Optional()])
    last_date = DateField("To", default=date.today(), validators=[Optional()])
    tag = SelectField("Tag", choices=tags, coerce=int, validators=[Optional()])
    submit = SubmitField("Filter")
    last_month = SubmitField("Last Month")
    this_month = SubmitField("This Month")
    last_week = SubmitField("Last Week")
    this_week = SubmitField("This Week")
    last_day = SubmitField("Yesterday")
    this_day = SubmitField("Today")


class UserFilterEventsForm(Form):
    """
    Form for users to filter their own clock events by date. Users can look
    at self-generated clock events between first_date and last_date.
    """
    first_date = DateField("From",
                           default=date(2004, 1, 1),
                           validators=[DataRequired()]
                           )
    last_date = DateField("To",
                          default=date.today(),
                          validators=[DataRequired()]
                          )
    submit = SubmitField("Filter")
    last_month = SubmitField("Last Month")
    this_month = SubmitField("This Month")
    last_week = SubmitField("Last Week")
    this_week = SubmitField("This Week")
    last_day = SubmitField("Yesterday")
    this_day = SubmitField("Today")
