"""Template syntax and field binding without XML or timing calculations."""

import pytest

from mpd_parser.exceptions import InvalidTemplateError
from mpd_parser._segments.template import URLTemplate


def test_literal_url_escapes():
    """Percent escapes outside fields are ordinary URL text."""
    assert URLTemplate.parse("media%20name.m4s").bind({}).render() == "media%20name.m4s"


def test_escaped_dollar():
    """Doubled dollars are literals, including next to a substituted field."""
    template = URLTemplate.parse("$$$Number$$$$$").bind({})
    assert template.render(number=7) == "$7$$"


def test_representation_binding_is_reusable():
    """One compiled template serves multiple segments without reparsing."""
    template = URLTemplate.parse("$RepresentationID$/$Number$.m4s").bind(
        {"RepresentationID": "video"}
    )
    assert template.render(number=7) == "video/7.m4s"
    assert template.render(number=8) == "video/8.m4s"


def test_bound_values_are_not_reparsed():
    """A dollar inside an identifier remains literal data."""
    template = URLTemplate.parse("$RepresentationID$").bind({"RepresentationID": "$Number$"})
    assert template.render(number=7) == "$Number$"


def test_timestamp_precision():
    """URL timestamps never pass through a floating-point conversion."""
    assert URLTemplate.parse("$Time$").bind({}).render(time=9007199254740993) == "9007199254740993"


def test_decimal_padding():
    """Padding is a minimum width, not truncation."""
    template = URLTemplate.parse("$Number%03d$").bind({})
    assert template.render(number=7) == "007"
    assert template.render(number=1234) == "1234"


@pytest.mark.parametrize("conversion", ["d", "i", "u"])
def test_decimal_conversions(conversion):
    """DASH integer conversions share decimal formatting."""
    template = URLTemplate.parse(f"$Number%03{conversion}$").bind({})
    assert template.render(number=12) == "012"


@pytest.mark.parametrize(("conversion", "expected"), [("o", "0014"), ("x", "000c"), ("X", "000C")])
def test_alternate_integer_bases(conversion, expected):
    """Octal and hexadecimal retain their declared base and case."""
    template = URLTemplate.parse(f"$Bandwidth%04{conversion}$").bind({"Bandwidth": 12})
    assert template.render() == expected


def test_unclosed_field():
    """The scanner rejects a missing closing delimiter."""
    with pytest.raises(InvalidTemplateError):
        URLTemplate.parse("video/$Number")


def test_unknown_field():
    """The field parser rejects names outside the supported DASH grammar."""
    with pytest.raises(InvalidTemplateError):
        URLTemplate.parse("$Unknown$")


@pytest.mark.parametrize("formatting", ["5d", "00d", "03f", "0xd"])
def test_invalid_numeric_format(formatting):
    """Malformed numeric formats fail while compiling, before enumeration."""
    with pytest.raises(InvalidTemplateError):
        URLTemplate.parse(f"$Number%{formatting}$")


def test_text_field_cannot_be_formatted():
    """RepresentationID is text, even when its contents look numeric."""
    with pytest.raises(InvalidTemplateError):
        URLTemplate.parse("$RepresentationID%03d$")


def test_missing_representation_value():
    """Binding reports absent data before rendering any segments."""
    with pytest.raises(InvalidTemplateError):
        URLTemplate.parse("$Bandwidth$").bind({})


def test_missing_segment_value():
    """Rendering cannot silently invent a sequence number of zero."""
    template = URLTemplate.parse("$Number$").bind({})
    with pytest.raises(InvalidTemplateError):
        template.render()


def test_unrepresentable_format_width_has_template_error():
    """A width beyond the formatter's range remains a template failure."""
    template = URLTemplate.parse("$Number%0999999999999999999999999999999999d$").bind({})
    with pytest.raises(InvalidTemplateError):
        template.render(number=1)


@pytest.mark.parametrize("field", ["Number", "Time"])
def test_initialization_cannot_reference_a_segment(field):
    """Initialization has no media sequence number or timestamp."""
    with pytest.raises(InvalidTemplateError):
        URLTemplate.parse(f"${field}$").bind({}, initialization=True)
