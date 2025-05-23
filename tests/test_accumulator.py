'''test_accumulator.py: Contains the set of tests for the Accumulator class in the Python FIT SDK'''

###########################################################################################
# Copyright 2025 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


from garmin_fit_sdk.accumulator import Accumulator

def test_accumulator():
    '''Tests functionality of the accumulator class.'''
    accumulator = Accumulator()

    accumulator.createAccumulatedField(0,0,0)

    assert accumulator.accumulate(0,0,1,8) == 1
    assert accumulator.accumulate(0,0,2,8) == 2
    assert accumulator.accumulate(0,0,3,8) == 3
    assert accumulator.accumulate(0,0,4,8) == 4

def test_accumulators_accumulates_multiple_fields_independently():
    '''Tests that the accumulator can hold and accumluate different fields at the same time.'''
    accumulator = Accumulator()

    accumulator.createAccumulatedField(0,0,0)
    assert accumulator.accumulate(0,0,254,8) == 254

    accumulator.createAccumulatedField(1,1,0)
    assert accumulator.accumulate(1,1,2,8) == 2

    assert accumulator.accumulate(0,0,0,8) == 256

def test_accumulator_accumulates_field_rollover():
    '''Tests that the accumulator handles rollover field values accordingly.'''
    accumulator = Accumulator()

    accumulator.createAccumulatedField(0,0,250)
    
    assert accumulator.accumulate(0,0,254,8) == 254
    assert accumulator.accumulate(0,0,255,8) == 255
    assert accumulator.accumulate(0,0,0,8) == 256
    assert accumulator.accumulate(0,0,3,8) == 259