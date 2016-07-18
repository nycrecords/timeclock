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

    total_hours = 0

    # Looping through events array to get hours between neighboring events
    for x in range(0, len(events), 2):

        event = events[x]
        print(event)
        next_event = events[x + 1]
        time_in = event.time
        time_out = next_event.time
        hours_this_day = (time_out - time_in).seconds / 3600
        print('HOURS ON {}: {}'.format(time_in, hours_this_day))
        total_hours += hours_this_day
        print('TOTAL HOURS: {}'.format(total_hours))

    current_app.logger.info('End function calculate_hours')
    return total_hours


def calculate_earnings(email_input, first_date, last_date):
    """
    Calculates an employee's earnings over a given period.
    :param email_input: email of the employee whose earnings to calculate
    :param first_date: Beginning of pay period
    :param last_date: End of pay period
    :return: [FLOAT] The amount an employee has earned within the period (USD)
    """
    current_app.logger.info('Start function calculate_earnings()')
    total_earnings = 0
    # Set current payrate to first payrate before or on the beginning of the pay period
    current_pay_rate = get_payrate_before_or_after(email_input, first_date, True)
    done = False
    begin_date = first_date
    while not done and current_pay_rate.start < last_date:
        # Set the next payrate to the first payrate after the end of the pay period
        next_pay_rate = get_payrate_before_or_after(email_input, current_pay_rate.start, False)
        print('NEXT_PAY_RATE:', next_pay_rate)
        if next_pay_rate and next_pay_rate.start < last_date:
            # Multiple pay rates within the same period

            # So we calculate the hours between the start of the period and the start of the
            # next pay rate:
            hours_worked = calculate_hours_worked(email_input, begin_date, next_pay_rate.start)
            print('HOURS WORKED:', hours_worked)

            # Add amount earned within this time period
            total_earnings += current_pay_rate.rate * hours_worked
            print('TOTAL EARNINGS:', total_earnings)

            # Set the current pay date to the next pay date within the pay period
            current_pay_rate = next_pay_rate
            print('CURRENT PAY RATE:', current_pay_rate)

            # Set the first_date of the pay_period to the first date after the end of the last pay_period
            begin_date = current_pay_rate.start
            print('BEGIN DATE:', begin_date)
        else:
            # First pay rate applies to the entire period
            hours_worked = calculate_hours_worked(email_input, first_date, last_date)
            total_earnings += current_pay_rate.rate * hours_worked
            # Exit the loop
            done = True
    current_app.logger.info('End function calculate_earnings')
    return total_earnings




