""" Namespace for constants used across the lib """

# number constants
DERIVED_ATTRIBUTES_CACHE_SIZE = 5
ZERO_SECONDS = 0.0
TWO_SECONDS = 2.0

# parser constants
KEYS_NOT_FOR_SETTING = ['element', 'tag_map', 'encoding']

# xpath constants
LOOKUP_STR_FORMAT = './*[local-name(.) = "{target}" ]'
ANCESTOR_LOOKUP_STR_FORMAT = 'ancestor::*[local-name(.) = "{target}" ][1]'
