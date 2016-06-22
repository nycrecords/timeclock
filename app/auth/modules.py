from datetime import datetime
from werkzeug.security import check_password_hash
from ..models import User
from flask_login import current_user
from .. import db
import re


def get_day_of_week():
    """
    Gets the current day of the week.
    :return: The current day of the week as a string.
    """
    date_int_to_str = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }
    return date_int_to_str[datetime.today().weekday()]


def check_password_requirements(email, old_password, password, password_confirmation):
    """
    Check a password against security requirements.

    :param email: Email of user
    :param old_password: Original password
    :param password: Password that needs to be checked.
    :param password_confirmation: Confirmation of new password
    :return: Boolean (True if valid, False if not)
    """

    user_password = User.query.filter_by(email=email).first().password_hash

    if not check_password_hash(pwhash=user_password, password=old_password):
        return False

    if password != password_confirmation:
        return False

    if not re.match(r'^(?=.*?\d)(?=.*?[A-Z])(?=.*?[a-z])[A-Za-z\d]{8,128}$', password):
        return False

    return True

