import logging
import os
import time
from datetime import timedelta
from logging import Formatter
from logging.handlers import RotatingFileHandler

from flask import Flask, session
from flask_bootstrap import Bootstrap
from flask_kvsession import KVSessionExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from simplekv.db.sql import SQLAlchemyStore

from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
migrate = Migrate()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = (
    "strong"  # strong: track IP address and browser agent
)
login_manager.login_view = "auth.login"


def load_db(db):
    db.create_all()


def create_app(config_name):  # App Factory
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if os.environ.get("DATABASE_URL") is None:
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get(
            "SQLALCHEMY_DATABASE_URI"
        )
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

    config[config_name].init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    db.init_app(app)
    with app.app_context():
        # load_db(db)
        store = SQLAlchemyStore(db.engine, db.metadata, "sessions")
        kvsession = KVSessionExtension(store, app)
        logfile_name = "Timeclock" + time.strftime("%Y%m%d-%H%M%S") + ".log"
        handler = RotatingFileHandler(logfile_name, maxBytes=10000, backupCount=1)
        handler.setFormatter(
            Formatter(
                "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
            )
        )
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    login_manager.init_app(app)

    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    from .health_screen import health_screen_bp as health_screen_blueprint

    app.register_blueprint(health_screen_blueprint, url_prefix="/healthscreen")

    app.permanent_session_lifetime = timedelta(minutes=15)

    @app.before_request
    def func():
        session.modified = True

    return app
