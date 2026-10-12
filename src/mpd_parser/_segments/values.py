"""Parse MPD scalar values without losing submicrosecond precision."""

from collections.abc import Iterator
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from isodate import parse_datetime

from mpd_parser.exceptions import InvalidDurationError, SegmentError


def _duration_parts(text: str) -> Iterator[tuple[str, str]]:
    """Scan number/unit pairs; ordering and allowed units belong to the caller."""
    start = 0
    for index, char in enumerate(text):
        if char in "0123456789.":
            continue
        if start == index:
            raise InvalidDurationError("missing duration value")
        yield text[start:index], char
        start = index + 1
    if start != len(text):
        raise InvalidDurationError("missing duration unit")


def _duration_section(text: str, units: str, scales: tuple[int, ...]) -> Fraction:
    total = Fraction(0)
    previous = -1
    for number, unit in _duration_parts(text):
        position = units.find(unit)
        if position <= previous:
            raise InvalidDurationError("invalid duration unit order")
        if unit != "S" and "." in number:
            raise InvalidDurationError("fractional duration unit")
        try:
            value = Fraction(number)
        except ValueError as error:
            raise InvalidDurationError("invalid duration value") from error
        total += value * scales[position]
        previous = position
    return total


def duration_seconds(value: str | None) -> Fraction | None:
    """Read a nonnegative xs:duration using DASH's fixed-size calendar units.

    A month is 30 days and a year is 12 months (DASH-IF timing model, section 20).
    Fractional seconds retain their declared precision, unlike timedelta.
    """
    if value is None:
        return None
    value = value.strip()
    if not value.startswith("P") or value == "P":
        raise InvalidDurationError("invalid duration")
    date, separator, time = value[1:].partition("T")
    if separator and not time:
        raise InvalidDurationError("missing duration time")
    return _duration_section(date, "YMD", (31104000, 2592000, 86400)) + _duration_section(
        time, "HMS", (3600, 60, 1)
    )


def integer(
    value: str | None, name: str, *, default: int | None = None, minimum: int | None = None
) -> int:
    """Convert an integer attribute, preserving explicit zero values."""
    if value is None:
        if default is None:
            raise SegmentError(f"missing {name}")
        return default
    value = value.strip()
    digits = value[1:] if value.startswith(("+", "-")) else value
    if not digits or not digits.isascii() or not digits.isdecimal():
        raise SegmentError(f"invalid {name}")
    try:
        result = int(value)
    except ValueError as error:
        raise SegmentError(f"invalid {name}") from error
    if minimum is not None and result < minimum:
        raise SegmentError(f"invalid {name}")
    return result


def availability_offset(value: str | None) -> Fraction | None:
    """None represents an infinite availability offset; absence defaults to zero."""
    if value is None:
        return Fraction(0)
    value = value.strip()
    if value == "INF":
        return None
    try:
        if "_" in value or not value.isascii():
            raise ValueError("invalid decimal")
        return Fraction(Decimal(value))
    except (ValueError, OverflowError, InvalidOperation) as error:
        raise SegmentError("invalid availabilityTimeOffset") from error


def aware_datetime(value: str) -> datetime:
    """Use isodate for timestamps and require an unambiguous timezone."""
    try:
        result = parse_datetime(value)
    except (ValueError, OverflowError) as error:
        raise SegmentError("invalid availability time") from error
    if result.utcoffset() is None:
        raise SegmentError("missing timezone")
    return result


def elapsed_seconds(value: timedelta) -> Fraction:
    """Convert datetime arithmetic without an intermediate float."""
    return Fraction(value.days * 86400 + value.seconds) + Fraction(value.microseconds, 1000000)
