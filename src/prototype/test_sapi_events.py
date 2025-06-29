#!/usr/bin/env python3
"""
Diagnostic script to explore NBSapi's SAPI event capabilities.
Based on Microsoft SAPI documentation for proper Word Boundary Events.
"""

import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
	from NBSapi import NBSapi
	print("✅ NBSapi imported successfully")
except ImportError as e:
	print(f"❌ Failed to import NBSapi: {e}")
	sys.exit(1)

def explore_nbsapi_methods():
	"""Explore all available NBSapi methods for event handling."""
	print("\n🔍 Exploring NBSapi methods...")
	
	try:
		tts = NBSapi()
		print("✅ NBSapi TTS object created")
		
		all_methods = dir(tts)
		print(f"\n📋 Total methods available: {len(all_methods)}")
		
		# Look for event-related methods
		event_methods = [method for method in all_methods if any(keyword in method.lower() for keyword in ['event', 'notify', 'callback', 'interest', 'word', 'boundary'])]
		
		print(f"\n🎯 Event-related methods found: {len(event_methods)}")
		for method in sorted(event_methods):
			print(f"  - {method}")
		
		# Look for SAPI-specific methods
		sapi_methods = [method for method in all_methods if any(keyword in method.lower() for keyword in ['sapi', 'set', 'get', 'speak', 'voice'])]
		
		print(f"\n🔧 SAPI control methods found: {len(sapi_methods)}")
		for method in sorted(sapi_methods):
			print(f"  - {method}")
		
		# Test specific methods we're interested in
		print(f"\n🧪 Testing specific methods:")
		
		methods_to_test = [
			'SetWordCallBack',
			'SetCallBack', 
			'SetInterest',
			'SetNotifyCallbackFunction',
			'SetNotifyCallbackInterface',
			'SetNotifyWindowMessage',
			'SetNotifyWin32Event',
			'GetEvents',
			'SetEventInterest',
			'EnableEvents',
			'OnWordBoundary',
			'WordBoundary'
		]
		
		for method_name in methods_to_test:
			if hasattr(tts, method_name):
				print(f"  ✅ {method_name} - Available")
				try:
					method = getattr(tts, method_name)
					print(f"     Type: {type(method)}")
				except Exception as e:
					print(f"     Error accessing: {e}")
			else:
				print(f"  ❌ {method_name} - Not available")
		
		return tts
		
	except Exception as e:
		print(f"❌ Error exploring NBSapi: {e}")
		import traceback
		traceback.print_exc()
		return None

def test_word_callback_simple(tts):
	"""Test simple word callback approaches."""
	print("\n🧪 Testing simple word callback approaches...")
	
	test_text = "This is a test sentence for word highlighting."
	
	def word_callback(location, length):
		"""Simple word boundary callback."""
		try:
			word = test_text[location:location+length]
			print(f"🔤 Word callback: '{word}' at position {location}, length {length}")
		except Exception as e:
			print(f"❌ Callback error: {e}")
	
	# Test method 1: SetWordCallBack
	if hasattr(tts, 'SetWordCallBack'):
		print("🔄 Testing SetWordCallBack...")
		try:
			tts.SetWordCallBack(word_callback)
			print("✅ SetWordCallBack registered")
			
			print("🎙️ Speaking with SetWordCallBack...")
			tts.Speak(test_text, 1)  # Synchronous speech
			
			print("✅ Speech completed")
			
		except Exception as e:
			print(f"❌ SetWordCallBack error: {e}")
			import traceback
			traceback.print_exc()
	
	# Test method 2: SetCallBack 
	elif hasattr(tts, 'SetCallBack'):
		print("🔄 Testing SetCallBack...")
		try:
			tts.SetCallBack(word_callback)
			print("✅ SetCallBack registered")
			
			print("🎙️ Speaking with SetCallBack...")
			tts.Speak(test_text, 1)  # Synchronous speech
			
			print("✅ Speech completed")
			
		except Exception as e:
			print(f"❌ SetCallBack error: {e}")
			import traceback
			traceback.print_exc()
	
	else:
		print("⚠️ No simple callback methods available")

def test_sapi_events(tts):
	"""Test SAPI event-based approach."""
	print("\n🧪 Testing SAPI event-based approach...")
	
	# Look for SAPI event constants
	import NBSapi as nbsapi_module
	event_constants = [attr for attr in dir(nbsapi_module) if 'EVENT' in attr or 'SPEI' in attr]
	if event_constants:
		print(f"📋 Found event constants: {event_constants}")
	else:
		print("⚠️ No event constants found in NBSapi")
	
	# Test event interest setting
	if hasattr(tts, 'SetInterest'):
		print("🔄 Testing SetInterest...")
		try:
			# Try to set interest in word boundary events
			# SPEI_WORD_BOUNDARY is typically 0x00000008 in SAPI
			word_boundary_flag = 0x00000008
			tts.SetInterest(word_boundary_flag, word_boundary_flag)
			print("✅ SetInterest called successfully")
		except Exception as e:
			print(f"❌ SetInterest error: {e}")
	
	# Test notification methods
	if hasattr(tts, 'SetNotifyCallbackFunction'):
		print("🔄 Testing SetNotifyCallbackFunction...")
		try:
			def event_callback(wParam, lParam):
				print(f"📢 Event callback: wParam={wParam}, lParam={lParam}")
			
			tts.SetNotifyCallbackFunction(event_callback, 0, 0)
			print("✅ SetNotifyCallbackFunction registered")
		except Exception as e:
			print(f"❌ SetNotifyCallbackFunction error: {e}")

def main():
	"""Main diagnostic function."""
	print("🚀 NBSapi SAPI Event Diagnostics")
	print("=" * 50)
	
	tts = explore_nbsapi_methods()
	if not tts:
		return
	
	test_word_callback_simple(tts)
	test_sapi_events(tts)
	
	print("\n✅ Diagnostic completed")

if __name__ == "__main__":
	main() 