'''bitstream.py: Contains BitStream class which handles reading streams of data bit by bit '''

###########################################################################################
# Copyright 2022 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################
# ****WARNING****  This file is auto-generated!  Do NOT edit this file.
# Profile Version = 21.94Release
# Tag = production/akw/21.94.00-0-g0f668193
############################################################################################


from . import fit as FIT


class BitStream:
    '''
    A class that represents a stream of binary data from a chunk of data.

    Attributes:
        _array: The stream of data in an array structure.
        _current_array_position:   Current position in data array.
        _bits_per_position: Number of bits per step through the data.
        _current_byte: Position of the current byte being read in the data.
        _current_bit: Position of the current bit being read in the data.
        _bits_available: Remaining number of bits left unread in the data.
    '''
    def __init__(self, data, base_type):
        self._array = None
        self._current_array_position = 0
        self._bits_per_position = 0
        self._current_byte = 0
        self._current_bit = 0
        self._bits_available = 0

        self._array = data if isinstance(data, list) else [data]
        base_type_size = FIT.BASE_TYPE_DEFINITIONS[base_type]['size']
        self._bits_per_position = base_type_size * 8
        self.reset()

    def bits_available(self):
        '''Returns the number of bits left in the data.'''
        return self._bits_available

    def has_bits_available(self):
        '''Returns true if the data has bits available.'''
        return self._bits_available > 0

    def reset(self):
        '''Resets the bitstream to the start of the data and resets the bits available.'''
        self._current_array_position = 0
        self._bits_available = self._bits_per_position * len(self._array)
        self.__next_byte()

    def read_bit(self):
        '''Reads the next bit if possible.'''
        if self.has_bits_available() is False:
            self.__raise_error()

        if self._current_bit >= self._bits_per_position:
            self.__next_byte()

        bit = self._current_byte & 0x01
        self._current_byte = (self._current_byte >> 1)
        self._current_bit += 1
        self._bits_available -= 1

        return bit

    def read_bits(self, number_bits_to_read):
        '''Reads the specificed number of bits if possible.'''
        value = 0

        for i in range(number_bits_to_read):
            value |= self.read_bit() << i

        return value

    def __next_byte(self):
        if self._current_array_position >= len(self._array):
            self.__raise_error()

        self._current_byte = self._array[self._current_array_position]
        self._current_array_position += 1
        self._current_bit = 0

    def __raise_error(self):
        raise IndexError('FIT Runtime Error, no bits available.')
