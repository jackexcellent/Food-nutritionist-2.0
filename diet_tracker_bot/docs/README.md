# Diet Tracker Discord Bot

一個基於人工智慧的 Discord 飲食追蹤機器人，提供食物識別、營養分析和個人化推薦功能。

## 📋 專案概述

這個機器人結合了電腦視覺、營養資料庫和 AI 技術，讓使用者可以通過上傳食物圖片來追蹤飲食，獲得詳細的營養分析和個人化建議。

### 🎯 主要功能 (MVP 版本)

- **🔍 食物識別**: 使用 Azure Computer Vision API 識別上傳的食物圖片
- **📊 營養分析**: 結合 USDA API 和台灣衛福部資料計算營養成分
- **💾 歷史記錄**: 儲存用戶的飲食歷史和偏好
- **🚀 餐次分類**: 智慧分類餐點 (早餐/午餐/晚餐/點心) 與份量追蹤
- **📈 趨勢分析**: 多日營養模式分析和前序餐點查詢
- **🤖 AI 推薦**: 使用 Google Gemini LLM 生成個人化飲食建議 (階段 5)
- **📱 Discord 整合**: 透過 Discord Bot 介面提供便利的用戶體驗
- **🔮 RAG 準備**: 為未來語義搜尋和向量檢索奠定基礎

### 🏗️ 系統架構

```
diet_tracker_bot/
├── src/                     # 核心程式碼
│   ├── __init__.py         # 套件初始化
│   ├── main.py             # 主程式入口點 (Discord Bot + CLI)
│   ├── discord_bot.py      # 🤖 Discord 機器人模組 (階段6)
│   ├── utils.py            # 共用工具函數 + 快取機制
│   ├── image_processor.py  # 圖像處理模組 (階段1)
│   ├── nutrition_calculator.py  # 營養計算模組 (階段2)
│   ├── data_storage.py     # 資料儲存模組 (階段4)
│   └── recommendation_engine.py  # ✨ AI 推薦引擎 (階段5)
├── config/                  # 配置檔案
│   └── .env                # 環境變數 (需要設定API金鑰)
├── data/                   # 資料檔案
│   ├── tfnd_clean.jsonl    # 台灣食物營養資料庫
│   ├── user_data.db        # SQLite 使用者資料庫 (階段4)
│   └── cache/              # 快取資料 (自動生成)
├── tests/                  # 測試檔案
│   ├── __init__.py
│   ├── test_image_processor.py      # 圖像處理測試 (階段1)
│   ├── test_nutrition_calculator.py # 營養計算測試 (階段2)
│   ├── test_integration.py          # 系統整合測試 (階段3)
│   ├── test_data_storage.py         # 資料儲存測試 (階段4)
│   ├── test_recommendation_engine.py # ✨ AI 推薦引擎測試 (階段5)
│   └── test_discord_bot.py          # 🤖 Discord Bot 測試 (階段6)
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
├── data_storage.py (SQLite 資料儲存 - 階段4)
├── recommendation_engine.py (✨ AI 推薦引擎 - 階段5)
├── bot/ (未來實現)
│   ├── discord_bot.py
│   └── commands.py
├── database/ (未來實現 - MongoDB)
│   ├── models.py
│   └── repository.py
└── ai/ (已整合到 recommendation_engine.py)
    └── advanced_analytics.py (未來擴展)
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

## 🧪 測試與驗證

### 統一測試執行器 (推薦)

使用專案提供的測試執行腳本，支援不同測試類型和選項：

```bash
# 🎯 快速測試 (開發時使用)
python run_tests.py --fast

# 📋 運行所有測試並生成覆蓋率
python run_tests.py --all --coverage --verbose

# 🧪 只運行單元測試
python run_tests.py --unit --verbose

# 🔗 只運行整合測試
python run_tests.py --integration --coverage

# 🎯 只運行端到端測試
python run_tests.py --e2e --verbose

# ⚡ 只運行性能測試
python run_tests.py --performance

# 📊 查看所有可用選項
python run_tests.py --help
```

### 直接使用 pytest

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

# 執行資料儲存測試 (階段4, 26項測試)
pytest tests/test_data_storage.py -v

# 🧠 執行 AI 推薦引擎測試 (階段5)
pytest tests/test_recommendation_engine.py -v

# 🤖 執行 Discord Bot 測試 (階段6)
pytest tests/test_discord_bot.py -v

# 🎯 執行端到端整合測試 (完整 MVP 流程)
pytest tests/test_end_to_end.py -v

# ⚡ 執行性能和壓力測試
pytest tests/test_performance.py -v
```

### 測試類型說明

#### 🧪 單元測試 (Unit Tests)

測試個別函數和類別的功能：

- `test_utils.py` - 工具函數測試
- `test_image_processor.py` - 圖像處理測試
- `test_nutrition_calculator.py` - 營養計算測試
- `test_data_storage.py` - 資料儲存測試
- `test_recommendation_engine.py` - AI 推薦引擎測試

#### 🔗 整合測試 (Integration Tests)

測試模組間的交互作用：

- `test_discord_bot.py` - Discord Bot 整合測試
- `test_main.py` - 主程式整合測試

#### 🎯 端到端測試 (E2E Tests)

測試完整的用戶流程：

- `test_end_to_end.py` - 完整 MVP 流程測試
- 多用戶並發測試
- 完整用戶旅程驗證
- 系統資源使用測試

#### ⚡ 性能測試 (Performance Tests)

測試系統性能和擴展性：

- `test_performance.py` - 性能基準測試
- 壓力測試和負載測試
- 記憶體洩漏檢測
- 資料庫性能驗證

### 測試標記 (Markers)

使用 pytest 標記來選擇特定類型的測試：

```bash
# 只運行快速測試
pytest -m "not slow"

# 只運行需要外部 API 的測試
pytest -m "external"

# 只運行資料庫相關測試
pytest -m "database"

# 跳過性能測試
pytest -m "not performance"

# 只運行 Mock 測試
pytest -m "mock"
```

### 覆蓋率報告

```bash
# 生成詳細覆蓋率報告
python run_tests.py --all --coverage

# 查看 HTML 覆蓋率報告
# 報告將生成在 test_reports/ 目錄中
```

### 測試配置

專案使用 `pytest.ini` 進行測試配置：

- 自動發現測試檔案
- 配置覆蓋率報告
- 設定測試標記
- 配置日誌輸出

### 持續整合 (CI)

測試腳本支援 CI/CD 環境：

```bash
# CI 環境中的自動化測試
python run_tests.py --all --coverage --no-report

# 檢查測試結果
echo $?  # 0=成功, 1=失敗
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

## 🧠 階段 5: AI 推薦引擎

### 功能概述

實現基於 Google Gemini LLM 的智能推薦系統，能夠分析用戶飲食歷史並生成個人化的健康建議。系統結合專業營養學知識與 AI 技術，提供結構化且實用的飲食指導。

### 核心功能 (`src/recommendation_engine.py`)

#### 1. 智能推薦生成

```python
from src.recommendation_engine import get_recommendation

# 生成基於歷史的個人化推薦
user_id = "discord_user_123"
recommendation = get_recommendation(user_id, days=7)

print(recommendation)
# 輸出結構化推薦...
```

#### 2. Gemini AI 整合

系統使用 Google Gemini 1.5 Flash 模型進行快速推薦生成：

```python
import google.generativeai as genai

# 自動初始化 (從 .env 載入 GEMINI_KEY)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 構建結構化 prompt
prompt = """
你是一位專業的營養師，請根據用戶的飲食歷史提供健康建議。

飲食歷史資料：
{history_json}

統計資訊：
- 總餐數：{total_meals}
- 平均熱量：{avg_calories:.1f} kcal
- 最常吃的食物：{common_foods}

請提供結構化的分析和建議...
"""

response = model.generate_content(prompt)
```

### 推薦流程圖

```
┌──────────────┐
│  用戶請求推薦  │
│   user_id    │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│ 1. 資料收集 (data_storage)          │
├─────────────────────────────────────┤
│ • get_history(user_id, days=7)      │
│ • get_statistics(user_id, days=7)   │
│ • 格式化為結構化 JSON               │
└──────────────┬──────────────────────┘
               │ 飲食歷史 + 統計資訊
               ▼
┌─────────────────────────────────────┐
│ 2. Prompt 構建 (PromptTemplates)    │
├─────────────────────────────────────┤
│ • 基礎推薦模板 (MVP)                │
│ • 結構化輸出格式                    │
│ • 營養學專業指導                    │
│ • 個人化資料嵌入                    │
└──────────────┬──────────────────────┘
               │ 結構化 Prompt
               ▼
┌─────────────────────────────────────┐
│ 3. AI 推薦生成 (Gemini API)         │
├─────────────────────────────────────┤
│ Primary: Google Gemini 1.5 Flash    │
│ • model.generate_content(prompt)     │
│ • 回應驗證與品質檢查                │
│                                     │
│ Fallback: 規則型推薦引擎             │
│ • 熱量分析 (高/低/適中)             │
│ • 飲食頻率評估                      │
│ • 食物多樣性檢查                    │
└──────────────┬──────────────────────┘
               │ 結構化推薦內容
               ▼
┌─────────────────────────────────────┐
│ 4. 推薦結果輸出                     │
├─────────────────────────────────────┤
│ 🔍 **飲食分析**                     │
│ 💡 **健康建議** (3-5項具體建議)     │
│ 🍎 **推薦食物** (營養價值說明)      │
│ ⚠️ **注意事項** (個人化提醒)        │
└─────────────────────────────────────┘
```

### Prompt 模板設計

#### 基礎推薦模板 (MVP)

```python
class PromptTemplates:
    BASIC_RECOMMENDATION = """
你是一位專業的營養師，請根據用戶的飲食歷史提供健康建議。

飲食歷史資料：
{history_json}

統計資訊：
- 總餐數：{total_meals}
- 平均熱量：{avg_calories:.1f} kcal
- 最常吃的食物：{common_foods}

請提供結構化的分析和建議，格式如下：

🔍 **飲食分析**：
[分析用戶的飲食模式、熱量攝取、食物多樣性等]

💡 **健康建議**：
[提供3-5個具體的改善建議]

🍎 **推薦食物**：
[推薦3-5種適合的食物，說明營養價值]

⚠️ **注意事項**：
[提醒需要注意的飲食習慣]

請用繁體中文回答，建議要實用且易於執行。
"""
```

#### 推薦輸出範例

```
🔍 **飲食分析**：
根據您最近7天的飲食記錄，平均每餐熱量為 245 kcal，整體熱量適中。
您常食用蛋白質豐富的食物如雞肉和魚類，但蔬菜攝取略顯不足。

💡 **健康建議**：
1. 增加綠色蔬菜攝取，建議每餐至少包含一份蔬菜
2. 保持優質蛋白質來源的多樣性，可添加豆類製品
3. 適量增加全穀類食物，提供穩定的能量來源
4. 控制加工食品攝取，優先選擇原型食物

🍎 **推薦食物**：
- 深綠色蔬菜：菠菜、花椰菜 (提供豐富維生素K和葉酸)
- 豆類製品：豆腐、黑豆 (植物性蛋白質和纖維)
- 全穀類：糙米、燕麥 (複合碳水化合物和B群維生素)

⚠️ **注意事項**：
保持規律用餐時間，避免長時間空腹。如有特殊健康狀況，建議諮詢專業營養師。
```

### Fallback 機制

當 Gemini API 不可用時，系統自動切換到規則型推薦：

```python
def _generate_rule_based_recommendation(history_data, stats, days):
    """規則型推薦 (Fallback)"""

    # 熱量分析
    if avg_calories > 600:
        analysis_notes.append("您的平均熱量偏高，建議適量減少高熱量食物")
    elif avg_calories < 300:
        analysis_notes.append("您的平均熱量偏低，建議增加營養豐富的食物")

    # 飲食頻率分析
    meals_per_day = total_meals / days
    if meals_per_day < 2:
        analysis_notes.append("建議增加用餐頻率，保持規律飲食")

    # 食物多樣性分析
    unique_foods = len(set([food for food, _ in common_foods]))
    if unique_foods < 5:
        analysis_notes.append("建議增加食物種類，提升營養多樣性")

    return formatted_recommendation
```

### API 配置與環境設定

在 `config/.env` 中添加 Gemini API 金鑰：

```bash
# Google Gemini API 配置
GEMINI_KEY=your_google_gemini_api_key_here

# 其他已有的 API 配置...
AZURE_KEY=your_azure_key_here
USDA_KEY=your_usda_key_here
```

### 測試 (`tests/test_recommendation_engine.py`)

完整的推薦引擎測試涵蓋：

```bash
# 運行所有推薦引擎測試
pytest tests/test_recommendation_engine.py -v

# 測試類別分類
pytest tests/test_recommendation_engine.py::TestGeminiApiIntegration -v    # Gemini API 測試
pytest tests/test_recommendation_engine.py::TestRuleBasedFallback -v       # Fallback 機制測試
pytest tests/test_recommendation_engine.py::TestPromptTemplates -v         # Prompt 模板測試
```

**測試涵蓋範圍：**

- ✅ Gemini API 整合與 mock 測試
- ✅ Prompt 模板格式化與驗證
- ✅ Fallback 機制（規則型推薦）
- ✅ 資料格式化與結構驗證
- ✅ 錯誤處理與容錯機制
- ✅ 參數驗證與邊界條件
- ✅ 效能測試（大量歷史資料）
- ✅ 完整工作流程整合測試

---

## 🚀 餐次分類與智慧分析功能 (已完成)

**擴展資料庫架構，實現餐次類型分類、份量追蹤和時序分析功能。**

### 核心功能特色

#### 1. 🍽️ 餐次類型分類

智慧分類使用者的餐點記錄，支援精確的營養追蹤和分析：

- **`breakfast`** - 早餐
- **`lunch`** - 午餐
- **`dinner`** - 晚餐
- **`snack`** - 點心/零食
- **`meal`** - 一般餐點 (預設)

#### 2. ⚖️ 份量大小追蹤

精確記錄每餐的份量，提供更準確的營養計算：

- 預設份量：100g
- 支援自訂份量 (0.1g - 10000g)
- 自動份量單位換算
- 歷史份量趨勢分析

#### 3. 🧠 前序餐點智慧查詢

動態查詢當日已攝取的餐點，支援智慧營養規劃：

```python
# 晚餐前查看已吃的早餐和午餐
previous_meals = get_previous_meals(user_id, "dinner")
total_calories = sum(meal[3] for meal in previous_meals)
remaining_target = 2000 - total_calories  # 計算剩餘熱量需求
```

#### 4. 📊 多日營養趨勢分析

深度分析使用者的飲食模式和營養趨勢：

```python
# 分析過去 7 天的飲食模式
analysis = get_past_days(user_id, days=7)
print(f"平均每日熱量: {analysis['nutrition_trends']['avg_daily_calories']} kcal")
print(f"餐次分布: {analysis['meal_type_stats']}")
print(f"個性化建議: {analysis['recommendations']}")
```

### 資料庫架構升級

#### 新增欄位

```sql
-- 餐次類型欄位 (向後相容遷移)
ALTER TABLE meals ADD COLUMN meal_type TEXT DEFAULT 'meal';

-- 份量大小欄位 (向後相容遷移)
ALTER TABLE meals ADD COLUMN portion_size REAL DEFAULT 100.0;

-- 新增索引優化查詢效能
CREATE INDEX idx_meals_meal_type ON meals(meal_type);
CREATE INDEX idx_meals_user_type_date ON meals(user_id, meal_type, date DESC);
```

#### 完整資料表結構

```sql
CREATE TABLE meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    date TEXT NOT NULL,
    foods TEXT NOT NULL,           -- JSON 格式食物清單
    calories REAL NOT NULL,
    meal_type TEXT DEFAULT 'meal', -- 🚀 餐次類型
    portion_size REAL DEFAULT 100.0, -- 🚀 份量大小 (g)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### API 使用範例

#### 儲存餐點 (擴展版)

```python
from src.data_storage import store_meal

# 基本用法 (向後相容)
record_id = store_meal(
    user_id="user_123",
    foods={"蘋果": 52.0, "香蕉": 89.0},
    calories=141.0
)

# 新功能：指定餐次和份量
record_id = store_meal(
    user_id="user_123",
    foods={"燕麥片": 150.0, "牛奶": 60.0},
    calories=210.0,
    meal_type="breakfast",    # 🚀 餐次類型
    portion_size=200.0       # 🚀 份量 200g
)
```

#### 前序餐點查詢

```python
from src.data_storage import get_previous_meals

# 晚餐前查看今日已吃的餐點
previous_meals = get_previous_meals("user_123", "dinner")

for meal_id, date, foods, calories, portion_size, meal_type in previous_meals:
    print(f"{meal_type.upper()}: {calories} kcal ({portion_size}g)")
    for food, cal in foods.items():
        print(f"  - {food}: {cal} kcal")

# 輸出範例:
# BREAKFAST: 210.0 kcal (200.0g)
#   - 燕麥片: 150.0 kcal
#   - 牛奶: 60.0 kcal
# LUNCH: 335.0 kcal (300.0g)
#   - 雞胸肉: 200.0 kcal
#   - 糙米飯: 110.0 kcal
#   - 花椰菜: 25.0 kcal
```

#### 多日趨勢分析

```python
from src.data_storage import get_past_days

# 分析過去 3 天飲食
analysis = get_past_days("user_123", days=3)

# 每日摘要
for day in analysis['daily_summaries']:
    print(f"📅 {day['date']}: {day['total_calories']} kcal")
    for meal_type, count in day['meal_types'].items():
        if count > 0:
            print(f"   - {meal_type}: {count} 次")

# 營養趨勢
trends = analysis['nutrition_trends']
print(f"\n📊 平均每日熱量: {trends['avg_daily_calories']:.1f} kcal")
print(f"📊 最高單日熱量: {trends['max_daily_calories']:.1f} kcal")
print(f"📊 熱量變異度: {trends['calorie_variance']:.1f}")

# 餐次分布統計
meal_stats = analysis['meal_type_stats']
print(f"\n🍽️ 餐次分布 (總計 {analysis['total_meals']} 餐):")
for meal_type, percentage in meal_stats.items():
    print(f"   {meal_type}: {percentage:.1f}%")

# 個性化建議
print(f"\n💡 智慧營養建議:")
for i, rec in enumerate(analysis['recommendations'], 1):
    print(f"   {i}. {rec}")
```

### 🔮 未來 RAG 向量檢索擴展

當前架構已為進階 AI 功能奠定基礎：

#### 預留擴展欄位

```sql
-- 未來擴展欄位 (規劃中)
ALTER TABLE meals ADD COLUMN meal_description TEXT;    -- 餐點描述文字
ALTER TABLE meals ADD COLUMN embedding_vector BLOB;   -- 向量嵌入
ALTER TABLE meals ADD COLUMN nutrition_tags TEXT;     -- 營養標籤 JSON
```

#### 語義相似檢索 (規劃)

```python
# 🔮 未來功能預覽
from sentence_transformers import SentenceTransformer
import pinecone

def store_meal_with_embedding(user_id, foods, calories, meal_description=None):
    """儲存餐點 + 向量嵌入"""

    # 1. 儲存結構化資料
    record_id = store_meal(user_id, foods, calories)

    # 2. 生成語義嵌入
    if meal_description:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode(meal_description)

        # 3. 儲存到向量資料庫
        index = pinecone.Index("meal-embeddings")
        index.upsert([(str(record_id), embedding.tolist(), {
            'user_id': user_id,
            'calories': calories,
            'meal_type': meal_type
        })])

    return record_id

def find_similar_meals(query_text, user_id, top_k=5):
    """語義相似餐點檢索"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode(query_text)

    # 向量檢索
    index = pinecone.Index("meal-embeddings")
    results = index.query(
        vector=query_embedding.tolist(),
        filter={'user_id': user_id},
        top_k=top_k,
        include_metadata=True
    )

    return results['matches']

# 使用範例:
# similar_meals = find_similar_meals("健康的早餐", "user_123")
# for match in similar_meals:
#     print(f"相似度: {match['score']:.3f}")
#     print(f"熱量: {match['metadata']['calories']} kcal")
```

#### AI 驅動營養規劃 (規劃)

```python
# 🔮 未來整合 LLM + 向量檢索
def generate_ai_meal_plan(user_id, target_calories, dietary_preferences):
    """AI 驅動的個性化餐點規劃"""

    # 1. 獲取用戶歷史偏好
    user_history = get_past_days(user_id, days=30)

    # 2. 向量檢索相似成功案例
    similar_patterns = find_successful_nutrition_patterns(
        target_calories, dietary_preferences
    )

    # 3. LLM 生成個性化計畫
    meal_plan = generate_personalized_meal_plan(
        user_history=user_history,
        similar_patterns=similar_patterns,
        target_calories=target_calories,
        preferences=dietary_preferences
    )

    return meal_plan
```

### 測試覆蓋

新功能包含完整的測試套件：

```bash
# 執行餐次功能測試
python -m pytest tests/test_data_storage.py::TestMealTypeFeatures -v
python -m pytest tests/test_data_storage.py::TestPreviousMeals -v
python -m pytest tests/test_data_storage.py::TestPastDaysAnalysis -v
python -m pytest tests/test_data_storage.py::TestDatabaseMigration -v

# 演示新功能
python demo_meal_types.py
```

### 向後相容性保證

- ✅ 現有 API 完全向下相容
- ✅ 自動資料庫遷移 (零停機)
- ✅ 預設值處理 (meal_type='meal', portion_size=100.0)
- ✅ 現有測試和功能無影響
- ✅ 漸進式功能升級

---

## 🤖 階段 6: Discord Bot 整合 (MVP 完成)

**整合所有系統組件，提供完整的 Discord 機器人用戶體驗。**

### Discord Bot 架構

```
Discord Bot Integration Flow
───────────────────────────────

👤 用戶上傳食物圖片 + /track
          │
          ▼
┌─────────────────────────────────┐
│ Discord Bot (discord_bot.py)    │
├─────────────────────────────────┤
│ • 附件驗證 (圖片格式/大小)      │
│ • 臨時檔案管理                  │
│ • 用戶 ID 管理 (ctx.author.id)  │
│ • 進度訊息更新                  │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ 完整 MVP Pipeline               │
├─────────────────────────────────┤
│ 1. image_processor.process_image │
│ 2. nutrition_calculator.get_nutrition │
│ 3. data_storage.store_meal      │
│ 4. recommendation_engine.get_recommendation │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│ 結構化回應 (Discord Embed)       │
├─────────────────────────────────┤
│ ✅ 飲食分析完成                 │
│ 🔍 識別結果: 蘋果、香蕉         │
│ 📊 營養分析: [詳細營養資訊]     │
│ 🔥 總熱量: 141 kcal            │
│ 🤖 AI 個人化建議: [3項建議]     │
│ 📝 記錄 ID: #1001              │
└─────────────────────────────────┘
```

### 核心功能實現

#### 1. Discord Bot 初始化 (`src/discord_bot.py`)

```python
import discord
from discord.ext import commands

class DietTrackerBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # 需要讀取訊息內容

        super().__init__(
            command_prefix='/',
            intents=intents,
            help_command=None
        )

        self.stats = {
            'total_tracks': 0,
            'successful_analyses': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    async def on_ready(self):
        print(f'✅ 機器人已上線: {self.user}')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="你的飲食健康 | /track 開始追蹤"
            )
        )
```

#### 2. /track 命令實現

```python
@bot.command(name='track')
async def track_food(ctx: commands.Context):
    """MVP 核心功能 - 食物圖片追蹤"""

    # 1. 驗證附件
    if not ctx.message.attachments:
        await ctx.send("📷 請上傳食物圖片來開始分析！")
        return

    # 2. 檔案驗證
    attachment = ctx.message.attachments[0]
    if not _is_valid_image_file(attachment.filename):
        await ctx.send("❌ 請上傳有效的圖片檔案 (jpg, png, etc.)")
        return

    # 3. 進度追蹤
    processing_msg = await ctx.send("🔄 正在分析您的食物圖片...")

    try:
        # 4. 完整 Pipeline 執行
        user_id = str(ctx.author.id)

        # 步驟 1: 食物識別
        await processing_msg.edit(content="🔄 步驟 1/4: 識別食物中...")
        foods = image_processor.process_image(temp_path)

        # 步驟 2: 營養分析
        await processing_msg.edit(content="🔄 步驟 2/4: 計算營養成分...")
        nutrition_data = nutrition_calculator.get_nutrition(foods)

        # 步驟 3: 儲存記錄
        await processing_msg.edit(content="🔄 步驟 3/4: 儲存飲食記錄...")
        meal_id = data_storage.store_meal(user_id, food_dict, total_calories)

        # 步驟 4: AI 推薦
        await processing_msg.edit(content="🔄 步驟 4/4: 生成個人化建議...")
        recommendation = recommendation_engine.get_recommendation(user_id)

        # 5. 格式化並發送結果
        response = _format_track_response(foods, nutrition_data, total_calories, recommendation, meal_id)
        await processing_msg.edit(content=response)

    except Exception as e:
        await processing_msg.edit(content="❌ 處理過程中發生錯誤，請稍後再試。")
```

#### 3. 回應格式化

```python
def _format_track_response(foods, nutrition_data, total_calories, recommendation, meal_id):
    """格式化追蹤結果為用戶友好的訊息"""

    food_list = "、".join(foods) if foods else "未識別"

    # 營養詳情
    nutrition_details = []
    for food_name, data in nutrition_data.items():
        calories = data.get('calories', 0)
        protein = data.get('protein', 0)
        carbs = data.get('carbs', 0)
        fat = data.get('fat', 0)

        nutrition_details.append(
            f"• **{food_name}**: {calories:.0f} kcal "
            f"(蛋白質 {protein:.1f}g, 碳水 {carbs:.1f}g, 脂肪 {fat:.1f}g)"
        )

    # AI 推薦摘要
    recommendation_summary = _extract_recommendation_summary(recommendation)

    return f"""✅ **飲食分析完成！**

🔍 **識別結果**: {food_list}

📊 **營養分析**:
{chr(10).join(nutrition_details)}

🔥 **總熱量**: {total_calories:.0f} kcal

🤖 **AI 個人化建議**:
{recommendation_summary}

📝 **記錄 ID**: #{meal_id} | 使用 `/history` 查看完整記錄"""
```

### Discord Bot 設定指南

#### 1. 建立 Discord Bot

1. **前往 Discord Developer Portal**:

   - 訪問 https://discord.com/developers/applications
   - 登入您的 Discord 帳號

2. **建立新應用程式**:

   ```
   → 點擊 "New Application"
   → 輸入機器人名稱: "Diet Tracker Bot"
   → 點擊 "Create"
   ```

3. **設定機器人**:

   ```
   → 左側選單點擊 "Bot"
   → 點擊 "Add Bot"
   → 確認 "Yes, do it!"
   ```

4. **獲取 Bot Token**:

   ```
   → 在 Bot 頁面點擊 "Copy" 複製 Token
   → 將 Token 添加到 config/.env 文件中:
     DISCORD_TOKEN=your_bot_token_here
   ```

5. **設定機器人權限**:
   ```
   必要權限:
   ✅ Read Messages          (讀取訊息)
   ✅ Send Messages          (發送訊息)
   ✅ Read Message History   (讀取訊息歷史)
   ✅ Attach Files          (附加檔案)
   ✅ Use Slash Commands    (使用斜線命令，未來功能)
   ```

#### 2. 邀請機器人到伺服器

1. **生成邀請連結**:

   ```
   → Developer Portal → OAuth2 → URL Generator
   → Scopes: 選擇 "bot"
   → Bot Permissions: 選擇上述必要權限
   → 複製生成的 URL
   ```

2. **邀請步驟**:
   ```
   → 開啟邀請連結
   → 選擇要邀請的伺服器
   → 確認權限設定
   → 點擊 "Authorize" 授權
   ```

### 本地運行指南

#### 1. Discord Bot 模式 (預設)

```bash
# 啟動完整的 Discord 機器人
python src/main.py

# 或者使用模組執行
python -m src.main

# 機器人將顯示以下資訊:
# 🤖 啟動 Discord 飲食追蹤機器人...
# 📝 使用 /track 命令開始追蹤飲食
# 🔗 邀請機器人到您的伺服器並開始使用！
# ⚠️  按 Ctrl+C 停止機器人
```

#### 2. CLI 測試模式

```bash
# 使用 CLI 模式測試功能
python src/main.py --cli --image path/to/food_image.jpg

# CLI 模式參數
python src/main.py --cli --image test.jpg --user test_user --debug
```

#### 3. 使用 Discord Bot

1. **在 Discord 伺服器中**:

   ```
   /track  # 輸入命令
   [上傳食物圖片]  # 同時上傳圖片
   ```

2. **機器人回應流程**:
   ```
   🔄 正在分析您的食物圖片...
   🔄 步驟 1/4: 識別食物中...
   🔄 步驟 2/4: 計算營養成分...
   🔄 步驟 3/4: 儲存飲食記錄...
   🔄 步驟 4/4: 生成個人化建議...
   ✅ 飲食分析完成！ [詳細結果]
   ```

### 測試 (`tests/test_discord_bot.py`)

完整的 Discord Bot 測試涵蓋：

```bash
# 運行所有 Discord Bot 測試
pytest tests/test_discord_bot.py -v

# 測試分類運行
pytest tests/test_discord_bot.py::TestTrackCommand -v          # /track 命令測試
pytest tests/test_discord_bot.py::TestDietTrackerBot -v       # 機器人核心測試
pytest tests/test_discord_bot.py::TestUtilityFunctions -v     # 輔助函數測試
pytest tests/test_discord_bot.py::TestIntegration -v          # 整合測試
```

**測試涵蓋範圍：**

- ✅ 機器人初始化與配置測試
- ✅ /track 命令完整流程測試
- ✅ 圖片附件處理與驗證
- ✅ 錯誤處理與用戶反饋
- ✅ 統計功能與管理命令
- ✅ 輔助函數與格式化
- ✅ Mock 整合測試 (避免真實 Discord API)
- ✅ 異常處理與容錯機制

#### 未來擴展命令架構

```python
# 預留的未來命令 (架構已準備)

@bot.command(name='history')
async def view_history(ctx, days: int = 7):
    """查看飲食歷史記錄"""
    # 實現將在後續版本添加

@bot.command(name='stats')
async def nutrition_stats(ctx):
    """營養統計報告"""
    # 實現將在後續版本添加

@bot.command(name='profile')
async def user_profile(ctx):
    """個人檔案設定"""
    # 實現將在後續版本添加
```

**MVP Discord Bot 已完成！** 🎉

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
- [x] 🧠 AI 推薦引擎 (Gemini LLM) - 階段 5
- [x] 🧠 結構化 Prompt 模板 - 階段 5
- [x] 🧠 規則型 Fallback 機制 - 階段 5
- [x] 🤖 Discord Bot 核心功能 - 階段 6
- [x] 🤖 /track 命令整合 - 階段 6
- [x] 🤖 圖片附件處理 - 階段 6
- [x] 🤖 錯誤處理與用戶反饋 - 階段 6

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

**版本**: 1.2.0 (MVP - AI 推薦引擎完成)  
**最後更新**: 2024-11-07  
**開發團隊**: Food Nutritionist Team
