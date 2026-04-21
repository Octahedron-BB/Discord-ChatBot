import time
import random
import chromadb
import torch
import asyncio
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
        self.db = chromadb.PersistentClient(path="./discord_memory_db").get_or_create_collection(name="chat_history")
        self.enhancements = TwinEnhancements()
        self.last_interaction_time = datetime.now()
        self.target_user = target_user
        self.friend_name = friend_name
        self.conversation_buffer = []

    def get_memories(self, user_message):
        query_text = self.brain.expand_query(user_message)
        emb = self.embed_model.encode([query_text], normalize_embeddings=True).tolist()

        try:
            results = self.db.query(query_embeddings=emb, n_results=10)
            documents = results.get('documents', [[]])[0]
            return "\n".join(documents) if documents else ""
        except Exception as e:
            print(f"⚠️ Memory retrieval failed: {e}")
            return ""

    async def respond(self, a_message, author_id=None, author_name=None, background_history=None):
        self.last_interaction_time = datetime.now()
        memories = self.get_memories(a_message)

        # Resolve name from environment-driven aliases
        partner_name = config.FRIEND_ALIASES.get(str(author_id), author_name) if author_name else self.friend_name
        if not partner_name:
            partner_name = self.friend_name

        # Check if persona is configured
        persona_text = MY_PERSONA.strip() if MY_PERSONA.strip() else "You are a Discord user chatting with a friend. Please reply naturally."
        # Dynamic placeholder replacement
        persona_text = persona_text.replace("{{FRIEND_NAME}}", partner_name)

        context_block = ""
        if background_history:
            context_block = f"\n[Recent Conversation Context]:\n---\n{background_history}\n---\n"

        final_prompt = f"""
        {persona_text}
        
        [Past Memory Fragments (Your Lived Experiences)]:
        ---
        {memories}
        ---
        {context_block}
        
        [Current Interaction]:
        {partner_name}: "{a_message}"
        
        Instruction: 
        1. Reply in your persona. 
        2. These memory fragments represent your real past. If they contain specific factual details (like prices, numbers, specific names, or past events), INCORPORATE them accurately into your response.
        3. Use the [Recent Conversation Context] to understand the current flow, but prioritize direct responses to the [Current Interaction].
        4. Prioritize current conversation flow and personas consistency.
        5. Do NOT say "I don't know" if the answer is hidden in the Fragments above.
        """

        response = await asyncio.to_thread(
            self.brain.client.models.generate_content,
            model=config.MODEL_NAME,
            contents=final_prompt
        )
        raw_reply = response.text.strip()
        final_reply = self.enhancements.apply_typo(raw_reply)
        
        # Dynamic memory buffering
        self.conversation_buffer.append(f"{partner_name}: {a_message}")
        self.conversation_buffer.append(f"{self.target_user}: {final_reply}")

        if len(self.conversation_buffer) >= 10:
            segment = self.conversation_buffer.copy()
            self.conversation_buffer.clear()
            asyncio.create_task(self._process_dynamic_memory(segment))
            
        return final_reply

    async def _process_dynamic_memory(self, segment):
        chat_log = "\n".join(segment)
        prompt = f"Summarize in Bibi's tone: {chat_log}"
        try:
            response = await asyncio.to_thread(
                self.brain.client.models.generate_content,
                model=config.MODEL_NAME,
                contents=prompt
            )
            summary = response.text.strip()
            self.db.add(
                ids=[f"dyn_mem_{int(time.time())}"],
                embeddings=self.embed_model.encode([summary]).tolist(),
                documents=[summary],
                metadatas=[{"source": "dynamic_memory"}]
            )
            print("🧠 [Background] Processed dynamic memory and saved to ChromaDB.")
        except Exception as e:
            print(f"⚠️ Failed to process dynamic memory: {e}")

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
async def interactive_test():
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
                reply = await twin.respond(user_input, author_id="123", author_name="User")
                twin.humanized_reply(reply)
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    asyncio.run(interactive_test())