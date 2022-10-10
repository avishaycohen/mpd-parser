import pytest
from lxml import etree

from mpd_parser.parser import Parser
from mpd_parser.tags import Subset


@pytest.mark.parametrize("input_file", [
    "./../manifests/bigBuckBunny-onDemend.mpd",
])
class TestTag:
    """ generic test class for a tag """


class TestMPD(TestTag):
    """ test attribute assignment for MPD tag """

    def test_min_buffer_time(self, input_file):
        """ test changes to min_buffer_time attribute """
        with open(input_file, mode="r", encoding='UTF-8') as manifest_file:
            mpd_string = manifest_file.read()
            mpd = Parser.from_string(mpd_string)
            orig_value = mpd.min_buffer_time
            mpd.min_buffer_time = 'something else'
            assert mpd.min_buffer_time != orig_value
            assert mpd.element.attrib['minBufferTime'] == 'something else'


class TestProgramInfo(TestTag):
    """ test class for program information tag assignment"""

    def test_more_info_url(self, input_file):
        """ this test an existing attrib value being changed """
        with open(input_file, mode="r", encoding='UTF-8') as manifest_file:
            mpd_string = manifest_file.read()
            mpd = Parser.from_string(mpd_string)
            prog_info_list = mpd.program_informations
            orig_value = prog_info_list[0].more_info_url
            prog_info_list[0].more_info_url = "best-urls"
            assert prog_info_list[0].more_info_url != orig_value
            assert prog_info_list[0].element.attrib['moreInformationURL'] == 'best-urls'
            assert mpd.program_informations[0].element.attrib['moreInformationURL'] == 'best-urls'

    def test_lang(self, input_file):
        """ this test a new attrib that is being set """
        with open(input_file, mode="r", encoding='UTF-8') as manifest_file:
            mpd_string = manifest_file.read()
            mpd = Parser.from_string(mpd_string)
            prog_info_list = mpd.program_informations
            orig_value = prog_info_list[0].lang
            prog_info_list[0].lang = 'eng'
            assert prog_info_list[0].lang != orig_value
            assert prog_info_list[0].element.attrib['lang'] == 'eng'
            assert mpd.program_informations[0].element.attrib['lang'] == 'eng'

    def test_titles(self, input_file):
        """ test text value change """
        with open(input_file, mode="r", encoding='UTF-8') as manifest_file:
            mpd_string = manifest_file.read()
            mpd = Parser.from_string(mpd_string)
            prog_info_list = mpd.program_informations
            title_list = prog_info_list[0].titles
            first_title = title_list[0]
            orig_value = first_title.text
            first_title.text = 'new-text'
            assert first_title.text != orig_value
            assert first_title.element.text == 'new-text'
            assert mpd.program_informations[0].titles[0].text == 'new-text'


class TestListValueAssignment:
    """ test changing an attribute with a list type """

    def test_list_value_assignment(self):
        """ test changing an attribute with a list type """
        subset_xml = '<Subset id="1" contains="100,101"/>'
        element = etree.fromstring(subset_xml)
        subset = Subset(element)
        assert subset.contains == [100, 101]
        subset.contains = [1, 2]
        assert subset.element.attrib['contains'] == "1,2"

    def test_list_remove_value_assignment(self):
        """ test removing an attribute """
        subset_xml = '<Subset id="1" contains="100,101"/>'
        element = etree.fromstring(subset_xml)
        subset = Subset(element)
        assert subset.contains == [100, 101]
        subset.contains = None
        assert subset.element.attrib.get('contains') is None

    def test_add_list_to_non_exist_value(self):
        """ test adding a list attribute to one that doesn't exist yet """
        subset_xml = '<Subset id="1"/>'
        element = etree.fromstring(subset_xml)
        subset = Subset(element)
        subset.contains = [1, 2, 3]
        assert subset.element.attrib['contains'] == '1,2,3'
