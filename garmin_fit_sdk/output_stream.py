'''output_stream.py: Contains the OutputStream class for writing binary FIT data.'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import struct
from io import BytesIO


class OutputStream:
    '''
    A class for writing binary data to an output stream for FIT file encoding.

    Attributes:
        _buffer: BytesIO buffer to hold the binary data.
    '''

    def __init__(self):
        self._buffer = BytesIO()

    @property
    def length(self) -> int:
        '''Returns the current length of the buffer.'''
        return self._buffer.tell()

    @property
    def bytes(self) -> bytes:
        '''Returns the buffer contents as bytes.'''
        return self._buffer.getvalue()

    @property
    def bytearray(self) -> bytearray:
        '''Returns the buffer contents as a bytearray.'''
        return bytearray(self._buffer.getvalue())

    def write_uint8(self, value: int) -> None:
        '''Writes an unsigned 8-bit integer to the stream.'''
        self._buffer.write(struct.pack('<B', value & 0xFF))

    def write_int8(self, value: int) -> None:
        '''Writes a signed 8-bit integer to the stream.'''
        self._buffer.write(struct.pack('<b', value & 0xFF))

    def write_uint16(self, value: int, little_endian: bool = True) -> None:
        '''Writes an unsigned 16-bit integer to the stream.'''
        fmt = '<H' if little_endian else '>H'
        self._buffer.write(struct.pack(fmt, value & 0xFFFF))

    def write_int16(self, value: int, little_endian: bool = True) -> None:
        '''Writes a signed 16-bit integer to the stream.'''
        fmt = '<h' if little_endian else '>h'
        self._buffer.write(struct.pack(fmt, value & 0xFFFF))

    def write_uint32(self, value: int, little_endian: bool = True) -> None:
        '''Writes an unsigned 32-bit integer to the stream.'''
        fmt = '<I' if little_endian else '>I'
        self._buffer.write(struct.pack(fmt, value & 0xFFFFFFFF))

    def write_int32(self, value: int, little_endian: bool = True) -> None:
        '''Writes a signed 32-bit integer to the stream.'''
        fmt = '<i' if little_endian else '>i'
        self._buffer.write(struct.pack(fmt, value & 0xFFFFFFFF))

    def write_uint64(self, value: int, little_endian: bool = True) -> None:
        '''Writes an unsigned 64-bit integer to the stream.'''
        fmt = '<Q' if little_endian else '>Q'
        self._buffer.write(struct.pack(fmt, value & 0xFFFFFFFFFFFFFFFF))

    def write_int64(self, value: int, little_endian: bool = True) -> None:
        '''Writes a signed 64-bit integer to the stream.'''
        fmt = '<q' if little_endian else '>q'
        self._buffer.write(struct.pack(fmt, value & 0xFFFFFFFFFFFFFFFF))

    def write_float32(self, value: float, little_endian: bool = True) -> None:
        '''Writes a 32-bit float to the stream.'''
        fmt = '<f' if little_endian else '>f'
        self._buffer.write(struct.pack(fmt, value))

    def write_float64(self, value: float, little_endian: bool = True) -> None:
        '''Writes a 64-bit float to the stream.'''
        fmt = '<d' if little_endian else '>d'
        self._buffer.write(struct.pack(fmt, value))

    def write_string(self, value: str, size: int) -> None:
        '''Writes a null-terminated string to the stream with specified size.'''
        if value is None:
            value = ''
        encoded = value.encode('utf-8')
        # Truncate if too long (leaving room for null terminator)
        if len(encoded) >= size:
            encoded = encoded[:size - 1]
        # Pad with null bytes to fill the size
        padded = encoded + b'\x00' * (size - len(encoded))
        self._buffer.write(padded)

    def write_bytes(self, data: bytes) -> None:
        '''Writes raw bytes to the stream.'''
        self._buffer.write(data)
    
    def write(self, values: list, base_type: int, little_endian: bool = True) -> None:
        '''Writes a list of values to the stream based on the base type.'''
        from . import fit as FIT
        
        base_type_def = FIT.BASE_TYPE_DEFINITIONS.get(base_type)
        if base_type_def is None:
            raise ValueError(f"Unknown base type: {base_type}")

        type_code = base_type_def['type']
        
        for value in values:
            if type_code == FIT.BASE_TYPE['ENUM'] or type_code == FIT.BASE_TYPE['UINT8'] or type_code == FIT.BASE_TYPE['UINT8Z'] or type_code == FIT.BASE_TYPE['BYTE']:
                self.write_uint8(value if value is not None else base_type_def['invalid'])
            elif type_code == FIT.BASE_TYPE['SINT8']:
                self.write_int8(value if value is not None else base_type_def['invalid'])
            elif type_code == FIT.BASE_TYPE['UINT16'] or type_code == FIT.BASE_TYPE['UINT16Z']:
                self.write_uint16(value if value is not None else base_type_def['invalid'], little_endian)
            elif type_code == FIT.BASE_TYPE['SINT16']:
                self.write_int16(value if value is not None else base_type_def['invalid'], little_endian)
            elif type_code == FIT.BASE_TYPE['UINT32'] or type_code == FIT.BASE_TYPE['UINT32Z']:
                self.write_uint32(value if value is not None else base_type_def['invalid'], little_endian)
            elif type_code == FIT.BASE_TYPE['SINT32']:
                self.write_int32(value if value is not None else base_type_def['invalid'], little_endian)
            elif type_code == FIT.BASE_TYPE['UINT64'] or type_code == FIT.BASE_TYPE['UINT64Z']:
                self.write_uint64(value if value is not None else base_type_def['invalid'], little_endian)
            elif type_code == FIT.BASE_TYPE['SINT64']:
                self.write_int64(value if value is not None else base_type_def['invalid'], little_endian)
            elif type_code == FIT.BASE_TYPE['FLOAT32']:
                self.write_float32(value if value is not None else float('nan'), little_endian)
            elif type_code == FIT.BASE_TYPE['FLOAT64']:
                self.write_float64(value if value is not None else float('nan'), little_endian)
            elif type_code == FIT.BASE_TYPE['STRING']:
                if isinstance(value, str):
                    self.write_bytes(value.encode('utf-8') + b'\x00')
                elif isinstance(value, bytes):
                    self.write_bytes(value + b'\x00')
                else:
                    self.write_uint8(0)  # Null terminator for invalid string
            else:
                raise ValueError(f"Unsupported base type: {type_code}")

    def set(self, data: bytes, position: int = 0) -> None:
        '''Sets bytes at a specific position in the buffer.'''
        current_pos = self._buffer.tell()
        self._buffer.seek(position)
        self._buffer.write(data)
        self._buffer.seek(current_pos)

    def reset(self) -> None:
        '''Resets the buffer.'''
        self._buffer = BytesIO()
