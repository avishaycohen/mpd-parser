"""Scalar grammar and precision, independent of manifests and enumeration."""

from fractions import Fraction

import pytest

from mpd_parser.exceptions import InvalidDurationError, SegmentError
from mpd_parser._segments.values import availability_offset, duration_seconds, integer


def test_absent_duration():
    """An absent bound differs from a declared zero bound."""
    assert duration_seconds(None) is None
    assert duration_seconds("PT0S") == 0


def test_submicrosecond_duration():
    """DASH timescales can be finer than datetime's resolution."""
    assert duration_seconds("PT0.000000003S") == Fraction(3, 1000000000)


def test_compound_duration():
    """Date and time units have distinct meanings for M."""
    assert duration_seconds("P1DT1H1M1.5S") == Fraction(180123, 2)


def test_zero_calendar_units():
    """Common packager spellings with zero years and months are accepted."""
    assert duration_seconds("P0Y0M0DT0H0M5S") == 5


def test_dash_calendar_units():
    """DASH defines a month as 30 days and a year as twelve months."""
    assert duration_seconds("P1Y1M") == 390 * 86400


@pytest.mark.parametrize("value", ["P", "PT", "P1DT"])
def test_missing_duration_component(value):
    """A duration needs a value, including after an explicit T separator."""
    with pytest.raises(InvalidDurationError):
        duration_seconds(value)


@pytest.mark.parametrize("value", ["PT1M1H", "PT1S2S", "P1W"])
def test_duration_unit_order(value):
    """Units are unique, ordered and restricted to the XML duration grammar."""
    with pytest.raises(InvalidDurationError):
        duration_seconds(value)


def test_fraction_requires_seconds():
    """XML duration permits fractional seconds, not fractional hours."""
    with pytest.raises(InvalidDurationError):
        duration_seconds("PT1.5H")


@pytest.mark.parametrize("value", ["-PT1S", "PT-1S", "PT1..2S", "PT1"])
def test_invalid_duration_number(value):
    """Invalid or negative values cannot become timing boundaries."""
    with pytest.raises(InvalidDurationError):
        duration_seconds(value)


def test_integer_zero_does_not_use_default():
    """An explicitly declared zero survives default resolution."""
    assert integer("0", "startNumber", default=1) == 0


@pytest.mark.parametrize("value", ["1_000", "1.0", "--1", ""])
def test_integer_uses_xml_lexical_form(value):
    """Python-only numeric spellings are not XML integer attributes."""
    with pytest.raises(SegmentError):
        integer(value, "duration")


def test_availability_offset_preserves_decimal_precision():
    """The offset is an XML floating-point value, calculated exactly."""
    assert availability_offset("1e-9") == Fraction(1, 1000000000)
    assert availability_offset("INF") is None


@pytest.mark.parametrize("value", ["1/2", "1_000", "NaN", "-INF"])
def test_invalid_availability_offset(value):
    """Nonfinite and non-XML numbers cannot become usable availability bounds."""
    with pytest.raises(SegmentError):
        availability_offset(value)
