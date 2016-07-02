"""
.. module:: utils.

   :synopsis: Utiltiy functions used throughout the application.
"""


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
