"""
Text selector module for copying selected text to clipboard.
"""

import time
import pyperclip
import platform

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class TextSelector:
    """Handles copying selected text to clipboard."""
    
    def __init__(self):
        """Initialize text selector."""
        self.system = platform.system()
        
    def copy_selected_text(self) -> bool:
        """Copy currently selected text to clipboard.
        
        Returns:
            True if successful, False otherwise
        """
        if not KEYBOARD_AVAILABLE:
            print("⚠️ Keyboard module not available for text selection")
            return False
            
        try:
            # Store current clipboard content
            original_clipboard = ""
            try:
                original_clipboard = pyperclip.paste()
            except:
                pass
            
            # Clear clipboard first
            pyperclip.copy("")
            
            # Give a small delay
            time.sleep(0.1)
            
            # Send Ctrl+C to copy selected text
            if self.system == "Darwin":  # macOS
                keyboard.send('cmd+c')
            else:  # Windows/Linux
                keyboard.send('ctrl+c')
            
            # Wait for clipboard to update
            time.sleep(0.2)
            
            # Check if clipboard has new content
            new_clipboard = pyperclip.paste()
            
            if new_clipboard and new_clipboard != original_clipboard:
                print(f"📋 Copied selected text: {new_clipboard[:50]}...")
                return True
            else:
                print("📋 No text was selected or copied")
                # Restore original clipboard if nothing was copied
                if original_clipboard:
                    pyperclip.copy(original_clipboard)
                return False
                
        except Exception as e:
            print(f"❌ Error copying selected text: {e}")
            return False
    
    def get_clipboard_text(self) -> str:
        """Get text from clipboard.
        
        Returns:
            Clipboard text or empty string
        """
        try:
            return pyperclip.paste() or ""
        except Exception as e:
            print(f"❌ Error reading clipboard: {e}")
            return "" 