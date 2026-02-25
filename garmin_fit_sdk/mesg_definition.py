'''mesg_definition.py: Contains the MesgDefinition class for FIT message definitions.'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


from . import fit as FIT
from .profile import Profile

_MESG_DEFINITION_MASK = 0x40
_DATE_TIME_TYPES = {'date_time', 'local_date_time'}  # These map to UINT32
_DEV_DATA_MASK = 0x20
_MAX_FIELD_SIZE = 255
_FIELD_DEFAULT_SCALE = 1
_FIELD_DEFAULT_OFFSET = 0

class FieldDefinition:
    '''Represents a field definition within a message definition.'''

    def __init__(self, name: str, num: int, size: int, base_type: int, 
                 field_type: str = None, scale: float = 1, offset: float = 0):
        self.name = name
        self.num = num
        self.size = size
        self.base_type = base_type
        self.type = field_type or 'uint8'
        self.scale = scale
        self.offset = offset

    def __eq__(self, other):
        if not isinstance(other, FieldDefinition):
            return False
        return (self.num == other.num and 
                self.size == other.size and 
                self.base_type == other.base_type)

    def __repr__(self):
        return f"FieldDefinition(name={self.name}, num={self.num}, size={self.size}, base_type={self.base_type})"


class DeveloperFieldDefinition:
    '''Represents a developer field definition within a message definition.'''

    def __init__(self, key: str, field_definition_number: int, size: int, 
                 developer_data_index: int, base_type: int):
        self.key = key
        self.field_definition_number = field_definition_number
        self.size = size
        self.developer_data_index = developer_data_index
        self.base_type = base_type

    def __eq__(self, other):
        if not isinstance(other, DeveloperFieldDefinition):
            return False
        return (self.field_definition_number == other.field_definition_number and
                self.size == other.size and
                self.developer_data_index == other.developer_data_index)

    def __repr__(self):
        return f"DeveloperFieldDefinition(key={self.key}, num={self.field_definition_number}, size={self.size})"


class MesgDefinition:
    '''
    Represents a FIT message definition.
    
    Used by the Encoder to define the structure of messages being written.
    '''

    def __init__(self, mesg_num: int, mesg: dict = None, field_descriptions: dict = None):
        '''
        Creates a MesgDefinition from a message number and message data.
        
        Args:
            mesg_num: The global message number
            mesg: The message data dictionary
            field_descriptions: Developer field descriptions
        '''
        self.mesg_num = mesg_num
        self.local_mesg_num = 0
        self.field_definitions = []
        self.developer_field_definitions = []
        
        if mesg is None:
            mesg = {}
        if field_descriptions is None:
            field_descriptions = {}

        mesg_profile = Profile['messages'].get(mesg_num)
        if mesg_profile is None:
            raise ValueError(f"Unknown message number: {mesg_num}")

        self._build_field_definitions(mesg, mesg_profile)
        
        developer_fields = mesg.get('developer_fields', {})
        if developer_fields:
            self._build_developer_field_definitions(developer_fields, field_descriptions)

        self._validate_field_sizes()

    def _build_field_definitions(self, mesg: dict, mesg_profile: dict):
        '''Builds field definitions from message data and profile.'''
        fields_profile = mesg_profile.get('fields', {})
        
        field_name_to_num = {}
        for field_num, field_info in fields_profile.items():
            field_name_to_num[field_info['name']] = field_num

        for field_name, value in mesg.items():
            if field_name in ('mesg_num', 'developer_fields'):
                continue
                
            field_num = field_name_to_num.get(field_name)
            if field_num is None:
                continue

            field_profile = fields_profile.get(field_num)
            if field_profile is None:
                continue

            field_def = self._create_field_definition(field_name, field_profile, value)
            if field_def is not None:
                self.field_definitions.append(field_def)

        self.field_definitions.sort(key=lambda x: x.num)

    def _create_field_definition(self, field_name: str, field_profile: dict, value) -> FieldDefinition:
        '''Creates a field definition from field profile and value.'''
        field_num = field_profile['num']
        field_type = field_profile['type']
        scale = field_profile.get('scale', [1])[0] if field_profile.get('scale') else 1
        offset = field_profile.get('offset', [0])[0] if field_profile.get('offset') else 0

        base_type = FIT.FIELD_TYPE_TO_BASE_TYPE.get(field_type)
        if base_type is None:
            if field_type in _DATE_TIME_TYPES:
                base_type = FIT.BASE_TYPE['UINT32']
            elif field_type in Profile.get('types', {}):
                base_type = FIT.BASE_TYPE['ENUM']
            else:
                base_type = FIT.BASE_TYPE['UINT8']

        size = self._calculate_field_size(value, base_type, field_type)

        return FieldDefinition(
            name=field_name,
            num=field_num,
            size=size,
            base_type=base_type,
            field_type=field_type,
            scale=scale,
            offset=offset
        )

    def _calculate_field_size(self, value, base_type: int, field_type: str) -> int:
        '''Calculates the size of a field based on value and base type.'''
        base_type_def = FIT.BASE_TYPE_DEFINITIONS.get(base_type)
        if base_type_def is None:
            return 1

        element_size = base_type_def['size']

        if base_type == FIT.BASE_TYPE['STRING']:
            if value is None:
                return 1
            if isinstance(value, str):
                return len(value.encode('utf-8')) + 1  # +1 for null terminator
            if isinstance(value, (list, tuple)):
                total = sum(len(str(v).encode('utf-8')) + 1 for v in value)
                return total
            return 1

        if isinstance(value, (list, tuple)):
            return element_size * len(value)

        return element_size

    def _build_developer_field_definitions(self, developer_fields: dict, field_descriptions: dict):
        '''Builds developer field definitions from developer fields data.'''
        for key, value in developer_fields.items():
            field_desc = field_descriptions.get(key)
            if field_desc is None:
                continue

            field_desc_mesg = field_desc.get('field_description_mesg', {})
            dev_data_id_mesg = field_desc.get('developer_data_id_mesg', {})

            base_type = field_desc_mesg.get('fit_base_type_id', FIT.BASE_TYPE['UINT8'])
            if isinstance(base_type, dict):
                base_type = base_type.get('raw_field_value', FIT.BASE_TYPE['UINT8'])
            base_type = base_type & FIT.BASE_TYPE_MASK

            dev_data_index = dev_data_id_mesg.get('developer_data_index', 0)
            if isinstance(dev_data_index, dict):
                dev_data_index = dev_data_index.get('raw_field_value', 0)

            field_def_num = field_desc_mesg.get('field_definition_number', 0)
            if isinstance(field_def_num, dict):
                field_def_num = field_def_num.get('raw_field_value', 0)

            size = self._calculate_field_size(value, base_type, 'uint8')

            dev_field_def = DeveloperFieldDefinition(
                key=key,
                field_definition_number=field_def_num,
                size=size,
                developer_data_index=dev_data_index,
                base_type=base_type
            )
            self.developer_field_definitions.append(dev_field_def)

    def _validate_field_sizes(self):
        '''Validates that all field sizes are within limits.'''
        invalid_fields = []
        for field_def in self.field_definitions:
            if field_def.size > _MAX_FIELD_SIZE:
                invalid_fields.append(field_def)
        
        for dev_field_def in self.developer_field_definitions:
            if dev_field_def.size > _MAX_FIELD_SIZE:
                invalid_fields.append(dev_field_def)

        if invalid_fields:
            raise ValueError(f"Some field sizes are greater than {_MAX_FIELD_SIZE}: {invalid_fields}")

    def equals(self, other: 'MesgDefinition') -> bool:
        '''Checks if this message definition equals another.'''
        if not isinstance(other, MesgDefinition):
            return False
        
        if self.mesg_num != other.mesg_num:
            return False
        
        if len(self.field_definitions) != len(other.field_definitions):
            return False
        
        if len(self.developer_field_definitions) != len(other.developer_field_definitions):
            return False

        for i, field_def in enumerate(self.field_definitions):
            if field_def != other.field_definitions[i]:
                return False

        for i, dev_field_def in enumerate(self.developer_field_definitions):
            if dev_field_def != other.developer_field_definitions[i]:
                return False

        return True

    def write(self, output_stream) -> None:
        '''Writes the message definition to the output stream.'''
        # Record header
        record_header = _MESG_DEFINITION_MASK | self.local_mesg_num
        if len(self.developer_field_definitions) > 0:
            record_header |= _DEV_DATA_MASK
        output_stream.write_uint8(record_header)

        # Reserved byte
        output_stream.write_uint8(0)

        # Architecture (0 = little endian)
        output_stream.write_uint8(0)

        # Global message number
        output_stream.write_uint16(self.mesg_num)

        # Number of fields
        output_stream.write_uint8(len(self.field_definitions))

        # Field definitions
        for field_def in self.field_definitions:
            output_stream.write_uint8(field_def.num)
            output_stream.write_uint8(field_def.size)
            output_stream.write_uint8(field_def.base_type)

        # Developer field definitions
        if len(self.developer_field_definitions) > 0:
            output_stream.write_uint8(len(self.developer_field_definitions))
            for dev_field_def in self.developer_field_definitions:
                output_stream.write_uint8(dev_field_def.field_definition_number)
                output_stream.write_uint8(dev_field_def.size)
                output_stream.write_uint8(dev_field_def.developer_data_index)

    def __repr__(self):
        return f"MesgDefinition(mesg_num={self.mesg_num}, local={self.local_mesg_num}, fields={len(self.field_definitions)}, dev_fields={len(self.developer_field_definitions)})"