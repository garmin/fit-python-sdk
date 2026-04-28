'''test_util.py: Contains the set of tests for the util module in the Python FIT SDK'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


from datetime import datetime, timezone

import pytest
from garmin_fit_sdk import util


@pytest.mark.parametrize(
    "given_timestamp,expected_datetime",
    [
        (1029086357, datetime.fromtimestamp(1029086357 + 631065600, timezone.utc)),
        (0, datetime.fromtimestamp(631065600, timezone.utc)),
        (None, datetime.fromtimestamp(631065600, timezone.utc)),
    ], ids=["Regular timestamp", "0 timestamp defaults to FITEPOCH", "Null timestamp defaults to FITEPOCH"],
)
def test_convert_datetime(given_timestamp, expected_datetime):
    '''Tests converting a FIT timestamp to a python utc datetime'''
    expected_datetime = expected_datetime.replace(tzinfo=timezone.utc)

    actual_datetime = util.convert_timestamp_to_datetime(given_timestamp)
    assert str(actual_datetime) == str(expected_datetime)

@pytest.mark.parametrize(
    "given_datetime,expected_timestamp",
    [
        (
            datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            1073001600,  # 1704067200 (unix) - 631065600 (FIT epoch)
        ),
        (
            datetime.fromtimestamp(631065600, timezone.utc),
            0,  # the FIT epoch itself maps to timestamp 0
        ),
        (
            datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            -631065600,  # Unix epoch is before the FIT epoch → negative
        ),
        (
            datetime.fromtimestamp(1000000000 + 631065600, timezone.utc),
            1000000000,  # known large FIT timestamp round-trips correctly
        ),
    ],
    ids=[
        "Regular datetime",
        "FIT epoch returns 0",
        "Before FIT epoch returns negative",
        "Known large FIT timestamp",
    ],
)
def test_convert_datetime_to_timestamp(given_datetime, expected_timestamp):
    '''Tests converting a Python datetime to a FIT timestamp'''
    result = util.convert_datetime_to_timestamp(given_datetime)
    assert result == expected_timestamp


@pytest.mark.parametrize(
    "given_bytes,expected",
    [
        (b"hello\x00", "hello"),
        (b"hello\x00world\x00", ["hello", "world"]),
        (b"\x00", None),
        (b"\x00\x00\x00", None),
        (b"hello", "hello"),
        (b"caf\xc3\xa9\x00", "caf\u00e9"),
        (b"one\x00two\x00three\x00", ["one", "two", "three"]),
        (b"\xff\xfe\x00", None),
    ],
    ids=[
        "Single string with null terminator",
        "Two null-separated strings",
        "Only null byte returns None",
        "Multiple null bytes returns None",
        "String without null terminator",
        "UTF-8 multibyte character",
        "Three null-separated strings",
        "Invalid UTF-8 bytes ignored returns None",
    ],
)
def test__convert_string(given_bytes, expected):
    '''Tests converting a raw byte string to a Python string per the FIT protocol.'''
    assert util._convert_string(given_bytes) == expected
