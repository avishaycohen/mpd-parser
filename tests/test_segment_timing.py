"""Timing rules expressed as domain values, without XML or URL strings."""

from datetime import datetime, timedelta, timezone
from fractions import Fraction

import pytest

from mpd_parser.exceptions import InvalidTimelineError, UnboundedTimelineError
from mpd_parser._segments.timeline import (
    AvailabilityWindow,
    MediaClock,
    PeriodTiming,
    Segment,
    SegmentRun,
    SegmentSchedule,
    SegmentWindow,
    TimelineEntry,
    timeline_runs,
)

START = datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize(("end", "count"), [(Fraction(5), 3), (Fraction(6), 3), (Fraction(0), 0)])
def test_period_end_includes_only_overlapping_segments(end, count):
    """Include a partial last segment; exclude a segment starting at the end."""
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(0, 2, None),))
    selected = list(schedule.segments(SegmentWindow(Fraction(0), end)))
    assert len(selected) == count


def test_decimal_boundary_is_exact():
    """An exact decimal boundary cannot introduce an extra segment."""
    clock = MediaClock(timescale=10)
    schedule = SegmentSchedule(clock, (SegmentRun(0, 1, None),))
    assert list(schedule.segments(SegmentWindow(Fraction(0), clock.to_ticks(Fraction(3, 10))))) == [
        Segment(1, 0, 1),
        Segment(2, 1, 1),
        Segment(3, 2, 1),
    ]


def test_presentation_offset_retains_numbering():
    """Clipping skips original segments rather than renumbering what remains."""
    schedule = SegmentSchedule(MediaClock(presentation_offset=100), (SegmentRun(98, 2, 5),), 7)
    assert list(schedule.segments(SegmentWindow(Fraction(100), Fraction(104)))) == [
        Segment(8, 100, 2),
        Segment(9, 102, 2),
    ]


def test_ept_delta_changes_timing_without_changing_url_time():
    """The first segment overlaps the Period start while retaining its timestamp."""
    clock = MediaClock(presentation_offset=100, ept_delta=-1)
    schedule = SegmentSchedule(clock, (SegmentRun(100, 2, None),))
    selected = list(
        schedule.segments(SegmentWindow(clock.to_ticks(Fraction(0)), clock.to_ticks(Fraction(6))))
    )
    assert selected == [
        Segment(1, 100, 2),
        Segment(2, 102, 2),
        Segment(3, 104, 2),
        Segment(4, 106, 2),
    ]
    assert clock.to_seconds(selected[0].time) == -1


def test_zero_start_number():
    """Zero is a valid explicitly supplied first number."""
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(0, 2, 1),), start_number=0)
    assert list(schedule.segments(SegmentWindow(Fraction(0)))) == [Segment(0, 0, 2)]


def test_implicit_timeline_starts_follow_previous_run():
    """A missing start follows all repeats, while explicit gaps are retained."""
    assert timeline_runs(
        (TimelineEntry(2, start=10, repeat=1), TimelineEntry(3), TimelineEntry(1, start=20))
    ) == (
        SegmentRun(10, 2, 2),
        SegmentRun(14, 3, 1),
        SegmentRun(20, 1, 1),
    )


def test_repeat_stops_at_next_explicit_start():
    """A negative repeat before another entry needs an explicit boundary."""
    assert timeline_runs((TimelineEntry(2, repeat=-1), TimelineEntry(1, start=6, repeat=1))) == (
        SegmentRun(0, 2, 3),
        SegmentRun(6, 1, 2),
    )


def test_final_negative_repeat_remains_open():
    """The selection window, rather than XML parsing, bounds the final run."""
    assert timeline_runs((TimelineEntry(2, repeat=-2),)) == (SegmentRun(0, 2, None),)


def test_overlapping_entries_are_rejected():
    """A later explicit timestamp cannot move into an earlier segment."""
    with pytest.raises(InvalidTimelineError):
        timeline_runs((TimelineEntry(2), TimelineEntry(2, start=1)))


def test_unbounded_repeat_is_distinct_from_invalid_timing():
    """A valid open repeat cannot be enumerated without a finite boundary."""
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(0, 2, None),))
    with pytest.raises(UnboundedTimelineError):
        list(schedule.segments(SegmentWindow(Fraction(0))))


def test_repeat_before_implicit_start_is_ambiguous():
    """The following implicit start cannot bound an open repeat."""
    with pytest.raises(InvalidTimelineError):
        timeline_runs((TimelineEntry(2, repeat=-1), TimelineEntry(2)))


@pytest.mark.parametrize(("elapsed", "expected"), [(3.999999, []), (4, [Segment(1, 0, 4)])])
def test_segment_becomes_available_at_its_end(elapsed, expected):
    """The availability upper boundary includes equality."""
    live = AvailabilityWindow(
        START, Fraction(0), START + timedelta(seconds=elapsed), Fraction(10), Fraction(0)
    )
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(0, 4, None),))
    assert list(schedule.segments(live.select(schedule.clock, None))) == expected


def test_segment_expires_at_lower_boundary():
    """A segment ending at the window start has expired."""
    live = AvailabilityWindow(
        START, Fraction(0), START + timedelta(seconds=22), Fraction(10), Fraction(0)
    )
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(0, 4, None),))
    assert list(schedule.segments(live.select(schedule.clock, None))) == [
        Segment(4, 12, 4),
        Segment(5, 16, 4),
    ]


def test_availability_offset_admits_early_requests():
    """An offset permits a segment to be requested before its nominal end."""
    live = AvailabilityWindow(
        START, Fraction(0), START + timedelta(seconds=3), Fraction(10), Fraction(1)
    )
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(0, 4, None),))
    assert list(schedule.segments(live.select(schedule.clock, None))) == [Segment(1, 0, 4)]


def test_submicrosecond_period_start():
    """The clock cannot round a future segment into the availability window."""
    live = AvailabilityWindow(
        START, Fraction(1, 1000000000), START + timedelta(seconds=4), None, Fraction(0)
    )
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(0, 4, None),))
    assert not list(schedule.segments(live.select(schedule.clock, None)))


def test_large_window_skips_history():
    """An epoch-scale timeline retains only the requested window's segments."""
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(0, 4, None),), 0)
    window = SegmentWindow(Fraction(10**12), available_end=Fraction(10**12 + 8))
    assert list(schedule.segments(window)) == [
        Segment(250000000000, 10**12, 4),
        Segment(250000000001, 10**12 + 4, 4),
    ]


def test_empty_future_run():
    """An open repeat beyond the current window produces no segments."""
    schedule = SegmentSchedule(MediaClock(), (SegmentRun(100, 4, None),))
    assert not list(schedule.segments(SegmentWindow(Fraction(10), available_end=Fraction(20))))


def test_negative_period_duration():
    """Inferred Period ends cannot precede their starts."""
    with pytest.raises(InvalidTimelineError):
        PeriodTiming(Fraction(10), Fraction(-1))
