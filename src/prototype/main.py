import sys
import os
import subprocess
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
from threading import Thread

from settings_manager import SettingsManager
from text_speaker import TextSpeakerFactory
from clipboard_reader import ClipboardReader
from hotkey_listener import HotkeyListener


class VorleseApp:
    """Main application class for the TTS hotkey app."""
    
    def __init__(self):
        """Initialize the application."""
        self.settings_manager = SettingsManager()
        self.clipboard_reader = ClipboardReader()
        self.hotkey_listener = HotkeyListener()
        
        # Create text speakers for each configured voice
        self.speakers = {}
        self._init_speakers()
        
        # System tray icon
        self.icon = None
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
                    
    def _create_tray_icon(self):
        """Create a simple placeholder icon for the system tray."""
        # Create a simple icon (white circle on blue background)
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        return image
        
    def _on_speak_hotkey(self, hotkey: str):
        """Handle speak hotkey press."""
        # Get clipboard text
        text = self.clipboard_reader.get_clipboard_text()
        if not text:
            print("No text in clipboard")
            return
            
        # Get voice configuration
        voice_config = self.settings_manager.get_voice_config(hotkey)
        if not voice_config:
            print(f"No voice configuration for {hotkey}")
            return
            
        # Get speaker
        speaker = self.speakers.get(hotkey)
        if not speaker:
            print(f"No speaker initialized for {hotkey}")
            return
            
        # Speak the text
        voice_name = voice_config.get("voice", "")
        rate = voice_config.get("rate", 1.0)
        
        print(f"Speaking text with {voice_name} at rate {rate}")
        speaker.speak(text, voice_name, rate)
        
    def _on_pause_resume_hotkey(self):
        """Handle pause/resume hotkey press."""
        # Find active speaker
        for speaker in self.speakers.values():
            if speaker.is_speaking():
                speaker.pause()
                print("Speech paused")
                return
                
        # If no speaker is active, try to resume
        for speaker in self.speakers.values():
            speaker.resume()
            print("Speech resumed")
            break
            
    def _register_hotkeys(self):
        """Register all configured hotkeys."""
        hotkeys = self.settings_manager.get_hotkeys()
        
        # Register speak hotkeys
        for action, hotkey in hotkeys.items():
            if action == "deSpeak":
                self.hotkey_listener.register_hotkey(
                    hotkey, 
                    lambda h=hotkey: self._on_speak_hotkey(h)
                )
            elif action == "enSpeak":
                self.hotkey_listener.register_hotkey(
                    hotkey,
                    lambda h=hotkey: self._on_speak_hotkey(h)
                )
            elif action == "pauseResume":
                self.hotkey_listener.register_hotkey(
                    hotkey,
                    self._on_pause_resume_hotkey
                )
                
    def _open_settings(self):
        """Open settings file in default text editor."""
        settings_path = self.settings_manager.get_settings_path()
        if sys.platform == "win32":
            os.startfile(str(settings_path))
        else:
            subprocess.run(["xdg-open", str(settings_path)])
            
    def _quit_app(self):
        """Quit the application."""
        self._is_running = False
        if self.icon:
            self.icon.stop()
            
    def _create_menu(self):
        """Create system tray menu."""
        return pystray.Menu(
            pystray.MenuItem("Einstellungen öffnen", self._open_settings),
            pystray.MenuItem("Beenden", self._quit_app)
        )
        
    def run(self):
        """Run the application."""
        print("Starting Vorlese-App...")
        
        # Register hotkeys
        self._register_hotkeys()
        
        # Start hotkey listener
        self.hotkey_listener.start()
        
        # Create and run system tray icon
        icon_image = self._create_tray_icon()
        self.icon = pystray.Icon(
            "VorleseApp",
            icon_image,
            "Vorlese-App",
            menu=self._create_menu()
        )
        
        print("App is running. Check system tray for icon.")
        print("Hotkeys registered:")
        for hotkey in self.hotkey_listener.get_registered_hotkeys():
            print(f"  - {hotkey}")
            
        # Run icon (this blocks)
        self.icon.run()
        
    def cleanup(self):
        """Clean up resources."""
        self.hotkey_listener.stop()
        for speaker in self.speakers.values():
            speaker.stop()
            

def main():
    """Main entry point."""
    app = VorleseApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        app.cleanup()
        

if __name__ == "__main__":
    main()