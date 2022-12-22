'''fit.py: Contains base type defintions and conversion functions compliant with the FIT Protocol.'''

###########################################################################################
# Copyright 2022 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################
# ****WARNING****  This file is auto-generated!  Do NOT edit this file.
# Profile Version = 21.100Release
# Tag = production/release/21.100.00-0-ga3950f6
############################################################################################


BASE_TYPE = {
    "ENUM": 0x00,
    "SINT8": 0x01,
    "UINT8": 0x02,
    "SINT16": 0x83,
    "UINT16": 0x84,
    "SINT32": 0x85,
    "UINT32": 0x86,
    "STRING": 0x07,
    "FLOAT32": 0x88,
    "FLOAT64": 0x89,
    "UINT8Z": 0x0A,
    "UINT16Z": 0x8B,
    "UINT32Z": 0x8C,
    "BYTE": 0x0D,
    "SINT64": 0x8E,
    "UINT64": 0x8F,
    "UINT64Z": 0x90
}

FIELD_TYPE_TO_BASE_TYPE = {
    "sint8": BASE_TYPE['SINT8'],
    "uint8": BASE_TYPE['UINT8'],
    "sint16": BASE_TYPE['SINT16'],
    "uint16": BASE_TYPE['UINT16'],
    "sint32": BASE_TYPE['SINT32'],
    "uint32": BASE_TYPE['UINT32'],
    "string": BASE_TYPE['STRING'],
    "float32": BASE_TYPE['FLOAT32'],
    "float64": BASE_TYPE['FLOAT64'],
    "uint8z": BASE_TYPE['UINT8Z'],
    "uint16z": BASE_TYPE['UINT16Z'],
    "uint32z": BASE_TYPE['UINT32Z'],
    "byte": BASE_TYPE['BYTE'],
    "sint64": BASE_TYPE['SINT64'],
    "uint64": BASE_TYPE['UINT64'],
    "uint64z": BASE_TYPE['UINT64Z']
}

BASE_TYPE_DEFINITIONS = {
    0x00: {'size': 1, 'type': BASE_TYPE["ENUM"], 'signed': False, 'type_code': 'B', 'invalid': 0xFF},
    0x01: {'size': 1, 'type': BASE_TYPE["SINT8"], 'signed': True, 'type_code': 'b', 'invalid': 0x7F},
    0x02: {'size': 1, 'type': BASE_TYPE["UINT8"], 'signed': False, 'type_code': 'B', 'invalid': 0xFF},
    0x83: {'size': 2, 'type': BASE_TYPE["SINT16"], 'signed': True, 'type_code': 'h', 'invalid': 0x7FFF},
    0x84: {'size': 2, 'type': BASE_TYPE["UINT16"], 'signed': False, 'type_code': 'H', 'invalid': 0xFFFF},
    0x85: {'size': 4, 'type': BASE_TYPE["SINT32"], 'signed': True, 'type_code': 'i', 'invalid': 0x7FFFFFFF},
    0x86: {'size': 4, 'type': BASE_TYPE["UINT32"], 'signed': False, 'type_code': 'I', 'invalid': 0xFFFFFFFF},
    0x07: {'size': 1, 'type': BASE_TYPE["STRING"], 'signed': False, 'type_code': 's', 'invalid': 0x00},
    0x88: {'size': 4, 'type': BASE_TYPE["FLOAT32"], 'signed': True, 'type_code': 'f', 'invalid': 0xFFFFFFFF},
    0x89: {'size': 8, 'type': BASE_TYPE["FLOAT64"], 'signed': True, 'type_code': 'd', 'invalid': 0xFFFFFFFFFFFFFFFF},
    0x0A: {'size': 1, 'type': BASE_TYPE["UINT8Z"], 'signed': False, 'type_code': 'B', 'invalid': 0x00},
    0x8B: {'size': 2, 'type': BASE_TYPE["UINT16Z"], 'signed': False, 'type_code': 'H', 'invalid': 0x0000},
    0x8C: {'size': 4, 'type': BASE_TYPE["UINT32Z"], 'signed': False, 'type_code': 'I', 'invalid': 0x00000000},
    0x0D: {'size': 1, 'type': BASE_TYPE["BYTE"], 'signed': False, 'type_code': 'B', 'invalid': 0xFF},
    0x8E: {'size': 8, 'type': BASE_TYPE["SINT64"], 'signed': True, 'type_code': 'q', 'invalid': 0x7FFFFFFFFFFFFFFF},
    0x8F: {'size': 8, 'type': BASE_TYPE["UINT64"], 'signed': False, 'type_code': 'Q', 'invalid': 0xFFFFFFFFFFFFFFFF},
    0x90: {'size': 8, 'type': BASE_TYPE["UINT64Z"], 'signed': False, 'type_code': 'L', 'invalid': 0x0000000000000000},
}

NUMERIC_FIELD_TYPES = [
    "sint8",
    "uint8",
    "sint16",
    "uint16",
    "sint32",
    "uint32",
    "float32",
    "float64",
    "uint8z",
    "uint16z",
    "uint32z",
    "byte",
    "sint64",
    "uint64",
    "uint64z"
]
