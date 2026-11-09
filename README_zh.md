# Discord Chat AI (EchoMirror)

[English](README.md) | [繁體中文](README_zh.md)

一個基於 RAG (檢索增強生成)、Few-Shot 語境學習與多模型架構（DeepSeek & Google Gemini）打造的 Discord 高擬真度「數位孿生」自動回覆機器人項目。它能從過往的聊天紀錄中精準捕捉特定用戶的打字節奏、斷句習慣、表情符號偏好與語義記憶，實現宛如真人打字般的沉浸式交流。

---

## 🌟 核心功能 (Features)

- **雙大模型無縫切換 (Multi-LLM Provider)**:
  - 預設原生支援 **DeepSeek**（`deepseek-flash` 極速多模態、`deepseek-chat` V3、`deepseek-reasoner` R1 思維鏈）。
  - 原生支援 **Google Gemini**（`gemini-3.8-flash` 多模態旗艦、`gemini-3.1-pro-preview` 深度推理），支援自訂 Cloudflare Worker 反向代理以突破地理限制。
  - 可在 Discord 聊天中直接以指令實時無縫切換模型。

- **多句連發打字節奏 (Burst Texting Cadence)**:
  - 徹底告別 AI「一次發一大坨論文」的機械感！支援模擬真人快速發送 1～5 則連續短訊息。
  - 訊息之間具備動態隨機打字延遲與 Discord「正在輸入…」狀態，還原真實鍵盤敲擊呼吸感。

- **Few-Shot 動態語境學習**:
  - 摒棄粗暴的人設生硬灌輸，從 17,000+ 條向量記憶庫（ChromaDB）中動態檢索最相關的真實發言對話對作為 Few-Shot 範例。
  - 自動推斷目前心境狀態（如犯懶、輕鬆吐槽、佛系閒聊等），確保語氣自然鬆弛。

- **多模態視覺與推特媒體解析 (`vision.py`)**:
  - 支援圖片附件、GIF 動圖首幀抽樣特徵解析。
  - 整合 `api.fxtwitter.com` 深度解析 Twitter / X 連結，即使是影片推文也能精準提取高畫質首幀封面與作者推文，解決 Discord 爬蟲與第三方機器人分流問題。

- **防復讀與 Emoji 疲勞度過濾器**:
  - 內建表情符號機率門禁，抑制大模型逢話必發 `🤔` 或特定口癖的模式化慣性。
  - 80% 以上保持真實純文字聊天，保留極為自然的偶發單發表情習慣。

- **Discord 管理指令系統**:
  - 內建 `!model`、`!model list`、`!debug`、`!help` 指令，執行指令時自動攔截並隔離人設閒聊，設定即時熱寫入 `.env`。

- **群聊主動破冰 (Proactive Mode)**:
  - 當指定頻道長時間（如 24 小時）無人發言時，機器人會從過往記憶中提取相關話題主動發起對話。

- **開箱即用與即時熱同步**:
  - 支援 Docker Compose，容器掛載本地代碼卷，配置更改與同步秒級生效。

---

## 📁 系統架構與組件 (Components)

- `discord_bot.py`: **Discord 連線主體**。處理 Gateway 事件、模擬打字呼吸感、解析推特/媒體連結、執行系統指令與多句連發。
- `main.py`: **數位孿生核心 (`DiscordTwin`)**。封裝 ChromaDB 檢索、Few-Shot 範例構建、動態心境推斷與回應生成。
- `brain.py`: **AI 調用引擎 (`ChatBrain`)**。統一封裝 DeepSeek 與 Gemini 的文字生成、視覺多模態與動態模型切換。
- `vision.py`: **視覺與媒體解析**。處理圖片縮放降採樣、GIF 幀抽取、推特元數據解析與畫面理解。
- `analyzer.py`: **特徵分析器**。分析過往對話的回覆延遲與遣詞用字，支援 `--update-config` 自動計算並寫入設定。
- `profile_builder.py`: 人設萃取工具，自動總結目標用戶的心理與表達風格。
- `setup.py`: **自動化初始化腳本**。一鍵執行數據清洗、風格分析、人格生成與向量庫建立。

---

## 🚀 快速開始 (Quick Start)

### 1. 準備對話紀錄 (匯出記憶)
1. 使用 [DiscordChatExporter](https://github.com/Tyrrrz/DiscordChatExporter) 匯出你與朋友的歷史私聊或群組對話，格式選擇 **JSON**。
2. 將匯出的檔案命名為 `MyA_Chat.json` 放於專案根目錄（亦可使用清洗後的 LINE 紀錄）。

### 2. 配置環境變數 (`.env`)
複製專案範本並填入你的密鑰：
```bash
cp .env.example .env
```
編輯 `.env` 檔案：
```env
# --- 選擇預設模型服務商 ('deepseek' 或 'gemini') ---
LLM_PROVIDER=deepseek

# DeepSeek 配置
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-flash

# Google Gemini 配置
DISCORD_AI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
# (選填) Gemini 反向代理
# GEMINI_PROXY_URL=https://your-proxy.workers.dev

# Discord 機器人 Token
DISCORD_BOT_TOKEN=your_discord_bot_token

# 管理員與允許私聊的 Discord 用戶 ID (逗號分隔)
ALLOWED_PRIVATE_IDS=123456789,987654321

# 自動回覆群聊頻道 ID (設為 0 則僅私聊與 @ 提及回覆)
AUTO_REPLY_CHANNEL_ID=0
```

### 3. 啟動方式

#### 選項 A：使用 Docker 部署（推薦，生產環境與 VPS 首選）
```bash
# 1. 啟動機器人容器 (背景執行)
docker compose up -d

# 2. 初始化向量資料庫 (僅首次或更新聊天記錄時執行)
docker compose run --rm discord-bot python setup.py
```

#### 選項 B：本機執行（開發除錯）
```bash
# 1. 安裝相依套件 (建議於虛擬環境執行)
pip install -r requirements.txt

# 2. 執行自動化配置 (清洗、風格分析、建庫)
python setup.py

# 3. 啟動機器人
python discord_bot.py
```

---

## 💬 Discord 聊天室指令手冊

在聊天室中發送以下指令，機器人會立即處理並回傳狀態（**不會觸發角色日常閒聊**）：

| 指令 | 權限要求 | 功能說明 |
| :--- | :---: | :--- |
| `!help` | 所有人 | 顯示完整指令手冊與當前運行狀態 |
| `!model` | 管理員 | 查看當前運行的模型、服務商、代理節點與除錯狀態 |
| `!model list` | 管理員 | 查看目前支援的所有推薦模型列表（含 DeepSeek 與 Gemini） |
| `!model <模型名稱>` | 管理員 | 實時切換模型（如 `!model gemini-3.8-flash`、`!model deepseek-flash`） |
| `!model deepseek` / `!model gemini` | 管理員 | 快捷切換服務商（自動套用該平台最新推薦模型） |
| `!debug` / `!debug on` / `!debug off` | 管理員 | 開啟或關閉除錯模式（開啟後每次發言前附帶其看到的推文/圖片解析） |

---

## ⚙️ 進階配置說明 (`config.py`)

- `AUTO_REPLY_DELAY_MIN` / `AUTO_REPLY_DELAY_MAX`: 模擬真人思考與打字的首句延遲（預設 2.0s ~ 10.0s）。
- `CHANNEL_REPLY_PROBABILITY`: 在自動回覆頻道中隨機接話的機率（預設 0.5）。
- `PROACTIVE_IDLE_TIME`: 頻道閒置多久後觸發主動話題破冰（小時，預設 24）。
- `SESSION_SPLIT_TIME`: 對話會話切分時間間隔（預設 1800 秒）。
- `TYPO_PROBABILITY`: 模擬真人打字手滑的隨機錯字機率（預設 0.005）。
