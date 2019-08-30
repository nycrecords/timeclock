"""
.. module:: main.views.

   :synopsis: Handles all core URL endpoints for the timeclock application
"""

from datetime import datetime

from flask import current_app
from flask import (
    render_template,
    flash,
    request,
    url_for,
    redirect,
    session,
    make_response
)
from flask_login import login_required, current_user

from . import main
from .forms import (
    AdminFilterEventsForm,
    UserFilterEventsForm,
    CreatePayRateForm,
    TimePunchForm,
    ApproveOrDenyForm,
    FilterTimePunchForm,
    ClearForm,
    AddEventForm,
    DeleteEventForm,
    GenerateMultipleTimesheetsForm,
    RequestVacationForm,
    FilterVacationForm,
    ExportForm
)
from .modules import (
    process_clock,
    set_clock_form,
    get_last_clock,
    get_events_by_date,
    get_clocked_in_users,
    get_time_period,
    process_time_periods,
    get_all_tags,
    check_total_clock_count,
    add_event,
    delete_event,
    generate_timesheet,
    generate_timesheets,
    create_csv
)
from .payments import (
    get_payrate_before_or_after,
    calculate_hours_worked
)
from .requests import (
    create_timepunch,
    get_timepunches_for_review,
    get_vacations_for_review,
    approve_or_deny,
    approve_or_deny_vacation
)
from .. import db
from ..decorators import admin_required
from ..models import Pay, User, Vacation
from app.utils import eval_request_bool


@main.route('/', methods=['GET', 'POST'])
def index():
    """
    View function for index page. Reroutes to login if user is not logged in.
    :return: index.html contents
    """
    current_app.logger.info('Start function index() [VIEW]')
    if not current_user.is_authenticated:  # Don't pass a form
        current_app.logger.error('Anonymous user visited index. Redirecting to /auth/login...')
        return redirect(url_for('auth.login'))

    if not current_user.validated:
        current_app.logger.info('{} visited index but is not validated. Redirecting to /auth/change_password'.
                                format(current_user.email))
        current_app.logger.info('End function index')
        return redirect(url_for('auth.change_password'))

    form = set_clock_form()
    if form.validate_on_submit():
        if form.note.data is not None and len(form.note.data) > 60:
            flash("Your note cannot exceed 60 characters", category='warning')
            current_app.logger.error('{} submitted a note that exceeded 60 characters'.format(current_user.email))
        else:
            ip = request.environ['REMOTE_ADDR']
            time = datetime.now()

            # Stores the time and the ip clocked in form
            process_clock(form.note.data, ip)
            flash("Clock submission successfully processed", category='success')

    last = get_last_clock()
    last_time = last.time.strftime("%b %d, %Y | %H:%M") if last else ""
    last_type = last.type if last else False
    current_app.logger.info('End function index')
    return render_template('main/index.html',
                           form=set_clock_form(),
                           last_event=last_time,
                           clocked_in_users=get_clocked_in_users(),
                           last_clock_event=last_type
                           )


@main.route('/all_history', methods=['GET', 'POST'])
@login_required
@admin_required
def all_history():
    """
    View function for url/all_history page.
    Contains a form for sorting by username, start date, and end date.
    :return: All user history, sorted (if applicable) with a form for further
    filtering.
    """
    current_app.logger.info('Start function all_history() [VIEW]')

    if 'first_date' not in session:
        current_app.logger.info('\'first_date\' not found in session. Setting to defaults.')
        session['first_date'] = get_time_period('w')[0]
        session['last_date'] = get_time_period('w')[1]
    if 'email' not in session:
        current_app.logger.info('\'email\' not found in session. Setting to defaults.')
        session['email'] = None
    if 'tag_input' not in session:
        current_app.logger.info('\'tag_input\' not found in session. Setting to defaults.')
        session['tag_input'] = 0
    if 'division' not in session:
        current_app.logger.info('\'division\' not found in session. Setting to defaults.')
        session['division'] = None

    if request.referrer and 'all_history' not in request.referrer:
        # If the user is visiting from another page, reset the session email variable
        current_app.logger.info('User is visiting from another page. Setting session[\'email\'] to None')
        session['email'] = None

    form = AdminFilterEventsForm()

    page = request.args.get('page', 1, type=int)

    if form.validate_on_submit() and (form.submit.data or form.last_month.data
                                      or form.this_month.data or form.last_week.data or
                                      form.this_week.data or form.last_day.data or form.this_day.data):
        time_period = process_time_periods(form)
        session['first_date'] = time_period[0]
        session['last_date'] = time_period[1]
        session['email'] = form.email.data
        session['tag_input'] = form.tag.data
        session['division'] = form.division.data
        page = 1

    addform = AddEventForm()
    if addform.validate_on_submit() and addform.add.data:
        if addform.addemail.data.lower() == current_user.email:
            flash('Administrators cannot edit their own clock events', 'error')
            return redirect(url_for('main.clear'))
        date_string = addform.add_date.data.strftime('%m/%d/%Y ')
        time_string = addform.add_time.data
        datetime_str = date_string + time_string
        try:
            datetime_obj = datetime.strptime(datetime_str, '%m/%d/%Y %H:%M')
        except ValueError:
            flash('Please make sure your time input is in the format HH:MM', category='error')
            return redirect(url_for('main.all_history'))
        u = User.query.filter_by(email=addform.addemail.data.lower()).first()
        add_event(u.id, datetime_obj, (addform.addpunch_type.data == "In"))
        flash("Clock event successfully processed", 'success')
        return redirect(url_for('main.clear'))

    deleteform = DeleteEventForm(request.form)
    if deleteform.validate_on_submit() and request.form.get('event_id', None) and deleteform.delete.data:
        delete_event(request.form['event_id'])
        flash('Event successfully deleted', category='success')
        return redirect(url_for('main.clear'))

    advtimesheetform = GenerateMultipleTimesheetsForm()
    advtimesheetform.emails.choices = [(u.email, u.email) for u in User.query.all()]
    if advtimesheetform.validate_on_submit() and advtimesheetform.gen_timesheets.data:
        # TODO: THIS MESSAGE ISNT FLASHING
        flash('Succesfully generated timesheet(s)', category='success')
        return generate_timesheets(advtimesheetform.emails.data, advtimesheetform.start_date.data,
                                   advtimesheetform.end_date.data)

    current_app.logger.info('Querying (calling get_events_by_date)')
    events_query = get_events_by_date()
    current_app.logger.info('Finished querying')

    exportform = ExportForm()
    if exportform.validate_on_submit() and exportform.export.data:
        flash('Succesfully exported events in query', 'success')
        return create_csv(events_query.all())


    # Pagination
    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items

    current_app.logger.info('Querying (calling get_all_tags)')
    tags = get_all_tags()
    current_app.logger.info('Finished querying')

    query_has_results = True if events_query.first() else False

    current_app.logger.info('End function all_history()')
    return render_template('main/all_history.html',
                           events=events,
                           form=form,
                           addform=addform,
                           deleteform=deleteform,
                           advtimesheetform=advtimesheetform,
                           exportform=exportform,
                           pagination=pagination,
                           tags=tags,
                           generation_events=events_query.all(),
                           query_has_results=query_has_results
                           )


@main.route('/history', methods=['GET', 'POST'])  # User history
@login_required
def history():
    """
    Shows a user their own history.
    TODO: Make filterable by date
    :return: An html page that contains user history, sorted (if applicable)
    with a form for further filtering.
    """
    current_app.logger.info('Start function all_history()')
    if not current_user.validated:
        current_app.logger.info('{} is not validated. Redirecting to /auth/change_password...'
                                .format(current_user.email))
        return redirect(url_for('auth.change_password'))

    # Explicitly set email session variable to current user's email, as users on the history page
    # should only be able to view their own information
    session['email'] = current_user.email

    form = UserFilterEventsForm()
    page = request.args.get('page', 1, type=int)
    if form.validate_on_submit():
        time_period = process_time_periods(form)
        session['first_date'] = time_period[0]
        session['last_date'] = time_period[1]
        page = 1

    current_app.logger.info('Querying (calling get_events_by_date)')
    events_query = get_events_by_date()
    current_app.logger.info('Finished querying')

    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items

    current_app.logger.info('Querying (calling get_all_tags)')
    tags = get_all_tags()
    current_app.logger.info('Finished querying')

    query_has_results = True if events_query.first() else False

    return render_template('main/history.html',
                           events=events,
                           form=form,
                           pagination=pagination,
                           generation_events=events_query.all(),
                           tags=tags,
                           query_has_results=query_has_results)


@main.route('/download_timesheet', methods=['GET', 'POST'])
@login_required
def download():
    """
    Creates a link to download a timesheet containing the given filtered data.
    :return: A directive to download a file timesheet.txt, which contains
    timesheet data
    """
    current_app.logger.info('Start function download()')
    errors = []
    if 'email' not in session or session['email'] is None or session['email'] == '':
        # This will only happen for admin searches, so we only need to
        # redirect to the admin page
        current_app.logger.error('User {} tried to generate a timesheet but '
                                 'did not specify a user'
                                 .format(current_user.email)
                                 )
        errors.append('You must specify a user.')
    if (session['last_date'] - session['first_date']).days > 8:
        current_app.logger.error('User {} tried to generate a timesheet but '
                                 'exceeded maximum duration (one week)'
                                 .format(current_user.email)
                                 )
        errors.append('Maximum timesheet duration is a week. '
                      'Please refine your filters')

    events = request.form.getlist('event')  # Gets event data from frontend - we can similarly pass in other data

    if not (check_total_clock_count(events)):
        current_app.logger.error('Timesheet was generated with odd number of clock ins/outs {}'.format(len(events)))
        flash('Each clock in must have corresponding clock out to generate a timesheet. '
              'Please submit a timepunch for missing times.', category='error')
        return redirect(url_for('main.' + (request.referrer).split('/')[3]))
    if errors:
        for error in errors:
            flash(error, 'warning')
        last_page = (request.referrer).split('/')[3]
        if last_page.find('?') != -1:
            last_page = last_page[:last_page.find('?')]
        current_app.logger.error('Errors occurred while generating timesheet (end function download).'
                                 ' Redirecting to main.{}...'.format(last_page))
        return redirect(url_for('main.' + last_page))

    response = make_response(generate_timesheet(events))
    response.headers['Content-Disposition'] = \
        "attachment; filename='timesheet.pdf"
    response.mimetype = 'application/pdf'
    current_app.logger.info('%s downloaded timesheet for user %s '
                            'beginning at %s' %
                            (current_user.email,
                             session['email'],
                             session['first_date'].strftime("%b %d, %Y %H:%M:%S %p")
                             )
                            )
    return response


@main.route('/download_invoice', methods=['GET', 'POST'])
@login_required
def download_invoice():
    """
    Creates a link to download a timesheet containing the given filtered data.
    :return: A directive to download a file timesheet.txt, which contains
    timesheet data
    """
    current_app.logger.info('Start function download_invoice()')
    errors = []

    # Get the page the user downloaded an invoice from
    last_page = (request.referrer).split('/')[3]
    if last_page.find('?') != -1:
        last_page = last_page[:last_page.find('?')]

    if 'email' not in session or session['email'] is None or session['email'] == '':
        # If an admin does not specify the account for which the invoice should
        # be generated, flash an error
        current_app.logger.error('User {} tried to generate an invoice but '
                                 'did not specify a user'
                                 .format(current_user.email)
                                 )
        errors.append('You must specify a user.')

    if (session['last_date'] - session['first_date']).days > 8:
        # If the time period is over a week, flash an error. We use days > 8
        # because we use a < as opposed to a <= in our query in modules.py
        current_app.logger.error('User {} tried to generate a timesheet but '
                                 'exceeded maximum duration (one week)'
                                 .format(current_user.email)
                                 )
        errors.append('Maximum timesheet duration is a week. '
                      'Please refine your filters')
    if errors:
        for error in errors:
            flash(error, 'warning')
        current_app.logger.error('Errors occurred while generating invoice (end function download_invoice).'
                                 ' Redirecting to main.{}...'.format(last_page))
        return redirect(url_for('main.' + last_page))

    # Append @records.nyc.gov if not already in user email field
    if '@records.nyc.gov' not in session['email']:
        session['email'] += '@records.nyc.gov'

    if session['email'] is None or session['email'] == '':
        u = User.query.filter_by(email=current_user.email.lower()).first()
    else:
        u = User.query.filter_by(email=session['email'].lower()).first()

    # Check for payrate
    if get_payrate_before_or_after(session['email'], session['first_date'], True) is None:
        flash('User {} does not have a payrate. Maybe you meant to generate a timesheet instead.'
              .format(session['email']), category='error')
        flash('If you believe this is an error, please contact a TimeClock administrator.', category='warning')
        return redirect(url_for('main.' + last_page))

    all_info = calculate_hours_worked(session['email'], session['first_date'], session['last_date'])
    if not all_info:
        current_app.logger.error('Invoice was generated with odd number of clock ins/outs {}')
        flash('Each clock in must have corresponding clock out to generate an invoice. '
              'Please submit a timepunch for missing times.', category='error')
        return redirect(url_for('main.' + last_page))
    day_events_list = all_info['days_list']
    total_hours = all_info['total_hours']
    total_earnings = all_info['total_earnings']
    return render_template('payments/invoice.html', day_events_list=day_events_list,
                           employee=u, total_hours=total_hours, total_earnings=total_earnings,
                           time=datetime.now(), budget_code=u.budget_code, object_code=u.object_code,
                           object_name=u.object_name)


@main.route('/clear_filter', methods=['GET', 'POST'])
@login_required
def clear():
    """
    Clear the admin's all_history filter.
    :return: A redirect to the all_history page.
    """
    current_app.logger.info('Start function clear()')
    session.pop('first_date', None)
    session.pop('last_date', None)
    session.pop('email', None)
    session.pop('tag_input', None)
    session.pop('division', None)
    current_app.logger.info('User %s cleared their admin history filter.' %
                            current_user.email)
    current_app.logger.info('End function clear()')
    return redirect(url_for('main.all_history'))


@main.route('/user_clear_filter', methods=['GET', 'POST'])
@login_required
def user_clear():
    """
    Clear a user's personal history filter.
    :return: A redirect to the history page.
    """
    current_app.logger.info('Start function user_clear()')
    session.pop('first_date', None)
    session.pop('last_date', None)
    session.pop('email', None)
    session.pop('tag_input', None)
    current_app.logger.info('User %s cleared their history filter.' %
                            current_user.email)
    current_app.logger.info('End function user_clear()')
    return redirect(url_for('main.history'))


@main.route('/create_payrate', methods=['GET', 'POST'])
@login_required
@admin_required
def pay():
    """
    View function used to render HTML to create a payrate.
    :return: HTML template to create payrates.
    """
    current_app.logger.info('Start function pay()')
    form = CreatePayRateForm()
    if form.validate_on_submit():
        current_app.logger.info('Querying for user with email {}'.format(form.email.data))
        u = User.query.filter_by(email=form.email.data.lower()).first()
        current_app.logger.info('Finished querying for user')
        if not u:
            current_app.logger.error('Tried creating pay for {}. A user with this email does not exist.'.
                                     format(form.email.data))
            flash('No such user exists', category='warning')
        else:
            p = Pay(start=form.start_date.data, end=form.start_date.data, rate=form.rate.data, user=u)
            db.session.add(p)
            db.session.commit()
            current_app.logger.info('Administrator {} created new pay rate for user {}'
                                    .format(current_user.email, u.email))
            flash('Pay rate successfully created', category='success')
    current_app.logger.info('End function pay')
    return render_template('payments/create_payrate.html', form=form, pays=Pay.query.all())


@main.route('/request_timepunch', methods=['GET', 'POST'])
@login_required
def request_timepunch():
    """
    Creates a form for users to be able to request a timepunch.
    :return: A page users can implement to request the addition of a clock event.
    """
    current_app.logger.info('Start function request_timepunch()')
    form = TimePunchForm()
    vacform = RequestVacationForm()
    if form.validate_on_submit() and form.submit.data:
        if form.note.data is not None and len(form.note.data) > 60:
            flash("Your note cannot exceed 60 characters", category='warning')
            current_app.logger.error('{} submitted a note that exceeded 60 characters'.format(current_user.email))
        elif not current_user.supervisor:
            flash("You must have a supervisor to request a timepunch. If you believe a supervisor "
                  "should be assigned to you, please contact the system administrator.", category='error')
            current_app.logger.error('Does not have a supervisor'.format(current_user.email))
        else:
            # Combine date and time fields
            date_string = form.punch_date.data.strftime('%m/%d/%Y ')
            time_string = form.punch_time.data
            datetime_str = date_string + time_string
            try:
                datetime_obj = datetime.strptime(datetime_str, '%m/%d/%Y %H:%M')
            except ValueError:
                flash('Please make sure your time input is in the format HH:MM', category='error')
                return redirect(url_for('main.request_timepunch'))
            past_type = get_last_clock(current_user, datetime_obj).type if get_last_clock(
                current_user, datetime_obj) else None

            if past_type == (form.punch_type.data == "In"):
                flash('Timepunch request failed: you would have two consecutive clocks of the same type', 'error')
                return redirect(url_for('main.request_timepunch'))
            create_timepunch(form.punch_type.data, datetime_obj, form.note.data)
            flash('Your timepunch request has been successfully submitted and is pending approval',
                  category='success')
            current_app.logger.info('End function request_timepunch')
            return redirect(url_for('main.request_timepunch'))
    elif vacform.validate_on_submit() and vacform.vac_request.data:
        if not current_user.supervisor:
            flash("You must have a supervisor to request a timepunch. If you believe a supervisor "
                  "should be assigned to you, please contact the system administrator.", category='error')
            current_app.logger.error('Does not have a supervisor'.format(current_user.email))
        else:
            v = Vacation(user_id=current_user.id, start=vacform.vac_start.data, end=vacform.vac_end.data,
                         approved=False, pending=True)
            db.session.add(v)
            db.session.commit()
            flash('Your vacation request has been successfully submitted and is pending approval', 'success')

        current_app.logger.info('End function request_timepunch')
        return redirect(url_for('main.request_timepunch'))

    current_app.logger.info('End function request_timepunch')
    return render_template('main/request_timepunch.html', form=form, vacform=vacform)


@main.route('/review_timepunches', methods=['GET', 'POST'])
@login_required
def review_timepunch():
    """
    Creates a page supervisors can use to approve or deny timepunches.
    :return: An HTML page in which supervisors can manage and filter timepunches.
    """
    current_app.logger.info('Start function review_timepunch()')
    timepunch_query = get_timepunches_for_review(current_user.email)
    form = ApproveOrDenyForm(request.form)
    filter_form = FilterTimePunchForm()
    clear_form = ClearForm()
    page = request.args.get('page', 1, type=int)
    if filter_form.validate_on_submit and filter_form.filter.data:
        if not filter_form.email.data or User.query.filter_by(email=filter_form.email.data.lower()).first():
            flash('Successfully filtered', 'success')
        else:
            flash('Invalid email', 'error')
        # User submits a filter
        page = 1

        # Filter through timepunches based on user selections
        timepunch_query = get_timepunches_for_review(current_user.email,
                                                     filter_form.email.data,
                                                     filter_form.status.data)

    if clear_form.validate_on_submit() and clear_form.clear.data:
        # User submits the clear form
        page = 1
        timepunch_query = get_timepunches_for_review(current_user.email)
        flash('Filter successfully cleared', category='success')

    if form.validate_on_submit():
        # User submits an approve or deny request
        if form.approve.data:
            approve_or_deny(request.form['event_id'], True)
            flash('Timepunch successfully approved', category='success')
            current_app.logger.info('{} approved timepunch with event_id {}'
                                    .format(current_user.email, request.form['event_id']))
        elif form.deny.data:
            approve_or_deny(request.form['event_id'], False)
            flash('Timepunch successfully unapproved', category='success')
            current_app.logger.info('{} denied timepunch with event_id {}'
                                    .format(current_user.email, request.form['event_id']))

    pagination = timepunch_query.paginate(
        page, per_page=15,
        error_out=False)

    query_has_results = True if timepunch_query.first() else False

    timepunch_list = pagination.items
    current_app.logger.info('End function review_timepunch')
    return render_template('main/review_timepunches.html',
                           timepunch_list=timepunch_list,
                           form=form,
                           pagination=pagination,
                           filter=filter_form,
                           clear=clear_form,
                           query_has_results=query_has_results)


@main.route('/edit_user_list', methods=['GET', 'POST'])
@login_required
@admin_required
def user_list_page():
    """
    Renders a page with the list of users on it and related data on them. Also includes edit button to direct to
    edit user page
    :return: user_list.html which lists all the users in the application
    """
    active = eval_request_bool(request.args.get('active', "true"), True)
    nondivision_users = []
    tags = get_all_tags()
    list_of_users = []
    list_of_users_all  = User.query.filter_by(is_active=active).all()
    for user in list_of_users:
        if user.division is None:
            list_of_users.remove(user)
            nondivision_users.append(user)   
    if request.method == 'GET':
        entry = request.args.get('search_input', '')
        search_result_email = User.query.filter(User.email.ilike('%' + entry + '%')).all()
        search_result_fname = User.query.filter(User.first_name.ilike('%' + entry.title()+ '%')).all()
        search_result_lname = User.query.filter(User.last_name.ilike('%' + entry.title() + '%')).all()
        list_of_users = list(set(list_of_users_all) & set(search_result_email + search_result_fname + search_result_lname))

    if not list_of_users:
        flash('No results found', category = 'error')
    # Pass in separate list of users with and without divisions
    return render_template('main/user_list.html', list_of_users=list_of_users, tags=tags,
                           nondivision_users=nondivision_users, active_users=active)


@main.route('/export_events', methods=['GET', 'POST'])
@login_required
@admin_required
def export_events():
    """
    Exports all events in the db to a csv file
    :return: CSV file response
    """
    return create_csv()


@main.route('/review_vacations', methods=['GET', 'POST'])
@login_required
def review_vacations():
    """
    Creates a page on which administrators can review vacation requests, and accept or deny them.
    :return: HTML page containing a table of vacations and a filter to specify vacations to review (by user and status)
    """
    current_app.logger.info('Start function review_vacations()')
    vacation_query = get_vacations_for_review(current_user.email)
    form = ApproveOrDenyForm(request.form)  # reuse same form
    filter_form = FilterVacationForm()
    clear_form = ClearForm()
    page = request.args.get('page', 1, type=int)
    if filter_form.validate_on_submit and filter_form.filter.data:
        if not filter_form.email.data or User.query.filter_by(email=filter_form.email.data.lower()).first():
            flash('Successfully filtered', 'success')
        else:
            flash('Invalid email', 'error')
        # User submits a filter
        page = 1

        # Filter through timepunches based on user selections
        vacation_query = get_vacations_for_review(current_user.email,
                                                  filter_form.email.data,
                                                  filter_form.status.data)

    if clear_form.validate_on_submit() and clear_form.clear.data:
        # User submits the clear form
        page = 1
        vacation_query = get_vacations_for_review(current_user.email)
        flash('Filter successfully cleared', category='success')

    if form.validate_on_submit():
        # User submits an approve or deny request
        if form.approve.data:
            approve_or_deny_vacation(request.form['vacation_id'], True)
            flash('Vacation successfully approved', category='success')
            current_app.logger.info('{} approved vacation with event_id {}'
                                    .format(current_user.email, request.form['vacation_id']))
        elif form.deny.data:
            approve_or_deny_vacation(request.form['vacation_id'], False)
            flash('Vacation successfully unapproved', category='success')
            current_app.logger.info('{} denied vacation with event_id {}'
                                    .format(current_user.email, request.form['vacation_id']))

    pagination = vacation_query.paginate(
        page, per_page=15,
        error_out=False)

    query_has_results = True if vacation_query.first() else False

    vacation_list = pagination.items
    current_app.logger.info('End function review_timepunch')
    return render_template('main/review_vacations.html',
                           vacation_list=vacation_list,
                           form=form,
                           pagination=pagination,
                           filter=filter_form,
                           clear=clear_form,
                           query_has_results=query_has_results)

