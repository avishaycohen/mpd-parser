"""Named document fixtures and minimal fragment wrappers for segment tests."""

from pathlib import Path

from mpd_parser.models.composite_tags import MPD
from mpd_parser.parser import Parser


SEGMENT_DATA_DIR = Path(__file__).parent / "data" / "segments"


def load_manifest(filename: str) -> MPD:
    """Parse a named segment fixture without altering its document structure."""
    return Parser.from_file(str(SEGMENT_DATA_DIR / filename))


def manifest(description: str, *, duration: str = "PT5S") -> MPD:
    """Wrap a segment description in a single-representation static MPD."""
    return Parser.from_string(
        '<MPD xmlns="urn:mpeg:dash:schema:mpd:2011">'
        f'<Period duration="{duration}"><AdaptationSet>'
        f'<Representation id="video" bandwidth="1024">{description}</Representation>'
        "</AdaptationSet></Period></MPD>"
    )


def live_manifest(description: str | None = None) -> MPD:
    """Build a live representation with a ten-second time shift buffer."""
    if description is None:
        description = '<SegmentTemplate duration="4" initialization="init" media="$Number$"/>'
    return Parser.from_string(
        '<MPD type="dynamic" availabilityStartTime="2026-01-01T00:00:00Z" '
        'timeShiftBufferDepth="PT10S">'
        '<Period start="PT0S"><AdaptationSet><Representation id="v">'
        f"{description}</Representation></AdaptationSet></Period></MPD>"
    )
