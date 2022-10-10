"""
Test the tag classes as standalone classes
"""
import math

import pytest
from lxml import etree
from mpd_parser.tags import ProgramInfo, BaseURL, UTCTiming, SegmentTemplate, Event, Subset


def test_program_info_tag():
    """ Test program info tag """
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
    assert len(prog_info.titles) == 2
    assert prog_info.titles[0].text == 'MultiRate'
    assert prog_info.titles[1].text == 'MultiRate2'
    assert prog_info.sources[0].text == 'source1'
    assert prog_info.copy_rights == []


@pytest.mark.parametrize('xml_snippet,expected', [
    ("""<BaseURL availabilityTimeOffset="INF">bunny_46980bps/BigBuckBunny_1snonSeg.mp4</BaseURL>""",
     {
         'base_url_value':           'bunny_46980bps/BigBuckBunny_1snonSeg.mp4',
         'availability_time_offset': math.inf
     }),
    ('<BaseURL availabilityTimeComplete="false" availabilityTimeOffset="7.000000">' \
     'some-other-url</BaseURL>',
     {
         'base_url_value':             'some-other-url',
         'availability_time_offset':   7.000000,
         'availability_time_complete': False
     })
])
def test_base_url_tag(xml_snippet, expected):
    """ test base url tag """
    element = etree.fromstring(xml_snippet)
    base_url = BaseURL(element)
    assert base_url.text == expected.get('base_url_value')
    assert base_url.availability_time_offset == expected.get('availability_time_offset')
    assert base_url.availability_time_complete == expected.get('availability_time_complete')


def test_utc_timing_tag():
    """ test utc timing tag"""
    utc_xml = '<UTCTiming schemeIdUri="urn:mpeg:dash:utc:http-iso:2014" value="https://time.akamai.com/?iso"/>'
    element = etree.fromstring(utc_xml)
    utc_timing = UTCTiming(element)
    assert utc_timing.scheme_id_uri == 'urn:mpeg:dash:utc:http-iso:2014'
    assert utc_timing.value == 'https://time.akamai.com/?iso'


def test_segment_template_tag():
    """ test segment template tag """
    segment_template_xml = '<SegmentTemplate ' \
                           'timescale="48000" ' \
                           'initialization="audio-7-lav/init.mp4" ' \
                           'media="audio-7-lav/$Number%05d$.mp4" ' \
                           'startNumber="1"/>'
    element = etree.fromstring(segment_template_xml)
    segment_template = SegmentTemplate(element)
    assert segment_template.timescale == 48000
    assert segment_template.initialization == 'audio-7-lav/init.mp4'
    assert segment_template.media == 'audio-7-lav/$Number%05d$.mp4'
    assert segment_template.start_number == 1


def test_event_tag():
    """ test event tag """
    event_xml = '<Event presentationTime="5" duration="1" id="2">Hello world</Event>'
    element = etree.fromstring(event_xml)
    event = Event(element)
    assert event.text == 'Hello world'
    assert event.presentation_time == 5
    assert event.duration == 1
    assert event.id == 2


def test_subset_tag():
    """ test event tag """
    subset_xml = '<Subset id="1" contains="100,101"/>'
    element = etree.fromstring(subset_xml)
    subset = Subset(element)
    assert subset.id == '1'
    assert subset.contains == [100, 101]
