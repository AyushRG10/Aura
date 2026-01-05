import sys
import requests
import json
import time

try:
    from senses import SensoryCortex
except ImportError:
    print("CRITICAL ERROR: Could not find 'senses.py'.")
    print("Please make sure the file is named 'senses.py' and is in the same folder.")
    sys.exit(1)

class NeuralCortex:
    def __init__(self):
        self.host = "http://localhost:11434"
        self.url = f"{self.host}/api/generate"
        self.model = "gemma2:2b" 
        self.context = []
        
        # --- BRAIN CHECK ---
        try:
            tags_response = requests.get(f"{self.host}/api/tags")
            if tags_response.status_code == 200:
                available_models = [m['name'] for m in tags_response.json().get('models', [])]
                if self.model in available_models:
                    print(f"  [System] Brain: Connected to {self.model}")
                elif available_models:
                    print(f"  [System] Warning: '{self.model}' not found. Switching to {available_models[0]}")
                    self.model = available_models[0]
                else:
                    print("  [System] CRITICAL: No models found!")
        except Exception:
            print("  [System] WARNING: Ollama is not running.")

    def think(self, prompt):
        print("  [Thinking...]")
        
        system_instruction = (
            "You are Aura. Do NOT use emojis. "
            "Be extremely concise and quick. "
            "Only provide details if explicitly asked."
        )

        data = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "context": self.context,
            "stream": False
        }
        
        try:
            response = requests.post(self.url, json=data)
            if response.status_code == 200:
                result = response.json()
                self.context = result['context']
                return result['response']
            elif response.status_code == 404:
                return f"Error 404: Model '{self.model}' missing."
            else:
                return f"Error {response.status_code}"
        except Exception:
            return "I cannot connect to Ollama."

# --- MAIN EXECUTION LOOP ---
if __name__ == "__main__":
    print("--- AURA SYSTEM STARTUP ---")
    
    try:
        senses = SensoryCortex()
    except Exception as e:
        print(f"Hardware Failure: {e}")
        sys.exit(1)

    brain = NeuralCortex()
    senses.speak("System online.")

    # --- STATE MACHINE VARIABLES ---
    is_awake = False
    last_interaction_time = 0
    
    # UPDATED: Timer set to 30 seconds as requested
    DORMANCY_TIMEOUT = 30 

    while True:
        # 1. CHECK FOR TIMEOUT (Go to Sleep)
        time_since_last_interaction = time.time() - last_interaction_time
        
        if is_awake and (time_since_last_interaction > DORMANCY_TIMEOUT):
            is_awake = False
            # senses.speak("Dormant.") 

        # 2. DORMANT MODE (Wait for Wake Word)
        if not is_awake:
            # Anti-Echo Pause (Prevents her from waking herself up)
            time.sleep(1.0)
            
            if senses.wait_for_wake_word():
                is_awake = True
                # Reset timer immediately upon waking
                last_interaction_time = time.time()
                senses.speak("Online") 
                continue

        # 3. ACTIVE MODE (Listen for Commands)
        if is_awake:
            user_input = senses.listen(phrase_time_limit=15)
            
            if user_input:
                # --- TIMER DELETED ---
                # You just spoke, so we delete the old timer by resetting the clock.
                last_interaction_time = time.time() 
                
                if any(w in user_input.lower() for w in ["quit", "exit", "shutdown"]):
                    senses.speak("Shutting down.")
                    break
                
                reply = brain.think(user_input)
                senses.speak(reply)
                
                # --- NEW TIMER STARTED ---
                # Aura finished talking. We start a FRESH 30-second timer now.
                last_interaction_time = time.time()
                print(f"  [System] Waiting for response... ({DORMANCY_TIMEOUT}s remaining)")