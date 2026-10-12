# mpd-parser

## Installation
```shell
$ python -m pip install mpd-parser
```

*Note: `mpd-parser` requires Python 3.10 or newer.*

## Usage
### Importing

```python
from mpd_parser.parser import Parser
```
### parse from string
```python
with open("path/to/file.mpd", mode="r") as manifest_file:
    mpd_string = manifest_file.read()
    parsed_mpd = Parser.from_string(mpd_string)
```

### parse from file
```python
input_file = "path/to/file.mpd"
mpd = Parser.from_file(input_file)
```

### convert back to string
```python
mpd_as_xml_string = Parser.to_string(parsed_mpd)
```

### Segment URLs

```python
mpd = Parser.from_file("manifest.mpd")
for url in mpd.iter_segment_urls("https://example.com/video/manifest.mpd"):
    print(url)
```

Yields initialization and media URLs in representation and Period order.
Supports inherited templates, timelines, explicit lists, and single-file media.
Use `Representation.iter_segment_urls()` to enumerate one representation.
Each call returns a single-use iterator. URLs are resolved as iteration advances;
callers can stop early or collect the results if needed.

The optional base URL is a manifest URL or a directory URL ending in `/`.
Remote MPDs default to their final response URL; local references otherwise stay
relative. The first `BaseURL` at each level selects a mirror. Byte ranges retain
repeated URLs, with range metadata accessible through the existing parsed tags.

Execution starts when the iterator is first advanced. Live enumeration captures
the current UTC time then and uses it throughout that iteration. Pass a
timezone-aware `now` to select a specific time or use a corrected server clock.
Enumeration performs no network requests or MPD refreshes. Initialization is
emitted only when media is available.

The iterator reads the existing MPD tree without copying it. Finish or discard
an iterator before editing the tree; create a new iterator after edits.

Enumeration errors derive from `mpd_parser.exceptions.SegmentError`, a
`ValueError` subclass. `InvalidDurationError`, `InvalidTemplateError`, and
`InvalidTimelineError` identify invalid descriptions. `UnboundedTimelineError`
indicates that an open-ended template lacks a finite Period or availability
boundary. Errors arise while advancing the iterator, potentially after earlier
URLs have been yielded.

## Overview
A utility to parse mpeg dash mpd files quickly
This package is heavily inspired by [mpegdash package](https://github.com/sangwonl/python-mpegdash) the main difference is that I choose to relay on lxml for parsing, and not the standard xml library.

The decision to implement it with lxml is for two reasons:
1. lxml is faster then minidom
2. lxml mimics the ElementTree API which is a more pythonic approach to XMLs

mpegdash package has two distinct advantages over this package:
1. it does not require third party libraries.
2. it uses the classic DOM approach to parsing XML files. it is a well known standard.

## Benchmarks
You can run the benchmarks using the scripts in the `benchmarks/` directory.

```shell
$ python benchmarks/bench_mpd_parser.py --file manifests/test_manifest_1mb.mpd
$ python benchmarks/bench_mpegdash.py --file manifests/test_manifest_1mb.mpd
```

### Results
On a 1MB MPD file with 6,200 representations:
- **`mpd-parser`**: ~7 ms / parse
- **`mpegdash`**: ~174 ms / parse

*(mpd-parser is ~24x faster than mpegdash on this payload).*

## Example manifests
Taken from https://ottverse.com/free-mpeg-dash-mpd-manifest-example-test-urls/
These are what I used to test and benchmark the package.

## Missing unit-tests
1. tags
2. attribute parsers
3. full manifest testing

## Contributing
TBA

### Build locally
```shell
python -m build
```
### Run pylint locally
I try to keep the pylint score above 9.
```shell
python -m pylint ./mpd_parser/
```

## TODO
1. ~~finish working on periods and sub tags~~
   1. ~~periods~~
   2. ~~adapt-sets~~
   3. ~~segment bases~~
   4. ~~segment lists~~
   5. ~~segment templates~~
   6. ~~asset ids~~
   7. ~~event streams~~
   8. ~~subsets~~
2. ~~create package locally~~
3. ~~test it~~
4. complete readme
   1. ~~installation~~
   2. ~~usage~~
   3. ~~Benchmarks~~
   4. contributing
5. ~~push to github~~
6. ~~push package to pypi~~
7. add github actions
   1. ~~pylint~~
   2. ~~pytest~~
   3. ~~build package~~
   4. ~~push package~~
8. complete unit-tests
9. refactor tags to multiple files
10. Parsing:
    1. ~~parsing from string~~
    2. ~~parsing from file~~
    3. parsing from URL
11. save mpd object:
    1. ~~object to string~~
    2. object to file
