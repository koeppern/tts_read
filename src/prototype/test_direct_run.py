#!/usr/bin/env python3
"""
Direct test of main application to see where it fails.
"""

import os
import sys
import time
import threading

def test_direct_run():
	"""Test running the main application directly."""
	print("🧪 Direct Run Test")
	print("=" * 40)
	
	# Force console mode
	os.environ['VORLESE_CONSOLE_MODE'] = '1'
	
	try:
		print("📍 Importing main...")
		from main import main
		print("✅ Import successful")
		
		print("📍 Starting main in background thread...")
		
		# Run main in a separate thread so we can control it
		main_thread = threading.Thread(target=main, daemon=True)
		main_thread.start()
		
		print("📍 Main thread started, waiting 10 seconds...")
		time.sleep(10)
		
		if main_thread.is_alive():
			print("✅ Main thread is still running after 10 seconds!")
			print("📍 Application is working correctly")
			
			# Let it run a bit more
			time.sleep(5)
			
			print("📍 Stopping test...")
			return True
		else:
			print("❌ Main thread exited immediately")
			return False
			
	except Exception as e:
		print(f"❌ Error: {e}")
		import traceback
		traceback.print_exc()
		return False

def test_minimal_run():
	"""Test with minimal configuration."""
	print("🧪 Minimal Run Test")
	print("=" * 40)
	
	# Set all environment variables for safe startup
	os.environ['VORLESE_CONSOLE_MODE'] = '1'
	os.environ['VORLESE_SKIP_PROCESS_CLEANUP'] = '1'
	
	try:
		from main import VorleseApp
		
		print("📍 Creating VorleseApp...")
		app = VorleseApp()
		print("✅ VorleseApp created")
		
		print("📍 Starting app.run() in thread...")
		
		def run_app():
			try:
				app.run()
			except Exception as e:
				print(f"❌ Error in app.run(): {e}")
		
		run_thread = threading.Thread(target=run_app, daemon=True)
		run_thread.start()
		
		print("📍 Waiting 10 seconds...")
		time.sleep(10)
		
		if run_thread.is_alive():
			print("✅ App is running successfully!")
			
			print("📍 Cleaning up...")
			app.cleanup()
			return True
		else:
			print("❌ App exited immediately")
			return False
			
	except Exception as e:
		print(f"❌ Error: {e}")
		import traceback
		traceback.print_exc()
		return False

if __name__ == "__main__":
	print("🚀 Testing Direct Application Run")
	print("=" * 50)
	
	print()
	success1 = test_direct_run()
	
	print()
	success2 = test_minimal_run()
	
	print()
	print("=" * 50)
	if success1 or success2:
		print("✅ At least one test passed - application can run!")
	else:
		print("❌ All tests failed - there are issues with the application") 