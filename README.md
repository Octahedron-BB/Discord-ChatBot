# Discord Chat AI (EchoMirror)

一個基於 RAG (檢索增強生成) 與 Gemini API 打造的 Discord 自動回覆機器人項目。它能從過往的聊天記錄中分析並模仿特定用戶的說話風格、口癖與記憶，實現極高擬真度的「數位孿生」。

## 🌟 核心功能 (Features)

- **語氣學習**: 從 Discord 聊天記錄中分析並精準模仿特定用戶的說話風格與 Emoji 習慣。
- **長期記憶系統**: 使用向量數據庫（ChromaDB）與 Sentence-Transformers 檢索相關歷史對話背景。
- **人性化互動**: 自定義回覆延遲（模擬打字狀態）與隨機錯字生成，徹底褪去機器味。
- **自動化設置**: 提供一鍵設置腳本，自動完成數據清洗、特徵分析與資料庫構建。
- **開箱即用的部署**: 支援 Docker Compose，無懼底層依賴衝突，VPS 部署首選。

## 📁 系統架構與組件 (Components)

- `cleaner.py`: 將原始 Discord JSON 匯出檔清洗並結構化為對話片段。
- `profile_builder.py`: 使用 AI 從聊天數據中生成專屬的角色設定 (Persona)。
- `analyzer.py`: 計算平均回覆延遲時間與字詞使用習慣。
- `build_vectordb.py`: 建立語義記憶庫 (Semantic Memory)。
- `brain.py`: AI 核心邏輯與查詢擴展 (Query Expansion)。
- `main.py` / `discord_bot.py`: 機器人互動入口與 Discord 連線處理。

## 🚀 快速開始 (Quick Start)

### 1. 準備對話紀錄 (匯出記憶)
1. 使用 [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) 匯出你與朋友的歷史私聊或群組對話，格式請選擇 **JSON**。
2. 將匯出的檔案重新命名為 `MyA_Chat.json`（或依腳本設定）並放入專案根目錄。

### 2. 配置環境變數 (`.env`)
在專案根目錄建立 `.env` 檔案，嚴格按照以下格式填入設定：

```env
# Google Gemini API Key
DISCORD_AI_API_KEY=你的_GEMINI_API_金鑰

# Discord bot Token 
DISCORD_BOT_TOKEN=你的_DISCORD_機器人_TOKEN

# 允許私聊的 Discord ID (多個 ID 請用逗號分隔，例如: 12345,67890)
ALLOWED_PRIVATE_IDS=XXXXX,XXXX

# 機器人要模仿的目標使用者名稱 (Persona)
TARGET_USER_NAME=

# 預設聊天對象的名稱
DEFAULT_FRIEND_NAME=

# (選填) 關閉 ChromaDB 匿名追蹤以保持日誌乾淨
ANONYMIZED_TELEMETRY=False
```

### 3. 啟動方式 (選擇一種)

#### 選項 A：使用 Docker 部署（推薦，適合 VPS 與生產環境）
```bash
# 1. 啟動機器人容器
docker compose up -d

# 2. 構建向量資料庫與自動化分析 (僅第一次或更新資料時需要)
docker compose run --rm discord-bot python setup.py
```

#### 選項 B：本地運行（適合開發測試）
```bash
# 1. 安裝依賴 (建議使用虛擬環境)
pip install -r requirements.txt

# 2. 運行自動化設置 (清洗、分析、建庫)
python setup.py

# 3. 啟動機器人
python main.py
```

## ⚙️ 配置說明 (Configuration)

編輯 `config.py` 來微調機器人的行為參數：
- `TYPO_PROBABILITY`: 隨機錯字生成的機率。
- `AUTO_REPLY_DELAY_MIN` / `MAX`: 模擬真人打字延遲的秒數範圍。
- `PROACTIVE_IDLE_TIME`: 主動模式觸發間隔（小時），閒置過久會主動搭話。
- `PERSONA`: AI 的詳細角色人格設定。

## ⚠️ 注意事項

- **硬體資源**：在沒有 GPU 的環境（如 VPS），安裝依賴時請確保下載 CPU 版本的 PyTorch (`--extra-index-url https://download.pytorch.org/whl/cpu`) 以節省空間。

---

# Discord Chat AI (EchoMirror) - English Version

An AI-powered auto-reply Discord bot built with RAG (Retrieval-Augmented Generation) and the Gemini API. It accurately mimics the speaking style, habits, and memories of a specific user based on past chat logs, creating a highly realistic "digital twin."

## 🌟 Features

- **Style Learning**: Analyzes and perfectly mimics a specific user's speaking style and emoji habits from Discord chat logs.
- **Long-term Memory System**: Leverages a vector database (ChromaDB) and Sentence-Transformers to retrieve relevant historical conversation context.
- **Humanized Interaction**: Features customizable simulated typing delays and randomized typo generation for a natural feel.
- **Automated Setup**: A streamlined setup script automatically handles data cleaning, analysis, and DB construction.
- **Containerized Deployment**: Docker Compose ready, making it robust against dependency conflicts and ideal for VPS deployment.

## 📁 Components

- `cleaner.py`: Processes raw Discord JSON exports into structured sessions.
- `profile_builder.py`: Uses AI to generate a dedicated persona profile from chat data.
- `analyzer.py`: Calculates average response time and vocabulary habits.
- `build_vectordb.py`: Builds the semantic memory using sentence embeddings.
- `brain.py`: Core AI logic and query expansion.
- `main.py` / `discord_bot.py`: Interactive bot entry point and Discord gateway handler.

## 🚀 Quick Start

### 1. Prepare Chat Data
1. Export your historical DMs or server chats using [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter). Set the export format to **JSON**.
2. Rename the exported file to `MyA_Chat.json` (or as configured) and place it in the project root directory.

### 2. Configure Environment (`.env`)
Create a `.env` file in the root directory and fill it out following this format:

```env
# Google Gemini API Key
DISCORD_AI_API_KEY=your_gemini_api_key_here

# Discord bot Token 
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Allowed private chat IDs (comma separated)
ALLOWED_PRIVATE_IDS=12345,67890

# Target user name to mimic (Persona)
TARGET_USER_NAME=YourName

# Default chat partner's name
DEFAULT_FRIEND_NAME=FriendName

# Disable ChromaDB telemetry for cleaner logs
ANONYMIZED_TELEMETRY=False
```

### 3. Launch the Bot (Choose one method)

#### Option A: Docker Deployment (Recommended for VPS)
```bash
# 1. Build and start the container
docker compose up -d

# 2. Run the setup script to build the DB (Only needed on first run or data update)
docker compose run --rm discord-bot python setup.py
```

#### Option B: Local Execution
```bash
# 1. Install dependencies (Virtual environment recommended)
pip install -r requirements.txt

# 2. Run automated setup (Cleans data, analyzes, and builds DB)
python setup.py

# 3. Launch the bot
python main.py
```

## ⚙️ Configuration

Edit `config.py` to customize the bot's behavior:
- `TYPO_PROBABILITY`: Probability of introducing random typos.
- `AUTO_REPLY_DELAY_MIN` / `MAX`: Range for the simulated typing delay (in seconds).
- `PROACTIVE_IDLE_TIME`: Idle time threshold (hours) before the bot initiates a conversation proactively.
- `PERSONA`: Detailed character profile and instructions for the AI.

## ⚠️ Notes

- **Resources**: When installing on a VPS without a GPU, ensure you install the CPU version of PyTorch to save disk space.