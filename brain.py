import ollama

class Brain:

    def __init__(self, model_name = "llama3.1"):

        self.model = model_name
        self.memory = [] #short conversational memory

        self.system_prompt = {
            'role' : 'system',
            'content' : (
                "You are Aura, an advanced local AI assistant running on a home computer. "
                "You are helpful, concise, and slightly witty. "
                "Keep your answers short and efficient unless asked for details."
            )
        }

        #initialize memory with the system prompt
        self.memory = [self.system_prompt]

    def think(self, user_input):
        
        self.memory.append({'role': 'user', 'content': user_input})

        try:

            print(' Thinking...') #visual feedback for user
            response = ollama.chat(model = self.model, messages = self.memory)

            reply_content = response['message']['content']

            self.memory.append({'role': 'assistant', 'content': reply_content})

            return reply_content

        except Exception as e:
            return f"Error during thinking: {str(e)}"
        
if __name__ == "__main__":

    aura = Brain()
    print("Aura Brain initialized. Type 'exit' to stop.")

    while True:
        user_text = input("You: ")
        if (user_text.lower() in ["exit", "quit"]):
            print("Exiting Aura Brain. Goodbye!")
            break

        response = aura.think(user_text)
        print(f"Aura: {response}")