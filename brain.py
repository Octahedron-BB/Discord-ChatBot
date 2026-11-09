import os
import sys
import config
from config import update_env_value

class ChatBrain:
    def __init__(self, api_key=None):
        self.provider = getattr(config, 'LLM_PROVIDER', 'deepseek').lower().strip()
        self.deepseek_client = None
        self.gemini_client = None
        self.model_id = None
        
        if self.provider == 'gemini':
            self._init_gemini(api_key)
        else:
            self._init_deepseek(api_key)

    def _init_deepseek(self, api_key=None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("❌ 'openai' package not installed. Run: pip install openai")

        self.provider = 'deepseek'
        self.api_key = (api_key or config.DEEPSEEK_API_KEY).strip()
        self.base_url = config.DEEPSEEK_BASE_URL or "https://api.deepseek.com"
        self.model_id = config.DEEPSEEK_MODEL or "deepseek-flash"

        if not self.api_key:
            print("⚠️ DEEPSEEK_API_KEY is not set in .env! DeepSeek calls will fail unless configured.")

        print(f"🐳 Initializing DeepSeek Brain (Model: {self.model_id}, Endpoint: {self.base_url})")
        self.deepseek_client = OpenAI(
            api_key=self.api_key or "missing_key",
            base_url=self.base_url
        )
        self.client = self.deepseek_client

    def _init_gemini(self, api_key=None):
        try:
            from google import genai
        except ImportError:
            raise ImportError("❌ 'google-genai' package not installed. Run: pip install google-genai")

        self.provider = 'gemini'
        self.api_key = (api_key or config.GEMINI_API_KEY).strip()
        configured_model = (config.GEMINI_MODEL or "").strip()
        if not configured_model or "2.5" in configured_model:
            configured_model = "gemini-3.8-flash"
        self.model_id = configured_model
        proxy_url = getattr(config, 'GEMINI_PROXY_URL', "").strip()

        if proxy_url:
            print(f"🌍 Initializing Gemini Brain with Proxy: {proxy_url} (Model: {self.model_id})")
            self.gemini_client = genai.Client(
                api_key=self.api_key,
                http_options={"base_url": proxy_url}
            )
        else:
            print(f"🌐 Initializing Gemini Brain via official endpoint (Model: {self.model_id})")
            self.gemini_client = genai.Client(api_key=self.api_key)
        self.client = self.gemini_client

    def switch_model(self, target_spec: str) -> tuple[bool, str]:
        """
        Dynamically switch provider and/or model at runtime and persist to .env.
        Supports:
        - 'deepseek' / 'gemini' (switches provider and loads its configured default model)
        - Specific model names: 'deepseek-flash', 'deepseek-chat', 'gemini-3.8-flash', 'gemini-3.1-pro-preview', etc.
        """
        raw = target_spec.strip()
        lower = raw.lower()

        new_provider = self.provider
        new_model = self.model_id

        if lower in ['gemini', 'google']:
            new_provider = 'gemini'
            current_g = getattr(config, 'GEMINI_MODEL', '').strip()
            if not current_g or '2.5' in current_g:
                new_model = 'gemini-3.8-flash'
            else:
                new_model = current_g
        elif lower in ['deepseek', 'ds']:
            new_provider = 'deepseek'
            new_model = getattr(config, 'DEEPSEEK_MODEL', 'deepseek-flash') or 'deepseek-flash'
        elif 'gemini' in lower:
            new_provider = 'gemini'
            new_model = raw
        elif 'deepseek' in lower:
            new_provider = 'deepseek'
            new_model = raw
        else:
            # Keep current provider and switch to the named model
            new_model = raw

        # Initialize / switch client
        if new_provider == 'gemini':
            if not config.GEMINI_API_KEY:
                return False, "❌ 缺少 GEMINI_API_KEY (DISCORD_AI_API_KEY)，无法切换到 Gemini。"
            try:
                self.model_id = new_model
                self._init_gemini()
            except Exception as e:
                return False, f"❌ 切换至 Gemini 失败: {e}"
        else:
            if not config.DEEPSEEK_API_KEY:
                return False, "❌ 缺少 DEEPSEEK_API_KEY，无法切换到 DeepSeek。"
            try:
                self.model_id = new_model
                self._init_deepseek()
            except Exception as e:
                return False, f"❌ 切换至 DeepSeek 失败: {e}"

        # Update runtime config
        config.LLM_PROVIDER = new_provider
        if new_provider == 'gemini':
            config.GEMINI_MODEL = new_model
        else:
            config.DEEPSEEK_MODEL = new_model

        # Persist to .env
        try:
            update_env_value("LLM_PROVIDER", new_provider)
            if new_provider == 'gemini':
                update_env_value("GEMINI_MODEL", new_model)
            else:
                update_env_value("DEEPSEEK_MODEL", new_model)
        except Exception as e:
            print(f"⚠️ Failed to update .env: {e}")

        provider_name = "Google Gemini" if new_provider == 'gemini' else "DeepSeek"
        return True, f"✅ 模型已成功切换为 **{provider_name}** (`{new_model}`)！\n💾 配置已同步保存至 `.env`。"

    def get_model_status(self) -> str:
        provider_name = "Google Gemini" if self.provider == 'gemini' else "DeepSeek"
        endpoint = getattr(config, 'GEMINI_PROXY_URL', 'Official') if self.provider == 'gemini' else getattr(config, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        debug_status = "🟢 开启" if getattr(config, 'DEBUG_MODE', False) else "🔴 关闭"
        return (
            f"🤖 **当前模型状态**\n"
            f"• **服务商 (Provider)**: `{provider_name}`\n"
            f"• **当前模型 (Model)**: `{self.model_id}`\n"
            f"• **接口节点 (Endpoint)**: `{endpoint}`\n"
            f"• **调试显示 (Debug Mode)**: {debug_status}\n\n"
            f"💡 **快捷指令**:\n"
            f"• `!model list` : 查看推荐模型列表\n"
            f"• `!model <模型名>` : 切换模型 (如 `!model gemini-3.8-flash`)\n"
            f"• `!debug on/off` : 开启/关闭调试解析显示"
        )

    def get_model_list(self) -> str:
        return (
            f"📋 **支持与推荐的模型列表**\n\n"
            f"🌐 **Google Gemini 系列** (`!model gemini` 或具体型号):\n"
            f"• `gemini-3.8-flash` : ⚡ 最新多模态高速旗舰 (推荐默认，识图/闲聊超快)\n"
            f"• `gemini-flash-latest` : 🚀 始终追踪最新的 Gemini Flash 模型\n"
            f"• `gemini-3.1-pro-preview` : 🧠 复杂逻辑推理与深度分析旗舰\n"
            f"• `gemini-pro-latest` : 🏆 始终追踪最新的 Gemini Pro 模型\n"
            f"• `gemini-3.5-flash-lite` : 🪶 极速轻量模型，超低延迟\n"
            f"• `gemini-3.5-flash` : ⚡ 3.5代平稳多模态模型\n\n"
            f"🐳 **DeepSeek 系列** (`!model deepseek` 或具体型号):\n"
            f"• `deepseek-flash` : ⚡ 极速响应，支持多模态识图与深度思考 (当前默认)\n"
            f"• `deepseek-chat` : 💬 DeepSeek-V3 纯文本对话模型\n"
            f"• `deepseek-reasoner` : 🧠 DeepSeek-R1 深度思维链模型\n\n"
            f"👉 **切换指令示例**:\n"
            f"`!model gemini-3.8-flash`\n"
            f"`!model gemini-3.1-pro-preview`\n"
            f"`!model deepseek-flash`\n"
            f"`!model gemini` (自动切换至 Gemini 默认模型 `gemini-3.8-flash`)\n"
            f"`!model deepseek` (自动切换至 DeepSeek 默认模型)"
        )

    def generate_text(self, prompt: str, system_prompt: str = None) -> str:
        """Unified text generation for DeepSeek and Gemini."""
        if self.provider == 'gemini':
            return self._generate_gemini(prompt, system_prompt)
        return self._generate_deepseek(prompt, system_prompt)

    def _generate_deepseek(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            temperature=0.75,
            frequency_penalty=0.2
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    def _generate_gemini(self, prompt: str, system_prompt: str = None) -> str:
        gen_config = {
            "temperature": 0.85
        }
        if system_prompt:
            gen_config["system_instruction"] = system_prompt

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=gen_config
        )
        return (response.text or "").strip()

    def describe_image(self, image_data_url: str, prompt: str = None) -> str:
        """Analyze an image/gif and return a concise text description."""
        instruction = prompt or "简述这张图片的核心内容与文字信息。"

        if self.provider == 'gemini':
            return self._describe_image_gemini(image_data_url, instruction)
        return self._describe_image_deepseek(image_data_url, instruction)

    def _describe_image_deepseek(self, image_data_url: str, instruction: str) -> str:
        # If active model does not have vision (like deepseek-chat or deepseek-reasoner), use deepseek-flash for vision
        vision_model = self.model_id
        if "flash" not in vision_model.lower():
            vision_model = "deepseek-flash"

        response = self.client.chat.completions.create(
            model=vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {"type": "image_url", "image_url": {"url": image_data_url}}
                    ]
                }
            ],
            max_tokens=1500
        )
        msg = response.choices[0].message
        content = (msg.content or "").strip()
        return content

    def _describe_image_gemini(self, image_data_url: str, instruction: str) -> str:
        import base64
        if "," in image_data_url:
            header, b64_str = image_data_url.split(",", 1)
            mime_type = header.split(";")[0].replace("data:", "") or "image/jpeg"
        else:
            b64_str = image_data_url
            mime_type = "image/jpeg"

        raw_bytes = base64.b64decode(b64_str)
        try:
            from google.genai import types
            part = types.Part.from_bytes(data=raw_bytes, mime_type=mime_type)
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[instruction, part]
            )
            return (response.text or "").strip()
        except Exception as e:
            print(f"⚠️ [Gemini Vision] Error: {e}")
            return ""

    def expand_query(self, user_input: str) -> str:
        """Expand user query into search keywords for ChromaDB retrieval."""
        prompt = f"Transform this into 3 Discord search keywords: {user_input}. Output directly, comma-separated."

        try:
            expanded = self.generate_text(prompt)
            if expanded:
                print(f"DEBUG: [{self.provider.upper()}] Expansion result -> {expanded}")
                return f"query: {expanded}"
            return f"query: {user_input}"
        except Exception as e:
            print(f"⚠️ Query expansion with {self.provider} ({self.model_id}) failed: {e}")
            return f"query: {user_input}"

    def list_my_models(self):
        """List available models for the current API key."""
        print(f"🔍 Querying available models for {self.provider.upper()}...")
        if self.provider == 'gemini':
            for model in self.client.models.list():
                print(f" - {model.name}")
        else:
            try:
                models = self.client.models.list()
                for m in models:
                    print(f" - {m.id}")
            except Exception as e:
                print(f"⚠️ Failed to list models: {e}")
