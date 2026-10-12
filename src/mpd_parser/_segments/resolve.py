"""Resolve XML inheritance into typed addressing and timing values.

The timing and template engines consume checked values and never need to know
where an attribute was declared.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction
from urllib.parse import urlsplit

from lxml import etree

from mpd_parser.exceptions import InvalidTimelineError, SegmentError
from mpd_parser._segments.addressing import (
    BaseURL,
    ListedSegments,
    SingleFileSegments,
    TemplateSegments,
    resolve_url,
)
from mpd_parser._segments.template import URLTemplate
from mpd_parser._segments.timeline import (
    AvailabilityWindow,
    MediaClock,
    PeriodTiming,
    SegmentRun,
    SegmentSchedule,
    SegmentWindow,
    TimelineEntry,
    timeline_runs,
)
from mpd_parser._segments.values import (
    availability_offset,
    aware_datetime,
    duration_seconds,
    integer,
)

_ADDRESSING = ("SegmentTemplate", "SegmentList", "SegmentBase")


def children(element: etree._Element, name: str) -> list[etree._Element]:
    """Match direct children in the element's namespace, including unqualified MPDs."""
    namespace = etree.QName(element).namespace
    return element.findall(f"{{{namespace}}}{name}" if namespace is not None else name)


def representations(period: etree._Element) -> Iterator[etree._Element]:
    """Visit representations in manifest order."""
    for adaptation in children(period, "AdaptationSet"):
        yield from children(adaptation, "Representation")


def period_timings(root: etree._Element) -> dict[etree._Element, PeriodTiming]:
    """Resolve explicit and inferred Period boundaries once per MPD iteration."""
    periods = children(root, "Period")
    starts = [duration_seconds(period.get("start")) for period in periods]
    durations = [duration_seconds(period.get("duration")) for period in periods]
    if periods and starts[0] is None and root.get("type", "static") == "static":
        starts[0] = Fraction(0)
    for index in range(1, len(periods)):
        previous_start, previous_duration = starts[index - 1], durations[index - 1]
        if starts[index] is None and previous_start is not None and previous_duration is not None:
            starts[index] = previous_start + previous_duration
    end = duration_seconds(root.get("mediaPresentationDuration"))
    result = {}
    for index, period in enumerate(periods):
        start, duration = starts[index], durations[index]
        following = starts[index + 1] if index + 1 < len(periods) else end
        if duration is None and start is not None and following is not None:
            duration = following - start
        result[period] = PeriodTiming(start, duration)
    return result


@dataclass(frozen=True)
class InheritedDescription:
    """Nearest-first XML nodes of one addressing mode."""

    kind: str
    nodes: tuple[etree._Element, ...]

    def attribute(self, name: str) -> str | None:
        """Read an inherited attribute, retaining explicit zero values."""
        return next((node.get(name) for node in self.nodes if name in node.attrib), None)

    def children(self, name: str) -> list[etree._Element]:
        """The nearest child collection replaces the inherited collection."""
        for node in self.nodes:
            found = children(node, name)
            if found:
                return found
        return []


def inherited_description(element: etree._Element) -> InheritedDescription | None:
    """Reject conflicting addressing modes at or above the selected element."""
    nodes: list[etree._Element] = []
    kind = None
    if etree.QName(element).localname in _ADDRESSING:
        parent = element.getparent()
        if parent is None:
            return InheritedDescription(etree.QName(element).localname, (element,))
        element = parent
    for ancestor in (element, *element.iterancestors()):
        candidates = [child for name in _ADDRESSING for child in children(ancestor, name)]
        if not candidates:
            continue
        if len(candidates) != 1:
            raise SegmentError("multiple addressing modes")
        candidate = candidates[0]
        candidate_kind = etree.QName(candidate).localname
        if kind is not None and kind != candidate_kind:
            raise SegmentError("conflicting addressing modes")
        kind = candidate_kind
        nodes.append(candidate)
    return InheritedDescription(kind, tuple(nodes)) if kind is not None else None


def schedule(description: InheritedDescription) -> SegmentSchedule | None:
    """Convert inherited timing attributes and timeline entries into a schedule."""
    timeline = description.children("SegmentTimeline")
    duration = description.attribute("duration")
    if not timeline and duration is None:
        return None
    try:
        clock = MediaClock(
            integer(description.attribute("timescale"), "timescale", default=1),
            integer(
                description.attribute("presentationTimeOffset"), "presentationTimeOffset", default=0
            ),
            0 if timeline else integer(description.attribute("eptDelta"), "eptDelta", default=0),
        )
        number = integer(description.attribute("startNumber"), "startNumber", default=1)
        if timeline:
            entries = tuple(
                TimelineEntry(
                    duration=integer(entry.get("d"), "d"),
                    start=integer(entry.get("t"), "t") if "t" in entry.attrib else None,
                    repeat=integer(entry.get("r"), "r", default=0),
                )
                for entry in children(timeline[0], "S")
            )
            runs = timeline_runs(entries)
        else:
            count = (
                len(description.children("SegmentURL"))
                if description.kind == "SegmentList"
                else None
            )
            runs = (SegmentRun(clock.presentation_offset, integer(duration, "duration"), count),)
        return SegmentSchedule(clock, runs, number)
    except InvalidTimelineError:
        raise
    except SegmentError as error:
        raise InvalidTimelineError(str(error)) from error


def _selected_bases(element: etree._Element) -> Iterator[etree._Element]:
    """Choose one mirror per level for both URL and availability resolution."""
    for ancestor in reversed((element, *element.iterancestors())):
        bases = children(ancestor, "BaseURL")
        if bases:
            yield bases[0]


def base_url(element: etree._Element, override: str | None) -> BaseURL:
    """Resolve the selected BaseURLs, starting from the response URL."""
    if override is None:
        source = resolve_url("", element.getroottree().docinfo.URL or "")
        override = source if urlsplit(source).scheme in {"http", "https"} else ""
    override = resolve_url("", override)
    explicit = False
    for selected in _selected_bases(element):
        reference = (selected.text or "").strip()
        if not reference:
            raise SegmentError("empty BaseURL")
        override = resolve_url(override, reference)
        explicit = True
    return BaseURL(override, explicit)


def _availability_origin(root: etree._Element, now: datetime) -> datetime:
    """Read the clock origin and apply the leap correction in effect at now."""
    start = root.get("availabilityStartTime")
    if start is None:
        raise SegmentError("missing availabilityStartTime")
    origin = aware_datetime(start)
    leaps = children(root, "LeapSecondInformation")
    if leaps:
        leap = leaps[0]
        change = leap.get("nextLeapChangeTime")
        attribute = "availabilityStartLeapOffset"
        if change is not None and now >= aware_datetime(change):
            attribute = "nextAvailabilityStartLeapOffset"
        try:
            origin -= timedelta(seconds=integer(leap.get(attribute), attribute))
        except OverflowError as error:
            raise InvalidTimelineError("availability time out of range") from error
    return origin


def availability(
    root: etree._Element,
    period: PeriodTiming,
    description: InheritedDescription | None,
    element: etree._Element,
    now: datetime,
) -> AvailabilityWindow | None:
    """Combine the live clock, buffer depth and selected route's offsets."""
    if root.get("type", "static") != "dynamic" or period.start is None:
        return None
    origin = _availability_origin(root, now)
    offset = availability_offset(
        description.attribute("availabilityTimeOffset") if description else None
    )
    for selected in _selected_bases(element):
        added = availability_offset(selected.get("availabilityTimeOffset"))
        offset = None if offset is None or added is None else offset + added
    depth = duration_seconds(root.get("timeShiftBufferDepth"))
    return AvailabilityWindow(origin, period.start, now, depth, offset)


def selection_window(
    root: etree._Element,
    period: PeriodTiming,
    clock: MediaClock,
    live: AvailabilityWindow | None,
    now: datetime,
) -> SegmentWindow:
    """Apply snapshot expiry and exclude dynamic Periods with an unknown start."""
    end = root.get("availabilityEndTime")
    if root.get("type") == "dynamic":
        if period.start is None or (end is not None and now >= aware_datetime(end)):
            return SegmentWindow(Fraction(0), Fraction(0))
    if live is not None:
        return live.select(clock, period.duration)
    period_end = None if period.duration is None else clock.to_ticks(period.duration)
    return SegmentWindow(clock.to_ticks(Fraction(0)), period_end)


def addressing(
    element: etree._Element,
    description: InheritedDescription | None,
    base: BaseURL,
    timing: SegmentSchedule | None,
) -> TemplateSegments | ListedSegments | SingleFileSegments:
    """Build one concrete addressing mode; all XML stays at this boundary."""
    initialization = None
    if description is not None:
        initializations = description.children("Initialization")
        if len(initializations) > 1:
            raise SegmentError("multiple initializations")
        if initializations:
            initialization = base.resource(initializations[0].get("sourceURL"))
    if description is None or description.kind == "SegmentBase":
        return SingleFileSegments(base.resource(None), initialization)
    if description.kind == "SegmentList":
        references = tuple(node.get("media") for node in description.children("SegmentURL"))
        return ListedSegments(base, references, initialization, timing)
    if timing is None:
        raise InvalidTimelineError("missing segment timing")
    media_template = description.attribute("media")
    if not media_template:
        raise SegmentError("missing media template")
    values: dict[str, str | int] = {}
    if "id" in element.attrib:
        values["RepresentationID"] = element.attrib["id"]
    if "bandwidth" in element.attrib:
        values["Bandwidth"] = integer(element.get("bandwidth"), "bandwidth", minimum=0)
    media = URLTemplate.parse(media_template).bind(values)
    init_template = description.attribute("initialization")
    if init_template is not None:
        bound = URLTemplate.parse(init_template).bind(values, initialization=True)
        initialization = resolve_url(base.url, bound.render())
    return TemplateSegments(base.url, media, initialization, timing)
