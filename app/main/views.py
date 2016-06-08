from flask import render_template, session, redirect, url_for, current_app, flash
from .. import db
from ..models import User, Event
from ..email import send_email
from _datetime import datetime
from . import main
from flask_login import login_required, current_user
from .forms import ClockInForm, ClockOutForm
from .modules import process_clock, set_clock_form


@main.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:  # Don't pass a form
        return render_template('index.html')

    form = set_clock_form()

    if form.validate_on_submit():
        process_clock(form.note.data)

    form = set_clock_form()

    return render_template('index.html', form=form)


@main.route('/clock')
@login_required
def clock():
    return render_template('clock.html')


@main.route('/history')    # User history
@login_required
def history():
    events = Event.query.filter_by(user_id=current_user.id).all()
    return render_template('history.html', events=events)


@main.route('/timepunch')
@login_required
def timepunch():
    # TODO: IMPLEMENT FORM TO SUBMIT TIMEPUNCH
    return render_template('timepunch.html')


