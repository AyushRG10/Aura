import pyttsx3
import speech_recognition as sr
from faster_whisper import WhisperModel
import os
import time

class SensoryCortex:
    def __init__(self):
        print("  Initializing Sensory Cortex...")
        
        # 1. Initialize The Mouth (Text-to-Speech)
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 190)
        self.engine.setProperty('volume', 1.0)
        
        # 2. Initialize The Ears (Speech-to-Text)
        # Using a smaller model (tiny) for speed
        model_size = "tiny.en" 
        
        # Force CPU mode to avoid NVidia driver errors
        self.stt_model = WhisperModel(model_size, device="cpu", compute_type="int8")
        print("  - Ears: Hearing with CPU (Standard Speed)")

        # 3. Initialize the Recorder
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 1000
        self.recognizer.dynamic_energy_threshold = True

    def speak(self, text):
        """
        Converts text to speech and plays it immediately.
        """
        if not text: return
        print(f"Aura: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """
        Listens to the microphone and transcribes audio.
        """
        try:
            with sr.Microphone() as source:
                print("\n  Listening...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                with open("temp_command.wav", "wb") as f:
                    f.write(audio.get_wav_data())

            segments, info = self.stt_model.transcribe("temp_command.wav", beam_size=5)
            full_text = "".join([segment.text for segment in segments]).strip()
            
            if full_text:
                print(f"  Heard: '{full_text}'")
                return full_text
            return None

        except sr.WaitTimeoutError:
            return None 
        except Exception as e:
            print(f"  Error listening: {e}")
            return None

if __name__ == "__main__":
    senses = SensoryCortex()
    senses.speak("Sensory systems online.")