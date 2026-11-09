# Discord Chat AI (EchoMirror)

[English](README.md) | [繁體中文](README_zh.md)

An AI-powered Discord "digital twin" auto-reply bot built with RAG (Retrieval-Augmented Generation) and multi-LLM support (**DeepSeek** & **Google Gemini**). Accurately mimics a specific user's texting cadence, casual tone, emoji habits, and conversational memories.

---

## 🌟 Features

- **Dual-LLM Support**: Built-in support for **DeepSeek** (`deepseek-flash` / `deepseek-chat`) and **Google Gemini** (`gemini-3.8-flash` / `gemini-3.1-pro-preview`) with runtime seamless switching.
- **Burst Texting Cadence**: Sends **1 to 5 sequential short messages** with simulated typing delays and Discord "typing..." state intervals instead of monolithic text blocks.
- **Few-Shot In-Context Learning**: Dynamically pulls real conversation pairs from ChromaDB as Few-Shot exemplars, maintaining a relaxed, authentic tone.
- **Multimodal Vision & Twitter/X Parsing**: Automatically recognizes images/GIFs and extracts high-resolution video thumbnails and tweets via `api.fxtwitter.com`.
- **Emoji Anti-Fatigue Filtering**: Intelligently suppresses repetitive emojis (like `🤔`), keeping 80%+ of chat in natural plain text while preserving sporadic reactions.
- **In-Chat Bot Commands**: Manage models and debug settings in Discord (`!model`, `!debug`, `!help`) without triggering persona chatter.
- **Proactive Group Ice-Breaking**: Automatically recalls past memories to break the silence when a designated channel stays inactive.

---

## 🚀 Usage

### 1. Prepare Chat Data
Export your chat history (DMs or server channels) using [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) as **JSON**, rename it to `MyA_Chat.json`, and place it in the project root.

### 2. Configure Environment (`.env`)
Copy the sample environment file and add your keys:
```bash
cp .env.example .env
```
Key settings:
- `LLM_PROVIDER`: Default model provider (`deepseek` or `gemini`)
- `DEEPSEEK_API_KEY` / `DISCORD_AI_API_KEY`: API keys
- `DISCORD_BOT_TOKEN`: Your Discord bot token
- `ALLOWED_PRIVATE_IDS`: Discord user IDs allowed to DM and run admin commands (comma-separated)
- `AUTO_REPLY_CHANNEL_ID`: Channel ID for auto-replies (set to `0` to only reply in DMs & @mentions)

### 3. Run the Bot

**Option A: Using Docker (Recommended)**
```bash
# Start container in background
docker compose up -d

# Initialize vector database (Only needed on first run or data update)
docker compose run --rm discord-bot python setup.py
```

**Option B: Local Execution**
```bash
pip install -r requirements.txt
python setup.py          # Initialize database
python discord_bot.py    # Start the bot
```

---

## 💬 Bot Commands

| Command | Permission | Description |
| :--- | :---: | :--- |
| `!help` | Everyone | Shows command manual and runtime status |
| `!model` | Admin | Displays active model, provider, and debug mode |
| `!model list` | Admin | Lists verified, recommended models |
| `!model <name>` | Admin | Switches model (e.g., `!model gemini-3.8-flash` or `!model deepseek-flash`) |
| `!model gemini` / `deepseek` | Admin | Quick-switches provider to default recommended model |
| `!debug on` / `off` | Admin | Toggles debug mode (inspects parsed vision/link tokens) |

---

## 📖 In-Depth Documentation
For component breakdowns, internal architecture, and advanced parameters in `config.py`, see [Architecture & Configuration (docs/ARCHITECTURE.md)](docs/ARCHITECTURE.md).
