#!/usr/bin/env python3
"""
Test script for the new action-based system.
"""

import sys
from pathlib import Path

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from settings_manager import SettingsManager


def test_action_system():
    """Test the new action-based configuration system."""
    print("🧪 Testing Action-Based System")
    print("=" * 50)
    
    # Create settings manager
    settings = SettingsManager()
    
    # Test hotkey to action mapping
    print("1. Testing hotkey to action mapping:")
    test_hotkeys = ["ctrl+4", "ctrl+2", "ctrl+3", "ctrl+5"]
    for hotkey in test_hotkeys:
        action = settings.get_action_for_hotkey(hotkey)
        if action:
            action_config = settings.get_action_config(action)
            name = action_config.get("name", "Unknown")
            enabled = action_config.get("enabled", False)
            print(f"   {hotkey} → {action} → {name} ({'✅ Enabled' if enabled else '❌ Disabled'})")
        else:
            print(f"   {hotkey} → ❌ No action mapped")
    
    print()
    
    # Test action to hotkey mapping
    print("2. Testing action to hotkey mapping:")
    actions = ["action_0", "action_1", "action_2", "action_pause"]
    for action in actions:
        hotkey = settings.get_hotkey_for_action(action)
        if hotkey:
            print(f"   {action} → {hotkey}")
        else:
            print(f"   {action} → ❌ No hotkey mapped")
    
    print()
    
    # Test enabled actions
    print("3. Testing enabled actions:")
    enabled_actions = settings.get_enabled_actions()
    print(f"   Found {len(enabled_actions)} enabled actions:")
    for action, config in enabled_actions.items():
        hotkey = settings.get_hotkey_for_action(action)
        name = config.get("name", "Unknown")
        voice = config.get("voice", "Unknown")
        speed = config.get("speed", 1.0)
        print(f"      {hotkey} → {action} → {name}")
        print(f"         Voice: {voice}")
        print(f"         Speed: {speed}")
    
    print()
    
    # Test configuration display
    print("4. Full configuration:")
    settings.print_configuration()
    
    print("✅ Action system test completed!")


def test_hotkey_changes():
    """Demonstrate how hotkey changes work with the new system."""
    print("\n🔄 Testing Hotkey Change Flexibility")
    print("=" * 50)
    
    settings = SettingsManager()
    
    print("Current mapping:")
    print(f"   action_0: {settings.get_hotkey_for_action('action_0')}")
    print(f"   action_1: {settings.get_hotkey_for_action('action_1')}")
    
    print("\nTo change CTRL+4 to CTRL+1, you would only need to change:")
    print("   'action_0': 'ctrl+4'  →  'action_0': 'ctrl+1'")
    print("The voice configuration stays with action_0!")
    
    print("\nTo swap hotkeys between action_0 and action_1:")
    print("   'action_0': 'ctrl+4'  →  'action_0': 'ctrl+2'")
    print("   'action_1': 'ctrl+2'  →  'action_1': 'ctrl+4'")
    print("Voice configurations automatically follow their actions!")


def main():
    """Run all tests."""
    try:
        test_action_system()
        test_hotkey_changes()
        
        print("\n🎯 Summary:")
        print("The new action-based system prevents configuration mismatches!")
        print("- Hotkeys are mapped to actions (action_0, action_1, etc.)")
        print("- Voice configurations are tied to actions, not hotkeys")
        print("- Changing hotkeys won't break voice configurations")
        print("- Actions can be easily enabled/disabled")
        
    except Exception as e:
        print(f"❌ Test error: {e}")


if __name__ == "__main__":
    main() 