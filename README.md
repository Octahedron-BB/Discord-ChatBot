# Discord Chat AI (EchoMirror)

一個基於 RAG (檢索增強生成) 與 Gemini API 打造的 Discord 自動回覆機器人項目。它能從過往的聊天記錄中分析並模仿特定用戶的說話風格、口癖與記憶，實現極高擬真度的「數位孿生」。

## 🌟 核心功能 (Features)

- **語氣學習**: 從 Discord 聊天記錄中分析並精準模仿特定用戶的說話風格。
- **動態學習能力**: 機器人能在對話過程中實時記錄新的交流片段，並自動更新至長期記憶庫中。
- **上下文關聯**: 自動擷取最近的對話歷史作為背景，確保回覆內容具有高度的連貫性。
- **語義檢索增強 (RAG)**: 使用向量數據庫 (ChromaDB) 檢索歷史記憶，並具備 **查詢擴展 (Query Expansion)** 技術，自動優化搜尋關鍵詞以提高匹配率。
- **人性化互動**: 支援模擬打字狀態、隨機錯字生成，以及基於統計數據的 **自動回覆延遲調優**。
- **開箱即用的部署**: 支援 Docker Compose，具備代理伺服器 (Proxy) 支援，無懼網路限制。

## 📁 系統架構與組件 (Components)

- `setup.py`: **核心設置腳本**。依次執行數據清洗、人格生成、風格分析與數據庫構建。
- `discord_bot.py`: **機器人運行主體**。處理 Discord 連線、模擬打字動畫，並支援連網代理 (Proxy) 設定。
- `analyzer.py`: **特徵分析器**。分析用戶回覆延遲與遣詞用字，支持 `--update-config` 自動將統計結果應用至設定檔。
- `main.py`: 封裝了 `DiscordTwin` 類，核心處理 RAG 檢索、動態學習與文本生成。
- `brain.py`: AI 核心邏輯，負責調用 Gemini API 與執行 **查詢擴展**，提升記憶檢索深度。

## 🚀 快速開始 (Quick Start)

### 1. 準備對話紀錄 (匯出記憶)
1. 使用 [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) 匯出你與朋友的歷史私聊或群組對話，格式請選擇 **JSON**。
2. 將匯出的檔案重新命名為 `MyA_Chat.json`（或依腳本設定）並放入專案根目錄。

### 2. 配置環境變數 (`.env`)
在專案根目錄建立 `.env` 檔案，嚴格按照以下格式填入設定：

```env
# Google Gemini API Key
DISCORD_AI_API_KEY=你的_GEMINI_API_金鑰

# (選填) 好友暱稱映射 (JSON 格式，ID需為字串)
FRIEND_ALIASES_JSON='{"123456789": "暱稱"}'

# (選填) 指定自動回覆頻道 ID
AUTO_REPLY_CHANNEL_ID=

# (選填) 自動回覆機率 (0.0 到 1.0)
CHANNEL_REPLY_PROBABILITY=0.5

# (選填) 關閉 ChromaDB 匿名追蹤
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
- `PROACTIVE_IDLE_TIME`: 主動模式觸發間隔（小時）。
- `SESSION_SPLIT_TIME`: 對話會話分割時間（秒），預設 1800 秒。
- `WINDOW_SIZE` / `STEP`: 向量資料庫構建時的滑動窗口大小與步長。
- `REFRACTORY_ABSOLUTE`: 強制冷卻時間（秒），防止連續觸發。
- `PERSONA`: AI 的詳細角色人格設定。

- **硬體資源**：在沒有 GPU 的環境（如 VPS），安裝依賴時請確保下載 CPU 版本的 PyTorch (`--extra-index-url https://download.pytorch.org/whl/cpu`) 以節省空間。

---

# Discord Chat AI (EchoMirror) - English Version

An AI-powered auto-reply Discord bot built with RAG (Retrieval-Augmented Generation) and the Gemini API. It accurately mimics the speaking style, habits, and memories of a specific user based on past chat logs, creating a highly realistic "digital twin."

## 🌟 Features

- **Style Learning**: Analyzes and mimics a specific user's speaking style from Discord chat logs.
- **Dynamic Learning**: Real-time recording of ongoing conversations, automatically indexed into the long-term memory.
- **Contextual Awareness**: Automatically retrieves recent message history to ensure highly coherent responses.
- **Retrieval-Augmented Generation (RAG)**: Leverages ChromaDB for memory recall, featuring **Query Expansion** to automatically optimize search terms for better accuracy.
- **Humanized Interaction**: Features simulated typing status, randomized typos, and **auto-tuned reply delays** based on user statistics.
- **Ready-to-Deploy**: Docker Compose support with built-in **Proxy handling** for restricted network environments.

## 📁 Components

- `setup.py`: **Main Setup Script**. Automates cleaning, persona building, style analysis, and DB construction.
- `discord_bot.py`: **Bot Entry Point**. Handles Discord connectivity, simulated typing, and optional proxy settings.
- `analyzer.py`: **Style Analyzer**. Examines reply latency and vocabulary, supports `--update-config` to auto-apply statistics.
- `main.py`: Contains the `DiscordTwin` class which handles RAG retrieval, dynamic learning, and generation.
- `brain.py`: Core AI logic, responsible for Gemini API interaction and **Query Expansion** for deeper memory retrieval.

## 🚀 Quick Start

### 1. Prepare Chat Data
1. Export your historical DMs or server chats using [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter). Set the export format to **JSON**.
2. Rename the exported file to `MyA_Chat.json` (or as configured) and place it in the project root directory.

### 2. Configure Environment (`.env`)
Create a `.env` file in the root directory and fill it out following this format:

```env
# Google Gemini API Key
DISCORD_AI_API_KEY=your_gemini_api_key_here

# (Optional) Friend Name Aliases (JSON format, IDs must be strings)
FRIEND_ALIASES_JSON='{"123456789": "Nickname"}'

# (Optional) Specific Auto-Reply Channel ID
AUTO_REPLY_CHANNEL_ID=

# (Optional) Auto-Reply Probability (0.0 to 1.0)
CHANNEL_REPLY_PROBABILITY=0.5

# (Optional) Disable ChromaDB telemetry
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
- `AUTO_REPLY_DELAY_MIN` / `MAX`: Range for simulated typing delay (seconds).
- `PROACTIVE_IDLE_TIME`: Threshold (hours) for initiating proactive conversations.
- `SESSION_SPLIT_TIME`: Session timeout (seconds) for splitting chat history.
- `WINDOW_SIZE` / `STEP`: Sliding window configuration for vector DB indexing.
- `REFRACTORY_ABSOLUTE`: Mandatory cooldown period (seconds) between replies.
- `PERSONA`: Detailed character profile and instructions for the AI.

- **Resources**: When installing on a VPS without a GPU, ensure you install the CPU version of PyTorch to save disk space.