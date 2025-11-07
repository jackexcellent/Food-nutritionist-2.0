# user_data.db 資料庫查看指南

## 方法 1: 使用我提供的 Python 腳本

```bash
python view_database.py
```

## 方法 2: 使用 SQLite 命令列工具

### 進入 SQLite 互動模式

```bash
sqlite3 data/user_data.db
```

### 常用 SQLite 命令

#### 1. 查看所有表格

```sql
.tables
```

#### 2. 查看表格結構

```sql
.schema meals
```

#### 3. 設定更好的顯示格式

```sql
.mode column
.headers on
.width 5 15 25 50 10 20
```

#### 4. 查看所有記錄

```sql
SELECT * FROM meals;
```

#### 5. 查看最近 5 筆記錄

```sql
SELECT id, user_id, date, calories, created_at
FROM meals
ORDER BY date DESC
LIMIT 5;
```

#### 6. 查看特定用戶的記錄

```sql
SELECT * FROM meals WHERE user_id = 'test_user_123';
```

#### 7. 統計資訊查詢

```sql
-- 總記錄數
SELECT COUNT(*) as total_records FROM meals;

-- 每個用戶的記錄數
SELECT user_id, COUNT(*) as meal_count, SUM(calories) as total_calories
FROM meals
GROUP BY user_id;

-- 平均熱量
SELECT AVG(calories) as avg_calories FROM meals;
```

#### 8. 日期範圍查詢

```sql
-- 最近 7 天的記錄
SELECT * FROM meals
WHERE date >= datetime('now', '-7 days')
ORDER BY date DESC;
```

#### 9. 查看食物詳細內容（JSON 格式）

```sql
SELECT id, user_id, date, foods, calories
FROM meals
ORDER BY date DESC;
```

#### 10. 離開 SQLite

```sql
.quit
```

## 方法 3: 使用 VS Code 擴充功能

1. 安裝 SQLite Viewer 擴充功能
2. 在 VS Code 中開啟 `data/user_data.db` 檔案
3. 可視化瀏覽資料庫內容

## 方法 4: 使用 Python 程式碼直接查詢

```python
import sqlite3
import json
from pathlib import Path

# 連接資料庫
db_path = Path("data/user_data.db")
with sqlite3.connect(str(db_path)) as conn:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 查詢所有記錄
    cursor.execute("SELECT * FROM meals ORDER BY date DESC")
    records = cursor.fetchall()

    for record in records:
        print(f"ID: {record['id']}")
        print(f"用戶: {record['user_id']}")
        print(f"日期: {record['date']}")
        print(f"熱量: {record['calories']} kcal")

        # 解析食物 JSON
        foods = json.loads(record['foods'])
        print("食物:")
        for food, cal in foods.items():
            print(f"  - {food}: {cal} kcal")
        print("-" * 40)
```

## 資料庫結構說明

### meals 表格欄位

- `id`: 記錄的唯一識別碼（自動遞增）
- `user_id`: 用戶識別碼（通常是 Discord ID 或其他平台的用戶 ID）
- `date`: 記錄建立的日期時間（ISO 8601 格式）
- `foods`: 食物清單（JSON 格式儲存，包含食物名稱和熱量）
- `calories`: 該餐的總熱量
- `created_at`: 資料庫記錄的建立時間

### 範例資料

```
ID: 2
用戶: test_user_123
日期: 2025-11-06T00:19:09.640127
熱量: 188.0 kcal
食物:
  - apple: 52.0 kcal
  - banana: 89.0 kcal
  - orange: 47.0 kcal
```

# 🥗 Diet Tracker Bot - 整合使用指南

## 📋 整合狀況

✅ **已完成整合**: `main.py` 現在已經連接到 `data_storage.py`

### 🆕 新功能

1. **自動儲存記錄**: 提供用戶 ID 時會自動儲存到資料庫
2. **歷史記錄查詢**: 可查看用戶的飲食歷史
3. **統計資訊**: 顯示用戶的飲食統計

## 🚀 使用方法

### 1. 基本圖像處理 (不儲存)

```bash
python src/main.py --image path/to/image.jpg
```

### 2. 圖像處理 + 儲存記錄

```bash
python src/main.py --image path/to/image.jpg --user your_user_id
```

### 3. 查看歷史記錄

```bash
# 查看最近 7 天
python src/main.py --user your_user_id --history

# 查看最近 30 天
python src/main.py --user your_user_id --history --days 30
```

### 4. 除錯模式

```bash
python src/main.py --image path/to/image.jpg --user your_user_id --debug
```

## 📊 範例輸出

### 圖像處理 + 儲存

```
============================================================
Diet Tracker Bot - CLI 模式
飲食追蹤機器人 - 圖像到熱量計算
============================================================
============================================================
階段 1: 圖像處理與食物識別
============================================================
📸 載入圖像: apple.jpg
🔍 使用 Azure Computer Vision 識別食物...
✅ 成功識別 1 種食物
   食物清單: apple

============================================================
階段 2: 營養計算與熱量統計
============================================================
📊 查詢營養資料...
✅ 營養計算完成

============================================================
階段 3: 儲存飲食記錄
============================================================
💾 儲存記錄到資料庫: 用戶 john_doe
✅ 記錄已儲存: ID=3

============================================================
📋 處理結果摘要
============================================================
🍽️  識別的食物清單 (1 項):
   1. apple

🔥 營養資訊 (每 100g):
   ✅ apple           :   52.0 kcal

📊 總熱量: 52.0 kcal
💾 記錄已儲存: ID=3 (用戶: john_doe)
============================================================

📊 統計資訊 (最近 7 天):
========================================
   總餐數: 1
   總熱量: 52.0 kcal
   平均每餐: 52.0 kcal

✅ 處理完成！
```

### 歷史記錄查詢

```
============================================================
📋 用戶歷史記錄: test_user_123 (最近 7 天)
============================================================
📊 找到 1 筆記錄:

📝 記錄 #1 (ID: 2)
   📅 日期: 2025-11-06T00:19:09.640127
   🔥 總熱量: 188.0 kcal
   🍽️  食物:
      • apple: 52.0 kcal
      • banana: 89.0 kcal
      • orange: 47.0 kcal
   ⏰ 記錄時間: 2025-11-05 16:19:09

📊 統計資訊 (最近 7 天):
========================================
   總餐數: 1
   總熱量: 188.0 kcal
   平均每餐: 188.0 kcal

🏆 最常吃的食物:
      • apple: 1 次
      • banana: 1 次
      • orange: 1 次
```

## 🔧 技術細節

### 資料流程

1. **圖像輸入** → Azure Computer Vision API
2. **食物識別** → 英文食物名稱清單
3. **營養查詢** → TFND 資料庫 + USDA API
4. **記錄儲存** → SQLite 資料庫 (如果提供用戶 ID)
5. **結果顯示** → 格式化輸出

### 資料庫結構

- **表格**: `meals`
- **欄位**:
  - `id`: 記錄 ID (自動遞增)
  - `user_id`: 用戶識別碼
  - `date`: 記錄日期時間
  - `foods`: JSON 格式食物清單
  - `calories`: 總熱量
  - `created_at`: 建立時間

### 用戶 ID 格式

- 可以是任何字串格式
- 建議使用: Discord ID、Email、用戶名稱等
- 範例: `discord_123456789`, `john.doe@email.com`, `user_001`

## 🎯 下一步發展

### Discord Bot 整合

這個 CLI 版本為未來的 Discord Bot 提供了完整的後端功能：

1. **Discord Bot 命令**:

   - `/track <image>` - 上傳圖像追蹤飲食
   - `/history [days]` - 查看歷史記錄
   - `/stats [days]` - 查看統計資訊

2. **技術架構**:
   - Discord.py 處理 Bot 介面
   - 重用現有的圖像處理和資料儲存邏輯
   - 用戶 ID 使用 Discord User ID

### 功能擴展

- [ ] 份量識別與計算
- [ ] 營養素分析 (蛋白質、脂肪、碳水化合物)
- [ ] 飲食建議系統
- [ ] 資料匯出功能
- [ ] 多語言支援

## 🐛 疑難排解

### 常見問題

1. **找不到圖像檔案**: 檢查檔案路徑是否正確
2. **API 金鑰錯誤**: 檢查 `config/.env` 檔案
3. **資料庫錯誤**: 檢查 `data/` 目錄權限

### 除錯技巧

- 使用 `--debug` 參數查看詳細日誌
- 檢查 `data/user_data.db` 是否存在
- 確認網路連接正常 (API 呼叫需要)
