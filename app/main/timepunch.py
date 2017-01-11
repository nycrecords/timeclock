"""
.. module:: main.timepunch.

   :synopsis: Handles all communication with the database when adding, querying, or modifying timepunches.
   timeclock application
"""
import sqlalchemy
from flask import current_app
from flask_login import current_user

from .. import db
from ..email_notification import send_email
from ..models import User, Event


def create_timepunch(punch_type, punch_time, reason):
    """
    Creates a timepunch, adds it to the database, and sends an email to the appropriate user so
    that it may be approved or denied.
    :param punch_type: [String] type of requested punch (True for in, False for out)
    :param punch_time: [datetime] time of requested punch
    :param reason: [string] reason for timepunch submission
    :return: None
    """
    current_app.logger.info('Start function create_timepunch()')
    punch_type = punch_type == 'In'  # Must manually cast string to bool because wtf doesn't support coerce bool
    event = Event(time=punch_time, type=punch_type, note=reason, user=current_user, timepunch=True, approved=False,
                  pending=True)
    db.session.add(event)
    db.session.commit()
    send_email(current_user.supervisor.email,
               'TimePunch Request from {} {}'.format(current_user.first_name, current_user.last_name),
               '/main/email/request_timepunch',
               user=current_user, punch_time=punch_time, type=punch_type, note=reason)


def get_timepunches_for_review(user_email, filter_by_email=None, approved=None, status=None):
    """
    Queries the database for a list of timepunch requests that need to be approved or denied.
    :param user_email: The email of the supervisor.
    :param filter_by_email: The email of a specific user for optional filters.
    :param approved: [String] Approved, Unapproved, All. Used for more precise filtering.
    :param status: [String] Pending, Processed, All. Used for more precise filtering.
    :return: A query of all timepunch requests for the given user
    """
    current_app.logger.info('Start function get_timepunches_for_review()')
    u = User.query.filter_by(email=user_email).first()
    current_app.logger.info('Querying for timepunches submitted to {}'.format(user_email))
    timepunch_query = Event.query.join(User).filter_by(supervisor=u).filter(Event.timepunch == True).order_by(Event.id)
    current_app.logger.info('Finished querying for timepunches')

    # Filter by emails if user provides an email
    if filter_by_email and filter_by_email != '':
        u = User.query.filter_by(email=filter_by_email).first()
        if u:
            timepunch_query = timepunch_query.filter(Event.user_id == u.id)
        else:
            current_app.logger.error('Tried to filter timepunches from {} but no such account'
                                     'exists'.format(filter_by_email))

    # Filter by status if user provides a status
    if approved:
        if approved == 'Approved':
            timepunch_query = timepunch_query.filter(Event.approved == True)
        elif approved == 'Unapproved':
            timepunch_query = timepunch_query.filter(Event.approved == False)
            # else approved == 'All', in which case we don't need to add anything to the filter

    if status:
        if status == 'Pending':
            timepunch_query = timepunch_query.filter(Event.pending == True)
        elif status == 'Processed':
            timepunch_query = timepunch_query.filter(Event.pending == False)
            # else status == 'All', in which case we don't need to add anything to the filter

    # Check to make sure something is returned by the query
    result = timepunch_query.all()
    if not result:
        current_app.logger.error('No timepunches found for user {}'.format(user_email))

    # Last step: order timepunches by id
    timepunch_query = timepunch_query.order_by(sqlalchemy.desc(Event.id))

    current_app.logger.info('End function get_timepunches_for_review')
    return timepunch_query


def approve_or_deny(event_id, approve=False):
    """
    Approve or deny an event.
    :param event_id: [int] Id of the event to be marked as approved or unapproved.
    :param approve: [bool] True to approve the event, False to unapprove
    :return: Nothing.
    """
    current_app.logger.info('Start function approve_or_deny()')
    from .modules import get_event_by_id
    event = get_event_by_id(event_id)
    if approve:
        event.approved = True
    else:
        event.approved = False
    event.pending = False
    db.session.add(event)
    db.session.commit()
    current_app.logger.info('End function approve_or_deny()')
