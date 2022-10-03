'''test_util.py: Contains the set of tests for the util module in the Python FIT SDK'''

###########################################################################################
# Copyright 2022 Garmin International, Inc.
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
        (1029086357, datetime.utcfromtimestamp(1029086357 + 631065600)),
        (0, datetime.utcfromtimestamp(631065600)),
        (None, datetime.utcfromtimestamp(631065600)),
    ], ids=["Regular timestamp", "0 timestamp defaults to FITEPOCH", "Null timestamp defaults to FITEPOCH"],
)
def test_convert_datetime(given_timestamp, expected_datetime):
    '''Tests converting a FIT timestamp to a python utc datetime'''
    expected_datetime = expected_datetime.replace(tzinfo=timezone.utc)

    actual_datetime = util.convert_timestamp_to_datetime(given_timestamp)
    assert str(actual_datetime) == str(expected_datetime)
