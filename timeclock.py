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
from faker import Faker
from app.utils import divisions, tags

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


@app.cli.command("setup_db")
def setup_db():
    """Setup the database."""
    db.create_all()
    Role.insert_roles()
    Tag.insert_tags()


@app.cli.command("reset_db")
def reset_db():
    """Reset the database."""
    db.drop_all()
    db.create_all()
    Role.insert_roles()
    Tag.insert_tags()


@app.cli.command("setup_roles")
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


@app.cli.command("create_dev_users")
def create_users():
    """Create users for development."""
    # Administrator
    faker = Faker()
    first_name = faker.first_name()
    last_name = faker.last_name()
    tag_id = tags[faker.random_int(1, len(tags) - 1)][0]
    division = faker.random_elements(elements=divisions, length=1)[0]
    administrator = User(
        email="{first_initial}{last_name}@{email_domain}".format(
            first_initial=first_name[0].lower(),
            last_name=last_name.lower(),
            email_domain=app.config["EMAIL_DOMAIN"],
        ),
        first_name=first_name,
        last_name=last_name,
        password="Change4me",
        division=division,
        role=Role.query.filter_by(name="Administrator").first(),
        tag_id=tag_id,
        is_supervisor=True,
    )
    db.session.add(administrator)
    administrator.password_list.update(administrator.password_hash)

    # Supervisor
    first_name = faker.first_name()
    last_name = faker.last_name()
    tag_id = faker.random_elements(elements=tags, length=1)[0]
    division = faker.random_elements(elements=divisions, length=1)[0]
    supervisor = User(
        email="{first_initial}{last_name}@{email_domain}".format(
            first_initial=first_name[0].lower(),
            last_name=last_name.lower(),
            email_domain=app.config["EMAIL_DOMAIN"],
        ),
        first_name=first_name,
        last_name=last_name,
        password="Change4me",
        division=division,
        role=Role.query.filter_by(name="User").first(),
        tag_id=tag_id,
        is_supervisor=True,
    )
    db.session.add(supervisor)
    supervisor.password_list.update(supervisor.password_hash)

    # Users
    for i in range(10):
        faker = Faker()
        first_name = faker.first_name()
        last_name = faker.last_name()
        tag_id = tags[faker.random_int(1, len(tags) - 1)][0]
    division = faker.random_elements(elements=divisions, length=1)[0]
    user = User(
        email="{first_initial}{last_name}@{email_domain}".format(
            first_initial=first_name[0].lower(),
            last_name=last_name.lower(),
            email_domain=app.config["EMAIL_DOMAIN"],
        ),
        first_name=first_name,
        last_name=last_name,
        password="Change4me",
        division=division,
        role=Role.query.filter_by(name="User").first(),
        tag_id=tag_id,
        is_supervisor=False,
    )
    db.session.add(user)
    user.password_list.update(user.password_hash)


db.session.commit()
