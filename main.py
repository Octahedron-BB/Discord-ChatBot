import time
import random
import chromadb
import torch
import asyncio
from sentence_transformers import SentenceTransformer
from brain import ChatBrain
from datetime import datetime, timedelta
import config

class TwinEnhancements:
    @staticmethod
    def apply_typo(text, probability=None):
        if probability is None:
            probability = getattr(config, 'TYPO_PROBABILITY', 0.005)
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
        try:
            count = collection.count()
            if count == 0:
                return None
            random_index = random.randint(0, count - 1)
            random_memory = collection.get(limit=1, offset=random_index)
            documents = random_memory.get('documents', [])
            if documents:
                return documents[0].replace("passage: ", "").strip()
            return None
        except Exception as e:
            print(f"⚠️ Failed to retrieve proactive topic: {e}")
            return None

class DiscordTwin:
    def __init__(self, api_key=None, target_user=None, friend_name=None):
        self.brain = ChatBrain(api_key=api_key)
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.embed_model = SentenceTransformer(config.EMBEDDING_MODEL, device=self.device)
        db_path = getattr(config, 'DB_PATH', './discord_memory_db')
        self.db = chromadb.PersistentClient(path=db_path).get_or_create_collection(name="chat_history")
        self.enhancements = TwinEnhancements()
        self.last_interaction_time = datetime.now()
        self.target_user = target_user or getattr(config, 'TARGET_USER_NAME', 'me')
        self.friend_name = friend_name or getattr(config, 'DEFAULT_FRIEND_NAME', 'friend')
        self.conversation_buffer = []

    def get_persona(self):
        persona = getattr(config, 'PERSONA', '').strip()
        if not persona:
            persona = f"You are {self.target_user}, chatting naturally on Discord."
        return persona

    def get_current_mood(self, user_message: str) -> str:
        """Dynamically infer an emotional/engagement state to keep responses flexible and natural."""
        msg_lower = user_message.lower()
        if any(w in msg_lower for w in ["冷", "困", "睡", "累", "下班", "不想起", "烦", "好冷"]):
            return "有点困 / 犯懒 / 缩在被窝里不想动"
        elif any(w in msg_lower for w in ["哈哈", "草", "笑死", "卧槽", "牛逼", "好怪", "抽象"]):
            return "被逗乐 / 轻松吐槽 / 随性发笑"
        elif any(w in msg_lower for w in ["抽卡", "游戏", "更新", "池子", "沉了", "出货", "氪"]):
            return "老玩家闲聊 / 略带调侃 / 佛系心态"
        elif any(w in msg_lower for w in ["吃", "火锅", "烧烤", "奶茶", "饿", "好想吃"]):
            return "嘴馋 / 放松食客 / 想吃好吃的"
        else:
            return "随性摸鱼 / 正常闲聊"

    def get_few_shot_examples(self, user_message: str, partner_name: str = "朋友") -> list[str]:
        """
        Retrieve authentic past dialogues from ChromaDB and format them as Few-Shot in-context learning examples.
        This guides the model's brevity, sentence length, and natural tone by demonstration rather than rigid rules.
        """
        query_text = self.brain.expand_query(user_message)
        emb = self.embed_model.encode([query_text], normalize_embeddings=True).tolist()

        try:
            results = self.db.query(query_embeddings=emb, n_results=8)
            documents = results.get('documents', [[]])[0]

            examples = []
            seen = set()
            for doc in documents:
                clean = doc.replace("passage: ", "").strip()
                if not clean or clean in seen:
                    continue
                seen.add(clean)

                lines = [l.strip() for l in clean.split("\n") if l.strip()]
                if not lines:
                    continue

                formatted_lines = []
                for line in lines:
                    if line.startswith("me:"):
                        content = line[3:].strip()
                        formatted_lines.append(f"{self.target_user}: \"{content}\"")
                    elif ":" in line:
                        _, content = line.split(":", 1)
                        formatted_lines.append(f"{partner_name}: \"{content.strip()}\"")
                    else:
                        formatted_lines.append(f"{self.target_user}: \"{line}\"")

                if formatted_lines:
                    examples.append("\n".join(formatted_lines[:5]))
                    if len(examples) >= 4:
                        break

            return examples
        except Exception as e:
            print(f"⚠️ Few-shot memory retrieval failed: {e}")
            return []

    async def respond(self, a_message, author_id=None, author_name=None, background_history=None):
        self.last_interaction_time = datetime.now()

        # Resolve partner name from aliases or display name
        partner_name = config.FRIEND_ALIASES.get(str(author_id), author_name) if author_name else self.friend_name
        if not partner_name:
            partner_name = self.friend_name

        # 1. Retrieve authentic Few-Shot dialogue examples
        few_shot_examples = self.get_few_shot_examples(a_message, partner_name=partner_name)

        # 2. Dynamic persona resolution
        persona_text = self.get_persona()
        persona_text = persona_text.replace("{{FRIEND_NAME}}", partner_name)
        persona_text = persona_text.replace("{{TARGET_USER_NAME}}", self.target_user)

        few_shot_block = ""
        if few_shot_examples:
            few_shot_block = (
                "[你过往在类似语境下的真实发言范例（严格模仿其断句长度、简短节奏与说话习惯）]:\n"
                "---\n"
                + "\n\n".join(f"范例 {i+1}:\n{ex}" for i, ex in enumerate(few_shot_examples))
                + "\n---\n"
            )

        context_block = ""
        if background_history:
            context_block = f"\n[近期频道上下文]:\n---\n{background_history}\n---\n"

        current_mood = self.get_current_mood(a_message)

        final_prompt = f"""
{persona_text}

[当前状态/心境]: {current_mood}

{few_shot_block}
{context_block}
[当前对话]:
{partner_name}: "{a_message}"

核心回复原则（严格遵守）:
1. 语言节奏与多句打字规则（最高优先级）：
   - 绝大多数时候（80%以上）使用纯文字聊天，不要滥用 emoji！真实好友闲聊大部分都是纯文字快速敲击。
   - 像真人发 Discord 一样按换行连续发 1~5 句短消息（每行一条独立发言，绝不要带序号或标号，系统会模拟真人逐条发送）。
   - 单句字数控制：每句话/每行最多 35 个字以内，保持日常快速打字节奏。
   - 连续发送句数分布：
     * 通常（绝大多数时候）：发 1~2 句（随手一两句吐槽或日常回应）；
     * 偶尔：发 3 句（聊得开心、连发吐槽或追问）；
     * 极少：发 4~5 句（情绪激动、倾诉抱怨或碎碎念，最多绝对不超过 5 句）。
   - 表情稀疏原则（严禁模式化）：
     * 严禁把“第一句发 emoji，第二句发文字”当作固定模板反复套用！
     * 严禁无脑使用 🤔（思考脸），不要一看到问句就先发 🤔。
     * 只有极偶尔（极低概率，约 10%）遇到极其搞笑、无语或震惊时，第一句才可以单发一个 emoji，随后再说文字。
   - 绝对严禁写长篇大论、三段式分析或议论文。
2. 词汇多样性与拒绝复读：
   - 严禁词汇疲劳：不要机械地把“草”、“笑死”、“确实”等词当成逢话必说的万能口头禅。只有在真正戳中笑点或极度认同的情况下才用。
   - 多根据对方说的话具体接梗，说话随性自然，允许省略主谓宾。
3. 链接与媒体互动：
   - 如果对方发了图片、视频或链接预览，像朋友刷到动态一样随口说一句（如吐槽、笑出声或表示想买/想看），不要像讲解员一样逐条分析画面。
"""

        raw_reply = await asyncio.to_thread(
            self.brain.generate_text,
            final_prompt
        )
        final_reply = self.enhancements.apply_typo(raw_reply)
        
        # Dynamic memory buffering (track recent context, prevent self-pollution)
        self.conversation_buffer.append(f"{partner_name}: {a_message}")
        if len(self.conversation_buffer) >= 12:
            self.conversation_buffer.clear()
            
        return final_reply

    async def _process_dynamic_memory(self, segment):
        chat_log = "\n".join(segment)
        prompt = f"Summarize these conversation key points in {self.target_user}'s concise style: {chat_log}"
        try:
            summary = await asyncio.to_thread(
                self.brain.generate_text,
                prompt
            )
            summary = summary.strip()
            self.db.add(
                ids=[f"dyn_mem_{int(time.time())}"],
                embeddings=self.embed_model.encode([summary]).tolist(),
                documents=[summary],
                metadatas=[{"source": "dynamic_memory"}]
            )
            print("🧠 [Background] Processed dynamic memory and saved to ChromaDB.")
        except Exception as e:
            print(f"⚠️ Failed to process dynamic memory: {e}")

    async def generate_group_proactive_message(self, channel_name="群聊"):
        """Generate a proactive ice-breaker message for a specific Discord group/server channel."""
        memory = TwinEnhancements.get_proactive_topic(self.db)
        if not memory:
            print("⚠️ [Proactive] No memory found in database for proactive topic.")
            return None

        persona_text = self.get_persona()
        persona_text = persona_text.replace("{{FRIEND_NAME}}", self.friend_name)
        persona_text = persona_text.replace("{{TARGET_USER_NAME}}", self.target_user)

        prompt = f"""
{persona_text}

【场景】：你在一个 Discord 群聊中（频道名称：{channel_name}）。群里已经很久没有人说话了，有点冷清。
你突然回想起了一段过往的记忆碎片：
---
{memory}
---

【任务指示】：
1. 请完全保持你的角色人设与说话口吻，在群里主动发一句话打破冷场（可以是一句吐槽、分享一件趣事、提出一个和回忆相关的简短话题，或者像日常一样随口咕哝一句）。
2. 极其自然、口语化，符合你的极简/日常风格，字数不要太长。
3. 绝对不要像AI助手或客服，不要打招呼说“大家好”，要像一个真实群友随口发言。
4. 直接输出你要发送的内容，不要附加任何解释或引号。
"""
        try:
            reply = await asyncio.to_thread(self.brain.generate_text, prompt)
            if reply:
                reply = self.enhancements.apply_typo(reply.strip())
            return reply
        except Exception as e:
            print(f"⚠️ [Proactive] Failed to generate group proactive message: {e}")
            return None

    def check_proactive_mode(self, force=False):
        """Legacy 1-on-1 proactive check method (primarily for local CLI test mode)."""
        idle_time = datetime.now() - self.last_interaction_time
        if force or idle_time > timedelta(hours=config.PROACTIVE_IDLE_TIME):
            print("🚨 Activating Proactive Mode...")
            memory = TwinEnhancements.get_proactive_topic(self.db)
            if not memory:
                return None
            
            persona_text = self.get_persona()
            persona_text = persona_text.replace("{{FRIEND_NAME}}", self.friend_name)
            
            prompt = f"""
            {persona_text}
            You noticed it's been a while since you last talked to {self.friend_name}.
            You reviewed previous memory: "{memory}"
            Based on this memory, proactively start a short conversation or share a link in your style.
            """
            response = self.brain.generate_text(prompt)
            return response.strip() if response else None
        return None

    def humanized_reply(self, text):
        delay = random.uniform(config.AUTO_REPLY_DELAY_MIN, config.AUTO_REPLY_DELAY_MAX) 
        print(f"⏳ (Typing delay {delay:.1f}s...)")
        time.sleep(delay)
        print(f"😎 {self.target_user}: {text}\n")

# --- Interactive Test Mode ---
async def interactive_test():
    twin = DiscordTwin()
    
    print("🤖 EchoMirror Test Mode Started!")
    print(f"🧠 Provider: {getattr(config, 'LLM_PROVIDER', 'unknown').upper()} | Model: {getattr(config, 'MODEL_NAME', 'unknown')}")
    print("👉 Type directly to simulate a friend's message.")
    print("👉 Type '/proactive' to force AI to reach out (1-on-1).")
    print("👉 Type '/groupproactive' to test group proactive ice-breaker.")
    print("👉 Type 'exit' to quit.")
    print("-" * 40)
    
    while True:
        try:
            user_input = input(f"{twin.friend_name}: ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input == '/proactive':
                proactive_msg = twin.check_proactive_mode(force=True)
                if proactive_msg:
                    twin.humanized_reply(proactive_msg)
                twin.last_interaction_time = datetime.now()
            elif user_input == '/groupproactive':
                proactive_msg = await twin.generate_group_proactive_message("测试群聊")
                if proactive_msg:
                    twin.humanized_reply(proactive_msg)
                twin.last_interaction_time = datetime.now()
            elif user_input.strip() != "":
                reply = await twin.respond(user_input, author_id="123", author_name="User")
                twin.humanized_reply(reply)
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    asyncio.run(interactive_test())
