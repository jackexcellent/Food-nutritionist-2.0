# Diet Tracker Discord Bot

一個基於人工智慧的 Discord 飲食追蹤機器人，提供食物識別、營養分析和個人化推薦功能。

## 📋 專案概述

這個機器人結合了電腦視覺、營養資料庫和 AI 技術，讓使用者可以通過上傳食物圖片來追蹤飲食，獲得詳細的營養分析和個人化建議。

### 🎯 主要功能 (MVP 版本)

- **🔍 食物識別**: 使用 Azure Computer Vision API 識別上傳的食物圖片
- **📊 營養分析**: 結合 USDA API 和台灣衛福部資料計算營養成分
- **💾 歷史記錄**: 儲存用戶的飲食歷史和偏好
- **🤖 AI 推薦**: 使用 Google Gemini LLM 生成個人化飲食建議
- **📱 Discord 整合**: 透過 Discord Bot 介面提供便利的用戶體驗

### 🏗️ 系統架構

```
diet_tracker_bot/
├── src/                     # 核心程式碼
│   ├── __init__.py         # 套件初始化
│   ├── main.py             # 主程式入口點
│   └── utils.py            # 共用工具函數
├── config/                  # 配置檔案
│   └── .env                # 環境變數 (需要設定API金鑰)
├── data/                   # 資料檔案
│   ├── tfnd_clean.jsonl    # 台灣食物營養資料庫
│   └── cache/              # 快取資料 (自動生成)
├── tests/                  # 測試檔案
│   └── __init__.py
├── docs/                   # 文件資料夾
│   └── README.md           # 專案說明文件
├── logs/                   # 日誌檔案 (自動生成)
├── temp/                   # 臨時檔案 (自動生成)
├── requirements.txt        # Python依賴套件
├── .gitignore             # Git忽略檔案設定
└── setup.py               # 套件安裝設定 (選用)
```

### 🔄 模組依賴圖

```
main.py
├── utils.py (日誌、錯誤處理)
├── bot/ (未來實現)
│   ├── discord_bot.py
│   └── commands.py
├── vision/ (未來實現)
│   ├── food_detector.py
│   └── image_processor.py
├── nutrition/ (未來實現)
│   ├── usda_client.py
│   ├── taiwan_data.py
│   └── calculator.py
├── database/ (未來實現)
│   ├── models.py
│   └── repository.py
└── ai/ (未來實現)
    ├── gemini_client.py
    └── recommendation_engine.py
```

## 🚀 快速開始

### 1. 環境設定

```bash
# 克隆專案 (如果從Git)
git clone <repository-url>
cd diet_tracker_bot

# 建立Python虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安裝依賴套件
pip install -r requirements.txt
```

### 2. API 金鑰設定

複製 `config/.env` 檔案並填入你的 API 金鑰：

```bash
# Azure Computer Vision API 配置
AZURE_KEY=your_azure_cognitive_services_key_here
AZURE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/

# USDA FoodData Central API 配置
USDA_KEY=your_usda_api_key_here

# Google Gemini API 配置
GEMINI_KEY=your_google_gemini_api_key_here

# Discord Bot 配置
DISCORD_TOKEN=your_discord_bot_token_here
```

#### 🔑 取得 API 金鑰指南

1. **Azure Computer Vision**:

   - 前往 [Azure Portal](https://portal.azure.com/)
   - 建立 Cognitive Services 資源
   - 複製金鑰和端點

2. **USDA FoodData Central**:

   - 前往 [USDA FoodData Central](https://fdc.nal.usda.gov/api-guide.html)
   - 註冊並取得免費 API 金鑰

3. **Google Gemini**:

   - 前往 [Google AI Studio](https://aistudio.google.com/)
   - 建立專案並取得 API 金鑰

4. **Discord Bot**:
   - 前往 [Discord Developer Portal](https://discord.com/developers/applications)
   - 建立應用程式和 Bot，複製 Token

### 3. 執行專案

```bash
# 執行主程式 (目前為MVP開發階段)
python src/main.py
```

## 📊 資料來源

### 台灣食物營養資料庫 (tfnd_clean.jsonl)

資料格式說明：

```json
{
  "name_zh": "食物中文名稱",
  "name_en": "Food English Name",
  "nutrients_per_100g": {
    "calories": 130,
    "protein": 2.7,
    "carbohydrates": 28.2,
    "fat": 0.3,
    "fiber": 0.4,
    "sodium": 1,
    "sugar": 0.1
  },
  "food_group": "食物分類",
  "serving_size_common": "常見份量"
}
```

**更新資料步驟**：

1. 下載最新的台灣食物營養成分資料庫
2. 使用資料清理腳本轉換為 JSONL 格式
3. 替換 `data/tfnd_clean.jsonl` 檔案
4. 重新啟動應用程式

## 🧪 測試

```bash
# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_utils.py

# 執行測試並生成覆蓋率報告
pytest --cov=src tests/
```

## 📚 開發指南

### 程式碼風格

- 使用 Python 3.8+語法特性
- 遵循 PEP 8 編碼風格
- 使用型別提示 (Type Hints)
- 添加詳細的 docstring 文件

### 日誌等級

- `DEBUG`: 詳細的除錯資訊
- `INFO`: 一般資訊和系統狀態
- `WARNING`: 警告訊息，但不影響運行
- `ERROR`: 錯誤訊息，可能影響功能
- `CRITICAL`: 嚴重錯誤，導致程式無法繼續

### 錯誤處理

使用專案提供的 `handle_error` 函數統一處理錯誤：

```python
from src.utils import handle_error

try:
    risky_operation()
except Exception as e:
    return handle_error(e, "操作描述", raise_error=False, default_return={})
```

## 🔄 未來擴展計畫

### Phase 1: 核心功能實現 (MVP)

- [x] 專案架構建立
- [ ] Discord Bot 基礎功能
- [ ] 圖像識別整合
- [ ] 營養資料查詢
- [ ] 基本資料儲存

### Phase 2: 功能增強

- [ ] 用戶偏好設定
- [ ] 多語言支援
- [ ] 圖表和統計功能
- [ ] 食物資料庫擴充

### Phase 3: 高級功能

- [ ] 機器學習模型訓練
- [ ] 個人化推薦算法
- [ ] 社群功能 (分享、排行榜)
- [ ] Web 儀表板介面

### Phase 4: 企業級功能

- [ ] 資料庫遷移 (SQLite → MongoDB)
- [ ] 微服務架構
- [ ] 雲端部署 (Docker + Kubernetes)
- [ ] API 速率限制和安全性
- [ ] 多租戶支援

## 🛠️ 技術棧

- **後端**: Python 3.8+
- **Discord**: discord.py
- **電腦視覺**: Azure Computer Vision API, OpenCV
- **AI/LLM**: Google Gemini API
- **資料庫**: SQLite (未來可遷移至 MongoDB)
- **API**: USDA FoodData Central API
- **測試**: pytest
- **日誌**: Python logging, colorlog
- **配置**: python-dotenv

## 🤝 貢獻指南

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📝 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案

## 🆘 故障排除

### 常見問題

1. **模組匯入錯誤**:

   ```bash
   # 確保在專案根目錄執行
   cd diet_tracker_bot
   python src/main.py
   ```

2. **API 金鑰錯誤**:

   - 檢查 `.env` 檔案是否存在
   - 確認所有 API 金鑰都已正確設定
   - 檢查 API 金鑰是否有效且未過期

3. **依賴套件問題**:

   ```bash
   # 更新pip並重新安裝依賴
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

4. **權限問題**:
   - 確保應用程式有讀寫 `data/`、`logs/`、`temp/` 目錄的權限
   - Windows 用戶可能需要以管理員身份執行

### 日誌檔案位置

- 應用程式日誌: `logs/diet_tracker_bot.log`
- 錯誤詳細堆疊: 在 DEBUG 模式下會記錄完整 traceback

### 聯絡資訊

如有問題或建議，請：

1. 開啟 GitHub Issue
2. 聯絡開發團隊: [your-email@example.com]

---

**版本**: 1.0.0 (MVP)  
**最後更新**: 2025-10-22  
**開發團隊**: Food Nutritionist Team
