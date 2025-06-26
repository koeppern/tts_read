#!/usr/bin/env python3
"""
Improved Text Speaker using NBSapi for better SAPI control.
"""

import threading
import time
import atexit
from typing import Optional, List
from abc import ABC, abstractmethod

try:
	from NBSapi import NBSapi
	NBSAPI_AVAILABLE = True
except ImportError:
	print("❌ NBSapi not available, falling back to pyttsx3")
	NBSAPI_AVAILABLE = False
	import pyttsx3


class TextSpeakerBase(ABC):
	"""Base class for text speakers."""
	
	def __init__(self):
		self._is_speaking = False
		self._is_paused = False
		self._current_text = ""
		self._lock = threading.Lock()
		
		# Register cleanup on program exit
		atexit.register(self.cleanup)
		
	@abstractmethod
	def speak(self, text: str, voice_name: str = "", rate: float = 1.0) -> None:
		"""Speak the given text."""
		pass
		
	@abstractmethod
	def pause(self) -> None:
		"""Pause current speech."""
		pass
		
	@abstractmethod
	def resume(self) -> None:
		"""Resume paused speech."""
		pass
		
	@abstractmethod
	def stop(self) -> None:
		"""Stop current speech."""
		pass
		
	@abstractmethod
	def cleanup(self) -> None:
		"""Cleanup resources on program exit."""
		pass
		
	def is_speaking(self) -> bool:
		"""Check if currently speaking."""
		with self._lock:
			return self._is_speaking and not self._is_paused
			
	def is_paused(self) -> bool:
		"""Check if currently paused."""
		with self._lock:
			return self._is_paused
			
	@abstractmethod
	def get_available_voices(self) -> List[str]:
		"""Get list of available voices."""
		pass


class NBSapiSpeaker(TextSpeakerBase):
	"""Text speaker using NBSapi for better SAPI control."""
	
	def __init__(self):
		super().__init__()
		self.tts = NBSapi()
		self._speech_thread = None
		print("✅ NBSapi speaker initialized")
		
	def speak(self, text: str, voice_name: str = "", rate: float = 1.0) -> None:
		"""Speak text using NBSapi with proper SAPI control."""
		print(f"🔊 NBSapi speaking: {text[:50]}...")
		
		# Stop any current speech
		self.stop()
		
		with self._lock:
			self._current_text = text
			self._is_speaking = True
			self._is_paused = False
			
		# Set voice if specified
		if voice_name:
			self._set_voice(voice_name)
			
		# Set rate (NBSapi uses -10 to 10 scale)
		# Convert our 0.5-2.0 scale to -10 to 10
		sapi_rate = round((rate - 1.0) * 10)
		sapi_rate = max(-10, min(10, sapi_rate))
		self.tts.SetRate(sapi_rate)
		
		# Start speaking in background thread
		self._speech_thread = threading.Thread(
			target=self._speak_worker,
			args=(text,),
			daemon=True
		)
		self._speech_thread.start()
		
	def _speak_worker(self, text: str) -> None:
		"""Worker thread for speaking."""
		try:
			# Speak without waiting (flag=1 for async)
			self.tts.Speak(text, 1)
			
			# Wait for speech to complete
			while True:
				status = self.tts.GetStatus("RunningState")
				if status != 2:  # Not speaking
					break
				time.sleep(0.1)
				
		except Exception as e:
			print(f"❌ NBSapi speak error: {e}")
		finally:
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
				
	def pause(self) -> None:
		"""Pause speech using NBSapi."""
		print("⏸️ NBSapi pausing...")
		try:
			self.tts.Pause()
			with self._lock:
				self._is_paused = True
			print("✅ NBSapi paused")
		except Exception as e:
			print(f"❌ NBSapi pause error: {e}")
			
	def resume(self) -> None:
		"""Resume speech using NBSapi."""
		print("▶️ NBSapi resuming...")
		try:
			self.tts.Resume()
			with self._lock:
				self._is_paused = False
			print("✅ NBSapi resumed")
		except Exception as e:
			print(f"❌ NBSapi resume error: {e}")
			
	def stop(self) -> None:
		"""Stop speech using NBSapi."""
		try:
			self.tts.Stop()
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
		except Exception as e:
			print(f"❌ NBSapi stop error: {e}")
			
	def cleanup(self) -> None:
		"""Cleanup NBSapi resources."""
		print("🧹 NBSapi cleanup...")
		try:
			self.stop()
			# Wait for speech thread to finish
			if self._speech_thread and self._speech_thread.is_alive():
				self._speech_thread.join(timeout=2.0)
		except Exception as e:
			print(f"❌ NBSapi cleanup error: {e}")
			
	def _set_voice(self, voice_name: str) -> None:
		"""Set voice by name."""
		try:
			voices = self.tts.GetVoices()
			for i, voice_info in enumerate(voices):
				if voice_name in voice_info.get("Name", ""):
					self.tts.SetVoice(i, "by_index")
					print(f"✅ Voice set to: {voice_name}")
					return
			print(f"❌ Voice not found: {voice_name}")
		except Exception as e:
			print(f"❌ Error setting voice: {e}")
			
	def get_available_voices(self) -> List[str]:
		"""Get available voices from NBSapi."""
		try:
			voices = self.tts.GetVoices()
			return [voice.get("Name", f"Voice {i}") for i, voice in enumerate(voices)]
		except Exception as e:
			print(f"❌ Error getting voices: {e}")
			return []


class Pyttsx3Speaker(TextSpeakerBase):
	"""Fallback text speaker using pyttsx3."""
	
	def __init__(self):
		super().__init__()
		self.engine = pyttsx3.init()
		self._speech_thread = None
		print("✅ pyttsx3 speaker initialized (fallback)")
		
	def speak(self, text: str, voice_name: str = "", rate: float = 1.0) -> None:
		"""Speak text using pyttsx3."""
		print(f"🔊 pyttsx3 speaking: {text[:50]}...")
		
		# Stop any current speech
		self.stop()
		
		with self._lock:
			self._current_text = text
			self._is_speaking = True
			self._is_paused = False
			
		# Set voice properties
		if voice_name:
			self._set_voice(voice_name)
			
		# Set rate (pyttsx3 typically uses 100-300 range)
		pyttsx3_rate = int(200 * rate)
		self.engine.setProperty('rate', pyttsx3_rate)
		
		# Start speaking in background thread
		self._speech_thread = threading.Thread(
			target=self._speak_worker,
			args=(text,),
			daemon=True
		)
		self._speech_thread.start()
		
	def _speak_worker(self, text: str) -> None:
		"""Worker thread for speaking."""
		try:
			self.engine.say(text)
			self.engine.runAndWait()
		except Exception as e:
			print(f"❌ pyttsx3 speak error: {e}")
		finally:
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
				
	def pause(self) -> None:
		"""Pause not supported in basic pyttsx3."""
		print("⏸️ pyttsx3 pause not supported - stopping instead")
		self.stop()
		
	def resume(self) -> None:
		"""Resume not supported in basic pyttsx3."""
		print("▶️ pyttsx3 resume not supported")
		
	def stop(self) -> None:
		"""Stop speech."""
		try:
			self.engine.stop()
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
		except Exception as e:
			print(f"❌ pyttsx3 stop error: {e}")
			
	def cleanup(self) -> None:
		"""Cleanup pyttsx3 resources."""
		print("🧹 pyttsx3 cleanup...")
		try:
			self.stop()
			if self._speech_thread and self._speech_thread.is_alive():
				self._speech_thread.join(timeout=2.0)
		except Exception as e:
			print(f"❌ pyttsx3 cleanup error: {e}")
			
	def _set_voice(self, voice_name: str) -> None:
		"""Set voice by name."""
		try:
			voices = self.engine.getProperty('voices')
			for voice in voices:
				if voice_name in voice.name:
					self.engine.setProperty('voice', voice.id)
					print(f"✅ Voice set to: {voice_name}")
					return
			print(f"❌ Voice not found: {voice_name}")
		except Exception as e:
			print(f"❌ Error setting voice: {e}")
			
	def get_available_voices(self) -> List[str]:
		"""Get available voices from pyttsx3."""
		try:
			voices = self.engine.getProperty('voices')
			return [voice.name for voice in voices if voice.name]
		except Exception as e:
			print(f"❌ Error getting voices: {e}")
			return []


class TextSpeakerFactory:
	"""Factory for creating text speakers."""
	
	@staticmethod
	def create_speaker(engine_type: str = "SAPI") -> TextSpeakerBase:
		"""Create a text speaker instance."""
		if engine_type == "SAPI" and NBSAPI_AVAILABLE:
			try:
				return NBSapiSpeaker()
			except Exception as e:
				print(f"❌ Failed to create NBSapi speaker: {e}")
				print("🔄 Falling back to pyttsx3...")
				
		# Fallback to pyttsx3
		return Pyttsx3Speaker()


# Global cleanup function
def cleanup_all_speakers():
	"""Cleanup function to be called on program exit."""
	print("🧹 Cleaning up all speakers...")


# Register global cleanup
atexit.register(cleanup_all_speakers) 