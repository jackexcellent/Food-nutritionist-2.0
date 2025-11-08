# 功能示範程式

這個目錄包含展示專案各項功能的示範程式和範例代碼。

---

## 📚 可用示範

### demo_meal_types.py

**功能**: 展示餐次類型分類、份量追蹤和智慧分析功能

**使用方式**:

```bash
cd "c:\python workspace\special reports\Food nutritionist\food nu 2.0\diet_tracker_bot"
python examples/demo_meal_types.py
```

**展示功能**:

#### 1. 餐次類型儲存

```python
# 支援的餐次類型
- breakfast (早餐)
- lunch (午餐)
- dinner (晚餐)
- snack (點心)
```

#### 2. 份量大小追蹤

```python
# 份量百分比 (預設 100.0)
- 50.0  = 半份
- 100.0 = 標準份量
- 150.0 = 1.5倍份量
```

#### 3. 前序餐點查詢

```python
# 智慧查詢當日前序餐點
# 例如：查詢午餐時，自動返回今日的早餐記錄
```

#### 4. 多日營養趨勢分析

```python
# 分析最近N天的營養攝取趨勢
- 每日總熱量
- 餐次類型分布
- 平均營養數據
```

---

## 🎯 示範場景

### 場景 1: 完整的一天飲食記錄

```python
# 早餐
store_meal(user_id, breakfast_foods, calories, meal_type='breakfast')

# 午餐
store_meal(user_id, lunch_foods, calories, meal_type='lunch')

# 晚餐
store_meal(user_id, dinner_foods, calories, meal_type='dinner')

# 點心
store_meal(user_id, snack_foods, calories, meal_type='snack')
```

### 場景 2: 智慧推薦系統準備

```python
# 查詢前序餐點進行上下文分析
previous_meals = get_previous_meals(user_id, current_meal_type)

# 基於歷史數據的營養建議
past_days_data = get_past_days(user_id, days=7)
```

### 場景 3: RAG 向量檢索準備

```python
# 🔮 未來功能預覽
# 將餐點資料轉換為向量表示
# 進行相似餐點檢索和推薦
```

---

## 🚀 執行示範

### 完整示範流程

```bash
# 1. 確保資料庫已初始化
python -c "from src.data_storage import init_database; init_database()"

# 2. 運行示範程式
python examples/demo_meal_types.py

# 3. 使用工具查看結果
python scripts/view_database.py
```

### 預期輸出

```
🍳 儲存早餐記錄...
✅ 記錄 ID: 1

🍜 儲存午餐記錄...
✅ 記錄 ID: 2

🍽️ 儲存晚餐記錄...
✅ 記錄 ID: 3

🍿 儲存點心記錄...
✅ 記錄 ID: 4

📊 查詢前序餐點...
✅ 找到 2 筆前序記錄

📈 分析 7 天營養趨勢...
✅ 趨勢分析完成
```

---

## 📖 學習資源

### 相關文件

- [餐次類型功能完成報告](../docs/MEAL_TYPES_COMPLETION_REPORT.md)
- [MVP 完成報告](../docs/MVP_COMPLETION_REPORT.md)
- [API 文件](../docs/API.md) _(待建立)_

### 程式碼範例

查看 `demo_meal_types.py` 中的詳細註解和說明

### 最佳實踐

1. **份量記錄**: 始終記錄實際份量百分比
2. **餐次分類**: 正確使用餐次類型以獲得更好的分析
3. **時間順序**: 按實際用餐時間順序記錄
4. **資料完整性**: 提供完整的食物和營養資訊

---

## 🔧 自訂示範

### 建立新的示範程式

1. **複製模板**:

   ```bash
   cp examples/demo_meal_types.py examples/demo_your_feature.py
   ```

2. **修改內容**:

   - 更新文件說明
   - 修改示範場景
   - 添加新功能展示

3. **更新 README**:
   在此文件中添加新示範的說明

### 示範程式模板

```python
#!/usr/bin/env python3
"""
功能名稱示範
==============

展示某項特定功能的使用方式和最佳實踐。
"""

import sys
from pathlib import Path

# 添加 src 目錄到路徑
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def demo_scenario_1():
    """示範場景 1"""
    print("🎯 示範場景 1")
    # 你的示範代碼

def demo_scenario_2():
    """示範場景 2"""
    print("🎯 示範場景 2")
    # 你的示範代碼

def main():
    """主函數"""
    print("=" * 50)
    print("功能示範開始")
    print("=" * 50)

    demo_scenario_1()
    demo_scenario_2()

    print("\n✅ 示範完成！")

if __name__ == "__main__":
    main()
```

---

## 💡 使用建議

### 教育用途

- 新團隊成員的學習材料
- 功能演示和展示
- 客戶 Demo

### 開發用途

- 測試新功能
- 驗證 API 行為
- 性能基準測試

### 文件用途

- 生成文件中的代碼範例
- 建立教學視頻腳本
- 編寫使用指南

---

**最後更新**: 2025-11-08
