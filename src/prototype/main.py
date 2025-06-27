import sys
import os
import subprocess
from pathlib import Path
import platform
import signal
import threading
try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except (ImportError, ValueError):
    PYSTRAY_AVAILABLE = False
from threading import Thread
import time

from settings_manager import SettingsManager
from text_speaker_v2 import TextSpeakerFactory, startup_cleanup, kill_previous_instances_fast, cleanup_all_speech_threads
from clipboard_reader import ClipboardReader
from hotkey_listener import HotkeyListener
from text_selector import TextSelector

# Global flag for graceful shutdown
_shutdown_requested = False

def signal_handler(signum, frame):
	"""Handle system signals for graceful shutdown."""
	global _shutdown_requested
	print(f"\n📡 Received signal {signum} - initiating graceful shutdown...")
	_shutdown_requested = True

# Register signal handlers
if hasattr(signal, 'SIGTERM'):
	signal.signal(signal.SIGTERM, signal_handler)
if hasattr(signal, 'SIGINT'):
	signal.signal(signal.SIGINT, signal_handler)

class VorleseApp:
    """Main application class for the TTS hotkey app."""
    
    def __init__(self):
        """Initialize the application."""
        print("Initializing VorleseApp...")
        
        # First, cleanup any previous instances and threads
        startup_cleanup()
        
        self.settings_manager = SettingsManager()
        print("Settings manager created")
        self.clipboard_reader = ClipboardReader()
        print("Clipboard reader created")
        self.text_selector = TextSelector()
        print("Text selector created")
        self.hotkey_listener = HotkeyListener()
        print("Hotkey listener created")
        
        # Create text speakers for each configured voice
        self.speakers = {}
        self._init_speakers()
        
        # System tray icon
        self.icon = None
        self._is_running = True
        
        # Register cleanup on exit
        import atexit
        atexit.register(self.cleanup)
        
    def _init_speakers(self):
        """Initialize text speakers based on configuration."""
        # Print available SAPI voices on startup
        print("🔊 Available SAPI Voices (NBSapi):")
        temp_speaker = TextSpeakerFactory.create_speaker("SAPI")
        available_voices = temp_speaker.get_available_voices()
        for i, voice in enumerate(available_voices):
            print(f"   {i+1}. {voice}")
        print()
        
        # Print current configuration
        self.settings_manager.print_configuration()
        
        # Initialize speakers for enabled actions
        enabled_actions = self.settings_manager.get_enabled_actions()
        for action, action_config in enabled_actions.items():
            engine_type = action_config.get("engine", "SAPI")
            self.speakers[action] = TextSpeakerFactory.create_speaker(engine_type)
            print(f"✅ Initialized NBSapi speaker for {action} ({action_config.get('name', 'Unnamed')})")
            
        # Cleanup temp speaker
        temp_speaker.cleanup()
                    
    def _create_tray_icon(self):
        """Create a simple placeholder icon for the system tray."""
        # Create a simple icon (white circle on blue background)
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        return image
        
    def _on_speak_hotkey(self, hotkey: str):
        """Handle speak hotkey press."""
        print(f"🔥 HOTKEY PRESSED: {hotkey} (speak)")
        
        # Get action for this hotkey
        action = self.settings_manager.get_action_for_hotkey(hotkey)
        if not action:
            print(f"❌ No action mapped to hotkey {hotkey}")
            return
            
        # Get action configuration
        action_config = self.settings_manager.get_action_config(action)
        if not action_config:
            print(f"❌ No configuration for action {action}")
            return
            
        if not action_config.get("enabled", False):
            print(f"❌ Action {action} is disabled")
            return
            
        print(f"🎯 Action: {action} ({action_config.get('name', 'Unnamed')})")
        
        # First try to copy selected text
        print("📋 Attempting to copy selected text...")
        copy_success = self.text_selector.copy_selected_text()
        
        # Get text from clipboard (either newly copied or existing)
        text = self.clipboard_reader.get_clipboard_text()
        if not text:
            print("❌ No text in clipboard and no text selected")
            return
            
        if not copy_success:
            print(f"📋 Using existing clipboard text: {text[:50]}...")
        else:
            print(f"📋 Using copied text: {text[:50]}...")
        
        print(f"⚙️ Action config: {action_config}")
        
        # Get speaker
        speaker = self.speakers.get(action)
        if not speaker:
            print(f"❌ No speaker initialized for action {action}")
            return
            
        # Speak the text
        voice_name = action_config.get("voice", "")
        rate = action_config.get("rate", 1.0)
        speed = action_config.get("speed", 1.0)
        
        print(f"🔊 Speaking text with {voice_name} at rate {rate}, speed {speed}")
        speaker.speak(text, voice_name, rate * speed)  # Combine rate and speed
        
    def _on_pause_resume_hotkey(self):
        """Handle pause/resume hotkey press."""
        print("🔥 HOTKEY PRESSED: PAUSE/RESUME")
        
        # Check if any speaker is currently speaking or paused
        active_speaker = None
        paused_speaker = None
        
        print("🔍 Checking speaker states:")
        for action, speaker in self.speakers.items():
            is_speaking = speaker.is_speaking()
            is_paused = getattr(speaker, '_is_paused', False)
            action_config = self.settings_manager.get_action_config(action)
            action_name = action_config.get('name', action)
            print(f"   {action} ({action_name}): speaking={is_speaking}, paused={is_paused}")
            
            if is_speaking and not is_paused:
                active_speaker = speaker
                print(f"   → Found active speaker: {action} ({action_name})")
                break
            elif is_paused:
                paused_speaker = speaker
                print(f"   → Found paused speaker: {action} ({action_name})")
                break
                
        if active_speaker:
            # Pause the active speaker
            print("⏸️ Pausing speech...")
            active_speaker.pause()
            print("✅ Speech paused")
        elif paused_speaker:
            # Resume the paused speaker
            print("▶️ Resuming speech...")
            paused_speaker.resume()
            print("✅ Speech resumed")
        else:
            print("❌ No active or paused speech found")
            
    def _register_hotkeys(self):
        """Register all configured hotkeys."""
        hotkeys = self.settings_manager.get_hotkeys()
        print(f"🔧 Registering hotkeys: {hotkeys}")
        
        # Register hotkeys for all actions
        for action, hotkey in hotkeys.items():
            print(f"🔧 Registering {action} -> {hotkey}")
            
            if action == "action_pause":
                # Special case for pause/resume
                success = self.hotkey_listener.register_hotkey(
                    hotkey,
                    self._on_pause_resume_hotkey
                )
                print(f"   ✅ {action} ({hotkey}): {'Success' if success else 'Failed'}")
            elif action.startswith("action_"):
                # Regular speak actions
                action_config = self.settings_manager.get_action_config(action)
                if action_config.get("enabled", False):
                    success = self.hotkey_listener.register_hotkey(
                        hotkey,
                        lambda h=hotkey: self._on_speak_hotkey(h)
                    )
                    action_name = action_config.get('name', action)
                    print(f"   ✅ {action} ({action_name}) - {hotkey}: {'Success' if success else 'Failed'}")
                else:
                    print(f"   ⏸️ {action} - {hotkey}: Disabled")
            else:
                print(f"   ❓ Unknown action type: {action}")
                
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
        
        # Check if we can use system tray (or force console mode)
        force_console = os.getenv('VORLESE_CONSOLE_MODE', '').lower() in ('1', 'true', 'yes')
        use_tray = PYSTRAY_AVAILABLE and platform.system() == "Windows" and not force_console
        
        print(f"🔧 System tray available: {PYSTRAY_AVAILABLE}")
        print(f"🔧 Platform: {platform.system()}")
        print(f"🔧 Force console mode: {force_console}")
        print(f"🔧 Will use system tray: {use_tray}")
        
        if use_tray:
            # Create and run system tray icon
            try:
                icon_image = self._create_tray_icon()
                self.icon = pystray.Icon(
                    "VorleseApp",
                    icon_image,
                    "Vorlese-App",
                    menu=self._create_menu()
                )
                print("✅ System tray icon created.")
                print("📍 Check system tray for the Vorlese-App icon.")
                print("📍 Right-click the icon to access settings or quit.")
                print("📍 The application is now running in the background.")
                
                # Run icon (this blocks until icon is stopped)
                self.icon.run()
                print("✅ System tray icon stopped.")
                
            except Exception as e:
                print(f"❌ Error with system tray: {e}")
                print("🔄 Falling back to console mode...")
                use_tray = False
        
        if not use_tray:
            # Run without system tray
            print("\n" + "="*50)
            print("🖥️  CONSOLE MODE")
            print("="*50)
            print("📍 The application is running in console mode.")
            print("📍 Hotkeys are active and ready to use:")
            for hotkey in self.hotkey_listener.get_registered_hotkeys():
                print(f"   - {hotkey}")
            print("📍 Press Ctrl+C to exit the application.")
            print("="*50)
            
            try:
                while self._is_running and not _shutdown_requested:
                    time.sleep(0.5)  # More responsive to shutdown signals
                    
                if _shutdown_requested:
                    print("\n📍 Shutdown requested by system signal...")
                    self._is_running = False
                    
            except KeyboardInterrupt:
                print("\n📍 Shutdown requested by user...")
                self._is_running = False
        
    def cleanup(self):
        """Clean up resources."""
        print("🧹 VorleseApp cleanup...")
        try:
            # Stop hotkey listener
            if hasattr(self, 'hotkey_listener'):
                self.hotkey_listener.stop()
                
            # Cleanup all speakers
            if hasattr(self, 'speakers'):
                for action, speaker in self.speakers.items():
                    print(f"🧹 Cleaning up speaker: {action}")
                    speaker.cleanup()
                    
            print("✅ VorleseApp cleanup completed")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            

def main():
    """Main entry point with fallback kill mechanism."""
    app = None
    startup_successful = False
    
    try:
        print("🚀 Starting Vorlese-App...")
        app = VorleseApp()
        startup_successful = True
        print("✅ App initialization successful")
        
        app.run()
        
    except KeyboardInterrupt:
        print("\n📍 Shutdown requested by user...")
        
    except Exception as e:
        print(f"❌ Critical error during startup/runtime: {e}")
        print("🔄 Attempting emergency cleanup...")
        
        # Emergency fallback kill - if startup failed, try aggressive cleanup
        if not startup_successful:
            print("💀 Startup failed - executing emergency force kill...")
            try:
                kill_previous_instances_fast()
                print("✅ Emergency force kill completed")
            except Exception as kill_error:
                print(f"❌ Emergency kill also failed: {kill_error}")
                print("⚠️ Manual cleanup may be required (Task Manager)")
        
    finally:
        print("🧹 Final cleanup...")
        if app:
            try:
                app.cleanup()
            except Exception as cleanup_error:
                print(f"❌ Cleanup error: {cleanup_error}")
        
        # Final safety net - ensure all our processes are cleaned up
        try:
            cleanup_all_speech_threads()
            print("✅ Final thread cleanup completed")
        except Exception as thread_cleanup_error:
            print(f"❌ Thread cleanup error: {thread_cleanup_error}")
        
        print("👋 Vorlese-App shutdown complete")
        

if __name__ == "__main__":
    main()