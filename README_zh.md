# Discord Chat AI (EchoMirror)

[English](README.md) | [繁體中文](README_zh.md)

基於 RAG (檢索增強生成) 與大語言模型（支援 DeepSeek & Gemini）打造的 Discord 高擬真度「數位孿生」自動回覆機器人。能從過往聊天紀錄中學習個人的打字節奏、語氣口癖與歷史記憶。

---

## 🌟 核心功能

- **雙大模型支援**：預設使用 **DeepSeek**（`deepseek-flash` / `deepseek-chat`），可即時無縫切換至 **Google Gemini**（`gemini-3.8-flash` / `gemini-3.1-pro-preview`）。
- **真人連發打字節奏**：支援模擬真人連續發送 1～5 則短訊息，訊息之間具備 Discord「正在輸入…」打字呼吸感。
- **Few-Shot 動態語境學習**：基於 ChromaDB 向量庫檢索真實發言作為對話範例，語氣自然鬆弛，避免機械背誦。
- **多模態視覺與推特解析**：自動辨識聊天圖片、GIF 動圖，並深度解析 Twitter / X 連結與影片首幀封面。
- **Emoji 疲勞度過濾**：自動抑制 AI 濫用 `🤔` 或每句必發表情的慣性，保持 80% 以上真實純文字交流。
- **Discord 內建指令系統**：支援 `!model`、`!debug`、`!help` 等指令，執行指令時自動隔離人設閒聊。
- **群聊主動破冰**：當指定頻道長時間無人發言時，自動從記憶庫中提取話題發起聊天。

---

## 🚀 使用方法

### 1. 準備對話紀錄
使用 [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) 匯出歷史私聊或群聊（格式選 **JSON**），重新命名為 `MyA_Chat.json` 放於專案根目錄。

### 2. 配置環境變數 (`.env`)
複製範本並填入金鑰與 Token：
```bash
cp .env.example .env
```
主要參數說明：
- `LLM_PROVIDER`: 預設服務商 (`deepseek` 或 `gemini`)
- `DEEPSEEK_API_KEY` / `DISCORD_AI_API_KEY`: 模型 API 金鑰
- `DISCORD_BOT_TOKEN`: 你的 Discord Bot Token
- `ALLOWED_PRIVATE_IDS`: 允許私聊與執行管理指令的 Discord 用戶 ID（逗號分隔）
- `AUTO_REPLY_CHANNEL_ID`: 指定自動回覆的群聊頻道 ID（設為 `0` 則僅私聊與 @ 提及時回覆）

### 3. 啟動機器人

**方式 A：使用 Docker（推薦）**
```bash
# 啟動容器
docker compose up -d

# 初始化資料庫（僅首次運行或更新聊天記錄時需要）
docker compose run --rm discord-bot python setup.py
```

**方式 B：本地執行**
```bash
pip install -r requirements.txt
python setup.py          # 首次初始化建庫
python discord_bot.py    # 啟動機器人
```

---

## 💬 常用指令

| 指令 | 權限 | 說明 |
| :--- | :---: | :--- |
| `!help` | 所有人 | 顯示指令說明與當前運行狀態 |
| `!model` | 管理員 | 查看目前運行的模型、服務商與除錯狀態 |
| `!model list` | 管理員 | 查看支援的模型列表 |
| `!model <名稱>` | 管理員 | 切換模型（如 `!model gemini-3.8-flash`、`!model deepseek-flash`） |
| `!model gemini` / `deepseek` | 管理員 | 快速切換服務商 |
| `!debug on` / `off` | 管理員 | 開啟或關閉除錯模式（顯示解析細節） |

---

## 📖 進階文件
詳細的系統架構拆解、程式碼模組功能與 `config.py` 進階參數設定，請參閱 [深入架構與配置文件 (docs/ARCHITECTURE.md)](docs/ARCHITECTURE.md)。
