# config.py - Configuration file for Discord Chat AI

import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_KEY = os.getenv("DISCORD_AI_API_KEY", "your_api_key_here")  # Use environment variable for security

# Discord Bot Configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

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

# Model Configuration
MODEL_NAME = "gemini-2.5-flash"

# Embedding Model
EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

# Chat Processing
SESSION_SPLIT_TIME = 1800  # seconds (30 minutes) - time gap to split conversations

# Typo Enhancement
TYPO_PROBABILITY = 0.005  # Probability of introducing typos

# Response Timing
AUTO_REPLY_DELAY_MIN = 2  # seconds
AUTO_REPLY_DELAY_MAX = 10.0  # seconds (for testing, adjust for production)

# Proactive Mode
PROACTIVE_IDLE_TIME = 24  # hours - time before proactive mode activates

# Vector DB Configuration
WINDOW_SIZE = 5
STEP = 3

# Automated Reply Configuration
AUTO_REPLY_CHANNEL_ID = int(os.getenv("AUTO_REPLY_CHANNEL_ID", 0))
CHANNEL_REPLY_PROBABILITY = float(os.getenv("CHANNEL_REPLY_PROBABILITY", 0.5))
REFRACTORY_ABSOLUTE = 2.0  # seconds

# User IDs (will be set dynamically)
USER_IDS = {}  # e.g., {"me": "123456", "friend": "789012", ...}

# Persona (can be customized)
# Run 'python profile_builder.py' to auto-generate based on your chat data
PERSONA = """ """
