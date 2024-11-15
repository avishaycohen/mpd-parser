""" Utilities to parse, compute and handle time and duration related information in the mpd file """

from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class SegmentTiming:
    """Represents timing information for a segment
    It is a parsed and extended version of `tags.Segment` class.
    """

    start_time: float  # in seconds from period start
    duration: float  # in seconds
    number: int  # segment number in sequence
    availability_start: Optional[datetime] = None  # for live streams
    availability_end: Optional[datetime] = None  # for live streams
