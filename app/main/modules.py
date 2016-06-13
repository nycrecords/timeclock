from flask import render_template, session, redirect, url_for, current_app, flash
from .. import db
from ..models import User, Event
from ..email import send_email
from datetime import datetime, timedelta
from . import main
from flask_login import login_required, current_user
from .forms import ClockInForm, ClockOutForm
import sqlalchemy


def process_clock(note_data):
    """
    Creates an Event and writes it to the database when a user clocks in or out.
    :param note_data: The note associated with a ClockInForm or ClockOutForm [string]
    :return: None
    """
    event = Event(type=not current_user.clocked_in, time=datetime.now(), user_id=current_user.id,
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
    # This shows first time event, need last time. .last() doesn't work
    # TODO: find alternatives when you have internet connection
    if Event.query.filter_by(user_id=current_user.id).first() is not None:
        return Event.query.filter_by(user_id=current_user.id).order_by(sqlalchemy.desc(Event.time)).first().time.strftime("%b %d, %Y | %l:%M:%S %p")


def get_events_by_date(email_input=None, first_date=datetime(2004, 1, 1), last_date=datetime.now()):
    """
    Filters the Events table for events granted by an (optional) user from an (optional) begin_date to an (optional)
    end date.

    :param email_input: username to search for
    :param first_date: the start date to return queries from
    :param last_date: the end date to query (must be after first date)
    :return: array of Event objects from a given user between two given dates
    """

    #  What to do if form date fields are left blank
    # if first_date is None:
    #     first_date = datetime(2004, 1, 1)   # First possible clock-in date
    # if last_date is None:
    #     last_date = datetime.now()          # Last possible clock-in date
    # TODO: CHECK WITH JOEL TO SEE IF ABOVE CODE IS STILL NEEDED

    events_query = db.session.query(Event).filter(
        Event.time >= first_date,
        Event.time <= last_date)

    #  User processing
    if email_input is not None and User.query.filter_by(email=email_input).first() is not None:
        user_id = User.query.filter_by(email=email_input).first().id
        events_query = events_query.filter(Event.user_id == user_id)

    return events_query.all()


