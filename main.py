import time
import random
import chromadb
import torch
from sentence_transformers import SentenceTransformer
from brain import ChatBrain
from datetime import datetime, timedelta
import config

# --- Configuration ---
# ⚠️ Use environment variables or ensure code is not uploaded to public repositories
MY_API_KEY = config.API_KEY
MY_PERSONA = config.PERSONA

class TwinEnhancements:
    @staticmethod
    def apply_typo(text, probability=config.TYPO_PROBABILITY): 
        if len(text) < 2 or random.random() > probability:
            return text
        text_list = list(text)
        typo_type = random.choice(['swap', 'double', 'skip'])
        idx = random.randint(0, len(text_list) - 2)
        
        if typo_type == 'swap':
            text_list[idx], text_list[idx+1] = text_list[idx+1], text_list[idx]
        elif typo_type == 'double':
            text_list.insert(idx, text_list[idx])
        elif typo_type == 'skip':
            text_list.pop(idx)
        return "".join(text_list)

    @staticmethod
    def get_proactive_topic(collection):
        count = collection.count()
        if count == 0: return None
        random_index = random.randint(0, count - 1)
        random_memory = collection.get(limit=1, offset=random_index)
        content = random_memory['documents'][0]
        return content.replace("passage: ", "").strip()

class DiscordTwin:
    # Fix 1: Accept api_key parameter
    def __init__(self, api_key, target_user='me', friend_name='Friend'):
        self.brain = ChatBrain(api_key=api_key)
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.embed_model = SentenceTransformer(config.EMBEDDING_MODEL, device=self.device)
        self.db = chromadb.PersistentClient(path="./discord_memory_db").get_collection(name="chat_history")
        self.enhancements = TwinEnhancements()
        self.last_interaction_time = datetime.now()
        self.target_user = target_user
        self.friend_name = friend_name

    def get_memories(self, user_message):
        query_text = self.brain.expand_query(user_message)
        emb = self.embed_model.encode([query_text], normalize_embeddings=True).tolist()

        try:
            results = self.db.query(query_embeddings=emb, n_results=3)
            documents = results.get('documents', [[]])[0]
            return "\n".join(documents) if documents else ""
        except Exception as e:
            print(f"⚠️ Memory retrieval failed: {e}")
            return ""

    def respond(self, a_message):
        self.last_interaction_time = datetime.now()
        memories = self.get_memories(a_message)

        # Check if persona is configured
        persona_text = MY_PERSONA.strip() if MY_PERSONA.strip() else "You are a Discord user chatting with a friend. Please reply naturally."

        final_prompt = f"""
        {persona_text}
        Here is the relevant conversation memory as background context:
        ---
        {memories}
        ---
        Now, {self.friend_name} sent a new message: "{a_message}"
        Please reply in your persona.
        """

        response = self.brain.client.models.generate_content(
            model=config.MODEL_NAME,
            contents=final_prompt
        )
        raw_reply = response.text.strip()
        return self.enhancements.apply_typo(raw_reply)

    def check_proactive_mode(self, force=False):
        idle_time = datetime.now() - self.last_interaction_time
        # Trigger proactive mode if idle time exceeds threshold
        if force or idle_time > timedelta(hours=config.PROACTIVE_IDLE_TIME):
            print("🚨 Activating Proactive Mode...")
            memory = TwinEnhancements.get_proactive_topic(self.db)
            
            # Check if persona is configured
            persona_text = MY_PERSONA.strip() if MY_PERSONA.strip() else "You are a Discord user chatting with a friend. Please reply naturally."
            
            prompt = f"""
            {persona_text}
            You noticed it's been a while since you last talked to {self.friend_name}.
            You reviewed previous memory: "{memory}"
            Based on this memory, proactively start a short conversation or share a link in your style.
            """
            response = self.brain.client.models.generate_content(
                model=config.MODEL_NAME,
                contents=prompt
            )
            return response.text.strip()
        return None

    def humanized_reply(self, text):
        # Simulated typing delay
        delay = random.uniform(config.AUTO_REPLY_DELAY_MIN, config.AUTO_REPLY_DELAY_MAX) 
        print(f"⏳ (Typing delay {delay:.1f}s...)")
        time.sleep(delay)
        print(f"😎 {self.target_user}: {text}\n")

# --- Interactive Test Mode ---
if __name__ == "__main__":
    twin = DiscordTwin(api_key=MY_API_KEY)
    
    print("🤖 EchoMirror Test Mode Started!")
    print("👉 Type directly to simulate a friend's message.")
    print("👉 Type '/proactive' to force AI to reach out.")
    print("👉 Type 'exit' to quit.")
    print("-" * 40)
    
    while True:
        try:
            # Add terminal input interface
            user_input = input(f"{twin.friend_name}: ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input == '/proactive':
                proactive_msg = twin.check_proactive_mode(force=True)
                twin.humanized_reply(proactive_msg)
                twin.last_interaction_time = datetime.now()
            elif user_input.strip() != "":
                reply = twin.respond(user_input)
                twin.humanized_reply(reply)
                
        except KeyboardInterrupt:
            break