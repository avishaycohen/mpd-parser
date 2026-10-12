"""Live URL enumeration at deterministic availability-window boundaries."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

from mpd_parser.exceptions import InvalidTimelineError, SegmentError
from mpd_parser.parser import Parser
from tests.segment_fixtures import live_manifest, load_manifest


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_buffer_depth_is_optional():
    """Absent depth retains available history from the Period start."""
    document = live_manifest()
    del document.element.attrib["timeShiftBufferDepth"]
    assert list(document.iter_segment_urls(now=START + timedelta(seconds=20))) == [
        "init",
        "1",
        "2",
        "3",
        "4",
        "5",
    ]


def test_availability_offsets_are_added_along_selected_route():
    """BaseURL offsets add to the inherited template offset, including low latency."""
    document = load_manifest("live_availability_offsets.mpd")
    assert list(document.iter_segment_urls(now=START + timedelta(seconds=21))) == [
        "https://cdn.example/video/3",
        "https://cdn.example/video/4",
        "https://cdn.example/video/5",
        "https://cdn.example/video/6",
    ]


def test_infinite_availability_offset_for_finite_period():
    """Pre-prepared media can be available ahead of the clock in a live MPD."""
    document = live_manifest(
        '<SegmentTemplate duration="4" availabilityTimeOffset="INF" media="$Number$"/>'
    )
    document.periods[0].element.set("duration", "PT28S")
    assert list(document.iter_segment_urls(now=START + timedelta(seconds=20))) == [
        "3",
        "4",
        "5",
        "6",
        "7",
    ]


def test_period_start_and_transitions():
    """A second Period resets local numbering and excludes expired prior content."""
    document = load_manifest("live_period_transition.mpd")
    assert list(document.iter_segment_urls(now=START + timedelta(seconds=20))) == [
        "new-init",
        "new-1",
        "new-2",
        "new-3",
    ]


def test_ended_period_has_no_future_segments():
    """An open-ended repeat stops at its Period end even when the live clock advances."""
    document = live_manifest("""<SegmentTemplate media="$Number$">
        <SegmentTimeline>
            <S d="4" r="-1"/>
        </SegmentTimeline>
    </SegmentTemplate>""")
    document.periods[0].element.set("duration", "PT16S")
    assert list(document.iter_segment_urls(now=START + timedelta(seconds=20))) == ["3", "4"]


def test_availability_end_time():
    """No segments remain available at the MPD's availability end."""
    document = live_manifest()
    document.element.set("availabilityEndTime", "2026-01-01T00:00:20Z")
    assert not list(document.iter_segment_urls(now=START + timedelta(seconds=20)))


def test_live_segment_list():
    """Explicit media addresses are selected by the same timing rules."""
    document = live_manifest("""<SegmentList duration="4">
        <Initialization sourceURL="init"/>
        <SegmentURL media="1"/>
        <SegmentURL media="2"/>
        <SegmentURL media="3"/>
        <SegmentURL media="4"/>
        <SegmentURL media="5"/>
        <SegmentURL media="6"/>
    </SegmentList>""")
    assert list(document.iter_segment_urls(now=START + timedelta(seconds=20))) == [
        "init",
        "3",
        "4",
        "5",
    ]


def test_clock_is_captured_once(monkeypatch):
    """All representations in one iteration use one clock reading."""
    document = load_manifest("live_multiple_representations.mpd")
    calls = []

    def clock_now(tz):
        """Advance one segment per reading to detect inconsistent snapshots."""
        calls.append(tz)
        return START + timedelta(seconds=16 + 4 * len(calls))

    monkeypatch.setattr("mpd_parser._segments.datetime", Mock(now=clock_now))
    assert list(document.iter_segment_urls()) == [
        "init",
        "3",
        "4",
        "5",
        "other-3",
        "other-4",
        "other-5",
    ]
    assert calls == [timezone.utc]


def test_existing_low_latency_manifest():
    """A real epoch-based live template enumerates only its small current window."""
    path = Path(__file__).resolve().parents[1] / "manifests/chunked-single-bitrate.mpd"
    document = Parser.from_file(str(path))
    now = datetime(2022, 2, 16, 14, 58, 53, tzinfo=timezone.utc)
    urls = list(document.iter_segment_urls(now=now))
    base = "https://livesim.dashif.org/livesim/sts_1645023533/sid_c2d9e37b/chunkdur_1/ato_7/testpic4_8s/"
    expected = []
    for representation in ("A48", "V300", "V600", "V1200", "V2400"):
        expected.append(f"{base}{representation}/init.mp4")
        expected.extend(
            f"{base}{representation}/{number}.m4s" for number in range(205627904, 205627942)
        )
    assert urls == expected


def test_early_available_period_is_skipped():
    """A Period whose start is not yet known cannot provide currently playable media."""
    document = load_manifest("live_unknown_period_start.mpd")
    assert list(document.iter_segment_urls(now=START + timedelta(seconds=20))) == [
        "init",
        "3",
        "4",
        "5",
    ]


def test_derived_live_timings(monkeypatch):
    """The existing timing property shares live filtering and reports aware availability times."""
    document = live_manifest(
        '<SegmentTemplate duration="4" availabilityTimeOffset="1" media="$Number$"/>'
    )
    monkeypatch.setattr(
        "mpd_parser._segments.datetime", Mock(now=lambda tz: START + timedelta(seconds=20))
    )
    template = document.periods[0].adaptation_sets[0].representations[0].segment_template
    timings = template.parsed_segment_timeline
    assert [(timing.number, timing.start_time, timing.duration) for timing in timings] == [
        (3, 8, 4),
        (4, 12, 4),
        (5, 16, 4),
    ]
    assert timings[0].availability_start == START + timedelta(seconds=11)
    assert timings[0].availability_end == START + timedelta(seconds=22)
    assert list(document.iter_segment_urls()) == ["3", "4", "5"]


def test_naive_clock_is_rejected():
    """A caller must supply an unambiguous point on the live timeline."""
    with pytest.raises(SegmentError):
        list(live_manifest().iter_segment_urls(now=datetime(2026, 1, 1)))


def test_missing_availability_origin():
    """Live segment numbering cannot be derived without the clock origin."""
    document = live_manifest()
    del document.element.attrib["availabilityStartTime"]
    with pytest.raises(SegmentError):
        list(document.iter_segment_urls(now=START))


def test_leap_offset_transition():
    """A declared leap correction takes effect exactly at its change time."""
    document = live_manifest()
    leap = document.element.makeelement(
        "LeapSecondInformation",
        availabilityStartLeapOffset="1",
        nextAvailabilityStartLeapOffset="2",
        nextLeapChangeTime="2026-01-01T00:00:19Z",
    )
    document.element.append(leap)
    before = START + timedelta(seconds=18, microseconds=999999)
    change = START + timedelta(seconds=19)
    assert list(document.iter_segment_urls(now=before)) == ["init", "3", "4"]
    assert list(document.iter_segment_urls(now=change)) == ["init", "3", "4", "5"]


def test_leap_correction_outside_datetime_range():
    """An unrepresentable clock origin reports a timing error."""
    document = live_manifest()
    document.element.set("availabilityStartTime", "0001-01-01T00:00:00Z")
    document.element.append(
        document.element.makeelement("LeapSecondInformation", availabilityStartLeapOffset="1")
    )
    with pytest.raises(InvalidTimelineError):
        next(document.iter_segment_urls(now=START))


def test_timing_does_not_resolve_media_addresses(monkeypatch):
    """The timing API reads a selected BaseURL's offset without parsing its URL."""
    document = live_manifest("""<BaseURL availabilityTimeOffset="1">https://[</BaseURL>
        <SegmentTemplate duration="4" media="$Number$"/>""")
    now = START + timedelta(seconds=3)
    monkeypatch.setattr("mpd_parser._segments.datetime", Mock(now=lambda tz: now))
    template = document.periods[0].adaptation_sets[0].representations[0].segment_template
    assert [timing.number for timing in template.parsed_segment_timeline] == [1]
    with pytest.raises(SegmentError):
        next(document.iter_segment_urls(now=now))
