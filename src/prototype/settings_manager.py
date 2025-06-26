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
                "action_0": "ctrl+4",
                "action_1": "ctrl+2",
                "action_2": "ctrl+5",
                "action_3": "ctrl+6",
                "action_4": "ctrl+7",
                "action_5": "ctrl+8",
                "action_6": "ctrl+9",
                "action_7": "ctrl+shift+1",
                "action_8": "ctrl+shift+2",
                "action_9": "ctrl+shift+3",
                "action_pause": "ctrl+3"
            },
            "actions": {
                "action_0": {
                    "name": "German Voice",
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0,
                    "speed": 0.9,
                    "enabled": True
                },
                "action_1": {
                    "name": "English Voice",
                    "engine": "SAPI",
                    "voice": "Microsoft Zira Desktop - English (United States)",
                    "rate": 1.0,
                    "speed": 1.0,
                    "enabled": True
                },
                "action_2": {
                    "name": "Fast German",
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0,
                    "speed": 1.3,
                    "enabled": False
                },
                "action_3": {
                    "name": "Slow German",
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0,
                    "speed": 0.7,
                    "enabled": False
                },
                "action_4": {
                    "name": "Fast English",
                    "engine": "SAPI",
                    "voice": "Microsoft Zira Desktop - English (United States)",
                    "rate": 1.0,
                    "speed": 1.3,
                    "enabled": False
                },
                "action_5": {
                    "name": "Unused Action 5",
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0,
                    "speed": 1.0,
                    "enabled": False
                },
                "action_6": {
                    "name": "Unused Action 6",
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0,
                    "speed": 1.0,
                    "enabled": False
                },
                "action_7": {
                    "name": "Unused Action 7",
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0,
                    "speed": 1.0,
                    "enabled": False
                },
                "action_8": {
                    "name": "Unused Action 8",
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0,
                    "speed": 1.0,
                    "enabled": False
                },
                "action_9": {
                    "name": "Unused Action 9",
                    "engine": "SAPI",
                    "voice": "Microsoft Hedda Desktop",
                    "rate": 1.0,
                    "speed": 1.0,
                    "enabled": False
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
        """Get hotkey mappings (action -> hotkey)."""
        return self.settings.get("hotkeys", {})
        
    def get_hotkey_for_action(self, action: str) -> str:
        """Get hotkey for a specific action.
        
        Args:
            action: The action name (e.g., "action_0")
            
        Returns:
            Hotkey string or empty string if not found.
        """
        return self.settings.get("hotkeys", {}).get(action, "")
        
    def get_action_for_hotkey(self, hotkey: str) -> str:
        """Get action for a specific hotkey.
        
        Args:
            hotkey: The hotkey string (e.g., "ctrl+4")
            
        Returns:
            Action name or empty string if not found.
        """
        hotkeys = self.get_hotkeys()
        for action, mapped_hotkey in hotkeys.items():
            if mapped_hotkey == hotkey:
                return action
        return ""
        
    def get_action_config(self, action: str) -> Dict[str, Any]:
        """Get action configuration for a specific action.
        
        Args:
            action: The action name (e.g., "action_0")
            
        Returns:
            Action configuration dict with engine, voice name, rate, speed, etc.
        """
        return self.settings.get("actions", {}).get(action, {})
        
    def get_enabled_actions(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled actions with their configurations.
        
        Returns:
            Dict of enabled actions with their configs.
        """
        actions = self.settings.get("actions", {})
        return {action: config for action, config in actions.items() 
                if config.get("enabled", False)}
        
    def get_startup_enabled(self) -> bool:
        """Check if auto-startup is enabled."""
        return self.settings.get("startup", False)
        
    def reload(self) -> None:
        """Reload settings from file."""
        self.settings = self._load_settings()
        
    def get_settings_path(self) -> Path:
        """Get the path to the settings file."""
        return self.config_path
        
    def print_configuration(self) -> None:
        """Print current configuration in a readable format."""
        print("🔧 Current Configuration:")
        print("=" * 50)
        
        # Print enabled actions
        enabled_actions = self.get_enabled_actions()
        print(f"📋 Enabled Actions ({len(enabled_actions)}):")
        for action, config in enabled_actions.items():
            hotkey = self.get_hotkey_for_action(action)
            name = config.get("name", "Unnamed")
            voice = config.get("voice", "Unknown")
            speed = config.get("speed", 1.0)
            print(f"   {hotkey} → {action} → {name}")
            print(f"      Voice: {voice}")
            print(f"      Speed: {speed}")
            print()
            
        # Print pause action
        pause_hotkey = self.get_hotkey_for_action("action_pause")
        print(f"⏸️ Pause/Resume: {pause_hotkey}")
        print()
        
        # Print disabled actions
        all_actions = self.settings.get("actions", {})
        disabled_actions = {action: config for action, config in all_actions.items() 
                          if not config.get("enabled", False)}
        if disabled_actions:
            print(f"💤 Disabled Actions ({len(disabled_actions)}):")
            for action, config in disabled_actions.items():
                hotkey = self.get_hotkey_for_action(action)
                name = config.get("name", "Unnamed")
                print(f"   {hotkey} → {action} → {name} (disabled)")
            print()
            
    # Legacy compatibility methods (deprecated)
    def get_voice_config(self, hotkey: str) -> Dict[str, Any]:
        """Legacy method: Get voice config by hotkey.
        
        DEPRECATED: Use get_action_config() with get_action_for_hotkey() instead.
        """
        action = self.get_action_for_hotkey(hotkey)
        if action:
            return self.get_action_config(action)
        return {}