#!/usr/bin/env python3
"""
Test script for new features:
1. Available voices display
2. Speed parameter
3. Text selection copying
"""

import sys
import time
from pathlib import Path

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from text_speaker import SAPITextSpeaker
from text_selector import TextSelector
from settings_manager import SettingsManager


def test_available_voices():
    """Test displaying available voices."""
    print("=== Testing Available Voices ===")
    
    speaker = SAPITextSpeaker()
    voices = speaker.get_available_voices()
    
    print(f"Found {len(voices)} available voices:")
    for i, voice in enumerate(voices):
        print(f"   {i+1}. {voice}")
    print()


def test_speed_parameter():
    """Test speed parameter functionality."""
    print("=== Testing Speed Parameter ===")
    
    speaker = SAPITextSpeaker()
    voices = speaker.get_available_voices()
    
    if not voices:
        print("❌ No voices available")
        return
    
    voice_name = voices[0]
    test_text = "Dies ist ein Test der Geschwindigkeits-Kontrolle."
    
    print(f"Using voice: {voice_name}")
    print("Testing different speeds...")
    
    # Test slow speed
    print("\n1. Testing slow speed (0.7)...")
    speaker.speak(test_text, voice_name, 0.7)
    time.sleep(4)
    
    # Test normal speed
    print("2. Testing normal speed (1.0)...")
    speaker.speak(test_text, voice_name, 1.0)
    time.sleep(3)
    
    # Test fast speed
    print("3. Testing fast speed (1.3)...")
    speaker.speak(test_text, voice_name, 1.3)
    time.sleep(3)
    
    speaker.stop()
    print("✅ Speed test complete")


def test_text_selector():
    """Test text selector functionality."""
    print("\n=== Testing Text Selector ===")
    
    selector = TextSelector()
    
    print("Text selector created")
    print("Note: This test cannot automatically select text.")
    print("To test manually:")
    print("1. Select some text in another application")
    print("2. Run the main application")
    print("3. Press CTRL+1 or CTRL+2")
    print("4. The selected text should be copied and spoken")
    
    # Test getting current clipboard
    current_clipboard = selector.get_clipboard_text()
    if current_clipboard:
        print(f"📋 Current clipboard: {current_clipboard[:50]}...")
    else:
        print("📋 Clipboard is empty")


def test_settings_with_speed():
    """Test settings manager with speed parameter."""
    print("\n=== Testing Settings with Speed ===")
    
    settings = SettingsManager()
    
    # Get voice configurations
    voice_configs = settings.settings.get("voices", {})
    
    print("Voice configurations:")
    for hotkey, config in voice_configs.items():
        voice = config.get("voice", "Unknown")
        rate = config.get("rate", 1.0)
        speed = config.get("speed", 1.0)
        combined_speed = rate * speed
        
        print(f"   {hotkey}:")
        print(f"      Voice: {voice}")
        print(f"      Rate: {rate}")
        print(f"      Speed: {speed}")
        print(f"      Combined: {combined_speed}")
        print()


def main():
    """Run all tests."""
    print("🧪 Testing New Features")
    print("=" * 50)
    
    try:
        test_available_voices()
        test_speed_parameter()
        test_text_selector()
        test_settings_with_speed()
        
        print("\n✅ All tests completed!")
        print("\nTo test the text selection feature:")
        print("1. Start the main application: py -3 src/prototype/main.py")
        print("2. Select text in any application")
        print("3. Press CTRL+1 or CTRL+2")
        print("4. The selected text should be copied and spoken")
        
    except Exception as e:
        print(f"❌ Test error: {e}")


if __name__ == "__main__":
    main() 