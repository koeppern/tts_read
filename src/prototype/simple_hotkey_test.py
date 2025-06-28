#!/usr/bin/env python3
"""
Simple keyboard test - works without admin privileges.
"""

import sys
import os
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_keyboard_basic():
    """Test basic keyboard functionality without admin privileges."""
    print("🧪 Basic Keyboard Test")
    print("=" * 40)
    
    try:
        import keyboard
        print("✅ keyboard module imported successfully")
        
        print("\n🔍 Testing keyboard detection (no admin required)...")
        print("Press 'q' to quit this test")
        
        def on_key_event(event):
            if event.event_type == keyboard.KEY_DOWN:
                key_name = event.name
                print(f"🎯 Key detected: {key_name}")
                if key_name == 'q':
                    print("✅ Test completed - 'q' pressed")
                    return False  # Stop the hook
        
        # Hook all keyboard events (works without admin)
        keyboard.hook(on_key_event)
        
        print("🚀 Listening for keystrokes... Press any key (q to quit)")
        keyboard.wait('q')  # Wait until 'q' is pressed
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    print("\n✅ Basic keyboard test completed")

def test_hotkey_detection():
    """Test hotkey detection with better error handling."""
    print("\n🧪 Hotkey Detection Test")
    print("=" * 40)
    
    try:
        import keyboard
        
        def hotkey_callback():
            print(f"🎯 HOTKEY DETECTED: Ctrl+1 at {time.strftime('%H:%M:%S')}")
        
        print("🔧 Registering Ctrl+1 hotkey...")
        try:
            keyboard.add_hotkey('ctrl+1', hotkey_callback)
            print("✅ Hotkey registered successfully")
            
            print("🚀 Press Ctrl+1 to test (press 'esc' to quit)")
            keyboard.wait('esc')
            
        except Exception as e:
            print(f"❌ Hotkey registration failed: {e}")
            if "access" in str(e).lower():
                print("💡 This error suggests admin privileges are needed")
                print("   Try running as administrator")
            
    except Exception as e:
        print(f"❌ Error in hotkey test: {e}")
        
    print("✅ Hotkey test completed")

def main():
    print("🔧 Simple Keyboard & Hotkey Diagnostics")
    print("🔧 This test works step-by-step to identify issues")
    print()
    
    # Test 1: Basic keyboard detection
    test_keyboard_basic()
    
    # Test 2: Hotkey detection
    test_hotkey_detection()
    
    print("\n🎯 All tests completed!")
    print("If hotkey test failed, try running as administrator")

if __name__ == "__main__":
    main() 