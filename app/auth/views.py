"""
.. module:: auth.views.

   :synopsis: Handles all authentication URL endpoints for the
   timeclock application
"""
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from . import auth
from .. import db
from ..models import User, Tag
from ..decorators import admin_required
from ..email_notification import send_email
from ..utils import InvalidResetToken
from .forms import (
    LoginForm,
    RegistrationForm,
    AdminRegistrationForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    ChangePasswordForm
)
from .modules import get_day_of_week, check_password_requirements
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash
from flask import current_app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Renders the HTML page where users can register new accounts. If the RegistrationForm meets criteria, a new user is
    written into the database.

    :return: HTML page for registration.
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    password=form.password.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    validated=True)
        db.session.add(user)
        db.session.commit()
        # TODO: Add logging here.
        flash('User successfully registered', category='success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth.route('/admin_register', methods=['GET', 'POST'])
@admin_required
def admin_register():
    """
    Renders a form for admins to register new users.

    :return: HTML page where admins can register new users
    """
    form = AdminRegistrationForm()

    if form.validate_on_submit():
        # TODO: Can this be done using `datetime.datetime.today().strftime('%A%d')`? This outputs 'Saturday02'
        temp_password = get_day_of_week() + str(datetime.today().day)

        # TODO: What is a valid 'default' tag?
        tag_id = 6
        if 'tag' in form:
            tag_id = form.tag.data
        user = User(email=form.email.data,
                    password=temp_password,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    division=form.division.data,
                    role_id=form.role.data,
                    tag_id=tag_id
                    )
        # user.password_list.valid
        db.session.add(user)
        db.session.commit()

        send_email(user.email,
                   'DORIS TimeClock - New User Registration',
                   'auth/email/new_user',
                   user=user,
                   temp_password=temp_password)

        current_app.logger.info('Sent login instructions to {}'.format(user.email))
        flash('User successfully registered\nAn email with login instructions has been sent to {}'.format(user.email),
              category='success')

        current_app.logger.info('%s registered user with email %s' % (current_user.email, form.email.data))
        return redirect(url_for('main.index'))
    return render_template('auth/admin_register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    View function to login a user. Redirects the user to the index page on successful login.

    :return: Login page.
    """
    # Redirect to index if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=(form.email.data).lower()).first()
        if user and user.login_attempts >= 2:
            # TODO: Add logging
            flash('You have too many invalid login attempts. You must reset your password.',
                  category='error')
            return redirect(url_for('auth.password_reset_request'))
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            user.login_attempts = 0
            db.session.add(user)
            db.session.commit()
            current_app.logger.info('{} successfully logged in'.format(current_user.email))
            current_app.logger.error('{} is still logged in.'.format(current_user.email))
            # Check to ensure password isn't outdated
            current_app.logger.info('TIMEOUT PASSWORD? {}'.format(
                (datetime.today() - current_user.password_list.last_changed).days > 90
            ))
            current_app.logger.error('{} is still logged in. - Checked password timeout'.format(current_user.email))
            if (datetime.today() - current_user.password_list.last_changed).days > 90:
                current_user.validated = False
                db.session.add(current_user)
                db.session.commit()
                flash('You haven\'t changed your password in 90 days. You must re-validate your account',
                      category='error')
                return redirect(url_for('auth.change_password'))
            current_app.logger.error('{} is still logged in. Check days to change password'.format(current_user.email))

            if (datetime.today() - current_user.password_list.last_changed).days > 75:
                days_to_expire = (datetime.today() - current_user.password_list.last_changed).days
                flash('Your password will expire in {} days.'.format(days_to_expire), category='warning')
            current_app.logger.error('{} is still logged in. Redirecting to main.index'.format(current_user.email))
            # return redirect(request.args.get('next') or url_for('main.index'))
            current_app.logger.info('{}'.format(request.args.get('next')))
            return render_template('index.html')
        if user:
            current_app.logger.info('{} failed to log in: Invalid username or password'.format(user.email))
            user.login_attempts += 1
            db.session.add(user)
            db.session.commit()
        flash('Invalid username or password', category='error')
    return render_template('auth/login.html', form=form, reset_url=url_for('auth.password_reset_request'))


@auth.route('/logout')
@login_required
def logout():
    """
    View function to logout a user.

    :return: Index page.
    """
    current_app.logger.info('{} logged out'.format(current_user.email))
    logout_user()
    flash('You have been logged out.', category='success')
    return redirect(url_for('auth.login'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    View function for changing a user password.

    :return: Change Password page.
    """
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if (
                                check_password_hash(pwhash=current_user.password_list.p1,
                                                    password=form.password.data) or
                                check_password_hash(pwhash=current_user.password_list.p2,
                                                    password=form.password.data) or
                            check_password_hash(pwhash=current_user.password_list.p3, password=form.password.data) or
                        check_password_hash(pwhash=current_user.password_list.p4, password=form.password.data) or
                    check_password_hash(pwhash=current_user.password_list.p5, password=form.password.data)
        ):
            current_app.logger.info('{} tried to change password. Failed: Used old password.'.format(
                current_user.email))
            flash('Your password cannot be the same as the last 5 passwords', category='error')
        elif check_password_requirements(
                current_user.email,
                form.old_password.data,
                form.password.data,
                form.password2.data):
            current_user.password_list.update(current_user.password_hash)
            current_user.password = form.password.data
            current_user.validated = True
            db.session.add(current_user)
            db.session.commit()
            current_app.logger.info('{} changed their password.'.format(current_user.email))
            flash('Your password has been updated.', category='success')
            return redirect(url_for('main.index'))
    return render_template("auth/change_password.html", form=form)


@auth.route('/reset', methods=['GET', 'POST'])
def password_reset_request():
    """
    View function for requesting a password reset.

    :return: HTML page in which users can request a password reset.
    """
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        current_app.logger.info('Tried to submit a password reset request with account email {}'.format(
            form.email.data))
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email,
                       'Reset Your Password',
                       'auth/email/reset_password',
                       user=user,
                       token=token,
                       next=request.args.get('next'))
            current_app.logger.info('Sent password reset instructions to {}'.format(form.email.data))
            flash('An email with instructions to reset your password has been sent to you.', category='success')
        else:
            current_app.logger.info('Requested password reset for e-mail %s but no such account exists' %
                                    form.email.data)
            flash('An account with this email was not found in the system.', category='error')
        return redirect(url_for('auth.login'))
    return render_template('auth/request_reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    """
    View function after a user has clicked on a password reset link in their inbox.

    :param token: The token that is checked to verify the user's credentials.
    :return: HTML page in which users can reset their passwords.
    """
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except ValueError:
            flash('This token is no longer valid.', category='warning')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(id=data.get('reset')).first()
        if user is None:
            current_app.logger.info('Requested password reset for invalid account.')
            return redirect(url_for('main.index'))
        try:
            if user.reset_password(token, form.password.data):
                user.login_attempts = 0
                db.session.add(user)
                db.session.commit()
                flash('Your password has been updated.', category='success')
                return redirect(url_for('auth.login'))
            else:
                flash('Password must be at least 8 characters with at least 1 Uppercase Letter and 1 Number',
                      category='error')
                return render_template('auth/reset_password.html', form=form)
        except InvalidResetToken:
            flash('This token is no longer valid.', category='warning')
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)
