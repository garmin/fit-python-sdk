'''stream.py: Contains stream class which handles reading streams of data in the following ways:
    1. From a binary .fit file
    2. From a Python bytearray
    3. From a Python BytesIO object
    4. From a Python BufferedReader'''

###########################################################################################
# Copyright 2024 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################
# ****WARNING****  This file is auto-generated!  Do NOT edit this file.
# Profile Version = 21.141.0Release
# Tag = production/release/21.141.0-0-g2aa27e1
############################################################################################


import os
from enum import Enum
from io import BufferedReader, BytesIO
from struct import unpack


class Endianness(str, Enum):
    '''An enum class for denoting a bytes endinannes (LSB or MSB)'''
    LITTLE = "little"
    BIG = "big"


class Stream:
    '''
    A class that represents a stream of data from a .fit file.

    Attributes:
        _buffered_reader: The buffered reader that holds the stream data.
        _stream_length:   The calculated length of the stream.
        _crc_calculator:  The CRC calculator which calculates the CRC each time bytes are read.
    '''
    @staticmethod
    def from_file(filename):
        '''Creates a stream object from a given .fit file'''
        buffered_reader = open(filename, "rb")
        return Stream.from_buffered_reader(buffered_reader, os.path.getsize(filename))

    @staticmethod
    def from_byte_array(byte_array: bytearray, stream_length = None):
        '''Creates a stream object from a given byte array'''
        bytes_io = BytesIO(byte_array)
        if stream_length is None:
            stream_length = len(byte_array)

        return Stream.from_bytes_io(bytes_io, stream_length)

    @staticmethod
    def from_bytes_io(bytes_io: BytesIO, length = None):
        '''Creates a stream object from a given BytesIO object'''
        buffered_reader = BufferedReader(bytes_io)
        if length is None:
            length = bytes_io.getbuffer().nbytes

        return Stream.from_buffered_reader(buffered_reader, length)

    @staticmethod
    def from_buffered_reader(buffered_reader: BufferedReader, length = None):
        '''Creates a stream boject from a given BufferedReader object'''
        if length is None:
            length = Stream.__calc_stream_size(buffered_reader)

        stream = Stream(buffered_reader, length)
        return stream

    @staticmethod
    def __calc_stream_size(buffered_reader: BufferedReader):
        starting_position = buffered_reader.tell()
        buffered_reader.seek(0, os.SEEK_END)
        size = buffered_reader.tell()
        buffered_reader.seek(starting_position)
        return size

    def __init__(self, buffered_reader: BufferedReader, stream_length):
        self._buffered_reader = buffered_reader
        self._stream_length = stream_length

        self._crc_calculator = None

    def __del__(self):
        self.close()

    def __exit__(self, *_):
        self.close()

    def close(self):
        '''Closes the buffered reader in the stream.'''
        self._buffered_reader.close()

    def get_buffered_reader(self):
        '''Returns the buffered reader of the stream.'''
        return self._buffered_reader

    def peek_byte(self):
        '''Reads one byte from the stream without advancing stream position.'''
        return self._buffered_reader.peek(1)[0]

    def peek_bytes(self, num_bytes: int):
        '''Reads the given amount of bytes from the stream without advancing stream position '''
        return self._buffered_reader.peek(num_bytes)[0:num_bytes]

    def slice(self, start: int, end: int):
        '''Returns all of the bytes from the stream between the given start and end.'''
        starting_position = self.position()
        self.seek(start)
        slice = self.peek_bytes(end - start)[0: end - start]
        self.seek(starting_position)
        return slice

    def seek(self, position: int):
        '''Moves the stream position of stream to the given position.'''
        self._buffered_reader.seek(position)

    def read_byte(self):
        '''Reads one byte from the stream.'''
        if self.position() > self._stream_length - 1:
            raise IndexError("FIT Runtime Error, end of file reached at byte pos: " + self.position())
        return self.read_bytes(1)[0]

    def read_bytes(self, num_bytes: int):
        '''Reads the given amount of bytes from the stream.'''
        if num_bytes > (self._stream_length - self.position()):
            raise IndexError("FIT Runtime Error number of bytes provided is longer than the number of bytes remaining")

        read_bytes = self._buffered_reader.read(num_bytes)[0:num_bytes]

        if self._crc_calculator is not None:
            self._crc_calculator.add_bytes(read_bytes, 0, num_bytes)

        return read_bytes

    def read_unint_16(self, endianness: Endianness = Endianness.LITTLE):
        '''Reads a 16-bit unsigned integer from the stream with the given endianness'''
        return int.from_bytes(self.read_bytes(2), endianness)

    def read_unint_32(self, endianness: Endianness = Endianness.LITTLE):
        '''Reads a 32-bit unsigned integer from the stream with the given endianness'''
        return int.from_bytes(self.read_bytes(4), endianness)

    def read_string(self, string_length):
        '''Reads a string from the stream with the given string length'''
        struct_string = "=" + str(string_length) + "s"
        return self.read_and_unpack(string_length, struct_string)

    def reset(self):
        '''Resets the stream position to the beginning of the stream.'''
        self._buffered_reader.seek(0)

    def position(self):
        '''Returns the current position in the stream.'''
        return self._buffered_reader.tell()

    def get_length(self):
        '''Returns the total length of the stream.'''
        return self._stream_length

    def read_and_unpack(self, size: int, struct_format_string):
        '''Reads a given number of bytes and unpacks the binary struct given a formatting string template'''
        byte_array = self.read_bytes(size)

        values = list(unpack(struct_format_string, byte_array))

        return values

    def get_crc_caclulator(self):
        '''Returns the CRC calculator'''
        return self._crc_calculator

    def set_crc_calculator(self, crc_calculator):
        '''Sets the CRC calculator'''
        self._crc_calculator = crc_calculator
