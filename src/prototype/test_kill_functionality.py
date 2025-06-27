#!/usr/bin/env python3
"""
Test script for the improved kill functionality.
"""

import os
import sys
import time
import subprocess
import threading
from text_speaker_v2 import (
	kill_previous_instances, 
	kill_previous_instances_fast,
	startup_cleanup
)

def test_kill_functions():
	"""Test both kill functions."""
	print("🧪 Testing kill functionality...")
	print("=" * 50)
	
	# Test 1: Normal kill function
	print("🧪 Test 1: Normal kill function")
	try:
		start_time = time.time()
		kill_previous_instances()
		elapsed = time.time() - start_time
		print(f"✅ Normal kill completed in {elapsed:.2f} seconds")
	except Exception as e:
		print(f"❌ Normal kill failed: {e}")
	
	print()
	
	# Test 2: Fast kill function
	print("🧪 Test 2: Fast kill function")
	try:
		start_time = time.time()
		kill_previous_instances_fast()
		elapsed = time.time() - start_time
		print(f"✅ Fast kill completed in {elapsed:.2f} seconds")
	except Exception as e:
		print(f"❌ Fast kill failed: {e}")
	
	print()
	
	# Test 3: Startup cleanup with different modes
	print("🧪 Test 3: Startup cleanup modes")
	
	# Normal mode
	os.environ.pop('VORLESE_FAST_KILL', None)
	os.environ.pop('VORLESE_SKIP_PROCESS_CLEANUP', None)
	
	try:
		start_time = time.time()
		startup_cleanup()
		elapsed = time.time() - start_time
		print(f"✅ Normal startup cleanup: {elapsed:.2f} seconds")
	except Exception as e:
		print(f"❌ Normal startup cleanup failed: {e}")
	
	# Fast kill mode
	os.environ['VORLESE_FAST_KILL'] = '1'
	
	try:
		start_time = time.time()
		startup_cleanup()
		elapsed = time.time() - start_time
		print(f"✅ Fast kill startup cleanup: {elapsed:.2f} seconds")
	except Exception as e:
		print(f"❌ Fast kill startup cleanup failed: {e}")
	
	# Skip mode
	os.environ.pop('VORLESE_FAST_KILL', None)
	os.environ['VORLESE_SKIP_PROCESS_CLEANUP'] = '1'
	
	try:
		start_time = time.time()
		startup_cleanup()
		elapsed = time.time() - start_time
		print(f"✅ Skip cleanup mode: {elapsed:.2f} seconds")
	except Exception as e:
		print(f"❌ Skip cleanup mode failed: {e}")
	
	print()
	print("=" * 50)
	print("✅ All kill functionality tests completed!")

def test_batch_files():
	"""Test the batch files."""
	print("🧪 Testing batch file creation...")
	
	batch_files = [
		'start.bat',
		'start_fast.bat', 
		'start_force_kill.bat'
	]
	
	for batch_file in batch_files:
		if os.path.exists(batch_file):
			print(f"✅ {batch_file} exists")
		else:
			print(f"❌ {batch_file} missing")
	
	print("✅ Batch file test completed!")

if __name__ == "__main__":
	print("🚀 Starting kill functionality tests...")
	print()
	
	test_kill_functions()
	print()
	test_batch_files()
	
	print()
	print("🎉 All tests completed!") 