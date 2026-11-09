# Discord Chat AI (EchoMirror)

[English](README.md) | [繁體中文](README_zh.md)

An AI-powered Discord "digital twin" auto-reply bot built with RAG (Retrieval-Augmented Generation), Few-Shot in-context learning, and dual-provider LLM support (**DeepSeek** & **Google Gemini**). It captures and mimics a specific user's conversational tone, texting cadence, emoji habits, and episodic memories based on past chat archives.

---

## 🌟 Key Features

- **Dual LLM Provider & Dynamic Switching**:
  - Native support for **DeepSeek** (`deepseek-flash` for high-speed multimodal, `deepseek-chat` V3, `deepseek-reasoner` R1 reasoning chain).
  - Native support for **Google Gemini** (`gemini-3.8-flash` multimodal flagship, `gemini-3.1-pro-preview` deep reasoning). Supports Cloudflare Worker reverse proxies for geo-unrestricted connectivity.
  - Seamless in-chat runtime model switching via bot commands (`!model`).

- **Human-like Burst Texting Cadence**:
  - Say goodbye to monolithic AI essay responses! Sends **1 to 5 sequential short messages** just like a real friend chatting on Discord.
  - Features dynamic typing delays and realistic Discord "typing..." state intervals between message bursts.

- **Few-Shot In-Context Persona Learning**:
  - Instead of brittle and rigid prompt scripts, dynamically retrieves semantic dialogue pairs from a 17,000+ vector memory database (ChromaDB) as Few-Shot exemplars.
  - Dynamically infers mood states (casual, sleepy, sarcastic, teasing) to maintain conversational elasticity.

- **Multimodal Vision & Twitter/X Media Parsing (`vision.py`)**:
  - Automatically parses attached images and samples first-frame features from GIFs.
  - Integrates `api.fxtwitter.com` to resolve Twitter / X links, extracting high-resolution video thumbnails and tweet bodies even when companion bots split embeds.

- **Anti-Fatigue & Emoji Frequency Control**:
  - Built-in probabilistic gating to prevent AI inductive bias from overusing emojis (e.g., spamming `🤔` on every question).
  - Maintains 80%+ pure text conversations while preserving natural, sporadic standalone emoji reactions.

- **Isolated Bot Management Commands**:
  - Built-in commands (`!model`, `!model list`, `!debug`, `!help`) that execute immediately without leaking into or triggering persona chatter.
  - Settings are hot-persisted to `.env` in real time.

- **Proactive Group Ice-Breaking**:
  - When an assigned server channel remains quiet for an extended period (e.g., 24 hours), the bot recalls a memory from the database and proactively initiates a conversation.

- **Docker-Ready & Hot-Reloadable**:
  - Full Docker Compose integration with volume-mapped code execution for instant updates.

---

## 📁 System Architecture & Components

- `discord_bot.py`: **Main Discord Entrypoint**. Handles Gateway events, simulated typing cadence, Twitter/media resolution, bot commands, and sequential burst sending.
- `main.py`: **Digital Twin Core (`DiscordTwin`)**. Coordinates ChromaDB memory retrieval, Few-Shot prompt assembly, and dynamic mood synthesis.
- `brain.py`: **Unified LLM Engine (`ChatBrain`)**. Abstracts DeepSeek and Gemini API calls, vision multimodal queries, and dynamic model switching.
- `vision.py`: **Visual & Media Understanding**. Handles image downsampling, GIF frame extraction, and Twitter metadata retrieval.
- `analyzer.py`: **Chat Feature Analyzer**. Examines reply latency and message length distributions, automatically tuning timing parameters via `--update-config`.
- `profile_builder.py`: Behavioral profile generator for extracting communication style summaries from raw chat logs.
- `setup.py`: **All-in-One Initializer**. Automates data cleaning, persona building, style analysis, and vector database indexing.

---

## 🚀 Quick Start

### 1. Prepare Chat Data
1. Export your historical Discord DMs or group chats using [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) (Select **JSON** format).
2. Rename the exported file to `MyA_Chat.json` and place it in the project root directory (cleaned LINE chat exports are also supported).

### 2. Configure Environment (`.env`)
Copy the sanitized environment template:
```bash
cp .env.example .env
```
Edit your `.env` file with your credentials:
```env
# --- Choose default LLM provider ('deepseek' or 'gemini') ---
LLM_PROVIDER=deepseek

# DeepSeek Configuration
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-flash

# Google Gemini Configuration
DISCORD_AI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
# Optional Gemini reverse proxy
# GEMINI_PROXY_URL=https://your-worker.workers.dev

# Discord Bot Token
DISCORD_BOT_TOKEN=your_discord_bot_token

# Admin & allowed private chat Discord User IDs (comma-separated)
ALLOWED_PRIVATE_IDS=123456789,987654321

# Auto-reply server channel ID (Set to 0 to only reply in DMs & @mentions)
AUTO_REPLY_CHANNEL_ID=0
```

### 3. Launching the Bot

#### Option A: Docker Deployment (Recommended for VPS / Production)
```bash
# 1. Start the bot container in background
docker compose up -d

# 2. Build the vector database (Only needed on first setup or data update)
docker compose run --rm discord-bot python setup.py
```

#### Option B: Local Execution (For Development)
```bash
# 1. Install dependencies (Virtual environment recommended)
pip install -r requirements.txt

# 2. Run automated setup (Cleans data, analyzes habits, builds DB)
python setup.py

# 3. Start the bot
python discord_bot.py
```

---

## 💬 In-Chat Bot Commands

Send these commands in any channel or DM where the bot has access (**commands will never trigger persona chit-chat**):

| Command | Permission | Description |
| :--- | :---: | :--- |
| `!help` | Everyone | Displays the help manual and current runtime status |
| `!model` | Admin | Shows active model, provider, endpoint, and debug mode status |
| `!model list` | Admin | Displays all verified, recommended models (DeepSeek & Gemini) |
| `!model <name>` | Admin | Seamlessly switches the model (e.g., `!model gemini-3.8-flash` or `!model deepseek-flash`) |
| `!model deepseek` / `!model gemini` | Admin | Quick-switches provider and automatically selects its recommended default |
| `!debug` / `!debug on` / `!debug off` | Admin | Toggles debug mode (inspects parsed vision/link preview tokens before reply) |

---

## ⚙️ Advanced Settings (`config.py`)

- `AUTO_REPLY_DELAY_MIN` / `AUTO_REPLY_DELAY_MAX`: Simulated reading/typing delay before the first message (default: 2.0s ~ 10.0s).
- `CHANNEL_REPLY_PROBABILITY`: Probability of spontaneously replying to a message in the auto-reply channel (default: 0.5).
- `PROACTIVE_IDLE_TIME`: Inactivity threshold (in hours) to trigger a proactive conversation opener (default: 24).
- `SESSION_SPLIT_TIME`: Conversation session segmentation boundary (default: 1800 seconds).
- `TYPO_PROBABILITY`: Chance of simulating natural human keyboard slips (default: 0.005).
