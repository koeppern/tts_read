#!/usr/bin/env python3
"""Test imports step by step."""

import sys

print("Testing imports step by step...")

print("\n1. Standard library imports:")
try:
    import os
    print("  ✓ os")
    import subprocess
    print("  ✓ subprocess")
    from pathlib import Path
    print("  ✓ pathlib.Path")
    import platform
    print("  ✓ platform")
    from threading import Thread
    print("  ✓ threading.Thread")
    import time
    print("  ✓ time")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

print("\n2. Third-party imports:")
try:
    print("  Testing pystray...")
    import pystray
    print("  ✓ pystray")
except Exception as e:
    print(f"  ✗ pystray failed: {e}")

try:
    print("  Testing PIL...")
    from PIL import Image, ImageDraw
    print("  ✓ PIL")
except Exception as e:
    print(f"  ✗ PIL failed: {e}")

print("\n3. Local imports:")
try:
    from settings_manager import SettingsManager
    print("  ✓ settings_manager")
    from text_speaker import TextSpeakerFactory
    print("  ✓ text_speaker")
    from clipboard_reader import ClipboardReader
    print("  ✓ clipboard_reader")
    from hotkey_listener import HotkeyListener
    print("  ✓ hotkey_listener")
except Exception as e:
    print(f"  ✗ Failed: {e}")
    sys.exit(1)

print("\nAll imports successful!")