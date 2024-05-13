'''crc_calculator.py: Contains the CRC class which is used for calculating the header and file data CRCs.'''

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


_CRC_TABLE = [
    0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
    0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400
]


class CrcCalculator:
    '''A class for calculating the CRC of a given .fit file header or file contents.'''

    def __init__(self) -> None:
        self._crc = 0
        self._bytes_seen = 0

    def get_crc(self):
        '''Returns the calculated CRC value.'''
        return self._crc

    def __update_crc(self, value):
        # compute checksum of lower four bits of byte
        temp = _CRC_TABLE[self._crc & 0xF]
        self._crc = (self._crc >> 4) & 0x0FFF
        self._crc = self._crc ^ temp ^ _CRC_TABLE[value & 0xF]

        # compute checksum of upper four bits of byte
        temp = _CRC_TABLE[self._crc & 0xF]
        self._crc = (self._crc >> 4) & 0x0FFF
        self._crc = self._crc ^ temp ^ _CRC_TABLE[(value >> 4) & 0xF]

        return self._crc

    def add_bytes(self, buffer, start, end):
        '''Adds another chunk of bytes for calculating the CRC.'''
        for i in range(start, end):
            self._crc = self.__update_crc(buffer[i])
            self._bytes_seen += 1

        return self._crc

    @staticmethod
    def calculate_crc(buffer, start: int, end: int):
        '''Calculates the CRC of a given buffer from the given starting index to the ending index.'''
        crc_calculator = CrcCalculator()
        return crc_calculator.add_bytes(buffer, start, end)
