"""
Exceptions Module
"""


class UnicodeDeclaredError(Exception):
    """ Raised when the XML has an encoding declaration in it's manifest and the parser did not remove it """
    description = "xml has encoding declaration, lxml cannot process it"

class UnknownValueError(Exception):
    """ Raised when the XML parsing fails on unexpected issue, check error for more information """
    description = "lxml failed to parse manifest, verify the input"

class UnknownElementTreeParseError(Exception):
    """ Raised after a etree parse operation fails on an unexpected error """
    description = "encountered unexpected error while using lxml parsing operation"

class NoPeriodAncestorForTargetElement(Exception):
    """ Raised when trying to create a timeline from template without parent period """
    description = "targeted segment template is not nested under a periods"
