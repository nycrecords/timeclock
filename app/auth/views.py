"""
.. module:: auth.views.

   :synopsis: Handles all authentication URL endpoints for the
   TimeClock application
"""
from datetime import datetime

from flask import current_app, jsonify
from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_required, login_user, logout_user, current_user
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import check_password_hash

from . import auth
from .forms import (
    LoginForm,
    RegistrationForm,
    AdminRegistrationForm,
    PasswordResetForm,
    PasswordResetRequestForm,
    ChangePasswordForm,
    ChangeUserDataForm,
)
from .modules import (
    check_password_requirements,
    get_supervisors_for_division,
    create_user,
    get_changelog_by_user_id,
    update_user_information,
)
from .. import db
from ..decorators import admin_required
from ..email_notification import send_email
from ..models import User, Role
from ..utils import InvalidResetToken
from app.auth.constants import passwords



@auth.route("/admin_register", methods=["GET", "POST"])
@login_required
@admin_required
def admin_register():
    """
    Renders a form for admins to register new users.

    :return: HTML page where admins can register new users
    """
    current_app.logger.info("Start function admin_register() [VIEW]")
    form = AdminRegistrationForm()
    form.supervisor_id.choices = [(0, "No Supervisor")] + [
        (user.id, user.email) for user in User.query.filter_by(is_supervisor=True).all()
    ]
    if request.method == "POST" and form.validate_on_submit():
        temp_password = datetime.today().strftime("%A%-d")
        email = create_user(
            form.email.data.lower(),
            temp_password,
            form.first_name.data,
            form.last_name.data,
            form.division.data,
            form.role.data,
            form.tag.data,
            form.is_supervisor.data,
            form.supervisor_id.data,
            form.budget_code.data,
            form.object_code.data,
            form.object_name.data,
        )
        flash(
            "User successfully registered.\nAn email with login instructions has been sent to {}".format(
                email
            ),
            category="success",
        )
        current_app.logger.info("End function admin_register() [VIEW]")
        return redirect(url_for("main.index"))

    current_app.logger.info("End function admin_register() [VIEW]")
    return render_template("auth/admin_register.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    View function to login a user. Redirects the user to the index page on successful login.

    :return: Login page.
    """
    current_app.logger.info("Start function login() [VIEW]")

    # Redirect to index if already logged in
    if current_user.is_authenticated:
        current_app.logger.info(
            "{} is already authenticated: redirecting to index".format(
                current_user.email
            )
        )
        current_app.logger.info("End function login() [VIEW]")
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            if not user.is_active:
                current_app.logger.info(
                    "Inactive User {} trying to login".format(current_user)
                )
                flash(
                    "Invalid username or password. Please contact HR for assistance",
                    category="error",
                )
                current_app.logger.info("End function login() [VIEW]")
            elif user.login_attempts > 2:
                # Too many invalid attempts
                current_app.logger.info("{} has been locked out".format(user.email))
                flash(
                    "You have too many invalid login attempts. You must reset your password.",
                    category="error",
                )
                current_app.logger.info("End function login() [VIEW]")
                return redirect(url_for("auth.password_reset_request"))

            elif user.verify_password(form.password.data):
                # Credentials successfully submitted: log the user in and set their login_attempts to 0
                login_user(user)
                user.login_attempts = 0
                db.session.add(user)
                db.session.commit()
                current_app.logger.info('{} successfully logged in'.format(current_user.email))
                # Check to ensure password isn't outdated
                if (datetime.today() - current_user.password_list.last_changed).days > passwords.DAYS_TILL_EXPIRE:
                    # If user's password has expired (not update in 90 days)
                    current_app.logger.info(
                        "{}'s password hasn't been updated in 90 days: account invalidated.".format(
                            current_user.email
                        )
                    )
                    current_user.validated = False
                    db.session.add(current_user)
                    db.session.commit()
                    flash('You haven\'t changed your password in 90 days. You must re-validate your account',
                          category='error')
                    current_app.logger.info('End function login() [VIEW]')
                    return redirect(url_for('auth.change_password'))
                elif (datetime.today() - current_user.password_list.last_changed).days > passwords.DAYS_UNTIL_PW_WARNING:
                    # If user's password is about to expire (not updated in 75 days)
                    days_to_expire = passwords.DAYS_TILL_EXPIRE-((datetime.today() - current_user.password_list.last_changed).days)
                    flash('Your password will expire in {} days.'.format(days_to_expire), category='warning')
                current_app.logger.error('{} is already logged in. Redirecting to main.index'.format(current_user.email))
                current_app.logger.info('End function login() [VIEW]')
                return redirect(request.args.get('next') or url_for('main.index'))

            else:
                # If the user exists in the database but entered incorrect information
                current_app.logger.info(
                    "{} failed to log in: Invalid username or password".format(
                        user.email
                    )
                )
                user.login_attempts += 1
                db.session.add(user)
                db.session.commit()
            if user.is_active:
                flash("Invalid username or password", category="error")
    current_app.logger.info("End function login() [VIEW]")
    return render_template(
        "auth/login.html", form=form, reset_url=url_for("auth.password_reset_request")
    )


@auth.route("/logout")
@login_required
def logout():
    """
    View function to logout a user.

    :return: Index page.
    """
    current_app.logger.info("Start function logout() [VIEW]")
    current_user_email = current_user.email
    logout_user()
    current_app.logger.info("{} logged out".format(current_user_email))
    flash("You have been logged out.", category="success")
    current_app.logger.info("End function logout() [VIEW]")
    return redirect(url_for("auth.login"))


@auth.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    View function for changing a user password.

    :return: Change Password page.
    """
    current_app.logger.info("Start function change_password() [VIEW]")
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if (
            check_password_hash(
                pwhash=current_user.password_list.p1, password=form.password.data
            )
            or check_password_hash(
                pwhash=current_user.password_list.p2, password=form.password.data
            )
            or check_password_hash(
                pwhash=current_user.password_list.p3, password=form.password.data
            )
            or check_password_hash(
                pwhash=current_user.password_list.p4, password=form.password.data
            )
            or check_password_hash(
                pwhash=current_user.password_list.p5, password=form.password.data
            )
        ):
            # If the inputted password is one of the user's last five passwords
            current_app.logger.info(
                "{} tried to change password. Failed: Used old password.".format(
                    current_user.email
                )
            )
            flash(
                "Your password cannot be the same as the last 5 passwords",
                category="error",
            )
            return render_template("auth/change_password.html", form=form)

        elif check_password_requirements(
            current_user.email,
            form.old_password.data,
            form.password.data,
            form.password2.data,
        ):
            # If password security requirements are met
            current_user.password_list.update(current_user.password_hash)
            current_user.password = form.password.data
            current_user.validated = True
            db.session.add(current_user)
            db.session.commit()
            current_app.logger.info(
                "{} changed their password.".format(current_user.email)
            )
            flash("Your password has been updated.", category="success")
            current_app.logger.info("End function logout() [VIEW]")
            return redirect(url_for("main.index"))

    current_app.logger.info("End function logout() [VIEW]")
    return render_template("auth/change_password.html", form=form)


@auth.route("/reset", methods=["GET", "POST"])
def password_reset_request():
    """
    View function for requesting a password reset.

    :return: HTML page in which users can request a password reset.
    """
    current_app.logger.info("Start function password_reset_request() [VIEW]")
    if not current_user.is_anonymous:
        # If the current user is signed in, redirect them to TimeClock home.
        current_app.logger.info(
            "Current user ({}) is already signed in. Redirecting to index...".format(
                current_user.email
            )
        )
        return redirect(url_for("main.index"))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        current_app.logger.info(
            "Tried to submit a password reset request with account email {}".format(
                form.email.data
            )
        )
        current_app.logger.info(
            "Querying for user with given email: {}".format(form.email.data)
        )
        user = User.query.filter_by(email=form.email.data.lower()).first()
        current_app.logger.info("Finished querying for user with given email")
        if user:
            # If the user exists, generate a reset token and send an email containing a link to reset the user's
            # password
            token = user.generate_reset_token()
            send_email(
                user.email,
                "Reset Your Password",
                "auth/email/reset_password",
                user=user,
                token=token,
                next=request.args.get("next"),
            )
            current_app.logger.info(
                "Sent password reset instructions to {}".format(form.email.data)
            )
        flash(
            "If this account is in the system, an email with instructions to reset your password has been sent to you.",
            category="success",
        )
        current_app.logger.info("Redirecting to /auth/login...")
        current_app.logger.info("End function password_reset_request() [VIEW]")
        return redirect(url_for("auth.login"))
    current_app.logger.info("End function password_reset_request() [VIEW]")
    return render_template("auth/request_reset_password.html", form=form)


@auth.route("/reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    """
    View function after a user has clicked on a password reset link in their inbox.

    :param token: The token that is checked to verify the user's credentials.
    :return: HTML page in which users can reset their passwords.
    """
    current_app.logger.info("Start function password_reset [VIEW]")
    if not current_user.is_anonymous:
        # If a user is signed in already, redirect them to index
        current_app.logger.info(
            "{} is already signed in. redirecting to /index...".format(
                current_user.email
            )
        )
        current_app.logger.info("End function password_reset")
        return redirect(url_for("main.index"))
    form = PasswordResetForm()
    if form.validate_on_submit():
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            # Token has timed out
            current_app.logger.error("EXCEPTION (ValueError): Token no longer valid")
            flash("This token is no longer valid.", category="warning")
            current_app.logger.info("End function password_reset")
            return redirect(url_for("auth.login"))

        current_app.logger.error("Querying for user that corresponds to given token")
        user = User.query.filter_by(id=data.get("reset")).first()
        current_app.logger.error("Finished querying for user")

        if user is None:
            # If the user associated with the token does not exist, log an error and redirect user to index
            current_app.logger.error("Requested password reset for invalid account.")
            current_app.logger.info("End function password_reset")
            return redirect(url_for("main.index"))

        elif (
            check_password_hash(
                pwhash=user.password_list.p1, password=form.password.data
            )
            or check_password_hash(
                pwhash=user.password_list.p2, password=form.password.data
            )
            or check_password_hash(
                pwhash=user.password_list.p3, password=form.password.data
            )
            or check_password_hash(
                pwhash=user.password_list.p4, password=form.password.data
            )
            or check_password_hash(
                pwhash=user.password_list.p5, password=form.password.data
            )
        ):
            # If user tries to set password to one of last five passwords, flash an error and reset the form
            current_app.logger.error(
                "{} tried to change password. Failed: Used old password.".format(
                    user.email
                )
            )
            flash(
                "Your password cannot be the same as the last 5 passwords",
                category="error",
            )
            current_app.logger.info("End function password_reset")
            return render_template("auth/reset_password.html", form=form)
        else:
            try:
                if (
                    "reset_token" in session
                    and session["reset_token"]["valid"]
                    and user.reset_password(token, form.password.data)
                ):
                    # If the token has not been used and the user submits a proper new password, reset users password
                    # and login attempts
                    user.login_attempts = 0
                    db.session.add(user)
                    db.session.commit()
                    session["reset_token"][
                        "valid"
                    ] = False  # Now that the token has been used, invalidate it
                    current_app.logger.error(
                        "Successfully changed password for {}".format(user.email)
                    )
                    flash("Your password has been updated.", category="success")
                    current_app.logger.info(
                        "End function password_reset... redirecting to login"
                    )
                    return redirect(url_for("auth.login"))

                elif "reset_token" in session and not session["reset_token"]["valid"]:
                    # If the token has already been used, flash an error message
                    current_app.logger.error(
                        "Failed to change password for {}: token invalid (already used)".format(
                            user.email
                        )
                    )
                    flash(
                        "You can only use a reset token once. Please generate a new reset token.",
                        category="error",
                    )
                    current_app.logger.info("End function password_reset")
                    return render_template("auth/reset_password.html", form=form)

                else:
                    if not "reset_token" in session:
                        flash(
                            "The reset token is timed out. Please generate a new reset token.",
                            category="error",
                        )
                    # Then the token is valid but the new password didn't meet minimum security criteria
                    else:
                        current_app.logger.error(
                            "Entered invalid new password for {}".format(user.email)
                        )
                        flash(
                            "Password must be at least 8 characters with at least 1 Uppercase Letter and 1 Number",
                            category="error",
                        )
                    current_app.logger.info("End function password_reset")
                    return render_template("auth/reset_password.html", form=form)

            except InvalidResetToken:
                current_app.logger.error(
                    "EXCEPTION (InvalidResetToken): Token no longer valid"
                )
                flash("This token is no longer valid.", category="warning")
                current_app.logger.info("End function password_reset")
                return redirect(url_for("auth.login"))

    current_app.logger.info("End function password_reset")
    return render_template("auth/reset_password.html", form=form)


@auth.route("/parse_division", methods=["GET"])
def get_sups():
    """
    Get selected division value from the request body and generate a list of supervisors for that division.
    :return: list of supervisors for division
    """
    choices = []
    if request.args["division"]:
        choices = [(0, "No Supervisor")] + get_supervisors_for_division(
            request.args["division"]
        )
    if not choices:
        sups = User.query.filter_by(is_supervisor=True).all()
        choices = [(user.id, user.email) for u in sups]
    return jsonify(choices)


@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    Renders the HTML page where users can register new accounts. If the RegistrationForm meets criteria, a new user is
    written into the database.

    :return: HTML page for registration.
    """
    current_app.logger.info("Start function register() [VIEW]")
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower(),
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            division=form.division.data,
            tag_id=form.tag.data,
            budget_code=form.budget_code.data,
            object_code=form.object_code.data,
            object_name=form.object_name.data,
            is_administrator=True,
            is_supervisor=True,
            validated=True,
        )
        db.session.add(user)
        db.session.commit()
        current_app.logger.info("Successfully registered user {}".format(user.email))
        flash("User successfully registered.", category="success")
        current_app.logger.info("End function register() [VIEW]")
        return redirect(url_for("auth.login"))
    current_app.logger.info("End function register() [VIEW]")
    return render_template("auth/register.html", form=form)


@auth.route("/user/<user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def user_profile(user_id):
    """
    Generates an editable user profile page for admins.
    :param username: The username of the user whose page is viewed/edited.
    :return: HTML page containing user information and a form to edit it.
    """
    current_app.logger.info("Start function user_profile() for user {}".format(user_id))
    # Usernames are everything in the email before the @ symbol
    # i.e. for sdhillon@records.nyc.gov, username is sdhillon
    user = User.query.filter_by(id=user_id).first()
    form = ChangeUserDataForm()
    list_of_sups = [
        (user.id, user.email) for user in User.query.filter_by(is_supervisor=True).all()
    ] + [(0, "No Supervisor")]
    if user.supervisor:
        # If a user has a supervisor, then that supervisor should be selected by default
        list_of_sups.insert(
            0,
            list_of_sups.pop(
                list_of_sups.index((user.supervisor.id, user.supervisor.email))
            ),
        )
    form.supervisor_id.choices = list_of_sups
    if not user:
        flash("No user with id {} was found".format(user_id), category="error")
        return redirect(url_for("main.user_list_page"))
    elif user.role.name == "Administrator" and user == current_user:
        # If user is admin, redirect to index and flash a message,
        # as admin should not be allowed to edit their own info through frontend.
        # This also avoids the issue that comes with the fact that admins don't have
        # a supervisor.
        flash("Admins cannot edit their own information.", category="error")
        current_app.logger.info("End function user_profile")
        return redirect(url_for("main.user_list_page"))

    if form.validate_on_submit():
        if user.id == form.supervisor_id.data:
            flash(
                "A user cannot be their own supervisor. Please revise your supervisor "
                "field.",
                category="error",
            )
        else:
            flash("User information has been updated", category="success")
            update_user_information(
                user,
                form.first_name.data,
                form.last_name.data,
                form.division.data,
                form.tag.data,
                form.supervisor_id.data,
                form.is_supervisor.data,
                form.is_active.data,
                form.role.data,
                form.budget_code.data,
                form.object_code.data,
                form.object_name.data,
            )
            current_app.logger.info(
                "{} update information for {}".format(current_user.email, user.email)
            )
            current_app.logger.info("End function user_profile")
            return redirect(url_for("auth.user_profile", user_id=user.id))
    else:
        # Pre-populate the form with current values
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.division.data = user.division
        form.tag.data = user.tag_id
        form.is_supervisor.data = user.is_supervisor
        form.supervisor_id.data = user.supervisor.email if user.supervisor else 0
        form.is_active.data = user.is_active
        form.role.data = user.role.name
        form.budget_code.data = user.budget_code
        form.object_code.data = user.object_code
        form.object_name.data = user.object_name

    current_app.logger.info("End function user_profile")

    # For ChangeLog Table
    changes = get_changelog_by_user_id(user.id)

    page = request.args.get("page", 1, type=int)
    pagination = changes.paginate(page, per_page=10, error_out=False)
    changes = pagination.items

    return render_template(
        "auth/user_page.html",
        user=user,
        form=form,
        changes=changes,
        pagination=pagination,
    )
