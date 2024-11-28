# pylint: disable=missing-function-docstring
""" Segment and timeline related tags """
from functools import cached_property
from mpd_parser.attribute_parsers import get_bool_value, get_float_value, get_int_value
from mpd_parser.constants import LOOKUP_STR_FORMAT
from mpd_parser.models.base_tags import URL, Tag


class Initialization(URL):
    """Initialization tag representation"""


class RepresentationIndex(URL):
    """Representation Index tag representation"""


class BitstreamSwitchings(URL):
    """BitstreamSwitching tag representation"""


class Segment(Tag):
    """S tag representation. A single segment of video"""

    @cached_property
    def t(self):
        """starting time of the segment"""
        return get_int_value(self.element.attrib.get("t"))

    @cached_property
    def d(self):
        """duration time of the segmeent"""
        return get_int_value(self.element.attrib.get("d"))

    @cached_property
    def r(self):
        """number of repeating segments"""
        return get_int_value(self.element.attrib.get("r"))


class SegmentBase(Tag):
    """Basic Segment tag representation"""

    @cached_property
    def timescale(self):
        return get_int_value(self.element.attrib.get("timescale"))

    @cached_property
    def index_range(self):
        return self.element.attrib.get("indexRange")

    @cached_property
    def index_range_exact(self):
        return get_bool_value(self.element.attrib.get("indexRangeExact"))

    @cached_property
    def presentation_time_offset(self):
        return get_int_value(self.element.attrib.get("presentationTimeOffset"))

    @cached_property
    def availability_time_offset(self):
        return get_float_value(self.element.attrib.get("availabilityTimeOffset"))

    @cached_property
    def availability_time_complete(self):
        return get_bool_value(self.element.attrib.get("availabilityTimeComplete"))

    @cached_property
    def initializations(self):
        return [
            Initialization(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Initialization")
            )
        ]

    @cached_property
    def representation_indexes(self):
        return [
            RepresentationIndex(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="RepresentationIndex")
            )
        ]

class MultipleSegmentBase(SegmentBase):
    """Multiple segments tag"""

    @cached_property
    def duration(self):
        return get_int_value(self.element.attrib.get("duration"))

    @cached_property
    def start_number(self):
        return get_int_value(self.element.attrib.get("startNumber"))

    @cached_property
    def segment_timelines(self):
        return [
            SegmentTimeline(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentTimeline")
            )
        ]

    @cached_property
    def bitstream_switchings(self):
        return [
            BitstreamSwitchings(member)
            for member in self.element.xpath(
                './*[local-name(.) = "BitstreamSwitching" ]'
            )
        ]


class SegmentURL(Tag):
    """SegmentURL tag"""

    @cached_property
    def media(self):
        return self.element.attrib.get("media")

    @cached_property
    def media_range(self):
        return self.element.attrib.get("mediaRange")

    @cached_property
    def index(self):
        return self.element.attrib.get("index")

    @cached_property
    def index_range(self):
        return self.element.attrib.get("indexRange")


class SegmentList(MultipleSegmentBase):
    """SegmentList tag"""

    @cached_property
    def segment_urls(self):
        return [
            SegmentURL(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentURL")
            )
        ]

class SegmentTimeline(Tag):
    """SegmentTimeline tag repr"""

    @cached_property
    def segments(self):
        return [
            Segment(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="S"))
        ]
