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
│   ├── main.py             # 主程式入口點 (CLI)
│   ├── utils.py            # 共用工具函數 + 快取機制
│   ├── image_processor.py  # 圖像處理模組 (階段1)
│   ├── nutrition_calculator.py  # 營養計算模組 (階段2)
│   └── data_storage.py     # ✨ 資料儲存模組 (階段4)
├── config/                  # 配置檔案
│   └── .env                # 環境變數 (需要設定API金鑰)
├── data/                   # 資料檔案
│   ├── tfnd_clean.jsonl    # 台灣食物營養資料庫
│   ├── user_data.db        # ✨ SQLite 使用者資料庫 (階段4)
│   └── cache/              # 快取資料 (自動生成)
├── tests/                  # 測試檔案
│   ├── __init__.py
│   ├── test_image_processor.py      # 圖像處理測試 (階段1)
│   ├── test_nutrition_calculator.py # 營養計算測試 (階段2)
│   ├── test_integration.py          # 系統整合測試 (階段3)
│   └── test_data_storage.py         # ✨ 資料儲存測試 (階段4)
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
├── utils.py (日誌、錯誤處理、圖像儲存、快取機制)
├── image_processor.py (圖像識別與食物偵測 - 階段1)
├── nutrition_calculator.py (營養計算與資料庫查詢 - 階段2)
├── data_storage.py (✨ SQLite 資料儲存 - 階段4)
├── bot/ (未來實現)
│   ├── discord_bot.py
│   └── commands.py
├── database/ (未來實現 - MongoDB)
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

# 🆕 測試圖像處理功能 (階段1)
python -m src.image_processor path/to/your/test_image.jpg

# 🆕 測試營養計算功能 (階段2)
python -m src.nutrition_calculator mackerel apple rice --debug
```

## 🖼️ 階段 1: 圖像處理功能

### 圖像識別流程

這個階段實現了核心的圖像處理和食物識別功能：

1. **圖像預處理**:

   - 自動調整圖像大小到 800x600 標準尺寸
   - 使用高斯模糊去噪，保持食物細節清晰
   - 保存預處理後的圖像到 `temp/` 目錄用於偵錯

2. **Azure Computer Vision 整合**:

   - 安全的 API 金鑰管理 (從 `.env` 載入)
   - 智能的食物標籤提取 (過濾非食物項目)
   - 多重數據源分析 (標籤 + 描述文字)

3. **結果處理**:
   - 去重和過濾無效項目
   - 置信度篩選 (可調整閾值)
   - 返回清理後的食物名稱列表

### 使用範例

```python
from src.image_processor import process_image

# 分析單張圖像
foods = process_image("my_lunch.jpg")
print(f"識別出的食物: {foods}")
# 輸出: ['rice', 'chicken', 'vegetables']

# 命令列使用
python -m src.image_processor my_lunch.jpg --debug
```

### 錯誤處理與容錯

- **API 故障**: 自動記錄錯誤並返回空列表，不會中斷程式
- **圖像格式**: 支援常見格式 (JPG, PNG)，自動檢測無效檔案
- **網路問題**: 完整的重試機制和超時處理
- **未來擴展**: 預留本地 AI 模型 fallback 接口

## 🍎 階段 2: 營養計算功能 (新增)

### 營養查詢流程

這個階段實現了營養資訊查詢和計算功能：

1. **台灣食品營養資料庫 (TFND) 查詢**:

   - 載入本地 JSONL 資料庫 (`data/tfnd_clean.jsonl`)
   - 精確匹配食物英文名稱 (不區分大小寫)
   - 從 `nutrients_per_100g` 提取熱量資訊

2. **智能模糊匹配**:

   - 使用 fuzzywuzzy 或 difflib 進行相似度匹配
   - 閾值設定 >80% 確保準確度
   - 自動處理拼寫錯誤和變體名稱

3. **USDA API Fallback**:

   - 當本地資料庫無匹配時，自動呼叫 USDA FoodData Central API
   - 智能單位轉換 (kJ → kcal)
   - 完整的錯誤處理和重試機制

4. **熱量計算**:
   - 返回每種食物的熱量值 (kcal/100g)
   - 自動計算總熱量
   - 處理查詢失敗情況 (返回 0 kcal)

### 使用範例

```python
from src.nutrition_calculator import get_nutrition

# 查詢單個或多個食物
foods = ['mackerel', 'apple', 'rice']
nutrition_dict, total_calories = get_nutrition(foods)

print("營養資訊:")
for food, calories in nutrition_dict.items():
    print(f"  {food}: {calories} kcal")
print(f"總熱量: {total_calories} kcal")

# 輸出範例:
#   mackerel: 410.0 kcal
#   apple: 52.0 kcal
#   rice: 183.0 kcal
# 總熱量: 645.0 kcal

# 命令列使用
python -m src.nutrition_calculator mackerel apple rice --debug
```

### 匹配邏輯詳解

**1. 精確匹配 (Exact Match)**:

```python
# 直接比對 name_en 欄位 (小寫)
"mackerel" → 鯖魚(炒) ✓ 410 kcal
"apple" → 蘋果 ✓ 52 kcal
```

**2. 模糊匹配 (Fuzzy Match)**:

```python
# 使用相似度算法，閾值 >80%
"mackrel" (拼寫錯誤) → "mackerel" ✓ 410 kcal
"apples" (複數形式) → "apple" ✓ 52 kcal
"grilled chicken" → "chicken" ✓ (自動移除描述詞)
```

**3. USDA API Fallback**:

```python
# 本地資料庫無匹配時
"pizza" → USDA API 查詢 → 266 kcal (依API結果)
"hamburger" → USDA API 查詢 → 295 kcal
```

### 食物名稱處理

**當前實現 (MVP)**:

- 接受英文食物名稱輸入
- 自動清理描述詞 (如 fried, grilled, baked)
- 轉小寫並去除多餘空格

**未來擴展計畫**:

```python
# 計畫中的多語言支援
# 1. 中文名稱翻譯 (使用 googletrans)
"蘋果" → translate → "apple" → 52 kcal

# 2. 中英混用處理
"grilled 鯖魚" → "mackerel" → 410 kcal

# 3. 地區性食物名稱
"滷肉飯" → TFND查詢 → 本地資料庫
"珍珠奶茶" → 台灣特色食物資料庫

# 4. 同義詞和別名
"番茄" / "西紅柿" → "tomato"
"馬鈴薯" / "土豆" → "potato"
```

### 錯誤處理

- **資料庫載入失敗**: 返回空列表，記錄警告
- **API 連接錯誤**: 自動 fallback，返回 0 kcal
- **無效食物名稱**: 返回 0 kcal，記錄偵錯資訊
- **JSON 解析錯誤**: 跳過錯誤行，繼續處理

### 效能優化 (未來)

```python
# 計畫中的優化方案
1. 使用 Pandas DataFrame 加速查詢
2. 建立食物名稱索引
3. 快取 USDA API 結果
4. 批量查詢優化
5. 非同步 API 呼叫
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

# 🆕 執行圖像處理模組測試
pytest tests/test_image_processor.py -v

# 🆕 執行營養計算模組測試 (階段2)
pytest tests/test_nutrition_calculator.py -v

# 執行特定測試檔案
pytest tests/test_utils.py

# 執行測試並生成覆蓋率報告
pytest --cov=src tests/

# 執行圖像處理測試（詳細輸出）
pytest tests/test_image_processor.py -v --tb=short

# 執行營養計算測試 (階段2)
pytest tests/test_nutrition_calculator.py -v

# 執行系統整合測試 (階段3)
pytest tests/test_integration.py -v

# ✨ 執行資料儲存測試 (階段4, 26項測試)
pytest tests/test_data_storage.py -v
```

### 🆕 圖像處理測試指南

新增的測試涵蓋以下功能：

1. **圖像預處理測試**: 驗證圖像調整大小和去噪功能
2. **Azure API 模擬測試**: 使用 mock 避免真實 API 呼叫
3. **食物識別解析測試**: 測試從 API 結果提取食物項目
4. **錯誤處理測試**: 驗證各種異常情況的處理
5. **工具函數測試**: 測試圖像保存和格式化功能

```python
# 運行特定測試類別
pytest tests/test_image_processor.py::TestImageProcessor::test_preprocess_image_success -v

# 運行整合測試
pytest tests/test_image_processor.py::TestIntegration -v
```

### 🆕 營養計算測試指南 (階段 2)

新增的營養計算測試涵蓋：

1. **TFND 資料庫測試**:

   - 資料庫載入和解析
   - 精確匹配查詢
   - 模糊匹配算法

2. **匹配邏輯測試**:

   - 精確匹配 (exact match)
   - 模糊匹配 (fuzzy match, >80% threshold)
   - 食物名稱清理和標準化

3. **USDA API 測試**:

   - API 成功回應處理
   - API 錯誤處理 (網路錯誤、無結果)
   - 單位轉換 (kJ → kcal)

4. **整合測試**:
   - 端到端工作流程
   - 多食物查詢
   - Fallback 機制驗證

```python
# 運行特定測試類別
pytest tests/test_nutrition_calculator.py::TestNutritionCalculator -v

# 測試模糊匹配功能
pytest tests/test_nutrition_calculator.py::TestNutritionCalculator::test_query_tfnd_fuzzy_match -v

# 測試 USDA API fallback
pytest tests/test_nutrition_calculator.py::TestNutritionCalculator::test_query_usda_api_success -v

# 運行整合測試
pytest tests/test_nutrition_calculator.py::TestIntegration -v
```

---

## 🔗 階段 3: 系統整合 (MVP CLI)

### 功能概述

整合階段完成了圖像處理和營養計算兩個模組的串接，提供命令列介面(CLI)來測試完整的端到端流程。

### 核心功能

#### 1. CLI 入口 (`src/main.py`)

提供命令列介面來測試圖像到熱量的完整流程：

```bash
# 基本使用
python src/main.py --image test_images/apple.jpg

# 啟用除錯模式
python src/main.py --image test_images/meal.jpg --debug

# 查看版本
python src/main.py --version

# 查看幫助
python src/main.py --help
```

**輸出範例:**

```
=============================================================
階段 1: 圖像處理與食物識別
=============================================================
📸 載入圖像: test_images/apple.jpg
🔍 使用 Azure Computer Vision 識別食物...
✅ 成功識別 2 種食物
   食物清單: apple, banana

=============================================================
階段 2: 營養計算與熱量統計
=============================================================
📊 查詢營養資訊...
   - 優先查詢快取
   - TFND 資料庫精確/模糊匹配
   - USDA API fallback
✅ 營養計算完成

=============================================================
📋 處理結果摘要
=============================================================

🍽️  識別的食物清單 (2 項):
   1. apple
   2. banana

🔥 營養資訊 (每 100g):
   ✅ apple          :   52.0 kcal
   ✅ banana         :   89.0 kcal

📊 總熱量: 141.0 kcal
=============================================================

💡 資料來源:
   • 圖像識別: Azure Computer Vision API
   • 營養資料: TFND 台灣食品營養資料庫 + USDA FoodData Central
   • 快取機制: 記憶體快取 (未來可升級為 Redis)
```

#### 2. 快取機制 (`src/utils.py`)

實現記憶體快取來優化常見食物的查詢效能：

**快取功能:**

- 全域 dict 快取（MVP 階段）
- TTL (Time-To-Live) 24 小時自動過期
- 最大快取 1000 項
- 簡易 LRU 淘汰策略

**使用範例:**

```python
from utils import get_cached_nutrition, set_cached_nutrition

# 查詢快取
calories = get_cached_nutrition('apple')
if calories is None:
    # 從資料庫或 API 查詢
    calories = query_from_database('apple')
    # 存入快取
    set_cached_nutrition('apple', calories, source='TFND')
```

**未來升級計畫:**

```python
# Redis 快取範例（未來實現）
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

# 設定 TTL 為 1 小時
cache.setex(
    f'nutrition:{food_name}',
    3600,
    json.dumps({'calories': 52.0, 'source': 'TFND'})
)

# 讀取快取
cached_data = cache.get(f'nutrition:{food_name}')
if cached_data:
    nutrition = json.loads(cached_data)
```

#### 3. 端到端整合流程

```
┌─────────────┐
│   使用者    │
│  上傳圖像   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  階段 1: 圖像處理 (image_processor) │
├─────────────────────────────────────┤
│ • 載入圖像檔案                       │
│ • 圖像預處理 (CLAHE + 銳化)         │
│ • Azure Computer Vision API 呼叫    │
│ • 食物標籤解析與過濾                │
└──────────────┬──────────────────────┘
               │ 食物清單 ['apple', 'banana']
               ▼
┌─────────────────────────────────────┐
│ 階段 2: 營養計算 (nutrition_calculator)│
├─────────────────────────────────────┤
│ 對每個食物:                          │
│   1. 檢查快取 (utils.get_cached)    │
│   2. TFND 精確匹配                  │
│   3. TFND 模糊匹配 (>80%)           │
│   4. USDA API fallback              │
│   5. 存入快取 (utils.set_cached)    │
└──────────────┬──────────────────────┘
               │ {'apple': 52.0, 'banana': 89.0}
               ▼
┌─────────────────────────────────────┐
│  階段 3: 結果顯示 (main.py)         │
├─────────────────────────────────────┤
│ • 格式化食物清單                    │
│ • 顯示各項熱量                      │
│ • 計算總熱量                        │
│ • 顯示資料來源                      │
└─────────────────────────────────────┘
```

### 整合測試 (`tests/test_integration.py`)

新增完整的端到端整合測試：

```bash
# 運行所有整合測試
pytest tests/test_integration.py -v

# 運行特定測試類別
pytest tests/test_integration.py::TestEndToEndIntegration -v
pytest tests/test_integration.py::TestCachePerformance -v

# 測試完整工作流程
pytest tests/test_integration.py::TestEndToEndIntegration::test_full_workflow_image_to_calories -v
```

**測試涵蓋範圍:**

- ✅ 端到端工作流程（圖像 → 食物 → 熱量）
- ✅ 快取機制測試
- ✅ 多資料來源整合（TFND + USDA）
- ✅ 錯誤處理測試
- ✅ 快取過期機制
- ✅ 資料流標準化

### 錯誤處理機制

整合了全域錯誤處理，確保系統穩定性：

```python
# 在 main.py 中
try:
    # 階段 1: 圖像處理
    food_items = processor.process_image(image_path)

    # 階段 2: 營養計算
    nutrition_data, total = get_nutrition(food_items)

    # 階段 3: 顯示結果
    display_results(food_items, nutrition_data, total)

except FileNotFoundError:
    logger.error("圖像檔案不存在")
except Exception as e:
    handle_error(e, "處理失敗", logger)
```

**錯誤類型:**

- `FileNotFoundError`: 圖像檔案不存在
- `APIError`: Azure/USDA API 呼叫失敗
- `DataNotFoundError`: 營養資料查詢失敗

### 未來擴展計畫

#### 份量識別

```python
# 未來功能：支援份量輸入
python src/main.py --image meal.jpg --portions "apple:1,banana:2"

# 輸出會根據份量調整
# apple (1個, ~150g): 78 kcal
# banana (2根, ~240g): 213 kcal
# 總熱量: 291 kcal
```

#### 多語言支援

```python
# 未來功能：支援中文食物名稱
from googletrans import Translator
translator = Translator()

# 自動翻譯
zh_name = "蘋果"
en_name = translator.translate(zh_name, src='zh-tw', dest='en').text
# en_name = "apple"
```

#### Discord Bot 整合

```python
# 未來功能：Discord Bot 命令
@bot.command()
async def analyze(ctx, *, image_url: str):
    """分析食物圖像"""
    # 1. 下載圖像
    # 2. 呼叫 process_image_to_nutrition()
    # 3. 格式化結果並回覆
    await ctx.send(f"總熱量: {total_calories} kcal")
```

#### 效能優化

```python
# 使用 Pandas DataFrame 優化 TFND 查詢
import pandas as pd

class NutritionCalculator:
    def __init__(self):
        # 載入為 DataFrame
        self.tfnd_df = pd.read_json(TFND_DATA_PATH, lines=True)
        # 建立索引
        self.tfnd_df.set_index('name_en', inplace=True)

    def _query_tfnd(self, food_name):
        # 快速查詢
        return self.tfnd_df.loc[food_name.lower()]
```

### 使用統計

快取統計資訊：

```python
from utils import get_cache_stats

stats = get_cache_stats()
print(f"快取大小: {stats['size']}/{stats['max_size']}")
print(f"TTL: {stats['ttl_hours']} 小時")
print(f"快取項目: {stats['items']}")
```

---

## � 階段 4: 資料儲存與持久化

### 功能概述

實現 SQLite 資料庫用於儲存用戶的飲食記錄，並提供完整的 MongoDB 遷移文檔，為未來的雲端部署做準備。

### 資料庫架構

#### SQLite Schema (MVP)

```sql
-- meals 表：儲存用戶飲食記錄
CREATE TABLE meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 記錄ID
    user_id TEXT NOT NULL,                 -- 使用者ID (Discord ID)
    date TEXT NOT NULL,                    -- 飲食日期 (ISO 8601格式)
    foods TEXT NOT NULL,                   -- 食物列表 (JSON格式)
    calories REAL NOT NULL,                -- 總熱量 (kcal)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))  -- 記錄建立時間
);

-- 索引：優化按用戶和日期的查詢效能
CREATE INDEX idx_meals_user_date ON meals(user_id, date DESC);
```

**資料範例:**

```json
{
  "id": 1,
  "user_id": "discord_user_123456",
  "date": "2024-10-28T12:30:00",
  "foods": {
    "apple": 52.0,
    "chicken": 165.0,
    "rice": 130.0
  },
  "calories": 347.0,
  "created_at": "2024-10-28T12:31:45"
}
```

### 核心功能 (`src/data_storage.py`)

#### 1. 資料庫初始化

```python
from src.data_storage import init_database

# 初始化資料庫（自動創建表和索引）
init_database()
```

#### 2. 儲存飲食記錄

```python
from src.data_storage import store_meal

# 儲存記錄
user_id = "discord_user_123456"
foods = {"apple": 52.0, "banana": 89.0}
calories = sum(foods.values())

record_id = store_meal(user_id, foods, calories)
print(f"記錄已儲存，ID: {record_id}")

# 指定日期儲存
from datetime import datetime
custom_date = datetime(2024, 10, 27, 18, 30).isoformat()
record_id = store_meal(user_id, foods, calories, date=custom_date)
```

#### 3. 查詢歷史記錄

```python
from src.data_storage import get_history

# 查詢最近 7 天的記錄（默認）
history = get_history(user_id)

# 查詢最近 30 天的記錄
history = get_history(user_id, days=30)

# 記錄格式: (id, date, foods_dict, calories, created_at)
for record in history:
    print(f"日期: {record[1]}")
    print(f"食物: {record[2]}")
    print(f"熱量: {record[3]} kcal")
    print("---")
```

#### 4. 查詢單筆記錄

```python
from src.data_storage import get_meal_by_id

# 根據 ID 查詢
meal = get_meal_by_id(record_id)

if meal:
    print(f"用戶: {meal[1]}")
    print(f"日期: {meal[2]}")
    print(f"食物: {meal[3]}")
    print(f"熱量: {meal[4]} kcal")
```

#### 5. 刪除記錄

```python
from src.data_storage import delete_meal

# 刪除指定記錄
success = delete_meal(record_id)

if success:
    print("記錄已刪除")
else:
    print("記錄不存在或刪除失敗")
```

#### 6. 統計功能

```python
from src.data_storage import get_statistics

# 獲取最近 7 天的統計
stats = get_statistics(user_id, days=7)

print(f"總飲食次數: {stats['total_meals']}")
print(f"總熱量: {stats['total_calories']} kcal")
print(f"平均熱量: {stats['avg_calories']:.2f} kcal/餐")
print("最常見食物:")
for food, count in stats['most_common_foods']:
    print(f"  • {food}: {count} 次")
```

#### 7. 資料匯出

```python
from src.data_storage import export_to_json

# 匯出所有資料為 JSON
output_path = export_to_json("backup/meals_backup.json")
print(f"資料已匯出至: {output_path}")
```

### MongoDB 遷移指南

當需要擴展到雲端部署時，可以遷移至 MongoDB：

#### 安裝 MongoDB 驅動

```bash
pip install pymongo
```

#### MongoDB Schema

```python
# meals 集合（Collection）
{
    "_id": ObjectId("..."),
    "user_id": "discord_user_123456",
    "date": ISODate("2024-10-28T12:30:00Z"),
    "foods": {
        "apple": 52.0,
        "chicken": 165.0,
        "rice": 130.0
    },
    "calories": 347.0,
    "created_at": ISODate("2024-10-28T12:31:45Z")
}
```

#### MongoDB 連接設定

```python
from pymongo import MongoClient

# 連接 MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["diet_tracker"]
meals_collection = db["meals"]

# 創建索引
meals_collection.create_index([("user_id", 1), ("date", -1)])
meals_collection.create_index("created_at", expireAfterSeconds=31536000)  # 1年TTL
```

#### 資料遷移函數

```python
from src.data_storage import get_db_connection
from pymongo import MongoClient

def migrate_to_mongodb(mongo_uri="mongodb://localhost:27017/"):
    """將 SQLite 資料遷移至 MongoDB"""
    # 連接 MongoDB
    client = MongoClient(mongo_uri)
    db = client["diet_tracker"]
    meals_collection = db["meals"]

    # 讀取 SQLite 資料
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meals")
        rows = cursor.fetchall()

        for row in rows:
            # 轉換為 MongoDB 文檔
            document = {
                "user_id": row['user_id'],
                "date": row['date'],
                "foods": json.loads(row['foods']),
                "calories": row['calories'],
                "created_at": row['created_at']
            }

            # 插入 MongoDB
            meals_collection.insert_one(document)

    print(f"成功遷移 {len(rows)} 筆記錄")
```

#### MongoDB 操作範例

每個 `data_storage.py` 函數的 docstring 都包含對應的 MongoDB 實現：

```python
# 儲存記錄（MongoDB 版本）
meal_doc = {
    "user_id": user_id,
    "date": datetime.now(),
    "foods": foods_dict,
    "calories": calories,
    "created_at": datetime.now()
}
result = meals_collection.insert_one(meal_doc)
meal_id = result.inserted_id

# 查詢歷史（MongoDB 版本）
from datetime import datetime, timedelta
start_date = datetime.now() - timedelta(days=7)
meals = meals_collection.find({
    "user_id": user_id,
    "date": {"$gte": start_date}
}).sort("date", -1)

# 統計查詢（MongoDB 版本）
pipeline = [
    {"$match": {"user_id": user_id, "date": {"$gte": start_date}}},
    {"$group": {
        "_id": None,
        "total_meals": {"$sum": 1},
        "total_calories": {"$sum": "$calories"},
        "avg_calories": {"$avg": "$calories"}
    }}
]
stats = list(meals_collection.aggregate(pipeline))
```

### 資料流程圖

```
┌──────────────┐
│   使用者     │
│  上傳圖像    │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────┐
│ 階段 1-3: 圖像 → 食物 → 熱量       │
│ (image_processor + nutrition_calc)  │
└──────────────┬─────────────────────┘
               │ {'apple': 52.0, 'banana': 89.0}
               ▼
┌────────────────────────────────────┐
│  階段 4: 資料儲存 (data_storage)   │
├────────────────────────────────────┤
│  store_meal(user_id, foods, 141.0) │
│         ↓                          │
│  SQLite Database                   │
│  data/user_data.db                 │
│         ↓                          │
│  INSERT INTO meals                 │
│  (user_id, date, foods, calories)  │
└────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│  查詢與統計功能                    │
├────────────────────────────────────┤
│  • get_history(user_id, days=7)    │
│    → 最近 N 天飲食記錄             │
│                                    │
│  • get_statistics(user_id, days=7) │
│    → 總餐數、平均熱量、常見食物    │
│                                    │
│  • export_to_json(path)            │
│    → 資料備份與遷移                │
└────────────────────────────────────┘
```

### 測試 (`tests/test_data_storage.py`)

完整的資料儲存測試涵蓋：

```bash
# 運行所有資料儲存測試（26 項測試）
pytest tests/test_data_storage.py -v

# 測試類別分類
pytest tests/test_data_storage.py::TestDatabaseConnection -v      # 資料庫連接測試
pytest tests/test_data_storage.py::TestStoreMeal -v               # 儲存功能測試
pytest tests/test_data_storage.py::TestGetHistory -v              # 歷史查詢測試
pytest tests/test_data_storage.py::TestGetStatistics -v           # 統計功能測試
pytest tests/test_data_storage.py::TestIntegration -v             # 整合測試

# 測試特定功能
pytest tests/test_data_storage.py::TestStoreMeal::test_store_meal_json_encoding -v
pytest tests/test_data_storage.py::TestGetHistory::test_get_history_order -v
```

**測試涵蓋範圍：**

- ✅ 資料庫連接與初始化
- ✅ Schema 驗證（表結構、欄位、索引）
- ✅ 儲存功能（基本、指定日期、JSON 編碼、參數驗證）
- ✅ 歷史查詢（默認/自定義天數、排序、空結果、參數驗證）
- ✅ 單筆記錄查詢（成功、不存在）
- ✅ 刪除功能（成功、不存在）
- ✅ 統計功能（基本統計、最常見食物、空資料）
- ✅ JSON 匯出（檔案生成、內容驗證）
- ✅ 錯誤處理（連接錯誤、無效 JSON）
- ✅ 完整工作流程整合測試

### 效能優化建議

#### SQLite 優化

```sql
-- 啟用 WAL 模式（提升並發效能）
PRAGMA journal_mode = WAL;

-- 增加快取大小
PRAGMA cache_size = -64000;  -- 64MB

-- 啟用記憶體映射 I/O
PRAGMA mmap_size = 268435456;  -- 256MB
```

#### MongoDB 索引優化

```python
# 複合索引優化查詢
meals_collection.create_index([
    ("user_id", 1),
    ("date", -1),
    ("calories", -1)
])

# 文字搜索索引（未來擴展）
meals_collection.create_index([("foods", "text")])

# TTL 索引自動清理舊資料
meals_collection.create_index(
    "created_at",
    expireAfterSeconds=31536000  # 保留 1 年資料
)
```

### 資料備份與恢復

#### SQLite 備份

```bash
# 使用 SQLite CLI 備份
sqlite3 data/user_data.db ".backup backup/user_data_backup.db"

# 使用 Python 備份
python -c "from src.data_storage import export_to_json; export_to_json('backup/meals.json')"
```

#### MongoDB 備份

```bash
# 使用 mongodump 備份
mongodump --db diet_tracker --collection meals --out backup/

# 恢復資料
mongorestore --db diet_tracker backup/diet_tracker/
```

### 安全性考量

1. **SQL Injection 防護**：使用參數化查詢

   ```python
   # ✅ 安全：使用參數化查詢
   cursor.execute("SELECT * FROM meals WHERE user_id = ?", (user_id,))

   # ❌ 危險：字串拼接
   cursor.execute(f"SELECT * FROM meals WHERE user_id = '{user_id}'")
   ```

2. **MongoDB Injection 防護**：使用驗證

   ```python
   # ✅ 安全：驗證輸入
   if not isinstance(user_id, str) or not user_id:
       raise ValueError("Invalid user_id")

   meals_collection.find({"user_id": user_id})
   ```

3. **資料加密**（生產環境）：
   ```python
   # 加密敏感欄位
   from cryptography.fernet import Fernet
   cipher = Fernet(encryption_key)
   encrypted_data = cipher.encrypt(data.encode())
   ```

---

## �📚 開發指南

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
- [x] 🆕 圖像處理模組 (Azure Computer Vision 整合) - 階段 1
- [x] 🆕 圖像預處理功能 (OpenCV) - 階段 1
- [x] 🆕 食物識別與結果解析 - 階段 1
- [x] 🆕 營養計算模組 (TFND + USDA API) - 階段 2
- [x] 🆕 智能匹配算法 (精確/模糊匹配) - 階段 2
- [x] 🆕 熱量計算與統計 - 階段 2
- [x] 🆕 系統整合與 CLI 介面 - 階段 3
- [x] 🆕 快取機制實現 - 階段 3
- [x] 🆕 端到端整合測試 - 階段 3
- [x] ✨ SQLite 資料儲存模組 - 階段 4
- [x] ✨ CRUD 操作與歷史查詢 - 階段 4
- [x] ✨ 統計功能與資料匯出 - 階段 4
- [x] ✨ MongoDB 遷移文檔 - 階段 4
- [ ] Discord Bot 基礎功能
- [ ] Discord Bot 與資料庫整合

### Phase 2: 功能增強

- [ ] 用戶偏好設定
- [ ] 🆕 多語言食物名稱翻譯 (googletrans)
- [ ] 🆕 中英混用名稱處理
- [ ] 🆕 份量識別與計算
- [ ] 🆕 更多營養素查詢 (蛋白質、脂肪、碳水)
- [ ] 🆕 圖像增強和品質優化
- [ ] 🆕 USDA API 結果快取
- [ ] 圖表和統計功能
- [ ] 食物資料庫擴充

### Phase 3: 高級功能

- [ ] 機器學習模型訓練
- [ ] 🆕 批量圖像處理
- [ ] 🆕 圖像品質評估和自動校正
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
- **🆕 電腦視覺**: Azure Computer Vision API, OpenCV
- **🆕 圖像處理**: cv2, numpy, PIL (未來擴展)
- **AI/LLM**: Google Gemini API
- **資料庫**: SQLite (未來可遷移至 MongoDB)
- **API**: USDA FoodData Central API
- **測試**: pytest, unittest.mock
- **日誌**: Python logging, colorlog
- **配置**: python-dotenv

## 🔧 未來擴展計畫

### 圖像處理增強 (階段 2 預計功能)

1. **多 API 支援**:

   ```python
   # 預計支援的替代方案
   - Google Vision API fallback
   - AWS Rekognition 整合
   - 本地 YOLO/ResNet 模型
   ```

2. **圖像增強功能**:

   ```python
   # 計畫中的增強功能
   - 自動曝光和對比度調整
   - 圖像旋轉校正
   - 模糊檢測和銳化
   - 食物邊界檢測
   ```

3. **多語言支援**:
   ```python
   # 多語言食物識別
   - 中英日韓食物名稱對照
   - 地區性食物資料庫整合
   - 文化適應性調整
   ```

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

**版本**: 1.1.0 (MVP - 資料持久化完成)  
**最後更新**: 2024-10-28  
**開發團隊**: Food Nutritionist Team
