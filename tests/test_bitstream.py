'''test_bitstream.py: Contains the set of tests for the Bitstream class in the Python FIT SDK'''

###########################################################################################
# Copyright 2025 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import pytest
from garmin_fit_sdk import BitStream
from garmin_fit_sdk import fit as FIT


class TestFromByteArray:
    def test_next_bit(self):
        bit_stream = BitStream([0xAA, 0xAA], FIT.BASE_TYPE['UINT8'])
        values = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]

        index = 0
        for expected in values:
            assert bit_stream.bits_available() == len(values) - index
            assert bit_stream.has_bits_available() is True

            actual = bit_stream.read_bit()
            assert actual == expected

            assert bit_stream.bits_available() == len(values) - index - 1

            index += 1

    @pytest.mark.parametrize(
        "test_data",
        [
            {
                'data': [0xAA],
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [4, 4],
                'values': [0xA, 0xA]
            },
            {
                'data': [0xAA],
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [8],
                'values': [0xAA]
            },
            {
                'data': [0xAA, 0xAA],
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [16],
                'values': [0xAAAA]
            },
            {
                'data': [0xFF, 0xFF],
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [16],
                'values': [0xFFFF]
            },
            {
                'data': [0xAA, 0xAA, 0xAA, 0x2A],
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [32],
                'values': [0x2AAAAAAA]
            },
            {
                'data': [0x10, 0x32, 0x54, 0x76],
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [32],
                'values': [0x76543210]
            },
        ],
    )
    def test_from_byte_array(self, test_data):
        bit_stream = BitStream(test_data['data'], test_data['base_type'])
        index = 0
        for expected in test_data['values']:
            actual = bit_stream.read_bits(test_data['bits_to_read'][index])
            assert actual == expected
            index += 1

class TestFromInteger:

    def test_next_bit(self):
        bit_stream = BitStream(0x0FAA, FIT.BASE_TYPE['UINT16'])
        values = [0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0]

        index = 0
        for expected in values:
            assert bit_stream.bits_available() == len(values) - index
            assert bit_stream.has_bits_available() is True

            actual = bit_stream.read_bit()
            assert actual == expected

            assert bit_stream.bits_available() == len(values) - index - 1

            index += 1

    @pytest.mark.parametrize(
        "test_data",
        [
            {
                'data': 0xAA,
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [4],
                'values': [0xA]
            },
            {
                'data': 0xAA,
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [4, 4],
                'values': [0xA, 0xA]
            },
            {
                'data': 0xAA,
                'base_type': FIT.BASE_TYPE['UINT8'],
                'bits_to_read': [4, 1, 1, 1, 1],
                'values': [0xA, 0x0, 0x1, 0x0, 0x1]
            },
            {
                'data': 0xAA,
                'base_type': FIT.BASE_TYPE['UINT16'],
                'bits_to_read': [4, 1, 1, 1, 1],
                'values': [0xA, 0x0, 0x1, 0x0, 0x1]
            },
            {
                'data': [0xAAAA, 0x2AAA],
                'base_type': FIT.BASE_TYPE['UINT16'],
                'bits_to_read': [32],
                'values': [0x2AAAAAAA]
            },
            {
                'data': [0xAAAAAAAA],
                'base_type': FIT.BASE_TYPE['UINT32'],
                'bits_to_read': [16, 8, 8],
                'values': [0xAAAA, 0xAA, 0xAA]
            },
        ],
    )
    def test_from_integer(self, test_data):
        bit_stream = BitStream(test_data['data'], test_data['base_type'])
        index = 0
        for expected in test_data['values']:
            actual = bit_stream.read_bits(test_data['bits_to_read'][index])
            assert actual == expected
            index += 1

def test_exception_raised_big_overstep():
    '''Test that makes sure that an index error exception is raised when reading too many bits.'''
    try:
        bit_stream = BitStream(0x0FAA, FIT.BASE_TYPE['UINT16'])
        bit_stream.read_bits(20)
        assert False
    except IndexError:
        assert True
def test_exception_raised_boundary():
    '''Test that makes sure that an index error exception is raised when reading one too many bits.'''
    try:
        bit_stream = BitStream(0x0FAA, FIT.BASE_TYPE['UINT16'])
        bit_stream.read_bits(16)
        bit_stream.read_bit()
        assert False
    except IndexError:
        assert True
