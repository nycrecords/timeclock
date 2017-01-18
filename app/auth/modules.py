"""
.. module:: auth.views.

   :synopsis: Handles all authentication URL endpoints for the
   TimeClock application
"""

import re

from flask import flash, current_app
from flask_login import current_user
from werkzeug.security import check_password_hash

from .. import db
from ..email_notification import send_email
from ..models import User, Role



def check_password_requirements(email, old_password, password, password_confirmation):
    """
    Check a password against security requirements.

    :param email: Email of user
    :param old_password: Original password
    :param password: Password that needs to be checked.
    :param password_confirmation: Confirmation of new password
    :return: Whether or not the new password is valid [Boolean]
    """

    user_password = User.query.filter_by(email=email).first().password_hash

    if not check_password_hash(pwhash=user_password, password=old_password):
        # If the user enters the wrong current password
        current_app.logger.info('{} tried to change their password but failed: entered invalid old password'.format(
                                current_user.email))
        flash('Your old password did not match', category='warning')
        return False
    if password != password_confirmation:
        current_app.logger.info('{} tried to change their password but failed: passwords did not match'.format(
                                current_user.email))
        return False

    # Use a score based system to ensure that users match password security requirements
    score = 0
    if re.search('\d+', password):
        # If the password contains a digit, increment score
        score += 1
    if re.search('[a-z]', password) and re.search('[A-Z]', password):
        # If the password contains lowercase and uppercase letters, increment score
        score += 1
    if score < 2:
        current_app.logger.info('{} tried to change their password but failed: new password missing uppercase letter '
                                'or number'.format(current_user.email))
        flash('Your new password must contain eight characters and at least one uppercase letter and one number',
              category='warning')
        return False

    return True


def get_supervisors_for_division(div):
    """
    Gets a list of all the supervisors for a division
    :param div: The division
    :return: A list of users who are supervisors for the division
    """
    users = User.query.filter_by(division=div).filter_by(is_supervisor=True).all()
    return [(user.id, user.email) for user in users]


def _send_new_user_email(user, temp_password):
        """
        Sends a user an email instructing them on how to set up their new account.
        :param user: The user to send the email to
        :param temp_password: The initial temporary password the user is sent to sign up with
        :return: None
        """
        send_email(user.email,
                   'DORIS TimeClock - New User Registration',
                   'auth/email/new_user',
                   user=user,
                   temp_password=temp_password)
        current_app.logger.info('Sent login instructions to {}'.format(user.email))


def create_user(email, password, first, last, div, role, tag, is_sup, sup, budget_code=None, object_code=None,
                object_name=None):
    """
    Creates a user and adds it to the database. Also updates the user's password_list and emails instructions if the user
    is new.
    :param email: User's email
    :param password: User's password
    :param first: User's first name
    :param last: User's last name
    :param div: User's division
    :param role: User's role
    :param tag: User's tag [int]
    :param is_sup: User's status as a supervisor [bool]
    :param sup: User's supervisor's id [int]
    :param budget_code: User's budget code
    :param object_code: User's object code
    :param object_name: User's object name
    :return: None
    """
    role_obj = Role.query.filter_by(name=role).first()
    sup_obj = User.query.filter_by(id=sup).first()
    u = User(email=email, first_name=first, last_name=last, password=password,
             division=div, role=role_obj, tag_id=tag, is_supervisor=is_sup, supervisor=sup_obj, budget_code=budget_code,
             object_code=object_code, object_name=object_name)
    db.session.add(u)
    db.session.commit()
    u.password_list.update(u.password_hash)
    _send_new_user_email(u, password)
    current_app.logger.info('{} successfully registered user with email {}'.format(current_user.email, u.email))
    return u.email
