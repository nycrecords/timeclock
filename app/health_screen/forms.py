from flask_wtf import Form
from wtforms import (
    StringField,
    SubmitField,
    DateField,
    SelectField,
    BooleanField,
)
from wtforms.validators import DataRequired, Optional, Email
from app.utils import divisions


class HealthScreenForm(Form):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email("You must provide a valid @records.nyc.gov email address."),
        ],
    )
    date = StringField("Date", default="", validators=[DataRequired()])
    division = SelectField("Division", choices=divisions, validators=[DataRequired()])
    questionnaire_confirmation = BooleanField(validators=[DataRequired()])
    report_to_work = SelectField(
        choices=[("", ""), ("Yes", "Yes"), ("No", "No")], validators=[DataRequired()]
    )
    # recaptcha = Recaptcha3Field(action="TestAction", execute_on_load=True)
    submit = SubmitField("Submit")


class HealthScreenAdminForm(Form):
    name = StringField("Name", validators=[Optional()])
    email = StringField(
        "Email",
        validators=[
            Optional(),
            Email("You must provide a valid @records.nyc.gov email address."),
        ],
    )
    date = StringField("Date", default="", validators=[Optional()],)
    division = SelectField("Division", choices=divisions, validators=[Optional()])
    report_to_work = SelectField(
        choices=[("", ""), ("Yes", "Yes"), ("No", "No")], validators=[Optional()]
    )
    submit = SubmitField("Submit")


class AddHealthScreenUserForm(Form):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email("You must provide a valid @records.nyc.gov email address."),
        ],
    )
    division = SelectField("Division", choices=divisions, validators=[DataRequired()])
    submit = SubmitField("Submit")


class EditHealthScreenUserForm(Form):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email("You must provide a valid @records.nyc.gov email address."),
        ],
    )
    division = SelectField("Division", choices=divisions, validators=[DataRequired()])
    submit = SubmitField("Submit")
