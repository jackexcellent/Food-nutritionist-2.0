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
