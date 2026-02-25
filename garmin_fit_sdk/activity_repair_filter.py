'''activity_repair_filter.py: Contains the ActivityRepairFilter class for repairing corrupt FIT activity files.'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .util import FIT_EPOCH_S


# Message numbers from Profile
MESG_NUM_FILE_ID = 0
MESG_NUM_SPORT = 12
MESG_NUM_SESSION = 18
MESG_NUM_LAP = 19
MESG_NUM_RECORD = 20
MESG_NUM_DEVICE_INFO = 23
MESG_NUM_ACTIVITY = 34
MESG_NUM_DEVELOPER_DATA_ID = 207
MESG_NUM_FIELD_DESCRIPTION = 206

# Field numbers
FIELD_TIMESTAMP = 253

# DateTime minimum (FIT epoch start: Dec 31, 1989)
DATETIME_MIN = 0

# Two days in seconds for reasonable span check
TWO_DAYS_IN_SECONDS = 172800

# Device index for creator
DEVICE_INDEX_CREATOR = 0


class ActivityRepairFilter:
    '''
    A filter that repairs corrupt or invalid FIT Activity files.
    
    This class processes incoming FIT messages, filters valid record messages,
    and reconstructs a valid activity file structure with proper file_id,
    device_info, lap, session, and activity messages.
    
    Usage:
        filter = ActivityRepairFilter()
        
        # Process messages from decoder
        for mesg_num, mesg in decoded_messages:
            filter.on_mesg(mesg_num, mesg)
        
        # Check if repair is possible
        if filter.can_repair_file():
            repaired_messages = filter.get_repaired_messages()
    '''

    def __init__(self, serial_number: int = 123456789):
        '''
        Initialize the ActivityRepairFilter.
        
        Args:
            serial_number: Serial number to use for device identification.
        '''
        self._serial_number = serial_number
        self._mesg_listeners: List[Callable] = []
        self._filtered_record_mesgs: List[Dict] = []
        self._previous_mesg: Optional[Dict] = None
        self._continue_filtering_record_mesgs = True
        self._continue_checking_for_file_id_mesg = True
        self._file_id_mesg_from_file: Optional[Dict] = None
        
        self._all_messages: Dict[str, List[Dict]] = {
            'record_mesgs': [],
            'device_info_mesgs': [],
            'sport_mesgs': [],
            'lap_mesgs': [],
            'developer_data_id_mesgs': [],
            'field_description_mesgs': [],
        }

    def on_mesg(self, mesg_num: int, mesg: Dict[str, Any]) -> None:
        '''
        Process an incoming message.
        
        Args:
            mesg_num: The message number.
            mesg: The message data dictionary.
        '''
        self._store_message(mesg_num, mesg)
        
        if mesg_num == MESG_NUM_RECORD:
            self._filter_incoming_record_messages()
        
        self._check_for_file_id_mesg(mesg_num, mesg)

    def add_listener(self, mesg_listener: Callable) -> None:
        '''
        Add a message listener.
        
        Args:
            mesg_listener: A callable that receives (mesg_num, mesg) tuples.
        '''
        if mesg_listener is not None and mesg_listener not in self._mesg_listeners:
            self._mesg_listeners.append(mesg_listener)

    def can_repair_file(self) -> bool:
        '''
        Check if the file can be repaired.
        
        Returns:
            True if there are valid record messages to create a repaired file.
        '''
        return len(self._filtered_record_mesgs) > 0

    def flush_mesgs(self) -> None:
        '''
        Flush all repaired messages to registered listeners.
        
        Call this after all messages have been processed to emit the repaired
        activity file structure.
        '''
        if len(self._filtered_record_mesgs) == 0:
            return

        start = self._filtered_record_mesgs[0]
        end = self._filtered_record_mesgs[-1]

        start_time = self._get_timestamp(start)

        # Create required messages
        file_id_mesg = self._create_file_id_mesg(start_time)
        device_info_mesg = self._create_device_info_mesg(start_time)
        lap_mesg = self._create_lap_mesg(start, end)
        session_mesg = self._create_session_mesg(start, end)
        activity_mesg = self._create_activity_mesg(start, end)

        # Flush messages in correct order
        self._flush_mesg(MESG_NUM_FILE_ID, file_id_mesg)
        self._flush_mesg(MESG_NUM_DEVICE_INFO, device_info_mesg)
        
        # Flush developer data
        for mesg in self._all_messages.get('developer_data_id_mesgs', []):
            self._flush_mesg(MESG_NUM_DEVELOPER_DATA_ID, mesg)
        for mesg in self._all_messages.get('field_description_mesgs', []):
            self._flush_mesg(MESG_NUM_FIELD_DESCRIPTION, mesg)
        
        # Flush record messages
        for mesg in self._filtered_record_mesgs:
            self._flush_mesg(MESG_NUM_RECORD, mesg)
        
        # Flush summary messages
        self._flush_mesg(MESG_NUM_LAP, lap_mesg)
        self._flush_mesg(MESG_NUM_SESSION, session_mesg)
        self._flush_mesg(MESG_NUM_ACTIVITY, activity_mesg)

    def get_repaired_messages(self) -> List[tuple]:
        '''
        Get all repaired messages as a list of (mesg_num, mesg) tuples.
        
        Returns:
            List of (mesg_num, mesg) tuples in the correct order.
        '''
        if len(self._filtered_record_mesgs) == 0:
            return []

        messages = []
        
        start = self._filtered_record_mesgs[0]
        end = self._filtered_record_mesgs[-1]
        start_time = self._get_timestamp(start)

        # Create required messages
        file_id_mesg = self._create_file_id_mesg(start_time)
        device_info_mesg = self._create_device_info_mesg(start_time)
        lap_mesg = self._create_lap_mesg(start, end)
        session_mesg = self._create_session_mesg(start, end)
        activity_mesg = self._create_activity_mesg(start, end)

        # Add messages in correct order
        messages.append((MESG_NUM_FILE_ID, file_id_mesg))
        messages.append((MESG_NUM_DEVICE_INFO, device_info_mesg))
        
        for mesg in self._all_messages.get('developer_data_id_mesgs', []):
            messages.append((MESG_NUM_DEVELOPER_DATA_ID, mesg))
        for mesg in self._all_messages.get('field_description_mesgs', []):
            messages.append((MESG_NUM_FIELD_DESCRIPTION, mesg))
        
        for mesg in self._filtered_record_mesgs:
            messages.append((MESG_NUM_RECORD, mesg))
        
        messages.append((MESG_NUM_LAP, lap_mesg))
        messages.append((MESG_NUM_SESSION, session_mesg))
        messages.append((MESG_NUM_ACTIVITY, activity_mesg))

        return messages

    def _store_message(self, mesg_num: int, mesg: Dict) -> None:
        '''Store message by type for later use.'''
        if mesg_num == MESG_NUM_RECORD:
            self._all_messages['record_mesgs'].append(mesg)
        elif mesg_num == MESG_NUM_DEVICE_INFO:
            self._all_messages['device_info_mesgs'].append(mesg)
        elif mesg_num == MESG_NUM_SPORT:
            self._all_messages['sport_mesgs'].append(mesg)
        elif mesg_num == MESG_NUM_LAP:
            self._all_messages['lap_mesgs'].append(mesg)
        elif mesg_num == MESG_NUM_DEVELOPER_DATA_ID:
            self._all_messages['developer_data_id_mesgs'].append(mesg)
        elif mesg_num == MESG_NUM_FIELD_DESCRIPTION:
            self._all_messages['field_description_mesgs'].append(mesg)

    def _check_for_file_id_mesg(self, mesg_num: int, mesg: Dict) -> None:
        '''Check for and store the file_id message from the original file.'''
        if not self._continue_checking_for_file_id_mesg:
            return

        # Skip pad messages
        if mesg_num == 105:  # PAD message number
            return

        if mesg_num == MESG_NUM_FILE_ID:
            self._file_id_mesg_from_file = mesg.copy()

        self._continue_checking_for_file_id_mesg = False

    def _filter_incoming_record_messages(self) -> None:
        '''Filter incoming record messages for valid timestamps and sequence.'''
        if not self._continue_filtering_record_mesgs:
            return

        record_mesgs = self._all_messages['record_mesgs']
        if len(record_mesgs) == 0:
            return
            
        current_mesg = record_mesgs[-1]

        if not self._has_valid_timestamp(current_mesg):
            return

        if len(self._filtered_record_mesgs) == 0:
            self._filtered_record_mesgs.append(current_mesg)
            self._previous_mesg = current_mesg
            return

        if not self._is_sequential(self._previous_mesg, current_mesg):
            return

        if not self._is_reasonable_span(self._previous_mesg, current_mesg):
            self._continue_filtering_record_mesgs = False
            return

        self._filtered_record_mesgs.append(current_mesg)
        self._previous_mesg = current_mesg

    def _create_file_id_mesg(self, time_created: int) -> Dict:
        '''Create a file_id message.'''
        file_id_mesg = self._file_id_mesg_from_file.copy() if self._file_id_mesg_from_file else {}

        if not file_id_mesg:
            file_id_mesg = {
                'type': 4,  # activity
                'product': 0,
                'serial_number': self._serial_number,
            }

        if file_id_mesg.get('manufacturer') is None:
            file_id_mesg['manufacturer'] = 255  # development

        if file_id_mesg.get('time_created') is None:
            file_id_mesg['time_created'] = time_created

        return file_id_mesg

    def _create_device_info_mesg(self, start_time: int) -> Dict:
        '''Create a device_info message.'''
        # Try to find existing creator device info
        device_info_mesgs = self._all_messages.get('device_info_mesgs', [])
        
        for mesg in device_info_mesgs:
            device_index = mesg.get('device_index')
            if device_index is not None and device_index == DEVICE_INDEX_CREATOR:
                result = mesg.copy()
                if result.get('timestamp') is None:
                    result['timestamp'] = start_time
                return result

        # Create new device info
        return {
            'device_index': DEVICE_INDEX_CREATOR,
            'manufacturer': 255,  # development
            'product': 0,
            'product_name': 'Activity Repair',
            'serial_number': self._serial_number,
            'software_version': 1.0,
            'timestamp': start_time,
        }

    def _create_lap_mesg(self, start: Dict, end: Dict) -> Dict:
        '''Create a lap message.'''
        start_time = self._get_timestamp(start)
        end_time = self._get_timestamp(end)
        elapsed_time = float(end_time - start_time)

        lap_mesg = {
            'message_index': 0,
            'start_time': start_time,
            'timestamp': end_time,
            'total_elapsed_time': elapsed_time,
            'total_timer_time': elapsed_time,
        }

        distance = end.get('distance')
        if distance is not None:
            lap_mesg['total_distance'] = distance

        return lap_mesg

    def _create_session_mesg(self, start: Dict, end: Dict) -> Dict:
        '''Create a session message.'''
        start_time = self._get_timestamp(start)
        end_time = self._get_timestamp(end)
        elapsed_time = float(end_time - start_time)

        session_mesg = {
            'message_index': 0,
            'start_time': start_time,
            'timestamp': end_time,
            'total_elapsed_time': elapsed_time,
            'total_timer_time': elapsed_time,
            'first_lap_index': 0,
            'num_laps': 1,
        }

        # Try to get sport from sport messages
        sport_mesgs = self._all_messages.get('sport_mesgs', [])
        for mesg in sport_mesgs:
            sport = mesg.get('sport')
            sub_sport = mesg.get('sub_sport')
            if sport is not None and sub_sport is not None:
                session_mesg['sport'] = sport
                session_mesg['sub_sport'] = sub_sport
                return session_mesg

        # Try to get sport from lap messages
        lap_mesgs = self._all_messages.get('lap_mesgs', [])
        for mesg in lap_mesgs:
            sport = mesg.get('sport')
            sub_sport = mesg.get('sub_sport')
            if sport is not None and sub_sport is not None:
                session_mesg['sport'] = sport
                session_mesg['sub_sport'] = sub_sport
                return session_mesg

        # Default to generic
        session_mesg['sport'] = 0  # generic
        session_mesg['sub_sport'] = 0  # generic

        return session_mesg

    def _create_activity_mesg(self, start: Dict, end: Dict) -> Dict:
        '''Create an activity message.'''
        start_time = self._get_timestamp(start)
        end_time = self._get_timestamp(end)
        elapsed_time = float(end_time - start_time)

        # Get timezone offset
        try:
            now = datetime.now(timezone.utc).astimezone()
            timezone_offset = int(now.utcoffset().total_seconds())
        except Exception:
            timezone_offset = 0

        return {
            'timestamp': end_time,
            'num_sessions': 1,
            'local_timestamp': end_time + timezone_offset,
            'total_timer_time': elapsed_time,
        }

    def _has_valid_timestamp(self, mesg: Dict) -> bool:
        '''Check if message has a valid timestamp.'''
        timestamp = mesg.get('timestamp')
        if timestamp is None:
            return False
        
        # Handle datetime objects
        if isinstance(timestamp, datetime):
            return True
        
        # Handle numeric timestamps
        if isinstance(timestamp, (int, float)):
            return timestamp >= DATETIME_MIN
        
        return False

    def _get_timestamp(self, mesg: Dict) -> int:
        '''Get timestamp value from message as FIT epoch integer.'''
        timestamp = mesg.get('timestamp')
        
        if timestamp is None:
            return 0
        
        if isinstance(timestamp, datetime):
            # Convert datetime to FIT timestamp
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            return int(timestamp.timestamp()) - FIT_EPOCH_S
        
        if isinstance(timestamp, (int, float)):
            return int(timestamp)
        
        return 0

    def _is_sequential(self, previous_mesg: Dict, current_mesg: Dict) -> bool:
        '''Check if current message timestamp is sequential (not before previous).'''
        prev_time = self._get_timestamp(previous_mesg)
        curr_time = self._get_timestamp(current_mesg)
        return prev_time <= curr_time

    def _is_reasonable_span(self, previous_mesg: Dict, current_mesg: Dict) -> bool:
        '''Check if time span between messages is reasonable (less than 2 days).'''
        prev_time = self._get_timestamp(previous_mesg)
        curr_time = self._get_timestamp(current_mesg)
        return curr_time < prev_time + TWO_DAYS_IN_SECONDS

    def _flush_mesg(self, mesg_num: int, mesg: Dict) -> None:
        '''Flush a message to all registered listeners.'''
        for listener in self._mesg_listeners:
            listener(mesg_num, mesg)
