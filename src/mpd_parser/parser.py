"""
Main module of the package, Parser class
"""
from re import Match, sub
from lxml import etree

from mpd_parser.exceptions import UnicodeDeclaredError
from mpd_parser.tags import MPD

ENCODING_PATTERN = r'<\?.*?\s(encoding=\"\S*\").*\?>'


class Parser:
    """
    Parser class, holds factories to work with manifest files.
    can parse:
    1. from string - using the from_string method
    2. from file - TBA
    3. from url - TBA
    """

    @classmethod
    def from_string(cls, manifest_as_string: str) -> MPD:
        """generate a parsed mpd object from a given string

        Args:
            manifest_as_string (str): string repr of a manifest file.

        Returns:
            an object representing the MPD tag and all it's XML goodies
        """
        # remove encoding declaration from manifest if exist
        encoding = []
        if "encoding" in manifest_as_string:
            def cut_and_burn(match: Match) -> str:
                """ Helper to save the removed encoding"""
                encoding.append(match)
                return ""

            manifest_as_string = sub(ENCODING_PATTERN, cut_and_burn, manifest_as_string)
        try:
            root = etree.fromstring(manifest_as_string)
        except ValueError as err:
            if "Unicode" in err.args[0]:
                raise UnicodeDeclaredError() from err
        if encoding:
            return MPD(root, encoding=encoding[0].groups()[0])
        return MPD(root)

    @classmethod
    def from_file(cls, manifest_file_name: str) -> MPD:
        """
            Generate a parsed mpd object from a given file name
        Args:
            manifest_file_name (str): file name to parse

        Returns:
            an object representing the MPD tag and all it's XML goodies
        """
        try:
            tree = etree.parse(manifest_file_name)
        except ValueError as err:
            if "Unicode" in err.args[0]:
                raise UnicodeDeclaredError() from err
        return MPD(tree.getroot())

    @classmethod
    def to_string(cls, mpd: MPD) -> str:
        """ generate a string xml from a given MPD tag object

        Args:
                mpd: MPD object created by one of the parser factories
        Returns:
                a string representation of the MPD object, it's an xml and dash mpeg manifest
        """
        return etree.tostring(mpd.element).decode("utf-8")
