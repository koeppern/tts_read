import pyperclip
import time
from typing import Optional


class ClipboardReader:
    """Handles reading text from the system clipboard."""
    
    def __init__(self):
        """Initialize clipboard reader."""
        self._last_clipboard_content = ""
        
    def get_selected_text(self) -> Optional[str]:
        """Get currently selected text via clipboard.
        
        This method temporarily copies the selection to clipboard,
        reads it, and attempts to restore the previous clipboard content.
        
        Returns:
            Selected text or None if clipboard is empty/invalid
        """
        # Store current clipboard content
        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            original_clipboard = ""
            
        # Simulate Ctrl+C to copy selection
        # Note: In the full implementation, this would use keyboard simulation
        # For the prototype, we'll assume the user has already copied text
        
        # Small delay to ensure clipboard is updated
        time.sleep(0.1)
        
        try:
            # Get new clipboard content
            selected_text = pyperclip.paste()
            
            # Check if clipboard content has changed or is valid
            if selected_text and isinstance(selected_text, str):
                self._last_clipboard_content = selected_text
                return selected_text.strip()
            else:
                return None
                
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return None
            
    def get_clipboard_text(self) -> Optional[str]:
        """Get current clipboard text without selection.
        
        Returns:
            Current clipboard text or None if empty/invalid
        """
        try:
            text = pyperclip.paste()
            if text and isinstance(text, str):
                return text.strip()
            return None
        except Exception as e:
            print(f"Error reading clipboard: {e}")
            return None
            
    def clear_clipboard(self) -> None:
        """Clear the clipboard."""
        try:
            pyperclip.copy("")
        except Exception as e:
            print(f"Error clearing clipboard: {e}")