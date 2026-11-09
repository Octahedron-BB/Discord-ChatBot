# config.py - Configuration file for Discord Chat AI

import os
import re
import json
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load environment variables from .env file located in project directory
dotenv_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path, override=True)
else:
    load_dotenv(override=True)

# --- LLM Provider Configuration ---
# Options: 'deepseek' (default) or 'gemini'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower().strip()

# DeepSeek Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()

# Gemini Configuration
GEMINI_API_KEY = os.getenv("DISCORD_AI_API_KEY", os.getenv("GEMINI_API_KEY", "")).strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
GEMINI_PROXY_URL = os.getenv("GEMINI_PROXY_URL", "").strip()

# Active Model & API Key
API_KEY = DEEPSEEK_API_KEY if LLM_PROVIDER == "deepseek" else GEMINI_API_KEY
MODEL_NAME = DEEPSEEK_MODEL if LLM_PROVIDER == "deepseek" else GEMINI_MODEL

# --- Discord Bot Configuration ---
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()

# Parse allowed private chat IDs from comma-separated list
ALLOWED_PRIVATE_IDS_STR = os.getenv("ALLOWED_PRIVATE_IDS", "")
ALLOWED_PRIVATE_IDS = [int(id.strip()) for id in ALLOWED_PRIVATE_IDS_STR.split(",") if id.strip()]

TARGET_USER_NAME = os.getenv("TARGET_USER_NAME", "me")
DEFAULT_FRIEND_NAME = os.getenv("DEFAULT_FRIEND_NAME", "friend")

# Friend Aliases configuration
FRIEND_ALIASES_JSON = os.getenv('FRIEND_ALIASES_JSON', '{}')
try:
    FRIEND_ALIASES = json.loads(FRIEND_ALIASES_JSON)
except json.JSONDecodeError:
    FRIEND_ALIASES = {}
    print("⚠️ Error parsing FRIEND_ALIASES_JSON, using empty mapping.")

# Enable server mentions
RESPOND_TO_MENTIONS = True  # Bot will respond when @mentioned in servers

# Debug Mode: If True, prints verbose perceptual inputs and returns [DEBUG] info in chat
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower().strip() in ("true", "1", "yes")

# Embedding Model
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# Chat Processing
SESSION_SPLIT_TIME = 1800  # seconds (30 minutes) - time gap to split conversations

# Typo Enhancement
TYPO_PROBABILITY = 0.005  # Probability of introducing typos

# Response Timing
AUTO_REPLY_DELAY_MIN = 2.0  # seconds
AUTO_REPLY_DELAY_MAX = 10.0  # seconds (for testing, adjust for production)

# Proactive Mode
PROACTIVE_IDLE_TIME = float(os.getenv("PROACTIVE_IDLE_TIME", "24"))  # hours before proactive mode triggers
PROACTIVE_CHECK_INTERVAL = int(os.getenv("PROACTIVE_CHECK_INTERVAL", "900"))  # seconds between checks (15 min)

# Vector DB Configuration
DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "discord_memory_db"))
WINDOW_SIZE = 5
STEP = 3

# Automated Reply Configuration
AUTO_REPLY_CHANNEL_ID = int(os.getenv("AUTO_REPLY_CHANNEL_ID", 0))
CHANNEL_REPLY_PROBABILITY = float(os.getenv("CHANNEL_REPLY_PROBABILITY", 0.5))
REFRACTORY_ABSOLUTE = 2.0  # seconds

# User IDs (will be set dynamically)
USER_IDS = {}  # e.g., {"me": "123456", "friend": "789012", ...}


# Persona Loader: loads from environment variable or external file
def load_persona():
    env_persona = os.getenv("PERSONA", "").strip()
    if env_persona:
        return env_persona

    persona_file = os.getenv("PERSONA_FILE", "current_persona.txt").strip()
    if persona_file:
        if not os.path.isabs(persona_file):
            persona_file = os.path.join(BASE_DIR, persona_file)
        if os.path.exists(persona_file):
            try:
                with open(persona_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
            except Exception as e:
                print(f"⚠️ Failed to read persona from {persona_file}: {e}")

    return ""


PERSONA = load_persona()


def update_env_value(key: str, value: str):
    """Dynamically update or append a key-value pair in the .env file and os.environ."""
    os.environ[key] = str(value)
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = rf"^{key}=.*$"
        if re.search(pattern, content, flags=re.MULTILINE):
            new_content = re.sub(pattern, f"{key}={value}", content, flags=re.MULTILINE)
        else:
            new_content = content.rstrip() + f"\n{key}={value}\n"

        with open(env_path, "w", encoding="utf-8") as f:
            f.write(new_content)
    except Exception as e:
        print(f"⚠️ Failed to write to .env: {e}")

