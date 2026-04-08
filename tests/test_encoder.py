'''test_encoder.py: Contains the set of tests for the Encoder class in the Python FIT SDK'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import pytest
from garmin_fit_sdk import Decoder, Encoder, Stream
from garmin_fit_sdk.crc_calculator import CrcCalculator
from garmin_fit_sdk import fit as FIT
from garmin_fit_sdk.profile import Profile

DEFAULT_DECODER_OPTS = {
    'convert_types_to_strings': False,
    'convert_datetimes_to_dates': False,
}

# MARK: Constructor

class TestEncoderConstructor:

    def test_creates_encoder(self):
        encoder = Encoder()
        assert encoder is not None

    def test_creates_encoder_with_field_descriptions(self):
        field_descriptions = {
            0: {
                'developer_data_id_mesg': {'developer_data_index': 0},
                'field_description_mesg': {
                    'developer_data_index': 0,
                    'fit_base_type_id': FIT.BASE_TYPE['UINT16'],
                    'field_definition_number': 0,
                },
            }
        }
        encoder = Encoder(field_descriptions=field_descriptions)
        assert encoder is not None

# MARK: Add Developer Field

class TestEncoderAddDeveloperField:
    '''Tests for the add_developer_field method.'''

    def test_add_developer_field(self):
        encoder = Encoder()
        dev_id = {'developer_data_index': 0}
        field_desc = {
            'developer_data_index': 0,
            'fit_base_type_id': FIT.BASE_TYPE['UINT16'],
            'field_definition_number': 0,
        }
        result = encoder.add_developer_field(0, dev_id, field_desc)
        assert result is encoder  # returns self for chaining

    def test_raises_on_none_dev_data_id(self):
        encoder = Encoder()
        with pytest.raises(ValueError):
            encoder.add_developer_field(0, None, {'developer_data_index': 0})

    def test_raises_on_none_field_desc(self):
        encoder = Encoder()
        with pytest.raises(ValueError):
            encoder.add_developer_field(0, {'developer_data_index': 0}, None)

    def test_raises_on_mismatched_dev_data_index(self):
        encoder = Encoder()
        with pytest.raises(ValueError, match="do not match"):
            encoder.add_developer_field(
                0,
                {'developer_data_index': 0},
                {'developer_data_index': 1, 'fit_base_type_id': 0, 'field_definition_number': 0},
            )

# MARK: Write Mesg

class TestEncoderWriteMesg:
    '''Tests for the write_mesg method.'''

    def test_write_mesg_requires_mesg_num(self):
        encoder = Encoder()
        with pytest.raises(ValueError, match="mesg_num"):
            encoder.write_mesg({'type': 4})

    def test_write_mesg_basic(self):
        encoder = Encoder()
        encoder.write_mesg({'mesg_num': 0, 'type': 4})
        data = encoder.close()
        assert len(data) > 14 + 2  # header + CRC minimum

    def test_write_mesg_round_trip(self):
        encoder = Encoder()
        encoder.write_mesg({'mesg_num': 0, 'type': 4, 'manufacturer': 1})
        fit_data = encoder.close()

        stream = Stream.from_byte_array(bytearray(fit_data))
        decoder = Decoder(stream)
        messages, errors = decoder.read(**DEFAULT_DECODER_OPTS)
        assert len(errors) == 0
        assert messages['file_id_mesgs'][0]['type'] == 4
        assert messages['file_id_mesgs'][0]['manufacturer'] == 1

# MARK: Encoder Close

class TestEncoderClose:
    '''Tests for the close method.'''

    def test_close_returns_valid_fit_data(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4, 'manufacturer': 1})
        fit_data = encoder.close()

        # Check the file header
        assert fit_data[0] == 14  # header size
        assert fit_data[8:12] == b'.FIT'  # data type

    def test_close_creates_valid_crc(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4, 'manufacturer': 1})
        fit_data = encoder.close()

        # The data should have a valid header CRC
        header_crc = CrcCalculator.calculate_crc(fit_data, 0, 12)
        stored_header_crc = int.from_bytes(fit_data[12:14], 'little')
        assert header_crc == stored_header_crc

#MARK: Transform Values

class TestEncoderTransformValues:
    '''Tests for value transformation during encoding.'''

    @pytest.mark.parametrize('input_value,base_type,field_type,scale,offset,expected', [
        ('42',    'UINT16', 'uint16', 1,   0,   42),
        (1.5,     'UINT32', 'uint32', 100, 0,   150),
        (10,      'SINT32', 'sint32', 2,   500, 1020),
        ('hello', 'STRING', 'string', 1,   0,   'hello'),
    ])
    def test_transform_value(self, input_value, base_type, field_type, scale, offset, expected):
        encoder = Encoder()
        field_def = {
            'base_type': FIT.BASE_TYPE[base_type],
            'type': field_type,
            'scale': scale,
            'offset': offset,
        }
        result = encoder._transform_value(input_value, field_def)
        assert result == expected

    @pytest.mark.parametrize('input_value,base_type,field_type,scale,offset,expected', [
        (None,         'UINT8',  'uint8',  1, 0, [0xFF]),
        ([10, 20, 30], 'UINT16', 'uint16', 1, 0, [10, 20, 30]),
    ])
    def test_transform_values(self, input_value, base_type, field_type, scale, offset, expected):
        encoder = Encoder()
        field_def = {
            'base_type': FIT.BASE_TYPE[base_type],
            'type': field_type,
            'scale': scale,
            'offset': offset,
        }
        result = encoder._transform_values(input_value, field_def)
        assert result == expected

    def test_invalid_type_conversion_raises(self):
        encoder = Encoder()
        field_def = {
            'base_type': FIT.BASE_TYPE['UINT16'],
            'type': 'uint16',
            'scale': 1,
            'offset': 0,
        }
        with pytest.raises(ValueError, match="Could not convert"):
            encoder._transform_value([1, 2, 3], field_def)

# MARK: Local Message Definitions

class TestEncoderLocalMesgDefinitions:
    '''Tests for local message definition caching and reuse.'''

    def test_reuses_local_mesg_definition(self):
        '''Same message shape should reuse the local definition.'''
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4})
        initial_length = encoder._output_stream.length
        encoder.on_mesg(0, {'type': 5})
        second_length = encoder._output_stream.length

        # The second write should be smaller since the definition is already written
        # The difference should be just the message data (1 header + 1 field)
        # compared to a definition + message for the first
        first_increment = initial_length - 14  # subtract header
        second_increment = second_length - initial_length
        assert second_increment < first_increment

    def test_different_message_types_get_different_local_nums(self):
        '''Different message types should get different local message numbers.'''
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4})
        encoder.on_mesg(49, {'software_version': 100})
        fit_data = encoder.close()

        stream = Stream.from_byte_array(bytearray(fit_data))
        decoder = Decoder(stream)
        messages, errors = decoder.read(**DEFAULT_DECODER_OPTS)
        assert len(errors) == 0
        assert len(messages['file_id_mesgs']) == 1
        assert len(messages['file_creator_mesgs']) == 1

# MARK: On Mesg Chaining

class TestEncoderOnMesgChaining:
    '''Tests that on_mesg returns self for chaining.'''

    def test_chaining(self):
        encoder = Encoder()
        result = encoder.on_mesg(0, {'type': 4}).on_mesg(49, {'software_version': 100})
        assert result is encoder

# MARKL: File Structure

class TestEncoderFileStructure:
    '''Tests to verify the structure of encoded FIT files.'''

    def test_header_size(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4})
        data = encoder.close()
        assert data[0] == 14  # HEADER_WITH_CRC_SIZE

    def test_protocol_version(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4})
        data = encoder.close()
        assert data[1] == 0x20  # version 2.0

    def test_profile_version(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4})
        data = encoder.close()
        expected = Profile['version']['major'] * 1000 + Profile['version']['minor']
        stored = int.from_bytes(data[2:4], 'little')
        assert stored == expected

    def test_data_type_marker(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4})
        data = encoder.close()
        assert data[8:12] == b'.FIT'

    def test_data_size_correct(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4})
        data = encoder.close()
        data_size = int.from_bytes(data[4:8], 'little')
        # total size = header(14) + data + CRC(2)
        assert data_size == len(data) - 14 - 2

    def test_file_crc_valid(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4})
        data = encoder.close()
        # CRC is calculated over everything except the last 2 bytes (the CRC itself)
        calculated_crc = CrcCalculator.calculate_crc(data, 0, len(data) - 2)
        stored_crc = int.from_bytes(data[-2:], 'little')
        assert calculated_crc == stored_crc

    def test_empty_encoder_is_16_bytes(self):
        encoder = Encoder()
        data = encoder.close()
        assert len(data) == 16

    def test_file_id_with_five_fields_is_51_bytes(self):
        encoder = Encoder()
        encoder.on_mesg(0, {
            'type': 4,
            'manufacturer': 255,
            'product': 0,
            'time_created': 1000000000,
            'serial_number': 1234,
        })
        assert len(encoder.close()) == 51

# MARK: String Fields

class TestEncoderStringFields:
    '''Tests for string field encoding edge cases.'''

    def test_short_single_byte_string_encoded_length(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'product_name': 'Short String Of Single Byte Characters'})
        assert len(encoder.close()) == 65

    def test_long_single_byte_string_raises_and_encoder_recovers(self):
        long_str = 'A' * 256  # 256 bytes + null terminator = 257 > 255 max
        encoder = Encoder()
        with pytest.raises(ValueError):
            encoder.on_mesg(0, {'product_name': long_str})
        # After the error, close() should still return a valid (empty) file
        assert len(encoder.close()) == 16

    def test_short_multibyte_string_encoded_length(self):
        encoder = Encoder()
        encoder.on_mesg(0, {'product_name': '中文占位符文本'})  # 7 × 3 = 21 UTF-8 bytes
        assert len(encoder.close()) == 48

    def test_long_multibyte_string_raises_and_encoder_recovers(self):
        # 5 repetitions of a 19-char Chinese phrase, each char = 3 UTF-8 bytes → > 255 bytes
        long_str = '这是一个占位符文本，用于展示设计效果。' * 5
        encoder = Encoder()
        with pytest.raises(ValueError):
            encoder.on_mesg(0, {'product_name': long_str})
        assert len(encoder.close()) == 16

# MARK: Add Developer Field

class TestEncoderAddDeveloperFieldValidation:
    '''add_developer_field should raise for all combinations of missing/mismatched index.'''

    @pytest.mark.parametrize('id1,id2', [
        (None, None),
        (None, 1),
        (1, None),
        (0, 1),
    ])
    def test_add_dev_field_invalid_indices_raises(self, id1, id2):
        encoder = Encoder()
        with pytest.raises(ValueError):
            encoder.add_developer_field(
                0,
                {'developer_data_index': id1},
                {'developer_data_index': id2,
                 'fit_base_type_id': FIT.BASE_TYPE['UINT8'],
                 'field_definition_number': 0},
            )

        encoder.close()


# MARK: Developer Data Constructor

class TestEncoderConstructorDeveloperDataValidation:
    '''Constructor should reject fieldDescriptions with invalid developerDataIndex pairs.'''

    @pytest.mark.parametrize('id1,id2', [
        (None, None),
        (None, 1),
        (1, None),
        (0, 1),
    ])
    def test_constructor_invalid_field_descriptions_raises(self, id1, id2):
        field_descriptions = {
            0: {
                'developer_data_id_mesg': {'developer_data_index': id1},
                'field_description_mesg': {'developer_data_index': id2,
                                           'fit_base_type_id': FIT.BASE_TYPE['UINT8'],
                                           'field_definition_number': 0},
            }
        }
        with pytest.raises((ValueError, Exception)):
            Encoder(field_descriptions=field_descriptions)


# MARK: Helpers

DEFAULT_CUSTOM_MESG_NUM = 65280  # A high message number not used by the FIT profile


def _add_custom_mesg_to_profile(mesg_num, mesg_name, fields):
    """Insert a custom message into the global Profile dict for testing."""
    profile_fields = {}
    for field_num, info in fields.items():
        base = info.get('base_type', info.get('baseType', info.get('type', 'uint8')))
        profile_fields[field_num] = {
            'num': field_num,
            'name': info['name'],
            'type': info.get('type', base),
            'base_type': base,
            'array': 'false',
            'scale': [info.get('scale', 1)],
            'offset': [info.get('offset', 0)],
            'units': '',
            'bits': [],
            'components': [],
            'is_accumulated': False,
            'has_components': False,
            'sub_fields': [],
        }
    Profile['messages'][mesg_num] = {
        'num': mesg_num,
        'name': mesg_name,
        'messages_key': f'{mesg_name}_mesgs',
        'fields': profile_fields,
    }


@pytest.fixture
def custom_mesg():
    """Yields an add() callback; removes all registered custom messages on teardown."""
    added = []

    def add(mesg_num, mesg_name, fields):
        _add_custom_mesg_to_profile(mesg_num, mesg_name, fields)
        added.append(mesg_num)

    yield add
    for num in added:
        Profile['messages'].pop(num, None)


def _encode_mesgs(mesgs, field_descriptions=None):
    """Encode a list of {'mesg_num': N, 'mesg': {...}} dicts and return the bytes."""
    kwargs = {'field_descriptions': field_descriptions} if field_descriptions else {}
    encoder = Encoder(**kwargs)
    for item in mesgs:
        encoder.on_mesg(item['mesg_num'], item['mesg'])
    return encoder.close()


def _encode_then_decode(mesgs, field_descriptions=None, decoder_opts=None):
    """Encode then decode a list of messages.  Returns (messages_dict, errors_list)."""
    data = _encode_mesgs(mesgs, field_descriptions)
    stream = Stream.from_byte_array(bytearray(data))
    decoder = Decoder(stream)
    opts = {'convert_types_to_strings': False, 'convert_datetimes_to_dates': False}
    if decoder_opts:
        opts.update(decoder_opts)
    return decoder.read(**opts)


def _assert_values_equal(base_type, expected, actual):
    expected = expected if isinstance(expected, list) else [expected]
    actual = actual if isinstance(actual, list) else [actual]

    assert len(actual) == len(expected), f'{actual!r} != {expected!r}'

    for expected_value, actual_value in zip(expected, actual):
        if base_type == 'string':
            assert actual_value == expected_value
        else:
            assert actual_value == pytest.approx(expected_value, abs=2)


# MARK: Endianness

class TestEncoderEndianness:
    '''Multi-byte base types must have the endianness flag set (bit 7 of base-type byte).'''

    def test_uint16_field_base_type_byte_has_endianness_flag(self):
        # FILE_ID with a single UINT16 field (product).
        # Binary layout: 14-byte header | def-hdr | reserved | arch | mesg-num(2) |
        #                field-count | field-def-num | field-size | base-type-byte ← [22]
        encoder = Encoder()
        encoder.on_mesg(0, {'product': 0x1234})
        data = encoder.close()
        assert data[22] == 0x84  # UINT16 (0x04) | endian flag (0x80)

    def test_dev_field_fit_base_type_id_written_as_is(self):
        # When a FIELD_DESCRIPTION message stores fitBaseTypeId = 0x84 (UINT16 with
        # endianness bit), the encoder must preserve that byte value unchanged.
        dev_id = {'developer_data_index': 0}
        field_desc = {
            'developer_data_index': 0,
            'field_definition_number': 1,
            'fit_base_type_id': 0x84,
        }
        field_descriptions = {0: {'developer_data_id_mesg': dev_id,
                                   'field_description_mesg': field_desc}}
        encoder = Encoder(field_descriptions=field_descriptions)
        encoder.on_mesg(Profile['mesg_num']['DEVELOPER_DATA_ID'], {'developer_data_index': 0})
        encoder.on_mesg(Profile['mesg_num']['FIELD_DESCRIPTION'], {'developer_data_index': 0,
                               'field_definition_number': 1,
                               'fit_base_type_id': 0x84})
        encoder.on_mesg(Profile['mesg_num']['SESSION'], {'message_index': 2, 'developer_fields': {0: 0x1234}})
        data = encoder.close()
        # Byte 43 is the fit_base_type_id value inside the FIELD_DESCRIPTION message data
        assert data[43] == 0x84

# MARK: Unexpected Types

@pytest.mark.parametrize('base_type,value', [
    ('uint8',  'hello'),
    ('uint64', 'hello'),
    ('uint8',  {'a': 1}),
])
class TestEncoderUnexpectedTypes:
    '''Non-convertible value types must raise a ValueError, not silently corrupt data.'''

    def test_unexpected_type_raises(self, base_type, value, custom_mesg):
        custom_mesg(DEFAULT_CUSTOM_MESG_NUM, 'err_mesg', {
            0: {'name': 'val', 'type': base_type, 'base_type': base_type},
        })
        with pytest.raises(ValueError):
            _encode_mesgs([{'mesg_num': DEFAULT_CUSTOM_MESG_NUM, 'mesg': {'val': value}}])



# MARK: Encoder Decoder Integration

class TestEncoderDecoderIntegration:

    def test_encode_decode_file_id(self):
        '''Encode a file_id message and decode it back.'''
        messages, errors = _encode_then_decode([{
            'mesg_num': Profile['mesg_num']['FILE_ID'],
            'mesg': {'type': 4, 'manufacturer': 1, 'serial_number': 12345},
        }])
        assert len(errors) == 0
        assert 'file_id_mesgs' in messages
        assert len(messages['file_id_mesgs']) == 1
        file_id = messages['file_id_mesgs'][0]
        assert file_id['type'] == 4
        assert file_id['manufacturer'] == 1
        assert file_id['serial_number'] == 12345

    def test_encode_decode_multiple_messages(self):
        '''Encode multiple messages and decode them back.'''
        messages, errors = _encode_then_decode([
            {'mesg_num': Profile['mesg_num']['FILE_ID'],  'mesg': {'type': 4, 'manufacturer': 1}},
            {'mesg_num': Profile['mesg_num']['FILE_CREATOR'], 'mesg': {'software_version': 100, 'hardware_version': 5}},
        ])
        assert len(errors) == 0
        assert len(messages['file_id_mesgs']) == 1
        assert len(messages['file_creator_mesgs']) == 1
        file_creator = messages['file_creator_mesgs'][0]
        assert file_creator['software_version'] == 100
        assert file_creator['hardware_version'] == 5

    def test_encode_decode_string_field(self):
        '''Encode a message with a string field and decode it back.'''
        messages, errors = _encode_then_decode([{
            'mesg_num': Profile['mesg_num']['FILE_ID'],
            'mesg': {'type': 4, 'manufacturer': 1, 'product_name': 'TestDevice'},
        }])
        assert len(errors) == 0
        file_id = messages['file_id_mesgs'][0]
        assert file_id['product_name'] == 'TestDevice'

    def test_encode_decode_with_type_strings(self):
        '''Encode using numeric values, decode with type string conversion.'''
        messages, errors = _encode_then_decode(
            [{'mesg_num': Profile['mesg_num']['FILE_ID'], 'mesg': {'type': 4, 'manufacturer': 1}}],
            decoder_opts={'convert_types_to_strings': True},
        )
        assert len(errors) == 0
        file_id = messages['file_id_mesgs'][0]
        assert file_id['type'] == 'activity'
        assert file_id['manufacturer'] == 'garmin'

    def test_encode_decode_same_mesg_type_multiple_times(self):
        '''Encode the same message type multiple times (definition reuse).'''
        messages, errors = _encode_then_decode([
            {'mesg_num': Profile['mesg_num']['FILE_ID'], 'mesg': {'type': 4, 'manufacturer': 1}},
            {'mesg_num': Profile['mesg_num']['FILE_ID'], 'mesg': {'type': 4, 'manufacturer': 2}},
        ])
        assert len(errors) == 0
        assert len(messages['file_id_mesgs']) == 2
        assert messages['file_id_mesgs'][0]['manufacturer'] == 1
        assert messages['file_id_mesgs'][1]['manufacturer'] == 2

    def test_encode_decode_integrity_check(self):
        '''Encoded file should pass integrity check.'''
        encoder = Encoder()
        encoder.on_mesg(0, {'type': 4, 'manufacturer': 1})
        fit_data = encoder.close()

        stream = Stream.from_byte_array(bytearray(fit_data))
        decoder = Decoder(stream)
        assert decoder.check_integrity()

    def test_encode_decode_with_expanded_component_fields(self):
        '''HR messages with eventTimestamp12 should produce expanded eventTimestamp.'''
        hr_mesg = {
            'timestamp': 840026841,
            'filtered_bpm': [71, 72, 75, 77, 79, 81, 83, 83],
            'event_timestamp_12': [78, 91, 230, 94, 209, 70, 64, 135, 161, 245, 28, 254],
        }
        messages, errors = _encode_then_decode(
            [{'mesg_num': Profile['mesg_num']['HR'], 'mesg': hr_mesg}],
            decoder_opts={'merge_heart_rates': False})
        
        expected_expanded_event_timestamps = [
            2.826171875,
            3.5986328125,
            4.341796875,
            5.1064453125,
            5.8125,
            6.5234375,
            7.2392578125,
            7.9697265625,
            ]
        
        assert errors == []
        assert len(messages['hr_mesgs']) == 1
        decoded = messages['hr_mesgs'][0]
        assert decoded['event_timestamp'] == expected_expanded_event_timestamps
        assert decoded['event_timestamp_12'] == hr_mesg['event_timestamp_12']
        assert decoded['filtered_bpm'] == hr_mesg['filtered_bpm']
        assert decoded['timestamp'] == hr_mesg['timestamp']

    def test_encoder_rounds_numeric_non_floating_point_fields_with_scale_and_offset(self):
        '''A float heart_rate (no scale) should truncate to int on decode.'''
        record_mesg = {
            'timestamp': 1112368427,
            'heart_rate': 123.56,  # uint8, no scale → truncate to 123
            'speed': 1.019,
            'distance': 10.789,   # scale=100 → encoded as round(1078.9)=1079 → decoded 10.79
        }
        messages, errors = _encode_then_decode(
            [{'mesg_num': Profile['mesg_num']['RECORD'], 'mesg': record_mesg}])
        assert errors == []
        decoded = messages['record_mesgs'][0]
        assert decoded['heart_rate'] == 123
        assert decoded['distance'] == 10.79
        assert decoded['speed'] == record_mesg['speed']
        assert decoded['enhanced_speed'] == record_mesg['speed']

    def test_encoder_applies_scale_and_offset_to_expanded_component_fields(self):
        '''Fields with singular expanded components (altitude, speed) round-trip correctly.'''
        record_mesg = {
            'heart_rate': 55,
            'altitude': 100,
            'speed': 1.5,
        }
        messages, errors = _encode_then_decode(
            [{'mesg_num': Profile['mesg_num']['RECORD'], 'mesg': record_mesg}])
        assert errors == []
        decoded = messages['record_mesgs'][0]
        assert decoded['heart_rate'] == record_mesg['heart_rate']
        assert decoded['altitude'] == record_mesg['altitude']
        assert decoded['speed'] == record_mesg['speed']

    def test_encode_decode_dev_field_multibyte_base_type(self):
        '''Developer fields with multi-byte base types round-trip correctly.'''
        dev_id_mesg = {'developer_data_index': 0}
        field_desc_mesg = {
            'developer_data_index': 0,
            'field_definition_number': 1,
            'fit_base_type_id': 0x84,  # UINT16 with endian flag
        }
        file_id_mesg = {
            'product': 0x5555,
            'developer_fields': {0: 0x1234},
        }
        field_descriptions = {
            0: {'developer_data_id_mesg': dev_id_mesg,
                'field_description_mesg': field_desc_mesg},
        }
        mesgs = [
            {'mesg_num': Profile['mesg_num']['DEVELOPER_DATA_ID'], 'mesg': dev_id_mesg},
            {'mesg_num': Profile['mesg_num']['FIELD_DESCRIPTION'], 'mesg': field_desc_mesg},
            {'mesg_num': Profile['mesg_num']['FILE_ID'],   'mesg': file_id_mesg},
        ]
        messages, errors = _encode_then_decode(mesgs, field_descriptions=field_descriptions)
        assert errors == []
        assert len(messages['file_id_mesgs']) == 1
        decoded = messages['file_id_mesgs'][0]
        assert decoded['product'] == file_id_mesg['product']
        assert decoded['developer_fields'][0] == file_id_mesg['developer_fields'][0]


# MARK: Encoder Decoder All Types

@pytest.mark.parametrize('base_type_name,input_value,expected_value,options', [
    # ── Basic single values ──────────────────────────────────────────────────
    ('uint8',   123,            123,            {}),
    ('uint16',  12345,          12345,          {}),
    ('uint32',  1234567890,     1234567890,     {}),
    ('sint8',   -123,           -123,           {}),
    ('sint16',  -12345,         -12345,         {}),
    ('sint32',  -123456789,     -123456789,     {}),
    ('string',  'Test String',  'Test String',  {}),
    ('float32', 123.4,          123.4,          {}),
    ('float64', 123456.789012,  123456.789012,  {}),
    ('uint8z',  200,            200,            {}),
    ('uint16z', 60000,          60000,          {}),
    ('uint32z', 4000000000,     4000000000,     {}),
    ('byte',    0xDE,           0xDE,           {}),
    ('sint64',  -12345678901234,  -12345678901234,  {}),
    ('uint64',  12345678901234,   12345678901234,   {}),
    ('uint64z', 12345678901234,   12345678901234,   {}),
    # ── Array values ────────────────────────────────────────────────────────
    ('uint8',   [12, 34, 56],           [12, 34, 56],           {}),
    ('uint16',  [12345, 54321],         [12345, 54321],         {}),
    ('uint32',  [1234567890, 987654321], [1234567890, 987654321], {}),
    ('sint8',   [-123, -12],            [-123, -12],            {}),
    ('sint16',  [-12345, -5432],        [-12345, -5432],        {}),
    ('sint32',  [-123456789, -98765432], [-123456789, -98765432], {}),
    ('string',  ['Test String 1', 'Test String 2'], ['Test String 1', 'Test String 2'], {}),
    ('float32', [123.4, 432.1],         [123.4, 432.1],         {}),
    ('float64', [123456.789012, 210987.654321], [123456.789012, 210987.654321], {}),
    ('uint8z',  [200, 150],             [200, 150],             {}),
    ('uint16z', [60000, 30000],         [60000, 30000],         {}),
    ('uint32z', [4000000000, 2000000000], [4000000000, 2000000000], {}),
    ('byte',    [0xDE, 0xAD],           [0xDE, 0xAD],           {}),
    ('sint64',  [-12345678901234, -43210987654321], [-12345678901234, -43210987654321], {}),
    ('uint64',  [12345678901234, 43210987654321],  [12345678901234, 43210987654321],  {}),
    ('uint64z', [12345678901234, 43210987654321],  [12345678901234, 43210987654321],  {}),
    # ── Offset tests (decoder applies offset → round-trips to original) ─────
    ('uint8',   123,        123,        {'offset': 2}),
    ('uint16',  12345,      12345,      {'offset': 2}),
    ('uint32',  1234567890, 1234567890, {'offset': 2}),
    ('sint8',   -64,        -64,        {'offset': 2}),
    ('sint16',  -12345,     -12345,     {'offset': 2}),
    ('sint32',  -123456789, -123456789, {'offset': 2}),
    ('string',  'Test String', 'Test String', {'offset': 2}),
    ('float32', 123.4,      123.4,      {'offset': 2}),
    ('float64', 123456.789012, 123456.789012, {'offset': 2}),
    ('uint8z',  100,        100,        {'offset': 2}),
    ('uint16z', 60000,      60000,      {'offset': 2}),
    ('uint32z', 1000000000, 1000000000, {'offset': 2}),
    ('byte',    0xDE,       0xDE,       {'offset': 2}),
    # ── Scale tests (decoder applies scale → round-trips to original) ────────
    ('uint8',   123,        123,        {'scale': 2}),
    ('uint16',  12345,      12345,      {'scale': 2}),
    ('uint32',  1234567890, 1234567890, {'scale': 2}),
    ('sint8',   -12,        -12,        {'scale': 2}),
    ('sint16',  -1234,      -1234,      {'scale': 2}),
    ('sint32',  -12345,     -12345,     {'scale': 2}),
    ('string',  'Test String', 'Test String', {'scale': 2}),
    ('float32', 123.4,      123.4,      {'scale': 2}),
    ('float64', 123456.789012, 123456.789012, {'scale': 2}),
    ('uint8z',  123,        123,        {'scale': 2}),
    ('uint16z', 1234,       1234,       {'scale': 2}),
    ('uint32z', 12345,      12345,      {'scale': 2}),
    ('byte',    0x01,       0x01,       {'scale': 2}),
    # ── 64-bit scale/offset (Python decoder applies them → round-trips) ──────
    ('sint64',  -100,   -100,   {'offset': 2}),
    ('uint64',  100,    100,    {'offset': 2}),
    ('uint64z', 100,    100,    {'offset': 2}),
    ('sint64',  -500,   -500,   {'scale': 2}),
    ('uint64',  100,    100,    {'scale': 2}),
    ('uint64z', 100,    100,    {'scale': 2}),
    ('uint64',  123.45, 123.45, {'scale': 100}),
    # ── Integer rounding with scale ─────────────────────────────────────────
    ('uint8', 12.21, 12.2, {'scale': 10}),
    ('uint8', 12.77, 12.8, {'scale': 10}),
    ('uint8', 12.5,  12.5, {'scale': 10}),
    # ── String-to-numeric conversion ────────────────────────────────────────
    ('uint8',  '123',            123,            {}),
    ('float32', '123.456',       123.456,        {}),
    ('float64', '123456.789012', 123456.789012,  {}),
    ('uint64',  '12345678901234',  12345678901234,  {}),
    ('sint64',  '-12345678901234', -12345678901234, {}),
    # Very large uint64 string – truncated to 64 bits
    ('uint64', '1234567890123456789012345678901234567890', 12446928571455179474, {}),
    # ── Overflow / truncation tests ─────────────────────────────────────────
    ('uint8',   0x1234,          0x34,           {}),
    ('sint8',   0x12FF,          -1,             {}),
    ('uint8z',  0x1234,          0x34,           {}),
    ('uint16',  0x123456,        0x3456,         {}),
    ('sint16',  0x12FFFF,        -1,             {}),
    ('uint16z', 0x123456,        0x3456,         {}),
    ('uint32',  0x1234567899,    0x34567899,     {}),
    ('sint32',  0x12FFFFFFFF,    -1,             {}),
    ('uint32z', 0x1234567899,    0x34567899,     {}),
    ('byte',    0x1234,          0x34,           {}),
    ('uint64', 0x12FFFFFFFFFFFFFFFFFFFFFFFF1, 0xFFFFFFFFFFFFFFF1, {}),
    ('uint64z', 0x12FFFFFFFFFFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF, {}),
    ('sint64',  0x12FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, -1,    {}),
])
class TestBaseTypeEncodeDecode:
    '''Encode then decode a single custom field for every parametrised case.'''

    def test_encode_decode(self, base_type_name, input_value, expected_value, options,
                           custom_mesg):
        scale = options.get('scale', 1)
        offset = options.get('offset', 0)

        custom_mesg(DEFAULT_CUSTOM_MESG_NUM, 'test_mesg', {
            0: {'name': 'test_field', 'type': base_type_name,
                'base_type': base_type_name, 'scale': scale, 'offset': offset},
        })

        messages, errors = _encode_then_decode([{
            'mesg_num': DEFAULT_CUSTOM_MESG_NUM,
            'mesg': {'test_field': input_value},
        }])

        assert errors == []
        assert 'test_mesg_mesgs' in messages
        raw = messages['test_mesg_mesgs'][0].get('test_field')
        _assert_values_equal(base_type_name, expected_value, raw)


# MARK: Encoder Decoder Developer Field Types

@pytest.mark.parametrize('base_type_name,field_value', [
    ('uint8',   123),
    ('uint16',  12345),
    ('uint32',  1234567890),
    ('sint8',   -123),
    ('sint16',  -12345),
    ('sint32',  -123456789),
    ('string',  'Test Field'),
    ('float32', 123.456),
    ('float64', 123456.789012),
    ('uint8z',  200),
    ('uint16z', 60000),
    ('uint32z', 4000000000),
    ('byte',    0xDE),
    ('sint64',  -12345678901234),
    ('uint64',  12345678901234),
    ('uint64z', 12345678901234),
    # Array values
    ('uint8',   [12, 34, 56]),
    ('uint16',  [12345, 54321]),
    ('uint32',  [1234567890, 987654321]),
    ('sint8',   [-123, -12]),
    ('sint16',  [-12345, -5432]),
    ('sint32',  [-123456789, -98765432]),
    ('string',  ['Test String 1', 'Test String 2']),
    ('float32', [123.4, 432.1]),
    ('float64', [123456.789012, 210987.654321]),
    ('uint8z',  [200, 150]),
    ('uint16z', [60000, 30000]),
    ('uint32z', [4000000000, 2000000000]),
    ('byte',    [0xDE, 0xAD]),
    ('sint64',  [-12345678901234, -43210987654321]),
    ('uint64',  [12345678901234, 43210987654321]),
    ('uint64z', [12345678901234, 43210987654321]),
])
class TestDevFieldBaseTypeEncodeDecode:
    '''Developer fields must encode and decode correctly for every base type.'''

    def test_encode_decode_dev_field(self, base_type_name, field_value):
        from garmin_fit_sdk import fit as FIT
        DEV_KEY = 0
        fit_base_type_id = FIT.FIELD_TYPE_TO_BASE_TYPE.get(base_type_name,
                                                            FIT.BASE_TYPE['UINT8'])

        dev_id_mesg = {
            'application_id': list(range(16)),
            'application_version': 1,
            'developer_data_index': 0,
        }
        field_desc_mesg = {
            'developer_data_index': 0,
            'field_definition_number': 0,
            'fit_base_type_id': fit_base_type_id,
            'field_name': 'Test Field',
        }
        field_descriptions = {
            DEV_KEY: {
                'developer_data_id_mesg': dev_id_mesg,
                'field_description_mesg': field_desc_mesg,
            }
        }
        session_mesg = {
            'message_index': 0,
            'sport': 1,
            'developer_fields': {DEV_KEY: field_value},
        }
        mesgs = [
            {'mesg_num': Profile['mesg_num']['DEVELOPER_DATA_ID'], 'mesg': dev_id_mesg},
            {'mesg_num': Profile['mesg_num']['FIELD_DESCRIPTION'], 'mesg': field_desc_mesg},
            {'mesg_num': Profile['mesg_num']['SESSION'],  'mesg': session_mesg},
        ]
        messages, errors = _encode_then_decode(mesgs, field_descriptions=field_descriptions)

        assert errors == []
        assert len(messages['session_mesgs']) == 1
        actual = messages['session_mesgs'][0]['developer_fields'][DEV_KEY]
        _assert_values_equal(base_type_name, field_value, actual)
