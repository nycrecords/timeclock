from flask import render_template, session, redirect, url_for, current_app, flash
from .. import db
from ..models import User, Event
from ..email import send_email
from _datetime import datetime
from . import main
from flask_login import login_required, current_user
from .forms import ClockInForm, ClockOutForm


@main.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:  # Not sure if this is the best approach
        return render_template('index.html')

    if current_user.clocked_in: # How can I avoid using this twice?
        form = ClockOutForm()
    else:
        form = ClockInForm()

    if form.validate_on_submit():
        event = Event(type=not current_user.clocked_in, time=datetime.utcnow(), user_id=current_user.id,
                      note=form.note.data)
        current_user.clocked_in = not current_user.clocked_in
        db.session.add(current_user)
        db.session.add(event)
        db.session.commit()
    if current_user.clocked_in:  # Some bad code repetition here - any thoughts?
        form = ClockOutForm()
    else:
        form = ClockInForm()

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


