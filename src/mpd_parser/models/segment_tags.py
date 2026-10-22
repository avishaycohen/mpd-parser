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


def _find_inherited_attribute(element, local_name, attrib_name):
    """Find inherited attribute from ancestor AdaptationSet or Period."""
    el_ns = element.tag.split('}')[0] + '}' if '}' in element.tag else ''
    target_child_tag = f"{el_ns}{local_name}" if el_ns else local_name

    for ancestor in element.iterancestors():
        local_ancestor = ancestor.tag.split('}')[-1] if '}' in ancestor.tag else ancestor.tag
        if local_ancestor not in ("AdaptationSet", "Period"):
            continue
 
        for child in ancestor:
            if child is not element and child.tag == target_child_tag:
                val = child.attrib.get(attrib_name)
                if val is not None:
                    return val

        val = ancestor.attrib.get(attrib_name)
        if val is not None:
            return val

        if local_ancestor == "Period":
            break
    return None


def _find_inherited_element(element, local_name, child_name):
    """Find inherited child element (e.g. SegmentTimeline) from ancestor AdaptationSet or Period."""
    el_ns = element.tag.split('}')[0] + '}' if '}' in element.tag else ''
    target_child_tag = f"{el_ns}{local_name}" if el_ns else local_name
    target_subchild_tag = f"{el_ns}{child_name}" if el_ns else child_name

    for ancestor in element.iterancestors():
        local_ancestor = ancestor.tag.split('}')[-1] if '}' in ancestor.tag else ancestor.tag
        if local_ancestor not in ("AdaptationSet", "Period"):
            continue

        for child in ancestor:
            if child is element or child.tag != target_child_tag:
                continue
            for subchild in child:
                if subchild.tag == target_subchild_tag:
                    return subchild

        if local_ancestor == "Period":
            break
    return None


class SegmentBase(Tag):
    """Basic Segment tag representation"""

    @cached_property
    def timescale(self):
        val = self.element.attrib.get("timescale")
        if val is not None:
            return get_int_value(val)
        local_name = self.element.tag.split('}')[-1]
        ancestor_val = _find_inherited_attribute(self.element, local_name, "timescale")
        if ancestor_val is not None:
            return get_int_value(ancestor_val)
        return 1

    @cached_property
    def index_range(self):
        return self.element.attrib.get("indexRange")

    @cached_property
    def index_range_exact(self):
        return get_bool_value(self.element.attrib.get("indexRangeExact"))

    @cached_property
    def presentation_time_offset(self):
        val = self.element.attrib.get("presentationTimeOffset")
        if val is not None:
            return get_int_value(val)
        local_name = self.element.tag.split('}')[-1]
        ancestor_val = _find_inherited_attribute(self.element, local_name, "presentationTimeOffset")
        if ancestor_val is not None:
            return get_int_value(ancestor_val)
        return 0

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
        val = self.element.attrib.get("duration")
        if val is not None:
            return get_int_value(val)
        local_name = self.element.tag.split('}')[-1]
        ancestor_val = _find_inherited_attribute(self.element, local_name, "duration")
        if ancestor_val is not None:
            return get_int_value(ancestor_val)
        return None

    @cached_property
    def start_number(self):
        val = self.element.attrib.get("startNumber")
        if val is not None:
            return get_int_value(val)
        local_name = self.element.tag.split('}')[-1]
        ancestor_val = _find_inherited_attribute(self.element, local_name, "startNumber")
        if ancestor_val is not None:
            return get_int_value(ancestor_val)
        return 1

    @cached_property
    def segment_timeline(self):
        elements = self.element.xpath(
            LOOKUP_STR_FORMAT.format(target="SegmentTimeline")
        )
        if elements:
            return SegmentTimeline(elements[0])
        local_name = self.element.tag.split('}')[-1]
        ancestor_el = _find_inherited_element(self.element, local_name, "SegmentTimeline")
        if ancestor_el is not None:
            return SegmentTimeline(ancestor_el)
        return None

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
