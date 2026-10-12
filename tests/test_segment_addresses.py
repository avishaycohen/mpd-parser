"""Addressing modes and resolution failures through the public API."""

import pytest

from mpd_parser.exceptions import InvalidTemplateError, InvalidTimelineError, SegmentError
from mpd_parser.parser import Parser
from tests.segment_fixtures import load_manifest, manifest


def test_explicit_media_list():
    """List order is retained and absolute URLs override the document base."""
    document = manifest("""<SegmentList>
        <Initialization sourceURL="init.mp4"/>
        <SegmentURL media="one.m4s"/>
        <SegmentURL media="https://other.example/two.m4s"/>
    </SegmentList>""")
    assert list(document.iter_segment_urls("https://cdn.example/")) == [
        "https://cdn.example/init.mp4",
        "https://cdn.example/one.m4s",
        "https://other.example/two.m4s",
    ]


def test_byte_ranges_retain_repeated_resource_urls():
    """URL enumeration does not discard separately referenced byte ranges."""
    document = manifest("""<BaseURL>video.mp4</BaseURL><SegmentList>
        <Initialization range="0-99"/>
        <SegmentURL mediaRange="100-199"/><SegmentURL mediaRange="200-299"/>
    </SegmentList>""")
    assert list(document.iter_segment_urls()) == ["video.mp4", "video.mp4", "video.mp4"]


def test_segment_base():
    """Initialization and media can address separate ranges of one resource."""
    document = manifest("""<BaseURL>video.mp4</BaseURL>
        <SegmentBase indexRange="100-199"><Initialization range="0-99"/></SegmentBase>""")
    assert list(document.iter_segment_urls()) == ["video.mp4", "video.mp4"]


def test_single_media_resource():
    """A media BaseURL does not require a segment description."""
    assert list(manifest("<BaseURL>video.mp4</BaseURL>").iter_segment_urls()) == ["video.mp4"]


def test_missing_media_reference():
    """A directory BaseURL cannot substitute for a missing media resource."""
    with pytest.raises(SegmentError):
        list(
            manifest(
                "<BaseURL>directory/</BaseURL><SegmentList><SegmentURL/></SegmentList>"
            ).iter_segment_urls()
        )


def test_conflicting_inherited_modes():
    """One representation cannot inherit two different addressing modes."""
    document = load_manifest("conflicting_addressing_modes.mpd")
    with pytest.raises(SegmentError):
        list(document.iter_segment_urls())


def test_duplicate_addressing_modes():
    """Ambiguous siblings fail during inheritance resolution."""
    with pytest.raises(SegmentError):
        list(
            manifest(
                '<SegmentList/><SegmentTemplate duration="1" media="$Number$"/>'
            ).iter_segment_urls()
        )


def test_invalid_xml_document_kind():
    """An XML error page is not an empty MPD."""
    with pytest.raises(SegmentError):
        list(Parser.from_string("<html/>").iter_segment_urls())


def test_template_error_type_reaches_caller():
    """Resolution retains the template parser's dedicated exception type."""
    with pytest.raises(InvalidTemplateError):
        list(manifest('<SegmentTemplate duration="1" media="$Unknown$"/>').iter_segment_urls())


def test_timeline_error_type_reaches_caller():
    """Scalar conversion failures in a timeline have the timeline error type."""
    with pytest.raises(InvalidTimelineError):
        list(manifest('<SegmentTemplate duration="bad" media="$Number$"/>').iter_segment_urls())


def test_timeline_cannot_index_beyond_media_list():
    """An inconsistent timed list fails instead of dropping described segments."""
    document = manifest("""<SegmentList><SegmentTimeline><S d="1" r="2"/></SegmentTimeline>
        <SegmentURL media="one"/></SegmentList>""")
    with pytest.raises(InvalidTimelineError):
        list(document.iter_segment_urls())
