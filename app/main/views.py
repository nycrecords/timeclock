from flask import render_template, session, redirect, url_for, current_app, flash
from datetime import datetime
from .. import db
from ..models import User, Event
from ..email import send_email
from . import main
from flask_login import login_required, current_user
from .modules import process_clock, set_clock_form, get_last_clock, get_events_by_username, get_events_by_date
from ..decorators import admin_required, permission_required
from ..models import Permission
from .forms import AdminFilterEventsForm, UserFilterEventsForm


@main.route('/', methods=['GET', 'POST'])
def index():
    if not current_user.is_authenticated:  # Don't pass a form
        return render_template('index.html')
    last_event = get_last_clock()
    form = set_clock_form()

    if form.validate_on_submit():
        process_clock(form.note.data)

    form = set_clock_form()

    return render_template('index.html', form=form, last_event=last_event)


@main.route('/all_history',  methods=['GET', 'POST'])
@permission_required(Permission.ADMINISTER)
def all_history():
    form = AdminFilterEventsForm()
    events = Event.query.all()
    if form.validate_on_submit():
        events = get_events_by_date(form.username.data, form.first_date.data, form.last_date.data)
    return render_template('all_history.html', events=events, form=form)


@main.route('/history')    # User history
@login_required
def history():
    events = Event.query.filter_by(user_id=current_user.id).all()
    return render_template('history.html', events=events)


