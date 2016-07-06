from flask import current_app
from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, ValidationError, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from ..models import User
from flask_login import current_user
from ..utils import tags, divisions, roles



class LoginForm(Form):
    """Used for registered users to log into the system."""
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    """Used to register new users into the system."""
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    first_name = StringField("First name")
    last_name = StringField("Last name")
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email_field):
        """
        Verifies that e-mails used for registration do not already exist in the system.

        :param field:
        :return:
        """
        user = User.query.filter_by(email=email_field.data).first()
        if user:
            if user.email:
                current_app.logger.error('{} tried to register user with email {} but user already exists.'.format(
                    user.email, email_field.data))
            else:
                current_app.logger.error('Anonymous user tried to register user with email {} but user already exists.'.
                                         format(email_field.data))
            raise ValidationError('An account with this email address already exists')

    def validate_password(self, password_field):
        """
        Used to verify that password meets security criteria.

        :param field: password field
        :return: A validation message if password is not secure.
        """
        if len(password_field.data) < 8:
            raise ValidationError('Your password must be 8 or more characters')

        has_num = False
        has_capital = False
        for i in password_field.data:
            if i.isdigit():
                has_num = True
            if i.isupper():
                has_capital = True

        if not (has_num or has_capital):
            raise ValidationError('Passwords must contain at least one number and one capital letter')

        if not has_num:
            raise ValidationError('Password must contain at least one number')

        if not has_capital:
            raise ValidationError('Password must contain at least one capital letter')


class AdminRegistrationForm(Form):
    """Used by admins to register new users into the system."""
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    first_name = StringField("First name")
    last_name = StringField("Last name")
    division = SelectField('Division', choices=divisions, validators=[DataRequired()])
    tag = SelectField('Tag', choices=tags, coerce=int, validators=[DataRequired()])
    role = SelectField('Role', choices=roles, validators=[DataRequired()])

    submit = SubmitField('Register')

    def validate_email(self, email_field):
        """
        Verifies that e-mails used for registration do not already exist in the system.

        :param field:
        :return:
        """
        if User.query.filter_by(email=email_field.data).first():
            raise ValidationError('An account with this email address already exists')
        return True

    def validate_tag(self, tag_field):
        """
        Verify that the tag is valid.

        :param field: Field passed in to validate (Tag)
        :return: Nothing if check passes; Raise validation error if invalid entry in field.
        """
        if not tag_field.data or tag_field.data == '':
            raise ValidationError('All users must be tagged')
        return True

    def validate_division(self, div_field):
        """
        Verify that the division is valid.

        :param field: Field passed in to validate (Division)
        :return: Nothing if check passes; Raise validation error if invalid entry in field.
        """
        if not div_field.data or div_field.data == '':
            raise ValidationError('All users must belong to a division')
        return True



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
    # email = StringField('Email', validators=[DataRequired(), Length(1, 100),
    #                                          Email()])
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')
