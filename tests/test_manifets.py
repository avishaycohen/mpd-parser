"""
Test the parsing of full manifests
"""
import os

from pytest import mark
from mpd_parser.parser import Parser

from conftest import touch_attributes, MANIFESTS_DIR


@mark.parametrize("input_file", [
    "./../manifests/bigBuckBunny-onDemend.mpd",
])
def test_mpd_tag(input_file):
    """ Test that parser works and create MPD object """
    with open(input_file, mode="r", encoding='UTF-8') as manifest_file:
        mpd_string = manifest_file.read()
        mpd = Parser.from_string(mpd_string)
        assert mpd.id is None
        assert mpd.type == "static"
        assert mpd.min_buffer_time == "PT1.500000S"
        assert mpd.media_presentation_duration == "PT0H9M55.46S"
        assert mpd.profiles == "urn:mpeg:dash:profile:isoff-on-demand:2011"
        assert len(mpd.program_informations) == 1
        assert mpd.program_informations[0].titles[0] == \
               "dashed/BigBuckBunny_1s_onDemand_2014_05_09.mpd generated by GPAC"
        assert mpd.program_informations[0].more_info_url == "http://gpac.sourceforge.net"
        assert len(mpd.periods) == 1
        assert mpd.periods[0].id is None
        assert mpd.periods[0].duration == "PT0H9M55.46S"


@mark.parametrize("input_file", [f"{MANIFESTS_DIR}{name}" for name in os.listdir(MANIFESTS_DIR)])
def test_touch_all_manifest_properties(input_file):
    """
        Test each manifest by walking over it's xml tree.
    Does not verify values.
    """
    with open(input_file, mode="r", encoding='UTF-8') as manifest_file:
        mpd_string = manifest_file.read()
        mpd = Parser.from_string(mpd_string)
        touch_attributes(mpd)

