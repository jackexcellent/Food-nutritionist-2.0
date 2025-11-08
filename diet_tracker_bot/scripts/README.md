# 工具腳本說明

這個目錄包含各種開發和維護用的工具腳本。

---

## 📋 可用腳本

### view_database.py

**功能**: 查看和分析 user_data.db 資料庫內容的互動式工具

**使用方式**:

```bash
cd "c:\python workspace\special reports\Food nutritionist\food nu 2.0\diet_tracker_bot"
python scripts/view_database.py
```

**功能清單**:

- 📊 顯示所有資料表結構
- 👁️ 查看所有記錄內容
- 🔍 查詢特定用戶的歷史記錄
- 📈 顯示用戶統計資訊（總餐數、平均熱量等）
- 🗄️ 資料庫健康檢查

**互動式選單**:

```
1. 查看所有表格
2. 查看所有記錄
3. 查看用戶歷史記錄
4. 查看用戶統計
5. 退出
```

**使用案例**:

- 開發時快速檢查資料庫內容
- 驗證用戶數據是否正確儲存
- 調試資料庫相關問題
- 生成用戶使用報告

---

## 🔧 使用提示

### 環境要求

確保已安裝所有依賴：

```bash
pip install -r requirements.txt
```

### 資料庫位置

工具腳本會自動尋找 `data/user_data.db`，確保：

1. 資料庫檔案存在
2. 有適當的讀取權限

### 錯誤處理

如果遇到資料庫鎖定錯誤：

1. 確保沒有其他程式正在使用資料庫
2. 關閉 Discord bot（如果正在運行）
3. 重試操作

---

## 📝 添加新工具

如果要添加新的工具腳本：

1. **建立腳本檔案**:

   ```bash
   touch scripts/your_tool.py
   ```

2. **添加腳本說明**:
   在此 README 中添加新工具的說明

3. **使用標準模板**:

   ```python
   #!/usr/bin/env python3
   """
   工具名稱 - 簡短描述
   """

   import sys
   from pathlib import Path

   # 添加 src 到路徑
   current_dir = Path(__file__).parent.parent
   src_dir = current_dir / "src"
   sys.path.insert(0, str(src_dir))

   def main():
       """主函數"""
       pass

   if __name__ == "__main__":
       main()
   ```

---

## 🔗 相關資源

- [主專案 README](../docs/README.md)
- [測試文件](../tests/README.md) _(待建立)_
- [API 文件](../docs/) _(待建立)_

---

**最後更新**: 2025-11-08
