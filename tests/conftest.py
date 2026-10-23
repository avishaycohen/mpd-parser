"""
Conftest module for package testing
"""

from typing import Any

import os
from mpd_parser.models.base_tags import Tag

MANIFESTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "manifests")) + "/"


def touch_attributes(obj: Any, verbose: bool = False):
    """ this function go over an object attributes and tries to see that they are populated """
    attrib_list = [a for a in dir(obj) if not a.startswith('__')]
    for attrib in attrib_list:
        if getattr(obj, attrib) is None:
            continue
        if not isinstance(getattr(obj, attrib), list):
            print(f'{attrib}: {getattr(obj, attrib)}')
            continue
        for item in getattr(obj, attrib):
            if isinstance(item, Tag):
                touch_attributes(item)
                continue
            print(f'{attrib}: {getattr(obj, attrib) if verbose else "object"}')
