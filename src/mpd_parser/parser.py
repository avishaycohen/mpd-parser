"""
Main module of the package, Parser class
"""
from re import Match, sub
from urllib.request import urlopen

from lxml import etree

from mpd_parser.exceptions import UnicodeDeclaredError, UnknownElementTreeParseError
from mpd_parser.tags import MPD

ENCODING_PATTERN = r'<\?.*?\s(encoding=\"\S*\").*\?>'


class Parser:
    """
        Parser class, holds factories to work with manifest files.
    can parse manifests in the following formats:
        1. from string
        2. from file
        3. from url
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
        except Exception as err:
            raise UnknownElementTreeParseError() from err
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
        except Exception as err:
            raise UnknownElementTreeParseError() from err
        return MPD(tree.getroot())

    @classmethod
    def from_url(cls, url: str) -> MPD:
        """
            Generate a parsed mpd object from a given URL
        Args:
            url (str): the url of the file to parse

        Returns:
            an object representing the MPD tag and all it's XML goodies
        """
        try:
            with urlopen(url) as manifest_file:
                tree = etree.parse(manifest_file)
        except ValueError as err:
            if "Unicode" in err.args[0]:
                raise UnicodeDeclaredError() from err
        except Exception as err:
            raise UnknownElementTreeParseError() from err
        return MPD(tree.getroot())

    @classmethod
    def to_string(cls, mpd: MPD) -> str:
        """ generate a string xml from a given MPD tag object

        Args:
                mpd: MPD object created by one of the parser factories
        Returns:
                a string representation of the MPD object, xml formatted dash mpeg manifest
        """
        return etree.tostring(mpd.element).decode("utf-8")
