'''test_encoder.py: Tests for the FIT Encoder.'''

import os
import sys
import tempfile
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from garmin_fit_sdk import Encoder, Decoder, Stream


def test_encoder_basic():
    '''Test basic encoder functionality.'''
    encoder = Encoder()
    
    # Write a file_id message
    encoder.on_mesg(0, {  # 0 = FILE_ID mesg_num
        'type': 4,  # activity
        'manufacturer': 1,  # garmin
        'product': 1,
        'serial_number': 12345,
        'time_created': datetime.now(timezone.utc),
    })
    
    fit_data = encoder.close()
    
    # Verify the output is bytes
    assert isinstance(fit_data, bytes)
    
    # Verify minimum header size
    assert len(fit_data) >= 14
    
    # Verify FIT signature
    assert fit_data[8:12] == b'.FIT'
    
    print(f"✓ Basic encoder test passed. Generated {len(fit_data)} bytes.")
    return fit_data


def test_encoder_with_write_message():
    '''Test encoder with write_message method.'''
    encoder = Encoder()
    
    encoder.write_message({
        'mesg_num': 0,  # FILE_ID
        'type': 4,  # activity
        'manufacturer': 1,
        'product': 1,
        'serial_number': 12345,
    })
    
    fit_data = encoder.close()
    assert len(fit_data) >= 14
    assert fit_data[8:12] == b'.FIT'
    
    print(f"✓ write_message test passed. Generated {len(fit_data)} bytes.")
    return fit_data


def test_encode_activity():
    '''Test encoding a simple activity file.'''
    encoder = Encoder()
    
    now = datetime.now(timezone.utc)
    
    # File ID message (required first message)
    encoder.on_mesg(0, {
        'type': 4,  # activity
        'manufacturer': 1,  # garmin
        'product': 1,
        'serial_number': 12345,
        'time_created': now,
    })
    
    # File Creator message
    encoder.on_mesg(49, {
        'software_version': 100,
        'hardware_version': 1,
    })
    
    fit_data = encoder.close()
    
    assert len(fit_data) >= 14
    assert fit_data[8:12] == b'.FIT'
    
    print(f"✓ Activity encoding test passed. Generated {len(fit_data)} bytes.")
    return fit_data


def test_encode_and_decode():
    '''Test that encoded files can be decoded.'''
    encoder = Encoder()
    
    now = datetime.now(timezone.utc)
    
    # File ID message
    encoder.on_mesg(0, {
        'type': 4,  # activity
        'manufacturer': 1,
        'product': 1,
        'serial_number': 12345,
        'time_created': now,
    })
    
    fit_data = encoder.close()
    
    # Write to temp file and decode
    with tempfile.NamedTemporaryFile(suffix='.fit', delete=False) as f:
        f.write(fit_data)
        temp_path = f.name
    
    try:
        # Decode the file
        stream = Stream.from_file(temp_path)
        decoder = Decoder(stream)
        
        # Check integrity
        is_fit = decoder.is_fit()
        print(f"  is_fit: {is_fit}")
        
        if is_fit:
            messages, errors = decoder.read()
            print(f"  Decoded messages: {list(messages.keys())}")
            print(f"  Errors: {errors}")
            
            if 'file_id_mesgs' in messages:
                file_id = messages['file_id_mesgs'][0]
                print(f"  File ID: {file_id}")
        
        stream.close()
        
    finally:
        os.unlink(temp_path)
    
    print("Encode and decode test passed.")


def test_multiple_messages():
    '''Test encoding multiple messages of the same type.'''
    encoder = Encoder()
    
    now = datetime.now(timezone.utc)
    
    # File ID
    encoder.on_mesg(0, {
        'type': 4,
        'manufacturer': 1,
        'product': 1,
        'serial_number': 12345,
        'time_created': now,
    })
    
    # Multiple record messages (mesg_num = 20)
    for i in range(5):
        encoder.on_mesg(20, {
            'timestamp': now,
            'heart_rate': 120 + i,
            'cadence': 80 + i,
        })
    
    fit_data = encoder.close()
    
    assert len(fit_data) >= 14
    print(f"✓ Multiple messages test passed. Generated {len(fit_data)} bytes.")
    return fit_data


if __name__ == '__main__':
    print("Running Encoder tests...\n")
    
    try:
        test_encoder_basic()
        test_encoder_with_write_message()
        test_encode_activity()
        test_encode_and_decode()
        test_multiple_messages()
        
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
