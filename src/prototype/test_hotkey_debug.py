#!/usr/bin/env python3
"""
Debug script to test hotkey detection.
This will help us see if the hotkeys are being registered and detected.
"""

import sys
import time
from pathlib import Path

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from hotkey_listener import HotkeyListener


def test_hotkey_detection():
    """Test if hotkeys are being detected."""
    print("=== Hotkey Detection Test ===")
    
    listener = HotkeyListener()
    
    def on_ctrl_1():
        print("🔥 CTRL+1 detected!")
    
    def on_ctrl_2():
        print("🔥 CTRL+2 detected!")
    
    def on_ctrl_3():
        print("🔥 CTRL+3 detected!")
    
    print("Registering hotkeys...")
    
    success1 = listener.register_hotkey("ctrl+1", on_ctrl_1)
    success2 = listener.register_hotkey("ctrl+2", on_ctrl_2)
    success3 = listener.register_hotkey("ctrl+3", on_ctrl_3)
    
    print(f"CTRL+1 registration: {'✅ Success' if success1 else '❌ Failed'}")
    print(f"CTRL+2 registration: {'✅ Success' if success2 else '❌ Failed'}")
    print(f"CTRL+3 registration: {'✅ Success' if success3 else '❌ Failed'}")
    
    print(f"Registered hotkeys: {listener.get_registered_hotkeys()}")
    
    if listener._dummy_mode:
        print("⚠️ WARNING: Running in dummy mode - hotkeys won't work!")
        print("This means the keyboard module is not available or you're on Linux.")
        return
    
    print("\nStarting hotkey listener...")
    listener.start()
    
    print("🎯 Press CTRL+1, CTRL+2, or CTRL+3 to test hotkey detection")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        listener.stop()


if __name__ == "__main__":
    test_hotkey_detection()