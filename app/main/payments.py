from ..models import User, Tag, Pay
from datetime import datetime, date
import sqlalchemy
from flask import current_app


def get_payrate_before_or_after(email_input, start, before_or_after):
    """
    Gets the pay object before the provided start date,
    :param email_input: Email of the user whose pays to query through.
    :param start: Start date - the query will search for the pay with a start date closest (but before)
    to this date.
    :param before_or_after: [Boolean] True to get payrate before date, False to get payrate after date
    :return: An object from the pay table.
    """
    current_app.logger.info('Start function get_pay_before()')
    current_app.logger.info('Querying for user with given e-mail: {}'.format(email_input))
    user = User.query.filter_by(email=email_input).first()
    current_app.logger.info('Finished querying for user with given e-mail')
    if user:
        current_app.logger.info('User {} was found in database'.format(email_input))
        current_app.logger.info('Querying for most recent pay for user {}'.format(email_input))
        pay_query = Pay.query.filter(Pay.user_id == user.id)
        if before_or_after:
            p = pay_query.filter(Pay.start <= start).order_by(sqlalchemy.desc(Pay.start)).first()
            # Get the first payment before the given date
        else:
            p = pay_query.filter(Pay.start >= start).first()
            # Get the first payment after the given date
        if not p:
            current_app.logger.error('No pay for user {} exists before date {}'
                                     .format(email_input, start))
        current_app.logger.info('Finished querying for most recent pay for user {}'.
                                format(email_input))
    else:
        current_app.logger.error('User with email {} was not found in database. Aborting...'
                                 .format(email_input))
        p = None
    current_app.logger.info('End function get_pay_before()')
    return p


def calculate_hours(email_input, start, end):
    """
    Calculates the hours worked by a user between two dates.
    :param email_input: Email of employee whose hours are to be calculated.
    :param start: The date
    :return: [FLOAT] The number of hours worked within the given period
    """
    from .modules import get_events_by_date
    events = get_events_by_date(email_input, start, end)
    current_app.logger.info('Start function calculate_hours()')
    events = sorted(events)
    if len(events) % 2 != 0:
        events.pop(0)
    events = sorted(events)

    total_hours = 0

    # Looping through events array to get hours between neighboring events
    for x in range(0, len(events), 2):

        event = events[x]
        print(event)
        next_event = events[x + 1]
        time_in = event[:event.index('|') - 1]
        time_out = next_event[:next_event.index('|') - 1]
        time_in_datetime = datetime.strptime(time_in, "%b %d, %Y %H:%M:%S %p")
        time_out_datetime = datetime.strptime(time_out, "%b %d, %Y %H:%M:%S %p")
        hours_this_day = (time_out_datetime - time_in_datetime).seconds / 3600
        print('HOURS ON {}: {}'.format(time_in_datetime, hours_this_day))
        total_hours += hours_this_day
        print('TOTAL HOURS: {}'.format(total_hours))

    current_app.logger.info('End function calculate_hours')
