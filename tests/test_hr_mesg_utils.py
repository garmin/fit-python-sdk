'''test_hr_mesg_utils.py: Contains the tests for the heart rate message merging functionality'''

###########################################################################################
# Copyright 2025 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


from garmin_fit_sdk import hr_mesg_utils
from garmin_fit_sdk.decoder import Decoder
from garmin_fit_sdk.stream import Stream

from . import data_expand_hr_mesgs


def test_expand_heart_rates():
    '''Tests expanding heart rates'''
    stream = Stream.from_file("tests/fits/HrmPluginTestActivity.fit")
    decoder = Decoder(stream)
    messages, errors = decoder.read()

    assert len(errors) == 0

    heartrates = hr_mesg_utils.expand_heart_rates(messages['hr_mesgs'])

    assert len(heartrates) == len(data_expand_hr_mesgs.expanded_hr_messages)

    index = 0
    for message in heartrates:
        expected = data_expand_hr_mesgs.expanded_hr_messages[index]
        assert message['timestamp'] == expected['timestamp']
        assert message['heart_rate'] == expected['heart_rate']
        index += 1

def test_hr_mesgs_to_record_mesgs():
    '''Tests that the heart rate messages are merged into the record messages correctly.'''
    stream = Stream.from_file("tests/fits/HrmPluginTestActivity.fit")
    decoder = Decoder(stream)
    messages, errors = decoder.read(merge_heart_rates=True, convert_datetimes_to_dates=False)

    assert len(errors) == 0
    assert len(messages['record_mesgs']) == len(data_expand_hr_mesgs.merged_record_messages)

    index = 0
    for message in messages['record_mesgs']:
        expected = data_expand_hr_mesgs.merged_record_messages[index]
        assert message['timestamp'] == expected['timestamp']
        assert message['heart_rate'] == expected['heart_rate']
        index += 1
