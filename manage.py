#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Role, Event, Pay, Tag, Password
from flask.ext.script import Manager, Shell
from flask.ext.migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Event=Event, Pay=Pay, Tag=Tag, Password=Password)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():  # Grinberg's unit tests, we can del if need be  - Sarvar
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

def db_setup():
    """Sets up the database"""
    db.create_all()
    Role.insert_roles()
    Tag.insert_tags()

if __name__ == '__main__':
    manager.run()
