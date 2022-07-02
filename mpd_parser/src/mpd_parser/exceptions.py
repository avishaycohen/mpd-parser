"""
Exceptions Module
"""


class UnicodeDeclaredError(Exception):
    """ Raised when the XML has an encoding declaration in it's manifest and the parser did not remove it """
    description = "xml has encoding declaration, lxml cannot process it"
