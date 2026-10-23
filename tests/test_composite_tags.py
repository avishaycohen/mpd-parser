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


def test_segment_template_parsed_segment_timeline_with_timeline():
    """test parsing of SegmentTimeline inside SegmentTemplate"""
    xml_data = """
    <Period start="PT0S" duration="PT30S">
        <AdaptationSet startWithSAP="1">
            <SegmentTemplate timescale="90000" startNumber="1">
                <SegmentTimeline>
                    <S d="180000" r="2" t="0"/>
                    <S d="90000" t="540000"/>
                </SegmentTimeline>
            </SegmentTemplate>
        </AdaptationSet>
    </Period>
    """
    period_elem = etree.fromstring(xml_data)
    template_elem = period_elem.xpath('.//*[local-name()="SegmentTemplate"]')[0]
    template = SegmentTemplate(template_elem)

    assert template.timescale == 90000
    assert template.start_number == 1
    assert template.segment_timeline is not None

    timings = template.parsed_segment_timeline
    assert len(timings) == 4

    assert timings[0].number == 1
    assert timings[0].start_time == 0.0
    assert timings[0].duration == 2.0

    assert timings[1].number == 2
    assert timings[1].start_time == 2.0
    assert timings[1].duration == 2.0

    assert timings[2].number == 3
    assert timings[2].start_time == 4.0
    assert timings[2].duration == 2.0

    assert timings[3].number == 4
    assert timings[3].start_time == 6.0
    assert timings[3].duration == 1.0


def test_segment_template_parsed_segment_timeline_negative_r():
    """test parsing of SegmentTimeline with negative repeat count r=-1"""
    xml_data = """
    <Period start="PT0S" duration="PT10S">
        <AdaptationSet>
            <SegmentTemplate timescale="1000" startNumber="1">
                <SegmentTimeline>
                    <S d="2000" r="-1" t="0"/>
                </SegmentTimeline>
            </SegmentTemplate>
        </AdaptationSet>
    </Period>
    """
    period_elem = etree.fromstring(xml_data)
    template_elem = period_elem.xpath('.//*[local-name()="SegmentTemplate"]')[0]
    template = SegmentTemplate(template_elem)

    timings = template.parsed_segment_timeline

    assert len(timings) == 5
    for idx, segment in enumerate(timings):
        assert segment.number == idx + 1
        assert segment.start_time == idx * 2.0
        assert segment.duration == 2.0


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


def test_segment_template_timeline_exposes_raw_time():
    """Test Issue 1: SegmentTiming should expose raw timescale ticks for $Time$ URL templates"""
    xml_data = """
    <Period>
        <AdaptationSet>
            <SegmentTemplate timescale="90000" presentationTimeOffset="180000">
                <SegmentTimeline>
                    <S t="180000" d="90000" r="1"/>
                </SegmentTimeline>
            </SegmentTemplate>
        </AdaptationSet>
    </Period>
    """
    period_elem = etree.fromstring(xml_data)
    template = SegmentTemplate(period_elem.xpath('.//*[local-name()="SegmentTemplate"]')[0])
    timings = template.parsed_segment_timeline

    assert len(timings) == 2
    assert timings[0].time == 180000
    assert timings[0].start_time == 0.0
    assert timings[1].time == 270000
    assert timings[1].start_time == 1.0


def test_segment_template_timeline_availability_start_includes_period_start():
    """Test Issue 2: availability_start must include Period@start offset in multi-period live streams"""
    xml_data = """
    <MPD type="dynamic" availabilityStartTime="1970-01-01T00:00:00Z">
        <Period start="PT30S">
            <AdaptationSet>
                <SegmentTemplate timescale="1000">
                    <SegmentTimeline>
                        <S t="0" d="2000"/>
                    </SegmentTimeline>
                </SegmentTemplate>
            </AdaptationSet>
        </Period>
    </MPD>
    """
    root = etree.fromstring(xml_data)
    template = SegmentTemplate(root.xpath('.//*[local-name()="SegmentTemplate"]')[0])
    timings = template.parsed_segment_timeline

    assert len(timings) == 1
    # AST (0) + Period@start (30.0) + segment start_time (0.0) = 30.0
    assert timings[0].availability_start == 30.0


def test_segment_template_timeline_negative_r_partial_final_segment():
    """Test Issue 3: r=-1 in Period duration should include partial final segment (ceil logic)"""
    xml_data = """
    <Period duration="PT7S">
        <AdaptationSet>
            <SegmentTemplate timescale="1000">
                <SegmentTimeline>
                    <S t="0" d="2000" r="-1"/>
                </SegmentTimeline>
            </SegmentTemplate>
        </AdaptationSet>
    </Period>
    """
    period_elem = etree.fromstring(xml_data)
    template = SegmentTemplate(period_elem.xpath('.//*[local-name()="SegmentTemplate"]')[0])
    timings = template.parsed_segment_timeline

    # 7 seconds with 2-second segments: 0-2s, 2-4s, 4-6s, 6-7s (partial) => 4 segments total
    assert len(timings) == 4


def test_segment_template_timeline_live_negative_r_not_zero():
    """Test Issue 4: Dynamic/Live stream with large t and r=-1 should not collapse to 0 segments"""
    xml_data = """
    <MPD type="dynamic" availabilityStartTime="1970-01-01T00:00:00Z" timeShiftBufferDepth="PT60S">
        <Period>
            <AdaptationSet>
                <SegmentTemplate timescale="1000">
                    <SegmentTimeline>
                        <S t="3600000" d="2000" r="-1"/>
                    </SegmentTimeline>
                </SegmentTemplate>
            </AdaptationSet>
        </Period>
    </MPD>
    """
    root = etree.fromstring(xml_data)
    template = SegmentTemplate(root.xpath('.//*[local-name()="SegmentTemplate"]')[0])
    timings = template.parsed_segment_timeline

    assert len(timings) >= 1


def test_segment_template_timeline_availability_end_includes_timeshift_buffer():
    """Test Issue 5: availability_end should reflect retention window (SAST + timeShiftBufferDepth + duration)"""
    xml_data = """
    <MPD type="dynamic" availabilityStartTime="1970-01-01T00:00:00Z" timeShiftBufferDepth="PT60S">
        <Period start="PT0S">
            <AdaptationSet>
                <SegmentTemplate timescale="1000">
                    <SegmentTimeline>
                        <S t="0" d="2000"/>
                    </SegmentTimeline>
                </SegmentTemplate>
            </AdaptationSet>
        </Period>
    </MPD>
    """
    root = etree.fromstring(xml_data)
    template = SegmentTemplate(root.xpath('.//*[local-name()="SegmentTemplate"]')[0])
    timings = template.parsed_segment_timeline

    assert len(timings) == 1
    # SAET = availability_start (0) + timeShiftBufferDepth (60.0) + duration (2.0) = 62.0
    assert timings[0].availability_end == 62.0
