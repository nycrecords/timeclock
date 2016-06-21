from flask import Flask, session
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from datetime import timedelta

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
migrate = Migrate()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = 'strong'  # strong: track IP address and browser agent
login_manager.login_view = 'auth.login'


def create_app(config_name):                        # App Factory
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    db.init_app(app)
    login_manager.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix="/auth")

    app.permanent_session_lifetime = timedelta(minutes=15)

    @app.before_request
    def func():
        session.modified = True

    return app

