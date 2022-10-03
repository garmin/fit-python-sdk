'''test_accumulator.py: Contains the set of tests for the Accumulator class in the Python FIT SDK'''

###########################################################################################
# Copyright 2022 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


from garmin_fit_sdk.accumulator import Accumulator

def test_accumulator():
    '''Tests functionality of the accumulator class.'''
    accumulator = Accumulator()

    accumulator.add(0,0,0)
    assert accumulator.accumulate(0,0,1,8) == 1

    accumulator.add(0,0,0)
    assert accumulator.accumulate(0,0,2,8) == 2

    accumulator.add(0,0,0)
    assert accumulator.accumulate(0,0,3,8) == 3

    accumulator.add(0,0,0)
    assert accumulator.accumulate(0,0,4,8) == 4
