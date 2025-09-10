from flask import Blueprint

# Blueprint for health screen module
health_screen_bp = Blueprint("health_screen", __name__)

# Register routes
from app.health_screen import views  # noqa: E402,F401

