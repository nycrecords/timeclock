from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required, login_user, logout_user
from . import auth
from .. import db
from ..models import User
from ..decorators import admin_required
from .forms import LoginForm, RegistrationForm, AdminRegistrationForm
from .modules import get_day_of_week
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
                        last_name=form.last_name.data)
            db.session.add(user)
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
        print("Temporary Password: " + get_day_of_week() + str(datetime.today().day))
        user = User(email=form.email.data,
                    password=get_day_of_week() + str(datetime.today().day),
                    first_name=form.first_name.data,
                    last_name=form.last_name.data)
        db.session.add(user)
        flash('User successfully registered')
        return redirect(url_for('auth.login'))
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
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """
    HTML page to logout a user, immediately redirects to index.
    :return: Index page.
    """
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))
