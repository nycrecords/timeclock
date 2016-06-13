from flask_wtf import Form
from wtforms import StringField, SubmitField, BooleanField, DateTimeField
from wtforms.validators import DataRequired, Optional


class ClockInForm(Form):
    note = StringField("Note: ")
    submit = SubmitField("Clock In")


class ClockOutForm(Form):
    note = StringField("Note: ")
    submit = SubmitField("Clock Out")


class AdminFilterEventsForm(Form):
    username = StringField("Username", validators=[Optional()])
    first_date = DateTimeField("From", validators=[Optional()])
    last_date = DateTimeField("To", validators=[Optional()])
    submit = SubmitField("Filter")


class UserFilterEventsForm(Form):
    first_date = DateTimeField("From")
    last_date = DateTimeField("To")
    submit = SubmitField("Filter")
