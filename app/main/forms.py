from datetime import date, datetime

from flask_wtf import Form
from wtforms import StringField, SubmitField, DateField, SelectField, FloatField, BooleanField, SelectMultipleField, \
    ValidationError
from wtforms.validators import DataRequired, Optional, Length, Email

from ..models import User
from ..utils import tags, divisions, roles


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
    punch_date = DateField(u'Date', default=datetime.today(), validators=[DataRequired()])
    punch_time = StringField(u'Time (24-hour)', default="9:00", validators=[DataRequired()])
    note = StringField("Note: ", validators=[DataRequired(), Length(min=0, max=120)])
    submit = SubmitField("Submit Request")


class RequestVacationForm(Form):
    """
    Form for users to request a vacation.
    """
    vac_start = DateField(u'Start Date', default=datetime.today(), validators=[DataRequired()])
    vac_end = DateField(u'End Date', default=datetime.today(), validators=[DataRequired()])
    vac_request = SubmitField("Submit Request")


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

    def validate_email(self, email):
        """
        Verifies that a user with the given email exists in the system.

        :param email: The filtered email
        :return:
        """
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account with that email exists')


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
    """
    Form for creating payrates. Should only be usable by admins.
    """
    email = StringField("Email", validators=[DataRequired(), Email()])
    start_date = DateField("Start", default=date.today(), validators=[DataRequired()])
    rate = FloatField("Rate", validators=[DataRequired()])
    submit = SubmitField("Create Pay Rate")

    def validate_email(self, email):
        """
        Verifies that a user with the given email exists in the system.

        :param email: The filtered email
        :return:
        """
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account with that email exists')


class ApproveOrDenyForm(Form):
    """
    Form administrators use to approve or deny a request.
    Implemented in review_timepunches.html and review_vacations.html
    """
    approve = SubmitField("")
    deny = SubmitField("")


class AddEventForm(Form):
    """
    Form administrators use to add events. Implemented in all_history.html
    """
    addemail = StringField("Email", validators=[DataRequired(), Email()])
    add_date = DateField(u'Date', default=datetime.today(), validators=[DataRequired()])
    add_time = StringField(u'Time (24-hour)', default="9:00", validators=[DataRequired()])
    addpunch_type = SelectField(u'Punch Type', validators=[DataRequired()], choices=[('In', 'In'), ('Out', 'Out')])
    add = SubmitField("Create clock event")

    def validate_addemail(self, email):
        """
        Verifies that e-mails used for supervisors exist in the system.

        :param email: The supervisor's email
        :return:
        """
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account with that email exists')


class DeleteEventForm(Form):
    """
    Form administrators use to delete events. Implemented in all_history.html
    """
    delete = SubmitField("")


class FilterTimePunchForm(Form):
    """
    Form administrators use to filter through TimePunches.
    """
    email = StringField("Email", validators=[Optional(), Email()])
    approved = SelectField(u'Approval Status', validators=[Optional()], choices=[
        ('All', 'All'),
        ('Approved', 'Approved'),
        ('Unapproved', 'Unapproved')])
    status = SelectField(u'Status', validators=[Optional()], choices=[
        ('All', 'All'),
        ('Pending', 'Pending'),
        ('Processed', 'Processed')])
    filter = SubmitField("Filter")

    def validate_email(self, email):
        """
        Verifies that e-mails used for supervisors exist in the system.

        :param email: The email
        :return:
        """
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account with that email exists')


class ClearForm(Form):
    """
    Form administrators use to clear their filters.
    """
    clear = SubmitField("Clear Filter")


class FilterVacationForm(Form):
    """
     Form administrators use to filter through Vacations.
    """
    email = StringField("Email", validators=[Optional(), Email()])
    approved = SelectField(u'Status', validators=[Optional()], choices=[
        ('All', 'All'),
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Unapproved', 'Unapproved')])
    filter = SubmitField("Filter")

    def validate_email(self, email):
        """
        Verifies that e-mails used for supervisors exist in the system.

        :param email: The email
        :return:
        """
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account with that email exists')


class GenerateMultipleTimesheetsForm(Form):
    """
    Form to generate multiple timesheets (used only by administrators)
    """
    emails = SelectMultipleField(choices=[], validators=[DataRequired()], coerce=str)
    start_date = DateField(u'Start Date', default=datetime.today(), validators=[DataRequired()])
    end_date = DateField(u'End Date', default=datetime.today(), validators=[DataRequired()])
    gen_timesheets = SubmitField("Generate Timesheets")


class ExportForm(Form):
    export = SubmitField("Export")
