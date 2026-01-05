import os
import time
import speech_recognition as sr
import pyttsx3
import subprocess
import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model
import torch
from faster_whisper import WhisperModel

# --- 1. CRITICAL GPU FIX ---
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

force_cudnn_initialization()

class SensoryCortex:
    def __init__(self):
        print("  [System] Initializing Senses...")
        
        # --- MOUTH SETUP ---
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
        
        # --- EARS SETUP (Whisper) ---
        model_size = "base.en"
        try:
            self.stt_model = WhisperModel(model_size, device="cuda", compute_type="float16")
            print(f"  [System] Ears: Online ({model_size}) with GPU 🚀")
        except Exception:
            print("  [System] Ears: GPU Failed. using CPU (Slower).")
            self.stt_model = WhisperModel(model_size, device="cpu", compute_type="int8")

        # --- WAKE WORD SETUP (Custom Awrah Support) ---
        print("  [System] Loading Wake Word Models...")
        
        # UPDATED: Now looks for the phonetic spelling file
        self.custom_model_name = "Awrah.onnx" 
        
        if os.path.exists(self.custom_model_name):
            print(f"  [System] Custom Model Found: {self.custom_model_name}")
            self.oww_model = Model(wakeword_models=[self.custom_model_name], inference_framework="onnx")
            self.wake_word_target = "Awrah"
        else:
            print(f"  [System] '{self.custom_model_name}' not found. Using default 'Hey Jarvis'.")
            print("  [Tip] Train your model here: https://colab.research.google.com/drive/1q1oe2zOyZp7UsB3jJiQ1IFn8z5YfjwEb?usp=sharing")
            openwakeword.utils.download_models() 
            self.oww_model = Model(inference_framework="onnx") 
            self.wake_word_target = "Hey Jarvis"

        # Load Silero VAD
        self.vad_model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad', 
            model='silero_vad', 
            force_reload=False, 
            trust_repo=True
        )
        (self.get_speech_timestamps, self.save_audio, self.read_audio, self.VADIterator, self.collect_chunks) = utils
        print("  [System] Wake Word & VAD Systems Online.")

        # Standard Recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 1000 
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.0  
        self.recognizer.non_speaking_duration = 0.5
        
        print("  [System] Calibrating microphone... (Silence please)")
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)

    def speak(self, text):
        if not text: return
        clean_text = text.replace("*", "").replace('"', '').replace("\n", " ").strip()
        print(f"Aura: {clean_text}")
        
        spoken = False
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

        if not spoken and self.engine:
            try:
                self.engine.say(clean_text)
                self.engine.runAndWait()
            except Exception:
                pass

    def wait_for_wake_word(self):
        """
        Listens for wake word and verifies with VAD.
        """
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1280 
        audio = pyaudio.PyAudio()
        mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        print(f"\n  [System] Status: DORMANT (Waiting for '{self.wake_word_target}')...")
        
        while True:
            # Get audio chunk
            audio_data = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)
            
            # 1. Check OpenWakeWord
            prediction = self.oww_model.predict(audio_data)
            
            # We iterate through all loaded models (usually just one if custom)
            for model_name in prediction.keys():
                if prediction[model_name] > 0.5:
                    
                    # 2. Check Silero VAD (Strictly expects 512 samples)
                    audio_float = audio_data.astype(np.float32) / 32768.0
                    audio_tensor = torch.from_numpy(audio_float)
                    
                    is_speech = False
                    
                    # Window Scanning for VAD
                    if self.vad_model(audio_tensor[:512], RATE).item() > 0.5:
                        is_speech = True
                    elif self.vad_model(audio_tensor[512:1024], RATE).item() > 0.5:
                        is_speech = True
                    elif self.vad_model(audio_tensor[-512:], RATE).item() > 0.5:
                        is_speech = True
                        
                    if is_speech:
                        print(f"  [Wake Word] '{model_name}' Detected! (Conf: {prediction[model_name]:.2f})")
                        mic_stream.stop_stream()
                        mic_stream.close()
                        audio.terminate()
                        return True
                    else:
                        pass 

    def listen(self, phrase_time_limit=15):
        try:
            with sr.Microphone() as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=phrase_time_limit)
                
                with open("temp_audio.wav", "wb") as f:
                    f.write(audio.get_wav_data())

            segments, info = self.stt_model.transcribe("temp_audio.wav", beam_size=7)
            full_text = "".join([segment.text for segment in segments]).strip()
            
            if full_text:
                print(f"  User: '{full_text}'")
                return full_text
            return None
            
        except sr.WaitTimeoutError:
            return None
        except Exception:
            return None