import sys
import os
import subprocess
from pathlib import Path
import platform
try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except (ImportError, ValueError):
    PYSTRAY_AVAILABLE = False
from threading import Thread
import time

from settings_manager import SettingsManager
from text_speaker import TextSpeakerFactory
from clipboard_reader import ClipboardReader
from hotkey_listener import HotkeyListener


class VorleseApp:
    """Main application class for the TTS hotkey app."""
    
    def __init__(self):
        """Initialize the application."""
        print("Initializing VorleseApp...")
        self.settings_manager = SettingsManager()
        print("Settings manager created")
        self.clipboard_reader = ClipboardReader()
        print("Clipboard reader created")
        self.hotkey_listener = HotkeyListener()
        print("Hotkey listener created")
        
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
        print(f"Detected hotkey: {hotkey}")
        
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
        print("Detected pause/resume hotkey")
        
        # Check if any speaker is currently speaking (not paused)
        active_speaker = None
        paused_speaker = None
        
        for speaker in self.speakers.values():
            if speaker.is_speaking():
                active_speaker = speaker
                break
            elif hasattr(speaker, '_is_paused') and speaker._is_paused:
                paused_speaker = speaker
                
        if active_speaker:
            # Pause the active speaker
            active_speaker.pause()
            print("Speech paused")
        elif paused_speaker:
            # Resume the paused speaker
            paused_speaker.resume()
            print("Speech resumed")
        else:
            print("No active or paused speech found")
            
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
        if PYSTRAY_AVAILABLE:
            return pystray.Menu(
                pystray.MenuItem("Einstellungen öffnen", self._open_settings),
                pystray.MenuItem("Beenden", self._quit_app)
            )
        return None
        
    def run(self):
        """Run the application."""
        print("Starting Vorlese-App...")
        
        # Register hotkeys
        self._register_hotkeys()
        
        # Start hotkey listener
        self.hotkey_listener.start()
        
        print("TTS Vorlese-App is running.")
        print("Hotkeys registered:")
        for hotkey in self.hotkey_listener.get_registered_hotkeys():
            print(f"  - {hotkey}")
        
        # Check if we can use system tray
        use_tray = PYSTRAY_AVAILABLE and platform.system() == "Windows"
        
        if use_tray:
            # Create and run system tray icon
            icon_image = self._create_tray_icon()
            self.icon = pystray.Icon(
                "VorleseApp",
                icon_image,
                "Vorlese-App",
                menu=self._create_menu()
            )
            print("Check system tray for icon.")
            # Run icon (this blocks)
            self.icon.run()
        else:
            # Run without system tray
            print("\nRunning in console mode (no system tray).")
            print("Press Ctrl+C to exit.")
            try:
                while self._is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self._is_running = False
        
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