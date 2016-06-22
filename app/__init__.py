from flask import Flask, session
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from datetime import timedelta
from .models import Role, Tag
import os


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
migrate = Migrate()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = 'strong'  # strong: track IP address and browser agent
login_manager.login_view = 'auth.login'


def load_db(db):
    db.drop_all()
    # db.create_all()
    # Role.insert_roles()
    # Tag.insert_tags()


def create_app(config_name):                        # App Factory
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    print(app.config.get(
            'SQLALCHEMY_DATABASE_URI'))
    print(app.config.get(
            'DATABASE_URL'))

    if os.environ.get('DATABASE_URL') is None:
        app.config[
            'SQLALCHEMY_DATABASE_URI'] = app.config.get(
            'SQLALCHEMY_DATABASE_URI'
        )
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    migrate.init_app(app, db)
    db.init_app(app)
    with app.app_context():
        load_db(db)
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

