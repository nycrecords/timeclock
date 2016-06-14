from flask import render_template
from . import main


@main.app_errorhandler(404)
def page_not_found(e):
    """
    Renders the appropriate HTML page when a 404 error is encountered.
    :param e: Error message
    :return: HTML page to be shown for 404 errors.
    """
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    """
    Renders the appropriate HTML page when a 500 error is encountered.
    :param e: Error message
    :return: HTML page to be shown for 500 errors.
    """
    return render_template('500.html'), 500
