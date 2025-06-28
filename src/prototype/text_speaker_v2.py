#!/usr/bin/env python3
"""
Improved Text Speaker using NBSapi for better SAPI control.
"""

import threading
import time
import atexit
import os
import psutil
import signal
from typing import Optional, List, Dict, Set, Callable
from abc import ABC, abstractmethod
from threading import Lock

# Global thread registry to track all speech threads
_GLOBAL_THREAD_REGISTRY: Set[threading.Thread] = set()
_REGISTRY_LOCK = Lock()

# Process management
_CURRENT_PID = os.getpid()
_PROCESS_LOCK_FILE = "vorlese_app.lock"

try:
	from NBSapi import NBSapi
	NBSAPI_AVAILABLE = True
except ImportError:
	print("❌ NBSapi not available, falling back to pyttsx3")
	NBSAPI_AVAILABLE = False
	import pyttsx3


# Global thread registry functions
def register_speech_thread(thread: threading.Thread) -> None:
	"""Register a speech thread in the global registry."""
	with _REGISTRY_LOCK:
		_GLOBAL_THREAD_REGISTRY.add(thread)
	print(f"🔧 Registered speech thread: {thread.name}")

def unregister_speech_thread(thread: threading.Thread) -> None:
	"""Unregister a speech thread from the global registry."""
	with _REGISTRY_LOCK:
		_GLOBAL_THREAD_REGISTRY.discard(thread)
	print(f"🔧 Unregistered speech thread: {thread.name}")

def cleanup_all_speech_threads() -> None:
	"""Force cleanup of all registered speech threads."""
	print("🧹 Cleaning up all speech threads...")
	
	with _REGISTRY_LOCK:
		threads_to_cleanup = list(_GLOBAL_THREAD_REGISTRY)
	
	for thread in threads_to_cleanup:
		if thread.is_alive():
			print(f"🔧 Terminating thread: {thread.name}")
			try:
				thread.join(timeout=1.0)
				if thread.is_alive():
					print(f"⚠️ Thread {thread.name} did not terminate gracefully")
			except Exception as e:
				print(f"❌ Error terminating thread {thread.name}: {e}")
	
	with _REGISTRY_LOCK:
		_GLOBAL_THREAD_REGISTRY.clear()
	
	print("✅ All speech threads cleanup completed")

def kill_previous_instances_fast() -> None:
	"""Ultra-fast kill function - immediate force kill without graceful termination."""
	# Only kill previous instances if explicitly enabled
	if os.getenv('VORLESE_KILL_PREVIOUS', '').lower() not in ('1', 'true', 'yes'):
		print("⚡ Skipping kill previous instances (disabled by default)")
		print("   Set VORLESE_KILL_PREVIOUS=1 to enable")
		return
		
	print("⚡ Fast-killing previous instances...")
	
	current_pid = os.getpid()
	killed_count = 0
	
	try:
		for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
			try:
				if proc.info['pid'] == current_pid:
					continue
				
				# More selective criteria to avoid killing debuggers or other processes
				if (proc.info['name'] and 'python' in proc.info['name'].lower() and
					proc.info['cmdline'] and 
					any('main.py' in str(cmd) for cmd in proc.info['cmdline']) and
					not any('debugpy' in str(cmd) for cmd in proc.info['cmdline']) and  # Avoid VSCode debugger
					not any('pdb' in str(cmd) for cmd in proc.info['cmdline']) and     # Avoid Python debugger
					not any('.cursor' in str(cmd) for cmd in proc.info['cmdline']) and # Avoid Cursor editor
					not any('vscode' in str(cmd).lower() for cmd in proc.info['cmdline']) and # Avoid VSCode
					'vorlese' in ' '.join(proc.info['cmdline']).lower()):  # Only target our app
					
					print(f"⚡ Immediately killing PID {proc.info['pid']}")
					proc.kill()
					killed_count += 1
					
			except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
				continue
				
	except Exception as e:
		print(f"❌ Error in fast kill: {e}")
	
	if killed_count > 0:
		print(f"⚡ Fast-killed {killed_count} instance(s)")
	else:
		print("✅ No instances to kill")

def startup_cleanup() -> None:
	"""Perform startup cleanup of threads and processes."""
	print("🚀 Performing startup cleanup...")
	kill_previous_instances_fast()
	cleanup_all_speech_threads()
	
	try:
		current_pid = os.getpid()
		if os.path.exists(_PROCESS_LOCK_FILE):
			os.remove(_PROCESS_LOCK_FILE)
			print("🧹 Removed old lock file")
		
		with open(_PROCESS_LOCK_FILE, 'w') as f:
			f.write(str(current_pid))
		print(f"🔒 Created lock file for PID {current_pid}")
	except Exception as e:
		print(f"❌ Error creating lock file: {e}")
	
	print("✅ Startup cleanup completed")


class TextSpeakerBase(ABC):
	"""Base class for text speakers."""
	
	def __init__(self):
		self._is_speaking = False
		self._is_paused = False
		self._current_text = ""
		self._lock = threading.Lock()
		atexit.register(self.cleanup)
		
	@abstractmethod
	def speak(self, text: str, voice_name: str = "", speed: float = 1.0, word_callback: Optional[Callable[[int, int], None]] = None) -> None:
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
		self._word_callback = None
		print("✅ NBSapi speaker initialized")
		
	def speak(self, text: str, voice_name: str = "", speed: float = 1.0, word_callback: Optional[Callable[[int, int], None]] = None) -> None:
		"""Speak text using NBSapi with proper SAPI control."""
		print(f"🔊 NBSapi speaking: {text[:50]}...")
		
		self.stop()
		
		with self._lock:
			self._current_text = text
			self._is_speaking = True
			self._is_paused = False
			self._word_callback = word_callback
			
		if voice_name:
			self._set_voice(voice_name)
			
		sapi_rate = round((speed - 1.0) * 10)
		sapi_rate = max(-10, min(10, sapi_rate))
		self.tts.SetRate(sapi_rate)
		
		self._speech_thread = threading.Thread(
			target=self._speak_worker,
			args=(text,),
			daemon=True,
			name=f"NBSapi-Speech-{id(self)}"
		)
		register_speech_thread(self._speech_thread)
		self._speech_thread.start()
		
	def _speak_worker(self, text: str) -> None:
		"""Worker thread for speaking."""
		current_thread = threading.current_thread()
		try:
			if self._word_callback:
				def on_word_boundary(location, length):
					try:
						if self._word_callback:
							self._word_callback(location, length)
					except Exception as e:
						print(f"❌ Error in NBSapi word callback: {e}")
				
				try:
					self.tts.SetWordCallBack(on_word_boundary)
				except AttributeError:
					print("⚠️ NBSapi word callbacks not supported - continuing without highlighting")

			self.tts.Speak(text, 1)
			
			while True:
				with self._lock:
					if not self._is_speaking:
						break
				
				status = self.tts.GetStatus("RunningState")
				if status == 1: # Completed
					break
				
				time.sleep(0.1)
			
		except Exception as e:
			print(f"❌ NBSapi speak error: {e}")
		finally:
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
				self._word_callback = None
			unregister_speech_thread(current_thread)
				
	def pause(self) -> None:
		"""Pause speech using NBSapi."""
		try:
			self.tts.Pause()
			with self._lock:
				self._is_paused = True
		except Exception as e:
			print(f"❌ NBSapi pause error: {e}")
			
	def resume(self) -> None:
		"""Resume speech using NBSapi."""
		try:
			self.tts.Resume()
			with self._lock:
				self._is_paused = False
		except Exception as e:
			print(f"❌ NBSapi resume error: {e}")
			
	def stop(self) -> None:
		"""Stop speech using NBSapi."""
		try:
			self.tts.Stop()
			if self._word_callback:
				try:
					self.tts.SetWordCallBack(None)
				except AttributeError:
					pass  # Word callbacks not supported, ignore
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
		except Exception as e:
			print(f"❌ NBSapi stop error: {e}")
			
	def cleanup(self) -> None:
		"""Cleanup NBSapi resources."""
		self.stop()
		if self._speech_thread and self._speech_thread.is_alive():
			self._speech_thread.join(timeout=1.0)
			unregister_speech_thread(self._speech_thread)
			
	def _set_voice(self, voice_name: str) -> None:
		"""Set voice by name."""
		try:
			voices = self.tts.GetVoices()
			for i, voice_info in enumerate(voices):
				if voice_name in voice_info.get("Name", ""):
					self.tts.SetVoice(i, "by_index")
					return
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
		self._word_callback = None
		print("✅ pyttsx3 speaker initialized (fallback)")
		
	def speak(self, text: str, voice_name: str = "", speed: float = 1.0, word_callback: Optional[Callable[[int, int], None]] = None) -> None:
		"""Speak text using pyttsx3."""
		self.stop()
		
		with self._lock:
			self._current_text = text
			self._is_speaking = True
			self._is_paused = False
			self._word_callback = word_callback
			
		if voice_name:
			self._set_voice(voice_name)
			
		pyttsx3_rate = int(200 * speed)
		self.engine.setProperty('rate', pyttsx3_rate)
		
		if self._word_callback:
			def on_word(name, location, length):
				try:
					if self._word_callback:
						self._word_callback(location, length)
				except Exception as e:
					print(f"Error in pyttsx3 word callback: {e}")
			self.engine.connect('started-word', on_word)

		self._speech_thread = threading.Thread(
			target=self._speak_worker,
			args=(text,),
			daemon=True,
			name=f"Pyttsx3-Speech-{id(self)}"
		)
		register_speech_thread(self._speech_thread)
		self._speech_thread.start()
		
	def _speak_worker(self, text: str) -> None:
		"""Worker thread for speaking."""
		current_thread = threading.current_thread()
		try:
			self.engine.say(text)
			self.engine.runAndWait()
		except Exception as e:
			print(f"❌ pyttsx3 speak error: {e}")
		finally:
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
				if self._word_callback:
					pass
			unregister_speech_thread(current_thread)
				
	def pause(self) -> None:
		"""Pause not supported in basic pyttsx3."""
		self.stop()
		
	def resume(self) -> None:
		"""Resume not supported in basic pyttsx3."""
		pass
		
	def stop(self) -> None:
		"""Stop speech."""
		try:
			self.engine.stop()
			if self._word_callback:
				self.engine.disconnect('started-word')
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
		except Exception as e:
			print(f"❌ pyttsx3 stop error: {e}")
			
	def cleanup(self) -> None:
		"""Cleanup pyttsx3 resources."""
		self.stop()
		if self._speech_thread and self._speech_thread.is_alive():
			self._speech_thread.join(timeout=1.0)
			unregister_speech_thread(self._speech_thread)
			
	def _set_voice(self, voice_name: str) -> None:
		"""Set voice by name."""
		try:
			voices = self.engine.getProperty('voices')
			for voice in voices:
				if voice_name in voice.name:
					self.engine.setProperty('voice', voice.id)
					return
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
				
		return Pyttsx3Speaker()

def cleanup_all_speakers():
	"""Cleanup function to be called on program exit."""
	print("🧹 Cleaning up all speakers...")
	cleanup_all_speech_threads()
	
	try:
		if os.path.exists(_PROCESS_LOCK_FILE):
			os.remove(_PROCESS_LOCK_FILE)
			print("🧹 Removed lock file")
	except Exception as e:
		print(f"❌ Error removing lock file: {e}")