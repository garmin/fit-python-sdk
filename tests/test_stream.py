'''test_stream.py: Contains the set of tests for the Stream class in the Python FIT SDK'''

###########################################################################################
# Copyright 2022 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import io

import pytest
from garmin_fit_sdk import Stream, util


def test_stream_from_buffered_reader():
    '''Tests creating a stream from a buffered reader object'''
    buffered_reader = io.BufferedReader(
        io.BytesIO(bytearray([0x0E, 0x20, 0x8B])))
    stream = Stream.from_buffered_reader(buffered_reader)
    assert stream.get_buffered_reader() is not None
    assert stream.peek_byte() == 0x0E

def test_stream_from_bytes_io():
    '''Tests creating a stream from a BytesIO object'''
    bytes_io = io.BytesIO(bytearray([0x0E, 0x20, 0x8B]))
    stream = Stream.from_bytes_io(bytes_io)
    assert stream.get_buffered_reader() is not None
    assert stream.peek_byte() == 0x0E

def test_stream_from_byte_array():
    '''Tests creating a stream from a bytearray object'''
    byte_array = bytearray([0x0E, 0x20, 0x8B])
    stream = Stream.from_byte_array(byte_array)
    assert stream.get_buffered_reader() is not None
    assert stream.peek_byte() == 0x0E

def test_stream_from_file():
    '''Tests creating a stream from a binary fit file'''
    stream = Stream.from_file("tests/fits/ActivityDevFields.fit")
    assert stream.get_buffered_reader() is not None
    assert stream.peek_byte() == 0x0E


@pytest.mark.parametrize(
    "given_bytes,position,expected_value",
    [
        (bytearray([0x0E, 0x20, 0x8B]), 0, 0x0E),
        (bytearray([0x0E, 0x20, 0x8B]), 1, 0x20),
        (bytearray([0x0E, 0x20, 0x8B]), 2, 0x8B),
    ],
)
class TestParametrizedByByte:
    '''Group of tests for testing read and peek by byte'''
    def test_peek_byte(self, given_bytes, position, expected_value):
        '''Tests peeking a single byte from the stream and returning its value'''
        stream = Stream.from_byte_array(given_bytes)
        stream.seek(position)
        assert stream.peek_byte() == expected_value
        assert stream.peek_byte() == stream.read_byte()

    def test_read_byte(self, given_bytes, position, expected_value):
        '''Tests reading a single byte from the stream and returning its value'''
        stream = Stream.from_byte_array(given_bytes)
        stream.seek(position)
        assert stream.read_byte() == expected_value
        stream.seek(position)
        assert stream.peek_byte() == stream.read_byte()


@pytest.mark.parametrize(
    "given_bytes,num_bytes,expected_value",
    [
        (bytearray([0x0E, 0x20, 0x8B]), 0, bytearray([])),
        (bytearray([0x0E, 0x20, 0x8B]), 1, bytearray([0x0E])),
        (bytearray([0x0E, 0x20, 0x8B]), 2, bytearray([0x0E, 0x20])),
        (bytearray([0x0E, 0x20, 0x8B]), 3, bytearray([0x0E, 0x20, 0x8B])),
    ],
)
class TestParametrizedByBytes:
    '''Set of tests for verifying reads and peeks greater than one byte'''
    def test_peek_bytes(self, given_bytes, num_bytes, expected_value):
        '''Tests peeking a number of bytes from a stream'''
        stream = Stream.from_byte_array(given_bytes)
        assert stream.peek_bytes(num_bytes) == expected_value
        assert stream.peek_bytes(num_bytes) == stream.read_bytes(num_bytes)

    def test_read_bytes(self, given_bytes, num_bytes, expected_value):
        '''Tests peeking a number of bytes from a stream'''
        stream = Stream.from_byte_array(given_bytes)
        assert stream.read_bytes(num_bytes) == expected_value
        stream.reset()
        assert stream.peek_bytes(num_bytes) == stream.read_bytes(num_bytes)


@pytest.mark.parametrize(
    "given_bytes,start,end,expected_value",
    [
        (bytearray([0x0E, 0x20, 0x8B]), 0, 1, bytearray([0x0E])),
        (bytearray([0x0E, 0x20, 0x8B]), 1, 2, bytearray([0x20])),
        (bytearray([0x0E, 0x20, 0x8B]), 0, 2, bytearray([0x0E, 0x20])),
        (bytearray([0x0E, 0x20, 0x8B]), 0, 3, bytearray([0x0E, 0x20, 0x8B])),
    ],
)
def test_slice(given_bytes, start, end, expected_value):
    '''Tests taking an array values from the stream from the start index to the end'''
    stream = Stream.from_byte_array(given_bytes)
    starting_position = stream.position()
    assert stream.slice(start, end) == expected_value
    assert stream.position() == starting_position


class TestReadValues:
    '''Set of tests which validate correct reading of numeric values and strings from the stream.'''
    @pytest.mark.parametrize(
        "given_bytes",
        [
        (bytearray([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])),
        ],
    )
    class TestInts:
        '''Set of tests which verify decoding of int values from a fit file.'''
        def test_read_unint8(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=8B' )
            assert values == [255, 255, 255, 255, 255, 255, 255, 255]

        def test_read_sint8(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=8b' )
            assert values == [-1, -1, -1, -1, -1, -1, -1, -1]

        def test_read_unint16(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=4H' )
            assert values == [65535, 65535, 65535, 65535]

        def test_read_sint16(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=4h' )
            assert values == [-1, -1, -1, -1]

        def test_read_uint32(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=2I' )
            assert values == [4294967295, 4294967295]

        def test_read_sint32(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=2i' )
            assert values == [-1, -1]

        def test_read_uint64(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=Q' )
            assert values == [18446744073709551615]
        def test_read_sint64(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=q' )
            assert values == [-1]


    @pytest.mark.parametrize(
        "given_bytes",
        [
        (bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0x3F])),
        ],
    )
    class TestFloats:
        '''Set of tests which verify decoding of float values from a fit file.'''
        def test_read_float_32(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=2f' )
            assert values == [0.0, 1.875]

        def test_read_double_64(self, given_bytes):
            stream = Stream.from_byte_array(given_bytes)
            values = stream.read_and_unpack(stream.get_length(), '=d' )
            assert values == [1]


    class TestStrings:
        '''Set of tests which verify decoding of strings from a fit file.'''
        @pytest.mark.parametrize(
        "given_bytes,expected_value",
        [
            (bytearray([0x2E, 0x46, 0x49, 0x54]), ".FIT"),
            (bytearray([0x2E, 0x46, 0x49, 0x54, 0x00, 0x00]), ".FIT"),
            (bytearray([0xe8, 0xbf, 0x99, 0xe5, 0xa5, 0x97, 0xe5, 0x8a, 0xa8, 0xe4, 0xbd,
                        0x9c, 0xe7, 0x94, 0xb1, 0xe4, 0xb8, 0xa4, 0xe7, 0xbb, 0x84]), "这套动作由两组"),
            (bytearray([0xe8, 0xbf, 0x99, 0xe5, 0xa5, 0x97, 0xe5, 0x8a, 0xa8, 0xe4, 0xbd,
                        0x9c, 0xe7, 0x94, 0xb1, 0xe4, 0xb8, 0xa4, 0xe7, 0xbb, 0x84, 0x00]), "这套动作由两组"),
        ], ids=["Regular String", "String w/ Null Terminator", "Multibyte String w/o Null Terminator", "Multibyte String w/ Null Terminator"],
        )
        def test_read_string(self, given_bytes, expected_value):
            '''Tests reading any given string from the stream.'''
            stream = Stream.from_byte_array(given_bytes)
            value = stream.read_string(stream.get_length())
            assert util._convert_string(value[0]) == expected_value

        def test_read_string_array(self):
            '''Tests reading an array of strings from the stream.'''
            stream = Stream.from_byte_array(bytearray([0x2E, 0x46, 0x49, 0x54, 0x00, 0x2E, 0x46, 0x49, 0x54, 0x00]))
            string = stream.read_string(stream.get_length())
            strings = util._convert_string(string[0])
            for string in strings:
                assert string == '.FIT'

    def test_read_string_bad_utf8_characters(self):
        '''Tests correctly reading bad utf8 characters after decoding from the stream.'''
        stream = Stream.from_byte_array(bytearray([
            0x37, 0x35, 0x25, 0x20, 0x65, 0x66, 0x66, 0x6F, 0x72, 0x74, 0x2E, 0x00, 0x65, 0x66, 0x66, 0x6F,
            0x72, 0x74, 0x2E, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF,
            0x75, 0x6E, 0x00, 0x01, 0x00, 0x00, 0x00, 0x20, 0x00, 0x03, 0x40, 0x00, 0x01, 0x00, 0x1B, 0x07,
            0xFE, 0x02, 0x84, 0x07, 0x01, 0x00, 0x03, 0x01, 0x00, 0x04, 0x04, 0x86, 0x01, 0x01,
            0x00, 0x02, 0x04, 0x86, 0x08, 0x0C, 0x07, 0x00, 0x00, 0x00, 0x02, 0x02, 0x00, 0x00, 0x00, 0x00,
            0x01, 0x00, 0x01, 0xD7, 0x7C, 0x37, 0x35, 0x25, 0x20, 0x65, 0x66, 0x66, 0x6F, 0x72, 0x74, 0x2E,
            0x00, 0x40, 0x00, 0x01, 0x00, 0x1B, 0x0B, 0xFE, 0x02, 0x84, 0x07, 0x01, 0x00, 0x03, 0x01,
            0x00, 0x05, 0x04, 0x86, 0x06, 0x04, 0x86, 0x04, 0x04, 0x86, 0x01, 0x01, 0x00, 0x02,
            0x04, 0x86, 0x08, 0x10, 0x07, 0x0A, 0x02, 0x84, 0x0B, 0x02, 0x84, 0x00, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x08, 0xEB, 0x00, 0x03, 0x7B, 0xD7, 0x00, 0x00, 0x00, 0x00, 0x01,
            0x00, 0x03, 0xAE, 0xF8, 0x52, 0x61, 0x63, 0x65, 0x20, 0x67, 0x6F, 0x61, 0x6C, 0x20, 0x70,
            0x61, 0x63, 0x65, 0x2E, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x02, 0x03, 0x02, 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00,
            0x00, 0x00, 0x01, 0x00, 0x01, 0xD7, 0x7C, 0x37, 0x35, 0x25, 0x20, 0x65, 0x66]))
        string = stream.read_string(stream.get_length())
        strings = util._convert_string(string[0])
        assert len(strings) == 54
        assert strings[0] == "75% effort."
        assert strings[6] == "un" # Not '����un'
        assert strings[13] == "" # Not '��'
        assert strings[42] == "Race goal pace." # Not '��Race goal pace.'
        assert strings[53] == "|75% ef" # Not '�|75% ef'
