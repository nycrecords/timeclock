from flask import Blueprint, session

from . import views, errors
from ..models import Permission

main = Blueprint('main', __name__)



@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)


@main.before_request
def func():
    session.modified = True
