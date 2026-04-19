# Discord Chat AI

一個模仿 Discord 用户語氣的 AI 自動回覆機器人項目。

## 🌟 核心功能

- **語氣學習**: 從 Discord 聊天记录中分析並模仿特定用戶的說話風格。
- **記憶系統**: 使用向量數據庫（ChromaDB）檢索相關歷史對話背景。
- **人性化模擬**: 自定義回覆延遲與隨機錯字生成，使機器人更像真人。
- **自動化設置**: 提供一键設置腳本，自動完成清洗、分析與數據庫構建。

## 🚀 快速開始

1. **安裝依賴**:
   ```bash
   pip install google-genai sentence-transformers chromadb torch
   ```

2. **配置 API Key**:
   ```bash
   export DISCORD_AI_API_KEY="你的_Google_AI_API_Key"
   ```

3. **運行設置**:
   將 Discord 聊天記錄（JSON）放入根目錄，運行：
   ```bash
   python setup.py
   ```

4. **啟動機器人**:
   ```bash
   python main.py
   ```

## ⚙️ 配置說明

編輯 `config.py` 調整參數：
- `TYPO_PROBABILITY`: 錯字機率。
- `AUTO_REPLY_DELAY_MIN/MAX`: 打字延遲範圍。
- `PROACTIVE_IDLE_TIME`: 主動模式觸發間隔（小時）。
- `PERSONA`: AI 的角色設定。

---

# Discord Chat AI (English Version)

An AI-powered auto-reply bot designed to mimic specific Discord users' speaking styles.

## 🌟 Features

- **Style Learning**: Analyzes and mimics the unique speaking style of a user from Discord chat logs.
- **Memory System**: Leverages a vector database (ChromaDB) to retrieve relevant conversation context.
- **Humanized Interaction**: Customizable reply delays and randomized typo generation for a more natural feel.
- **Automated Setup**: A streamlined setup script handles data cleaning, analysis, and DB construction.

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install google-genai sentence-transformers chromadb torch
   ```

2. **Configure API Key**:
   ```bash
   export DISCORD_AI_API_KEY="your_google_ai_api_key_here"
   ```

3. **Run Setup**:
   Place your Discord chat log (JSON format) in the root directory and run:
   ```bash
   python setup.py
   ```

4. **Launch the Bot**:
   ```bash
   python main.py
   ```

## ⚙️ Configuration

Edit `config.py` to customize parameters:
- `TYPO_PROBABILITY`: Probability of introducing random typos.
- `AUTO_REPLY_DELAY_MIN/MAX`: Range for simulated typing delay.
- `PROACTIVE_IDLE_TIME`: Idle time threshold (hours) before proactive mode triggers.
- `PERSONA`: Detailed character profile for the AI.

## 🛠️ Components

- `cleaner.py`: Processes raw Discord JSON into structured sessions.
- `profile_builder.py`: Uses AI to generate a persona profile from chat data.
- `analyzer.py`: Calculates average response time and word usage.
- `build_vectordb.py`: Builds the semantic memory using sentence embeddings.
- `brain.py`: Core AI logic and query expansion.
- `main.py`: Interactive bot entry point with proactive engagement features.

## ⚠️ Security

- Always use environment variables for your `API_KEY`.
- Avoid uploading sensitive chat data or keys to public repositories.