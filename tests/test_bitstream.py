'''test_bitstream.py: Contains the set of tests for the Bitstream class in the Python FIT SDK'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import pytest
from garmin_fit_sdk import BitStream
from garmin_fit_sdk import fit as FIT


class TestReadBit:
    def test_from_byte_array(self):
        '''Tests read_bit() reading each bit from a byte array LSB first.'''
        bit_stream = BitStream([0xAA, 0xFF], FIT.BASE_TYPE['UINT8'])
        expected_values = [0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        for index, expected in enumerate(expected_values):
            assert bit_stream.bits_available() == len(expected_values) - index
            assert bit_stream.has_bits_available() is True
            assert bit_stream.read_bit() == expected
            assert bit_stream.bits_available() == len(expected_values) - index - 1

    def test_from_integer(self):
        '''Tests read_bit() reading each bit from a single integer LSB first.'''
        bit_stream = BitStream(0xAAFF, FIT.BASE_TYPE['UINT16'])
        expected_values = [1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1]

        for index, expected in enumerate(expected_values):
            assert bit_stream.bits_available() == len(expected_values) - index
            assert bit_stream.has_bits_available() is True
            assert bit_stream.read_bit() == expected
            assert bit_stream.bits_available() == len(expected_values) - index - 1


class TestReadBitsFromArray:
    @pytest.mark.parametrize(
        "data,base_type,bits_to_read,expected_values,takes_fast_path",
        [
            ([0xAB],                             FIT.BASE_TYPE['UINT8'],  [8],        [0xAB],                              True),
            ([0xAB],                             FIT.BASE_TYPE['UINT8'],  [4, 4],     [0xB, 0xA],                          False),
            ([0xAB],                             FIT.BASE_TYPE['UINT8'],  [4,1,1,1,1],[0xB, 0, 1, 0, 1],                   False),
            ([0xAA, 0xCB],                       FIT.BASE_TYPE['UINT8'],  [16],       [0xCBAA],                            False),
            ([0xAA, 0xCB, 0xDE, 0xFF],           FIT.BASE_TYPE['UINT8'],  [16, 16],   [0xCBAA, 0xFFDE],                    False),
            ([0xAA, 0xCB, 0xDE, 0xFF],           FIT.BASE_TYPE['UINT8'],  [32],       [0xFFDECBAA],                        False),
            ([0xAA, 0xBB],                       FIT.BASE_TYPE['UINT8'],  [8, 8],     [0xAA, 0xBB],                        True),
            ([0xABCD, 0xEF01],                   FIT.BASE_TYPE['UINT16'], [16, 16],   [0xABCD, 0xEF01],                    True),
            ([0xABCD, 0xEF01],                   FIT.BASE_TYPE['UINT16'], [32],       [0xEF01ABCD],                        False),
            ([0xABCDEF01],                       FIT.BASE_TYPE['UINT32'], [32],       [0xABCDEF01],                        True),
            ([0xABCDEF01, 0x12345678],           FIT.BASE_TYPE['UINT32'], [32, 32],   [0xABCDEF01, 0x12345678],            True),
            ([0x7BCDEF0123456789],               FIT.BASE_TYPE['UINT64'], [64],       [0x7BCDEF0123456789],                True),
            ([0x7BCDEF0123456789,
              0x0BCDEF0123456789],               FIT.BASE_TYPE['UINT64'], [64, 64],   [0x7BCDEF0123456789,
                                                                                        0x0BCDEF0123456789],                True),
            ([0xABCDEF0123456789],               FIT.BASE_TYPE['UINT64'], [32],       [0x23456789],                        False),
            ([0xABCDEF0123456789],               FIT.BASE_TYPE['UINT64'], [32, 32],   [0x23456789, 0xABCDEF01],            False),
        ],
        ids=[
            "UInt8 [0xAB] - 8",
            "UInt8 [0xAB] - 4,4",
            "UInt8 [0xAB] - 4,1,1,1,1",
            "UInt8 [0xAA, 0xCB] - 16 (cross-boundary)",
            "UInt8 [0xAA, 0xCB, 0xDE, 0xFF] - 16,16 (cross-boundary)",
            "UInt8 [0xAA, 0xCB, 0xDE, 0xFF] - 32 (cross-boundary)",
            "UInt8 [0xAA, 0xBB] - 8,8",
            "UInt16 [0xABCD, 0xEF01] - 16,16",
            "UInt16 [0xABCD, 0xEF01] - 32",
            "UInt32 [0xABCDEF01] - 32",
            "UInt32 [0xABCDEF01, 0x12345678] - 32,32",
            "UInt64 [0x7BCDEF0123456789] - 64",
            "UInt64 [0x7BCDEF0123456789, 0x0BCDEF0123456789] - 64,64",
            "UInt64 [0xABCDEF0123456789] - 32",
            "UInt64 [0xABCDEF0123456789] - 32,32",
        ],
    )
    def test_read_bits(self, data, base_type, bits_to_read, expected_values, takes_fast_path):
        bit_stream = BitStream(data, base_type)
        for i, expected in enumerate(expected_values):
            assert bit_stream.read_bits(bits_to_read[i]) == expected
        assert (bit_stream._array is None) == takes_fast_path


class TestReadBitsFromInteger:
    @pytest.mark.parametrize(
        "data,base_type,bits_to_read,expected_values,takes_fast_path",
        [
            (0xAB,               FIT.BASE_TYPE['UINT8'],  [8],         [0xAB],                   True),
            (0xAB,               FIT.BASE_TYPE['UINT8'],  [4, 4],      [0xB, 0xA],               False),
            (0xAB,               FIT.BASE_TYPE['UINT8'],  [4,1,1,1,1], [0xB, 0, 1, 0, 1],        False),
            (0xAACB,             FIT.BASE_TYPE['UINT16'], [16],        [0xAACB],                 True),
            (0xABCDEF01,         FIT.BASE_TYPE['UINT32'], [16, 16],    [0xEF01, 0xABCD],          False),
            (0xABCDEF01,         FIT.BASE_TYPE['UINT32'], [32],        [0xABCDEF01],             True),
            (0x7BCDEF0123456789, FIT.BASE_TYPE['UINT64'], [64],        [0x7BCDEF0123456789],     True),
            (0xABCDEF0123456789, FIT.BASE_TYPE['UINT64'], [64],        [0xABCDEF0123456789],     True),
            (0xABCDEF0123456789, FIT.BASE_TYPE['UINT64'], [32],        [0x23456789],             False),
            (0xABCDEF0123456789, FIT.BASE_TYPE['UINT64'], [32, 32],    [0x23456789, 0xABCDEF01], False),
            (25,                 FIT.BASE_TYPE['SINT8'],  [8],         [25],                     True),
            (-56,                FIT.BASE_TYPE['SINT8'],  [8],         [200],                    True),
            (500,                FIT.BASE_TYPE['SINT16'], [16],        [500],                    True),
            (-1,                 FIT.BASE_TYPE['SINT16'], [16],        [0xFFFF],                 True),
            (0x3FC00000,         FIT.BASE_TYPE['FLOAT32'], [32],       [0x3FC00000],             True),
            (0x3FF8000000000000, FIT.BASE_TYPE['FLOAT64'], [64],       [0x3FF8000000000000],     True),
        ],
        ids=[
            "UInt8 0xAB - 8",
            "UInt8 0xAB - 4,4",
            "UInt8 0xAB - 4,1,1,1,1",
            "UInt16 0xAACB - 16",
            "UInt32 0xABCDEF01 - 16,16",
            "UInt32 0xABCDEF01 - 32",
            "UInt64 0x7BCDEF0123456789 - 64",
            "UInt64 0xABCDEF0123456789 - 64",
            "UInt64 0xABCDEF0123456789 - 32",
            "UInt64 0xABCDEF0123456789 - 32,32",
            "SInt8 25 - 8 positive value unchanged by mask",
            "SInt8 -56 (0xC8) - 8 fast path matches slow path unsigned bit pattern",
            "SInt16 500 - 16 positive value unchanged by mask",
            "SInt16 -1 (0xFFFF) - 16 fast path matches slow path unsigned bit pattern",
            "Float32 0x3FC00000 (1.5f) - 32 fast path uses bit mask",
            "Float64 0x3FF8000000000000 (1.5d) - 64 fast path uses bit mask",
        ],
    )
    def test_read_bits(self, data, base_type, bits_to_read, expected_values, takes_fast_path):
        bit_stream = BitStream(data, base_type)
        for i, expected in enumerate(expected_values):
            assert bit_stream.read_bits(bits_to_read[i]) == expected
        assert (bit_stream._array is None) == takes_fast_path


class TestExceptions:
    def test_read_bits_when_no_bits_available_raises_index_error(self):
        '''Tests that reading bits when none are available raises IndexError.'''
        bit_stream = BitStream(0xABCDEFFF, FIT.BASE_TYPE['UINT32'])
        bit_stream.read_bits(32)
        with pytest.raises(IndexError):
            bit_stream.read_bits(2)

    def test_read_bit_when_no_bits_available_raises_index_error(self):
        '''Tests that reading a bit when none are available raises IndexError.'''
        bit_stream = BitStream(0xAB, FIT.BASE_TYPE['UINT8'])
        bit_stream.read_bits(8)
        with pytest.raises(IndexError):
            bit_stream.read_bit()


class TestDeferredInit:
    '''Tests covering the deferred _array initialisation state machine in BitStream.'''

    def test_fast_path_multiple_elements_sequential(self):
        '''Fast path fires for each full-element read, leaving _array None between reads.'''
        bit_stream = BitStream([0x11, 0x22, 0x33], FIT.BASE_TYPE['UINT8'])
        assert bit_stream._array is None
        assert bit_stream.read_bits(8) == 0x11
        assert bit_stream._array is None
        assert bit_stream.bits_available() == 16
        assert bit_stream.read_bits(8) == 0x22
        assert bit_stream._array is None
        assert bit_stream.read_bits(8) == 0x33
        assert bit_stream.bits_available() == 0

    def test_slow_path_after_fast_path_initialises_array(self):
        '''A partial read after fast-path consumption triggers lazy _array init at the correct offset.'''
        bit_stream = BitStream([0xAB, 0xCD], FIT.BASE_TYPE['UINT8'])
        assert bit_stream.read_bits(8) == 0xAB
        assert bit_stream._array is None
        assert bit_stream.read_bits(4) == 0xD   # low nibble of 0xCD
        assert bit_stream._array is not None
        assert bit_stream.read_bits(4) == 0xC   # high nibble of 0xCD
        assert bit_stream.bits_available() == 0

    def test_read_bit_after_fast_path_initialises_array(self):
        '''read_bit() after fast-path consumption initialises _array lazily from the correct offset.'''
        bit_stream = BitStream([0xFF, 0x00], FIT.BASE_TYPE['UINT8'])
        assert bit_stream.read_bits(8) == 0xFF
        assert bit_stream._array is None
        assert bit_stream.read_bit() == 0
        assert bit_stream._array is not None
        for _ in range(7):
            assert bit_stream.read_bit() == 0
        assert bit_stream.bits_available() == 0

    def test_reset_restores_deferred_state(self):
        '''reset() restores _array to None, making the fast path available and bits_available correct.'''
        bit_stream = BitStream([0x12, 0x34], FIT.BASE_TYPE['UINT8'])
        bit_stream.read_bits(4)
        assert bit_stream._array is not None
        bit_stream.reset()
        assert bit_stream._array is None
        assert bit_stream.bits_available() == 16
        assert bit_stream.read_bits(8) == 0x12
        assert bit_stream.read_bits(8) == 0x34
