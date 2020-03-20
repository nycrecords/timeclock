import os

import click
from flask_migrate import Migrate

from app import create_app, db
from app.models import User, Permission, Event, Pay, Password, ChangeLog, Vacation, Role, Tag
from faker import Faker 
from app.utils import divisions, roles, tags

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

@app.cli.command()
def create_users():
    # Administrator
    faker = Faker()
    fname = faker.first_name()
    lname = faker.last_name()
    u = User(
        email=fname[0].lower()+lname.lower()+'@records.nyc.gov',
        first_name=fname,
        last_name=lname,
        password='Change4me',
        division=divisions[faker.random_int(0, 9)],
        role=Role.query.filter_by(name='Administrator').first(),
        # tag_id=tags[faker.random_int(0,7)]
        tag_id = None,
        is_supervisor=True
    )
    db.session.add(u)
    db.session.commit()
    u.password_list.update(u.password_hash)

    #Supervisor 
    faker = Faker()
    fname = faker.first_name()
    lname = faker.last_name()
    u = User(
        email=fname[0].lower()+lname.lower()+'@records.nyc.gov',
        first_name=lname,
        last_name=lname,
        password='Change4me',
        division=divisions[faker.random_int(0, 9)],
        role=Role.query.filter_by(name='User').first(),
        # tag_id=tags[faker.random_int(0,7)]
        tag_id = None,
        is_supervisor=True
    )
    db.session.add(u)
    db.session.commit()
    u.password_list.update(u.password_hash)


    # Users
    for i in range(10):

        faker = Faker()
        fname = faker.first_name()
        lname = faker.last_name()
        u = User(
            email=fname[0].lower()+lname.lower()+'@records.nyc.gov',
            first_name=lname,
            last_name=lname,
            password='Change4me',
            division=divisions[faker.random_int(0, 9)],
            role=Role.query.filter_by(name='User').first(),
            # tag_id=tags[faker.random_int(0,7)]
            tag_id = 0,
            is_supervisor=False
        )
        db.session.add(u)
        db.session.commit()
        u.password_list.update(u.password_hash)