from flask import render_template, session, redirect, url_for, current_app, flash
from .. import db
from ..models import User
from ..email import send_email
from _datetime import datetime
from . import main
from flask_login import login_required
from .forms import ClockInForm, ClockOutForm


clocked_in = True

@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', current_app=current_app)



@main.route('/history')                         # User history
def history():
    return render_template('history.html')


@main.route('/timepunch')
def timepunch():
    # TODO: IMPLEMENT FORM TO SUBMIT TIMEPUNCH
    return render_template('timepunch.html')


