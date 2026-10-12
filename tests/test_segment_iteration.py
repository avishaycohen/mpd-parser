"""Iterator consumption, deferred errors and the lifetime of the live clock."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from mpd_parser.exceptions import InvalidTemplateError, SegmentError
from mpd_parser.parser import Parser
from tests.segment_fixtures import live_manifest, load_manifest, manifest


def test_creation_does_not_start_resolution():
    """Even a malformed document is inspected only when iteration starts."""
    urls = Parser.from_string("<html/>").iter_segment_urls()
    assert iter(urls) is urls
    with pytest.raises(SegmentError):
        next(urls)


def test_later_representations_are_resolved_on_demand():
    """A caller can consume the first representation without resolving the second."""
    document = load_manifest("deferred_representation_error.mpd")
    urls = document.iter_segment_urls()
    assert next(urls) == "first.m4s"
    with pytest.raises(InvalidTemplateError):
        next(urls)


def test_explicit_list_resolves_one_media_reference_per_advance():
    """A malformed later reference cannot prevent consumption of earlier URLs."""
    document = manifest("""<SegmentList>
        <SegmentURL media="first.m4s"/><SegmentURL media="https://["/>
        </SegmentList>""")
    urls = document.iter_segment_urls("https://cdn.example/")
    assert next(urls) == "https://cdn.example/first.m4s"
    with pytest.raises(SegmentError):
        next(urls)


def test_live_clock_is_captured_at_first_advance(monkeypatch):
    """Creating an iterator does not freeze time; starting it does."""
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    clock = Mock(return_value=start + timedelta(seconds=4))
    monkeypatch.setattr("mpd_parser._segments.datetime", Mock(now=clock))
    urls = live_manifest().iter_segment_urls()
    clock.assert_not_called()

    clock.return_value = start + timedelta(seconds=20)
    assert next(urls) == "init"
    clock.return_value = start + timedelta(seconds=100)
    assert next(urls) == "3"
    assert next(urls) == "4"
    assert next(urls) == "5"
    with pytest.raises(StopIteration):
        next(urls)
    clock.assert_called_once_with(timezone.utc)


def test_exhausted_iterator_is_not_restarted():
    """Another traversal requires another API call."""
    document = manifest('<SegmentTemplate duration="5" media="$Number$"/>')
    urls = document.iter_segment_urls()
    assert next(urls) == "1"
    with pytest.raises(StopIteration):
        next(urls)
    with pytest.raises(StopIteration):
        next(urls)
    assert next(document.iter_segment_urls()) == "1"


def test_expired_list_references_are_not_resolved():
    """Availability selection precedes resolution of media URLs."""
    document = live_manifest("""<SegmentList duration="4">
        <SegmentURL media="https://["/><SegmentURL media="expired"/>
        <SegmentURL media="third"/><SegmentURL media="fourth"/><SegmentURL media="fifth"/>
        </SegmentList>""")
    now = datetime(2026, 1, 1, 0, 0, 20, tzinfo=timezone.utc)
    urls = document.iter_segment_urls(now=now)
    assert next(urls) == "third"
    assert next(urls) == "fourth"
    assert next(urls) == "fifth"
    with pytest.raises(StopIteration):
        next(urls)
