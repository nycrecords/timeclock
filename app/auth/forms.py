from flask_wtf import Form
from wtforms import StringField, PasswordField, SubmitField, ValidationError, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo

from ..models import User
from ..utils import tags, divisions, roles


class LoginForm(Form):
    """Used for registered users to log into the system."""
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class RegistrationForm(Form):
    """Used to register new users into the system."""
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    first_name = StringField("First name", validators=[DataRequired()])
    last_name = StringField("Last name", validators=[DataRequired()])
    division = SelectField('Division', choices=divisions, validators=[DataRequired()])
    tag = SelectField('Tag', choices=tags, coerce=int, validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match'), Length(min=8)])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    budget_code = StringField('Budget Code')
    object_code = StringField('Object Code')
    object_name = StringField('Object Name')
    submit = SubmitField('Register')

    def validate_email(self, email_field):
        """
        Verifies that e-mails used for registration do not already exist in the system.

        :param email_field:
        :return:
        """
        if User.query.filter_by(email=email_field.data).first():
            raise ValidationError('An account with this email address already exists')
        return True

    def validate_tag(self, tag_field):
        """
        Verify that the tag is valid.

        :param tag_field: Field passed in to validate (Tag)
        :return: Nothing if check passes; Raise validation error if invalid entry in field.
        """
        if not tag_field.data or tag_field.data == '':
            raise ValidationError('All users must be tagged')
        return True

    def validate_division(self, div_field):
        """
        Verify that the division is valid.

        :param div_field: Field passed in to validate (Division)
        :return: Nothing if check passes; Raise validation error if invalid entry in field.
        """
        if not div_field.data or div_field.data == '':
            raise ValidationError('All users must belong to a division')
        return True

    def validate_password(self, password_field):
        """
        Used to verify that password meets security criteria.

        :param password_field: password field
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
    # SUPERVISOR EMAIL IS DYNAMICALLY ADDED IN VIEW FUNCTION
    supervisor_email = SelectField('Supervisor Email', choices=[], coerce=int,
                                   validators=[DataRequired()])
    is_supervisor = BooleanField('User is supervisor')
    # supervisor_email = StringField('Supervisor Email', validators=[DataRequired(), Length(1, 64), Email()])
    role = SelectField('Role', choices=roles, validators=[DataRequired()])
    budget_code = StringField('Budget Code')
    object_code = StringField('Object Code')
    object_name = StringField('Object Name')
    submit = SubmitField('Register')

    def validate_email(self, email_field):
        """
        Verifies that e-mails used for registration do not already exist in the system.

        :param email_field:
        :return:
        """
        if User.query.filter_by(email=email_field.data).first():
            # raise ValidationError
            # flash('An account with this email address already exists', 'error')
            self.email.errors = 'An account with this email address already exists',
            return False
        return True

    def validate_tag(self, tag_field):
        """
        Verify that the tag is valid.

        :param tag_field: Field passed in to validate (Tag)
        :return: Nothing if check passes; Raise validation error if invalid entry in field.
        """
        if not tag_field.data or tag_field.data == '' or int(tag_field.data) < 1 or int(tag_field.data > 7):
            # raise ValidationError('All users must be tagged')
            # flash('All users must be tagged', 'error')
            self.tag.errors = 'All users must have a tag',
            return False
        return True

    def validate_division(self, div_field):
        """
        Verify that the division is valid.

        :param div_field: Field passed in to validate (Division)
        :return: Nothing if check passes; Raise validation error if invalid entry in field.
        """
        if not div_field.data or div_field.data == '':
            # raise ValidationError('All users must belong to a division')
            # flash('All users must belong to a division', 'error')
            self.division.errors = 'All users must belong to a division',
            return False
        return True

    def validate_supervisor_email(self, email_field):
        """
        Verifies that e-mails used for supervisors exist in the system.

        :param email_field:
        :return:
        """
        user = User.query.filter_by(id=email_field.data).first()
        if not user:
            # raise ValidationError('No account with that email exists')
            # flash('Invalid supervisor email', 'error')
            self.supervisor_email.errors = 'Invalid supervisor',
            return False
        return True

    def validate_on_submit(self):
        is_email = True
        try:
            (Email(self.email).__call__(self, self.email))
        except ValidationError:
            # flash("Invalid e-mail address", 'error')
            self.email.errors = 'Invalid e-mail address',
            is_email = False

        if self.first_name._value():
            first_name = True
        else:
            first_name = False
            self.first_name.errors = 'User must have a first name',
            # flash('User must have a first name', 'error')

        if self.last_name._value():
            last_name = True
        else:
            last_name = False
            self.last_name.errors = 'User must have a last name',
            # flash('User must have a last name', 'error')

        valid_email = self.validate_email(self.email)
        valid_div = self.validate_division(self.division)
        valid_tag = self.validate_tag(self.tag)
        valid_sup = self.validate_supervisor_email(self.supervisor_email)

        return is_email and valid_email and first_name and last_name and valid_div and valid_tag and valid_sup


class ChangePasswordForm(Form):
    """Form for changing password"""
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match'), Length(min=8)])
    password2 = PasswordField('Confirm new password', validators=[DataRequired()])
    submit = SubmitField('Update Password')


class PasswordResetRequestForm(Form):
    """Initial request form for password reset"""
    email = StringField('Email', validators=[DataRequired(), Length(1, 100),
                                             Email()])
    submit = SubmitField('Reset Password')


class PasswordResetForm(Form):
    """Password reset form after email confirmation"""
    password = PasswordField('New Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class ChangeUserDataForm(Form):
    """
    Form administrators use to change a User's information.
    """
    first_name = StringField("First name")
    last_name = StringField("Last name")
    division = SelectField(u'Division', choices=divisions, validators=[DataRequired()])
    tag = SelectField(u'Tag', coerce=int, choices=tags, validators=[DataRequired()])
    # supervisor_email = StringField("Supervisor Email", validators=[DataRequired()])
    supervisor_email = SelectField('Supervisor Email', choices=[], coerce=int,
                                   validators=[DataRequired()])
    is_supervisor = BooleanField("User is a supervisor")
    role = SelectField(u'Role', choices=roles, validators=[DataRequired()])
    budget_code = StringField('Budget Code')
    object_code = StringField('Object Code')
    object_name = StringField('Object Name')
    user_status = SelectField('Set Status', choices=[("Active", "Active"), ("Inactive", "Inactive") ], validators=[DataRequired()])

    submit = SubmitField('Update')

    def validate_supervisor_email(self, email_field):
        """
        Verifies that e-mails used for supervisors exist in the system.
        :param email_field: The supervisor's email
        :return:
        """
        user = User.query.filter_by(id=email_field.data).first()
        if not user:
            raise ValidationError('No account with that email exists')