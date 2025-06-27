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
from typing import Optional, List, Dict, Set
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
			# Note: Python doesn't have direct thread termination
			# We rely on the thread's cleanup mechanisms
			try:
				thread.join(timeout=1.0)
				if thread.is_alive():
					print(f"⚠️ Thread {thread.name} did not terminate gracefully")
			except Exception as e:
				print(f"❌ Error terminating thread {thread.name}: {e}")
	
	with _REGISTRY_LOCK:
		_GLOBAL_THREAD_REGISTRY.clear()
	
	print("✅ All speech threads cleanup completed")

def kill_previous_instances() -> None:
	"""Kill all previous instances of the application with aggressive force-kill."""
	print("🔍 Checking for previous application instances...")
	
	current_pid = os.getpid()
	killed_count = 0
	force_killed_count = 0
	
	try:
		# Look for other Python processes running this application
		processes_to_kill = []
		
		for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
			try:
				if proc.info['pid'] == current_pid:
					continue
					
				# Check if it's a Python process running our application
				if (proc.info['name'] and 'python' in proc.info['name'].lower() and
					proc.info['cmdline'] and any('main.py' in str(cmd) for cmd in proc.info['cmdline'])):
					
					processes_to_kill.append(proc)
					
			except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
				# Process already gone or no access
				continue
		
		if not processes_to_kill:
			print("✅ No previous instances found")
			return
		
		print(f"🎯 Found {len(processes_to_kill)} previous instance(s)")
		
		# Phase 1: Try graceful termination with very short timeout
		for proc in processes_to_kill[:]:  # Copy list to modify during iteration
			try:
				print(f"📤 Sending SIGTERM to PID {proc.pid}")
				proc.terminate()  # Send SIGTERM
				
				# Wait for graceful termination with very short timeout
				try:
					proc.wait(timeout=0.3)  # Reduced to 0.3 seconds
					print(f"✅ Gracefully terminated PID {proc.pid}")
					processes_to_kill.remove(proc)
					killed_count += 1
				except psutil.TimeoutExpired:
					print(f"⏰ PID {proc.pid} did not respond to SIGTERM")
					
			except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
				print(f"⚠️ Process PID {proc.pid} already gone")
				processes_to_kill.remove(proc)
				continue
		
		# Phase 2: Force kill remaining processes immediately
		if processes_to_kill:
			print(f"💀 Force killing {len(processes_to_kill)} unresponsive process(es)")
			
			for proc in processes_to_kill:
				try:
					print(f"🔪 Force killing PID {proc.pid}")
					proc.kill()  # SIGKILL - immediate termination
					
					# Very short wait to confirm kill
					try:
						proc.wait(timeout=0.1)  # Just 0.1 seconds
						print(f"💀 Force killed PID {proc.pid}")
						force_killed_count += 1
					except psutil.TimeoutExpired:
						print(f"⚠️ PID {proc.pid} still running after force kill")
						
				except (psutil.NoSuchProcess, psutil.AccessDenied):
					print(f"⚠️ Process PID {proc.pid} already gone or no access")
					continue
				except Exception as e:
					print(f"❌ Error force killing PID {proc.pid}: {e}")
		
		# Phase 3: Nuclear option - use OS-level kill if available
		if force_killed_count == 0 and processes_to_kill:
			print("☢️ Using nuclear option - OS-level kill")
			
			for proc in processes_to_kill:
				try:
					if os.name == 'nt':  # Windows
						os.system(f"taskkill /F /PID {proc.pid} >nul 2>&1")
						print(f"☢️ OS-killed PID {proc.pid} (Windows)")
					else:  # Unix/Linux
						os.kill(proc.pid, signal.SIGKILL)
						print(f"☢️ OS-killed PID {proc.pid} (Unix)")
					
					force_killed_count += 1
					
				except Exception as e:
					print(f"❌ OS-level kill failed for PID {proc.pid}: {e}")
		
	except Exception as e:
		print(f"❌ Error checking for previous instances: {e}")
	
	# Summary
	total_killed = killed_count + force_killed_count
	if total_killed > 0:
		print(f"🧹 Terminated {total_killed} previous instance(s) "
		      f"(graceful: {killed_count}, force: {force_killed_count})")
	else:
		print("✅ No previous instances found")

def kill_previous_instances_fast() -> None:
	"""Ultra-fast kill function - immediate force kill without graceful termination."""
	print("⚡ Fast-killing previous instances...")
	
	current_pid = os.getpid()
	killed_count = 0
	
	try:
		for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
			try:
				if proc.info['pid'] == current_pid:
					continue
					
				# Check if it's a Python process running our application
				if (proc.info['name'] and 'python' in proc.info['name'].lower() and
					proc.info['cmdline'] and any('main.py' in str(cmd) for cmd in proc.info['cmdline'])):
					
					print(f"⚡ Immediately killing PID {proc.info['pid']}")
					proc.kill()  # Immediate SIGKILL
					killed_count += 1
					
			except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
				continue
				
	except Exception as e:
		print(f"❌ Error in fast kill: {e}")
	
	if killed_count > 0:
		print(f"⚡ Fast-killed {killed_count} instance(s)")
	else:
		print("✅ No instances to kill")

def detect_runtime_environment() -> str:
	"""Detect the runtime environment to choose optimal startup mode."""
	
	# Check for VS Code / IDE environment
	if any(env_var in os.environ for env_var in [
		'VSCODE_PID', 'VSCODE_INJECTION', 'TERM_PROGRAM', 
		'PYCHARM_HOSTED', 'JUPYTER_RUNTIME_DIR'
	]):
		return "ide"
	
	# Check for batch file execution
	if os.environ.get('VORLESE_BATCH_MODE'):
		return "batch"
	
	# Check for terminal/console
	if os.environ.get('TERM') or os.environ.get('ConEmuPID'):
		return "terminal"
	
	# Default
	return "unknown"

def get_optimal_startup_mode() -> dict:
	"""Get optimal startup configuration based on environment."""
	env = detect_runtime_environment()
	
	config = {
		"skip_process_cleanup": False,
		"fast_kill_mode": False,
		"console_mode": False,
		"reason": ""
	}
	
	if env == "ide":
		# VS Code, PyCharm, etc. - use fast mode to avoid hanging
		config.update({
			"skip_process_cleanup": True,
			"console_mode": True,
			"reason": "IDE environment detected - using fast startup"
		})
	elif env == "batch":
		# Batch file - respect user choice
		config.update({
			"reason": "Batch file execution - using configured mode"
		})
	elif env == "terminal":
		# Terminal - normal mode but with console output
		config.update({
			"console_mode": True,
			"reason": "Terminal environment - using normal mode with console output"
		})
	else:
		# Unknown - be conservative
		config.update({
			"fast_kill_mode": True,
			"reason": "Unknown environment - using safe fast mode"
		})
	
	return config

def startup_cleanup() -> None:
	"""Perform startup cleanup of threads and processes with intelligent mode detection."""
	print("🚀 Performing startup cleanup...")
	
	# Get optimal configuration
	optimal_config = get_optimal_startup_mode()
	print(f"🎯 {optimal_config['reason']}")
	
	# Check environment variables (they override auto-detection)
	skip_process_cleanup = os.getenv('VORLESE_SKIP_PROCESS_CLEANUP', '').lower() in ('1', 'true', 'yes')
	fast_kill_mode = os.getenv('VORLESE_FAST_KILL', '').lower() in ('1', 'true', 'yes')
	
	# Apply optimal config if no explicit override
	if not skip_process_cleanup and not fast_kill_mode:
		skip_process_cleanup = optimal_config["skip_process_cleanup"]
		fast_kill_mode = optimal_config["fast_kill_mode"]
		
		# Set console mode if recommended
		if optimal_config["console_mode"] and not os.getenv('VORLESE_CONSOLE_MODE'):
			os.environ['VORLESE_CONSOLE_MODE'] = '1'
	
	if skip_process_cleanup:
		print("⏭️ Skipping process cleanup (auto-detected or manually set)")
	else:
		# Choose kill method based on environment variable or auto-detection
		if fast_kill_mode:
			print("⚡ Using fast kill mode (auto-detected or manually set)")
			kill_previous_instances_fast()
		else:
			print("🎯 Using normal kill mode (graceful + force)")
			kill_previous_instances()
	
	# Then cleanup any remaining threads
	cleanup_all_speech_threads()
	
	# Create lock file regardless
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
			daemon=True,
			name=f"NBSapi-Speech-{id(self)}"
		)
		register_speech_thread(self._speech_thread)
		self._speech_thread.start()
		
	def _speak_worker(self, text: str) -> None:
		"""Worker thread for speaking."""
		current_thread = threading.current_thread()
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
			unregister_speech_thread(current_thread)
				
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
				unregister_speech_thread(self._speech_thread)
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
			unregister_speech_thread(current_thread)
				
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
				unregister_speech_thread(self._speech_thread)
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
	cleanup_all_speech_threads()
	
	# Clean up lock file
	try:
		if os.path.exists(_PROCESS_LOCK_FILE):
			os.remove(_PROCESS_LOCK_FILE)
			print("🧹 Removed lock file")
	except Exception as e:
		print(f"❌ Error removing lock file: {e}")


# Register global cleanup
atexit.register(cleanup_all_speakers) 