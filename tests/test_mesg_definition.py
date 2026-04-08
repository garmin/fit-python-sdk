'''test_mesg_definition.py: Contains the set of tests for the _MesgDefinition class.'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import pytest
from garmin_fit_sdk.mesg_definition import _MesgDefinition
from garmin_fit_sdk import fit as FIT


class TestMesgDefinition:
    '''Tests for the _MesgDefinition class.'''

    def test_create_file_id_definition(self):
        mesg = {'type': 4, 'manufacturer': 1}
        mesg_def = _MesgDefinition(0, mesg)

        assert mesg_def.global_message_number == 0
        assert len(mesg_def.field_definitions) == 2

    def test_raises_on_none_mesg(self):
        with pytest.raises(ValueError, match="mesg is missing"):
            _MesgDefinition(0, None)

    def test_raises_on_none_mesg_num(self):
        with pytest.raises(ValueError, match="mesg_num is missing"):
            _MesgDefinition(None, {'type': 4})

    def test_raises_on_invalid_mesg_num(self):
        with pytest.raises(ValueError, match="could not be found"):
            _MesgDefinition(999999, {'type': 4})

    def test_raises_on_no_valid_fields(self):
        with pytest.raises(ValueError, match="No valid fields"):
            _MesgDefinition(0, {'nonexistent_field': 123})

    def test_equals_same_definition(self):
        mesg = {'type': 4, 'manufacturer': 1}
        def1 = _MesgDefinition(0, mesg)
        def2 = _MesgDefinition(0, mesg)
        assert def1.equals(def2)

    def test_not_equals_different_fields(self):
        def1 = _MesgDefinition(0, {'type': 4, 'manufacturer': 1})
        def2 = _MesgDefinition(0, {'type': 4})
        assert not def1.equals(def2)

    def test_not_equals_different_mesg(self):
        def1 = _MesgDefinition(0, {'type': 4})
        def2 = _MesgDefinition(49, {'software_version': 100})
        assert not def1.equals(def2)

    def test_skips_none_values(self):
        mesg = {'type': 4, 'manufacturer': None}
        mesg_def = _MesgDefinition(0, mesg)
        assert len(mesg_def.field_definitions) == 1

    def test_string_field_size(self):
        mesg = {'type': 4, 'product_name': 'TestDevice'}
        mesg_def = _MesgDefinition(0, mesg)
        string_fd = next(fd for fd in mesg_def.field_definitions if fd['name'] == 'product_name')
        assert string_fd['size'] == len('TestDevice'.encode('utf-8')) + 1  # +1 for null terminator

    def test_raises_on_oversized_field(self):
        mesg = {'type': 4, 'product_name': 'A' * 255}
        with pytest.raises(ValueError, match=f"greater than {FIT.MAX_FIELD_SIZE}"):
            _MesgDefinition(0, mesg)

    def test_raises_on_oversized_developer_field(self):
        dev_id = {'developer_data_index': 0}
        field_desc = {
            'developer_data_index': 0,
            'field_definition_number': 0,
            'fit_base_type_id': 0x02,  # UINT8, size=1
        }
        field_descriptions = {0: {'developer_data_id_mesg': dev_id, 'field_description_mesg': field_desc}}
        mesg = {'type': 4, 'developer_fields': {0: [0] * (FIT.MAX_FIELD_SIZE + 1)}}
        with pytest.raises(ValueError, match="Developer field size"):
            _MesgDefinition(0, mesg, field_descriptions=field_descriptions)