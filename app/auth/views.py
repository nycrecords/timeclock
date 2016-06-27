from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from . import auth
from .. import db
from ..models import User
from ..decorators import admin_required
from ..email import send_email
from .forms import LoginForm, RegistrationForm, AdminRegistrationForm, PasswordResetForm, PasswordResetRequestForm, ChangePasswordForm
from .modules import get_day_of_week, check_password_requirements
from datetime import datetime


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
        user = User(email=form.email.data,
                    password=temp_pass,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    )
        db.session.add(user)
        db.session.commit()
        flash('User successfully registered')
    return render_template('auth/admin_register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renders the HTML page where users can log in to the system. If a login is successful, users are redirected to
    the index page.
    :return:
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form, reset_url=url_for('auth.password_reset_request'))


@auth.route('/logout')
@login_required
def logout():
    """
    HTML page to logout a user, immediately redirects to index.
    :return: Index page.
    """
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Password change page"""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_requirements(current_user.email,
                                       form.old_password.data,
                                       form.password.data,
                                       form.password2.data):
            current_user.password_list.update(current_user.password_hash)
            current_user.password = form.password.data
            current_user.validated = True
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('Password must be at least 8 characters with at least 1 UPPERCASE and 1 NUMBER')
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
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, 'Reset Your Password',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
            flash('An email with instructions to reset your password has been sent to you.')
        else:
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
        if user.reset_password(token, form.password.data):
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            flash('Password must be at least 8 characters with at least 1 UPPERCASE and 1 NUMBER')
    return render_template('auth/reset_password.html', form=form)


@auth.route('/unconfirmed', methods=['GET', 'POST'])
def unconfirmed():
    """
    View function for unconfirmed users to change their passwords and re-confirm their accounts. Once users have changed
    their password, they become confirmed.
    :return: HTML page containing a form for users to change their password.
    """
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_requirements(current_user.email,
                                       form.old_password.data,
                                       form.password.data,
                                       form.password2.data):
            current_user.password = form.password.data
            current_user.validated = True  # TODO: Check to ensure this actually does validate users
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html', form=form)