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
		
		# Word tracking for resume functionality
		self._current_words = []
		self._current_word_index = 0
		self._paused_word_index = 0
		
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
					if status_check_count % 50 == 0:  # Every 5 seconds
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
		"""SAPI status-based word highlighting - synchronized with actual speech progress."""
		import re
		
		print("🔄 Starting SAPI status-based word highlighting...")
		
		# Split text into words and track positions
		words = []
		cumulative_chars = 0
		for match in re.finditer(r'\S+', text):
			word = match.group()
			start_pos = match.start()
			end_pos = match.end()
			words.append({
				'text': word,
				'start': start_pos,
				'end': end_pos,
				'length': len(word),
				'cumulative_start': cumulative_chars,
				'cumulative_end': cumulative_chars + len(word)
			})
			cumulative_chars += len(word) + 1  # +1 for space
		
		print(f"📝 Found {len(words)} words for highlighting")
		
		# Store words for resume functionality
		with self._lock:
			self._current_words = words
			self._current_word_index = 0
		
		# Start speaking the whole text
		speech_start_time = time.time()
		print("🎙️ Starting SAPI speech...")
		self.tts.Speak(text, 1)  # Asynchronous speech
		
		# SAPI status-based highlighting algorithm
		self._sapi_status_word_highlighting(words, speech_start_time, text)
		
	def _sapi_status_word_highlighting(self, words, speech_start_time, full_text):
		"""Hybrid word highlighting: time-based + SAPI monitoring + adaptive correction."""
		
		print("⏱️ Starting hybrid word highlighting (time + SAPI + adaptive)...")
		
		# Calculate dynamic speech rate with better estimation
		try:
			sapi_rate = self.tts.GetRate()  # SAPI rate: -10 to +10
			# More accurate WPM calculation based on SAPI documentation
			# SAPI rate 0 = 180-200 WPM, each point = ±20 WPM  
			base_wpm = 190 + (sapi_rate * 20)
			words_per_second = base_wpm / 60.0
			
			# Account for text complexity and punctuation
			text_complexity = self._calculate_text_complexity(full_text)
			adjusted_wps = words_per_second * (1.0 - text_complexity * 0.3)  # Slow down for complex text
			
		except:
			text_complexity = 0.0
			adjusted_wps = 3.0  # Fallback: 180 WPM
		
		print(f"📊 Speech rate: {base_wpm if 'base_wpm' in locals() else 'unknown'} WPM → {adjusted_wps:.1f} words/sec (complexity: {text_complexity:.2f})")
		
		# Pre-calculate timing with variable intervals based on word length
		for i, word in enumerate(words):
			# Base timing on word count, not character count for better accuracy
			base_time = speech_start_time + (i / adjusted_wps)
			
			# Add extra time for longer words and punctuation
			word_penalty = len(word['text']) * 0.02  # 20ms per character for long words
			punct_penalty = 0.1 if any(c in word['text'] for c in '.,!?;:') else 0
			
			word['expected_time'] = base_time + word_penalty + punct_penalty
			
		# Adaptive tracking variables
		current_word_index = 0
		last_check_time = speech_start_time
		timing_corrections = []
		sapi_completion_detected = False
		
		# Continuous monitoring loop
		while current_word_index < len(words) and not sapi_completion_detected:
			current_time = time.time()
			
			# Check speech state
			with self._lock:
				if not self._is_speaking:
					print("🔚 Highlighting stopped - speech ended")
					break
				
				# Handle pause state with precise timing adjustment
				if self._is_paused:
					pause_word = words[current_word_index]['text'] if current_word_index < len(words) else "end"
					print(f"⏸️ Highlighting paused at word '{pause_word}'")
					
					pause_start = time.time()
					while self._is_paused and self._is_speaking:
						time.sleep(0.05)  # More responsive pause checking
					
					if not self._is_speaking:
						print("🔚 Speech stopped during pause")
						break
					
					# Precise timing adjustment for all remaining words
					pause_duration = time.time() - pause_start
					for j in range(current_word_index, len(words)):
						words[j]['expected_time'] += pause_duration
					
					print(f"▶️ Resumed after {pause_duration:.1f}s pause - timeline adjusted")
					continue
			
			# SAPI completion check (every 200ms to reduce overhead)
			if current_time - last_check_time >= 0.2:
				try:
					status = self.tts.GetStatus("RunningState")
					if status == 1:  # Completed
						print(f"✅ SAPI completed early at word {current_word_index}/{len(words)}")
						sapi_completion_detected = True
						
						# Highlight remaining words with smart pacing
						remaining_words = len(words) - current_word_index
						if remaining_words > 0:
							interval = min(0.08, 1.0 / remaining_words)  # Adaptive interval, max 80ms
							print(f"🔤 Quick-highlighting {remaining_words} remaining words ({interval*1000:.0f}ms intervals)")
							
							for i in range(current_word_index, len(words)):
								word = words[i]
								if self._word_callback:
									self._word_callback(word['start'], word['length'])
								time.sleep(interval)
						break
					last_check_time = current_time
				except:
					pass
			
			# Word highlighting based on timing
			if current_word_index < len(words):
				word = words[current_word_index]
				
				# Check if it's time to highlight this word
				if current_time >= word['expected_time']:
					
					# Highlight the word
					try:
						elapsed = current_time - speech_start_time
						word_timing = current_time - word['expected_time']
						print(f"🔤 [{elapsed:.1f}s] Highlighting: '{word['text']}' (timing: {word_timing:+.2f}s)")
						
						if self._word_callback:
							self._word_callback(word['start'], word['length'])
						
						# Adaptive timing correction based on actual vs expected
						expected_elapsed = word['expected_time'] - speech_start_time
						actual_elapsed = current_time - speech_start_time
						if expected_elapsed > 0:
							timing_ratio = actual_elapsed / expected_elapsed
							timing_corrections.append(timing_ratio)
							
							# Apply corrections to future words (running average)
							if len(timing_corrections) >= 3:
								avg_correction = sum(timing_corrections[-3:]) / 3
								correction_factor = (avg_correction - 1.0) * 0.3  # Gentle correction
								
								# Adjust remaining words
								for j in range(current_word_index + 1, len(words)):
									adjustment = (words[j]['expected_time'] - speech_start_time) * correction_factor
									words[j]['expected_time'] += adjustment
						
						current_word_index += 1
						
					except Exception as e:
						print(f"❌ Word highlighting error: {e}")
						current_word_index += 1
			
			# Smart sleep: sleep until next word or check interval
			next_check = min(
				words[current_word_index]['expected_time'] if current_word_index < len(words) else current_time + 1,
				last_check_time + 0.2  # SAPI status check interval
			)
			sleep_time = max(0.01, min(next_check - current_time, 0.1))  # 10ms minimum, 100ms maximum
			time.sleep(sleep_time)
		
		print("✅ Hybrid word highlighting completed")
	
	def _calculate_text_complexity(self, text):
		"""Calculate text complexity factor (0.0 = simple, 1.0 = complex)."""
		if not text:
			return 0.0
		
		# Count complexity indicators
		punct_count = sum(1 for c in text if c in '.,!?;:')
		digit_count = sum(1 for c in text if c.isdigit())
		upper_count = sum(1 for c in text if c.isupper())
		
		# Calculate ratios
		punct_ratio = punct_count / len(text)
		digit_ratio = digit_count / len(text)
		upper_ratio = upper_count / len(text)
		
		# Combine factors (weighted)
		complexity = (punct_ratio * 0.4 + digit_ratio * 0.3 + upper_ratio * 0.3)
		return min(complexity, 1.0)  # Cap at 1.0
	
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
			
			# Save current word index for resume
			with self._lock:
				self._paused_word_index = self._current_word_index
				print(f"📍 DEBUG: Pausiert bei Wort-Index {self._paused_word_index}")
				
				# Find word context for better resume
				if self._current_words and self._paused_word_index < len(self._current_words):
					current_word = self._current_words[self._paused_word_index]['text']
					print(f"📝 DEBUG: Pausiert bei Wort: '{current_word}'")
			
			print("⏸️ DEBUG: Pausiere NBSapi...")
			self.tts.Pause()
			with self._lock:
				self._is_paused = True
			print("✅ DEBUG: Pause erfolgreich")
		except Exception as e:
			print(f"❌ DEBUG: NBSapi pause error: {e}")
			
	def resume(self) -> None:
		"""Resume speech using NBSapi with one-word-back functionality."""
		print("▶️ DEBUG: Resume-Befehl erhalten")
		try:
			with self._lock:
				if not self._is_speaking:
					print("⚠️ DEBUG: Nicht am Sprechen - Resume ignoriert")
					return
				if not self._is_paused:
					print("⚠️ DEBUG: Nicht pausiert - Resume ignoriert")
					return
			
			# Check if we can do intelligent resume with word-back
			with self._lock:
				if self._current_words and self._paused_word_index > 0:
					# Calculate resume position: one word back
					resume_word_index = max(0, self._paused_word_index - 1)
					resume_word = self._current_words[resume_word_index]
					
					print(f"🔄 DEBUG: Intelligenter Resume - gehe ein Wort zurück")
					print(f"📍 DEBUG: Pausiert bei Index {self._paused_word_index}, Resume bei Index {resume_word_index}")
					print(f"📝 DEBUG: Resume-Wort: '{resume_word['text']}'")
					
					# Extract text from resume position
					text_from_resume = self._current_text[resume_word['start']:]
					
					# Stop current speech and restart from earlier position
					print("🛑 DEBUG: Stoppe aktuelles SAPI für intelligenten Resume...")
					self.tts.Stop()
					
					# Update word index for highlighting
					self._current_word_index = resume_word_index
					
					# Restart speech from the earlier position
					print(f"🎙️ DEBUG: Starte neu ab Wort '{resume_word['text']}'...")
					self.tts.Speak(text_from_resume, 1)
					
					with self._lock:
						self._is_paused = False
					print("✅ DEBUG: Intelligenter Resume erfolgreich")
					return
				else:
					print("⚠️ DEBUG: Kein intelligenter Resume möglich - verwende Standard-Resume")
			
			# Fallback to standard resume
			print("▶️ DEBUG: Setze NBSapi fort (Standard)...")
			self.tts.Resume()
			with self._lock:
				self._is_paused = False
			print("✅ DEBUG: Standard-Resume erfolgreich")
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