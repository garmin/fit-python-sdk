# Garmin - FIT Python SDK

## FIT SDK Documentation
The FIT SDK documentation is available at [https://developer.garmin.com/fit](https://developer.garmin.com/fit).
## FIT SDK Developer Forum
Share your knowledge, ask questions, and get the latest FIT SDK news in the [FIT SDK Developer Forum](https://forums.garmin.com/developer/).

## FIT Python SDK Requirements
* [Python](https:##www.python.org/downloads/) Version 3.6 or greater is required to run the FIT Python SDK

## Install
```sh
pip install garmin-fit-sdk
```

## Usage
```py
from garmin_fit_sdk import Decoder, Stream

stream = Stream.from_file("Activity.fit")
decoder = Decoder(stream)
messages, errors = decoder.read()

print(errors)
print(messages)
```

## Decoder

### Constructor

Creating Decoder objects requires an input Stream representing the binary FIT file data to be decoded. See [Creating Streams](#creatingstreams) for more information on constructing Stream objects.

Once a Decoder object is created it can be used to check that the Stream is a FIT file, that the FIT file is valid, and to read the contents of the FIT file.

### is_fit Method

All valid FIT files should include a 12 or 14 byte file header. The 14 byte header is the preferred header size and the most common size used. Bytes 8-11 of the header contain the ASCII values ".FIT". This string can easily be spotted when opening a binary FIT file in a text or hex editor.

```
  Offset: 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
00000000: 0E 10 43 08 78 06 09 00 2E 46 49 54 96 85 40 00    ..C.x....FIT..@.
00000010: 00 00 00 07 03 04 8C 04 04 86 07 04 86 01 02 84    ................
00000020: 02 02 84 05 02 84 00 01 00 00 19 28 7E C5 95 B0    ...........(~E.0
```

### check_integrity Method

The checkIntegrity method performs three checks on a FIT file:

1. Checks that bytes 8-11 of the header contain the ASCII values ".FIT".
2. Checks that the total file size is equal to Header Size + Data Size + CRC Size.
3. Reads the contents of the file, computes the CRC, and then checks that the computed CRC matches the file CRC.

A file must pass all three of these tests to be considered a valid FIT file. See the [IsFIT(), CheckIntegrity(), and Read() Methods recipe](/fit/cookbook/isfit-checkintegrity-read/) for use-cases where the checkIntegrity method should be used and cases when it might be better to avoid it.

#### Read Method
The Read method decodes all messages from the input stream and returns an object containing a list of errors encountered during the decoding and a dictionary of decoded messages grouped by message type. Any exceptions encountered during decoding will be caught by the Read method and added to the list of errors.

The Read method accepts an optional options object that can be used to customize how field data is represented in the decoded messages. All options are enabled by default. Disabling options may speed up file decoding. Options may also be enabled or disable based on how the decoded data will be used.

```py
messages, errors = read(
            apply_scale_and_offset = True,
            convert_datetimes_to_dates = True,
            convert_types_to_strings = True,
            enable_crc_check = True,
            expand_sub_fields = True,
            expand_components = True,
            merge_heart_rates = True,
            mesg_listener = None)
```
#### mesg_listener
Optional callback function that can be used to inspect or manipulate messages after they are fully decoded and all the options have been applied. The message is mutable and we be returned from the Read method in the messages dictionary.

Example mesg_listener callback that tracks the field names across all Record messages.

```py
from garmin_fit_sdk import Decoder, Stream, Profile

stream = Stream.from_file("Activity.fit")
decoder = Decoder(stream)

record_fields = set()
def mesg_listener(mesg_num, message):
    if mesg_num == Profile['mesg_num']['RECORD']:
        for field in message:
            record_fields.add(field)

messages, errors = decoder.read(mesg_listener = mesg_listener)

if len(errors) > 0:
    print(f"Something went wrong decoding the file: {errors}")
    return

print(record_fields)
```

#### apply_scale_and_offset: true | false
When true the scale and offset values as defined in the FIT Profile are applied to the raw field values.
```py
{
  'altitude': 1587 ## with a scale of 5 and offset of 500 applied
}
```
When false the raw field value is used.
```py
{
  'altitude': 10435 ## raw value store in file
}
```
#### enable_crc_check: true | false
When true the CRC of the file is calculated when decoding a FIT file and then validated with the CRC found in the file. Disabling the CRC calculation will improve the performance of the read method.
#### expand_sub_fields: true | false
When true subfields are created for fields as defined in the FIT Profile.
```py
{
  'event': 'rear_gear_change',
  'data': 16717829,
  'gear_change_data':16717829 ## Sub Field of data when event == 'rear_gear_change'
}
```
When false subfields are omitted.
```py
{
  'event': 'rearGearChange',
  'data': 16717829
}
```
#### expand_components: true | false
When true field components as defined in the FIT Profile are expanded into new fields. expand_sub_fields must be set to true in order for subfields to be expanded

```py
{
  'event': 'rear_gear_change'
  'data': 16717829,
  'gear_change_data':16717829, ## Sub Field of data when event == 'rear_gear_change'
  'front_gear': 2, ## Expanded field of gear_change_data, bits 0-7
  'front_gear_num': 53, ## Expanded field of gear_change_data, bits 8-15
  'rear_gear': 11, ## Expanded field of gear_change_data, bits 16-23
  'rear_gear_num': 1, ## Expanded field of gear_change_data, bits 24-31
}
```
When false field components are not expanded.
```py
{
  'event': 'rear_gear_change',
  'data': 16717829,
  'gear_change_data': 16717829 ### Sub Field of data when event == 'rear_gear_change'
}
```
#### convert_types_to_strings: true | false
When true field values are converted from raw integer values to the corresponding string values as defined in the FIT Profile.
```py
{ 'type':'activity'}
```
When false the raw integer value is used.
```py
{ 'type': 4 }
```
#### convert_datetimes_to_dates: true | false
When true FIT Epoch values are converted to Python datetime objects.
```py
{ 'time_created': {Python datetime object} }
```
When false the FIT Epoch value  is used.
```py
{ 'time_created': 995749880 }
```
When false the Util.convert_timestamp_to_datetime method may be used to convert FIT Epoch values to Python datetime objects.
#### merge_heart_rates: true | false
When true automatically merge heart rate values from HR messages into the Record messages. This option requires the apply_scale_and_offset and expand_components options to be enabled. This option has no effect on the Record messages when no HR messages are present in the decoded messages.

## Creating Streams
Stream objects contain the binary FIT data to be decoded. Streams objects can be created from bytearrays, BufferedReaders, and BytesIO objects. Internally the Stream class uses a BufferedReader to manage the byte stream.

#### From a file
```py
stream = Stream.from_file("activity.fit")
print(f"is_fit: {Decoder.is_fit(stream)}")
```
#### From a bytearray
```py
fit_byte_array = bytearray([0x0E, 0x10, 0xD9, 0x07, 0x00, 0x00, 0x00, 0x00, 0x2E, 0x46, 0x49, 0x54, 0x91, 0x33, 0x00, 0x00])
stream = Stream.from_byte_array(fit_byte_array)
print(f"is_fit: {Decoder.is_fit(stream)}")
```
#### From a BytesIO Object
```py
fit_byte_bytes_io = io.BytesIO(bytearray([0x0E, 0x10, 0xD9, 0x07, 0x00, 0x00, 0x00, 0x00, 0x2E, 0x46, 0x49, 0x54, 0x91, 0x33, 0x00, 0x00]))
stream = Stream.from_byte_io(fit_byte_bytes_io)
print(f"is_fit: {Decoder.is_fit(stream)}")
```
#### From a buffered_reader
```py
fit_buffered_reader = io.BufferedReader(io.BytesIO(bytearray([0x0E, 0x10, 0xD9, 0x07, 0x00, 0x00, 0x00, 0x00, 0x2E, 0x46, 0x49, 0x54, 0x91, 0x33, 0x00, 0x00])))
stream = Stream.from_buffered_reader(fit_buffered_reader)
print(f"is_fit: {Decoder.is_fit(stream)}")
```

## Util
The Util object contains both constants and methods for working with decoded messages and fields.
### FIT_EPOCH_S Constant
The FIT_EPOCH_S constant represents the number of seconds between the Unix Epoch and the FIT Epoch.
```py
FIT_EPOCH_S = 631065600
```
The FIT_EPOCH_S value can be used to convert FIT Epoch values to Python datetime objects.
```py
python_date = datetime.datetime.utcfromtimestamp(fitDateTime + FIT_EPOCH_S)
```
### convert_timestamp_to_datetime Method
A convenience method for converting FIT Epoch values to Python Datetime objects.
```py
python_date = convert_timestamp_to_datetime(fit_datetime)
```