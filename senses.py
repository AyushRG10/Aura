import os
import time
import speech_recognition as sr
import pyttsx3
import subprocess
from faster_whisper import WhisperModel

# --- 1. CRITICAL GPU FIX ---
# Keeps the "Ears" working by finding NVIDIA drivers
def force_cudnn_initialization():
    try:
        import site
        packages_dirs = site.getsitepackages()
        nvidia_paths = []
        for directory in packages_dirs:
            nvidia_dir = os.path.join(directory, 'nvidia')
            if os.path.exists(nvidia_dir):
                nvidia_paths.append(nvidia_dir)

        found_dll = False
        for nvidia_dir in nvidia_paths:
            for root, dirs, files in os.walk(nvidia_dir):
                if any(f.endswith('.dll') for f in files):
                    current_path = os.environ.get("PATH", "")
                    os.environ["PATH"] = root + os.pathsep + current_path
                    try:
                        if hasattr(os, 'add_dll_directory'):
                            os.add_dll_directory(root)
                    except Exception:
                        pass
                    if 'cudnn_ops64_9.dll' in files:
                        print(f"  [System] GPU Driver Found: {root}")
                        found_dll = True
        if not found_dll:
            print("  [System] Warning: cudnn_ops64_9.dll not found. Whisper might fail.")
    except Exception as e:
        print(f"  [System] GPU Setup Error: {e}")

# Run driver fix on import
force_cudnn_initialization()

class SensoryCortex:
    def __init__(self):
        print("  [System] Initializing Senses...")
        
        # --- MOUTH SETUP (Backup Engine) ---
        self.engine = None
        try:
            self.engine = pyttsx3.init("sapi5")
            self.engine.setProperty('rate', 175)
            self.engine.setProperty('volume', 1.0)
            voices = self.engine.getProperty('voices')
            zira = next((v for v in voices if "Zira" in v.name), None)
            if zira: self.engine.setProperty('voice', zira.id)
        except Exception:
            pass
        
        # --- EARS SETUP (Whisper AI) ---
        try:
            self.stt_model = WhisperModel("tiny.en", device="cuda", compute_type="float16")
            print("  [System] Ears: GPU Acceleration Active 🚀")
        except Exception:
            print("  [System] Ears: GPU Failed. using CPU (Slower).")
            self.stt_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 1000 
        self.recognizer.dynamic_energy_threshold = True

    def speak(self, text):
        if not text: return
        
        # Clean text for command line usage
        clean_text = text.replace("*", "").replace('"', '').replace("\n", " ").strip()
        print(f"Aura: {clean_text}")
        
        spoken = False

        # Method 1: Windows PowerShell (High Stability)
        # We spawn a totally separate process to speak. This prevents Python from locking up.
        try:
            safe_text = clean_text.replace("'", "''")
            cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; ' \
                  f'$syn = New-Object System.Speech.Synthesis.SpeechSynthesizer; ' \
                  f'$syn.SelectVoiceByHints(\'Female\'); ' \
                  f'$syn.Speak(\'{safe_text}\');"'
            
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            spoken = True
        except Exception:
            spoken = False

        # Method 2: Python Engine (Fallback)
        if not spoken and self.engine:
            try:
                self.engine.say(clean_text)
                self.engine.runAndWait()
            except Exception:
                print("  [Error] Vocal cords failed.")

    def listen(self):
        try:
            with sr.Microphone() as source:
                print("\n  [Listening...]")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                # 'phrase_time_limit' prevents it from getting stuck listening to silence
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                print("  [Processing...]")
                with open("temp_audio.wav", "wb") as f:
                    f.write(audio.get_wav_data())

            segments, info = self.stt_model.transcribe("temp_audio.wav", beam_size=5)
            full_text = "".join([segment.text for segment in segments]).strip()
            
            if full_text:
                print(f"  User: '{full_text}'")
                return full_text
            return None
            
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"  [Error] Hearing failure: {e}")
            return None