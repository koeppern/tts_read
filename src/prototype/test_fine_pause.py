#!/usr/bin/env python3
"""
Test fine-grained pause functionality with smaller text chunks.
"""

import sys
import time
from pathlib import Path

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from text_speaker import SAPITextSpeaker


def main():
    """Test fine-grained pause/resume functionality."""
    print("=== Fine-Grained Pause/Resume Test ===")
    
    # Create speaker
    speaker = SAPITextSpeaker()
    voices = speaker.get_available_voices()
    
    if not voices:
        print("❌ No voices available")
        return
    
    # Test text with pause tags and longer content
    test_text = """
    Dies ist ein Test für feinere Pause-Kontrolle. [pause] 
    Jetzt sollte eine Pause gewesen sein. Der Text wird in kleinere 
    Wort-Gruppen aufgeteilt für bessere Kontrolle. [pause] 
    Sie können jetzt während jedem kleinen Abschnitt pausieren. 
    Das macht es viel einfacher, genau dann zu pausieren, 
    wenn Sie es möchten. [pause] Probieren Sie es aus!
    """
    
    voice_name = voices[0]
    print(f"Using voice: {voice_name}")
    print("Text with [pause] tags will have extra pauses")
    
    print("\n--- Starting fine-grained speech ---")
    print("Text will be split into small chunks (~6 words each)")
    print("You can pause at any point during speech")
    
    speaker.speak(test_text, voice_name, 0.9)  # Slightly slower
    
    # Let it run and demonstrate auto-pause
    time.sleep(3)
    
    print("\n--- Auto-testing fine pause ---")
    print("Pausing in 2 seconds...")
    time.sleep(2)
    
    speaker.pause()
    print("✅ Paused mid-chunk")
    
    time.sleep(2)
    print("Resuming...")
    speaker.resume()
    print("✅ Resumed from exact position")
    
    # Let it finish
    time.sleep(8)
    speaker.stop()
    
    print("\n=== Fine-Grained Test Complete ===")
    print("You should have been able to pause within sentences!")


if __name__ == "__main__":
    main() 