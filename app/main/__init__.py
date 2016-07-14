from flask import Blueprint, session

main = Blueprint('main', __name__)

from . import views, errors
from app.models import Permission

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)


@main.before_request
def func():
    session.modified = True
