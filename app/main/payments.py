from ..models import User, Pay
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
            p = pay_query.filter(Pay.start < start).order_by(sqlalchemy.desc(Pay.start)).first()
            # Get the first payment before the given date
        else:
            p = pay_query.filter(Pay.start > start).first()
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


def calculate_hours_worked(email_input, start, end):
    """
    Calculates the hours worked by a user between two dates.
    :param email_input: Email of employee whose hours are to be calculated.
    :param start: The date
    :return: [FLOAT] The number of hours worked within the given period
    """
    current_app.logger.info('Start function calculate_hours()')
    from .modules import get_events_by_date
    events = get_events_by_date(email_input, start, end).all()
    if len(events) % 2 != 0:
        events.pop(0)

    # Order from oldest to most recent
    events.reverse()

    # List of dictionaries of day info to return
    all_info = {
        'days_list': [],
        'total_hours': 0,
        'total_earnings': 0
    }

    # Looping through events array to get hours between neighboring events
    for x in range(0, len(events), 2):
        event = events[x]
        next_event = events[x + 1]
        time_in = event.time
        time_out = next_event.time
        payrate_this_day = get_payrate_before_or_after(email_input, time_in.date(), True)
        hours_this_day = (time_out - time_in).seconds / float(3600)
        day_dict = {
            'date': time_in.strftime('%a %b %d, %Y'),
            'time_in': time_in.strftime('%H:%M'),
            'time_out': time_out.strftime('%H:%M'),
            # If a user has been clocked in for over five hours, automatically subtract an hour for lunch
            'hours': hours_this_day - 1 if hours_this_day >= 5 else hours_this_day,
            'rate': payrate_this_day.rate,
            'earnings': hours_this_day * payrate_this_day.rate
        }

        all_info['days_list'].append(day_dict)
        all_info['total_hours'] += day_dict['hours']
        all_info['total_earnings'] += day_dict['earnings']

    current_app.logger.info('End function calculate_hours')
    return all_info
