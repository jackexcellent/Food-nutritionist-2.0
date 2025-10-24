"""
Diet Tracker Bot Tests Package
==============================

這個包包含了Diet Tracker Bot的所有測試代碼。

測試結構：
- test_utils.py: 測試共用工具函數
- test_bot.py: 測試Discord Bot功能 (未來實現)
- test_vision.py: 測試圖像識別功能 (未來實現)
- test_nutrition.py: 測試營養計算功能 (未來實現)
- test_database.py: 測試資料庫操作 (未來實現)
- test_ai.py: 測試AI推薦功能 (未來實現)

執行測試命令：
- 執行所有測試: pytest
- 執行特定測試: pytest tests/test_utils.py
- 生成覆蓋率報告: pytest --cov=src tests/

測試原則：
1. 每個模組都應該有對應的測試文件
2. 測試函數名稱應該清楚描述測試的功能
3. 使用fixture來設定測試環境
4. 模擬外部API呼叫，避免在測試中使用真實API
5. 測試應該快速、獨立且可重複執行
"""

__version__ = "1.0.0"