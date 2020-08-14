import csv
from io import BytesIO, StringIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app import db
from app.email_notification import send_async_email, send_email
from app.models import HealthScreenResults
from app.utils import eval_request_bool

WIDTH, LENGTH = letter


def process_health_screen_confirmation(
    name, email, division, date, questionnaire_confirmation, report_to_work
):
    # Store Health Screen in DB
    health_screen = HealthScreenResults(
        name=name,
        email=email,
        division=division,
        date=date,
        questionnaire_confirmation=eval_request_bool(questionnaire_confirmation),
        report_to_work=eval_request_bool(report_to_work),
    )
    db.session.add(health_screen)
    db.session.commit()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    generate_health_screen_confirmation(
        c, health_screen
    )
    c.save()
    pdf = buffer.getvalue()
    buffer.close()

    filename = "{username}-health-check-report_to_work-{report_to_work}-{date}.pdf".format(
        username=email.split("@")[0],
        report_to_work=report_to_work.lower(),
        date=datetime.strptime(date, "%m/%d/%Y").strftime("%Y-%m-%d"),
    )
    attachment = {"filename": filename, "mimetype": "application/pdf", "file": pdf}
    send_email(
        to="healthcheck@records.nyc.gov",
        subject="(Report to Work: {report_to_work} - {date}) Health Screening Confirmation - {name}".format(
            report_to_work=report_to_work, date=date, name=name
        ),
        template="health_screen/emails/results",
        attachment=attachment,
        bcc=[email],
        health_screen_results=health_screen,
    )


def generate_health_screen_confirmation(
    canvas_field, health_screen_results
):
    canvas_field.setFont("Times-Bold", 14)
    canvas_field.drawString(220, LENGTH - 52, "Employee Health Screening")

    canvas_field.setFont("Times-Roman", 12)
    canvas_field.drawString(70, LENGTH - 110, "Name: " + health_screen_results.name)

    canvas_field.drawString(70, LENGTH - 140, "Division: " + health_screen_results.division)

    canvas_field.drawString(70, LENGTH - 170, "Date: " + health_screen_results.date.strftime("%-m/%-d/%Y"))

    if health_screen_results.questionnaire_confirmation:
        canvas_field.drawString(
            70,
            LENGTH - 200,
            "1.   Employee confirms they have completed the entire health check questionnaire: Yes",
        )
    else:
        canvas_field.drawString(
            70,
            LENGTH - 200,
            "1.   Employee confirms they have completed the entire health check questionnaire: No",
        )
    canvas_field.drawString(
        70,
        LENGTH - 230,
        "2.   Based on the questionnaire results, the employee may return to work on {date}: {report_to_work}".format(
            date=health_screen_results.date.strftime("%-m/%-d/%Y"), report_to_work=health_screen_results.report_to_work
        ),
    )
    canvas_field.drawString(
        70,
        LENGTH - 300,
        "If your response is “no”, please contact the Administration Division at healthcheck@records.nyc.gov.",
    )


def generate_health_screen_export(results):
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Date",
            "Name",
            "Email",
            "Division",
            "Completed Questionnaire?",
            "Report to Work?"
        ]
    )
    for result in results:
        writer.writerow(
            [
                result.date,
                result.name,
                result.email,
                result.division,
                result.questionnaire_confirmation,
                result.report_to_work
            ]
        )
    return buffer.getvalue().encode("UTF-8")


def generate_health_screen_daily_summary_export(results):
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Name",
            "Email",
            "Division",
            "Completed Questionnaire?",
            "Report to Work?"
        ]
    )
    for result in results:
        writer.writerow(
            [
                result[0].name,
                result[0].email,
                result[0].division,
                result[1],
                result[2]
            ]
        )
    return buffer.getvalue().encode("UTF-8")
