# __init__garmin_fit_sdk.py

###########################################################################################
# Copyright 2022 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################
# ****WARNING****  This file is auto-generated!  Do NOT edit this file.
# Profile Version = 21.99Release
# Tag = production/release/21.99.00-0-gb5b0e7a
############################################################################################


from garmin_fit_sdk.accumulator import Accumulator
from garmin_fit_sdk.bitstream import BitStream
from garmin_fit_sdk.crc_calculator import CrcCalculator
from garmin_fit_sdk.decoder import Decoder
from garmin_fit_sdk.fit import BASE_TYPE, BASE_TYPE_DEFINITIONS
from garmin_fit_sdk.hr_mesg_utils import expand_heart_rates
from garmin_fit_sdk.profile import Profile
from garmin_fit_sdk.stream import Stream
from garmin_fit_sdk.util import FIT_EPOCH_S, convert_timestamp_to_datetime

__version__ = '0.99.0'
