"""
Test the composite tags classes as standalone classes
"""

from lxml import etree

from mpd_parser.models.composite_tags import SegmentTemplate


def test_segment_template_tag():
    """test segment template tag"""
    segment_template_xml = (
        "<SegmentTemplate "
        'timescale="48000" '
        'initialization="audio-7-lav/init.mp4" '
        'media="audio-7-lav/$Number%05d$.mp4" '
        'startNumber="1"/>'
    )
    element = etree.fromstring(segment_template_xml)
    segment_template = SegmentTemplate(element)
    assert segment_template.timescale == 48000
    assert segment_template.initialization == "audio-7-lav/init.mp4"
    assert segment_template.media == "audio-7-lav/$Number%05d$.mp4"
    assert segment_template.start_number == 1
