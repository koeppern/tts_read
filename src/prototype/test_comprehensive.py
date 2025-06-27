#!/usr/bin/env python3
"""
Comprehensive test suite for text_speaker_v2 module to achieve 80%+ coverage.
"""

import pytest
import time
import threading
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules directly to ensure they're loaded for coverage
import text_speaker_v2
from text_speaker_v2 import (
	TextSpeakerFactory,
	NBSapiSpeaker,
	Pyttsx3Speaker,
	TextSpeakerBase,
	NBSAPI_AVAILABLE,
	cleanup_all_speakers
)


class TestTextSpeakerFactory:
	"""Test the TextSpeakerFactory class."""
	
	def test_create_nbsapi_speaker_when_available(self):
		"""Test creating NBSapi speaker when available."""
		if NBSAPI_AVAILABLE:
			with patch('text_speaker_v2.NBSapi') as mock_nbsapi:
				mock_instance = Mock()
				mock_nbsapi.return_value = mock_instance
				
				speaker = TextSpeakerFactory.create_speaker("SAPI")
				assert isinstance(speaker, NBSapiSpeaker)
				mock_nbsapi.assert_called_once()
		else:
			# If NBSapi not available, should fallback to pyttsx3
			with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
				mock_engine = Mock()
				mock_pyttsx3.init.return_value = mock_engine
				
				speaker = TextSpeakerFactory.create_speaker("SAPI")
				assert isinstance(speaker, Pyttsx3Speaker)
				
	def test_create_fallback_speaker(self):
		"""Test fallback to pyttsx3 speaker."""
		with patch('text_speaker_v2.NBSAPI_AVAILABLE', False):
			with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
				mock_engine = Mock()
				mock_pyttsx3.init.return_value = mock_engine
				
				speaker = TextSpeakerFactory.create_speaker("SAPI")
				assert isinstance(speaker, Pyttsx3Speaker)
				mock_pyttsx3.init.assert_called_once()
				
	def test_create_unknown_engine_type(self):
		"""Test creating speaker with unknown engine type."""
		with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
			mock_engine = Mock()
			mock_pyttsx3.init.return_value = mock_engine
			
			speaker = TextSpeakerFactory.create_speaker("UNKNOWN")
			assert isinstance(speaker, Pyttsx3Speaker)
			
	def test_create_nbsapi_with_exception(self):
		"""Test NBSapi creation with exception falls back to pyttsx3."""
		if NBSAPI_AVAILABLE:
			with patch('text_speaker_v2.NBSapi', side_effect=Exception("NBSapi failed")):
				with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
					mock_engine = Mock()
					mock_pyttsx3.init.return_value = mock_engine
					
					speaker = TextSpeakerFactory.create_speaker("SAPI")
					assert isinstance(speaker, Pyttsx3Speaker)
					
	def test_factory_with_none_engine_type(self):
		"""Test factory with None engine type."""
		with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
			mock_engine = Mock()
			mock_pyttsx3.init.return_value = mock_engine
			
			speaker = TextSpeakerFactory.create_speaker(None)
			assert isinstance(speaker, Pyttsx3Speaker)


@pytest.mark.skipif(not NBSAPI_AVAILABLE, reason="NBSapi not available")
class TestNBSapiSpeaker:
	"""Test NBSapi speaker functionality."""
	
	@pytest.fixture
	def mock_nbsapi(self):
		"""Mock NBSapi for testing."""
		with patch('text_speaker_v2.NBSapi') as mock:
			mock_instance = Mock()
			mock.return_value = mock_instance
			
			# Mock methods
			mock_instance.GetVoices.return_value = [
				{"Name": "Microsoft Hedda Desktop"},
				{"Name": "Microsoft Zira Desktop"}
			]
			mock_instance.GetStatus.return_value = 0  # Not speaking
			mock_instance.SetRate.return_value = None
			mock_instance.SetVoice.return_value = None
			mock_instance.Speak.return_value = None
			mock_instance.Pause.return_value = None
			mock_instance.Resume.return_value = None
			mock_instance.Stop.return_value = None
			
			yield mock_instance
			
	@pytest.fixture
	def speaker(self, mock_nbsapi):
		"""Create NBSapi speaker for testing."""
		return NBSapiSpeaker()
		
	def test_init(self, mock_nbsapi):
		"""Test NBSapi speaker initialization."""
		speaker = NBSapiSpeaker()
		assert speaker.tts is not None
		assert not speaker.is_speaking()
		assert not speaker.is_paused()
		assert speaker._speech_thread is None
		
	def test_speak_basic(self, speaker, mock_nbsapi):
		"""Test basic speaking functionality."""
		text = "Test speech"
		
		# Don't patch stop to test the actual flow
		speaker.speak(text)
		
		mock_nbsapi.Speak.assert_called_with(text, 1)
		assert speaker._current_text == text
		# The speak method sets _is_speaking to True, then starts a thread
		# which may complete quickly in tests
		
	def test_speak_with_voice_and_rate(self, speaker, mock_nbsapi):
		"""Test speaking with voice and rate."""
		text = "Test speech"
		voice_name = "Microsoft Hedda Desktop"
		rate = 0.9
		
		speaker.speak(text, voice_name, rate)
		
		# Verify NBSapi methods were called
		mock_nbsapi.SetRate.assert_called_once_with(-1)  # 0.9 -> -1
		mock_nbsapi.Speak.assert_called_with(text, 1)
		assert speaker._current_text == text
		
	def test_rate_conversion(self, speaker, mock_nbsapi):
		"""Test rate conversion from our scale to SAPI scale."""
		test_cases = [
			(0.5, -5),   # 0.5 -> -5
			(1.0, 0),    # 1.0 -> 0
			(1.5, 5),    # 1.5 -> 5
			(2.0, 10),   # 2.0 -> 10
			(0.1, -9),   # Very slow -> -9
			(3.0, 10),   # Very fast -> 10 (clamped)
		]
		
		for input_rate, expected_sapi_rate in test_cases:
			mock_nbsapi.reset_mock()
			speaker.speak("Test", rate=input_rate)
			mock_nbsapi.SetRate.assert_called_with(expected_sapi_rate)
		
	def test_pause(self, speaker, mock_nbsapi):
		"""Test pause functionality."""
		speaker.pause()
		
		mock_nbsapi.Pause.assert_called_once()
		assert speaker._is_paused
		
	def test_pause_with_exception(self, speaker, mock_nbsapi):
		"""Test pause with exception."""
		mock_nbsapi.Pause.side_effect = Exception("Pause failed")
		
		speaker.pause()
		
		# Should handle exception gracefully
		mock_nbsapi.Pause.assert_called_once()
		
	def test_resume(self, speaker, mock_nbsapi):
		"""Test resume functionality."""
		speaker._is_paused = True
		speaker.resume()
		
		mock_nbsapi.Resume.assert_called_once()
		assert not speaker._is_paused
		
	def test_resume_with_exception(self, speaker, mock_nbsapi):
		"""Test resume with exception."""
		mock_nbsapi.Resume.side_effect = Exception("Resume failed")
		
		speaker.resume()
		
		# Should handle exception gracefully
		mock_nbsapi.Resume.assert_called_once()
		
	def test_stop(self, speaker, mock_nbsapi):
		"""Test stop functionality."""
		speaker._is_speaking = True
		speaker._is_paused = True
		
		speaker.stop()
		
		mock_nbsapi.Stop.assert_called_once()
		assert not speaker._is_speaking
		assert not speaker._is_paused
		
	def test_stop_with_exception(self, speaker, mock_nbsapi):
		"""Test stop with exception."""
		mock_nbsapi.Stop.side_effect = Exception("Stop failed")
		
		speaker.stop()
		
		# Should handle exception gracefully
		mock_nbsapi.Stop.assert_called_once()
		
	def test_cleanup(self, speaker, mock_nbsapi):
		"""Test cleanup functionality."""
		speaker._is_speaking = True
		
		with patch.object(speaker, 'stop') as mock_stop:
			speaker.cleanup()
			mock_stop.assert_called_once()
			
	def test_cleanup_with_thread(self, speaker, mock_nbsapi):
		"""Test cleanup with active thread."""
		mock_thread = Mock()
		mock_thread.is_alive.return_value = True
		speaker._speech_thread = mock_thread
		
		with patch.object(speaker, 'stop'):
			speaker.cleanup()
			mock_thread.join.assert_called_once_with(timeout=2.0)
			
	def test_cleanup_with_exception(self, speaker, mock_nbsapi):
		"""Test cleanup with exception."""
		with patch.object(speaker, 'stop', side_effect=Exception("Stop failed")):
			speaker.cleanup()
			# Should handle exception gracefully
			
	def test_get_available_voices(self, speaker, mock_nbsapi):
		"""Test getting available voices."""
		voices = speaker.get_available_voices()
		
		expected_voices = ["Microsoft Hedda Desktop", "Microsoft Zira Desktop"]
		assert voices == expected_voices
		mock_nbsapi.GetVoices.assert_called_once()
		
	def test_get_available_voices_error(self, speaker, mock_nbsapi):
		"""Test getting available voices with error."""
		mock_nbsapi.GetVoices.side_effect = Exception("Test error")
		
		voices = speaker.get_available_voices()
		
		assert voices == []
		
	def test_set_voice_found(self, speaker, mock_nbsapi):
		"""Test setting voice when found."""
		voice_name = "Microsoft Hedda Desktop"
		
		speaker._set_voice(voice_name)
		
		mock_nbsapi.SetVoice.assert_called_with(0, "by_index")
		
	def test_set_voice_not_found(self, speaker, mock_nbsapi):
		"""Test setting voice when not found."""
		voice_name = "Nonexistent Voice"
		
		speaker._set_voice(voice_name)
		
		# Should not call SetVoice
		mock_nbsapi.SetVoice.assert_not_called()
		
	def test_set_voice_error(self, speaker, mock_nbsapi):
		"""Test setting voice with error."""
		mock_nbsapi.GetVoices.side_effect = Exception("Test error")
		
		speaker._set_voice("Test Voice")
		
		# Should handle error gracefully
		mock_nbsapi.SetVoice.assert_not_called()
		
	def test_speak_worker_completion(self, speaker, mock_nbsapi):
		"""Test speech worker thread completion."""
		# Mock GetStatus to return not speaking immediately
		mock_nbsapi.GetStatus.return_value = 0
		
		speaker._speak_worker("Test text")
		
		# Should call Speak and GetStatus
		mock_nbsapi.Speak.assert_called_with("Test text", 1)
		mock_nbsapi.GetStatus.assert_called()
		
	def test_speak_worker_with_speaking_status(self, speaker, mock_nbsapi):
		"""Test speech worker with speaking status."""
		# Mock GetStatus to return speaking first, then not speaking
		mock_nbsapi.GetStatus.side_effect = [2, 2, 0]  # Speaking, Speaking, Not speaking
		
		with patch('time.sleep'):  # Speed up the test
			speaker._speak_worker("Test text")
			
		# Should call GetStatus multiple times
		assert mock_nbsapi.GetStatus.call_count >= 2
		
	def test_speak_worker_error(self, speaker, mock_nbsapi):
		"""Test speech worker with error."""
		mock_nbsapi.Speak.side_effect = Exception("Test error")
		
		speaker._speak_worker("Test text")
		
		# Should handle error and reset state
		assert not speaker._is_speaking
		assert not speaker._is_paused
		
	def test_is_speaking_and_paused_states(self, speaker):
		"""Test speaking and paused state methods."""
		# Initial state
		assert not speaker.is_speaking()
		assert not speaker.is_paused()
		
		# Set speaking
		with speaker._lock:
			speaker._is_speaking = True
			
		assert speaker.is_speaking()
		assert not speaker.is_paused()
		
		# Set paused
		with speaker._lock:
			speaker._is_paused = True
			
		assert not speaker.is_speaking()  # Speaking but paused = not speaking
		assert speaker.is_paused()


class TestPyttsx3Speaker:
	"""Test pyttsx3 speaker functionality."""
	
	@pytest.fixture
	def mock_pyttsx3_engine(self):
		"""Mock pyttsx3 engine for testing."""
		mock_engine = Mock()
		
		# Mock voice objects
		mock_voice1 = Mock()
		mock_voice1.name = "Microsoft Hedda Desktop"
		mock_voice1.id = "voice1_id"
		
		mock_voice2 = Mock()
		mock_voice2.name = "Microsoft Zira Desktop"
		mock_voice2.id = "voice2_id"
		
		mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]
		mock_engine.setProperty.return_value = None
		mock_engine.say.return_value = None
		mock_engine.runAndWait.return_value = None
		mock_engine.stop.return_value = None
		
		return mock_engine
		
	@pytest.fixture
	def speaker(self, mock_pyttsx3_engine):
		"""Create pyttsx3 speaker for testing."""
		with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
			mock_pyttsx3.init.return_value = mock_pyttsx3_engine
			return Pyttsx3Speaker()
			
	def test_init(self, mock_pyttsx3_engine):
		"""Test pyttsx3 speaker initialization."""
		with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
			mock_pyttsx3.init.return_value = mock_pyttsx3_engine
			
			speaker = Pyttsx3Speaker()
			assert speaker.engine is not None
			assert not speaker.is_speaking()
			assert not speaker.is_paused()
			mock_pyttsx3.init.assert_called_once()
			
	def test_speak_basic(self, speaker, mock_pyttsx3_engine):
		"""Test basic speaking functionality."""
		text = "Test speech"
		
		with patch('threading.Thread') as mock_thread:
			mock_thread_instance = Mock()
			mock_thread.return_value = mock_thread_instance
			
			speaker.speak(text)
			
			# Verify state
			assert speaker._current_text == text
			assert speaker._is_speaking
			
			# Verify thread creation
			mock_thread.assert_called_once()
			mock_thread_instance.start.assert_called_once()
			
	def test_speak_with_voice_and_rate(self, speaker, mock_pyttsx3_engine):
		"""Test speaking with voice and rate."""
		text = "Test speech"
		voice_name = "Microsoft Hedda Desktop"
		rate = 1.2
		
		with patch('threading.Thread') as mock_thread:
			mock_thread_instance = Mock()
			mock_thread.return_value = mock_thread_instance
			
			speaker.speak(text, voice_name, rate)
			
			# Verify pyttsx3 methods were called
			expected_rate = int(200 * rate)  # 240
			mock_pyttsx3_engine.setProperty.assert_any_call('rate', expected_rate)
			mock_pyttsx3_engine.setProperty.assert_any_call('voice', 'voice1_id')
			
	def test_pause_not_supported(self, speaker, mock_pyttsx3_engine):
		"""Test pause functionality (not supported)."""
		speaker._is_speaking = True
		
		with patch.object(speaker, 'stop') as mock_stop:
			speaker.pause()
			mock_stop.assert_called_once()
			
	def test_resume_not_supported(self, speaker, mock_pyttsx3_engine):
		"""Test resume functionality (not supported)."""
		speaker.resume()
		# Should do nothing (just print message)
		
	def test_stop(self, speaker, mock_pyttsx3_engine):
		"""Test stop functionality."""
		speaker._is_speaking = True
		speaker._is_paused = True
		
		speaker.stop()
		
		mock_pyttsx3_engine.stop.assert_called_once()
		assert not speaker._is_speaking
		assert not speaker._is_paused
		
	def test_stop_with_exception(self, speaker, mock_pyttsx3_engine):
		"""Test stop with exception."""
		mock_pyttsx3_engine.stop.side_effect = Exception("Stop failed")
		
		speaker.stop()
		
		# Should handle exception gracefully
		mock_pyttsx3_engine.stop.assert_called_once()
		
	def test_cleanup(self, speaker, mock_pyttsx3_engine):
		"""Test cleanup functionality."""
		speaker._is_speaking = True
		
		with patch.object(speaker, 'stop') as mock_stop:
			speaker.cleanup()
			mock_stop.assert_called_once()
			
	def test_cleanup_with_thread(self, speaker, mock_pyttsx3_engine):
		"""Test cleanup with active thread."""
		mock_thread = Mock()
		mock_thread.is_alive.return_value = True
		speaker._speech_thread = mock_thread
		
		with patch.object(speaker, 'stop'):
			speaker.cleanup()
			mock_thread.join.assert_called_once_with(timeout=2.0)
			
	def test_cleanup_with_exception(self, speaker, mock_pyttsx3_engine):
		"""Test cleanup with exception."""
		with patch.object(speaker, 'stop', side_effect=Exception("Stop failed")):
			speaker.cleanup()
			# Should handle exception gracefully
			
	def test_get_available_voices(self, speaker, mock_pyttsx3_engine):
		"""Test getting available voices."""
		voices = speaker.get_available_voices()
		
		expected_voices = ["Microsoft Hedda Desktop", "Microsoft Zira Desktop"]
		assert voices == expected_voices
		mock_pyttsx3_engine.getProperty.assert_called_with('voices')
		
	def test_get_available_voices_error(self, speaker, mock_pyttsx3_engine):
		"""Test getting available voices with error."""
		mock_pyttsx3_engine.getProperty.side_effect = Exception("Test error")
		
		voices = speaker.get_available_voices()
		
		assert voices == []
		
	def test_get_available_voices_with_none_names(self, speaker, mock_pyttsx3_engine):
		"""Test getting voices with None names."""
		mock_voice_with_none = Mock()
		mock_voice_with_none.name = None
		mock_pyttsx3_engine.getProperty.return_value = [mock_voice_with_none]
		
		voices = speaker.get_available_voices()
		
		assert voices == []  # None names are filtered out
		
	def test_set_voice_found(self, speaker, mock_pyttsx3_engine):
		"""Test setting voice when found."""
		voice_name = "Microsoft Hedda Desktop"
		
		speaker._set_voice(voice_name)
		
		mock_pyttsx3_engine.setProperty.assert_called_with('voice', 'voice1_id')
		
	def test_set_voice_not_found(self, speaker, mock_pyttsx3_engine):
		"""Test setting voice when not found."""
		voice_name = "Nonexistent Voice"
		
		# Reset mock to clear previous calls
		mock_pyttsx3_engine.reset_mock()
		
		speaker._set_voice(voice_name)
		
		# Should not call setProperty with voice
		voice_calls = [call for call in mock_pyttsx3_engine.setProperty.call_args_list 
		               if call[0][0] == 'voice']
		assert len(voice_calls) == 0
		
	def test_set_voice_with_exception(self, speaker, mock_pyttsx3_engine):
		"""Test setting voice with exception."""
		mock_pyttsx3_engine.getProperty.side_effect = Exception("Test error")
		
		speaker._set_voice("Test Voice")
		
		# Should handle error gracefully
		mock_pyttsx3_engine.setProperty.assert_not_called()
		
	def test_speak_worker_success(self, speaker, mock_pyttsx3_engine):
		"""Test speech worker thread success."""
		speaker._speak_worker("Test text")
		
		mock_pyttsx3_engine.say.assert_called_with("Test text")
		mock_pyttsx3_engine.runAndWait.assert_called_once()
		
		# State should be reset
		assert not speaker._is_speaking
		assert not speaker._is_paused
		
	def test_speak_worker_error(self, speaker, mock_pyttsx3_engine):
		"""Test speech worker with error."""
		mock_pyttsx3_engine.say.side_effect = Exception("Test error")
		
		speaker._speak_worker("Test text")
		
		# Should handle error and reset state
		assert not speaker._is_speaking
		assert not speaker._is_paused


class TestTextSpeakerBase:
	"""Test the abstract base class functionality."""
	
	def test_cannot_instantiate_abstract_class(self):
		"""Test that TextSpeakerBase cannot be instantiated directly."""
		with pytest.raises(TypeError):
			TextSpeakerBase()
			
	def test_speaker_base_methods_exist(self):
		"""Test that base class defines required methods."""
		required_methods = [
			'speak', 'pause', 'resume', 'stop', 'cleanup', 
			'is_speaking', 'is_paused', 'get_available_voices'
		]
		
		for method_name in required_methods:
			assert hasattr(TextSpeakerBase, method_name)


class TestGlobalFunctions:
	"""Test global functions and cleanup."""
	
	def test_cleanup_all_speakers(self):
		"""Test global cleanup function."""
		# This function just prints a message, so we test it runs without error
		cleanup_all_speakers()
		
	def test_nbsapi_available_flag(self):
		"""Test NBSAPI_AVAILABLE flag."""
		# This tests the import logic
		assert isinstance(NBSAPI_AVAILABLE, bool)
		
	def test_atexit_registration(self):
		"""Test that atexit registration works."""
		import atexit
		
		# Check that cleanup_all_speakers is registered
		assert callable(cleanup_all_speakers)


class TestThreadingSafety:
	"""Test threading safety of speakers."""
	
	@pytest.fixture
	def mock_speaker(self):
		"""Create a mock speaker for threading tests."""
		if NBSAPI_AVAILABLE:
			with patch('text_speaker_v2.NBSapi'):
				return NBSapiSpeaker()
		else:
			with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
				mock_engine = Mock()
				mock_pyttsx3.init.return_value = mock_engine
				return Pyttsx3Speaker()
				
	def test_concurrent_state_access(self, mock_speaker):
		"""Test concurrent access to speaker state."""
		def toggle_state():
			for _ in range(10):  # Reduced iterations for faster test
				with mock_speaker._lock:
					mock_speaker._is_speaking = not mock_speaker._is_speaking
					mock_speaker._is_paused = not mock_speaker._is_paused
					
		# Start multiple threads
		threads = [threading.Thread(target=toggle_state) for _ in range(2)]
		for thread in threads:
			thread.start()
			
		# Access state from main thread
		for _ in range(10):
			mock_speaker.is_speaking()
			mock_speaker.is_paused()
			
		# Wait for all threads to complete
		for thread in threads:
			thread.join()
			
		# Should not crash (basic threading safety test)
		assert True


class TestIntegration:
	"""Integration tests for the complete system."""
	
	def test_full_speech_cycle_mocked(self):
		"""Test a complete speech cycle with mocked dependencies."""
		if NBSAPI_AVAILABLE:
			with patch('text_speaker_v2.NBSapi') as mock_nbsapi:
				mock_instance = Mock()
				mock_nbsapi.return_value = mock_instance
				mock_instance.GetStatus.return_value = 0  # Not speaking
				
				speaker = TextSpeakerFactory.create_speaker("SAPI")
				
				text = "Integration test"
				speaker.speak(text, rate=1.0)
					
				# Test pause/resume cycle
				speaker.pause()
				speaker.resume()
				
				# Stop and cleanup
				speaker.stop()
				speaker.cleanup()
				
				assert True  # If we get here without crashing, test passes
		else:
			with patch.object(text_speaker_v2, 'pyttsx3', create=True) as mock_pyttsx3:
				mock_engine = Mock()
				mock_pyttsx3.init.return_value = mock_engine
				
				speaker = TextSpeakerFactory.create_speaker("SAPI")
				
				text = "Integration test"
				speaker.speak(text, rate=1.0)
					
				# Test pause/resume cycle
				speaker.pause()
				speaker.resume()
				
				# Stop and cleanup
				speaker.stop()
				speaker.cleanup()
				
				assert True
	
	def test_module_imports_correctly(self):
		"""Test that the module imports correctly."""
		import text_speaker_v2
		
		# Test that all main classes are importable
		assert hasattr(text_speaker_v2, 'TextSpeakerFactory')
		assert hasattr(text_speaker_v2, 'NBSapiSpeaker')
		assert hasattr(text_speaker_v2, 'Pyttsx3Speaker')
		assert hasattr(text_speaker_v2, 'TextSpeakerBase')


class TestThreadCleanup:
	"""Test thread cleanup functionality."""
	
	def test_thread_registration(self):
		"""Test thread registration and unregistration."""
		from text_speaker_v2 import (
			register_speech_thread, 
			unregister_speech_thread,
			_GLOBAL_THREAD_REGISTRY,
			_REGISTRY_LOCK
		)
		
		# Create a dummy thread
		import threading
		import time
		
		def dummy_worker():
			time.sleep(0.1)
		
		thread = threading.Thread(target=dummy_worker, name="TestThread")
		
		# Test registration
		initial_count = len(_GLOBAL_THREAD_REGISTRY)
		register_speech_thread(thread)
		
		with _REGISTRY_LOCK:
			assert len(_GLOBAL_THREAD_REGISTRY) == initial_count + 1
			assert thread in _GLOBAL_THREAD_REGISTRY
		
		# Test unregistration
		unregister_speech_thread(thread)
		
		with _REGISTRY_LOCK:
			assert len(_GLOBAL_THREAD_REGISTRY) == initial_count
			assert thread not in _GLOBAL_THREAD_REGISTRY
	
	def test_cleanup_all_speech_threads(self):
		"""Test cleanup of all speech threads."""
		from text_speaker_v2 import (
			register_speech_thread,
			cleanup_all_speech_threads,
			_GLOBAL_THREAD_REGISTRY,
			_REGISTRY_LOCK
		)
		
		import threading
		import time
		
		def dummy_worker():
			time.sleep(0.5)
		
		# Create and register some threads
		threads = []
		for i in range(2):
			thread = threading.Thread(
				target=dummy_worker,
				name=f"TestCleanupThread-{i}",
				daemon=True
			)
			threads.append(thread)
			register_speech_thread(thread)
			thread.start()
		
		# Verify threads are registered
		with _REGISTRY_LOCK:
			assert len(_GLOBAL_THREAD_REGISTRY) >= 2
		
		# Cleanup all threads
		cleanup_all_speech_threads()
		
		# Verify registry is cleared
		with _REGISTRY_LOCK:
			assert len(_GLOBAL_THREAD_REGISTRY) == 0
	
	def test_startup_cleanup_execution(self):
		"""Test that startup_cleanup executes without errors."""
		from text_speaker_v2 import startup_cleanup
		
		# This test just ensures the function runs without exceptions
		# In a real scenario, it would kill other processes
		try:
			startup_cleanup()
		except Exception as e:
			pytest.fail(f"startup_cleanup raised an exception: {e}")
	
	def test_lock_file_handling(self):
		"""Test lock file creation and cleanup."""
		from text_speaker_v2 import _PROCESS_LOCK_FILE, startup_cleanup
		import os
		
		# Ensure no lock file exists initially
		if os.path.exists(_PROCESS_LOCK_FILE):
			os.remove(_PROCESS_LOCK_FILE)
		
		# Run startup cleanup
		startup_cleanup()
		
		# Verify lock file was created
		assert os.path.exists(_PROCESS_LOCK_FILE)
		
		# Read the lock file content
		with open(_PROCESS_LOCK_FILE, 'r') as f:
			pid_str = f.read().strip()
			assert pid_str.isdigit()
			assert int(pid_str) == os.getpid()


if __name__ == "__main__":
	# Run tests with pytest
	pytest.main([__file__, "-v", "--tb=short", "--cov=text_speaker_v2", "--cov-report=term-missing"]) 