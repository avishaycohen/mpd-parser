"""
Test the base tag classes as standalone classes
"""

import math
from xml.etree.ElementTree import Element

import pytest
from lxml import etree

from mpd_parser.models.base_tags import (
    URL,
    AssetIdentifiers,
    BaseURL,
    ContentComponent,
    Descriptor,
    Event,
    EventStream,
    ProgramInfo,
    Subset,
    Tag,
    TextTag,
    UTCTiming,
)


def test_tag_initialization():
    """test tag init"""
    element = Element("test_tag")
    tag = Tag(element)
    assert tag.element == element


def test_tag_setattr():
    """test basic ability to set value in a tag"""
    element = Element("test_tag")
    tag = Tag(element)
    tag.new_attribute = "value"
    assert element.attrib["newAttribute"] == "value"


def test_text_tag():
    """test text tag"""
    tag_text_xml = "<MyTag>Hello, world!</MyTag>"
    element = etree.fromstring(tag_text_xml)
    text_tag = TextTag(element)
    assert text_tag.text == "Hello, world!"


def test_event_tag():
    """test event tag"""
    event_xml = '<Event presentationTime="5" duration="1" id="2">Hello world</Event>'
    element = etree.fromstring(event_xml)
    event = Event(element)
    assert event.text == "Hello world"
    assert event.presentation_time == 5
    assert event.duration == 1
    assert event.id == 2


def test_descriptor_tag():
    """test descriptor tag"""
    desc_xml = '<Descriptor schemeIdUri="urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed" value="someval" id="desc1" />'
    element = etree.fromstring(desc_xml)
    desc = Descriptor(element)
    assert desc.scheme_id_uri == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed"
    assert desc.value == "someval"
    assert desc.id == "desc1"


def test_utc_timing_tag():
    """test utc timing tag"""
    utc_xml = '<UTCTiming schemeIdUri="urn:mpeg:dash:utc:http-head:2014" value="http://time.akamai.com" id="utc1" />'
    element = etree.fromstring(utc_xml)
    utc = UTCTiming(element)
    assert utc.scheme_id_uri == "urn:mpeg:dash:utc:http-head:2014"
    assert utc.value == "http://time.akamai.com"
    assert utc.id == "utc1"


def test_asset_identifiers_tag():
    """test asset identfiers tag"""
    ai_xml = '<AssetIdentifiers schemeIdUri="urn:org:foo:asset-id" value="asset123" id="ai1" />'
    element = etree.fromstring(ai_xml)
    ai = AssetIdentifiers(element)
    assert ai.scheme_id_uri == "urn:org:foo:asset-id"
    assert ai.value == "asset123"
    assert ai.id == "ai1"


def test_content_component_tag():
    """test content component tag"""
    cc_xml = """
    <ContentComponent id="1" lang="en" contentType="video/mp4" par="16:9">
        <Accessibility schemeIdUri="urn:foo:acc" value="desc" id="acc1" />
        <Role schemeIdUri="urn:foo:role" value="main" id="role1" />
        <Rating schemeIdUri="urn:foo:rating" value="PG" id="rating1" />
        <Viewpoint schemeIdUri="urn:foo:viewpoint" value="3d" id="view1" />
    </ContentComponent>
    """
    element = etree.fromstring(cc_xml)
    cc = ContentComponent(element)
    assert cc.id == 1
    assert cc.lang == "en"
    assert cc.content_type == "video/mp4"
    assert cc.par == "16:9"
    assert len(cc.accessibilities) == 1
    assert cc.accessibilities[0].scheme_id_uri == "urn:foo:acc"
    assert cc.accessibilities[0].value == "desc"
    assert cc.accessibilities[0].id == "acc1"
    assert len(cc.roles) == 1
    assert cc.roles[0].scheme_id_uri == "urn:foo:role"
    assert cc.roles[0].value == "main"
    assert cc.roles[0].id == "role1"
    assert len(cc.ratings) == 1
    assert cc.ratings[0].scheme_id_uri == "urn:foo:rating"
    assert cc.ratings[0].value == "PG"
    assert cc.ratings[0].id == "rating1"
    assert len(cc.viewpoints) == 1
    assert cc.viewpoints[0].scheme_id_uri == "urn:foo:viewpoint"
    assert cc.viewpoints[0].value == "3d"
    assert cc.viewpoints[0].id == "view1"


def test_program_info_tag():
    """test program info tag"""
    pi_xml = """
    <ProgramInformation lang="en" moreInformationURL="https://example.com">
        <Title>My Program</Title>
        <Source>My Source</Source>
        <Copyright>Copyright Info</Copyright>
    </ProgramInformation>
    """
    element = etree.fromstring(pi_xml)
    pi = ProgramInfo(element)
    assert pi.lang == "en"
    assert pi.more_info_url == "https://example.com"
    assert len(pi.titles) == 1
    assert pi.titles[0].text == "My Program"
    assert len(pi.sources) == 1
    assert pi.sources[0].text == "My Source"
    assert len(pi.copy_rights) == 1
    assert pi.copy_rights[0].text == "Copyright Info"


def test_url_tag():
    """test url tag"""
    url_xml = '<URL sourceURL="https://example.com/content" range="100-200" />'
    element = etree.fromstring(url_xml)
    url = URL(element)
    assert url.source_url == "https://example.com/content"
    assert url.range == "100-200"


def test_event_stream_tag():
    """test event stream tag"""
    event_stream_xml = """
    <EventStream schemeIdUri="urn:example:event" value="example" timescale="1000">
        <Event presentationTime="5000" duration="1000" id="1">Hello</Event>
        <Event presentationTime="6000" duration="1000" id="2">World</Event>
    </EventStream>
    """
    element = etree.fromstring(event_stream_xml)
    event_stream = EventStream(element)
    assert event_stream.scheme_id_uri == "urn:example:event"
    assert event_stream.value == "example"
    assert event_stream.timescale == "1000"
    assert len(event_stream.events) == 2
    assert event_stream.events[0].text == "Hello"
    assert event_stream.events[0].presentation_time == 5000
    assert event_stream.events[0].duration == 1000
    assert event_stream.events[0].id == 1
    assert event_stream.events[1].text == "World"
    assert event_stream.events[1].presentation_time == 6000
    assert event_stream.events[1].duration == 1000
    assert event_stream.events[1].id == 2


def test_subset_tag():
    """test subset tag"""
    subset_xml = '<Subset id="subset1" contains="1,2,3" />'
    element = etree.fromstring(subset_xml)
    subset = Subset(element)
    assert subset.id == "subset1"
    assert subset.contains == [1, 2, 3]


@pytest.mark.parametrize(
    "xml_snippet,expected",
    [
        (
            """<BaseURL availabilityTimeOffset="INF">bunny_46980bps/BigBuckBunny_1snonSeg.mp4</BaseURL>""",
            {
                "base_url_value": "bunny_46980bps/BigBuckBunny_1snonSeg.mp4",
                "availability_time_offset": math.inf,
            },
        ),
        (
            '<BaseURL availabilityTimeComplete="false" availabilityTimeOffset="7.000000">'
            "some-other-url</BaseURL>",
            {
                "base_url_value": "some-other-url",
                "availability_time_offset": 7.000000,
                "availability_time_complete": False,
            },
        ),
    ],
)
def test_base_url_tag(xml_snippet, expected):
    """test base url tag"""
    element = etree.fromstring(xml_snippet)
    base_url = BaseURL(element)
    assert base_url.text == expected.get("base_url_value")
    assert base_url.availability_time_offset == expected.get("availability_time_offset")
    assert base_url.availability_time_complete == expected.get(
        "availability_time_complete"
    )
