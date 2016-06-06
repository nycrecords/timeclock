from flask import render_template, session, redirect, url_for, current_app
from .. import db
from ..models import User
from ..email import send_email
from . import main
#from .forms import <FORM NAME HERE>

@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')
