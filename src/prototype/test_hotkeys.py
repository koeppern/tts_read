#!/usr/bin/env python3
"""Simple test for hotkey functionality."""

import time
from hotkey_listener import HotkeyListener

def on_hotkey1():
    print("Hotkey 1 pressed!")

def on_hotkey2():
    print("Hotkey 2 pressed!")

def main():
    print("Starting hotkey test...")
    
    listener = HotkeyListener()
    
    # Register some test hotkeys
    listener.register_hotkey("ctrl+alt+1", on_hotkey1)
    listener.register_hotkey("ctrl+alt+2", on_hotkey2)
    
    # Start listener
    listener.start()
    
    print("Hotkey listener started.")
    print("Registered hotkeys:")
    for hk in listener.get_registered_hotkeys():
        print(f"  - {hk}")
    
    print("\nPress Ctrl+Alt+1 or Ctrl+Alt+2 to test")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        listener.stop()
        print("Done.")

if __name__ == "__main__":
    main()