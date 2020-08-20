from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import xlsxwriter

from app import db
from app.email_notification import send_email
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
    generate_health_screen_confirmation(c, health_screen)
    c.save()
    pdf = buffer.getvalue()
    buffer.close()

    filename = "{username}-health-check-report_to_work-{report_to_work}-{date}.pdf".format(
        username=email.split("@")[0],
        report_to_work="Yes" if report_to_work else "No",
        date=datetime.strptime(date, "%m/%d/%Y").strftime("%Y-%m-%d"),
    )
    attachment = {"filename": filename, "mimetype": "application/pdf", "file": pdf}
    send_email(
        to="healthcheck@records.nyc.gov",
        subject="(Report to Work: {report_to_work} - {date}) Health Screening Confirmation - {name}".format(
            report_to_work="Yes" if report_to_work else "No", date=date, name=name
        ),
        template="health_screen/emails/results",
        attachment=attachment,
        bcc=[email],
        health_screen_results=health_screen,
        sender="healthcheck@records.nyc.gov"
    )


def generate_health_screen_confirmation(canvas_field, health_screen_results):
    canvas_field.setFont("Times-Bold", 14)
    canvas_field.drawString(220, LENGTH - 52, "Employee Health Screening")

    canvas_field.setFont("Times-Roman", 12)
    canvas_field.drawString(70, LENGTH - 110, "Name: " + health_screen_results.name)

    canvas_field.drawString(
        70, LENGTH - 140, "Division: " + health_screen_results.division
    )

    canvas_field.drawString(
        70, LENGTH - 170, "Date: " + health_screen_results.date.strftime("%-m/%-d/%Y")
    )

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
    if health_screen_results.report_to_work:
        canvas_field.drawString(
            70,
            LENGTH - 230,
            "2.   Based on the questionnaire results, the employee may return to work on {date}: Yes".format(
                date=health_screen_results.date.strftime("%-m/%-d/%Y")
            )
        )
    else:
        canvas_field.drawString(
            70,
            LENGTH - 230,
            "2.   Based on the questionnaire results, the employee may return to work on {date}: No".format(
                date=health_screen_results.date.strftime("%-m/%-d/%Y")
            )
        )
    canvas_field.drawString(
        70,
        LENGTH - 300,
        "If your response is “no”, please contact the Administration Division at healthcheck@records.nyc.gov.",
    )


def generate_health_screen_export(results, filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({"bold": True})
    red = workbook.add_format({"font_color": "red"})
    green = workbook.add_format({"font_color": "green"})

    worksheet.write("A1", "Date", bold)
    worksheet.write("B1", "Name", bold)
    worksheet.write("C1", "Email", bold)
    worksheet.write("D1", "Division", bold)
    worksheet.write("E1", "Completed Questionnaire?", bold)
    worksheet.write("F1", "Report to Work?", bold)

    row = 1
    col = 0

    for result in results:
        if result.report_to_work:
            worksheet.write(row, col, datetime.strftime(result.date, '%m/%d/%Y'), green)
            worksheet.write(row, col + 1, result.name, green)
            worksheet.write(row, col + 2, result.email, green)
            worksheet.write(row, col + 3, result.division, green)
            worksheet.write(row, col + 4, "Yes", green)
            worksheet.write(row, col + 5, "Yes", green)
        elif not result.report_to_work and result.questionnaire_confirmation:
            worksheet.write(row, col, datetime.strftime(result.date, '%m/%d/%Y'), red)
            worksheet.write(row, col + 1, result.name, red)
            worksheet.write(row, col + 2, result.email, red)
            worksheet.write(row, col + 3, result.division, red)
            worksheet.write(row, col + 4, "Yes", red)
            worksheet.write(row, col + 5, "No", red)
        else:
            worksheet.write(row, col, datetime.strftime(result.date, '%m/%d/%Y'))
            worksheet.write(row, col + 1, result.name)
            worksheet.write(row, col + 2, result.email)
            worksheet.write(row, col + 3, result.division)
            worksheet.write(row, col + 4, "No")
            worksheet.write(row, col + 4, "N/A")
        row += 1

    workbook.close()
    with open(filename, "rb") as f:
        data = f.read()

    return data


def generate_health_screen_daily_summary_export(results, filename):
    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()

    bold = workbook.add_format({"bold": True})
    red = workbook.add_format({"font_color": "red"})
    green = workbook.add_format({"font_color": "green"})

    worksheet.write("A1", "Name", bold)
    worksheet.write("B1", "Email", bold)
    worksheet.write("C1", "Division", bold)
    worksheet.write("D1", "Completed Questionnaire?", bold)
    worksheet.write("E1", "Report to Work?", bold)

    row = 1
    col = 0

    for result in results:
        if result[3]:
            worksheet.write(row, col, result[1].name, green)
            worksheet.write(row, col + 1, result[1].email, green)
            worksheet.write(row, col + 2, result[1].division, green)
            worksheet.write(row, col + 3, "Yes", green)
            worksheet.write(row, col + 4, "Yes", green)
        elif not result[3] and result[2]:
            worksheet.write(row, col, result[1].name, red)
            worksheet.write(row, col + 1, result[1].email, red)
            worksheet.write(row, col + 2, result[1].division, red)
            worksheet.write(row, col + 3, "Yes", red)
            worksheet.write(row, col + 4, "No", red)
        else:
            worksheet.write(row, col, result[1].name)
            worksheet.write(row, col + 1, result[1].email)
            worksheet.write(row, col + 2, result[1].division)
            worksheet.write(row, col + 3, "No")
            worksheet.write(row, col + 4, "N/A")
        row += 1
    workbook.close()
    with open(filename, "rb") as f:
        data = f.read()
    return data
