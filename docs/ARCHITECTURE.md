# System Architecture & Detailed Configuration

This document contains in-depth information about EchoMirror's internal architecture, file components, and advanced configuration options.

---

## 📁 System Components

| File | Role | Description |
| :--- | :--- | :--- |
| `discord_bot.py` | **Bot Entrypoint** | Manages Discord Gateway connection, typing simulation, message burst sequencing, and admin command handling. |
| `main.py` | **Digital Twin Core** | Encapsulates `DiscordTwin`, ChromaDB vector retrieval, Few-Shot turn extraction, and mood synthesis. |
| `brain.py` | **Unified LLM Engine** | Unified interface (`ChatBrain`) for DeepSeek and Google Gemini API calls, vision handling, and runtime model switching. |
| `vision.py` | **Media Understanding** | Handles image downsampling, GIF frame extraction, and Twitter / X metadata/video resolution via `api.fxtwitter.com`. |
| `analyzer.py` | **Statistical Analyzer** | Analyzes user reply latency, message lengths, and vocabulary; auto-tunes configuration via `--update-config`. |
| `profile_builder.py` | **Persona Generator** | Analyzes chat history to generate structured personality summaries. |
| `setup.py` | **Setup Orchestrator** | Automates chat data cleaning, persona extraction, style analysis, and vector database indexing. |

---

## ⚙️ Advanced Configuration (`config.py`)

| Parameter | Default | Description |
| :--- | :---: | :--- |
| `AUTO_REPLY_DELAY_MIN` | `2.0` | Minimum simulated typing delay (seconds) before sending the first response. |
| `AUTO_REPLY_DELAY_MAX` | `10.0` | Maximum simulated typing delay (seconds). |
| `CHANNEL_REPLY_PROBABILITY` | `0.5` | Probability of replying to messages in the designated auto-reply channel (0.0 to 1.0). |
| `PROACTIVE_IDLE_TIME` | `24` | Inactivity threshold (in hours) to trigger a proactive conversation opener. |
| `PROACTIVE_CHECK_INTERVAL`| `900` | Inactivity check frequency (seconds). |
| `SESSION_SPLIT_TIME` | `1800` | Time threshold (seconds) used to split continuous chat into distinct conversation sessions. |
| `WINDOW_SIZE` / `STEP` | `5` / `3` | Sliding window size and step size used when constructing vector chunks for ChromaDB. |
| `REFRACTORY_ABSOLUTE` | `2.0` | Cooldown period (seconds) preventing immediate double-triggering. |
| `TYPO_PROBABILITY` | `0.005` | Chance of simulating natural keyboard typos. |
| `DEBUG_MODE` | `false` | When true, prepends perceived link/vision analysis headers to bot replies. |
