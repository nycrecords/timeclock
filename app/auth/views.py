from flask import render_template
from flask_login import login_required
from . import auth
from .forms import LoginForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    return render_template('auth/login.html', form=form)


@auth.route('/secret')
@login_required
def secret():
    return 'Only authenticated users are allowed!'
