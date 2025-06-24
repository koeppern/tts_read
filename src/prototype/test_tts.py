#!/usr/bin/env python3
"""Test TTS functionality without user interaction."""

from settings_manager import SettingsManager
from text_speaker import TextSpeakerFactory
from clipboard_reader import ClipboardReader

def test_tts():
    """Test the TTS functionality."""
    print("Testing TTS functionality...")
    
    # Initialize components
    settings_manager = SettingsManager()
    clipboard_reader = ClipboardReader()
    
    # Create a TTS speaker
    speaker = TextSpeakerFactory.create_speaker("SAPI")
    
    # Test text
    test_text = "Hello, this is a test of the text-to-speech system. It should work even in dummy mode."
    
    print(f"Test text: {test_text}")
    
    # Get voice configuration
    voice_config = settings_manager.get_voice_config('ctrl+1')
    if voice_config:
        voice_name = voice_config.get("voice", "Default Voice")
        rate = voice_config.get("rate", 1.0)
        
        print(f"Using voice: {voice_name}, rate: {rate}")
        
        # Speak the text
        speaker.speak(test_text, voice_name, rate)
        
        print("TTS test completed successfully!")
    else:
        print("No voice configuration found.")

if __name__ == "__main__":
    test_tts()