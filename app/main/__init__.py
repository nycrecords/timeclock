from flask import Blueprint, session, jsonify

main = Blueprint("main", __name__)

from app.main import views, errors
from app.models import Permission


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)


@main.before_request
def func():
    session.modified = True

# Quell Chrome devtools probe logs
@main.route("/.well-known/appspecific/com.chrome.devtools.json")
def chrome_devtools_probe():
    return jsonify({})
