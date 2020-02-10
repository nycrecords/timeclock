# # -*- coding: utf-8 -*-
# """Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_webpack import Webpack
from flask_wtf.csrf import CSRFProtect
from flask import Flask, session
from flask_bootstrap import Bootstrap
from flask_kvsession import KVSessionExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from simplekv.db.sql import SQLAlchemyStore

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
migrate = Migrate()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = (
    "strong"
)  # strong: track IP address and browser agent
login_manager.login_view = "auth.login"
bcrypt = Bcrypt()
csrf_protect = CSRFProtect()
cache = Cache()
debug_toolbar = DebugToolbarExtension()
webpack = Webpack()
