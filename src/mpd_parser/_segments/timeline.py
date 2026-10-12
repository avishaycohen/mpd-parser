"""Exact segment timing, independent of XML and URL syntax."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction
from math import ceil

from mpd_parser.exceptions import InvalidTimelineError, UnboundedTimelineError
from mpd_parser._segments.values import elapsed_seconds


@dataclass(frozen=True)
class PeriodTiming:
    """Presentation start and duration in seconds; None means not yet known."""

    start: Fraction | None
    duration: Fraction | None

    def __post_init__(self) -> None:
        if self.duration is not None and self.duration < 0:
            raise InvalidTimelineError("negative Period duration")


@dataclass(frozen=True)
class MediaClock:
    """Map URL timestamps to seconds relative to the Period start.

    eptDelta changes presentation timing, not the $Time$ substitution.
    """

    timescale: int = 1
    presentation_offset: int = 0
    ept_delta: int = 0

    def __post_init__(self) -> None:
        if self.timescale <= 0:
            raise InvalidTimelineError("invalid timescale")
        if self.presentation_offset < 0:
            raise InvalidTimelineError("negative presentationTimeOffset")

    def to_ticks(self, seconds: Fraction) -> Fraction:
        """Map a presentation boundary to URL timestamp units."""
        return seconds * self.timescale + self.presentation_offset - self.ept_delta

    def to_seconds(self, ticks: int) -> Fraction:
        """Map an unmodified URL timestamp to its presentation time."""
        return Fraction(ticks - self.presentation_offset + self.ept_delta, self.timescale)


@dataclass(frozen=True)
class Segment:
    """One segment's original number, URL timestamp and duration in ticks."""

    number: int
    time: int
    duration: int


@dataclass(frozen=True)
class SegmentRun:
    """Consecutive equal-duration segments; None count is an open-ended repeat."""

    start: int
    duration: int
    count: int | None

    def __post_init__(self) -> None:
        if self.start < 0 or self.duration <= 0 or (self.count is not None and self.count < 0):
            raise InvalidTimelineError("invalid segment run")

    def bounded_count(self, end: Fraction | None) -> int:
        """Resolve an open repeat without expanding its individual segments."""
        if self.count is not None:
            return self.count
        if end is None:
            raise UnboundedTimelineError("missing timeline boundary")
        return max(0, ceil((end - self.start) / self.duration))


@dataclass(frozen=True)
class TimelineEntry:
    """One explicit timeline entry, before resolving implicit starts and repeats."""

    duration: int
    start: int | None = None
    repeat: int = 0

    def __post_init__(self) -> None:
        if self.duration <= 0 or (self.start is not None and self.start < 0):
            raise InvalidTimelineError("invalid timeline entry")


def timeline_runs(entries: tuple[TimelineEntry, ...]) -> tuple[SegmentRun, ...]:
    """Resolve implicit starts and repeats bounded by the following entry."""
    runs = []
    end = 0
    for index, entry in enumerate(entries):
        start = end if entry.start is None else entry.start
        if start < end:
            raise InvalidTimelineError("overlapping timeline entries")
        count = entry.repeat + 1 if entry.repeat >= 0 else None
        if count is None and index + 1 < len(entries):
            following = entries[index + 1].start
            if following is None or following <= start:
                raise InvalidTimelineError("missing repeat boundary")
            count = ceil(Fraction(following - start, entry.duration))
        runs.append(SegmentRun(start, entry.duration, count))
        if count is not None:
            end = start + count * entry.duration
    return tuple(runs)


@dataclass(frozen=True)
class SegmentWindow:
    """Selection boundaries in URL ticks, with distinct endpoint semantics.

    Segment ends must exceed start. Segment starts must precede period_end.
    Segment ends must be at or before available_end. None means no upper bound.
    """

    start: Fraction
    period_end: Fraction | None = None
    available_end: Fraction | None = None

    @property
    def end(self) -> Fraction | None:
        """The finite boundary used to expand an otherwise open-ended run."""
        limits = [value for value in (self.period_end, self.available_end) if value is not None]
        return min(limits) if limits else None

    def positions(self, run: SegmentRun, count: int) -> range:
        """Jump to the selected part of a run without visiting expired history."""
        first = max(0, (self.start - run.start) // run.duration)
        stop = count
        if self.period_end is not None:
            stop = min(stop, ceil((self.period_end - run.start) / run.duration))
        if self.available_end is not None:
            stop = min(stop, (self.available_end - run.start) // run.duration)
        return range(first, max(first, stop))


@dataclass(frozen=True)
class AvailabilityWindow:
    """A live snapshot's bounds in seconds relative to its Period start."""

    origin: datetime
    period_start: Fraction
    now: datetime
    depth: Fraction | None
    offset: Fraction | None

    @property
    def elapsed(self) -> Fraction:
        """Keep the Period offset exact even below datetime's resolution."""
        return elapsed_seconds(self.now - self.origin) - self.period_start

    def select(self, clock: MediaClock, duration: Fraction | None) -> SegmentWindow:
        """Convert availability and Period bounds to the schedule's timestamp units."""
        start = (
            max(Fraction(0), self.elapsed - self.depth) if self.depth is not None else Fraction(0)
        )
        available_end = None if self.offset is None else clock.to_ticks(self.elapsed + self.offset)
        period_end = None if duration is None else clock.to_ticks(duration)
        return SegmentWindow(clock.to_ticks(start), period_end, available_end)

    def times(self, segment_end: Fraction) -> tuple[datetime | None, datetime | None]:
        """Report wall-clock availability using datetime's microsecond precision."""
        end = self.period_start + segment_end
        try:
            start_time = (
                None
                if self.offset is None
                else self.origin + timedelta(seconds=float(end - self.offset))
            )
            end_time = (
                None
                if self.depth is None
                else self.origin + timedelta(seconds=float(end + self.depth))
            )
        except OverflowError as error:
            raise InvalidTimelineError("availability time out of range") from error
        return start_time, end_time


@dataclass(frozen=True)
class SegmentSchedule:
    """Compact segment runs and their shared numbering and media clock."""

    clock: MediaClock
    runs: tuple[SegmentRun, ...]
    start_number: int = 1

    def __post_init__(self) -> None:
        if self.start_number < 0:
            raise InvalidTimelineError("negative startNumber")

    def segments(self, window: SegmentWindow) -> Iterator[Segment]:
        """Select segments while retaining numbering across skipped runs."""
        boundary = window.end
        if boundary is not None and boundary <= window.start:
            return
        number = self.start_number
        for run in self.runs:
            count = run.bounded_count(boundary)
            for position in window.positions(run, count):
                yield Segment(number + position, run.start + position * run.duration, run.duration)
            number += count
