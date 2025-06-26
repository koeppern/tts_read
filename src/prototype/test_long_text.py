#!/usr/bin/env python3
"""
Test with longer text to verify pause/resume works with multiple sentences.
"""

import sys
import time
from pathlib import Path

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from text_speaker import SAPITextSpeaker


def main():
    """Test pause/resume with longer text."""
    print("=== Long Text Pause/Resume Test ===")
    
    # Create speaker
    speaker = SAPITextSpeaker()
    voices = speaker.get_available_voices()
    
    if not voices:
        print("❌ No voices available")
        return
    
    # Longer test text with multiple sentences and parts
    long_text = """
    Willkommen zu diesem ausführlichen Test der Text-zu-Sprache-Funktionalität. 
    Diese Anwendung kann deutschen Text vorlesen und dabei pausiert werden.
    Der Text wird in mehrere Teile aufgeteilt, um eine bessere Kontrolle zu ermöglichen.
    Jeder Satz wird einzeln gesprochen, so dass Sie jederzeit pausieren können.
    Dies ist besonders nützlich für längere Texte oder Dokumente.
    Sie können die Wiedergabe jederzeit mit STRG+3 pausieren und wieder fortsetzen.
    Die Anwendung merkt sich die Position und setzt genau dort fort, wo sie pausiert wurde.
    Das ist eine sehr praktische Funktion für das Vorlesen von Artikeln oder E-Mails.
    Probieren Sie es aus, indem Sie während der Wiedergabe pausieren und wieder fortsetzen.
    """
    
    voice_name = voices[0]
    print(f"Using voice: {voice_name}")
    print(f"Text length: {len(long_text)} characters")
    
    print("\n--- Starting long text speech ---")
    print("You have about 30-40 seconds to test pause/resume")
    print("The text will be split into multiple parts for better control")
    
    speaker.speak(long_text, voice_name, 0.8)  # Slower speed for testing
    
    # Let it run for a while
    time.sleep(5)
    
    print("\n--- Auto-testing pause/resume ---")
    print("Pausing in 2 seconds...")
    time.sleep(2)
    
    speaker.pause()
    print("✅ Paused - you should hear silence now")
    
    time.sleep(3)
    print("Resuming...")
    speaker.resume()
    print("✅ Resumed - speech should continue")
    
    # Let it finish
    time.sleep(10)
    speaker.stop()
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    main() 