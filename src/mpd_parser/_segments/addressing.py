"""Concrete addressing modes after XML inheritance and defaults are resolved."""

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import chain
from urllib.parse import urljoin, urlsplit

from mpd_parser.exceptions import InvalidTimelineError, SegmentError
from mpd_parser._segments.template import URLTemplate
from mpd_parser._segments.timeline import SegmentSchedule, SegmentWindow


def resolve_url(base: str, reference: str) -> str:
    """Resolve one URL and translate urllib parsing failures at this boundary."""
    try:
        result = urljoin(base, reference)
        urlsplit(result)
    except ValueError as error:
        raise SegmentError("invalid URL") from error
    return result


@dataclass(frozen=True)
class BaseURL:
    """The resolved mirror route used for relative and byte-range references."""

    url: str
    explicit: bool

    def resource(self, source: str | None) -> str:
        """Resolve a reference, or use a file BaseURL for a byte-range resource."""
        if not source and (
            not self.explicit or not self.url or urlsplit(self.url).path.endswith("/")
        ):
            raise SegmentError("missing media URL")
        return resolve_url(self.url, source or "")


@dataclass(frozen=True)
class TemplateSegments:
    """Templated media addresses backed by a segment schedule."""

    base_url: str
    media: URLTemplate
    initialization: str | None
    schedule: SegmentSchedule

    def media_urls(self, window: SegmentWindow) -> Iterator[str]:
        """Substitute each selected segment's original number and timestamp."""
        for segment in self.schedule.segments(window):
            yield resolve_url(
                self.base_url, self.media.render(number=segment.number, time=segment.time)
            )


@dataclass(frozen=True)
class ListedSegments:
    """Explicit media URLs, optionally selected by an associated schedule."""

    base: BaseURL
    media: tuple[str | None, ...]
    initialization: str | None
    schedule: SegmentSchedule | None

    def media_urls(self, window: SegmentWindow) -> Iterator[str]:
        """Use original segment numbers to index an unmodified media list."""
        if self.schedule is None:
            for reference in self.media:
                yield self.base.resource(reference)
            return
        for segment in self.schedule.segments(window):
            position = segment.number - self.schedule.start_number
            if position >= len(self.media):
                raise InvalidTimelineError("timeline exceeds SegmentList")
            yield self.base.resource(self.media[position])


@dataclass(frozen=True)
class SingleFileSegments:
    """One media resource; byte-range metadata remains on the parsed XML tags."""

    media: str
    initialization: str | None

    def media_urls(self, window: SegmentWindow) -> Iterator[str]:
        """Return the resource if its Period has not been excluded."""
        if window.end is None or window.end > window.start:
            yield self.media


def segment_urls(
    addressing: TemplateSegments | ListedSegments | SingleFileSegments,
    window: SegmentWindow,
) -> Iterator[str]:
    """Emit initialization only when the selected representation has media."""
    media = addressing.media_urls(window)
    first = next(media, None)
    if first is None:
        return
    if addressing.initialization is not None:
        yield addressing.initialization
    yield from chain((first,), media)
