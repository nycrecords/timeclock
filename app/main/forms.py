from flask_wtf import Form
from wtforms import StringField, SubmitField, DateTimeField, SelectField
from wtforms.validators import DataRequired, Optional, Length
from datetime import date


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


class AdminFilterEventsForm(Form):
    """
    Form for Administrators to filter all clock events.
    Administrators can search users by email.
    Administrators can search for clock events between first_date and last_date.
    Administrators can search for clock events created by a given user between first_date and second_date.
    """
    email = StringField("Email", validators=[Optional()])
    first_date = DateTimeField("From", default=date(2004, 1, 1), validators=[Optional()])
    last_date = DateTimeField("To", default=date.today(), validators=[Optional()])
    tag = SelectField(u"Tag",
                      choices=[(0, 'None'), (1, 'Intern'), (2, 'Contractor'), (3, 'SYEP'), (4, 'Radical'), (5,'Consultant'), (6, 'Other')],
                      coerce=int,
                      validators=[Optional()])
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
    first_date = DateTimeField("From",
                               default=date(2004, 1, 1),
                               validators=[DataRequired()]
                               )
    last_date = DateTimeField("To",
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
