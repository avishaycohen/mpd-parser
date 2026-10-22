"""
Test the composite tags classes as standalone classes
"""

from lxml import etree
from pytest import mark

from mpd_parser.models.composite_tags import SegmentTemplate
from mpd_parser.parser import Parser


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


@mark.parametrize(
    "period_duration,timescale,segment_duration,segment_count",
    [
        ("PT31.658666S", 48000, 184320, 9),
        ("PT5S", 1, 2, 3),
        ("PT6S", 1, 2, 3),
        ("PT1S", 1, 2, 1),
        ("PT0.3S", 10, 1, 3),
        ("PT2.1S", 10, 3, 7),
        ("PT2.099999S", 10, 3, 7),
        ("PT2.100001S", 10, 3, 8),
        ("PT0S", 1, 2, 0),
    ],
)
def test_segment_template_period_segment_count(
    period_duration, timescale, segment_duration, segment_count
):
    """Include a partial final segment without adding one at an exact boundary."""
    mpd = Parser.from_string(
        '<MPD type="static">'
        f'<Period duration="{period_duration}"><AdaptationSet>'
        f'<SegmentTemplate timescale="{timescale}" duration="{segment_duration}" '
        'startNumber="7"/>'
        '</AdaptationSet></Period></MPD>'
    )
    template = mpd.periods[0].adaptation_sets[0].segment_template
    timings = template.parsed_segment_timeline
    assert [segment.number for segment in timings] == list(
        range(7, 7 + segment_count)
    )


def test_segment_template_inheritance_from_adaptation_set():
    """test that child SegmentTemplate inherits attributes and SegmentTimeline from parent AdaptationSet template"""
    xml_data = """
    <MPD xmlns="urn:mpeg:dash:schema:mpd:2011">
        <Period>
            <AdaptationSet>
                <SegmentTemplate timescale="48000" presentationTimeOffset="96000" duration="1920" startNumber="10">
                    <SegmentTimeline>
                        <S t="0" d="1920" r="2"/>
                    </SegmentTimeline>
                </SegmentTemplate>
                <Representation id="rep_audio">
                    <SegmentTemplate media="audio_$Number$.mp4"/>
                </Representation>
            </AdaptationSet>
        </Period>
    </MPD>
    """
    root = etree.fromstring(xml_data.encode("utf-8"))
    child_template_el = root.xpath(".//*[local-name()='Representation']/*[local-name()='SegmentTemplate']")[0]
    template = SegmentTemplate(child_template_el)

    assert template.timescale == 48000
    assert template.presentation_time_offset == 96000
    assert template.duration == 1920
    assert template.start_number == 10
    assert template.media == "audio_$Number$.mp4"
    assert template.segment_timeline is not None
    assert len(template.segment_timeline.segments) == 1
    assert template.segment_timeline.segments[0].d == 1920


def test_segment_template_direct_adaptation_set_attributes():
    """test that child SegmentTemplate inherits attributes declared directly on AdaptationSet"""
    xml_data = """
    <MPD>
        <Period>
            <AdaptationSet timescale="90000" presentationTimeOffset="180000">
                <Representation id="rep_video">
                    <SegmentTemplate media="video_$Number$.mp4"/>
                </Representation>
            </AdaptationSet>
        </Period>
    </MPD>
    """
    root = etree.fromstring(xml_data.encode("utf-8"))
    child_template_el = root.xpath(".//Representation/SegmentTemplate")[0]
    template = SegmentTemplate(child_template_el)

    assert template.timescale == 90000
    assert template.presentation_time_offset == 180000
    assert template.media == "video_$Number$.mp4"

