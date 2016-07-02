from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from . import auth
from .. import db
from ..models import User, Tag
from ..decorators import admin_required
from ..email import send_email
from .forms import LoginForm, RegistrationForm, AdminRegistrationForm, PasswordResetForm, PasswordResetRequestForm, ChangePasswordForm
from .modules import get_day_of_week, check_password_requirements
from datetime import datetime, date, timedelta
from werkzeug.security import check_password_hash
from flask import current_app
import calendar


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Renders the HTML page where users can register new accounts. If the RegistrationForm meets criteria,
    a new user is written into the database.
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
            flash('User successfully registered')
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
        temp_pass = get_day_of_week() + str(datetime.today().day)
        if 'tag' in form:
            tag_id=Tag.query.filter_by(name=form.tag.data).first().id
        user = User(email=form.email.data,
                    password=temp_pass,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    division=form.division.data,
                    role_id=1,
                    tag_id=tag_id
                    )
        db.session.add(user)
        db.session.commit()
        day_of_week = calendar.day_name[date.today().weekday()]
        day_of_month = datetime.today().day
        send_email(user.email, 'Reset Your Password', body=render_template(template='auth/email/admin_register.html',user=user,
                                                           day_of_week=day_of_week,day_of_month=day_of_month))
        current_app.logger.info(current_user.email + ' registered user with email ' + form.email.data)
        flash('User successfully registered')
        return redirect(url_for('main.index'))
    return render_template('auth/admin_register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renders the HTML page where users can log in to the system. If a login is successful, users are redirected to
    the index page.
    :return:
    """

    # Redirect to index if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.login_attempts >= 2:
            flash('You have too many invalid login attempts. You must reset your password.')
            return redirect(url_for('auth.password_reset_request'))
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            user.login_attempts = 0
            db.session.add(user)
            db.session.commit()
            current_app.logger.info(user.email + ' successfully logged in')
            # Check to ensure password isn't outdated
            print('TIMEOUT PASSWORD?', (datetime.today() - current_user.password_list.last_changed).days > 90)
            if (datetime.today() - current_user.password_list.last_changed).days > 90:
                current_user.validated = False
                db.session.add(current_user)
                db.session.commit()
                flash('You haven\'t changed your password in 90 days. You must re-validate your account')
                return redirect(url_for('auth.change_password'))
            return redirect(request.args.get('next') or url_for('main.index'))
        if user:
            current_app.logger.info(user.email + ' failed to log in: Invalid username or password')
            user.login_attempts += 1
            db.session.add(user)
            db.session.commit()
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form, reset_url=url_for('auth.password_reset_request'))


@auth.route('/logout')
@login_required
def logout():
    """
    HTML page to logout a user, immediately redirects to index.
    :return: Index page.
    """
    current_app.logger.info(current_user.email + ' logged out')
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Password change page"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(pwhash=current_user.password_list.p1, password=form.password.data) or \
            check_password_hash(pwhash=current_user.password_list.p2, password=form.password.data) or \
            check_password_hash(pwhash=current_user.password_list.p3, password=form.password.data) or \
            check_password_hash(pwhash=current_user.password_list.p4, password=form.password.data) or \
                check_password_hash(pwhash=current_user.password_list.p5, password=form.password.data):
            current_app.logger.info(current_user.email + 'tried to change password. Failed: Used old password.')
            flash("You cannot repeat passwords")
        elif check_password_requirements(current_user.email,
                form.old_password.data,
                form.password.data,
                form.password2.data):
            current_user.password_list.update(current_user.password_hash)
            current_user.password = form.password.data
            current_user.validated = True
            db.session.add(current_user)
            db.session.commit()
            current_app.logger.info(current_user.email + 'changed their password.')
            flash('Your password has been updated.')
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
        current_app.logger.info('Tried to submit a password reset request with account email ' + form.email.data)
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
            current_app.logger.info('Sent password reset instructions to ' + form.email.data)
            flash('An email with instructions to reset your password has been sent to you.')
        else:
            current_app.logger.info('Requested password reset for e-mail ' + form.email.data +
                                    ' but no such account exists')
            flash('An account with this email was not found in the system.')
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
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        current_app.logger.info('Requested password reset for e-mail ' + form.email.data +
                                ' but no such account exists')
        if user.reset_password(token, form.password.data):
            user.login_attempts = 0
            db.session.add(user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('Password must be at least 8 characters with at least 1 UPPERCASE and 1 NUMBER')
    return render_template('auth/reset_password.html', form=form)