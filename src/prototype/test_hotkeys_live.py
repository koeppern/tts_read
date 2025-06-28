#!/usr/bin/env python3
"""
Live hotkey test to verify functionality.
"""

import sys
import os
import time
import ctypes

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotkey_listener import HotkeyListener

def check_admin_privileges():
    """Check if running as administrator on Windows."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def test_callback(hotkey_name):
    """Test callback function."""
    print(f"🎯 HOTKEY TRIGGERED: {hotkey_name} at {time.strftime('%H:%M:%S')}")

def main():
    print("🧪 Hotkey Test Tool")
    print("=" * 50)
    
    # Check admin privileges
    is_admin = check_admin_privileges()
    print(f"👤 Running as administrator: {is_admin}")
    if not is_admin:
        print("⚠️  WARNING: Global hotkeys may not work without admin privileges")
        print("   Try running as administrator for best results")
    
    print()
    
    # Create hotkey listener
    print("🔧 Creating HotkeyListener...")
    listener = HotkeyListener()
    
    # Register test hotkeys
    test_hotkeys = {
        "ctrl+1": "German Voice",
        "ctrl+2": "English Voice", 
        "ctrl+3": "Pause/Resume",
        "win+space": "Show Text Window"
    }
    
    print("\n🎯 Registering test hotkeys...")
    for hotkey, description in test_hotkeys.items():
        success = listener.register_hotkey(
            hotkey, 
            lambda desc=description: test_callback(desc)
        )
        status = "✅" if success else "❌"
        print(f"   {status} {hotkey} -> {description}")
    
    # Start listening
    print("\n🚀 Starting hotkey listener...")
    listener.start()
    
    print("\n" + "=" * 50)
    print("🎯 HOTKEY TEST ACTIVE")
    print("Press the following keys to test:")
    for hotkey, description in test_hotkeys.items():
        print(f"   {hotkey.upper()} -> {description}")
    print("\nPress Ctrl+C to stop the test")
    print("=" * 50)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Test stopped by user")
        
    finally:
        print("🧹 Cleaning up...")
        listener.stop()
        print("✅ Test completed")

if __name__ == "__main__":
    main() 