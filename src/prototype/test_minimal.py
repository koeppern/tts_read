#!/usr/bin/env python3
"""Minimal test to isolate the issue."""

import sys
import time

print("Step 1: Basic imports")
try:
    from settings_manager import SettingsManager
    print("  ✓ SettingsManager imported")
except Exception as e:
    print(f"  ✗ SettingsManager import failed: {e}")
    sys.exit(1)

print("\nStep 2: Create SettingsManager")
try:
    sm = SettingsManager()
    print("  ✓ SettingsManager created")
except Exception as e:
    print(f"  ✗ SettingsManager creation failed: {e}")
    sys.exit(1)

print("\nStep 3: Get hotkeys")
try:
    hotkeys = sm.get_hotkeys()
    print(f"  ✓ Hotkeys retrieved: {hotkeys}")
except Exception as e:
    print(f"  ✗ Getting hotkeys failed: {e}")
    sys.exit(1)

print("\nAll steps completed successfully!")