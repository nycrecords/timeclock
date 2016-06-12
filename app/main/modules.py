from flask import render_template, session, redirect, url_for, current_app, flash
from .. import db
from ..models import User, Event
from ..email import send_email
from _datetime import datetime
from . import main
from flask_login import login_required, current_user
from .forms import ClockInForm, ClockOutForm


def process_clock(note_data):
    """
    Creates an Event and writes it to the database when a user clocks in or out.
    :param note_data: The note associated with a ClockInForm or ClockOutForm [string]
    :return: None
    """
    event = Event(type=not current_user.clocked_in, time=datetime.utcnow(), user_id=current_user.id,
                  note=note_data)
    current_user.clocked_in = not current_user.clocked_in
    db.session.add(current_user)
    db.session.add(event)
    db.session.commit()


def set_clock_form():
    """
    For use in main/views.py: Determine the type of form to be rendered to index.html.
    :return: ClockInForm if user is clocked out. ClockOutForm if user is clocked in
    """
    if current_user.clocked_in:
        form = ClockOutForm()
    else:
        form = ClockInForm()
    return form


def get_last_clock():
    """
    Obtains the last clock in or clock out instance created by this user.
    :return: Formatted time of last clock event
    """
    return Event.query.filter_by(user_id=current_user.id).first().time.strftime("%b %d, %Y | %l:%M:%S %p")
    # This shows first time event, need last time. .last() doesn't work
    # TODO: find alternatives when you have internet connection


def get_events_by_username(username_input):
    user_account = User.query.filter_by(username=username_input).first()
    events = Event.query.filter_by(user_id=user_account.id).all()  # THIS DOESN'T WORK
    return events

