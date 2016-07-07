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
    #('Moderator', 'Moderator'),
    ('Administrator', 'Administrator')
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
