"""
.. module:: utils.

   :synopsis: Utility functions used throughout the application.
"""

divisions = [
    ('', ''),
    ('Administration', 'Administration'),
    ('Archives', 'Archives'),
    ('Grants', 'Grants'),
    ('Library', 'Library'),
    ('Records Management', 'Records Management'),
    ('Reference Room', 'Reference Room'),
    ('Social Media', 'Social Media'),
    ('Tech', 'Tech'),
    ("Women's", "Women's")
]

roles = [
    ('User', 'User'),
    # ('Moderator', 'Moderator'),
    ('Administrator', 'Administrator')
]

tags = [
    (0, ''),
    (1, 'Intern'),
    (2, 'Contractor'),
    (3, 'SYEP'),
    (4, 'Employee'),
    (5, 'PENCIL'),
    (6, 'Volunteer'),
    (7, 'Other')
]


class InvalidResetToken(Exception):
    pass
