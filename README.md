# mpd-parser

## Installation
```shell
$ python -m pip install mpd-parser
```

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

## Overview
A utility to parse mpeg dash mpd files quickly
This package is heavily inspired by [mpegdash package](https://github.com/sangwonl/python-mpegdash) the main difference is that I choose to relay on lxml for parsing, and not the standard xml library.

The decision to implement it with lxml is for two reasons:
1. lxml is faster then minidom
2. lxml mimics the ElementTree API which is a more pythonic approach to XMLs

mpegdash package has two distinct advantages over this package:
1. it does not require third party libraries.
2. it uses the classic DOM approach to parsing XML files. it is a well known standard.

Currently, the package supports parsing only, not the creation or object->string conversion.

## Benchmarks
TBA

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
   3. Benchmarks
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
10. add parsing from file
11. add parsing from URL
