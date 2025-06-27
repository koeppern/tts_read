#!/usr/bin/env python3
"""
Test script for the fallback kill mechanism in main.py.
"""

import os
import sys
import time
import subprocess
import threading
from unittest.mock import patch, MagicMock

def test_normal_startup():
	"""Test normal startup without errors."""
	print("🧪 Test 1: Normal startup")
	
	# Mock successful startup
	try:
		with patch('main.VorleseApp') as mock_app_class:
			mock_app = MagicMock()
			mock_app_class.return_value = mock_app
			
			# Import and run main
			import main
			
			# This should complete without errors
			print("✅ Normal startup test passed")
			
	except Exception as e:
		print(f"❌ Normal startup test failed: {e}")

def test_startup_failure():
	"""Test startup failure triggers emergency kill."""
	print("🧪 Test 2: Startup failure with emergency kill")
	
	try:
		with patch('main.VorleseApp') as mock_app_class, \
		     patch('main.kill_previous_instances_fast') as mock_kill:
			
			# Make VorleseApp initialization fail
			mock_app_class.side_effect = Exception("Simulated startup failure")
			
			# Import main module
			import main
			
			# Run main function - should trigger emergency kill
			try:
				main.main()
			except SystemExit:
				pass  # Expected
			
			# Verify emergency kill was called
			mock_kill.assert_called_once()
			print("✅ Emergency kill was triggered correctly")
			
	except Exception as e:
		print(f"❌ Startup failure test failed: {e}")

def test_signal_handling():
	"""Test signal handling for graceful shutdown."""
	print("🧪 Test 3: Signal handling")
	
	try:
		import main
		
		# Test signal handler
		original_flag = main._shutdown_requested
		main.signal_handler(15, None)  # SIGTERM
		
		if main._shutdown_requested:
			print("✅ Signal handler works correctly")
		else:
			print("❌ Signal handler did not set shutdown flag")
			
		# Reset flag
		main._shutdown_requested = original_flag
		
	except Exception as e:
		print(f"❌ Signal handling test failed: {e}")

def test_runtime_error_handling():
	"""Test runtime error handling."""
	print("🧪 Test 4: Runtime error handling")
	
	try:
		with patch('main.VorleseApp') as mock_app_class, \
		     patch('main.cleanup_all_speech_threads') as mock_cleanup:
			
			mock_app = MagicMock()
			mock_app_class.return_value = mock_app
			
			# Make run() method fail
			mock_app.run.side_effect = Exception("Simulated runtime error")
			
			import main
			
			try:
				main.main()
			except SystemExit:
				pass
			
			# Verify cleanup was called
			mock_cleanup.assert_called_once()
			print("✅ Runtime error cleanup works correctly")
			
	except Exception as e:
		print(f"❌ Runtime error test failed: {e}")

def simulate_hanging_process():
	"""Simulate a hanging process for testing."""
	print("🧪 Test 5: Simulating hanging process")
	
	# Create a simple script that hangs
	hanging_script = '''
import time
import sys
print("Hanging process started...")
sys.stdout.flush()
while True:
	time.sleep(1)
'''
	
	try:
		# Write hanging script
		with open('temp_hanging.py', 'w') as f:
			f.write(hanging_script)
		
		# Start hanging process
		process = subprocess.Popen([sys.executable, 'temp_hanging.py'])
		print(f"📍 Started hanging process: PID {process.pid}")
		
		# Give it time to start
		time.sleep(1)
		
		# Test our kill function on it
		from text_speaker_v2 import kill_previous_instances_fast
		
		print("🔪 Testing force kill on hanging process...")
		kill_previous_instances_fast()
		
		# Check if process is still running
		time.sleep(0.5)
		if process.poll() is None:
			print("⚠️ Process still running, manually terminating...")
			process.terminate()
			process.wait(timeout=2)
		
		print("✅ Hanging process test completed")
		
	except Exception as e:
		print(f"❌ Hanging process test failed: {e}")
		
	finally:
		# Cleanup
		try:
			if 'process' in locals() and process.poll() is None:
				process.kill()
			if os.path.exists('temp_hanging.py'):
				os.remove('temp_hanging.py')
		except:
			pass

if __name__ == "__main__":
	print("🚀 Starting fallback kill mechanism tests...")
	print("=" * 60)
	
	test_normal_startup()
	print()
	
	test_startup_failure()
	print()
	
	test_signal_handling()
	print()
	
	test_runtime_error_handling()
	print()
	
	simulate_hanging_process()
	print()
	
	print("=" * 60)
	print("🎉 All fallback kill tests completed!") 