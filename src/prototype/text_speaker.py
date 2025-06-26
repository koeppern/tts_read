import pyttsx3
from abc import ABC, abstractmethod
from typing import Optional, List
import threading
import platform
import time
import re


class TextSpeakerInterface(ABC):
    """Abstract interface for text-to-speech implementations."""
    
    @abstractmethod
    def speak(self, text: str, voice: str, rate: float) -> None:
        """Speak the given text with specified voice and rate."""
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
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        pass
        

class SAPITextSpeaker(TextSpeakerInterface):
    """SAPI (Speech API) implementation using pyttsx3."""
    
    def __init__(self):
        """Initialize SAPI text speaker."""
        self.engine = None
        self._use_dummy = False
        self._is_paused = False
        self._is_speaking = False
        self._current_text = ""
        self._current_sentences = []
        self._current_sentence_index = 0
        self._speaking_thread = None
        self._pause_event = threading.Event()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._init_engine()
        
    def _init_engine(self) -> None:
        """Initialize the TTS engine based on platform."""
        system = platform.system()
        
        # Try different engines in order of preference
        engines_to_try = []
        
        if system == "Windows":
            engines_to_try = ['sapi5', None]  # None means auto-detect
        elif system == "Darwin":
            engines_to_try = ['nsss', None]
        else:  # Linux/WSL
            engines_to_try = [None, 'espeak', 'dummy']  # Try auto-detect first
        
        for engine_name in engines_to_try:
            try:
                if engine_name == 'dummy':
                    # Create a dummy engine for testing without actual TTS
                    print("WARNING: Using dummy TTS engine. No audio will be produced.")
                    print("To enable audio on Linux, install espeak: sudo apt-get install espeak")
                    self._use_dummy = True
                    self.engine = None
                    return
                else:
                    self.engine = pyttsx3.init(engine_name)
                    self._use_dummy = False
                    print(f"Successfully initialized TTS engine: {engine_name or 'auto-detected'}")
                    return
            except Exception as e:
                continue
        
        # If we get here, no engine worked
        raise RuntimeError("No TTS engine available. Please install espeak on Linux: sudo apt-get install espeak")
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for better pause/resume control."""
        # Clean up text first
        text = text.strip()
        if not text:
            return []
        
        # Handle pause tags like [pause], [pause:2s], etc. (inspired by OpenAI TTS community)
        text = re.sub(r'\[pause(?::\d+[sm]?)?\]', ' [PAUSE] ', text)
        
        # Split on sentence endings, keeping the punctuation
        sentences = re.split(r'([.!?]+)', text)
        result = []
        
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            if i + 1 < len(sentences):
                punctuation = sentences[i + 1]
                sentence += punctuation
            if sentence:
                result.append(sentence)
        
        # If no proper sentences found, split by length or other delimiters
        if not result and text:
            # Try splitting by other delimiters like commas, semicolons, or line breaks
            parts = re.split(r'([,;:\n]+)', text)
            for i in range(0, len(parts), 2):
                part = parts[i].strip()
                if i + 1 < len(parts):
                    delimiter = parts[i + 1]
                    part += delimiter
                if part and len(part) > 5:  # Only add meaningful parts
                    result.append(part)
        
        # If still no parts, split by word count (every ~5-8 words for better pause control)
        if not result and text:
            words = text.split()
            chunk_size = 6  # Smaller chunks for better pause control
            for i in range(0, len(words), chunk_size):
                chunk = ' '.join(words[i:i + chunk_size])
                if chunk.strip():
                    result.append(chunk.strip())
        
        # Even if we have sentences, also split long sentences into smaller chunks
        if result:
            final_result = []
            for sentence in result:
                words = sentence.split()
                if len(words) > 8:  # Split long sentences
                    chunk_size = 6
                    for i in range(0, len(words), chunk_size):
                        chunk = ' '.join(words[i:i + chunk_size])
                        if chunk.strip():
                            final_result.append(chunk.strip())
                else:
                    final_result.append(sentence)
            result = final_result
        
        # Fallback: treat entire text as one sentence
        if not result:
            result = [text]
        
        print(f"🔧 Text split into {len(result)} parts:")
        for i, part in enumerate(result[:3]):  # Show first 3 parts
            print(f"   {i+1}. {part[:50]}{'...' if len(part) > 50 else ''}")
        if len(result) > 3:
            print(f"   ... and {len(result) - 3} more parts")
            
        return result
            
    def get_available_voices(self) -> List[str]:
        """Get list of available voice names."""
        if self._use_dummy:
            return ["Dummy Voice 1", "Dummy Voice 2"]
        if not self.engine:
            return []
        voices = self.engine.getProperty('voices')
        return [voice.name for voice in voices]
        
    def speak(self, text: str, voice: str, rate: float) -> None:
        """Speak the given text with specified voice and rate.
        
        Args:
            text: Text to speak
            voice: Voice name to use
            rate: Speaking rate (1.0 is normal speed)
        """
        with self._lock:
            # Stop any ongoing speech
            if self.is_speaking():
                self.stop()
                
            self._current_text = text
            self._current_sentences = self._split_into_sentences(text)
            self._current_sentence_index = 0
            self._is_paused = False
            self._is_speaking = True
            self._stop_event.clear()
            self._pause_event.set()  # Set means "not paused"
            
            if not self._use_dummy:
                # Configure voice
                voices = self.engine.getProperty('voices')
                for v in voices:
                    if voice.lower() in v.name.lower():
                        self.engine.setProperty('voice', v.id)
                        break
                        
                # Set speaking rate (pyttsx3 uses words per minute, default is ~200)
                base_rate = self.engine.getProperty('rate')
                self.engine.setProperty('rate', base_rate * rate)
            
            # Start speaking in a separate thread
            self._speaking_thread = threading.Thread(
                target=self._speak_sentences, 
                args=(voice, rate)
            )
            self._speaking_thread.daemon = True
            self._speaking_thread.start()
            
    def _speak_sentences(self, voice: str, rate: float) -> None:
        """Internal method to speak sentences with pause/resume support."""
        try:
            while (self._current_sentence_index < len(self._current_sentences) 
                   and not self._stop_event.is_set()):
                
                # Wait if paused
                self._pause_event.wait()
                
                # Check if we should stop
                if self._stop_event.is_set():
                    break
                
                sentence = self._current_sentences[self._current_sentence_index]
                
                # Check for pause tags
                if '[PAUSE]' in sentence:
                    print(f"🔊 Found pause tag, adding extra pause...")
                    time.sleep(1.0)  # Extra pause for [pause] tags
                    sentence = sentence.replace('[PAUSE]', '')  # Remove pause tag
                    if not sentence.strip():  # If sentence is only pause tag, skip speaking
                        self._current_sentence_index += 1
                        continue
                
                if self._use_dummy:
                    print(f"[DUMMY TTS] Speaking sentence {self._current_sentence_index + 1}/{len(self._current_sentences)}: {sentence[:50]}...")
                    # Simulate speaking time - slower for better testing
                    time.sleep(min(len(sentence) * 0.1, 5))
                else:
                    # Create a new engine instance for this sentence to avoid conflicts
                    temp_engine = pyttsx3.init()
                    
                    # Configure voice
                    voices = temp_engine.getProperty('voices')
                    for v in voices:
                        if voice.lower() in v.name.lower():
                            temp_engine.setProperty('voice', v.id)
                            break
                    
                    # Set rate
                    base_rate = temp_engine.getProperty('rate')
                    temp_engine.setProperty('rate', base_rate * rate)
                    
                    # Speak the sentence
                    temp_engine.say(sentence)
                    temp_engine.runAndWait()
                    temp_engine.stop()
                
                self._current_sentence_index += 1
                
                # Longer pause between chunks to allow for pause commands
                if not self._stop_event.is_set():
                    time.sleep(0.5)  # 500ms pause between chunks for better control
                
        except Exception as e:
            print(f"Error during speech: {e}")
        finally:
            with self._lock:
                self._is_speaking = False
                self._is_paused = False
            
    def pause(self) -> None:
        """Pause current speech."""
        with self._lock:
            if self._is_speaking and not self._is_paused:
                self._is_paused = True
                self._pause_event.clear()  # Clear means "paused"
                
                # Stop current engine if speaking
                if not self._use_dummy and self.engine:
                    try:
                        self.engine.stop()
                    except:
                        pass
                        
                print(f"🔊 TTS Engine paused at sentence {self._current_sentence_index + 1}/{len(self._current_sentences)}")
            else:
                print(f"🔊 Cannot pause - speaking: {self._is_speaking}, already paused: {self._is_paused}")
                
    def resume(self) -> None:
        """Resume paused speech."""
        with self._lock:
            if self._is_paused:
                self._is_paused = False
                self._pause_event.set()  # Set means "not paused"
                print(f"🔊 TTS Engine resumed from sentence {self._current_sentence_index + 1}/{len(self._current_sentences)}")
            else:
                print(f"🔊 Cannot resume - not paused (paused: {self._is_paused})")
                
    def stop(self) -> None:
        """Stop current speech."""
        with self._lock:
            self._stop_event.set()
            self._pause_event.set()  # Unblock any waiting threads
            
            if not self._use_dummy and self.engine:
                try:
                    self.engine.stop()
                except:
                    pass
                    
            self._current_text = ""
            self._current_sentences = []
            self._current_sentence_index = 0
            self._is_paused = False
            self._is_speaking = False
            
    def is_speaking(self) -> bool:
        """Check if currently speaking (includes paused state)."""
        return self._is_speaking
                

class TextSpeakerFactory:
    """Factory for creating text speaker instances."""
    
    @staticmethod
    def create_speaker(engine_type: str = "SAPI") -> TextSpeakerInterface:
        """Create a text speaker instance based on engine type.
        
        Args:
            engine_type: Type of TTS engine to use
            
        Returns:
            TextSpeakerInterface implementation
        """
        if engine_type.upper() == "SAPI":
            return SAPITextSpeaker()
        else:
            # Default to SAPI for now
            return SAPITextSpeaker()