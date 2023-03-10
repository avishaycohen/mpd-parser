"""
Exceptions Module
"""


class UnicodeDeclaredError(Exception):
    """ Raised when the XML has an encoding declaration in it's manifest and the parser did not remove it """
    description = "xml has encoding declaration, lxml cannot process it"


class UnknownElementTreeParseError(Exception):
    """ Raised after a etree parse operation fails on an unexpected error """
    description = "encountered unexpected error while using lxml parsing operation"
