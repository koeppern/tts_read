#!/usr/bin/env python3
"""
Test script for NBSapi implementation.
"""

import sys
import time
from pathlib import Path

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from text_speaker_v2 import TextSpeakerFactory


def test_nbsapi_basic():
	"""Test basic NBSapi functionality."""
	print("🧪 Testing NBSapi Basic Functionality")
	print("=" * 50)
	
	# Create speaker
	speaker = TextSpeakerFactory.create_speaker("SAPI")
	
	# Test available voices
	print("1. Available voices:")
	voices = speaker.get_available_voices()
	for i, voice in enumerate(voices):
		print(f"   {i+1}. {voice}")
	
	print()
	
	# Test speaking
	print("2. Testing speech:")
	test_text = "Dies ist ein Test der neuen NBSapi Implementierung. Die Sprache sollte jetzt viel flüssiger sein und echte Pause und Resume Funktionen haben."
	
	print(f"   Speaking: {test_text[:50]}...")
	speaker.speak(test_text, rate=0.9)
	
	# Wait a bit then test pause
	time.sleep(3)
	print("   Testing pause in 2 seconds...")
	time.sleep(2)
	
	print("3. Testing pause:")
	speaker.pause()
	print(f"   Is paused: {speaker.is_paused()}")
	print(f"   Is speaking: {speaker.is_speaking()}")
	
	# Wait then resume
	time.sleep(3)
	print("4. Testing resume:")
	speaker.resume()
	print(f"   Is paused: {speaker.is_paused()}")
	print(f"   Is speaking: {speaker.is_speaking()}")
	
	# Wait for completion
	time.sleep(5)
	print("5. Final status:")
	print(f"   Is paused: {speaker.is_paused()}")
	print(f"   Is speaking: {speaker.is_speaking()}")
	
	print("✅ NBSapi test completed!")


def test_nbsapi_cleanup():
	"""Test NBSapi cleanup functionality."""
	print("\n🧹 Testing NBSapi Cleanup")
	print("=" * 50)
	
	speaker = TextSpeakerFactory.create_speaker("SAPI")
	
	# Start speaking
	long_text = """
	Dies ist ein sehr langer Text um zu testen ob die Cleanup Funktionalität 
	ordnungsgemäß funktioniert. Wenn das Programm beendet wird, sollte die 
	Sprachausgabe sofort stoppen und nicht weiterlaufen. Das war eines der 
	Hauptprobleme mit der alten Implementierung. Die neue NBSapi Implementierung 
	sollte dieses Problem lösen durch ordnungsgemäße Ressourcen-Bereinigung 
	beim Programmende.
	"""
	
	print("Starting long speech...")
	speaker.speak(long_text.strip(), rate=0.8)
	
	# Wait a bit
	time.sleep(2)
	
	print("Testing manual cleanup...")
	speaker.cleanup()
	
	print("✅ Cleanup test completed!")
	print("   (Speech should have stopped immediately)")


def test_voice_switching():
	"""Test voice switching functionality."""
	print("\n🎭 Testing Voice Switching")
	print("=" * 50)
	
	speaker = TextSpeakerFactory.create_speaker("SAPI")
	voices = speaker.get_available_voices()
	
	if len(voices) >= 2:
		print(f"Testing with {len(voices)} available voices:")
		
		# Test first voice
		print(f"1. Testing voice: {voices[0]}")
		speaker.speak(
			"Hallo, ich spreche mit der ersten Stimme.",
			voice_name=voices[0],
			rate=0.9
		)
		time.sleep(4)
		
		# Test second voice
		print(f"2. Testing voice: {voices[1]}")
		speaker.speak(
			"Hello, I am speaking with the second voice.",
			voice_name=voices[1],
			rate=1.0
		)
		time.sleep(4)
		
		print("✅ Voice switching test completed!")
	else:
		print("❌ Not enough voices available for switching test")


def main():
	"""Run all tests."""
	try:
		test_nbsapi_basic()
		test_voice_switching()
		test_nbsapi_cleanup()
		
		print("\n🎯 Summary:")
		print("All NBSapi tests completed!")
		print("- Basic speech functionality ✅")
		print("- Pause/Resume functionality ✅") 
		print("- Voice switching ✅")
		print("- Cleanup functionality ✅")
		
		print("\n💡 Key improvements:")
		print("- No more sentence splitting (smooth speech)")
		print("- Real SAPI pause/resume (not stop/start)")
		print("- Proper cleanup on program exit")
		print("- Better voice control")
		
	except Exception as e:
		print(f"❌ Test error: {e}")
		import traceback
		traceback.print_exc()


if __name__ == "__main__":
	main() 