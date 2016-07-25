"""
.. module:: main.timepunch.

   :synopsis: Handles all communication with the database when adding, querying, or modifying timepunches.
   timeclock application
"""
from .. import db
from ..models import User, Event
from ..email_notification import send_email
from flask_login import current_user
from flask import current_app



def create_timepunch(punch_type, punch_time, reason):
    """
    Creates a timepunch, adds it to the database, and sends an email to the appropriate user so
    that it may be approved or denied.
    :param: punch_type: [String] type of requested punch (True for in, False for out)
    :param punch_time: [datetime] time of requested punch
    :param reason: [string] reason for timepunch submission
    :return: None
    """
    current_app.logger.info('Start function create_timepunch()')
    punch_type = punch_type is 'True'  # must manually cast string to bool because
    print('PUNCH TYPE IN CREATE_TIMEPUNCH', punch_type)
    # wtforms does not support this functionality (assigns any non-empty string to True)
    e = Event(time=punch_time, type=punch_type, note=reason, user=current_user, timepunch=True, approved=False)
    db.session.add(e)
    db.session.commit()
    send_email(current_user.supervisor.email,
               'TimePunch Request from {} {}'.format(current_user.first_name, current_user.last_name),
               '/main/email/request_timepunch',
               user=current_user, punch_time=punch_time, type=punch_type, note=reason)


def get_timepunches_for_review(user_email):
    """
    Queries the database for a list of timepunch requests that need to be approved or denied.
    :param user_email: The email of the supervisor.
    :return: A list of timepunch requests.
    """
    current_app.logger.info('Start function get_timepunches_for_review()')
    u = User.query.filter_by(email=user_email).first()
    current_app.logger.info('Querying for timepunches submitted to {}'.format(user_email))
    timepunch_query = Event.query.join(User).filter_by(supervisor=u).filter(Event.timepunch == True).order_by(Event.id)
    current_app.logger.info('Finished querying for timepunches')

    result = timepunch_query.all()
    if not result:
        current_app.logger.info('No timepunches found for user {}'.format(user_email))

    current_app.logger.info('End function get_timepunches_for_review')
    return timepunch_query.all()


def approve_or_deny(event_id, approve=False):
    current_app.logger.info('Start function approve_or_deny()')
    from .modules import get_event_by_id
    e = get_event_by_id(event_id)
    if approve:
        e.approved = True
    else:
        e.approved = False
    db.session.add(e)
    db.session.commit()
    current_app.logger.info('End function approve_or_deny()')
