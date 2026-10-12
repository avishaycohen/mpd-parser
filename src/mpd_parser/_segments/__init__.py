"""Connect the XML resolver to segment selection and resource URL rendering."""

from collections.abc import Iterator
from datetime import datetime, timezone

from lxml import etree

from mpd_parser.exceptions import InvalidTimelineError, SegmentError
from mpd_parser.timeline_utils import SegmentTiming
from mpd_parser._segments import resolve
from mpd_parser._segments.addressing import segment_urls
from mpd_parser._segments.timeline import MediaClock, PeriodTiming


def _snapshot_time(now: datetime | None) -> datetime:
    result = datetime.now(timezone.utc) if now is None else now
    if result.utcoffset() is None:
        raise SegmentError("missing timezone for now")
    return result


def _root(element: etree._Element) -> etree._Element:
    root = element.getroottree().getroot()
    if etree.QName(root).localname != "MPD":
        raise SegmentError("expected MPD")
    return root


def _period(element: etree._Element, timings: dict[etree._Element, PeriodTiming]) -> PeriodTiming:
    for ancestor in element.iterancestors():
        if ancestor in timings:
            return timings[ancestor]
    raise SegmentError("missing Period")


def _representation_urls(
    element: etree._Element, period: PeriodTiming, base_url: str | None, now: datetime
) -> Iterator[str]:
    root = _root(element)
    description = resolve.inherited_description(element)
    base = resolve.base_url(element, base_url)
    timing = resolve.schedule(description) if description is not None else None
    live = resolve.availability(root, period, description, element, now)
    clock = timing.clock if timing is not None else MediaClock()
    window = resolve.selection_window(root, period, clock, live, now)
    if window.end is not None and window.end <= window.start:
        return
    if (
        live is not None
        and timing is None
        and description is not None
        and description.kind == "SegmentList"
    ):
        raise InvalidTimelineError("missing live list timing")
    mode = resolve.addressing(element, description, base, timing)
    yield from segment_urls(mode, window)


def iter_segment_urls(
    element: etree._Element, base_url: str | None = None, *, now: datetime | None = None
) -> Iterator[str]:
    """Yield resource URLs incrementally using one captured availability time.

    Local references remain relative unless base_url is supplied. Remote MPDs
    use their response URL. Each BaseURL level selects its first mirror.
    Byte-range resources retain repeated URLs; range metadata stays on tags.
    Execution and errors are deferred until advancement. The caller must keep
    the parsed MPD tree unchanged while consuming the iterator.
    """
    now = _snapshot_time(now)
    root = _root(element)
    timings = resolve.period_timings(root)
    if etree.QName(element).localname == "Representation":
        yield from _representation_urls(element, _period(element, timings), base_url, now)
        return
    if element is not root:
        raise SegmentError("expected MPD or Representation")
    for period, timing in timings.items():
        for representation in resolve.representations(period):
            yield from _representation_urls(representation, timing, base_url, now)


def template_timings(element: etree._Element) -> list[SegmentTiming]:
    """Expose the same selected schedule through the existing timing API."""
    description = resolve.inherited_description(element)
    if description is None or description.kind != "SegmentTemplate":
        raise SegmentError("missing SegmentTemplate")
    timing = resolve.schedule(description)
    if timing is None:
        return []
    root = _root(element)
    period = _period(element, resolve.period_timings(root))
    now = _snapshot_time(None)
    live = resolve.availability(root, period, description, element, now)
    window = resolve.selection_window(root, period, timing.clock, live, now)
    result = []
    for segment in timing.segments(window):
        start = timing.clock.to_seconds(segment.time)
        end = timing.clock.to_seconds(segment.time + segment.duration)
        item = SegmentTiming(float(start), float(end - start), segment.number)
        if live is not None:
            item.availability_start, item.availability_end = live.times(end)
        result.append(item)
    return result
