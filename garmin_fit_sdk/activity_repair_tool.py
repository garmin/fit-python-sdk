'''activity_repair_tool.py: Contains the ActivityRepairTool class for repairing corrupt FIT activity files.'''

###########################################################################################
# Copyright 2026 Garmin International, Inc.
# Licensed under the Flexible and Interoperable Data Transfer (FIT) Protocol License; you
# may not use this file except in compliance with the Flexible and Interoperable Data
# Transfer (FIT) Protocol License.
###########################################################################################


import os
import sys
from typing import Optional

from .activity_repair_filter import ActivityRepairFilter


class ActivityRepairTool:
    '''
    A tool for repairing corrupt or invalid FIT Activity files.
    
    This tool reads a potentially corrupt FIT file, extracts valid record
    messages, and creates a new valid FIT activity file with proper structure.
    
    Usage:
        tool = ActivityRepairTool('corrupt_activity.fit')
        tool.repair()
        # Output file will be at 'corrupt_activity_repaired.fit'
        
    Or programmatically:
        tool = ActivityRepairTool('corrupt_activity.fit')
        if tool.repair():
            repaired_data = tool.get_repaired_data()
    '''

    def __init__(self, input_file_path: str, output_file_path: Optional[str] = None):
        '''
        Initialize the ActivityRepairTool.
        
        Args:
            input_file_path: Path to the input FIT file to repair.
            output_file_path: Optional path for the output file. 
                              Defaults to input_file_path with '_repaired' suffix.
        '''
        self._input_file_path = input_file_path
        self._output_file_path = output_file_path or self._create_output_file_path()
        self._repaired_data: Optional[bytes] = None
        self._repair_filter: Optional[ActivityRepairFilter] = None

    @property
    def output_file_path(self) -> str:
        '''Get the output file path.'''
        return self._output_file_path

    @property
    def repaired_data(self) -> Optional[bytes]:
        '''Get the repaired FIT file data as bytes.'''
        return self._repaired_data

    def repair(self, write_to_file: bool = True) -> bool:
        '''
        Repair the FIT activity file.
        
        Args:
            write_to_file: If True, write the repaired file to disk.
                          If False, only store in memory (access via repaired_data).
        
        Returns:
            True if repair was successful, False otherwise.
        '''
        from .decoder import Decoder
        from .encoder import Encoder
        from .stream import Stream
        
        self._repair_filter = ActivityRepairFilter()

        try:
            stream = Stream.from_file(self._input_file_path)
            decoder = Decoder(stream)
            
            def mesg_listener(mesg_num: int, mesg: dict):
                self._repair_filter.on_mesg(mesg_num, mesg)
            
            try:
                decoder.read(
                    mesg_listener=mesg_listener,
                    apply_scale_and_offset=False,
                    convert_datetimes_to_dates=False,
                    convert_types_to_strings=False,
                    expand_sub_fields=False,
                    expand_components=False,
                    merge_heart_rates=False,
                    enable_crc_check=False,  # Disable CRC check for corrupt files
                )
            except Exception as e:
                print(f"Error while decoding file: {e}. Attempting to repair file...")
            finally:
                stream.close()
                
        except Exception as e:
            print(f"Error opening input file: {e}")
            return False

        if not self._repair_filter.can_repair_file():
            print("File cannot be repaired. No valid record messages found.")
            return False

        try:
            encoder = Encoder()
            
            repaired_messages = self._repair_filter.get_repaired_messages()
            for mesg_num, mesg in repaired_messages:
                encoder.on_mesg(mesg_num, mesg)
            
            self._repaired_data = encoder.close()
            
            if write_to_file:
                if os.path.exists(self._output_file_path):
                    os.remove(self._output_file_path)
                
                with open(self._output_file_path, 'wb') as f:
                    f.write(self._repaired_data)
                
                print(f"Repair complete. Repaired .fit file can be found at: {self._output_file_path}")
            
            return True
            
        except Exception as e:
            print(f"Error in repair: {e}")
            return False

    def get_repaired_data(self) -> Optional[bytes]:
        '''
        Get the repaired FIT file data.
        
        Returns:
            The repaired FIT file as bytes, or None if repair hasn't been run.
        '''
        return self._repaired_data

    def _create_output_file_path(self) -> str:
        '''Create the output file path from the input file path.'''
        base, ext = os.path.splitext(self._input_file_path)
        return f"{base}_repaired{ext}"


def main():
    '''Command-line interface for the ActivityRepairTool.'''
    if len(sys.argv) != 2:
        print("Usage: python -m garmin_fit_sdk.activity_repair_tool <filename>")
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Input file does not exist: {input_file}")
        sys.exit(1)

    if not input_file.lower().endswith('.fit'):
        print(f"Input file is not a .fit file: {input_file}")
        sys.exit(1)

    tool = ActivityRepairTool(input_file)
    success = tool.repair()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()