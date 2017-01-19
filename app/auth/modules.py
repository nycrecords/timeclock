"""
.. module:: auth.views.

   :synopsis: Handles all authentication URL endpoints for the
   TimeClock application
"""

import re
import sqlalchemy

from flask import flash, current_app
from flask_login import current_user
from werkzeug.security import check_password_hash
from datetime import datetime

from .. import db
from ..email_notification import send_email
from ..models import User, Role, ChangeLog
from ..utils import tags


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


def get_changelog_by_user_id(id):
    """
    Obtains a changelog based on a user's id.
    :param id: The id of the user whose changelog is being queried for.
    :return: [BaseQuery] A ChangeLog query. We return a query to leverage the pagination macro.
    """
    current_app.logger.info('Start function get_changelog_by_user_id()')
    current_app.logger.info('Querying for changes made to user with id {}'.format(id))
    changes = ChangeLog.query.filter_by(user_id=id).order_by(sqlalchemy.desc(ChangeLog.timestamp))
    current_app.logger.info('End function get_changelog_by_user_id()')
    return changes


def update_user_information(user,
                            first_name_input,
                            last_name_input,
                            division_input,
                            tag_input,
                            supervisor_email_input,
                            is_supervisor_input,
                            role_input,
                            budget_code_input,
                            object_code_input,
                            object_name_input
                            ):
    """
    To be used in the user_profile view function to update a user's information in the database.
    :param user: The user whose information to update (must be a user object)
    :param first_name_input: New first name for user.
    :param last_name_input: New last name for user.
    :param division_input: New division for user.
    :param tag_input: New tag for user.
    :param supervisor_email_input: Email of the user's new supervisor.
    :param is_supervisor_input: Whether or not the user is a supervisor
    :return: None
    """
    current_app.logger.info('Start function update_user_information for {}'.format(user.email))
    if first_name_input and first_name_input != '' and (user.first_name != first_name_input):
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='FIRST NAME',
                           old=user.first_name,
                           new=first_name_input)
        db.session.add(change)
        db.session.commit()
        user.first_name = first_name_input

    if last_name_input and last_name_input != '' and (user.last_name != last_name_input):
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='LAST NAME',
                           old=user.last_name,
                           new=last_name_input)
        db.session.add(change)
        db.session.commit()
        user.last_name = last_name_input

    if division_input and division_input != '' and (user.division != division_input):
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='DIVISION',
                           old=user.division,
                           new=division_input)
        db.session.add(change)
        db.session.commit()
        user.division = division_input

    if tag_input and user.tag_id != tag_input:
        if user.tag_id:
            old_tag = tags[user.tag_id][1]
        else:
            old_tag = 'None'
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='TAG_INPUT',
                           old=old_tag,
                           new=tags[tag_input][1])
        db.session.add(change)
        db.session.commit()
        user.tag_id = tag_input

    if supervisor_email_input and supervisor_email_input != '' and user.supervisor.id != supervisor_email_input:
        sup = User.query.filter_by(id=supervisor_email_input).first()
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='SUPERVISOR',
                           old=user.supervisor.email,
                           new=sup.email)
        db.session.add(change)
        db.session.commit()
        sup = User.query.filter_by(id=supervisor_email_input).first()
        user.supervisor = sup


    if is_supervisor_input and (user.is_supervisor != is_supervisor_input):
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='IS SUPERVISOR',
                           old=user.is_supervisor,
                           new=is_supervisor_input)
        db.session.add(change)
        db.session.commit()
        user.is_supervisor = is_supervisor_input

    if budget_code_input and budget_code_input != '' and user.budget_code != budget_code_input:
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='BUDGET CODE',
                           old=user.budget_code,
                           new=budget_code_input)
        db.session.add(change)
        db.session.commit()
        user.budget_code = budget_code_input

    if object_code_input and object_code_input != '' and user.object_code != object_code_input:
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='OBJECT CODE',
                           old=user.object_code,
                           new=object_code_input)
        db.session.add(change)
        db.session.commit()
        user.object_code = object_code_input

    if object_name_input and object_name_input != '' and user.object_name != object_name_input:
        change = ChangeLog(changer_id=current_user.id,
                           user_id=user.id,
                           timestamp=datetime.now(),
                           category='OBJECT NAME',
                           old=user.object_name,
                           new=object_name_input)
        db.session.add(change)
        db.session.commit()
        user.object_name = object_name_input

    if role_input and role_input != user.role_id:
        new_role = Role.query.filter_by(name=role_input).first()
        if user.role != new_role:
            change = ChangeLog(changer_id=current_user.id,
                               user_id=user.id,
                               timestamp=datetime.now(),
                               category='ROLE',
                               old=user.role.name,
                               new=new_role.name)
            db.session.add(change)
            db.session.commit()
            user.role = Role.query.filter_by(name=role_input).first()

    db.session.add(user)
    db.session.commit()
    current_app.logger.info('End function update_user_information')