"""
This module provides validation tools for tags and attributes.
"""
from functools import cached_property
from mpd_parser.exceptions import InvalidManifestMissingMandatoryElementError

def mandatory(func):
    """ Decorator to mark a method as mandatory. """
    @cached_property
    def wrapper(self, *args, **kwargs):
        value = func(self, *args, **kwargs)
        if value is None:
            raise InvalidManifestMissingMandatoryElementError(
                f"Mandatory attribute '{func.__name__}' is missing in {type(self).__name__}")
        return value
    return wrapper
