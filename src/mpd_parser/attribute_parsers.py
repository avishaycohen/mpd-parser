"""
Module for utility functions
"""
import math
import re
from typing import Optional, Type

from lxml.etree import Element


def organize_ns(namespace_mapping: dict[Optional[str]]) -> dict:
    """
        xpath isn't compatible with None as key
    Args:
        namespace_mapping (dict): original namespace mapping

    Returns:
        dict: key values for the ns map without None as key
    """
    new_mapping: dict[Optional[str]] = dict(namespace_mapping)
    new_mapping['ns'] = namespace_mapping[None]
    new_mapping.pop(None)
    return new_mapping


def get_text_value(element: Element, tag_name: str, direct_child: bool = True) -> list[str]:
    """
        Extract the value of a text field from a tag
    Args:
        element: lxml element node
        tag_name: name of target tag
        direct_child: should we look only in direct children for results

    Returns:
        list of lxml elements that has tag_name as their tag
    """
    return [member.text for member in
            element.xpath(f'{"./" if direct_child else ".//"}*[local-name(.) = "{tag_name}" ]')]


def get_float_value(value: str) -> float:
    """ Helper to return a float from str """
    if value is None:
        return None
    return float(value) if value != 'INF' else math.inf


def get_bool_value(value: str) -> Optional[bool]:
    """ Helper to return a bool from str """
    if value == 'true':
        return True
    if value == 'false':
        return False
    return None


def get_int_value(value: str) -> Optional[int]:
    """
        Helper to return int/none value
    this makes sure we are not returning a number when a tag/attrib
    was not included in the manifest file
    """
    return value if value is None else int(value)


def get_list_of_type(target_type: Type, attribute_value: str) -> list[str]:
    """ Helper to return a list of strings from the tag attributte """
    if attribute_value is None:
        return []
    return [target_type(item) for item in re.split(r"[, ]", attribute_value)]
