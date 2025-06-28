#!/usr/bin/env python3
"""
Main application entry point for TTS hotkey system.
"""

print("🚀 main.py started - beginning imports...")

import sys
import os
import subprocess
from pathlib import Path
import platform
import signal
import threading

# Add the current directory to Python path for direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("📦 Basic modules imported, importing UI modules...")

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
    print("✅ pystray modules imported successfully")
except (ImportError, ValueError):
    PYSTRAY_AVAILABLE = False
    print("⚠️ pystray not available")
    
from threading import Thread
import time

print("🔧 Importing application modules...")

# Import with fallback for both relative and absolute imports
try:
    from .settings_manager import SettingsManager
    from .text_speaker_v2 import TextSpeakerFactory, startup_cleanup, kill_previous_instances_fast, cleanup_all_speech_threads
    from .clipboard_reader import ClipboardReader
    from .hotkey_listener import HotkeyListener
    from .text_selector import TextSelector
    from .text_display_window import TextDisplayWindow
    from .admin_helper import is_admin, print_admin_instructions
    print("✅ Relative imports successful")
except ImportError:
    print("⚠️ Relative imports failed, trying absolute imports...")
    # Fallback for direct execution
    from settings_manager import SettingsManager
    from text_speaker_v2 import TextSpeakerFactory, startup_cleanup, kill_previous_instances_fast, cleanup_all_speech_threads
    from clipboard_reader import ClipboardReader
    from hotkey_listener import HotkeyListener
    from text_selector import TextSelector
    from text_display_window import TextDisplayWindow
    from admin_helper import is_admin, print_admin_instructions
    print("✅ Absolute imports successful")

print("✅ All imports completed successfully")

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
        
        # Check administrator privileges first
        self.has_admin = is_admin()
        print(f"👤 Administrator privileges: {self.has_admin}")
        
        if not self.has_admin:
            print("⚠️ WARNING: Running without administrator privileges")
            print("🔑 Global hotkeys (Ctrl+1, Ctrl+2, Ctrl+3) will NOT work")
            print("💡 Win+Space may still work for text window")
            print("📖 See START_APP_AS_ADMIN.bat for easy admin start")
            print()
        
        startup_cleanup()
        
        print("📁 Creating SettingsManager...")
        self.settings_manager = SettingsManager()
        print("📋 Creating ClipboardReader...")
        self.clipboard_reader = ClipboardReader()
        print("🎯 Creating TextSelector...")
        self.text_selector = TextSelector()
        print("⌨️ Creating HotkeyListener...")
        self.hotkey_listener = HotkeyListener()
        print("🖥️ Creating TextDisplayWindow...")
        self.display_window = TextDisplayWindow(self.settings_manager)
        
        print("🔊 Initializing speakers...")
        self.speakers = {}
        self._init_speakers()
        
        self.icon = None
        self._is_running = True
        
        import atexit
        atexit.register(self.cleanup)
        print("✅ VorleseApp initialization complete")
        
        # Show admin warning again after initialization
        if not self.has_admin:
            self._show_admin_warning()
        
    def _init_speakers(self):
        """Initialize text speakers based on configuration."""
        print("🔊 Available SAPI Voices (NBSapi):")
        temp_speaker = TextSpeakerFactory.create_speaker("SAPI")
        available_voices = temp_speaker.get_available_voices()
        for i, voice in enumerate(available_voices):
            print(f"   {i+1}. {voice}")
        print()
        
        self.settings_manager.print_configuration()
        
        enabled_actions = self.settings_manager.get_enabled_actions()
        for action, action_config in enabled_actions.items():
            engine_type = action_config.get("engine", "SAPI")
            self.speakers[action] = TextSpeakerFactory.create_speaker(engine_type)
            print(f"✅ Initialized NBSapi speaker for {action} ({action_config.get('name', 'Unnamed')})")
            
        temp_speaker.cleanup()
                    
    def _create_tray_icon(self):
        """Create a simple placeholder icon for the system tray."""
        image = Image.new('RGB', (64, 64), color='blue')
        draw = ImageDraw.Draw(image)
        draw.ellipse([16, 16, 48, 48], fill='white')
        return image
        
    def _on_speak_hotkey(self, hotkey: str):
        """Handle speak hotkey press."""
        action = self.settings_manager.get_action_for_hotkey(hotkey)
        if not action:
            return
            
        action_config = self.settings_manager.get_action_config(action)
        if not action_config or not action_config.get("enabled", False):
            return
            
        copy_success = self.text_selector.copy_selected_text()
        text = self.clipboard_reader.get_clipboard_text()
        if not text:
            return
            
        self.display_window.set_text(text)
        self.display_window.show()

        speaker = self.speakers.get(action)
        if not speaker:
            return
            
        voice_name = action_config.get("voice", "")
        speed = action_config.get("speed", 1.0)
        
        speaker.speak(text, voice_name, speed, self.display_window.highlight_word)
        
    def _on_pause_resume_hotkey(self):
        """Handle pause/resume hotkey press."""
        active_speaker = None
        paused_speaker = None
        
        for speaker in self.speakers.values():
            if speaker.is_speaking():
                active_speaker = speaker
                break
            elif speaker.is_paused():
                paused_speaker = speaker
                break
                
        if active_speaker:
            active_speaker.pause()
        elif paused_speaker:
            paused_speaker.resume()

    def _on_show_window_hotkey(self):
        """Handle show/hide window hotkey press."""
        self.display_window.show()

    def _register_hotkeys(self):
        """Register all configured hotkeys."""
        try:
            print("🔍 Getting hotkeys from settings...")
            hotkeys = self.settings_manager.get_hotkeys()
            print(f"📋 Found hotkeys: {hotkeys}")
            
            for action, hotkey in hotkeys.items():
                print(f"⌨️ Registering hotkey for {action}: {hotkey}")
                
                if action == "action_pause":
                    print("   ⏸️ Registering pause/resume hotkey")
                    self.hotkey_listener.register_hotkey(hotkey, self._on_pause_resume_hotkey)
                elif action == "action_show_text":
                    print("   🖥️ Registering show text window hotkey")
                    self.hotkey_listener.register_hotkey(hotkey, self._on_show_window_hotkey)
                elif action.startswith("action_"):
                    action_config = self.settings_manager.get_action_config(action)
                    if action_config and action_config.get("enabled", False):
                        print(f"   🔊 Registering speak hotkey for {action}")
                        self.hotkey_listener.register_hotkey(hotkey, lambda h=hotkey: self._on_speak_hotkey(h))
                    else:
                        print(f"   ❌ Skipping disabled action: {action}")
                        
            print("✅ All hotkeys registered successfully")
            
        except Exception as e:
            print(f"❌ Error registering hotkeys: {e}")
            import traceback
            traceback.print_exc()
            raise
        
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
        print("🔧 Registering hotkeys...")
        self._register_hotkeys()
        print("⌨️ Starting hotkey listener...")
        self.hotkey_listener.start()
        
        print("🔍 Checking environment...")
        force_console = os.getenv('VORLESE_CONSOLE_MODE', '').lower() in ('1', 'true', 'yes')
        use_tray = PYSTRAY_AVAILABLE and platform.system() == "Windows" and not force_console
        print(f"💻 force_console: {force_console}, use_tray: {use_tray}, PYSTRAY_AVAILABLE: {PYSTRAY_AVAILABLE}")
        
        if use_tray:
            print("🖼️ Setting up system tray...")
            try:
                icon_image = self._create_tray_icon()
                self.icon = pystray.Icon("VorleseApp", icon_image, "Vorlese-App", menu=self._create_menu())
                print("🚀 Starting tray icon...")
                self.icon.run_detached()
                
                print("🔄 Entering main loop (tray mode)...")
                while self._is_running:
                    time.sleep(0.1)  # Simple sleep loop - Tkinter handles its own updates
                print("✅ Main loop exited (tray mode)")

            except Exception as e:
                print(f"❌ Error with system tray: {e}")
                import traceback
                traceback.print_exc()
                use_tray = False
        
        if not use_tray:
            print("💻 Running in console mode...")
            try:
                print("🔄 Entering main loop (console mode)...")
                while self._is_running and not _shutdown_requested:
                    time.sleep(0.1)  # Simple sleep loop - Tkinter handles its own updates
                print("✅ Main loop exited (console mode)")
            except KeyboardInterrupt:
                print("⌨️ Keyboard interrupt in console mode")
                self._is_running = False
        
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        if hasattr(self, 'speakers'):
            for speaker in self.speakers.values():
                speaker.cleanup()
            
    def _show_admin_warning(self):
        """Show detailed admin warning message."""
        print("\n" + "=" * 60)
        print("⚠️  ADMINISTRATOR PRIVILEGES REQUIRED FOR HOTKEYS")
        print("=" * 60)
        print("❌ Global hotkeys (Ctrl+1, Ctrl+2, Ctrl+3) will NOT work")
        print("✅ Text display window (Win+Space) may still work")
        print()
        print("📋 TO FIX THIS:")
        print("1. Close this app")
        print("2. Right-click on 'START_APP_AS_ADMIN.bat'")
        print("3. Select 'Run as administrator'")
        print()
        print("🔧 OR in VS Code:")
        print("1. Close VS Code")
        print("2. Right-click VS Code icon")
        print("3. Select 'Run as administrator'")
        print("4. Open project and run app again")
        print("=" * 60)
        print()

def main():
    """Main entry point."""
    print("🚀 Starting VorleseApp main...")
    app = None
    try:
        print("📦 Creating VorleseApp instance...")
        app = VorleseApp()
        print("✅ VorleseApp instance created successfully")
        
        print("🏃 Starting app.run()...")
        app.run()
        print("✅ app.run() completed")
        
    except KeyboardInterrupt:
        print("\n📍 Shutdown requested by user...")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🧹 Starting cleanup...")
        if app:
            app.cleanup()
        cleanup_all_speech_threads()
        print("👋 Vorlese-App shutdown complete")
        

if __name__ == "__main__":
    print("🎯 Running as main module")
    main()
else:
    print("📦 Imported as module")
        


