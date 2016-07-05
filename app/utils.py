"""
.. module:: utils.

   :synopsis: Utiltiy functions used throughout the application.
"""

divisions = [
    ('', ''),
    ('Records Management', 'Records Management'),
    ('Archives', 'Archives'),
    ('Grants', 'Grants'),
    ('Library', 'Library'),
    ('Executive', 'Executive'),
    ('MIS/Web', 'MIS/Web'),
    ('Administration', 'Administration')
]

roles = [
    ('User', 'User'),
    ('Moderator', 'Moderator'),
    ('Administrator', 'Administrator')
]

tags = [
    ('', ''),
    ('Intern', 'Intern'),
    ('Contractor', 'Contractor'),
    ('SYEP', 'SYEP'),
    ('Radical', 'Radical'),
    ('Consultant', 'Consultant'),
    ('Other', 'Other')
]


class InvalidResetToken(Exception):
    pass


def date_handler(obj):
    """
    Convert date to ISO Format.

    :param obj: Datetime object
    :return: ISO Format datetime OR TypeError
    """
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError
