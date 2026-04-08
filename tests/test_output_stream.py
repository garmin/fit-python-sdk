'''test_output_stream.py: Contains the set of tests for the _OutputStream class.'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import pytest
from garmin_fit_sdk import fit as FIT
from garmin_fit_sdk.output_stream import _OutputStream


class TestOutputStreamBasic:
    '''Basic OutputStream tests.'''

    def test_new_output_stream_has_length_zero(self):
        stream = _OutputStream()
        assert stream.length == 0

    def test_set_bytes(self):
        stream = _OutputStream()
        stream.write_values([0x00, 0x00], FIT.BASE_TYPE['UINT8'])
        stream.set_bytes(bytes([0xAA, 0xBB]), 0)
        assert stream.data == bytes([0xAA, 0xBB])

    def test_set_bytes_with_offset(self):
        stream = _OutputStream()
        stream.write_values([0x00, 0x00, 0x00], FIT.BASE_TYPE['UINT8'])
        stream.set_bytes(bytes([0x01, 0x02]), 1)
        assert stream.data == bytes([0x00, 0x01, 0x02])

    def test_set_bytes_pads_zeros_before_offset(self):
        stream = _OutputStream()
        stream.set_bytes(bytes([0, 1, 2, 3]), 1)
        assert list(stream.data) == [0, 0, 1, 2, 3]


# MARK: Write Single Values

@pytest.mark.parametrize('method,value,expected_length', [
    ('write_byte',    1,                    1),
    ('write_uint8',   1,                    1),
    ('write_uint16',  1,                    2),
    ('write_uint32',  1,                    4),
    ('write_uint64',  0x0807060504030201,   8),
    ('write_uint8z',  1,                    1),
    ('write_uint16z', 1,                    2),
    ('write_uint32z', 1,                    4),
    ('write_uint64z', 0x0807060504030201,   8),
    ('write_sint8',   1,                    1),
    ('write_sint16',  1,                    2),
    ('write_sint32',  1,                    4),
    ('write_sint64',  0x0807060504030201,   8),
    ('write_float32', 1234.5678,            4),
    ('write_float64', 1234.5678,            8),
    ('write_enum',    1,                    1),
])
class TestOutputStreamWriteSingleValues:
    '''Tests for writing single values to an OutputStream using typed write methods.'''

    def test_write_single_value_length(self, method, value, expected_length):
        stream = _OutputStream()
        getattr(stream, method)(value)
        assert stream.length == expected_length


# MARK: Write Array Values

@pytest.mark.parametrize('method,expected_length', [
    ('write_byte',    4),
    ('write_uint8',   4),
    ('write_uint16',  8),
    ('write_uint32',  16),
    ('write_uint64',  32),
    ('write_uint8z',  4),
    ('write_uint16z', 8),
    ('write_uint32z', 16),
    ('write_uint64z', 32),
    ('write_sint8',   4),
    ('write_sint16',  8),
    ('write_sint32',  16),
    ('write_sint64',  32),
    ('write_float32', 16),
    ('write_float64', 32),
])
class TestOutputStreamWriteArrayValues:
    '''Tests for writing arrays of values to an OutputStream using typed write methods.'''

    def test_write_array_length(self, method, expected_length):
        stream = _OutputStream()
        getattr(stream, method)([0, 1, 2, 3])
        assert stream.length == expected_length


# MARK: Write Value by Base Type

class TestOutputStreamWriteValueByBaseType:
    '''Tests for writing single values via write_value with each base type.'''

    @pytest.mark.parametrize('base_type,value,expected_length', [
        (FIT.BASE_TYPE['UINT8'],   1,   1),
        (FIT.BASE_TYPE['SINT8'],   1,   1),
        (FIT.BASE_TYPE['UINT16'],  1,   2),
        (FIT.BASE_TYPE['SINT16'],  1,   2),
        (FIT.BASE_TYPE['UINT32'],  1,   4),
        (FIT.BASE_TYPE['SINT32'],  1,   4),
        (FIT.BASE_TYPE['UINT64'],  1,   8),
        (FIT.BASE_TYPE['SINT64'],  1,   8),
        (FIT.BASE_TYPE['FLOAT32'], 1.0, 4),
        (FIT.BASE_TYPE['FLOAT64'], 1.0, 8),
    ])
    def test_write_value_length(self, base_type, value, expected_length):
        stream = _OutputStream()
        stream.write_value(value, base_type)
        assert stream.length == expected_length

    def test_write_value_unsupported_base_type_raises(self):
        stream = _OutputStream()
        with pytest.raises(ValueError):
            stream.write_value(1, 0xFF)

    def test_write_values_length(self):
        stream = _OutputStream()
        stream.write_values([0, 1, 2, 3], FIT.BASE_TYPE['UINT8'])
        assert stream.length == 4


# MARK: Write Endianness

class TestOutputStreamWriteEndianness:
    '''Tests for correct little-endian byte ordering.'''

    def test_uint16_little_endian(self):
        stream = _OutputStream()
        stream.write_uint16(0x1234)
        assert stream.data == bytes([0x34, 0x12])

    def test_uint32_little_endian(self):
        stream = _OutputStream()
        stream.write_uint32(0x12345678)
        assert stream.data == bytes([0x78, 0x56, 0x34, 0x12])

    def test_uint32_value_little_endian(self):
        stream = _OutputStream()
        stream.write_value(0x03020100, FIT.BASE_TYPE['UINT32'])
        assert list(stream.data) == [0x00, 0x01, 0x02, 0x03]


# MARK: Write Strings

class TestOutputStreamWriteStrings:
    '''Tests for writing strings to an OutputStream.'''

    def test_write_string_appends_null_terminator(self):
        stream = _OutputStream()
        stream.write_string('.FIT')
        assert stream.length == 5
        assert stream.data[4] == 0x00

    def test_write_string_list(self):
        stream = _OutputStream()
        stream.write_string(['.FIT', '.FIT'])
        assert stream.length == 10
        assert stream.data[4] == 0x00
        assert stream.data[9] == 0x00

    def test_write_string_content(self):
        stream = _OutputStream()
        stream.write_string('abc')
        assert stream.data == b'abc\x00'

    def test_write_string_via_write_method(self):
        stream = _OutputStream()
        stream.write('abc', FIT.BASE_TYPE['STRING'])
        assert stream.data == b'abc\x00'


# MARK: Write Invalid

class TestOutputStreamWriteInvalid:
    '''Tests for writing invalid/None values.'''

    def test_write_value_none_uses_invalid_marker(self):
        stream = _OutputStream()
        stream.write_value(None, FIT.BASE_TYPE['UINT8'])
        assert stream.data == bytes([0xFF])

    def test_write_value_none_uint16_uses_invalid_marker(self):
        stream = _OutputStream()
        stream.write_value(None, FIT.BASE_TYPE['UINT16'])
        assert stream.data == bytes([0xFF, 0xFF])

    def test_write_value_none_uint32_uses_invalid_marker(self):
        stream = _OutputStream()
        stream.write_value(None, FIT.BASE_TYPE['UINT32'])
        assert stream.data == bytes([0xFF, 0xFF, 0xFF, 0xFF])

    def test_write_value_overflow_signed_truncates(self):
        stream = _OutputStream()
        stream.write_sint8(0xFF)  # 0xFF masked to 8 bits = 255 → signed → -1
        assert stream.data == bytes([0xFF])
