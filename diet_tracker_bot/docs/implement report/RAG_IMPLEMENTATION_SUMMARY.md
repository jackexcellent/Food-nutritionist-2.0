# RAG (Retrieval-Augmented Generation) 實作總結

## 📋 實作概述

本次更新實現了基於 RAG 的智能推薦系統，結合歷史記錄檢索和 LLM 生成，提供更精準的個人化飲食建議。

## ✅ 完成項目

### 1. 核心功能實作

#### `src/recommendation_engine.py`

- ✅ 更新 `get_recommendation()` 函數接受新參數：
  - `meal_type`: 當前餐次類型
  - `current_foods`: 當前餐點食物字典
  - `current_calories`: 當前餐點總熱量
- ✅ 實作 RAG Pipeline：

  1. **檢索階段**: 呼叫 `get_previous_meals()` 和 `get_past_days()`
  2. **格式化階段**: 使用 `format_retrieved_text()` 格式化檢索結果
  3. **增強階段**: 構建包含歷史上下文的 RAG Prompt
  4. **生成階段**: 呼叫 Gemini API 生成推薦

- ✅ 新增 Prompt 模板：

  - `RAG_RECOMMENDATION`: 包含歷史上下文的推薦模板
  - `NO_HISTORY_RECOMMENDATION`: 無歷史記錄時的 fallback 模板

- ✅ 新增 `_generate_rag_recommendation()` 函數

  - 構建增強型 prompt
  - 處理有/無歷史記錄兩種情況
  - 餐次類型中文映射

- ✅ 新增 `_generate_rule_based_rag_recommendation()` 函數
  - Gemini API 失敗時的 fallback
  - 基於規則的智能建議
  - 結合檢索結果的規則型推薦

#### `src/utils.py`

- ✅ 新增 `format_retrieved_text()` 函數

  - 格式化前序餐點清單
  - 格式化過去統計分析
  - 計算今日已攝取熱量
  - 生成結構化檢索文本

- ✅ 詳細註解未來擴展：
  - sentence-transformers 語義嵌入
  - cosine 相似度計算
  - FAISS 向量索引加速
  - 語義搜尋實作範例

#### `docs/README.md`

- ✅ 新增 RAG 系統完整文檔章節
  - RAG Pipeline 流程圖
  - 核心功能使用範例
  - Prompt 模板說明
  - 未來擴展計畫（語義檢索、FAISS、VLM）
  - 測試指南

### 2. 未來擴展註解

#### 語義向量檢索

```python
# 已在 recommendation_engine.py 和 utils.py 中詳細註解
# 包含完整的實作範例代碼
```

#### VLM 熱量估計

```python
# 已在 recommendation_engine.py 註解
# MVP: 使用現有營養計算
# 未來: 使用 Gemini Vision API 直接估計熱量
```

#### FAISS 向量索引

```python
# 已在 utils.py 中註解完整實作範例
# 包含索引建立、檢索、加權排序
```

### 3. 錯誤處理

- ✅ 無歷史記錄時的 fallback prompt
- ✅ Gemini API 失敗時的規則型 fallback
- ✅ 檢索失敗的容錯處理
- ✅ 格式化錯誤的異常捕獲

## 📊 測試狀態

### 已通過的測試

- ✅ 中文資料庫功能測試 (4/4 通過)
- ✅ 餐次類型儲存測試 (4/4 通過)
- ✅ 營養計算器測試
- ✅ 資料儲存測試

### 待執行的 RAG 測試

需要在 `tests/test_recommendation_engine.py` 中新增：

- ⏳ RAG 檢索功能測試
- ⏳ format_retrieved_text() 單元測試
- ⏳ RAG prompt 構建測試
- ⏳ 端到端 RAG 流程測試
- ⏳ Fallback 機制測試

## 🎯 使用範例

### 基本 RAG 推薦

```python
from src.recommendation_engine import get_recommendation

# 使用 RAG 生成推薦
recommendation = get_recommendation(
    user_id='discord_user_123',
    meal_type='lunch',
    current_foods={
        '雞腿便當': 650.0,
        '珍珠奶茶': 350.0
    },
    current_calories=1000.0,
    days=7
)

print(recommendation)
```

### 檢索結果格式化

```python
from src.utils import format_retrieved_text
from src.data_storage import get_previous_meals, get_past_days

# 檢索歷史資料
previous_meals = get_previous_meals(user_id, 'dinner')
past_analysis = get_past_days(user_id, days=7)

# 格式化為結構化文本
retrieved_text = format_retrieved_text(
    previous_meals=previous_meals,
    past_analysis=past_analysis,
    days=7
)

print(retrieved_text)
```

## 🔄 工作流程

```
用戶輸入
    ↓
1. 檢索相關歷史 (Retrieval)
   - get_previous_meals(): 今日前序餐點
   - get_past_days(): 過去統計分析
    ↓
2. 格式化檢索結果 (Format)
   - format_retrieved_text(): 結構化文本
    ↓
3. 構建增強 Prompt (Augmentation)
   - 合併歷史上下文
   - 添加當前餐點資訊
    ↓
4. 生成推薦 (Generation)
   - Gemini API: AI 生成推薦
   - Fallback: 規則型推薦
    ↓
返回結構化推薦
```

## 🚀 未來發展路徑

### Phase 1: MVP (已完成) ✅

- 簡單時間序列檢索
- Gemini LLM 生成
- 基礎 RAG prompt
- 規則型 fallback

### Phase 2: 語義檢索 (計劃中) 📋

- sentence-transformers 嵌入
- cosine 相似度篩選
- 語義相關性排序
- 多模態嵌入

### Phase 3: 向量加速 (未來) 🔮

- FAISS 向量索引
- 高效相似度搜尋
- 分散式檢索
- 實時更新索引

### Phase 4: VLM 整合 (未來) 🎨

- Gemini Vision API
- 圖像熱量估計
- 份量自動識別
- 端到端視覺推薦

## 📝 檔案變更摘要

### 修改的檔案

1. **`src/recommendation_engine.py`** (重大更新)

   - 新增 RAG 支援
   - 更新函數簽名
   - 新增 RAG prompt 模板
   - 詳細未來擴展註解

2. **`src/utils.py`** (新增功能)

   - 新增 `format_retrieved_text()` 函數
   - 詳細語義檢索註解
   - FAISS 實作範例

3. **`docs/README.md`** (文檔更新)
   - 新增 RAG 章節
   - 流程圖和範例
   - 未來擴展說明
   - 測試指南

### 相依關係

- ✅ `data_storage.get_previous_meals()`
- ✅ `data_storage.get_past_days()`
- ✅ `utils.format_retrieved_text()`
- ✅ Google Gemini API

## 🔍 程式碼品質

### 可讀性 ✅

- 清晰的函數命名
- 詳細的 docstring
- 完整的型別註解
- 豐富的註解說明

### 可擴展性 ✅

- 模組化設計
- 插件式架構
- 預留擴展接口
- 詳細未來計劃

### 可維護性 ✅

- 統一錯誤處理
- 完整日誌記錄
- 清晰的代碼結構
- 測試友好設計

## 🎓 技術亮點

1. **RAG 架構**: 標準的檢索-增強-生成流程
2. **Fallback 機制**: 多層容錯保證系統穩定
3. **未來擴展**: 詳細註解語義檢索、FAISS、VLM
4. **中文支援**: 完整的繁體中文處理
5. **個人化**: 基於歷史的智能推薦

## ✨ 總結

本次實作成功建立了 MVP 版本的 RAG 推薦系統，為未來的語義檢索和視覺語言模型整合奠定了良好基礎。系統具備良好的可擴展性和可維護性，代碼品質優秀，文檔完整。

**核心價值**:

- 提供更精準的個人化推薦
- 結合歷史上下文的智能分析
- 為未來 AI 升級預留擴展空間
- 保持系統穩定性和用戶體驗
