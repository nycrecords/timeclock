"""
.. module:: main.views.

   :synopsis: Handles all core URL endpoints for the timeclock application
"""

from flask import (
    render_template,
    flash,
    request,
    make_response,
    url_for,
    redirect,
    session
)
from . import main
from flask_login import login_required, current_user
from .modules import (
    process_clock,
    set_clock_form,
    get_last_clock,
    get_events_by_date,
    get_clocked_in_users,
    get_time_period,
    process_time_periods,
    get_all_tags,
    get_last_clock_type,
    update_user_information,
    get_changelog_by_user_id
)
from .timepunch import (
    create_timepunch,
    get_timepunches_for_review,
    approve_or_deny
)
from .payments import (
    get_payrate_before_or_after,
    calculate_hours_worked
)
from ..decorators import admin_required
from .forms import (
    AdminFilterEventsForm,
    UserFilterEventsForm,
    CreatePayRateForm,
    TimePunchForm,
    ApproveOrDenyTimePunchForm,
    FilterTimePunchForm,
    ClearTimePunchFilterForm,
    ChangeUserDataForm
)
from .pdf import (
    generate_header,
    generate_footer,
    generate_employee_info,
    generate_timetable,
    generate_signature_template
)
from datetime import datetime
from flask import current_app
from ..models import Pay, User
from .. import db
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


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
            current_app.logger.info('%s clocked %s at %s' % (
                current_user.email,
                'in' if get_last_clock_type(current_user.id) else 'out',
                time)
            )
            flash("Clock submission successfully processed", category='success')
            return redirect(url_for('main.index'))

    current_app.logger.info('End function index')
    return render_template('main/index.html',
                           form=set_clock_form(),
                           last_event=get_last_clock(),
                           clocked_in_users=get_clocked_in_users(),
                           last_clock_event=get_last_clock_type(current_user.id)
                           )


@main.route('/all_history',  methods=['GET', 'POST'])
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

    if form.validate_on_submit():
        time_period = process_time_periods(form)
        session['first_date'] = time_period[0]
        session['last_date'] = time_period[1]
        session['email'] = form.email.data
        session['tag_input'] = form.tag.data
        session['division'] = form.division.data
        page = 1

    current_app.logger.info('Querying (calling get_events_by_date)')
    events_query = get_events_by_date()
    current_app.logger.info('Finished querying')

    # Pagination
    pagination = events_query.paginate(
        page, per_page=15,
        error_out=False)
    events = pagination.items

    current_app.logger.info('Querying (calling get_all_tags)')
    tags = get_all_tags()
    current_app.logger.info('Finished querying')

    current_app.logger.info('End function all_history()')
    return render_template('main/all_history.html',
                           events=events,
                           form=form,
                           pagination=pagination,
                           tags=tags,
                           generation_events=events_query.all()
                           )


@main.route('/history', methods=['GET', 'POST'])    # User history
@login_required
def history():
    """
    Shows a user their own history.
    TODO: Make filterable by date.
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

    return render_template('main/history.html',
                           events=events,
                           form=form,
                           pagination=pagination,
                           generation_events=events_query.all(),
                           tags=tags)


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
    if (session['last_date']-session['first_date']).days > 8:
        current_app.logger.error('User {} tried to generate a timesheet but '
                                 'exceeded maximum duration (one week)'
                                 .format(current_user.email)
                                 )
        errors.append('Maximum timesheet duration is a week. '
                      'Please refine your filters')
    if errors:
        for error in errors:
            flash(error, 'warning')
        last_page = (request.referrer).split('/')[3]
        if last_page.find('?') != -1:
            last_page = last_page[:last_page.find('?')]
        current_app.logger.error('Errors occurred while generating timesheet (end function download).'
                                 ' Redirecting to main.{}...'.format(last_page))
        return redirect(url_for('main.' + last_page))

    events = request.form.getlist('event')  # Gets event data from frontend - we can similarly pass in other data

    # Begin generation of the actual PDF here
    current_app.logger.info('Beginning to generate timesheet pdf...')
    import io
    output = io.BytesIO()
    c = canvas.Canvas(output, pagesize=letter)

    generate_header(c)
    generate_employee_info(c)
    generate_timetable(c, events)
    generate_signature_template(c)
    generate_footer(c)
    c.showPage()
    c.save()
    pdf_out = output.getvalue()
    output.close()
    current_app.logger.info('Finished generating timesheet PDF')

    response = make_response(pdf_out)
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
    current_app.logger.info('End function download')
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

    if (session['last_date']-session['first_date']).days > 8:
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

    if session['email'] is None or session['email'] == '':
        u = User.query.filter_by(email=current_user.email).first()
    else:
        u = User.query.filter_by(email=session['email']).first()

    # Check for payrate
    if get_payrate_before_or_after(session['email'], session['first_date'], True) is None:
        flash('User {} does not have a payrate. Maybe you meant to generate a timesheet instead.'
              .format(session['email']), category='error')
        flash('If you believe this is an error, please contact a TimeClock administrator.', category='warning')
        return redirect(url_for('main.' + last_page))

    all_info = calculate_hours_worked(session['email'], session['first_date'], session['last_date'])
    day_events_list = all_info['days_list']
    total_hours = all_info['total_hours']
    total_earnings = all_info['total_earnings']
    return render_template('payments/invoice.html', day_events_list=day_events_list,
                           employee=u, total_hours=total_hours, total_earnings=total_earnings,
                           time=datetime.now())


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
        u = User.query.filter_by(email=form.email.data).first()
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
    if form.validate_on_submit():
        if form.note.data is not None and len(form.note.data) > 60:
            flash("Your note cannot exceed 60 characters", category='warning')
            current_app.logger.error('{} submitted a note that exceeded 60 characters'.format(current_user.email))
        if not current_user.supervisor:
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

            create_timepunch(form.punch_type.data, datetime_obj, form.note.data)
            flash('Your timepunch request has been successfully submitted and is pending approval',
                  category='success')
            current_app.logger.info('End function request_timepunch')
            return redirect(url_for('main.request_timepunch'))

    current_app.logger.info('End function request_timepunch')
    return render_template('main/request_timepunch.html', form=form)


@main.route('/review_timepunches', methods=['GET', 'POST'])
@login_required
def review_timepunch():
    """
    Creates a page supervisors can use to approve or deny timepunches.
    :return: An HTML page in which supervisors can manage and filter timepunches.
    """
    current_app.logger.info('Start function review_timepunch()')
    timepunch_query = get_timepunches_for_review(current_user.email)
    form = ApproveOrDenyTimePunchForm(request.form)
    filter_form = FilterTimePunchForm()
    clear_form = ClearTimePunchFilterForm()
    page = request.args.get('page', 1, type=int)

    if filter_form.validate_on_submit and filter_form.filter.data:
        # User submits a filter
        page = 1

        # Filter through timepunches based on user selections
        timepunch_query = get_timepunches_for_review(current_user.email,
                                                     filter_form.email.data,
                                                     filter_form.status.data)
        flash('Successfully filtered', category='success')

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

    timepunch_list = pagination.items
    current_app.logger.info('End function review_timepunch')
    return render_template('main/review_timepunches.html',
                           timepunch_list=timepunch_list,
                           form=form,
                           pagination=pagination,
                           filter=filter,
                           clear=clear)


@main.route('/edit_user_list', methods=['GET', 'POST'])
@login_required
@admin_required
def user_list_page():
    """
    Renders a page with the list of users on it and related data on them. Also includes edit button to direct to
    edit user page
    :return: user_list.html which lists all the users in the application
    """
    nondivision_users = []
    tags = get_all_tags()
    list_of_users = User.query.all()
    for user in list_of_users:
        if user.division is None:
            list_of_users.remove(user)
            nondivision_users.append(user)
    # Pass in separate list of users with and without divisions
    return render_template('main/user_list.html', list_of_users=list_of_users, tags=tags,
                           nondivision_users=nondivision_users)


@main.route('/user/<username>', methods=['GET', 'POST'])
@login_required
@admin_required
def user_profile(username):
    """
    Generates an editable user profile page for admins.
    :param username: The username of the user whose page is viewed/edited.
    :return: HTML page containing user information and a form to edit it.
    """
    current_app.logger.info('Start function user_profile() for user {}'.format(username))
    # Usernames are everything in the email before the @ symbol
    # i.e. for sdhillon@records.nyc.gov, username is sdhillon
    if '@records.nyc.gov' in username:
        u = User.query.filter_by(email=(username)).first()
    else:
        u = User.query.filter_by(email=(username + '@records.nyc.gov')).first()
    form = ChangeUserDataForm()

    if not u:
        flash('No user with username {} was found'.format(username), category='error')
        return redirect(url_for('main.user_list_page'))
    elif u.role.name == 'Administrator' and u == current_user:
        # If user is admin, redirect to index and flash a message,
        # as admin should not be allowed to edit their own info through frontend.
        # This also avoids the issue that comes with the fact that admins don't have
        # a supervisor.
        flash('Admins cannot edit their own information.', category='error')
        current_app.logger.info('End function user_profile')
        return redirect(url_for('main.user_list_page'))

    if form.validate_on_submit():
        if u.email == form.supervisor_email.data:
            flash('A user cannot be their own supervisor. Please revise your supervisor '
                  'field.', category='error')
        else:
            flash('User information has been updated', category='success')
            update_user_information(u, form.first_name.data, form.last_name.data,
                                    form.division.data, form.tag.data, form.supervisor_email.data,
                                    form.role.data)
            current_app.logger.info('{} update information for {}'.format(current_user.email, u.email))
            current_app.logger.info('End function user_profile')
            return redirect(url_for('main.user_profile', username=username))
    else:
        # Pre-populate the form with current values
        form.first_name.data = u.first_name
        form.last_name.data = u.last_name
        form.division.data = u.division
        form.tag.data = u.tag_id
        form.supervisor_email.data = u.supervisor.email if u.supervisor else 'admin@records.nyc.gov'
        form.role.data = u.role.name

    current_app.logger.info('End function user_profile')

    # For ChangeLog Table
    changes = get_changelog_by_user_id(u.id)

    page = request.args.get('page', 1, type=int)
    pagination = changes.paginate(
        page, per_page=10,
        error_out=False)
    changes = pagination.items

    return render_template('main/user_page.html', username=username, u=u, form=form, changes=changes, pagination=pagination)
