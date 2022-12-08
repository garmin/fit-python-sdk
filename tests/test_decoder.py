'''test_decoder.py: Contains the set of tests for the decoder class in the Python FIT SDK'''

###########################################################################################
# Copyright 2022 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


from datetime import datetime, timezone

import pytest
from garmin_fit_sdk import Decoder, Stream

from tests.data import Data


class TestCheckIntegrity:
    '''Set of tests verify that the decoder class correctly tests the integrity of one or more fit files.'''
    @pytest.mark.parametrize(
        "data,expected_value",
        [
            (bytearray(), False),
            (Data.fit_file_invalid, False),
            (Data.fit_file_minimum, True),
            (Data.fit_file_short, True),

            (Data.fit_file_incorrect_data_size, False)
        ], ids=["Empty File", "Invalid Fit File", "Minimum Size Fit File",
                "Fit File with Messages", "Incorrect Data Size"]
    )
    def test_check_integrity(self, data, expected_value):
        '''Tests the validity of the decoder when it checks a fit file's integrity.'''
        stream = Stream.from_byte_array(data)
        decoder = Decoder(stream)
        assert decoder.check_integrity() == expected_value

    def test_check_integrity_is_fit_fail(self, mocker):
        '''Tests that an invalid fit file will fail when checking integrity.'''
        stream = Stream.from_byte_array(Data.fit_file_short)
        mocker.patch('garmin_fit_sdk.Decoder.is_fit', return_value=False)
        decoder = Decoder(stream)

        assert decoder.check_integrity() is False

    @pytest.mark.parametrize(
        "data,expected_value",
        [
            (Data.fit_file_invalid, False),
            (Data.fit_file_minimum, True),
            (Data.fit_file_short, True),
            (bytearray(), False),
            (bytearray([0xE]), False),
            (bytearray([0x0A, 0x10, 0xD9, 0x07, 0x00, 0x00, 0x00, 0x00,
                        0x2E, 0x46, 0x49, 0x54, 0x91, 0x33, 0x00, 0x00]), False),
            (bytearray([0x0E, 0x10, 0xD9, 0x07, 0x00, 0x00, 0x00, 0x00,
                        0x2C, 0x46, 0x49, 0x54, 0x91, 0x33, 0x00, 0x00]), False),
        ], ids=["Invalid Fit File", "Minimum Size Fit File", "Fit File with Messages",
                "Empty File", "Input Length < 14", "Header Size != 14 || 12", "Data Type != .FIT"]
    )
    def test_is_fit(self, data, expected_value):
        '''Tests the validity of the decoder function used to determine if a file is a valid fit file.'''
        stream = Stream.from_byte_array(data)
        decoder = Decoder(stream)
        assert decoder.is_fit() == expected_value

class TestDecoderConstructor:
    '''Set of tests that test the functionality of the Decoder constructor'''
    def test_fails_if_stream_is_none(self):
        '''Tests that the decoder will properly throw an error if a stream that is None is provided.'''
    try:
        decoder = Decoder(None)
        assert False
    except RuntimeError:
        assert True

class TestDecoderRead():
    '''Set of tests that verify the validity and accuracy of the decoder when reading files.'''
    @pytest.mark.parametrize(
        "data,num_messages",
        [
            (Data.fit_file_minimum, 0),
            (Data.fit_file_short, 2),
            (Data.fit_file_short_new, 1),
            (Data.fit_file_chained, 4)
        ], ids=["Fit File Minimum", "Fit File Short with Invalids", "Fit File Short", "Chained Fit File"]
    )
    def test_successful_read(self, data, num_messages):
        '''Tests that the decoder successfully reads fit files and returns the correct number of messages.'''
        stream = Stream.from_byte_array(data)
        decoder = Decoder(stream)
        messages, errors = decoder.read()
        assert len(errors) == 0
        assert decoder.get_num_messages() == num_messages

    def test_read_incorrect_field_def_size(self):
        '''Tests that the decoder doesn't break when reading a message with an incorrect field definition size.'''
        stream = Stream.from_byte_array(Data.fit_file_short_with_wrong_field_def_size)
        decoder = Decoder(stream)
        messages, errors = decoder.read(convert_datetimes_to_dates=False)

        assert len(errors) == 0
        assert "time_created" in messages["file_id_mesgs"][0]


    @pytest.mark.parametrize(
        "data,expected_output",
        [
            (Data.fit_file_short_new, {'file_id_mesgs' : [{'manufacturer': 'garmin', 'type': 'activity', 'time_created': 1000000000, 'product_name': 'abcdefghi'}]}),
            (Data.fit_file_short_none_array, {'file_id_mesgs' : [{'manufacturer': 'garmin', 'type': 'activity', 'time_created': 1000000000}]})
        ], ids=["Fit File Short", "Fit File Short w/ Invalid String"]
    )
    def test_read_decoder_output(self, data, expected_output):
        '''Tests the validity of the decoder's output after reading a fit file.'''
        stream = Stream.from_byte_array(data)
        decoder = Decoder(stream)
        messages, errors = decoder.read(convert_datetimes_to_dates=False)
        assert expected_output == messages
        assert len(errors) == 0


    @pytest.mark.parametrize(
        "option_status,expected_value",
        [
            (True, -127),
            (False, 1865),
            (None, -127)
        ], ids=["Set to True", "Set to False", "Default Should Apply Scale and Offset"]
    )
    def test_apply_scale_and_offset(self, option_status, expected_value):
        '''Tests the validity of applying scales and offsets to the decoded fields.'''
        stream = Stream.from_file('tests/fits/ActivityDevFields.fit')
        decoder = Decoder(stream)
        if option_status is not None:
            messages, errors = decoder.read(apply_scale_and_offset=option_status, merge_heart_rates=False)
        else:
            messages, errors = decoder.read()
        assert len(errors) == 0
        assert messages['record_mesgs'][0]['altitude'] == expected_value

    def test_scale_and_offset_apply_to_arrays(self):
        stream = Stream.from_file('tests/fits/WithGearChangeData.fit')
        decoder = Decoder(stream)
        messages, errors = decoder.read()
        assert len(errors) == 0

        left_power_phase = messages['record_mesgs'][28]['left_power_phase']
        left_power_phase_peak = messages['record_mesgs'][28]['left_power_phase_peak']

        right_power_phase = messages['record_mesgs'][28]['right_power_phase']
        right_power_phase_peak = messages['record_mesgs'][28]['right_power_phase_peak']

        assert left_power_phase == [337.5000052734376, 199.68750312011724]
        assert left_power_phase_peak == [75.93750118652346, 104.0625016259766]
        assert right_power_phase == [7.031250109863283, 205.31250320800785]
        assert right_power_phase_peak == [70.31250109863284, 106.8750016699219]

    def test_scale_and_offset_correct_type_conversion(self):
        '''Tests applying scale and offset producing the correct data type.'''
        stream = Stream.from_file('tests/fits/WithGearChangeData.fit')
        decoder = Decoder(stream)
        messages, errors = decoder.read()
        assert len(errors) == 0

        assert messages['file_id_mesgs'][0]['serial_number'] == 3390945015
        assert isinstance(messages['file_id_mesgs'][0]['serial_number'], int) is True

        assert messages['file_id_mesgs'][0]['product'] == 3843
        assert isinstance(messages['file_id_mesgs'][0]['product'], int) is True

        assert isinstance(messages['event_mesgs'][4]['rear_gear_num'], int) is True

    @pytest.mark.parametrize(
        "option_status,expected_value",
        [
            (True, datetime.utcfromtimestamp(1000000000 + 631065600)),
            (False, 1000000000),
            (None, datetime.utcfromtimestamp(1000000000 + 631065600))
        ], ids=["Set to True", "Set to False", "Default Should Convert Timestamps"]
    )
    def test_convert_datetimes_to_python_datetimes(self, option_status, expected_value):
        '''Tests the validity of converting timestamps to python datetimes when decoding files.'''
        stream = Stream.from_byte_array(Data.fit_file_short_new)
        decoder = Decoder(stream)
        if option_status is not None:
            messages, errors = decoder.read(convert_datetimes_to_dates=option_status)
        else:
            messages, errors = decoder.read()

        assert len(errors) == 0

        if option_status is False:
            assert messages['file_id_mesgs'][0]['time_created'] == expected_value
        else:
            assert str(messages['file_id_mesgs'][0]['time_created']) == str(expected_value.replace(tzinfo=timezone.utc))

    @pytest.mark.parametrize(
        "option_status,expected_type_value",
        [
            (True, 'activity'),
            (False, 4),
            (None, 'activity')
        ], ids=["Set to True", "Set to False", "Default Should Convert"]
    )
    def test_convert_types_to_strings(self, option_status, expected_type_value):
        '''Tests the validity of converting types to strings when decoding files.'''
        stream = Stream.from_byte_array(Data.fit_file_short_new)
        decoder = Decoder(stream)
        if option_status is not None:
            messages, errors = decoder.read(convert_types_to_strings=option_status)
        else:
            messages, errors = decoder.read()
        assert len(errors) == 0
        assert messages['file_id_mesgs'][0]['type'] == expected_type_value


    @pytest.mark.parametrize(
        "field_key,expected_value",
        [
            (0, pytest.approx(3.0, 0.1)),
            (2, [-10, 12]),
            (3, ['Hello!', 'Good Job!'])
        ], ids=["Single Value", "Array of Values", "String Value(s)"]
    )
    def test_read_developer_data(self, field_key, expected_value):
        '''Tests the validity of reading developer data from a fit file'''
        stream = Stream.from_file('tests/fits/ActivityDevFields.fit')
        decoder = Decoder(stream)
        decoder.read()
        messages, errors = decoder.read()

        assert len(errors) == 0
        assert len(messages['record_mesgs']) == 3601 and len(messages['session_mesgs']) == 1

        assert messages['session_mesgs'][0]['developer_fields'][field_key] == expected_value

    def test_read_dev_data_no_field_description(self):
        '''Tests reading past dev data with no field description message or dev data ID.'''

        stream = Stream.from_byte_array(Data.fit_file_dev_data_missing_field_description)
        decoder = Decoder(stream)
        decoder.read()
        messages, errors = decoder.read()

        assert len(errors) == 0 and len(messages['activity_mesgs']) == 1

    @pytest.mark.parametrize(
        "option_status",
        [
            (True),
            (False),
            (None)
        ], ids=["Set to True", "Set to False", "Default should expand sub fields"]
    )
    def test_expand_sub_fields_options(self, option_status):
        '''Tests the validity of expanding sub fields of messages decoded from a fit file'''
        stream = Stream.from_file('tests/fits/WithGearChangeData.fit')
        decoder = Decoder(stream)
        if option_status is not None:
            messages, errors = decoder.read(expand_sub_fields=option_status, convert_types_to_strings=False)
        else:
            messages, errors = decoder.read(convert_types_to_strings=False)

        assert len(errors) == 0
        assert decoder.get_num_messages() == 2055

        for message in (message for message in messages['event_mesgs'] if message['event'] == 'rider_position_change'):
            if option_status is True or option_status is None:
                assert message['rider_position'] == message['data']

    @pytest.mark.parametrize(
        "option_status, is_integer",
        [
            (True, False),
            (False, True),
        ], ids=["Convert Types is True, No Ints", "Convert Types is True, All Ints"]
    )
    def test_expand_sub_fields_convert_types_to_strings(self, option_status, is_integer):
        stream = Stream.from_file('tests/fits/WithGearChangeData.fit')
        decoder = Decoder(stream)
        messages, errors = decoder.read(convert_types_to_strings=option_status)

        assert len(errors) == 0

        rider_position_event_mesgs = [mesg for mesg in messages['event_mesgs'] if 'rider_position' in mesg]

        for mesg in rider_position_event_mesgs:
            assert isinstance(mesg['rider_position'], int) is is_integer

    @pytest.mark.parametrize(
        "option_status, data, distances",
        [
            (True, Data.fit_file_800m_repeats_little_endian, [4000, 800, 200, 1000]),
            (False, Data.fit_file_800m_repeats_little_endian, [400000, 80000, 20000, 100000]),
            (True, Data.fit_file_800m_repeats_big_endian, [4000, 800, 200, 1000]),
            (False, Data.fit_file_800m_repeats_big_endian, [400000, 80000, 20000, 100000]),
        ], ids=["Apply Scale and Offset is True, Little Endian", "Apply Scale and Offset is False, Little Endian",
        "Apply Scale and Offset is True, Big Endian", "Apply Scale and Offset is False, Big Endian"]
    )
    def test_expand_sub_fields_scale_and_offset(self, option_status, data, distances):
        stream = Stream.from_byte_array(data)
        decoder = Decoder(stream)
        messages, errors = decoder.read(apply_scale_and_offset=option_status, merge_heart_rates=False)

        assert len(errors) == 0

        duration_distance_workout_step_mesgs = [mesg for mesg in messages['workout_step_mesgs'] if 'duration_distance' in mesg]

        for mesg, distance in zip(duration_distance_workout_step_mesgs, distances):
            assert mesg['duration_distance'] == distance

class TestComponentExpansion:
    def test_sub_field_and_component_expansion(self):
        stream = Stream.from_file('tests/fits/WithGearChangeData.fit')
        decoder = Decoder(stream)
        messages, errors = decoder.read()

        assert len(errors) == 0

        rider_position_event_mesgs = [mesg for mesg in messages['event_mesgs'] if 'gear_change_data' in mesg]

        index = 0
        for mesg in rider_position_event_mesgs:
            expected = Data.gear_change_data[index]
            assert mesg['front_gear_num'] == expected['front_gear_num']
            assert mesg['front_gear'] == expected['front_gear']
            assert mesg['rear_gear_num'] == expected['rear_gear_num']
            assert mesg['rear_gear'] == expected['rear_gear']
            assert mesg['data'] == expected['data']
            assert mesg['gear_change_data'] == expected['gear_change_data']

            index += 1

    @pytest.mark.parametrize(
        "option_status",
        [
            (True),
            (False),
            (None)
        ], ids=["Set to True", "Set to False", "Default should expand components"]
    )
    def test_component_expansion_options(self, option_status):
        '''Tests the validity of expanding components of messages decoded from a fit file'''
        stream = Stream.from_file('tests/fits/WithGearChangeData.fit')
        decoder = Decoder(stream)
        if option_status is not None:
            messages, errors = decoder.read(expand_components=option_status, merge_heart_rates=False)
        else:
            messages, errors = decoder.read()

        assert len(errors) == 0

        for message in messages['record_mesgs']:
            if option_status is True or option_status is None:
                assert message['speed'] == message['enhanced_speed']
                assert message['altitude'] == message['enhanced_altitude']
            else:
                assert 'enhanced_speed' not in message
                assert 'enhanced_altitude' not in message

    def test_hr_message_component_expansion(self):
        '''Tests component expansion given heart rate messages.'''
        stream = Stream.from_file('tests/fits/HrmPluginTestActivity.fit')
        decoder = Decoder(stream)
        messages, errors = decoder.read()
        assert len(errors) == 0

        assert messages['hr_mesgs'][0]['event_timestamp'] == 1242209

        hr_mesgs = messages['hr_mesgs']

        index = 0
        for message in hr_mesgs:
            if isinstance(message['event_timestamp'], float):
                assert message['event_timestamp'] == pytest.approx(Data.hrm_plugin_test_activity_expected[index])
                index += 1
                continue
            for timestamp in message['event_timestamp']:
                assert timestamp == pytest.approx(Data.hrm_plugin_test_activity_expected[index])
                index += 1

class TestMergeHeartrates:
    '''Set of tests which verify the functionality of merging heartrates to records when decoding.'''
    @pytest.mark.parametrize(
            "option_status, expected",
            [
                (True, False),
                (False, True),
                (None, False)
            ], ids=["Set to True", "Set to False", "Default should merge heart rates"]
        )
    def test_merge_heart_rates_options(self, option_status, expected):
        '''Tests that all the options settings for merge_heart_rates work as expected when decoding.'''
        stream = Stream.from_file('tests/fits/HrmPluginTestActivity.fit')
        decoder = Decoder(stream)

        if option_status is not None:
            messages, errors = decoder.read(merge_heart_rates=option_status)
        else:
            messages, errors = decoder.read()

        assert len(errors) == 0

        missing_hr = False
        for message in messages['record_mesgs']:
            if 'heart_rate' not in message:
                missing_hr = True
        assert missing_hr == expected

    def test_merge_heart_rate_fails_without_scale_and_offset(self):
        '''Tests to ensure that decoding fails when merge_heart_rates == True but apply_scale_and_offset == False'''
        stream = Stream.from_file('tests/fits/HrmPluginTestActivity.fit')
        decoder = Decoder(stream)
        messages, errors = decoder.read(apply_scale_and_offset=False)
        assert len(errors) == 1

    def test_merge_heart_rate_fails_without_expand_components(self):
        '''Tests to ensure that decoding fails when merge_heart_rates == True but expand_components == False'''
        stream = Stream.from_file('tests/fits/HrmPluginTestActivity.fit')
        decoder = Decoder(stream)
        messages, errors = decoder.read(expand_components=False)
        assert len(errors) == 1


def test_mesg_listener():
    '''Tests that a message listener passed to the decoder is correctly called.'''
    stream = Stream.from_byte_array(Data.fit_file_short)
    decoder = Decoder(stream)

    def mesg_listener(mesg_num, message):
        raise Exception("The message listener was called!")

    messages, errors = decoder.read(mesg_listener=mesg_listener)

    assert len(errors) == 1
    assert str(errors[0]) == "The message listener was called!"
