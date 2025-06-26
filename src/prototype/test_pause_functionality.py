#!/usr/bin/env python3
"""
Test script for pause/resume functionality.
This script tests the new pause and resume features of the TTS system.
"""

import sys
import time
from pathlib import Path

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from text_speaker import SAPITextSpeaker


def test_pause_resume():
    """Test the pause and resume functionality."""
    print("=== Testing Pause/Resume Functionality ===")
    
    # Create a speaker instance
    speaker = SAPITextSpeaker()
    
    # Test text - long enough to allow for pausing
    test_text = """
    Dies ist ein Test der Pause- und Fortsetzungsfunktion. 
    Dieser Text ist lang genug, um das Pausieren und Fortsetzen zu testen.
    Es gibt mehrere Sätze in diesem Text.
    Jeder Satz sollte einzeln gesprochen werden können.
    Das ermöglicht es uns, an beliebigen Stellen zu pausieren.
    Und dann von genau dieser Stelle aus fortzusetzen.
    Dies ist eine wichtige Funktion für die Benutzerfreundlichkeit.
    """
    
    print("Available voices:")
    voices = speaker.get_available_voices()
    for i, voice in enumerate(voices[:5]):  # Show first 5 voices
        print(f"  {i+1}. {voice}")
    
    if not voices:
        print("No voices available!")
        return
    
    # Use first available voice
    voice_name = voices[0]
    print(f"\nUsing voice: {voice_name}")
    
    print("\n--- Test 1: Basic Pause and Resume ---")
    print("Starting speech...")
    speaker.speak(test_text, voice_name, 1.0)
    
    # Let it speak for a few seconds
    time.sleep(3)
    
    print("Pausing speech...")
    speaker.pause()
    
    # Verify it's paused
    print(f"Is speaking: {speaker.is_speaking()}")
    print(f"Is paused: {getattr(speaker, '_is_paused', False)}")
    
    # Wait a bit while paused
    print("Waiting 2 seconds while paused...")
    time.sleep(2)
    
    print("Resuming speech...")
    speaker.resume()
    
    # Let it finish or continue for a bit
    time.sleep(3)
    
    print("Stopping speech...")
    speaker.stop()
    
    print("\n--- Test 2: Multiple Pause/Resume Cycles ---")
    print("Starting speech again...")
    speaker.speak(test_text, voice_name, 1.2)  # Slightly faster
    
    for i in range(3):
        time.sleep(2)
        print(f"Pause cycle {i+1}/3")
        speaker.pause()
        time.sleep(1)
        speaker.resume()
    
    # Let it finish
    time.sleep(2)
    speaker.stop()
    
    print("\n--- Test 3: Sentence Splitting ---")
    sentences = speaker._split_into_sentences(test_text)
    print(f"Text split into {len(sentences)} sentences:")
    for i, sentence in enumerate(sentences):
        print(f"  {i+1}. {sentence.strip()}")
    
    print("\n=== Test Complete ===")


def interactive_test():
    """Interactive test where user can control pause/resume."""
    print("=== Interactive Pause/Resume Test ===")
    print("Commands:")
    print("  s - Start speaking")
    print("  p - Pause")
    print("  r - Resume")
    print("  t - Stop")
    print("  q - Quit")
    
    speaker = SAPITextSpeaker()
    voices = speaker.get_available_voices()
    
    if not voices:
        print("No voices available!")
        return
    
    voice_name = voices[0]
    test_text = """
    Willkommen zum interaktiven Test der Sprachausgabe.
    Sie können die Wiedergabe jederzeit pausieren und fortsetzen.
    Verwenden Sie die Befehle p für Pause und r für Fortsetzung.
    Dieser Text ist lang genug für ausgiebige Tests.
    Probieren Sie verschiedene Kombinationen aus.
    Die Pause-Funktion sollte jetzt korrekt funktionieren.
    """
    
    print(f"Using voice: {voice_name}")
    print("Ready for commands...")
    
    while True:
        try:
            cmd = input("\nCommand (s/p/r/t/q): ").lower().strip()
            
            if cmd == 's':
                print("Starting speech...")
                speaker.speak(test_text, voice_name, 1.0)
            elif cmd == 'p':
                print("Pausing...")
                speaker.pause()
                print(f"Status - Speaking: {speaker.is_speaking()}, Paused: {getattr(speaker, '_is_paused', False)}")
            elif cmd == 'r':
                print("Resuming...")
                speaker.resume()
                print(f"Status - Speaking: {speaker.is_speaking()}, Paused: {getattr(speaker, '_is_paused', False)}")
            elif cmd == 't':
                print("Stopping...")
                speaker.stop()
            elif cmd == 'q':
                print("Quitting...")
                speaker.stop()
                break
            else:
                print("Unknown command!")
                
        except KeyboardInterrupt:
            print("\nQuitting...")
            speaker.stop()
            break


def main():
    """Main test function."""
    print("TTS Pause/Resume Functionality Test")
    print("====================================")
    
    test_mode = input("Choose test mode:\n1. Automatic test\n2. Interactive test\nChoice (1/2): ").strip()
    
    if test_mode == "1":
        test_pause_resume()
    elif test_mode == "2":
        interactive_test()
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()