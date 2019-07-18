# -*- coding: utf-8 -*-
"""The public module, including the homepage and user auth."""
from . import views, errors # noqa
from flask import Blueprint, session

main = Blueprint('main', __name__)

from timeclock.user.models import Permission


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)


@main.before_request
def func():
    session.modified = True
