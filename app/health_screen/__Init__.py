from flask import Blueprint, session

health_screen_bp = Blueprint("health_screen", __name__)

from app.health_screen import views
from app.models import HealthScreenResults, HealthScreenUsers
