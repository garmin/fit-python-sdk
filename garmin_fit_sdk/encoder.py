'''encoder.py: Contains the Encoder class for encoding FIT files.'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import fit as FIT
from .crc_calculator import CrcCalculator
from .mesg_definition import MesgDefinition
from .output_stream import OutputStream
from .profile import Profile
from .util import FIT_EPOCH_S


_HEADER_WITH_CRC_SIZE = 14
_HEADER_WITHOUT_CRC_SIZE = 12
_LOCAL_MESG_NUM_MASK = 0x0F
_FIELD_DEFAULT_SCALE = 1
_FIELD_DEFAULT_OFFSET = 0


class Encoder:
    '''
    A class for encoding FIT files.
    
    The Encoder takes message data and writes it to a binary FIT file format.
    
    Usage:
        encoder = Encoder()
        encoder.write_message(mesg_num, message_data)
        fit_bytes = encoder.close()
    
    Attributes:
        _output_stream: The output stream for writing binary data.
        _local_mesg_definitions: Array of 16 local message definitions.
        _next_local_mesg_num: The next local message number to use.
        _field_descriptions: Developer field descriptions.
    '''

    def __init__(self, field_descriptions: Optional[Dict] = None):
        '''
        Creates a FIT File Encoder.
        
        Args:
            field_descriptions: Optional dictionary of developer field descriptions.
        '''
        self._output_stream = OutputStream()
        self._local_mesg_definitions: List[Optional[MesgDefinition]] = [None] * 16
        self._next_local_mesg_num = 0
        self._field_descriptions: Dict = {}

        if field_descriptions:
            for key, desc in field_descriptions.items():
                self.add_developer_field(
                    key,
                    desc.get('developer_data_id_mesg', {}),
                    desc.get('field_description_mesg', {})
                )

        self._write_empty_file_header()

    def close(self) -> bytes:
        '''
        Closes the encoder and returns the file data.
        
        Returns:
            bytes: The complete FIT file data.
        '''
        self._update_file_header()
        self._write_file_crc()
        return self._output_stream.bytes

    def write_message(self, mesg: Dict[str, Any]) -> 'Encoder':
        '''
        Encodes a message into the file.
        
        Args:
            mesg: The message data with 'mesg_num' key.
            
        Returns:
            self for method chaining.
        '''
        mesg_num = mesg.get('mesg_num')
        if mesg_num is None:
            raise ValueError("Message must contain 'mesg_num' field")
        return self.on_mesg(mesg_num, mesg)

    def write_mesg(self, mesg: Dict[str, Any]) -> 'Encoder':
        '''Alias for write_message for compatibility with JS SDK.'''
        return self.write_message(mesg)

    def on_mesg(self, mesg_num: int, mesg: Dict[str, Any]) -> 'Encoder':
        '''
        Encodes a message into the file.
        
        This method can be used as a Decoder mesg_listener callback.
        
        Args:
            mesg_num: The message number for this message.
            mesg: The message data dictionary.
            
        Returns:
            self for method chaining.
        '''
        try:
            mesg_definition = self._create_mesg_definition(mesg_num, mesg)
            self._write_mesg_definition_if_not_active(mesg_definition)

            self._output_stream.write_uint8(mesg_definition.local_mesg_num)

            for field_def in mesg_definition.field_definitions:
                values = self._transform_values(mesg.get(field_def.name), field_def)
                self._write_field_values(values, field_def)

            developer_fields = mesg.get('developer_fields', {})
            for dev_field_def in mesg_definition.developer_field_definitions:
                value = developer_fields.get(dev_field_def.key)
                values = self._transform_values(value, dev_field_def)
                self._write_field_values(values, dev_field_def)

        except Exception as error:
            raise RuntimeError(f"Could not write message: {mesg}") from error

        return self

    def add_developer_field(self, key: str, developer_data_id_mesg: Dict, 
                           field_description_mesg: Dict) -> 'Encoder':
        '''
        Adds a Developer Data Field Description and associated Developer Data Id Message.
        
        This provides the Encoder with the context required to write Developer Fields.
        Note: This method does not write the messages to the output-stream.
        
        Args:
            key: The unique key for this developer field.
            developer_data_id_mesg: The Developer Data Id message.
            field_description_mesg: The Field Description message.
            
        Returns:
            self for method chaining.
        '''
        dev_data_index_1 = developer_data_id_mesg.get('developer_data_index')
        dev_data_index_2 = field_description_mesg.get('developer_data_index')

        # Handle both raw and processed message formats
        if isinstance(dev_data_index_1, dict):
            dev_data_index_1 = dev_data_index_1.get('raw_field_value')
        if isinstance(dev_data_index_2, dict):
            dev_data_index_2 = dev_data_index_2.get('raw_field_value')

        if dev_data_index_1 is None or dev_data_index_2 is None:
            raise ValueError(
                f"add_developer_field() - one or more developer_data_index values are None. "
                f"key={key}, dev_data_id={developer_data_id_mesg}, field_desc={field_description_mesg}"
            )

        if dev_data_index_1 != dev_data_index_2:
            raise ValueError(
                f"add_developer_field() - developer_data_index values do not match. "
                f"key={key}, index1={dev_data_index_1}, index2={dev_data_index_2}"
            )

        self._field_descriptions[key] = {
            'developer_data_id_mesg': developer_data_id_mesg,
            'field_description_mesg': field_description_mesg
        }

        return self

    def _write_empty_file_header(self) -> None:
        '''Writes an empty file header placeholder.'''
        for _ in range(_HEADER_WITH_CRC_SIZE):
            self._output_stream.write_uint8(0)

    def _update_file_header(self) -> None:
        '''Updates the file header with correct values.'''
        header = bytearray(_HEADER_WITH_CRC_SIZE)
        
        # Header size
        header[0] = _HEADER_WITH_CRC_SIZE
        
        # Protocol version (2.0)
        header[1] = 0x20
        
        # Profile version
        profile_version = Profile['version']['major'] * 1000 + Profile['version']['minor']
        header[2] = profile_version & 0xFF
        header[3] = (profile_version >> 8) & 0xFF
        
        # Data size (little endian)
        data_size = self._output_stream.length - _HEADER_WITH_CRC_SIZE
        header[4] = data_size & 0xFF
        header[5] = (data_size >> 8) & 0xFF
        header[6] = (data_size >> 16) & 0xFF
        header[7] = (data_size >> 24) & 0xFF
        
        # Data type ".FIT"
        header[8] = 0x2E  # '.'
        header[9] = 0x46  # 'F'
        header[10] = 0x49  # 'I'
        header[11] = 0x54  # 'T'
        
        # Header CRC
        crc = CrcCalculator.calculate_crc(header, 0, _HEADER_WITHOUT_CRC_SIZE)
        header[12] = crc & 0xFF
        header[13] = (crc >> 8) & 0xFF
        
        self._output_stream.set(bytes(header), 0)

    def _write_file_crc(self) -> None:
        '''Writes the file CRC at the end of the file.'''
        crc = CrcCalculator.calculate_crc(self._output_stream.bytes, 0, self._output_stream.length)
        self._output_stream.write_uint16(crc)

    def _transform_values(self, value: Any, field_def) -> List[Any]:
        '''Transforms a value or list of values for encoding.'''
        if value is None:
            return [self._get_invalid_value(field_def)]
        
        values = value if isinstance(value, list) else [value]
        return [self._transform_value(v, field_def) for v in values]

    def _transform_value(self, value: Any, field_def) -> Any:
        '''Transforms a single value for encoding.'''
        try:
            if value is None:
                return self._get_invalid_value(field_def)

            field_type = getattr(field_def, 'type', 'uint8')
            base_type = getattr(field_def, 'base_type', FIT.BASE_TYPE['UINT8'])
            scale = getattr(field_def, 'scale', _FIELD_DEFAULT_SCALE)
            offset = getattr(field_def, 'offset', _FIELD_DEFAULT_OFFSET)

            # Handle numeric fields
            if field_type in FIT.NUMERIC_FIELD_TYPES:
                if not self._is_numeric(value):
                    return self._get_invalid_value(field_def)
                
                # Convert string numbers
                if isinstance(value, str):
                    try:
                        value = float(value) if '.' in value else int(value)
                    except ValueError:
                        return self._get_invalid_value(field_def)

                # Apply scale and offset (unapply for encoding)
                has_scale_or_offset = scale != _FIELD_DEFAULT_SCALE or offset != _FIELD_DEFAULT_OFFSET
                if has_scale_or_offset:
                    scaled_value = (value + offset) * scale
                    if field_type in ('float32', 'float64'):
                        return scaled_value
                    return int(round(scaled_value))

                return value

            # Handle date_time fields
            if field_type == 'date_time':
                if isinstance(value, datetime):
                    return self._convert_datetime_to_fit(value)
                if self._is_numeric(value):
                    return int(value)
                return self._get_invalid_value(field_def)

            # Handle string fields
            if field_type == 'string' or base_type == FIT.BASE_TYPE['STRING']:
                if isinstance(value, str):
                    return value
                return str(value) if value is not None else ''

            # Handle enum/type fields
            if self._is_numeric(value):
                return int(value) if isinstance(value, float) else value

            # Try to look up string value in profile types
            profile_types = Profile.get('types', {})
            if field_type in profile_types:
                type_values = profile_types[field_type]
                # Reverse lookup: find key by value
                for key, type_value in type_values.items():
                    if type_value == value:
                        return int(key)

            return self._get_invalid_value(field_def)

        except Exception:
            return self._get_invalid_value(field_def)

    def _get_invalid_value(self, field_def) -> Any:
        '''Gets the invalid value for a field's base type.'''
        base_type = getattr(field_def, 'base_type', FIT.BASE_TYPE['UINT8'])
        base_type_def = FIT.BASE_TYPE_DEFINITIONS.get(base_type, {})
        return base_type_def.get('invalid', 0xFF)

    def _is_numeric(self, value: Any) -> bool:
        '''Checks if a value is numeric.'''
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return False

    def _convert_datetime_to_fit(self, dt: datetime) -> int:
        '''Converts a Python datetime to FIT timestamp.'''
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        timestamp = int(dt.timestamp())
        return timestamp - FIT_EPOCH_S

    def _write_field_values(self, values: List[Any], field_def) -> None:
        '''Writes field values to the output stream.'''
        base_type = getattr(field_def, 'base_type', FIT.BASE_TYPE['UINT8'])
        base_type_def = FIT.BASE_TYPE_DEFINITIONS.get(base_type, {})
        type_code = base_type_def.get('type', FIT.BASE_TYPE['UINT8'])
        
        for value in values:
            if type_code == FIT.BASE_TYPE['STRING']:
                if isinstance(value, str):
                    encoded = value.encode('utf-8') + b'\x00'
                    self._output_stream.write_bytes(encoded)
                elif isinstance(value, bytes):
                    self._output_stream.write_bytes(value + b'\x00')
                else:
                    self._output_stream.write_uint8(0)
            elif type_code == FIT.BASE_TYPE['SINT8']:
                self._output_stream.write_int8(value if value is not None else base_type_def['invalid'])
            elif type_code in (FIT.BASE_TYPE['ENUM'], FIT.BASE_TYPE['UINT8'], 
                              FIT.BASE_TYPE['UINT8Z'], FIT.BASE_TYPE['BYTE']):
                self._output_stream.write_uint8(value if value is not None else base_type_def['invalid'])
            elif type_code == FIT.BASE_TYPE['SINT16']:
                self._output_stream.write_int16(value if value is not None else base_type_def['invalid'])
            elif type_code in (FIT.BASE_TYPE['UINT16'], FIT.BASE_TYPE['UINT16Z']):
                self._output_stream.write_uint16(value if value is not None else base_type_def['invalid'])
            elif type_code == FIT.BASE_TYPE['SINT32']:
                self._output_stream.write_int32(value if value is not None else base_type_def['invalid'])
            elif type_code in (FIT.BASE_TYPE['UINT32'], FIT.BASE_TYPE['UINT32Z']):
                self._output_stream.write_uint32(value if value is not None else base_type_def['invalid'])
            elif type_code == FIT.BASE_TYPE['SINT64']:
                self._output_stream.write_int64(value if value is not None else base_type_def['invalid'])
            elif type_code in (FIT.BASE_TYPE['UINT64'], FIT.BASE_TYPE['UINT64Z']):
                self._output_stream.write_uint64(value if value is not None else base_type_def['invalid'])
            elif type_code == FIT.BASE_TYPE['FLOAT32']:
                self._output_stream.write_float32(value if value is not None else float('nan'))
            elif type_code == FIT.BASE_TYPE['FLOAT64']:
                self._output_stream.write_float64(value if value is not None else float('nan'))
            else:
                self._output_stream.write_uint8(value if value is not None else 0xFF)

    def _create_mesg_definition(self, mesg_num: int, mesg: Dict[str, Any]) -> MesgDefinition:
        '''Creates a MesgDefinition from the message number and message data.'''
        mesg_definition = MesgDefinition(mesg_num, mesg, self._field_descriptions)
        mesg_definition.local_mesg_num = self._lookup_local_mesg_num(mesg_definition)
        return mesg_definition

    def _lookup_local_mesg_num(self, mesg_definition: MesgDefinition) -> int:
        '''Searches the local message definitions for a matching definition.'''
        for i, local_def in enumerate(self._local_mesg_definitions):
            if local_def is not None and local_def.equals(mesg_definition):
                return i
        
        local_mesg_num = self._next_local_mesg_num
        self._next_local_mesg_num = (self._next_local_mesg_num + 1) & _LOCAL_MESG_NUM_MASK
        return local_mesg_num

    def _write_mesg_definition_if_not_active(self, mesg_definition: MesgDefinition) -> int:
        '''Writes the message definition if it's not currently active.'''
        local_mesg_num = mesg_definition.local_mesg_num
        
        if (self._local_mesg_definitions[local_mesg_num] is None or
            not self._local_mesg_definitions[local_mesg_num].equals(mesg_definition)):
            self._write_mesg_definition(mesg_definition)
        
        return local_mesg_num

    def _write_mesg_definition(self, mesg_definition: MesgDefinition) -> 'Encoder':
        '''Writes the message definition to the output stream.'''
        mesg_definition.write(self._output_stream)
        self._local_mesg_definitions[mesg_definition.local_mesg_num] = mesg_definition
        return self
