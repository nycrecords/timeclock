from datetime import datetime
from io import BytesIO

from flask import current_app, render_template, flash, request, url_for, redirect, send_file
from flask_login import login_required, current_user

from app import db
from app.health_screen import health_screen_bp
from app.health_screen.forms import HealthScreenForm, HealthScreenAdminForm, AddHealthScreenUserForm, EditHealthScreenUserForm
from app.health_screen.utils import process_health_screen_confirmation, generate_health_screen_export, generate_health_screen_daily_summary_export
from app.utils import eval_request_bool
from ..decorators import admin_required
from app.models import HealthScreenResults, HealthScreenUsers
from sqlalchemy import asc, desc, cast, Date, and_


@health_screen_bp.route("/", methods=["GET", "POST"])
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


@health_screen_bp.route("/healthscreen-filter", methods=["GET", "POST"])
@login_required
@admin_required
def health_screen_filter():
    class HealthScreenData(object):
        date = datetime.now().strftime("%-m/%-d/%Y")

    form = HealthScreenAdminForm(obj=HealthScreenData)

    # Defaults
    results = HealthScreenResults.query.filter(HealthScreenResults.date.cast(Date) == datetime.today().date()).order_by(
        desc(HealthScreenResults.id)).all()

    if form.validate_on_submit():
        date = request.form["date"]
        if date is not "":
            try:
                date = datetime.strptime(date, "%m/%d/%Y")
            except ValueError:
                form.date.errors.append("Date must be in MM-DD-YYYY format.")
                return render_template("health_screen/health_screen_filter.html", results=[], form=form)
        name = request.form["name"]
        email = request.form["email"].lower()
        division = request.form["division"]
        report_to_work = request.form["report_to_work"]
        if report_to_work is not "":
            report_to_work = eval_request_bool(report_to_work)
        else:
            report_to_work = None

        query_filters = []
        if date:
            query_filters.append(HealthScreenResults.date.cast(Date) == date)
        if name:
            query_filters.append(HealthScreenResults.name == name)
        if email:
            query_filters.append(HealthScreenResults.email == email)
        if division:
            query_filters.append(HealthScreenResults.division == division)
        if report_to_work is not None:
            query_filters.append(HealthScreenResults.report_to_work == report_to_work)

        search_results = HealthScreenResults.query.filter(and_(*query_filters)).order_by(
            desc(HealthScreenResults.id)).all()

        if "export" in request.form:
            health_screen_export = generate_health_screen_export(search_results)
            return send_file(
                BytesIO(health_screen_export),
                attachment_filename="health_screen_results.csv",
                as_attachment=True
            )
        return render_template("health_screen/health_screen_filter.html", results=search_results, form=form)
    return render_template("health_screen/health_screen_filter.html", results=results, form=form)


@health_screen_bp.route("/healthscreen-daily-summary", methods=["GET", "POST"])
@login_required
@admin_required
def health_screen_daily_summary():
    class HealthScreenData(object):
        date = datetime.now().strftime("%-m/%-d/%Y")

    form = HealthScreenAdminForm(obj=HealthScreenData)

    date = HealthScreenData.date

    if form.validate_on_submit():
        date = request.form["date"]
        try:
            date = datetime.strptime(date, "%m/%d/%Y")
        except ValueError:
            form.date.errors.append("Date must be in MM-DD-YYYY format.")
            return render_template("health_screen/health_screen_daily_summary.html", results=[], form=form)

    results = HealthScreenResults.query.filter(HealthScreenResults.date.cast(Date) == date).order_by(
        asc(HealthScreenResults.id)).all()
    users = HealthScreenUsers.query.order_by(asc(HealthScreenUsers.name)).all()
    daily_results = []

    for user in users:
        questionnaire_confirmation = None
        report_to_work = None
        for result in results:
            if user.email == result.email:
                report_to_work = result.report_to_work
                questionnaire_confirmation = result.questionnaire_confirmation
        daily_results.append((user, questionnaire_confirmation, report_to_work))

    if "export" in request.form:
        health_screen_export = generate_health_screen_daily_summary_export(daily_results)
        return send_file(
            BytesIO(health_screen_export),
            attachment_filename="health_screen_results_{}.csv".format(date.strftime("%-m/%-d/%Y")),
            as_attachment=True
        )
    return render_template("health_screen/health_screen_daily_summary.html", results=daily_results, form=form)


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
