from datetime import datetime, timedelta

from flask import current_app, render_template, flash, request, url_for, redirect
from flask_login import login_required, current_user

from app import db
from app.health_screen import health_screen_bp
from app.health_screen.forms import HealthScreenForm, HealthScreenAdminForm, AddHealthScreenUserForm, EditHealthScreenUserForm
from app.health_screen.utils import process_health_screen_confirmation
from app.utils import eval_request_bool
from ..decorators import admin_required
from app.models import HealthScreenResults, HealthScreenUsers
from sqlalchemy import asc, desc


@health_screen_bp.route("/healthscreen", methods=["GET", "POST"])
def health_screen_confirm():
    class HealthScreenData(object):
        date = datetime.now().strftime("%-m/%-d/%Y")

    form = HealthScreenForm(obj=HealthScreenData)

    if form.validate_on_submit():
        if (
            not request.form.get("email", "").split("@")[-1].lower()
            == current_app.config["EMAIL_DOMAIN"]
        ):
            form.email.errors.append(
                "You must enter a {email_domain} email address.".format(
                    email_domain=current_app.config["EMAIL_DOMAIN"]
                )
            )
            return render_template("health_screen/health_screen_confirm.html", form=form)
        name = request.form["name"]
        email = request.form["email"].lower()
        date = request.form["date"]
        division = request.form["division"]
        questionnaire_confirmation = request.form["questionnaire_confirmation"]
        report_to_work = request.form["report_to_work"]

        # Generate and email PDF
        process_health_screen_confirmation(
            name, email, division, date, questionnaire_confirmation, report_to_work
        )

        flash(
            "Screening completed. You will receive a confirmation email shortly.",
            category="success",
        )
        return redirect(url_for("health_screen.health_screen_confirm"))
    return render_template("health_screen/health_screen_confirm.html", form=form)


@health_screen_bp.route("/healthscreen-admin", methods=["GET", "POST"])
@login_required
@admin_required
def health_screen_admin():
    class HealthScreenData(object):
        date = datetime.now().strftime("%-m/%-d/%Y")

    form = HealthScreenAdminForm(obj=HealthScreenData)

    if form.validate_on_submit():
        name = request.form["name"]
        email = request.form["email"].lower()
        date = request.form["date"]
        division = request.form["division"]
        report_to_work = eval_request_bool(request.form["report_to_work"])

    # defaults
    users = HealthScreenUsers.query.order_by(desc(HealthScreenUsers.name)).all()
    results = HealthScreenResults.query.all()

    return render_template("health_screen/health_screen_admin.html", results=results, form=form, users=users)


@health_screen_bp.route("/healthscreen-users", methods=["GET", "POST"])
@login_required
@admin_required
def health_screen_users():
    users = HealthScreenUsers.query.order_by(asc(HealthScreenUsers.name)).all()
    return render_template("health_screen/health_screen_users.html", users=users)


@health_screen_bp.route("/healthscreen-users/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_health_screen_user():
    form = AddHealthScreenUserForm()

    if form.validate_on_submit():
        user = HealthScreenUsers(
            name=request.form["name"],
            email=request.form["email"],
            division=request.form["division"]
        )
        db.session.add(user)
        db.session.commit()
        flash(
            "New health screen user created.",
            category="success",
        )
        return redirect(url_for("health_screen.health_screen_users"))
    return render_template("health_screen/add_health_screen_user.html", form=form)


@health_screen_bp.route("/healthscreen-users/edit/<user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_health_screen_user(user_id):
    user = HealthScreenUsers.query.filter_by(id=user_id).one()

    form = EditHealthScreenUserForm()
    form.name.data = user.name
    form.email.data = user.email
    form.division.data = user.division

    if form.validate_on_submit():
        user.name = request.form["name"]
        user.email = request.form["email"]
        user.division = request.form["division"]
        db.session.add(user)
        db.session.commit()
        flash(
            "User information edited.",
            category="success",
        )
        return redirect(url_for("health_screen.health_screen_users"))
    return render_template("health_screen/edit_health_screen_user.html", form=form, user=user)


@health_screen_bp.route("/healthscreen-users/remove/<user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def remove_health_screen_user(user_id):
    user = HealthScreenUsers.query.filter_by(id=user_id).one()
    user_name = user.name
    db.session.delete(user)
    db.session.commit()
    flash(
        "User {} Removed.".format(user_name),
        category="success",
    )
    return redirect(url_for("health_screen.health_screen_users"))
