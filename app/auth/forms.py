from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo
from ..models import User
from datetime import datetime


class LoginForm(Form):
    """
    Used for registered users to log into the system.
    """
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    """
    Used to register new users into the system.
    """
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    first_name = StringField("First name")
    last_name = StringField("Last name")
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        """
        Verifies that e-mails used for registration do not already exist in the system.
        :param field:
        :return:
        """
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('An account with this email address already exists')

    def validate_password(form, field):
        """
        Used to verify that password meets security criteria.
        :param field: password field
        :return: A validation message if password is not secure.
        """
        if len(field.data) <= 8:
            raise ValidationError('Your password must be longer than eight characters')

        has_num = False
        has_capital = False
        for i in field.data:
            if i.isdigit():
                has_num = True
            if i.isupper():
                has_capital = True

        if not (has_num or has_capital):
            raise ValidationError('Passwords must contain at least one number and one capital letter.')

        if not has_num:
            raise ValidationError('Password must contain at least one number')

        if not has_capital:
            raise ValidationError('Password must contain at least one capital letter')


class AdminRegistrationForm(Form):
    """
    Used by admins to register new users into the system.
    """
    email = StringField('Email', validators=[DataRequired(), Length(1,64), Email()])
    first_name = StringField("First name")
    last_name = StringField("Last name")
    submit = SubmitField('Register')

    def validate_email(self, field):
        """
        Verifies that e-mails used for registration do not already exist in the system.
        :param field:
        :return:
        """
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('An account with this email address already exists')

class ChangePasswordForm(Form):
    """Form for changing password"""
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    """Initial request form for password reset"""
    email = StringField('Email', validators=[DataRequired(), Length(1, 100),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    """Password reset form after email confirmation"""
    email = StringField('Email', validators=[DataRequired(), Length(1, 100),
                                             Email()])
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')
