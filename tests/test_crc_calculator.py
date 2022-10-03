'''test_crc_calculator.py: Contains the set of tests for the Stream class in the Python FIT SDK'''

###########################################################################################
# Copyright 2022 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import pytest
from garmin_fit_sdk import CrcCalculator

from tests.data import Data


@pytest.mark.parametrize(
    "data,crc_expected,is_correct_crc",
    [
        (Data.fit_file_invalid, 0x0000, False),
        (Data.fit_file_minimum, 0x488D, True),
        (Data.fit_file_short, 0xE3B9, True),
    ],
)
def test_file_header_crc(data, crc_expected, is_correct_crc):
    '''Tests which validate crc calcualtion on fit file headers'''
    if is_correct_crc:
        assert (CrcCalculator.calculate_crc(data, 0, 12) ==
                crc_expected) == is_correct_crc


@pytest.mark.parametrize(
    "data,file_length,crc_expected,is_correct_crc",
    [
        (Data.fit_file_invalid, len(Data.fit_file_invalid) - 2, 0x0000, False),
        (Data.fit_file_minimum, len(Data.fit_file_minimum) - 2, 0x0000, True),
        (Data.fit_file_short, len(Data.fit_file_short) - 2, 0x4F87, True),
    ],
)
def test_file_crc(data, crc_expected, is_correct_crc, file_length):
    '''Tests which validate crc calcualtion on fit file data.'''
    if is_correct_crc:
        assert (
            CrcCalculator.calculate_crc(data, 0, file_length) == crc_expected
        ) == is_correct_crc
