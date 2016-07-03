from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app
from . import login_manager
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
import re
from . import db
from .utils import InvalidResetToken


class Permission:
    """
    Used to provide user permissions and check to ensure users have proper rights.
    """
    USER = 0x01  # 0b00000001
    ADMINISTER = 0x80  # 0b10000000


class Role(db.Model):
    """
    Specifies the roles a user can have (normal User, Department Head(Moderator), Administrator).
    """
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        """
        Instantiates the roles column by initializing the User, Moderator, and Administrator rows.
        :return: None
        """
        roles = {
            'User': (Permission.USER, True),
            'Moderator': (Permission.ADMINISTER, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    """
    Specifies properties and functions of a TimeClock User.
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    # TODO: ENSURE USER EMAILS ARE xxx@records.nyc.gov
    # TODO: PAID TAG - necessary? We have a "pays" table, just associate a $0 pay.
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    clocked_in = db.Column(db.Boolean, default=False)
    validated = db.Column(db.Boolean, default=False)
    division = db.Column(db.String(128))
    login_attempts = db.Column(db.Integer, default=0)

    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'))
    old_passwords = db.Column(db.Integer, db.ForeignKey('passwords.id'))
    events = db.relationship('Event', backref='user', lazy='dynamic')
    pays = db.relationship('Pay', backref='user', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
                self.validated = True
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()
        self.password_list = Password(p1='', p2='', p3='', p4='', p5='', last_changed=datetime.now())

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """
        Creates and stores password hash.
        :param password: String to hash.
        :return: None.
        """
        self.password_hash = generate_password_hash(password)

    # generates token with default validity for 1 hour
    def generate_reset_token(self, expiration=3600):
        """
        Generates a token users can use to reset their accounts if locked out.
        :param expiration: Seconds the token is valid for after being created (default one hour).
        :return: the token.
        """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

        # verifies the token and if valid, resets password

    def reset_password(self, token, new_password):
        """
        Resets a user's password.
        :param token: The token to verify.
        :param new_password: The password the user will have after resetting.
        :return: True if operation is successful, false otherwise.
        """
        # checks if the new password is at least 8 characters with at least 1 UPPERCASE AND 1 NUMBER
        if not re.match(r'^(?=.*?\d)(?=.*?[A-Z])(?=.*?[a-z])[A-Za-z\d]{8,128}$', new_password):
            return False
        # If the password has been changed within the last second, the token is invalid.
        if (datetime.now() - self.password_list.last_changed).seconds < 1:
            current_app.logger.error('User {} tried to re-use a token.'.format(self.email))
            raise InvalidResetToken
        self.password = new_password
        self.password_list.update(self.password_hash)
        db.session.add(self)
        return True

    def verify_password(self, password):
        """
        Checks user-entered passwords against hashes stored in the database.
        :param password: The user-entered password.
        :return: True if user has entered the correct password, False otherwise.
        """
        return check_password_hash(self.password_hash, password)

    def can(self, permissions):
        """
        Checks to see if a user has access to certain permissions.
        :param permissions: An int that specifies the permissions we are checking to see whether or not the user has.
        :return: True if user is authorized for the given permission, False otherwise.
        """
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        """
        Checks to see whether the user is an administrator.
        :return: True if the user is an administrator, False otherwise.
        """
        return self.can(Permission.ADMINISTER)

    def __repr__(self):
        return '<User %r>' % self.email

    @staticmethod
    def generate_fake(count=100):
        """
        Used to generate fake users.
        """
        from sqlalchemy.exc import IntegrityError
        from random import seed, randint

        import forgery_py
        seed()
        tag_count = Tag.query.count()
        for i in range(count):
            t = Tag.query.offset(randint(0, tag_count - 1)).first()
            first = forgery_py.name.first_name()
            last = forgery_py.name.last_name()
            e = (first[:1] + last + '@records.nyc.gov').lower()
            u = User(email=e,
                     password=forgery_py.lorem_ipsum.word(),  # change to set a universal password for QA testing
                     first_name=first,
                     last_name=last,
                     tag=t
                     )
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class AnonymousUser(AnonymousUserMixin):
    """
    An anonymous user class to simplify user processes in other code.
    """

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


class Event(db.Model):
    """
    Model for clock events (in or out).
    """
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Boolean)  # True if clocking in, false if clocking out
    time = db.Column(db.DateTime)  # Time of clock in/out event
    note = db.Column(db.String(120))
    ip = db.Column(db.String(120))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        if not self.note:
            self.note = ""
        in_or_out = "IN" if self.type else "OUT"
        time_string = self.time.strftime("%b %d, %Y %H:%M:%S %p")
        return time_string + " | " + self.user.email + " | " + in_or_out + " | " + self.note

    @staticmethod
    def generate_fake(count=100):
        """
        Generates fake event instances.
        :param count: Number of instances to generate
        :return: None.
        """
        from random import seed, randint
        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            u.clocked_in = not u.clocked_in
            e = Event(user=u, type=u.clocked_in,
                      time=datetime(
                          year=randint(2004, 2016),
                          month=randint(1, 6),
                          day=randint(1, 28),
                          hour=randint(0, 23),
                          minute=randint(0, 59),
                      )
                      )
            db.session.add_all([e, u])
            db.session.commit()


class Pay(db.Model):
    """
    A model for user pay rates.
    """
    __tablename__ = 'pays'
    id = db.Column(db.Integer, primary_key=True)
    rate = db.Column(db.Float)
    start = db.Column(db.Date)
    end = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Tag(db.Model):
    """
    A model for different user tags.
    """
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='tag', lazy='dynamic')

    @staticmethod
    def insert_tags():
        tags = ['Intern', 'Contractor', 'SYEP', 'Radical', 'Consultant', 'Other']
        for t in tags:
            tag = Tag.query.filter_by(name=t).first()
            if tag is None:
                tag = Tag(name=t)
            db.session.add(tag)
        db.session.commit()

    def __repr__(self):
        return '<Tag %r>' % self.name


class Password(db.Model):
    __tablename__ = 'passwords'
    id = db.Column(db.Integer, primary_key=True)
    p1 = db.Column(db.String(128))
    p2 = db.Column(db.String(128))
    p3 = db.Column(db.String(128))
    p4 = db.Column(db.String(128))
    p5 = db.Column(db.String(128))
    last_changed = db.Column(db.DateTime)
    users = db.relationship('User', backref='password_list', lazy='dynamic')

    def update(self, password_hash):
        self.p5 = self.p4
        self.p4 = self.p3
        self.p3 = self.p2
        self.p2 = self.p1
        self.p1 = password_hash
        self.last_changed = datetime.now()


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
