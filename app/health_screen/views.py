from datetime import datetime, timedelta

from flask import current_app, render_template, flash, request, url_for, redirect
from flask_login import login_required, current_user

from app.health_screen import health_screen_bp
from app.health_screen.forms import HealthScreenForm, HealthScreenAdminForm
from app.health_screen.utils import process_health_screen_confirmation
from app.utils import eval_request_bool


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
            return render_template("main/health_screen_confirm.html", form=form)
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
        return redirect(url_for("main.health_screen_confirm"))
    return render_template("main/health_screen_confirm.html", form=form)


@health_screen_bp.route("/healthscreen-admin", methods=["GET", "POST"])
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

    return render_template("main/health_screen_admin.html", results=results, form=form)
