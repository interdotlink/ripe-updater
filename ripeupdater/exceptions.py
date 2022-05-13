# -*- coding: utf-8 -*-

"""
custom exception
"""


class RipeUpdaterException(Exception):
    """
    exception base class
    """
    pass


class ErrorSmallPrefix(RipeUpdaterException):
    """
    raised if prefix is too small to be handled
    """
    pass


class MissingDataFromNetbox(RipeUpdaterException):
    """
    raised if data cannot be pulled from netbox
    """
    pass


class NotRoutedNetwork(RipeUpdaterException):
    """
    raised if prefix is not meant to be in RIPE DB, e.g. RFC1918
    """
    pass


class BadRequest(RipeUpdaterException):
    """
    raised if invalid request
    """
    pass


class ConfigError(RipeUpdaterException):
    """
    raised if config data is missing
    """
    pass


class RipeDBError(RipeUpdaterException):
    """
    raised if data could not be querried from RIPE DB
    """
    pass
