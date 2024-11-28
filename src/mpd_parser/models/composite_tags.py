# pylint: disable=missing-function-docstring
""" Module for the compelex tags such as MPD, Period and others """
from functools import cached_property, lru_cache
from xml.etree.ElementTree import Element

from isodate import parse_datetime, parse_duration

from mpd_parser.attribute_parsers import (
    get_bool_value,
    get_float_value,
    get_int_value,
    get_list_of_type,
    organize_ns,
)
from mpd_parser.constants import (
    ANCESTOR_LOOKUP_STR_FORMAT,
    DERIVED_ATTRIBUTES_CACHE_SIZE,
    LOOKUP_STR_FORMAT,
    TWO_SECONDS,
    ZERO_SECONDS,
)
from mpd_parser.models.base_tags import (
    AssetIdentifiers,
    BaseURL,
    ContentComponent,
    ContentProtection,
    Descriptor,
    EventStream,
    Location,
    ProgramInfo,
    Subset,
    Tag,
    UTCTiming,
)
from mpd_parser.models.segment_tags import MultipleSegmentBase, SegmentBase, SegmentList
from mpd_parser.timeline_utils import SegmentTiming


class Period(Tag):
    """Period class, represents a period tag in mpd manifest."""

    @cached_property
    def id(self):
        return self.element.attrib.get("id")

    @cached_property
    def start(self):
        return self.element.attrib.get("start")

    @property
    @lru_cache(maxsize=DERIVED_ATTRIBUTES_CACHE_SIZE)
    def start_in_seconds(self) -> float:
        """Parsed and converted to seconds,
        Does not uses cached_property to block writes as it must be derived to maintain truthness
        """
        return (
            parse_duration(self.start).total_seconds() if self.start else ZERO_SECONDS
        )

    @cached_property
    def duration(self):
        return self.element.attrib.get("duration")

    @property
    def duration_in_seconds(self) -> float:
        """Parsed and converted to seconds"""
        return (
            parse_duration(self.duration).total_seconds()
            if self.duration
            else ZERO_SECONDS
        )

    @cached_property
    def bitstream_switching(self):
        return get_bool_value(self.element.attrib.get("bitstreamSwitching"))

    @cached_property
    def base_urls(self):
        return [
            BaseURL(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="BaseURL"))
        ]

    @cached_property
    def segment_bases(self):
        return [
            SegmentBase(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentBase")
            )
        ]

    @cached_property
    def segment_lists(self):
        return [
            SegmentList(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentList")
            )
        ]

    @cached_property
    def segment_templates(self):
        return [
            SegmentTemplate(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentTemplate")
            )
        ]

    @cached_property
    def asset_identifiers(self):
        return [
            AssetIdentifiers(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="AssetIdentifiers")
            )
        ]

    @cached_property
    def event_streams(self):
        return [
            EventStream(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="EventStream")
            )
        ]

    @cached_property
    def adaptation_sets(self):
        return [
            AdaptationSet(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="AdaptationSet")
            )
        ]

    @cached_property
    def subsets(self):
        return [
            Subset(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Subset"))
        ]


class MPD(Tag):  # pylint: disable=too-many-public-methods
    """
        MPD class represents the root of a mpd manifest,
    it is the top most tag of an XML file following the DASH format

    the element passed for MPD should be the root of the lxml.etree
    """

    def __init__(self, element: Element, encoding: str = "utf-8"):
        super().__init__(element=element)
        self.encoding = encoding
        self.tag_map = {"cenc": "xlmns:cenc"}

    @cached_property
    def namespace(self):
        value = self.element.nsmap
        if None in self.element.nsmap.keys():
            # can't use None as key in xpath
            value = organize_ns(self.element.nsmap)
        return value

    @cached_property
    def xmlns(self):
        return self.element.nsmap.get(None)

    @cached_property
    def id(self):
        return self.element.attrib.get("id")

    @cached_property
    def type(self):
        return self.element.attrib.get("type")

    @cached_property
    def profiles(self):
        return self.element.attrib.get("profiles")

    @cached_property
    def cenc(self):
        return self.element.attrib.get("xlmns:cenc")

    @cached_property
    def availability_start_time(self):
        return self.element.attrib.get("availabilityStartTime")

    @property
    @lru_cache
    def availability_start_time_in_seconds(self):
        return (
            (
                parse_datetime(self.availability_start_time)
                - parse_datetime("1970-01-01T00:00:00Z")
            ).total_seconds()
            if self.availability_start_time
            else None
        )

    @cached_property
    def availability_end_time(self):
        return self.element.attrib.get("availabilityEndTime")

    @property
    @lru_cache
    def availability_end_time_in_seconds(self):
        return (
            parse_duration(self.availability_end_time).total_seconds()
            if self.availability_end_time
            else None
        )

    @cached_property
    def publish_time(self):
        return self.element.attrib.get("publishTime")

    @cached_property
    def media_presentation_duration(self):
        return self.element.attrib.get("mediaPresentationDuration")

    @cached_property
    def minimum_update_period(self):
        return self.element.attrib.get("minimumUpdatePeriod")

    @property
    @lru_cache
    def minimum_update_period_in_seconds(self):
        return (
            parse_duration(self.minimum_update_period).total_seconds()
            if self.minimum_update_period
            else TWO_SECONDS  # default for minimumUpdatePeriod
        )

    @cached_property
    def min_buffer_time(self):
        return self.element.attrib.get("minBufferTime")

    @cached_property
    def time_shift_buffer_depth(self):
        return self.element.attrib.get("timeShiftBufferDepth")

    @property
    @lru_cache
    def time_shift_buffer_depth_in_seconds(self):
        return (
            parse_duration(self.time_shift_buffer_depth).total_seconds()
            if self.time_shift_buffer_depth
            else ZERO_SECONDS
        )

    @cached_property
    def suggested_presentation_delay(self):
        return self.element.attrib.get("suggestedPresentationDelay")

    @cached_property
    def max_segment_duration(self):
        return self.element.attrib.get("maxSegmentDuration")

    @cached_property
    def max_subsegment_duration(self):
        return self.element.attrib.get("maxSubsegmentDuration")

    @cached_property
    def program_informations(self):
        return [
            ProgramInfo(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="ProgramInformation")
            )
        ]

    @cached_property
    def base_urls(self):
        return [
            BaseURL(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="BaseURL"))
        ]

    @cached_property
    def locations(self):
        return [
            Location(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Location")
            )
        ]

    @cached_property
    def utc_timings(self):
        return [
            UTCTiming(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="UTCTiming")
            )
        ]

    @cached_property
    def periods(self):
        return [
            Period(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Period"))
        ]


class SegmentTemplate(MultipleSegmentBase):
    """SegmentTemplate tag"""

    @cached_property
    def media(self):
        return self.element.attrib.get("media")

    @cached_property
    def index(self):
        return self.element.attrib.get("index")

    @cached_property
    def initialization(self):
        return self.element.attrib.get("initialization")

    @cached_property
    def bitstream_switching(self):
        return self.element.attrib.get("bitstreamSwitching")

    @property
    @lru_cache(maxsize=DERIVED_ATTRIBUTES_CACHE_SIZE)
    def parsed_segment_timeline(self):
        """Calculate timing information for segments based on SegmentTemplate

        Returns:
            List[SegmentTiming]: List of segment timing information.
            if there's no duration and timescale in the template, returns empty list [].

        Example:
            >>> template.duration = 2000
            >>> template.timescale = 1000
            >>> template.start_number = 1
            >>> timings = TimelineUtils.get_segment_timing(template, 0)
            >>> print(timings[0].duration)  # 2.0
            >>> print(timings[0].start_time)  # 0.0
        """
        segments = []
        if not self.duration or not self.timescale:
            return segments

        # Get segment duration in seconds
        segment_duration = self.duration / self.timescale

        # Get relevant variables
        start_number = self.start_number or 1
        period_ancestor = None
        manifest_mpd = None
        try:
            period_ancestor = Period(
                self.element.xpath(ANCESTOR_LOOKUP_STR_FORMAT.format(target="Period"))[
                    0
                ]
            )
        except IndexError:
            pass

        try:
            manifest_mpd = MPD(
                self.element.xpath(ANCESTOR_LOOKUP_STR_FORMAT.format(target="MPD"))[0]
            )
        except IndexError:
            pass

        # Calculate segment count based on context
        if period_ancestor and period_ancestor.duration_in_seconds:
            # VOD content - use period duration
            segment_count = int(period_ancestor.duration_in_seconds / segment_duration)
        elif (
            manifest_mpd
            and manifest_mpd.availability_start_time
            and manifest_mpd.time_shift_buffer_depth
        ):
            # Live content - use time shift buffer if available
            time_shift_buffer = manifest_mpd.time_shift_buffer_depth_in_seconds
            segment_count = int(time_shift_buffer / segment_duration)
        else:
            # Dynamic content - use MPD update period
            update_period = manifest_mpd.minimum_update_period_in_seconds
            segment_count = int(update_period / segment_duration)

        current_time = period_ancestor.start_in_seconds or 0
        for i in range(start_number, start_number + segment_count):
            segment = SegmentTiming(
                start_time=current_time, duration=segment_duration, number=i
            )

            if manifest_mpd.availability_start_time:
                segment.availability_start = (
                    manifest_mpd.availability_start_time_in_seconds + current_time
                )
                segment.availability_end = segment.availability_start + segment_duration

            segments.append(segment)
            current_time += segment_duration

        return segments


class RepresentationBase(Tag):  # pylint: disable=too-many-public-methods
    """Generic representation tag"""

    def __init__(self, element):
        super().__init__(element)
        self.tag_map = {
            "maximum_sap_period": "maximumSAPPeriod",
            "start_with_sap": "startWithSAP",
        }

    @cached_property
    def profile(self):
        return self.element.attrib.get("profile")

    @cached_property
    def profiles(self):
        return self.element.attrib.get("profiles")

    @cached_property
    def width(self):
        return get_int_value(self.element.attrib.get("width"))

    @cached_property
    def height(self):
        return get_int_value(self.element.attrib.get("height"))

    @cached_property
    def sar(self):
        return self.element.attrib.get("sar")

    @cached_property
    def frame_rate(self):
        return self.element.attrib.get("frameRate")

    @cached_property
    def audio_sampling_rate(self):
        return self.element.attrib.get("audioSamplingRate")

    @cached_property
    def mime_type(self):
        return self.element.attrib.get("mimeType")

    @cached_property
    def segment_profiles(self):
        return self.element.attrib.get("segmentProfiles")

    @cached_property
    def codecs(self):
        return self.element.attrib.get("codecs")

    @cached_property
    def maximum_sap_period(self):
        return get_float_value(self.element.attrib.get("maximumSAPPeriod"))

    @cached_property
    def start_with_sap(self):
        return get_int_value(self.element.attrib.get("startWithSAP"))

    @cached_property
    def max_playout_rate(self):
        return get_float_value(self.element.attrib.get("maxPlayoutRate"))

    @cached_property
    def coding_dependency(self):
        return get_bool_value(self.element.attrib.get("codingDependency"))

    @cached_property
    def scan_type(self):
        return self.element.attrib.get("scanType")

    @cached_property
    def frame_packings(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="FramePacking")
            )
        ]

    @cached_property
    def audio_channel_configurations(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="AudioChannelConfiguration")
            )
        ]

    @cached_property
    def content_protections(self):
        return [
            ContentProtection(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="ContentProtection")
            )
        ]

    @cached_property
    def essential_properties(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="EssentialProperty")
            )
        ]

    @cached_property
    def supplemental_properties(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SupplementalProperty")
            )
        ]

    @cached_property
    def inband_event_stream(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="InbandEventStream")
            )
        ]


class SubRepresentation(RepresentationBase):
    """A sub representation tag"""

    @cached_property
    def level(self):
        return get_int_value(self.element.attrib.get("level"))

    @cached_property
    def bandwidth(self):
        return get_int_value(self.element.attrib.get("bandwidth"))

    @cached_property
    def dependency_level(self):
        return get_list_of_type(int, self.element.attrib.get("dependencyLevel"))

    @cached_property
    def content_component(self):
        return get_list_of_type(str, self.element.attrib.get("contentComponent"))


class Representation(RepresentationBase):
    """Representation tag"""

    @cached_property
    def id(self):
        return self.element.attrib.get("id")

    @cached_property
    def bandwidth(self):
        return get_int_value(self.element.attrib.get("bandwidth"))

    @cached_property
    def quality_ranking(self):
        return get_int_value(self.element.attrib.get("qualityRanking"))

    @cached_property
    def dependency_id(self):
        return get_list_of_type(str, self.element.attrib.get("dependencyId"))

    @cached_property
    def num_channels(self):
        return get_int_value(self.element.attrib.get("numChannels"))

    @cached_property
    def sample_rate(self):
        return get_int_value(self.element.attrib.get("sampleRate"))

    @cached_property
    def base_urls(self):
        return [
            BaseURL(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="BaseURL"))
        ]

    @cached_property
    def segment_bases(self):
        return [
            SegmentBase(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentBase")
            )
        ]

    @cached_property
    def segment_lists(self):
        return [
            SegmentList(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentList")
            )
        ]

    @cached_property
    def segment_templates(self):
        return [
            SegmentTemplate(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentTemplate")
            )
        ]

    @cached_property
    def sub_representations(self):
        return [
            SubRepresentation(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SubRepresentation")
            )
        ]


class AdaptationSet(RepresentationBase):  # pylint: disable=too-many-public-methods
    """Adaptation Set tag representation"""

    def __init__(self, element):
        super().__init__(element)
        self.tag_map = {"subsegment_starts_with_sap": "subsegmentStartsWithSAP"}

    @cached_property
    def id(self):
        return get_int_value(self.element.attrib.get("id"))

    @cached_property
    def group(self):
        return get_int_value(self.element.attrib.get("group"))

    @cached_property
    def lang(self):
        return self.element.attrib.get("lang")

    @cached_property
    def label(self):
        return self.element.attrib.get("label")

    @cached_property
    def content_type(self):
        return self.element.attrib.get("contentType")

    @cached_property
    def par(self):
        return self.element.attrib.get("par")

    @cached_property
    def min_bandwidth(self):
        return get_int_value(self.element.attrib.get("minBandwidth"))

    @cached_property
    def max_bandwidth(self):
        return get_int_value(self.element.attrib.get("maxBandwidth"))

    @cached_property
    def min_width(self):
        return get_int_value(self.element.attrib.get("minWidth"))

    @cached_property
    def max_width(self):
        return get_int_value(self.element.attrib.get("maxWidth"))

    @cached_property
    def min_height(self):
        return get_int_value(self.element.attrib.get("minHeight"))

    @cached_property
    def max_height(self):
        return get_int_value(self.element.attrib.get("maxHeight"))

    @cached_property
    def min_frame_rate(self):
        return self.element.attrib.get("minFrameRate")

    @cached_property
    def max_frame_rate(self):
        return self.element.attrib.get("maxFrameRate")

    @cached_property
    def segment_alignment(self):
        return get_bool_value(self.element.attrib.get("segmentAlignment"))

    @cached_property
    def selection_priority(self):
        return get_int_value(self.element.attrib.get("selectionPriority"))

    @cached_property
    def subsegment_starts_with_sap(self):
        return get_int_value(self.element.attrib.get("subsegmentStartsWithSAP"))

    @cached_property
    def subsegment_alignment(self):
        return get_bool_value(self.element.attrib.get("subsegmentAlignment"))

    @cached_property
    def bitstream_switching(self):
        return get_bool_value(self.element.attrib.get("bitstreamSwitching"))

    @cached_property
    def accessibilities(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Accessibility")
            )
        ]

    @cached_property
    def roles(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Role"))
        ]

    @cached_property
    def ratings(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="Rating"))
        ]

    @cached_property
    def viewpoints(self):
        return [
            Descriptor(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Viewpoint")
            )
        ]

    @cached_property
    def content_components(self):
        return [
            ContentComponent(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="ContentComponent")
            )
        ]

    @cached_property
    def base_urls(self):
        return [
            BaseURL(member)
            for member in self.element.xpath(LOOKUP_STR_FORMAT.format(target="BaseURL"))
        ]

    @cached_property
    def segment_bases(self):
        return [
            SegmentBase(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentBase")
            )
        ]

    @cached_property
    def segment_lists(self):
        return [
            SegmentList(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentList")
            )
        ]

    @cached_property
    def segment_templates(self):
        return [
            SegmentTemplate(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="SegmentTemplate")
            )
        ]

    @cached_property
    def representations(self):
        return [
            Representation(member)
            for member in self.element.xpath(
                LOOKUP_STR_FORMAT.format(target="Representation")
            )
        ]
