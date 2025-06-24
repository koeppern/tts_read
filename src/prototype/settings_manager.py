import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class SettingsManager:
    """Manages application settings from JSON configuration file."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize settings manager with config file path.
        
        Args:
            config_path: Path to settings.json file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/settings.json in project root
            self.config_path = Path(__file__).parent.parent.parent / "config" / "settings.json"
        else:
            self.config_path = Path(config_path)
            
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file with fallback to defaults."""
        default_settings = {
            "hotkeys": {
                "deSpeak": "ctrl+1",
                "enSpeak": "ctrl+2", 
                "pauseResume": "ctrl+3"
            },
            "voices": {
                "ctrl+1": {
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0
                },
                "ctrl+2": {
                    "engine": "SAPI",
                    "voice": "Microsoft Zira Desktop",
                    "rate": 1.0
                }
            },
            "startup": False
        }
        
        if not self.config_path.exists():
            # Create config directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            # Save default settings
            self._save_settings(default_settings)
            return default_settings
            
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in default_settings.items():
                    if key not in loaded_settings:
                        loaded_settings[key] = value
                return loaded_settings
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading settings: {e}. Using defaults.")
            return default_settings
            
    def _save_settings(self, settings: Dict[str, Any]) -> None:
        """Save settings to JSON file."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            
    def get_hotkeys(self) -> Dict[str, str]:
        """Get hotkey mappings."""
        return self.settings.get("hotkeys", {})
        
    def get_voice_config(self, hotkey: str) -> Dict[str, Any]:
        """Get voice configuration for a specific hotkey.
        
        Args:
            hotkey: The hotkey string (e.g., "ctrl+1")
            
        Returns:
            Voice configuration dict with engine, voice name, and rate.
        """
        return self.settings.get("voices", {}).get(hotkey, {})
        
    def get_startup_enabled(self) -> bool:
        """Check if auto-startup is enabled."""
        return self.settings.get("startup", False)
        
    def reload(self) -> None:
        """Reload settings from file."""
        self.settings = self._load_settings()
        
    def get_settings_path(self) -> Path:
        """Get the path to the settings file."""
        return self.config_path