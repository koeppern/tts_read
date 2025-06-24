#!/usr/bin/env python3
"""Simplified TTS app that works in console mode."""

import sys
import time
from settings_manager import SettingsManager
from text_speaker import TextSpeakerFactory
from clipboard_reader import ClipboardReader

class SimpleVorleseApp:
    """Simplified TTS app for testing."""
    
    def __init__(self):
        """Initialize the application."""
        print("Initializing SimpleVorleseApp...")
        self.settings_manager = SettingsManager()
        self.clipboard_reader = ClipboardReader()
        
        # Create text speakers
        self.speakers = {}
        self._init_speakers()
        self._is_running = True
        
    def _init_speakers(self):
        """Initialize text speakers based on configuration."""
        hotkeys = self.settings_manager.get_hotkeys()
        
        for action, hotkey in hotkeys.items():
            if action in ["deSpeak", "enSpeak"]:
                voice_config = self.settings_manager.get_voice_config(hotkey)
                if voice_config:
                    engine_type = voice_config.get("engine", "SAPI")
                    self.speakers[hotkey] = TextSpeakerFactory.create_speaker(engine_type)
                    print(f"Initialized speaker for {action} ({hotkey})")
                    
    def speak_clipboard(self, voice_key: str):
        """Speak clipboard content with specified voice."""
        text = self.clipboard_reader.get_text()
        if not text:
            print("Clipboard is empty")
            return
            
        voice_config = self.settings_manager.get_voice_config(voice_key)
        if not voice_config:
            print(f"No voice configuration for {voice_key}")
            return
            
        speaker = self.speakers.get(voice_key)
        if not speaker:
            print(f"No speaker initialized for {voice_key}")
            return
            
        voice_name = voice_config.get("voice", "")
        rate = voice_config.get("rate", 1.0)
        
        print(f"Speaking text with {voice_name} at rate {rate}")
        print(f"Text preview: {text[:100]}...")
        speaker.speak(text, voice_name, rate)
        
    def run(self):
        """Run the application in console mode."""
        print("\nSimple TTS Vorlese-App is running.")
        print("\nAvailable commands:")
        print("  1 - Speak clipboard with German voice (ctrl+1)")
        print("  2 - Speak clipboard with English voice (ctrl+2)")
        print("  q - Quit")
        print("\nNote: Copy text to clipboard before using speak commands.")
        
        while self._is_running:
            try:
                cmd = input("\nEnter command: ").strip().lower()
                
                if cmd == '1':
                    self.speak_clipboard('ctrl+1')
                elif cmd == '2':
                    self.speak_clipboard('ctrl+2')
                elif cmd == 'q':
                    self._is_running = False
                    print("Exiting...")
                else:
                    print("Unknown command. Use 1, 2, or q.")
                    
            except KeyboardInterrupt:
                self._is_running = False
                print("\nExiting...")
            except Exception as e:
                print(f"Error: {e}")
                
    def cleanup(self):
        """Clean up resources."""
        for speaker in self.speakers.values():
            speaker.stop()

def main():
    """Main entry point."""
    app = SimpleVorleseApp()
    try:
        app.run()
    finally:
        app.cleanup()

if __name__ == "__main__":
    main()