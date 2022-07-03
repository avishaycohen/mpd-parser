"""
Test module for attribute_parsers.py
"""
from math import inf
from pytest import mark

from mpd_parser.attribute_parsers import get_float_value, get_bool_value


@mark.parametrize("input_value, expected_output",
                  [
                      ("INF", inf),
                      ("5", 5.0),
                      ("10.000000", 10.0),
                      ("24", 24.0),
                      (None, None)
                  ])
def test_get_float_value(input_value, expected_output):
    assert get_float_value(input_value) == expected_output


@mark.parametrize("input_value, expected_output",
                  [
                      ('true', True),
                      ('false', False),
                      ('None', None),
                      ('1', None),
                      (None, None),
                      ('TRUE', None)
                  ])
def test_get_bool_value(input_value, expected_output):
    assert get_bool_value(input_value) == expected_output
