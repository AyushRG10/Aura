import sys
import requests
import json
import time

# Import the hardware driver
try:
    from senses import SensoryCortex
except ImportError:
    print("CRITICAL ERROR: Could not find 'sense.py'.")
    print("Please make sure both files are in the same folder.")
    sys.exit(1)

class NeuralCortex:
    def __init__(self):
        # Configuration for the AI Brain (Ollama)
        self.host = "http://localhost:11434"
        self.url = f"{self.host}/api/generate"
        
        # User requested: Gemma 2 2B IT (Instruction Tuned)
        self.model = "gemma2:2b" 
        self.context = []
        
        # --- SMART STARTUP CHECK ---
        try:
            tags_response = requests.get(f"{self.host}/api/tags")
            if tags_response.status_code == 200:
                available_models = [m['name'] for m in tags_response.json().get('models', [])]
                
                if self.model in available_models:
                    print(f"  [System] Brain: Connected to {self.model}")
                elif available_models:
                    print(f"  [System] Warning: '{self.model}' not found.")
                    print(f"  [System] Available brains: {available_models}")
                    self.model = available_models[0]
                    print(f"  [System] Auto-switched to: {self.model}")
                else:
                    print("  [System] CRITICAL: No models found in Ollama!")
                    print("  [Action] Run: ollama pull gemma2:2b")
            else:
                print("  [System] Warning: Could not verify models (Ollama might be busy).")
                
        except Exception:
            print("  [System] WARNING: Ollama is not running. Brain is offline.")

    def think(self, prompt):
        print("  [Thinking...]")
        
        # --- BEHAVIOR CONTROL ---
        # This tells the AI exactly how to behave for every response
        system_instruction = (
            "You are Aura. Do NOT use emojis. "
            "Be extremely concise and quick. "
            "Only provide details if explicitly asked."
        )

        data = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction, # Added the rule here
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
                return (f"Error 404: I tried to use '{self.model}', but it is missing. "
                        f"Please check your Ollama models.")
            else:
                return f"I am having trouble thinking. Error {response.status_code}."
                
        except Exception:
            return "I cannot connect to my neural network. Is Ollama running?"

# --- MAIN EXECUTION LOOP ---
if __name__ == "__main__":
    print("--- AURA SYSTEM STARTUP ---")
    
    # 1. Initialize Hardware
    try:
        senses = SensoryCortex()
    except Exception as e:
        print(f"Hardware Failure: {e}")
        sys.exit(1)

    # 2. Initialize Software
    brain = NeuralCortex()
    
    # 3. Startup Message
    senses.speak(f"System online using {brain.model}.")

    # 4. The Conversation Loop
    while True:
        user_input = senses.listen()
        
        if user_input:
            if any(word in user_input.lower() for word in ["quit", "exit", "shutdown"]):
                senses.speak("Shutting down. Goodbye.")
                break
            
            reply = brain.think(user_input)
            senses.speak(reply)