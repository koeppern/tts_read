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
		"""Check if currently speaking (not paused)."""
		with self._lock:
			return self._is_speaking and not self._is_paused
			
	def is_active(self) -> bool:
		"""Check if speech is active (speaking or paused)."""
		with self._lock:
			return self._is_speaking
			
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
		print(f"🔊 DEBUG: Neue Speak-Anfrage erhalten: {text[:50]}...")
		
		with self._lock:
			was_speaking = self._is_speaking
			was_paused = self._is_paused
		
		print(f"🔊 DEBUG: Aktueller Status - speaking: {was_speaking}, paused: {was_paused}")
		
		print("🛑 DEBUG: Stoppe aktuelles Vorlesen...")
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
			# Store text for word position calculation
			self._current_text = text
			
			if self._word_callback:
				print("🔊 DEBUG: Word-Callback aktiviert, registriere NBSapi-Callback...")
				
				def on_word_boundary(location, length):
					"""NBSapi word boundary callback handler."""
					try:
						print(f"📝 DEBUG: Word-Callback aufgerufen: Position={location}, Länge={length}")
						if self._word_callback and location >= 0 and length > 0:
							# Ensure we don't go beyond text boundaries
							if location + length <= len(self._current_text):
								word = self._current_text[location:location+length]
								print(f"🔤 DEBUG: Hervorgehobenes Wort: '{word}'")
								self._word_callback(location, length)
							else:
								print(f"⚠️ DEBUG: Word-Position außerhalb des Textes: {location}+{length} > {len(self._current_text)}")
					except Exception as e:
						print(f"❌ DEBUG: Fehler im Word-Callback: {e}")
						import traceback
						traceback.print_exc()
				
				try:
					# Try different NBSapi word callback methods
					if hasattr(self.tts, 'SetWordCallBack'):
						print("✅ DEBUG: Verwende SetWordCallBack")
						self.tts.SetWordCallBack(on_word_boundary)
					elif hasattr(self.tts, 'SetCallBack'):
						print("✅ DEBUG: Verwende SetCallBack")
						self.tts.SetCallBack(on_word_boundary)
					else:
						print("⚠️ DEBUG: Keine Word-Callback-Methode gefunden")
						available_methods = [method for method in dir(self.tts) if 'callback' in method.lower() or 'word' in method.lower()]
						print(f"🔍 DEBUG: Verfügbare Methoden: {available_methods}")
						print("🔄 DEBUG: Fallback-Highlighting wird verwendet")
						# DON'T disable word_callback - we need it for fallback highlighting!
				except Exception as e:
					print(f"❌ DEBUG: Fehler beim Registrieren des Word-Callbacks: {e}")
					print("🔄 DEBUG: Fallback-Highlighting wird verwendet")
					# DON'T disable word_callback - we need it for fallback highlighting!
			else:
				print("📝 DEBUG: Kein Word-Callback verfügbar")

			print("🎙️ DEBUG: Starte NBSapi.Speak()...")
			
			# Check if word callback is set but NBSapi doesn't support it
			use_fallback_highlighting = (self._word_callback and 
										not hasattr(self.tts, 'SetWordCallBack') and 
										not hasattr(self.tts, 'SetCallBack'))
			
			if use_fallback_highlighting:
				print("🔄 DEBUG: Verwende Fallback-Word-Highlighting...")
				self._speak_with_word_highlighting_fallback(text)
			else:
				self.tts.Speak(text, 1)
			
			status_check_count = 0
			while True:
				with self._lock:
					if not self._is_speaking:
						print("🔚 DEBUG: _is_speaking ist False - beende Speech-Thread")
						break
					
					# Don't check GetStatus when paused - wait for resume or stop
					if self._is_paused:
						if status_check_count % 50 == 0:  # Every 5 seconds
							print("⏸️ DEBUG: Speech-Thread wartet (pausiert)")
						status_check_count += 1
						time.sleep(0.1)
						continue
				
				# Only check status when not paused
				try:
					status = self.tts.GetStatus("RunningState")
					if status_check_count % 10 == 0:  # Every second
						print(f"🔊 DEBUG: SAPI Status: {status} (0=speaking, 1=completed)")
					
					if status == 1: # Completed (and not paused)
						with self._lock:
							if not self._is_paused:  # Only break if truly completed, not paused
								print("✅ DEBUG: SAPI completed - beende Speech-Thread")
								break
							else:
								print("⚠️ DEBUG: SAPI zeigt 'completed' aber wir sind pausiert - ignoriere")
				except Exception as e:
					if status_check_count % 50 == 0:  # Occasional debug
						print(f"⚠️ DEBUG: GetStatus error: {e}")
				
				status_check_count += 1
				time.sleep(0.1)
			
		except Exception as e:
			print(f"❌ DEBUG: NBSapi speak error: {e}")
			import traceback
			traceback.print_exc()
		finally:
			print("🔚 DEBUG: Speech-Thread wird beendet, räume auf...")
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
				self._word_callback = None
			unregister_speech_thread(current_thread)
			print("✅ DEBUG: Speech-Thread erfolgreich beendet")
	
	def _speak_with_word_highlighting_fallback(self, text: str) -> None:
		"""Adaptive word highlighting synchronized with real SAPI speech progress."""
		import re
		
		print("🔄 Starting adaptive word highlighting...")
		
		# Split text into words and track positions
		words = []
		for match in re.finditer(r'\S+', text):
			word = match.group()
			start_pos = match.start()
			end_pos = match.end()
			words.append({
				'text': word,
				'start': start_pos,
				'end': end_pos,
				'length': len(word)
			})
		
		print(f"📝 Found {len(words)} words for highlighting")
		
		# Start speaking the whole text
		speech_start_time = time.time()
		self.tts.Speak(text, 1)
		
		# Adaptive highlighting algorithm
		self._adaptive_word_highlighting(words, speech_start_time, text)
		
	def _adaptive_word_highlighting(self, words, speech_start_time, full_text):
		"""Adaptive word highlighting that learns from actual speech timing."""
		
		# Initial estimates based on typical speech patterns
		# Average speaking rate: 150-200 words per minute
		# Adjust based on SAPI rate settings if available
		try:
			sapi_rate = self.tts.GetRate()  # SAPI rate: -10 to +10
			# Convert SAPI rate to multiplier (rate 0 = normal, positive = faster)
			rate_multiplier = 1.0 + (sapi_rate * 0.1)  # Rough approximation
			base_chars_per_second = 12.0 * rate_multiplier  # Adaptive base rate
		except:
			base_chars_per_second = 12.0  # Fallback
		
		print(f"⏱️ Using adaptive speech rate: {base_chars_per_second:.1f} chars/sec")
		
		# Track actual vs expected timing for learning
		last_word_time = speech_start_time
		cumulative_chars = 0
		timing_corrections = []
		
		for i, word_info in enumerate(words):
			# Check if we should stop
			with self._lock:
				if not self._is_speaking:
					print("🔚 DEBUG: Highlighting stopped - _is_speaking ist False")
					break
				if self._is_paused:
					print(f"⏸️ DEBUG: Highlighting pausiert bei Wort '{word_info['text']}'")
			
			# Handle pause separately outside the lock to avoid deadlocks
			if self._is_paused:
				pause_start = time.time()
				pause_logged = False
				while True:
					with self._lock:
						if not self._is_speaking:
							print("🔚 DEBUG: Speech stopped während Pause")
							return
						if not self._is_paused:
							break
					
					if not pause_logged:
						print(f"⏸️ DEBUG: Warte auf Resume bei Wort '{word_info['text']}'...")
						pause_logged = True
					time.sleep(0.1)
				
				# Adjust speech start time for pause duration
				pause_duration = time.time() - pause_start
				speech_start_time += pause_duration
				print(f"▶️ DEBUG: Resume nach {pause_duration:.1f}s Pause, Timeline angepasst")
			
			# Calculate expected time for this word
			cumulative_chars += word_info['length'] + 1  # +1 for space
			
			# Apply timing corrections from previous words
			if timing_corrections:
				# Use recent corrections to adjust rate
				recent_corrections = timing_corrections[-3:]  # Last 3 corrections
				avg_correction = sum(recent_corrections) / len(recent_corrections)
				adjusted_rate = base_chars_per_second * avg_correction
			else:
				adjusted_rate = base_chars_per_second
			
			expected_word_time = speech_start_time + (cumulative_chars / adjusted_rate)
			
			# Wait until it's time for this word, but also check SAPI status
			current_time = time.time()
			wait_time = expected_word_time - current_time
			
			# Intelligent waiting: check SAPI status while waiting
			wait_start = time.time()
			while wait_time > 0 and self._is_speaking:
				# Check if speech is still running
				try:
					status = self.tts.GetStatus("RunningState")
					if status == 1:  # Completed
						# Speech finished earlier than expected
						remaining_words = len(words) - i
						if remaining_words > 1:
							print(f"⚡ Speech completed early, highlighting remaining {remaining_words} words quickly")
							# Highlight remaining words quickly
							for j in range(i, len(words)):
								remaining_word = words[j]
								if self._word_callback:
									self._word_callback(remaining_word['start'], remaining_word['length'])
								time.sleep(0.1)  # Brief pause between quick highlights
							return
						break
				except:
					pass
				
				# Sleep in small increments to remain responsive
				sleep_time = min(wait_time, 0.05)
				time.sleep(sleep_time)
				current_time = time.time()
				wait_time = expected_word_time - current_time
			
			# Highlight the word
			actual_word_time = time.time()
			try:
				print(f"🔤 Highlighting: '{word_info['text']}'")
				if self._word_callback:
					self._word_callback(word_info['start'], word_info['length'])
			except Exception as e:
				print(f"❌ Word highlighting error: {e}")
			
			# Learn from actual timing for future corrections
			if i > 0:  # Skip first word (no previous timing to compare)
				expected_duration = expected_word_time - last_word_time
				actual_duration = actual_word_time - last_word_time
				if expected_duration > 0:
					timing_ratio = actual_duration / expected_duration
					timing_corrections.append(timing_ratio)
					# Keep only recent corrections
					if len(timing_corrections) > 10:
						timing_corrections.pop(0)
			
			last_word_time = actual_word_time
		
		print("✅ Adaptive word highlighting completed")
				
	def pause(self) -> None:
		"""Pause speech using NBSapi."""
		print("⏸️ DEBUG: Pause-Befehl erhalten")
		try:
			with self._lock:
				if not self._is_speaking:
					print("⚠️ DEBUG: Nicht am Sprechen - Pause ignoriert")
					return
				if self._is_paused:
					print("⚠️ DEBUG: Bereits pausiert - Pause ignoriert")
					return
			
			print("⏸️ DEBUG: Pausiere NBSapi...")
			self.tts.Pause()
			with self._lock:
				self._is_paused = True
			print("✅ DEBUG: Pause erfolgreich")
		except Exception as e:
			print(f"❌ DEBUG: NBSapi pause error: {e}")
			
	def resume(self) -> None:
		"""Resume speech using NBSapi."""
		print("▶️ DEBUG: Resume-Befehl erhalten")
		try:
			with self._lock:
				if not self._is_speaking:
					print("⚠️ DEBUG: Nicht am Sprechen - Resume ignoriert")
					return
				if not self._is_paused:
					print("⚠️ DEBUG: Nicht pausiert - Resume ignoriert")
					return
			
			print("▶️ DEBUG: Setze NBSapi fort...")
			self.tts.Resume()
			with self._lock:
				self._is_paused = False
			print("✅ DEBUG: Resume erfolgreich")
		except Exception as e:
			print(f"❌ DEBUG: NBSapi resume error: {e}")
			
	def stop(self) -> None:
		"""Stop speech using NBSapi."""
		print("🛑 DEBUG: Stop-Befehl erhalten")
		try:
			with self._lock:
				was_speaking = self._is_speaking
				was_paused = self._is_paused
			
			if not was_speaking:
				print("⚠️ DEBUG: Nicht am Sprechen - Stop ignoriert")
				return
			
			print(f"🛑 DEBUG: Stoppe NBSapi (was_paused: {was_paused})")
			self.tts.Stop()
			if self._word_callback:
				try:
					self.tts.SetWordCallBack(None)
				except AttributeError:
					pass  # Word callbacks not supported, ignore
			
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
			print("✅ DEBUG: Stop erfolgreich")
		except Exception as e:
			print(f"❌ DEBUG: NBSapi stop error: {e}")
			# Ensure state is cleared even on error
			with self._lock:
				self._is_speaking = False
				self._is_paused = False
			
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