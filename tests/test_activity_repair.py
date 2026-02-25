'''test_activity_repair.py: Tests for the ActivityRepairFilter and ActivityRepairTool.'''

import os
import sys
import tempfile
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from garmin_fit_sdk import (
    ActivityRepairFilter, 
    ActivityRepairTool, 
    Encoder, 
    Decoder, 
    Stream
)


def test_activity_repair_filter_basic():
    '''Test basic ActivityRepairFilter functionality.'''
    repair_filter = ActivityRepairFilter()
    
    # Initially should not be able to repair (no messages)
    assert not repair_filter.can_repair_file()
    
    # Add some record messages with valid timestamps
    base_time = 1000000000  # FIT timestamp
    
    for i in range(5):
        repair_filter.on_mesg(20, {  # RECORD message
            'timestamp': base_time + i,
            'heart_rate': 120 + i,
            'cadence': 80,
        })
    
    # Now should be able to repair
    assert repair_filter.can_repair_file()
    
    # Get repaired messages
    repaired = repair_filter.get_repaired_messages()
    
    # Should have: file_id, device_info, 5 records, lap, session, activity = 10
    assert len(repaired) == 10
    
    # Check message types
    mesg_nums = [m[0] for m in repaired]
    assert mesg_nums[0] == 0  # FILE_ID
    assert mesg_nums[1] == 23  # DEVICE_INFO
    assert mesg_nums[2:7] == [20, 20, 20, 20, 20]  # RECORD messages
    assert mesg_nums[7] == 19  # LAP
    assert mesg_nums[8] == 18  # SESSION
    assert mesg_nums[9] == 34  # ACTIVITY
    
    print("✓ ActivityRepairFilter basic test passed")


def test_activity_repair_filter_with_file_id():
    '''Test that existing file_id is preserved.'''
    repair_filter = ActivityRepairFilter()
    
    # Add a file_id message first
    repair_filter.on_mesg(0, {  # FILE_ID
        'type': 4,
        'manufacturer': 1,  # garmin
        'product': 123,
        'serial_number': 999999,
    })
    
    # Add record messages
    base_time = 1000000000
    for i in range(3):
        repair_filter.on_mesg(20, {
            'timestamp': base_time + i,
            'heart_rate': 100,
        })
    
    repaired = repair_filter.get_repaired_messages()
    file_id = repaired[0][1]
    
    # Should preserve original manufacturer and product
    assert file_id.get('manufacturer') == 1
    assert file_id.get('product') == 123
    assert file_id.get('serial_number') == 999999
    
    print("✓ ActivityRepairFilter file_id preservation test passed")


def test_activity_repair_filter_invalid_timestamps():
    '''Test that invalid timestamps are filtered out.'''
    repair_filter = ActivityRepairFilter()
    
    # Add messages with invalid timestamps (None)
    repair_filter.on_mesg(20, {'timestamp': None, 'heart_rate': 100})
    repair_filter.on_mesg(20, {'heart_rate': 100})  # No timestamp
    
    # Should not be able to repair
    assert not repair_filter.can_repair_file()
    
    # Now add valid ones
    repair_filter.on_mesg(20, {'timestamp': 1000000000, 'heart_rate': 100})
    repair_filter.on_mesg(20, {'timestamp': 1000000001, 'heart_rate': 101})
    
    # Now should be able to repair
    assert repair_filter.can_repair_file()
    
    repaired = repair_filter.get_repaired_messages()
    record_mesgs = [m for m in repaired if m[0] == 20]
    assert len(record_mesgs) == 2
    
    print("✓ ActivityRepairFilter invalid timestamp filtering test passed")


def test_activity_repair_filter_non_sequential():
    '''Test that non-sequential timestamps are filtered.'''
    repair_filter = ActivityRepairFilter()
    
    # Add sequential messages
    repair_filter.on_mesg(20, {'timestamp': 1000000000, 'heart_rate': 100})
    repair_filter.on_mesg(20, {'timestamp': 1000000001, 'heart_rate': 101})
    
    # Add a message with earlier timestamp (should be filtered)
    repair_filter.on_mesg(20, {'timestamp': 999999999, 'heart_rate': 99})
    
    # Add another sequential message
    repair_filter.on_mesg(20, {'timestamp': 1000000002, 'heart_rate': 102})
    
    repaired = repair_filter.get_repaired_messages()
    record_mesgs = [m for m in repaired if m[0] == 20]
    
    # Should have 3 records (the non-sequential one is skipped)
    assert len(record_mesgs) == 3
    
    print("✓ ActivityRepairFilter non-sequential filtering test passed")


def test_activity_repair_tool_roundtrip():
    '''Test creating a file, "corrupting" it, and repairing.'''
    # Create a valid activity file
    encoder = Encoder()
    
    now = datetime.now(timezone.utc)
    base_timestamp = 1000000000
    
    # File ID
    encoder.on_mesg(0, {
        'type': 4,
        'manufacturer': 1,
        'product': 1,
        'serial_number': 12345,
        'time_created': base_timestamp,
    })
    
    # Record messages
    for i in range(10):
        encoder.on_mesg(20, {
            'timestamp': base_timestamp + i,
            'heart_rate': 120 + i,
            'cadence': 80,
            'distance': float(i * 100),
        })
    
    fit_data = encoder.close()
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix='.fit', delete=False) as f:
        f.write(fit_data)
        input_path = f.name
    
    try:
        # Repair the file (even though it's valid, repair should work)
        tool = ActivityRepairTool(input_path)
        success = tool.repair(write_to_file=True)
        
        assert success, "Repair should succeed"
        assert os.path.exists(tool.output_file_path), "Output file should exist"
        
        # Verify the repaired file is valid
        stream = Stream.from_file(tool.output_file_path)
        decoder = Decoder(stream)
        
        assert decoder.is_fit(), "Repaired file should be valid FIT"
        
        messages, errors = decoder.read()
        stream.close()
        
        assert len(errors) == 0, f"Should have no errors: {errors}"
        assert 'record_mesgs' in messages, "Should have record messages"
        assert len(messages['record_mesgs']) == 10, "Should have 10 record messages"
        
        # Cleanup
        os.unlink(tool.output_file_path)
        
        print("✓ ActivityRepairTool roundtrip test passed")
        
    finally:
        os.unlink(input_path)


def test_activity_repair_tool_in_memory():
    '''Test repair without writing to file.'''
    # Create a simple activity file
    encoder = Encoder()
    
    base_timestamp = 1000000000
    
    encoder.on_mesg(0, {
        'type': 4,
        'manufacturer': 1,
        'product': 1,
        'serial_number': 12345,
        'time_created': base_timestamp,
    })
    
    for i in range(5):
        encoder.on_mesg(20, {
            'timestamp': base_timestamp + i,
            'heart_rate': 100,
        })
    
    fit_data = encoder.close()
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(suffix='.fit', delete=False) as f:
        f.write(fit_data)
        input_path = f.name
    
    try:
        tool = ActivityRepairTool(input_path)
        success = tool.repair(write_to_file=False)
        
        assert success
        assert tool.repaired_data is not None
        assert len(tool.repaired_data) > 0
        
        # Output file should NOT exist
        assert not os.path.exists(tool.output_file_path)
        
        print("✓ ActivityRepairTool in-memory test passed")
        
    finally:
        os.unlink(input_path)


if __name__ == '__main__':
    print("Running Activity Repair tests...\n")
    
    try:
        test_activity_repair_filter_basic()
        test_activity_repair_filter_with_file_id()
        test_activity_repair_filter_invalid_timestamps()
        test_activity_repair_filter_non_sequential()
        test_activity_repair_tool_roundtrip()
        test_activity_repair_tool_in_memory()
        
        print("\n✓ All Activity Repair tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
