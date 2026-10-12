"""Regression tests for DASH addressing through the library's public API."""

from io import BytesIO

from mpd_parser.parser import Parser
from tests.segment_fixtures import SEGMENT_DATA_DIR, load_manifest, manifest


def test_supplied_manifest() -> None:
    """All seven representations include init and nine media segments, in order."""
    document = load_manifest("pc_hd_abr_v2_dash_master.mpd")
    stem = "dash/vf_p0pfyy51_9f7fd090-043e-4272-973d-5cb7a6a20777-"
    identifiers = [
        "audio_eng=96000",
        "video=281000",
        "video=437000",
        "video=827000",
        "video=1604000",
        "video=2812000",
        "video=5070000",
    ]
    expected = []
    for identifier in identifiers:
        expected.append(f"{stem}{identifier}.dash")
        expected.extend(f"{stem}{identifier}-{number}.m4s" for number in range(1, 10))
    assert list(document.iter_segment_urls()) == expected
    assert list(document.iter_segment_urls("https://cdn.example/media/master.mpd")) == [
        f"https://cdn.example/media/{url}" for url in expected
    ]


def test_nested_inheritance_and_base_urls() -> None:
    """Partial overrides inherit templates and BaseURLs at each level."""
    document = load_manifest("nested_inheritance.mpd")
    assert list(document.iter_segment_urls()) == [
        "https://cdn.example/root/video/one/init-one.mp4",
        "https://cdn.example/root/video/one/one/4.m4s",
        "https://cdn.example/root/video/one/one/5.m4s",
        "https://cdn.example/root/video/one/one/6.m4s",
        "https://cdn.example/root/video/two/init-two.mp4",
        "https://cdn.example/root/video/two/two/4.m4s",
        "https://cdn.example/root/video/two/two/5.m4s",
    ]


def test_enumeration_preserves_source_document() -> None:
    """Resolving inherited values does not write them into the parsed MPD."""
    document = load_manifest("nested_inheritance.mpd")
    before = Parser.to_string(document)
    for _ in document.iter_segment_urls():
        pass
    assert Parser.to_string(document) == before


def test_representation_enumeration_inherits_ancestor_values() -> None:
    """Direct representation enumeration retains inherited templates and BaseURLs."""
    document = load_manifest("nested_inheritance.mpd")
    representation = document.periods[0].adaptation_sets[0].representations[1]
    assert list(representation.iter_segment_urls()) == [
        "https://cdn.example/root/video/two/init-two.mp4",
        "https://cdn.example/root/video/two/two/4.m4s",
        "https://cdn.example/root/video/two/two/5.m4s",
    ]


def test_period_end_is_inferred_from_next_start() -> None:
    """The next Period's start bounds a Period without an explicit duration."""
    document = load_manifest("period_end_from_next_start.mpd")
    assert list(document.iter_segment_urls()) == ["first-1", "first-2", "second-1"]


def test_period_start_is_inferred_from_previous_duration() -> None:
    """An omitted start follows the previous Period's explicit end."""
    document = load_manifest("period_start_from_previous_duration.mpd")
    assert list(document.iter_segment_urls()) == [
        "first-1",
        "first-2",
        "second-1",
        "second-2",
        "second-3",
    ]


def test_final_period_end_is_inferred_from_mpd_duration() -> None:
    """The final Period's duration excludes time before its explicit start."""
    document = load_manifest("period_end_from_mpd_duration.mpd")
    assert list(document.iter_segment_urls()) == ["1", "2", "3"]


def test_segment_list_inherits_initialization_and_replaces_media() -> None:
    """A child list overrides the parent's media collection, keeping its init."""
    document = load_manifest("inherited_segment_list.mpd")
    assert list(document.iter_segment_urls()) == ["init", "child"]


def test_prefixed_namespace() -> None:
    """Namespace prefixes do not affect segment enumeration."""
    document = load_manifest("prefixed_namespace.mpd")
    assert list(document.iter_segment_urls()) == ["1.m4s"]


def test_absolute_template_media_overrides_base_url() -> None:
    """An absolute media template takes precedence over the document base."""
    document = manifest(
        '<SegmentTemplate duration="1" media="https://cdn.example/$Number$"/>',
        duration="PT1S",
    )
    assert list(document.iter_segment_urls("https://ignored.example/")) == ["https://cdn.example/1"]


def test_derived_timings_follow_mutation() -> None:
    """Derived timings are not cached across edits to their source attributes."""
    document = manifest('<SegmentTemplate duration="2" media="$Number$"/>')
    template = document.periods[0].adaptation_sets[0].representations[0].segment_template
    assert len(template.parsed_segment_timeline) == 3
    template.duration = 3
    template.element.set("startNumber", "0")
    assert [item.number for item in template.parsed_segment_timeline] == [0, 1]
    assert list(document.iter_segment_urls()) == ["0", "1"]


def test_remote_response_url(monkeypatch):
    """Relative segments use the response location after an HTTP redirect."""

    class Response(BytesIO):
        """Minimal HTTP response exposing its redirected URL."""

        def geturl(self):
            """Return the URL libxml2 should retain as the document base."""
            return "https://cdn.example/redirected/manifest.mpd"

    xml = (SEGMENT_DATA_DIR / "relative_media.mpd").read_bytes()
    monkeypatch.setattr("mpd_parser.parser.urlopen", lambda request: Response(xml))
    document = Parser.from_url("https://origin.example/start.mpd")
    assert list(document.iter_segment_urls()) == ["https://cdn.example/redirected/1.m4s"]
    assert list(document.iter_segment_urls("https://override.example/")) == [
        "https://override.example/1.m4s"
    ]
    assert list(document.iter_segment_urls("")) == ["1.m4s"]


def test_segment_list_timeline():
    """List indexing keeps its original positions when a presentation offset clips media."""
    document = manifest(
        """<SegmentList startNumber="7" presentationTimeOffset="2">
            <SegmentTimeline>
                <S d="2" r="3"/>
            </SegmentTimeline>
            <SegmentURL media="before"/>
            <SegmentURL media="first"/>
            <SegmentURL media="second"/>
            <SegmentURL media="after"/>
        </SegmentList>""",
        duration="PT4S",
    )
    assert list(document.iter_segment_urls()) == ["first", "second"]


def test_inherited_timeline_override():
    """A child timeline replaces the parent timeline while inheriting its template attributes."""
    document = load_manifest("inherited_timeline.mpd")
    assert list(document.iter_segment_urls()) == ["init", "0", "20"]
