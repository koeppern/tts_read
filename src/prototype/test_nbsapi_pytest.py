#!/usr/bin/env python3
"""
Pytest tests for NBSapi text speaker implementation.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add the prototype directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from text_speaker_v2 import (
	TextSpeakerFactory,
	NBSapiSpeaker,
	Pyttsx3Speaker,
	TextSpeakerBase,
	NBSAPI_AVAILABLE
)


class TestTextSpeakerFactory:
	"""Test the TextSpeakerFactory."""
	
	def test_create_nbsapi_speaker_when_available(self):
		"""Test creating NBSapi speaker when available."""
		if NBSAPI_AVAILABLE:
			speaker = TextSpeakerFactory.create_speaker("SAPI")
			assert isinstance(speaker, NBSapiSpeaker)
		else:
			speaker = TextSpeakerFactory.create_speaker("SAPI")
			assert isinstance(speaker, Pyttsx3Speaker)
			
	def test_create_fallback_speaker(self):
		"""Test fallback to pyttsx3 speaker."""
		with patch('text_speaker_v2.NBSAPI_AVAILABLE', False):
			speaker = TextSpeakerFactory.create_speaker("SAPI")
			assert isinstance(speaker, Pyttsx3Speaker)
			
	def test_create_unknown_engine_type(self):
		"""Test creating speaker with unknown engine type."""
		speaker = TextSpeakerFactory.create_speaker("UNKNOWN")
		# Should fallback to pyttsx3
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
		
	def test_speak(self, speaker, mock_nbsapi):
		"""Test speaking functionality."""
		text = "Test speech"
		voice_name = "Microsoft Hedda Desktop"
		rate = 0.9
		
		speaker.speak(text, voice_name, rate)
		
		# Verify NBSapi methods were called
		mock_nbsapi.SetRate.assert_called_once()
		mock_nbsapi.Speak.assert_called_with(text, 1)  # 1 for async
		
		# Verify state
		assert speaker._current_text == text
		assert speaker._is_speaking
		assert not speaker._is_paused
		
	def test_speak_without_voice(self, speaker, mock_nbsapi):
		"""Test speaking without specifying voice."""
		text = "Test speech"
		
		speaker.speak(text)
		
		mock_nbsapi.Speak.assert_called_with(text, 1)
		
	def test_pause(self, speaker, mock_nbsapi):
		"""Test pause functionality."""
		speaker.pause()
		
		mock_nbsapi.Pause.assert_called_once()
		assert speaker._is_paused
		
	def test_resume(self, speaker, mock_nbsapi):
		"""Test resume functionality."""
		speaker._is_paused = True
		speaker.resume()
		
		mock_nbsapi.Resume.assert_called_once()
		assert not speaker._is_paused
		
	def test_stop(self, speaker, mock_nbsapi):
		"""Test stop functionality."""
		speaker._is_speaking = True
		speaker._is_paused = True
		
		speaker.stop()
		
		mock_nbsapi.Stop.assert_called_once()
		assert not speaker._is_speaking
		assert not speaker._is_paused
		
	def test_cleanup(self, speaker, mock_nbsapi):
		"""Test cleanup functionality."""
		speaker._is_speaking = True
		
		speaker.cleanup()
		
		mock_nbsapi.Stop.assert_called()
		
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
		# Mock GetStatus to return "not speaking" immediately
		mock_nbsapi.GetStatus.return_value = 0
		
		speaker._speak_worker("Test text")
		
		# Should call Speak and GetStatus
		mock_nbsapi.Speak.assert_called_with("Test text", 1)
		mock_nbsapi.GetStatus.assert_called()
		
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
		
	def test_rate_conversion(self, speaker, mock_nbsapi):
		"""Test rate conversion from our scale to SAPI scale."""
		# Test various rates
		test_cases = [
			(0.5, -5),   # 0.5 -> -5
			(1.0, 0),    # 1.0 -> 0
			(1.5, 5),    # 1.5 -> 5
			(2.0, 10),   # 2.0 -> 10
			(0.1, -10),  # Very slow -> -10 (clamped)
			(3.0, 10),   # Very fast -> 10 (clamped)
		]
		
		for input_rate, expected_sapi_rate in test_cases:
			mock_nbsapi.reset_mock()
			speaker.speak("Test", rate=input_rate)
			mock_nbsapi.SetRate.assert_called_with(expected_sapi_rate)


class TestPyttsx3Speaker:
	"""Test pyttsx3 speaker functionality."""
	
	@pytest.fixture
	def mock_pyttsx3(self):
		"""Mock pyttsx3 for testing."""
		with patch('text_speaker_v2.pyttsx3') as mock:
			mock_engine = Mock()
			mock.init.return_value = mock_engine
			
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
			
			yield mock_engine
			
	@pytest.fixture
	def speaker(self, mock_pyttsx3):
		"""Create pyttsx3 speaker for testing."""
		return Pyttsx3Speaker()
		
	def test_init(self, mock_pyttsx3):
		"""Test pyttsx3 speaker initialization."""
		speaker = Pyttsx3Speaker()
		assert speaker.engine is not None
		assert not speaker.is_speaking()
		assert not speaker.is_paused()
		
	def test_speak(self, speaker, mock_pyttsx3):
		"""Test speaking functionality."""
		text = "Test speech"
		voice_name = "Microsoft Hedda Desktop"
		rate = 1.2
		
		speaker.speak(text, voice_name, rate)
		
		# Verify pyttsx3 methods were called
		expected_rate = int(200 * rate)  # 240
		mock_pyttsx3.setProperty.assert_any_call('rate', expected_rate)
		mock_pyttsx3.setProperty.assert_any_call('voice', 'voice1_id')
		
		# Verify state
		assert speaker._current_text == text
		assert speaker._is_speaking
		assert not speaker._is_paused
		
	def test_pause_not_supported(self, speaker, mock_pyttsx3):
		"""Test pause functionality (not supported)."""
		speaker._is_speaking = True
		
		speaker.pause()
		
		# Should call stop instead
		mock_pyttsx3.stop.assert_called_once()
		assert not speaker._is_speaking
		
	def test_resume_not_supported(self, speaker, mock_pyttsx3):
		"""Test resume functionality (not supported)."""
		speaker.resume()
		
		# Should do nothing (just print message)
		# No assertions needed as it's just a print statement
		
	def test_stop(self, speaker, mock_pyttsx3):
		"""Test stop functionality."""
		speaker._is_speaking = True
		speaker._is_paused = True
		
		speaker.stop()
		
		mock_pyttsx3.stop.assert_called_once()
		assert not speaker._is_speaking
		assert not speaker._is_paused
		
	def test_cleanup(self, speaker, mock_pyttsx3):
		"""Test cleanup functionality."""
		speaker._is_speaking = True
		
		speaker.cleanup()
		
		mock_pyttsx3.stop.assert_called()
		
	def test_get_available_voices(self, speaker, mock_pyttsx3):
		"""Test getting available voices."""
		voices = speaker.get_available_voices()
		
		expected_voices = ["Microsoft Hedda Desktop", "Microsoft Zira Desktop"]
		assert voices == expected_voices
		mock_pyttsx3.getProperty.assert_called_with('voices')
		
	def test_get_available_voices_error(self, speaker, mock_pyttsx3):
		"""Test getting available voices with error."""
		mock_pyttsx3.getProperty.side_effect = Exception("Test error")
		
		voices = speaker.get_available_voices()
		
		assert voices == []
		
	def test_set_voice_found(self, speaker, mock_pyttsx3):
		"""Test setting voice when found."""
		voice_name = "Microsoft Hedda Desktop"
		
		speaker._set_voice(voice_name)
		
		mock_pyttsx3.setProperty.assert_called_with('voice', 'voice1_id')
		
	def test_set_voice_not_found(self, speaker, mock_pyttsx3):
		"""Test setting voice when not found."""
		voice_name = "Nonexistent Voice"
		
		# Reset mock to clear previous calls
		mock_pyttsx3.reset_mock()
		
		speaker._set_voice(voice_name)
		
		# Should not call setProperty with voice
		voice_calls = [call for call in mock_pyttsx3.setProperty.call_args_list 
		               if call[0][0] == 'voice']
		assert len(voice_calls) == 0
		
	def test_speak_worker_success(self, speaker, mock_pyttsx3):
		"""Test speech worker thread success."""
		speaker._speak_worker("Test text")
		
		mock_pyttsx3.say.assert_called_with("Test text")
		mock_pyttsx3.runAndWait.assert_called_once()
		
	def test_speak_worker_error(self, speaker, mock_pyttsx3):
		"""Test speech worker with error."""
		mock_pyttsx3.say.side_effect = Exception("Test error")
		
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


class TestThreadingSafety:
	"""Test threading safety of speakers."""
	
	@pytest.fixture
	def mock_speaker(self):
		"""Create a mock speaker for threading tests."""
		with patch('text_speaker_v2.NBSapi'):
			return NBSapiSpeaker()
			
	def test_concurrent_state_access(self, mock_speaker):
		"""Test concurrent access to speaker state."""
		def toggle_state():
			for _ in range(100):
				with mock_speaker._lock:
					mock_speaker._is_speaking = not mock_speaker._is_speaking
					mock_speaker._is_paused = not mock_speaker._is_paused
					
		# Start multiple threads
		threads = [threading.Thread(target=toggle_state) for _ in range(5)]
		for thread in threads:
			thread.start()
			
		# Access state from main thread
		for _ in range(100):
			mock_speaker.is_speaking()
			mock_speaker.is_paused()
			
		# Wait for all threads to complete
		for thread in threads:
			thread.join()
			
		# Should not crash (basic threading safety test)
		assert True


class TestErrorHandling:
	"""Test error handling in various scenarios."""
	
	@pytest.fixture
	def failing_speaker(self):
		"""Create a speaker that fails on various operations."""
		with patch('text_speaker_v2.NBSapi') as mock:
			mock_instance = Mock()
			mock.return_value = mock_instance
			
			# Make all methods raise exceptions
			mock_instance.Speak.side_effect = Exception("Speak failed")
			mock_instance.Pause.side_effect = Exception("Pause failed")
			mock_instance.Resume.side_effect = Exception("Resume failed")
			mock_instance.Stop.side_effect = Exception("Stop failed")
			mock_instance.GetVoices.side_effect = Exception("GetVoices failed")
			mock_instance.SetVoice.side_effect = Exception("SetVoice failed")
			mock_instance.SetRate.side_effect = Exception("SetRate failed")
			
			return NBSapiSpeaker()
			
	def test_speak_with_errors(self, failing_speaker):
		"""Test speaking with various errors."""
		# Should not crash
		failing_speaker.speak("Test text", "Test Voice", 1.0)
		
	def test_pause_with_error(self, failing_speaker):
		"""Test pause with error."""
		failing_speaker.pause()
		# Should handle error gracefully
		
	def test_resume_with_error(self, failing_speaker):
		"""Test resume with error."""
		failing_speaker.resume()
		# Should handle error gracefully
		
	def test_stop_with_error(self, failing_speaker):
		"""Test stop with error."""
		failing_speaker.stop()
		# Should handle error gracefully
		
	def test_cleanup_with_error(self, failing_speaker):
		"""Test cleanup with error."""
		failing_speaker.cleanup()
		# Should handle error gracefully


# Integration tests
class TestIntegration:
	"""Integration tests for the complete system."""
	
	@pytest.mark.skipif(not NBSAPI_AVAILABLE, reason="NBSapi not available")
	def test_full_speech_cycle(self):
		"""Test a complete speech cycle."""
		speaker = TextSpeakerFactory.create_speaker("SAPI")
		
		# This is a real integration test - be careful with audio output
		# In a real test environment, you might want to mock the audio output
		
		text = "Integration test"
		speaker.speak(text, rate=1.0)
		
		# Small delay to let speech start
		time.sleep(0.1)
		
		# Test pause/resume cycle
		speaker.pause()
		time.sleep(0.1)
		speaker.resume()
		time.sleep(0.1)
		
		# Stop and cleanup
		speaker.stop()
		speaker.cleanup()
		
		assert True  # If we get here without crashing, test passes


if __name__ == "__main__":
	# Run tests with pytest
	pytest.main([__file__, "-v", "--tb=short"]) 