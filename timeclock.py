import os

import click
from flask_migrate import Migrate

from app import create_app, db
from app.models import (
    User,
    Permission,
    Event,
    Pay,
    Password,
    ChangeLog,
    Vacation,
    Role,
    Tag,
)

app = create_app(os.getenv("FLASK_CONFIG") or "default")
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(
        app=app,
        db=db,
        User=User,
        Permission=Permission,
        Event=Event,
        Pay=Pay,
        Password=Password,
        ChangeLog=ChangeLog,
        Vacation=Vacation,
        Role=Role,
        Tag=Tag,
    )


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest

    tests = unittest.TestLoader().discover("tests")
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command()
def db_setup():
    """Setup the database."""
    db.create_all()
    Role.insert_roles()
    Tag.insert_tags()


@app.cli.command()
def reset_db():
    """Reset the database."""
    db.drop_all()
    db.create_all()
    Role.insert_roles()
    Tag.insert_tags()


@app.cli.command()
def setup_roles():
    """Insert roles in the proper order."""
    Role.query.delete()
    user = Role(name="User", permissions=0x01, id=1)
    moderator = Role(name="Moderator", permissions=0x80, id=2)
    administrator = Role(name="Administrator", permissions=0xFF, id=3)
    db.session.add(user)
    db.session.add(moderator)
    db.session.add(administrator)
    db.session.commit()
