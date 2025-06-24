#!/usr/bin/env python3
"""Test script to debug the application startup."""

import sys
import traceback

def test_basic_imports():
    """Test basic imports."""
    print("Testing basic imports...")
    try:
        from settings_manager import SettingsManager
        print("✓ SettingsManager imported")
        
        from text_speaker import TextSpeakerFactory
        print("✓ TextSpeakerFactory imported")
        
        from clipboard_reader import ClipboardReader
        print("✓ ClipboardReader imported")
        
        from hotkey_listener import HotkeyListener
        print("✓ HotkeyListener imported")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False

def test_initialization():
    """Test component initialization."""
    print("\nTesting component initialization...")
    try:
        from settings_manager import SettingsManager
        settings = SettingsManager()
        print("✓ SettingsManager initialized")
        
        from clipboard_reader import ClipboardReader
        clipboard = ClipboardReader()
        print("✓ ClipboardReader initialized")
        
        from hotkey_listener import HotkeyListener
        hotkey = HotkeyListener()
        print("✓ HotkeyListener initialized")
        
        from text_speaker import TextSpeakerFactory
        speaker = TextSpeakerFactory.create_speaker("SAPI")
        print("✓ TextSpeaker initialized")
        
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        traceback.print_exc()
        return False

def test_app_creation():
    """Test VorleseApp creation."""
    print("\nTesting VorleseApp creation...")
    try:
        from main import VorleseApp
        app = VorleseApp()
        print("✓ VorleseApp created successfully")
        return True
    except Exception as e:
        print(f"✗ VorleseApp creation failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running diagnostic tests...\n")
    
    if test_basic_imports():
        if test_initialization():
            test_app_creation()
    
    print("\nDiagnostic tests completed.")