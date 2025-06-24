import pyttsx3
from abc import ABC, abstractmethod
from typing import Optional, List
import threading


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
        self._is_paused = False
        self._current_text = ""
        self._speaking_thread = None
        self._lock = threading.Lock()
        self._init_engine()
        
    def _init_engine(self) -> None:
        """Initialize the TTS engine."""
        try:
            self.engine = pyttsx3.init('sapi5')
        except Exception as e:
            print(f"Failed to initialize SAPI engine: {e}")
            self.engine = pyttsx3.init()  # Fallback to default
            
    def get_available_voices(self) -> List[str]:
        """Get list of available voice names."""
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
            self._is_paused = False
            
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
            self._speaking_thread = threading.Thread(target=self._speak_text, args=(text,))
            self._speaking_thread.daemon = True
            self._speaking_thread.start()
            
    def _speak_text(self, text: str) -> None:
        """Internal method to speak text."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error during speech: {e}")
            
    def pause(self) -> None:
        """Pause current speech."""
        with self._lock:
            if self.is_speaking() and not self._is_paused:
                # pyttsx3 doesn't have built-in pause, so we stop and save position
                self._is_paused = True
                self.engine.stop()
                
    def resume(self) -> None:
        """Resume paused speech."""
        with self._lock:
            if self._is_paused and self._current_text:
                self._is_paused = False
                # Resume by speaking the remaining text
                # Note: This is a simplified implementation
                self._speaking_thread = threading.Thread(
                    target=self._speak_text, 
                    args=(self._current_text,)
                )
                self._speaking_thread.daemon = True
                self._speaking_thread.start()
                
    def stop(self) -> None:
        """Stop current speech."""
        with self._lock:
            self.engine.stop()
            self._current_text = ""
            self._is_paused = False
            
    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return (self._speaking_thread is not None and 
                self._speaking_thread.is_alive())
                

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