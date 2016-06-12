from flask_wtf import Form
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class ClockInForm(Form):
    note = StringField("Note: ")
    submit = SubmitField("Clock In")


class ClockOutForm(Form):
    note = StringField("Note: ")
    submit = SubmitField("Clock Out")


class FilterUserForm(Form):
    username = StringField("Username")
    submit = SubmitField("Search Users")

