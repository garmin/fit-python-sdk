###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import math
from datetime import datetime, timezone

from garmin_fit_sdk import Encoder, FIT_EPOCH_S
from garmin_fit_sdk.fit import BASE_TYPE
from garmin_fit_sdk.profile import Profile

def test_can_encode_a_fit_activity_file():
    two_pi = math.pi * 2.0
    semicircles_per_meter = 107.173
    DOUGHNUTS_EARNED_KEY = 0
    HEART_RATE_KEY = 1

    mesgs = []

    # Create the Developer Id message for the developer data fields.
    developer_data_id_mesg = {
        'mesg_num': Profile['mesg_num']['DEVELOPER_DATA_ID'],
        'application_id': [0] * 16,  # In practice, this should be a UUID converted to a byte array
        'application_version': 1,
        'developer_data_index': 0,
    }
    mesgs.append(developer_data_id_mesg)

    # Create the developer data Field Descriptions
    doughnuts_field_desc_mesg = {
        'mesg_num': Profile['mesg_num']['FIELD_DESCRIPTION'],
        'developer_data_index': 0,
        'field_definition_number': 0,
        'fit_base_type_id': BASE_TYPE['FLOAT32'],
        'field_name': 'Doughnuts Earned',
        'units': 'doughnuts',
        'native_mesg_num': Profile['mesg_num']['SESSION'],
    }
    mesgs.append(doughnuts_field_desc_mesg)

    hr_field_desc_mesg = {
        'mesg_num': Profile['mesg_num']['FIELD_DESCRIPTION'],
        'developer_data_index': 0,
        'field_definition_number': 1,
        'fit_base_type_id': BASE_TYPE['UINT8'],
        'field_name': 'Heart Rate',
        'units': 'bpm',
        'native_mesg_num': Profile['mesg_num']['RECORD'],
        'native_field_num': 3,  # See the FIT Profile for the native field numbers
    }
    mesgs.append(hr_field_desc_mesg)

    # Link the Developer Data Id and Field Description messages with a unique key
    field_descriptions = {
        DOUGHNUTS_EARNED_KEY: {
            'developer_data_id_mesg': developer_data_id_mesg,
            'field_description_mesg': doughnuts_field_desc_mesg,
        },
        HEART_RATE_KEY: {
            'developer_data_id_mesg': developer_data_id_mesg,
            'field_description_mesg': hr_field_desc_mesg,
        },
    }

    # The starting timestamp for the activity
    now = datetime.now(tz=timezone.utc)
    local_timestamp_offset = int(datetime.now().astimezone().utcoffset().total_seconds())
    start_time = int(now.timestamp()) - FIT_EPOCH_S

    # Every FIT file MUST contain a File ID message
    mesgs.append({
        'mesg_num': Profile['mesg_num']['FILE_ID'],
        'type': 'activity',
        'manufacturer': 'development',
        'product': 0,
        'time_created': start_time,
        'serial_number': 1234,
    })

    # A Device Info message is a BEST PRACTICE for FIT ACTIVITY files
    mesgs.append({
        'mesg_num': Profile['mesg_num']['DEVICE_INFO'],
        'device_index': 'creator',
        'manufacturer': 'development',
        'product': 0,
        'product_name': 'FIT Cookbook',
        'serial_number': 1234,
        'software_version': 12.34,
        'timestamp': start_time,
    })

    # Timer Events are a BEST PRACTICE for FIT ACTIVITY files
    mesgs.append({
        'mesg_num': Profile['mesg_num']['EVENT'],
        'timestamp': start_time,
        'event': 'timer',
        'event_type': 'start',
    })

    # Every FIT ACTIVITY file MUST contain Record messages
    timestamp = start_time

    for i in range(3601):
        mesgs.append({
            'mesg_num': Profile['mesg_num']['RECORD'],
            'timestamp': timestamp,
            'distance': i,  # Ramp
            'enhanced_speed': 1,  # Flat Line
            'heart_rate': (math.sin(two_pi * (0.01 * i + 10)) + 1.0) * 127.0,  # Sine
            'cadence': i % 255,  # Sawtooth
            'power': 150 if (i % 255) < 127 else 250,  # Square
            'enhanced_altitude': abs((i % 255) - 127),  # Triangle
            'position_lat': 0,  # Flat Line
            'position_long': i * semicircles_per_meter,  # Ramp

            # Add a Developer Field to the Record Message
            'developer_fields': {
                HEART_RATE_KEY: (math.cos(two_pi * (0.01 * i + 10)) + 1.0) * 127.0,  # Cosine
            },
        })

        timestamp += 1

    # Timer Events are a BEST PRACTICE for FIT ACTIVITY files
    mesgs.append({
        'mesg_num': Profile['mesg_num']['EVENT'],
        'timestamp': timestamp,
        'event': 'timer',
        'event_type': 'stop',
    })

    # Every FIT ACTIVITY file MUST contain at least one Lap message
    mesgs.append({
        'mesg_num': Profile['mesg_num']['LAP'],
        'message_index': 0,
        'timestamp': timestamp,
        'start_time': start_time,
        'total_elapsed_time': timestamp - start_time,
        'total_timer_time': timestamp - start_time,
    })

    # Every FIT ACTIVITY file MUST contain at least one Session message
    mesgs.append({
        'mesg_num': Profile['mesg_num']['SESSION'],
        'message_index': 0,
        'timestamp': timestamp,
        'start_time': start_time,
        'total_elapsed_time': timestamp - start_time,
        'total_timer_time': timestamp - start_time,
        'sport': 'stand_up_paddleboarding',
        'sub_sport': 'generic',
        'first_lap_index': 0,
        'num_laps': 1,

        # Add a Developer Field to the Session Message
        'developer_fields': {
            DOUGHNUTS_EARNED_KEY: (timestamp - start_time) / 1200.0,  # Three per hour
        },
    })

    # Every FIT ACTIVITY file MUST contain EXACTLY one Activity message
    mesgs.append({
        'mesg_num': Profile['mesg_num']['ACTIVITY'],
        'timestamp': timestamp,
        'num_sessions': 1,
        'local_timestamp': timestamp + local_timestamp_offset,
        'total_timer_time': timestamp - start_time,
    })

    # Create an Encoder and provide the developer data field descriptions
    encoder = Encoder(field_descriptions=field_descriptions)

    # Write each message to the encoder
    for mesg in mesgs:
        encoder.write_mesg(mesg)

    # Close the encoder
    uint8_array = encoder.close()

    # Write the bytes to a file
    with open('tests/fits/encode-activity-recipe.fit', 'wb') as f:
        f.write(uint8_array)

    assert len(uint8_array) == 108485
