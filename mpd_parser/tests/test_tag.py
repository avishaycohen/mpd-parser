"""
Test the tag classes as standalone classes
"""
import math

import pytest
from lxml import etree
from mpd_parser.tags import ProgramInfo, BaseURL, UTCTiming


def test_program_info_tag():
    program_file_xml = """
     <ProgramInformation lang="some-lang" moreInformationURL="website">
      <Title>MultiRate</Title>
      <Title>MultiRate2</Title>
      <Source>source1</Source>
     </ProgramInformation>
     """
    element = etree.fromstring(program_file_xml)
    prog_info = ProgramInfo(element)
    assert prog_info.lang == 'some-lang'
    assert prog_info.more_info_url == 'website'
    assert prog_info.titles == ['MultiRate', 'MultiRate2']
    assert prog_info.sources == ['source1']
    assert prog_info.copy_rights == []


@pytest.mark.parametrize('xml_snippet,expected', [
    ("""<BaseURL availabilityTimeOffset="INF">bunny_46980bps/BigBuckBunny_1snonSeg.mp4</BaseURL>""",
     {
         'base_url_value':           'bunny_46980bps/BigBuckBunny_1snonSeg.mp4',
         'availability_time_offset': math.inf
     }),
    ("""<BaseURL availabilityTimeComplete="false" availabilityTimeOffset="7.000000">some-other-url</BaseURL>""",
     {
         'base_url_value':             'some-other-url',
         'availability_time_offset':   7.000000,
         'availability_time_complete': False
     })
])
def test_base_url_tag(xml_snippet, expected):
    element = etree.fromstring(xml_snippet)
    base_url = BaseURL(element)
    assert base_url.base_url_value == expected.get('base_url_value')
    assert base_url.availability_time_offset == expected.get('availability_time_offset')
    assert base_url.availability_time_complete == expected.get('availability_time_complete')


def test_utc_timing_tag():
    utc_xml = """<UTCTiming schemeIdUri="urn:mpeg:dash:utc:http-iso:2014" value="https://time.akamai.com/?iso" />"""
    element = etree.fromstring(utc_xml)
    utc_timing = UTCTiming(element)
    assert utc_timing.scheme_id_uri == 'urn:mpeg:dash:utc:http-iso:2014'
    assert utc_timing.value == 'https://time.akamai.com/?iso'
