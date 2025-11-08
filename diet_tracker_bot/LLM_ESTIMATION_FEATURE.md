# LLM 熱量估算功能

## 功能說明

當 USDA 和 TFND 資料庫都找不到食物的熱量資訊時，系統會自動使用 Google Gemini LLM 來估算熱量。

## 工作流程

1. **優先查詢 TFND（台灣食品營養成分資料庫）**

   - 精確匹配食物名稱
   - 模糊匹配（相似度 > 80%）

2. **Fallback 到 USDA FoodData Central API**

   - 使用英文食物名稱查詢
   - 獲取國際食品資料

3. **LLM 估算（最後手段）** ⭐ **新功能**

   - 使用 Google Gemini 2.0 Flash
   - 基於營養學知識估算熱量
   - 返回每 100g 的 kcal 值

4. **無法估算**
   - 如果 LLM 也無法估算（回傳 0）
   - 該食物不會顯示任何熱量數字
   - 用戶會看到警告訊息

## 配置要求

確保在 `.env` 檔案中設置了 Gemini API Key：

```bash
GEMINI_KEY=your_gemini_api_key_here
```

## 安裝依賴

```bash
pip install google-generativeai
```

## LLM 估算的特點

### ✅ 優點

- 可以處理創意料理、地方特色食物
- 基於大量營養學訓練數據
- 快速回應（使用 Flash 模型）

### ⚠️ 限制

- 估算值可能不如資料庫精確
- 對於虛構或無意義的食物會返回 0
- 需要網路連接和 API 配額

## 熱量合理性檢查

系統會驗證 LLM 估算的熱量是否合理：

- 必須 > 0 kcal
- 必須 ≤ 900 kcal/100g
- 超出範圍的值會被拒絕

## 日誌記錄

系統會記錄每個查詢的來源：

```
✅ apple: 52.0 kcal (來源: TFND)
✅ sushi: 143.0 kcal (來源: USDA)
✅ dragon fruit cake: 285.0 kcal (來源: LLM估算)
⚠️ xyzabc: 無法從任何來源獲取熱量資訊，已跳過
```

## 測試

執行測試腳本：

```bash
python test_llm_estimation.py
```

## 範例輸出

### 部分食物找到資訊

```
識別的食物: apple, mystery food, rice

✅ 找到熱量資訊:
  • apple: 52.0 kcal (TFND)
  • rice: 130.0 kcal (TFND)

總熱量: 182 kcal

註：mystery food 無法獲取熱量資訊
```

### 全部食物都找不到

```
❌ 無法獲取熱量資訊

識別的食物: xyzabc, qwerty

這些食物在資料庫（TFND、USDA）和AI估算中都找不到熱量資訊。
請嘗試：
• 使用更具體的食物名稱
• 拍攝更清晰的照片
• 確保照片中食物清晰可見
```

## 技術實現

### 修改的檔案

1. **src/nutrition_calculator.py**

   - 新增 `_estimate_calories_with_llm()` 方法
   - 修改 `get_nutrition()` 流程，增加 LLM fallback
   - 只有找到有效熱量才加入結果字典

2. **src/discord_bot.py**
   - 新增檢查：當 `nutrition_data` 為空時顯示錯誤訊息
   - 改進用戶體驗，給出明確的失敗提示

### Prompt 工程

LLM 使用的 prompt 設計重點：

- 明確要求只回答數字
- 提供範例引導格式
- 強調不確定時返回 0
- 指定單位為 kcal/100g

## 效能考量

- **快取機制**: LLM 估算結果會被快取，避免重複查詢
- **模型選擇**: 使用 Gemini 2.0 Flash（快速版本）
- **超時處理**: API 呼叫有錯誤處理機制

## 未來改進

- [ ] 支援中文食物名稱的 LLM 估算
- [ ] 增加信心度指標（high/medium/low confidence）
- [ ] 允許用戶手動修正 LLM 估算值
- [ ] 建立 LLM 估算值的品質回饋機制
