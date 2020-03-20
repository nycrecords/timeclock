#!/usr/bin/env python
"""
.. module:: manage.

   :synopsis: Provides CLI for the timeclock application
"""

import os
from app import create_app, db
from app.models import User, Role, Event, Pay, Tag, Password, ChangeLog, Vacation
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from faker import Faker 
from app.auth.modules import create_user
from app.utils import divisions, roles, tags 

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Event=Event, Pay=Pay, Tag=Tag, Password=Password,
                ChangeLog=ChangeLog, Vacation=Vacation)
manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():  # Grinberg's unit tests, we can del if need be  - Sarvar
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@manager.command
def db_setup():
    """Set up the database"""
    Role.insert_roles()
    Tag.insert_tags()

@manager.command
def reset_db():
    """Empties the database and generates it again with db_setup"""
    db.drop_all()
    db.create_all()
    db_setup()

@manager.command
def set_roles():
    """Ensures that roles are added in the proper order"""
    Role.query.delete()
    u = Role(name="User", permissions=0x01, id=1)
    m = Role(name="Moderator", permissions=0x80, id=2)
    a = Role(name="Administrator", permissions=0xff, id=3)
    db.session.add(u)
    db.session.add(m)
    db.session.add(a)
    db.session.commit()

@manager.command
def create_users():
    # Administrator
    faker = Faker()
    fname = faker.first_name()
    lname = faker.last_name()
    u = User(
        email=fname[0]+lname+'records.nyc.gov',
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
        email=fname[0]+lname+'records.nyc.gov',
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
            email=fname[0]+lname+'records.nyc.gov',
            first_name=lname,
            last_name=lname,
            password='Change4me',
            division=divisions[faker.random_int(0, 9)],
            role=Role.query.filter_by(name='User').first(),
            # tag_id=tags[faker.random_int(0,7)]
            tag_id = None,
            is_supervisor=False
        )
        db.session.add(u)
        db.session.commit()
        u.password_list.update(u.password_hash)


    #Supervisor 
    # faker = Faker()
    # fname = faker.first_name()
    # lname = faker.last_name()
    # create_user(
    #         fname[0]+lname+'records.nyc.gov',
    #         'Change4me',
    #         faker.first_name(),
    #         faker.last_name(),
    #         divisions[faker.random_int(0, 9)],
    #         'User',
    #         None,
    #         True,
    #         1)
# Users
    # for i in range(10):
    #     faker = Faker()
    #     fname = faker.first_name()
    #     lname = faker.last_name()
    #     create_user(
    #         fname[0]+lname+'records.nyc.gov',
    #         'Change4me',
    #         faker.first_name(),
    #         faker.last_name(),
    #         divisions[faker.random_int(0, 9)],
    #         'User',
    #         None,
    #         False,
    #         1
    #     )

if __name__ == '__main__':
    manager.run()
