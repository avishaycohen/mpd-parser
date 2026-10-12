"""DASH URL templates: scan literals, parse fields, then render bound values."""

from collections.abc import Mapping
from dataclasses import dataclass

from mpd_parser.exceptions import InvalidTemplateError

_FIELDS = {"RepresentationID", "Bandwidth", "Number", "Time"}


def _numeric_format(text: str) -> str:
    """Translate DASH's %0[width][conversion] to a Python integer format."""
    if len(text) < 3 or text[0] != "0" or text[-1] not in "diouxX":
        raise InvalidTemplateError("invalid numeric format")
    width = text[1:-1]
    if not width.isascii() or not width.isdecimal():
        raise InvalidTemplateError("invalid format width")
    try:
        format_width = int(width)
    except ValueError as error:
        raise InvalidTemplateError("invalid format width") from error
    if format_width == 0:
        raise InvalidTemplateError("invalid format width")
    conversion = "d" if text[-1] in "diu" else text[-1]
    return f"0{format_width}{conversion}"


@dataclass(frozen=True)
class TemplateField:
    """A validated identifier and optional numeric format."""

    name: str
    format_spec: str = ""

    @classmethod
    def parse(cls, text: str) -> "TemplateField":
        """Parse one field; dollar delimiters are handled by URLTemplate."""
        name, separator, formatting = text.partition("%")
        if name not in _FIELDS:
            raise InvalidTemplateError("unknown template field")
        if separator and name == "RepresentationID":
            raise InvalidTemplateError("formatted RepresentationID")
        return cls(name, _numeric_format(formatting) if separator else "")

    def render(self, values: Mapping[str, str | int]) -> str:
        """Substitute one field without changing literals or URL percent escapes."""
        if self.name not in values:
            raise InvalidTemplateError(f"missing {self.name}")
        value = values[self.name]
        if self.name == "RepresentationID":
            return str(value)
        if not isinstance(value, int):
            raise InvalidTemplateError(f"invalid {self.name}")
        try:
            return format(value, self.format_spec or "d")
        except (ValueError, OverflowError) as error:
            raise InvalidTemplateError("invalid numeric format") from error


@dataclass(frozen=True)
class URLTemplate:
    """A parsed template, reusable across all segments of a representation."""

    parts: tuple[str | TemplateField, ...]

    @classmethod
    def parse(cls, text: str) -> "URLTemplate":
        """Scan dollar-delimited fields; a doubled dollar is a literal dollar."""
        parts: list[str | TemplateField] = []
        position = 0
        while position < len(text):
            opening = text.find("$", position)
            if opening == -1:
                parts.append(text[position:])
                break
            parts.append(text[position:opening])
            closing = text.find("$", opening + 1)
            if closing == -1:
                raise InvalidTemplateError("unclosed template field")
            field = text[opening + 1 : closing]
            parts.append(TemplateField.parse(field) if field else "$")
            position = closing + 1
        return cls(tuple(parts))

    def bind(
        self, values: Mapping[str, str | int], *, initialization: bool = False
    ) -> "URLTemplate":
        """Resolve representation fields once; initialization cannot use segment fields."""
        parts: list[str | TemplateField] = []
        for part in self.parts:
            if isinstance(part, str):
                parts.append(part)
            elif part.name in {"Number", "Time"}:
                if initialization:
                    raise InvalidTemplateError("segment field in initialization")
                parts.append(part)
            else:
                parts.append(part.render(values))
        return URLTemplate(tuple(parts))

    def render(self, *, number: int | None = None, time: int | None = None) -> str:
        """Render a bound template using the original segment number and timestamp."""
        values = {
            name: value for name, value in (("Number", number), ("Time", time)) if value is not None
        }
        return "".join(
            part if isinstance(part, str) else part.render(values) for part in self.parts
        )
