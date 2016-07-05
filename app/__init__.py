from flask import Flask, session
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from datetime import timedelta
import os
import time
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler
from flask_cors import CORS, cross_origin

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
migrate = Migrate()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = 'strong'  # strong: track IP address and browser agent
login_manager.login_view = 'auth.login'

def load_db(db):
    db.create_all()


def create_app(config_name):  # App Factory
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if os.environ.get('DATABASE_URL') is None:
        app.config[
            'SQLALCHEMY_DATABASE_URI'] = \
            app.config.get('SQLALCHEMY_DATABASE_URI')
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    db.init_app(app)
    with app.app_context():
        load_db(db)
    login_manager.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    # app.permanent_session_lifetime = timedelta(minutes=15)

    @app.before_request
    @cross_origin()
    def func():
        session.modified = True

    logfile_name = 'logfile_directory' + \
                   "Timeclock" + \
                   time.strftime("%Y%m%d-%H%M%S") + \
                   ".log"

    handler = RotatingFileHandler('LogFile', maxBytes=10000, backupCount=1)
    handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s '
                                   '[in %(pathname)s:%(lineno)d]'))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    return app
