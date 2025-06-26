#!/usr/bin/env python3
"""
Simple test for pause/resume functionality.
Run this to verify the improvements work correctly.
"""

import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from text_speaker import SAPITextSpeaker
    print("✓ Successfully imported SAPITextSpeaker")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def main():
    """Simple test of pause/resume functionality."""
    print("=== Simple Pause/Resume Test ===")
    
    # Create speaker
    try:
        speaker = SAPITextSpeaker()
        print("✓ Speaker created successfully")
    except Exception as e:
        print(f"✗ Error creating speaker: {e}")
        return
    
    # Get voices
    try:
        voices = speaker.get_available_voices()
        print(f"✓ Found {len(voices)} voices")
        if voices:
            print(f"  Using: {voices[0]}")
        else:
            print("✗ No voices available")
            return
    except Exception as e:
        print(f"✗ Error getting voices: {e}")
        return
    
    # Test text
    test_text = """
    Hallo, dies ist ein Test der Pause-Funktion.
    Dieser Text sollte gesprochen werden.
    Dann wird er pausiert.
    Und dann wieder fortgesetzt.
    Das ist ein wichtiger Test.
    """
    
    voice_name = voices[0]
    
    print("\n--- Starting Test ---")
    print("1. Starting speech...")
    
    try:
        speaker.speak(test_text, voice_name, 1.0)
        print("✓ Speech started")
    except Exception as e:
        print(f"✗ Error starting speech: {e}")
        return
    
    # Wait a bit
    print("2. Waiting 2 seconds...")
    time.sleep(2)
    
    # Pause
    print("3. Pausing...")
    try:
        speaker.pause()
        print(f"✓ Paused. Status: Speaking={speaker.is_speaking()}, Paused={getattr(speaker, '_is_paused', False)}")
    except Exception as e:
        print(f"✗ Error pausing: {e}")
        return
    
    # Wait while paused
    print("4. Waiting 2 seconds while paused...")
    time.sleep(2)
    
    # Resume
    print("5. Resuming...")
    try:
        speaker.resume()
        print(f"✓ Resumed. Status: Speaking={speaker.is_speaking()}, Paused={getattr(speaker, '_is_paused', False)}")
    except Exception as e:
        print(f"✗ Error resuming: {e}")
        return
    
    # Wait to finish
    print("6. Letting it finish...")
    time.sleep(3)
    
    # Stop
    print("7. Stopping...")
    try:
        speaker.stop()
        print("✓ Stopped successfully")
    except Exception as e:
        print(f"✗ Error stopping: {e}")
    
    print("\n=== Test Complete ===")
    print("If you heard the speech pause and resume correctly, the fix works!")

if __name__ == "__main__":
    main() 