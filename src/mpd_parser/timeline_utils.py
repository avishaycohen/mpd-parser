""" Utilities to parse, compute and handle time and duration related information in the mpd file """

from dataclasses import dataclass
from typing import Optional


@dataclass
class SegmentTiming:
    """Represents timing information for a segment
    It is a parsed and extended version of `tags.Segment` class.
    """

    start_time: float  # in seconds from period start
    duration: float  # in seconds
    number: int  # segment number in sequence
    time: Optional[int] = None  # raw timescale ticks for $Time$ templates
    availability_start: Optional[float] = None  # for live streams (epoch seconds)
    availability_end: Optional[float] = None  # for live streams (epoch seconds)
