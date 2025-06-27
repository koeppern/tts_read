#!/usr/bin/env python3
"""
Test script to debug VS Code startup behavior.
"""

import os
import sys
import time
from text_speaker_v2 import detect_runtime_environment, get_optimal_startup_mode

def test_environment_detection():
	"""Test environment detection."""
	print("🔍 Environment Detection Test")
	print("=" * 40)
	
	# Show relevant environment variables
	print("📍 Relevant Environment Variables:")
	env_vars = [
		'VSCODE_PID', 'VSCODE_INJECTION', 'TERM_PROGRAM',
		'PYCHARM_HOSTED', 'JUPYTER_RUNTIME_DIR', 'TERM',
		'ConEmuPID', 'VORLESE_BATCH_MODE'
	]
	
	for var in env_vars:
		value = os.environ.get(var, 'Not set')
		print(f"   {var}: {value}")
	
	print()
	
	# Test detection
	env = detect_runtime_environment()
	print(f"🎯 Detected Environment: {env}")
	
	# Test optimal config
	config = get_optimal_startup_mode()
	print(f"⚙️ Optimal Configuration:")
	for key, value in config.items():
		print(f"   {key}: {value}")
	
	print()

def simulate_startup():
	"""Simulate the startup process."""
	print("🚀 Simulating Startup Process")
	print("=" * 40)
	
	try:
		print("📍 Step 1: Import main modules...")
		from main import VorleseApp
		print("✅ Imports successful")
		
		print("📍 Step 2: Create VorleseApp instance...")
		# This will trigger startup_cleanup()
		app = VorleseApp()
		print("✅ VorleseApp created successfully")
		
		print("📍 Step 3: Cleanup...")
		app.cleanup()
		print("✅ Cleanup completed")
		
		return True
		
	except Exception as e:
		print(f"❌ Error during startup simulation: {e}")
		import traceback
		traceback.print_exc()
		return False

def main():
	"""Main test function."""
	print("🧪 VS Code Startup Debug Test")
	print("=" * 50)
	print()
	
	test_environment_detection()
	print()
	
	print("🧪 Testing Startup Simulation...")
	success = simulate_startup()
	
	print()
	print("=" * 50)
	if success:
		print("✅ All tests passed! The application should work in VS Code.")
	else:
		print("❌ Tests failed! There are issues with VS Code startup.")

if __name__ == "__main__":
	main() 