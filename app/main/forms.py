from flask_wtf import Form
from wtforms import StringField, SubmitField, DateField, SelectField, FloatField, DateTimeField, ValidationError
from wtforms.validators import DataRequired, Optional, Length, Email
from datetime import date, datetime
from ..utils import tags, divisions, roles
from ..models import User


class ClockInForm(Form):
    """
    Form for clocked out users.
    """
    note = StringField("Note: ")
    submit = SubmitField("Clock In", render_kw={"style": "background-color:#5cb85c; border-color:#4cae4c"})


class ClockOutForm(Form):
    """
    Form for clocked in users.
    """
    note = StringField("Note: ")
    submit = SubmitField("Clock Out", render_kw={"style": "background-color:#f0ad4e; border-color:#eea236"})


class TimePunchForm(Form):
    """
    Form for requesting a time punch.
    """
    punch_type = SelectField(u'Punch Type', validators=[DataRequired()], choices=[('In', 'In'), ('Out', 'Out')])
    punch_time = DateTimeField(default=datetime.today(), validators=[DataRequired()])
    note = StringField("Note: ", validators=[DataRequired(), Length(min=0, max=120)])
    submit = SubmitField("Submit Request")


class AdminFilterEventsForm(Form):
    """
    Form for Administrators to filter all clock events.
    Administrators can search users by email.
    Administrators can search for clock events between first_date and last_date.
    Administrators can search for clock events created by a given user between first_date and second_date.
    """
    from .modules import get_time_period
    email = StringField("Username/Email", validators=[Optional()])
    first_date = DateField("From", default=get_time_period('w')[0], validators=[Optional()])
    last_date = DateField("To", default=date.today(), validators=[Optional()])
    tag = SelectField("Tag", choices=tags, coerce=int, validators=[Optional()])
    division = SelectField("Division", choices=divisions, validators=[Optional()])
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
    last_month = SubmitField("Last Month")
    this_month = SubmitField("This Month")
    last_week = SubmitField("Last Week")
    this_week = SubmitField("This Week")


class CreatePayRateForm(Form):
    email = StringField("Email", validators=[DataRequired(), Email()])
    start_date = DateField("Start", default=date.today(), validators=[DataRequired()])
    end_date = DateField("End", default=date.today(), validators=[DataRequired()])
    rate = FloatField("Rate", validators=[DataRequired()])
    submit = SubmitField("Create Pay Rate")


class ApproveOrDenyTimePunchForm(Form):
    approve = SubmitField("")
    deny = SubmitField("")


class FilterTimePunchForm(Form):
    email = StringField("Email", validators=[Optional(), Email()])
    status = SelectField(u'Status', validators=[Optional()], choices=[
        ('All', 'All'),
        ('Approved', 'Approved'),
        ('Unapproved', 'Unapproved')])
    filter = SubmitField("Filter")


class ClearTimePunchFilterForm(Form):
    clear = SubmitField("Clear Filter")


class ChangeUserDataForm(Form):
    first_name = StringField("First name")
    last_name = StringField("Last name")
    division = SelectField(u'Division', choices=divisions, validators=[DataRequired()])
    tag = SelectField(u'Tag', coerce=int, choices=tags, validators=[DataRequired()])
    supervisor_email = StringField("Supervisor Email", validators=[DataRequired()])
    role = SelectField(u'Role', choices=roles, validators=[DataRequired()])
    submit = SubmitField('Update')

    def validate_supervisor_email(self, email_field):
        """
        Verifies that e-mails used for supervisors exist in the system.

        :param email_field: The supervisor's email
        :return:
        """
        user = User.query.filter_by(email=email_field.data).first()
        if not user:
            raise ValidationError('No account with that email exists')

