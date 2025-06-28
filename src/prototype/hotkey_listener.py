import platform
import sys
from typing import Dict, Callable, Optional
import threading

# Handle keyboard import with better error messages
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
    print("✅ Keyboard module imported successfully")
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("❌ WARNING: keyboard module not available")
except Exception as e:
    KEYBOARD_AVAILABLE = False
    print(f"❌ WARNING: keyboard module error: {e}")


class HotkeyListener:
    """Manages global hotkey registration and callbacks."""
    
    def __init__(self):
        """Initialize hotkey listener."""
        self._hotkeys: Dict[str, int] = {}  # hotkey -> handler_id mapping
        self._callbacks: Dict[str, Callable] = {}  # hotkey -> callback mapping
        self._running = False
        self._thread: Optional[threading.Thread] = None
        # Only use dummy mode if keyboard is not available
        # Don't automatically use dummy mode on Linux - let it try first
        self._dummy_mode = not KEYBOARD_AVAILABLE
        
        print(f"🔧 Platform: {platform.system()}")
        print(f"🔧 Keyboard available: {KEYBOARD_AVAILABLE}")
        print(f"🔧 Dummy mode: {self._dummy_mode}")
        
        if self._dummy_mode:
            print("⚠️ WARNING: Hotkey listener running in dummy mode.")
            if not KEYBOARD_AVAILABLE:
                print("   Reason: keyboard module not available")
            if platform.system() == "Linux":
                print("   Note: Global hotkeys typically require root privileges on Linux.")
                print("   Consider running with sudo or using a different hotkey solution.")
        else:
            print("✅ Hotkey listener ready for real hotkey detection")
        
    def register_hotkey(self, hotkey: str, callback: Callable) -> bool:
        """Register a global hotkey with a callback function.
        
        Args:
            hotkey: Hotkey combination (e.g., "ctrl+1")
            callback: Function to call when hotkey is pressed
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Normalize hotkey string
            normalized_hotkey = hotkey.lower().replace(" ", "")
            
            # Unregister if already exists
            if normalized_hotkey in self._hotkeys:
                self.unregister_hotkey(normalized_hotkey)
                
            # Register new hotkey
            if self._dummy_mode:
                # In dummy mode, just store the callback
                self._hotkeys[normalized_hotkey] = -1  # Dummy ID
                self._callbacks[normalized_hotkey] = callback
                print(f"🔧 Registered hotkey (dummy mode): {normalized_hotkey}")
            else:
                try:
                    handler_id = keyboard.add_hotkey(normalized_hotkey, callback)
                    self._hotkeys[normalized_hotkey] = handler_id
                    self._callbacks[normalized_hotkey] = callback
                    print(f"✅ Registered hotkey: {normalized_hotkey}")
                except Exception as e:
                    print(f"❌ Failed to register hotkey {normalized_hotkey}: {e}")
                    if "access" in str(e).lower() or "permission" in str(e).lower():
                        print("   💡 Try running as administrator for global hotkeys")
                    return False
            return True
            
        except Exception as e:
            print(f"Failed to register hotkey {hotkey}: {e}")
            return False
            
    def unregister_hotkey(self, hotkey: str) -> bool:
        """Unregister a previously registered hotkey.
        
        Args:
            hotkey: Hotkey combination to unregister
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            normalized_hotkey = hotkey.lower().replace(" ", "")
            
            if normalized_hotkey in self._hotkeys:
                if not self._dummy_mode:
                    keyboard.remove_hotkey(self._hotkeys[normalized_hotkey])
                del self._hotkeys[normalized_hotkey]
                del self._callbacks[normalized_hotkey]
                print(f"Unregistered hotkey: {normalized_hotkey}")
                return True
            return False
            
        except Exception as e:
            print(f"Failed to unregister hotkey {hotkey}: {e}")
            return False
            
    def unregister_all(self) -> None:
        """Unregister all hotkeys."""
        hotkeys_to_remove = list(self._hotkeys.keys())
        for hotkey in hotkeys_to_remove:
            self.unregister_hotkey(hotkey)
            
    def start(self) -> None:
        """Start listening for hotkeys in a background thread."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            print("Hotkey listener started")
            
    def _listen_loop(self) -> None:
        """Main listening loop (runs in background thread)."""
        if self._dummy_mode:
            # In dummy mode, just sleep
            import time
            while self._running:
                time.sleep(1)
                print("🔧 Hotkey listener dummy mode - sleeping...")
        else:
            try:
                print("🎯 Starting hotkey listening loop...")
                # Simply keep the thread alive - keyboard module handles hotkeys automatically
                import time
                while self._running:
                    time.sleep(0.1)  # Small sleep to prevent high CPU usage
                print("✅ Hotkey listening loop ended")
            except Exception as e:
                print(f"❌ Hotkey listener error: {e}")
                self._running = False
            
    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if self._running:
            self._running = False
            self.unregister_all()
            # Trigger keyboard event to unblock wait()
            if not self._dummy_mode:
                try:
                    keyboard.press_and_release('esc')
                except:
                    pass
            print("Hotkey listener stopped")
            
    def is_running(self) -> bool:
        """Check if listener is currently running."""
        return self._running
        
    def get_registered_hotkeys(self) -> list:
        """Get list of currently registered hotkeys."""
        return list(self._hotkeys.keys())