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
    (1, 'Moderator'),
    (2, 'User'),
    (3, 'Administrator')
]

tags = [
    (0, ''),
    (1, 'Intern'),
    (2, 'Contractor'),
    (3, 'SYEP'),
    (4, 'Radical'),
    (5, 'Consultant'),
    (6, 'Other')
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
