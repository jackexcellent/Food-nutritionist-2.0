#!/usr/bin/env python3
"""
Diet Tracker Bot - 資料儲存模組測試
====================================

測試資料庫操作的完整性和正確性，包括：
1. SQLite 連接管理
2. CRUD 操作（創建、讀取、更新、刪除）
3. 歷史記錄查詢
4. 統計功能
5. 錯誤處理
6. 資料匯出

設計原則：
- 使用臨時資料庫避免污染生產資料
- 測試所有主要功能路徑
- 驗證錯誤處理機制
"""

import os
import sys
import json
import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# 導入要測試的模組
try:
    import data_storage
    from data_storage import (
        init_database,
        store_meal,
        get_history,
        get_meal_by_id,
        delete_meal,
        get_statistics,
        export_to_json
    )
except ImportError:
    # 如果無法導入，嘗試相對導入
    sys.path.insert(0, str(current_dir.parent))
    import src.data_storage as data_storage
    from src.data_storage import (
        init_database,
        store_meal,
        get_history,
        get_meal_by_id,
        delete_meal,
        get_statistics,
        export_to_json
    )



class TestDatabaseConnection:
    """資料庫連接測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """每個測試前後設置臨時資料庫"""
        # 設置臨時資料庫路徑
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        
        # 初始化測試資料庫
        init_database()
        
        yield
        
        # 恢復原始路徑
        data_storage.DB_PATH = self.original_db_path
    
    def test_database_connection(self):
        """測試資料庫連接"""
        with data_storage.get_db_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_database_initialization(self):
        """測試資料庫初始化"""
        # 驗證 meals 表存在
        with data_storage.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='meals'
            """)
            result = cursor.fetchone()
            assert result is not None
            assert result['name'] == 'meals'
    
    def test_database_schema(self):
        """測試資料庫 schema"""
        with data_storage.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(meals)")
            columns = cursor.fetchall()
            
            # 驗證欄位
            column_names = [col['name'] for col in columns]
            assert 'id' in column_names
            assert 'user_id' in column_names
            assert 'date' in column_names
            assert 'foods' in column_names
            assert 'calories' in column_names
            assert 'created_at' in column_names


class TestStoreMeal:
    """儲存飲食記錄測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """設置臨時資料庫"""
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        init_database()
        yield
        data_storage.DB_PATH = self.original_db_path
    
    def test_store_meal_basic(self):
        """測試基本的儲存功能"""
        user_id = "test_user_001"
        foods = {"apple": 52.0, "banana": 89.0}
        calories = sum(foods.values())
        
        # 儲存記錄
        record_id = store_meal(user_id, foods, calories)
        
        # 驗證返回的 ID
        assert isinstance(record_id, int)
        assert record_id > 0
    
    def test_store_meal_with_date(self):
        """測試指定日期的儲存"""
        user_id = "test_user_002"
        foods = {"chicken": 165.0}
        calories = 165.0
        custom_date = "2024-10-27T12:00:00"
        
        record_id = store_meal(user_id, foods, calories, date=custom_date)
        
        # 驗證日期正確儲存
        meal = get_meal_by_id(record_id)
        assert meal is not None
        assert meal[2] == custom_date  # date 欄位
    
    def test_store_meal_json_encoding(self):
        """測試 JSON 編碼"""
        user_id = "test_user_003"
        foods = {
            "蘋果": 52.0,  # 中文
            "Grilled Chicken": 165.0  # 英文
        }
        calories = sum(foods.values())
        
        record_id = store_meal(user_id, foods, calories)
        
        # 驗證可以正確讀取
        meal = get_meal_by_id(record_id)
        assert meal is not None
        retrieved_foods = meal[3]  # foods 欄位
        assert retrieved_foods == foods
    
    def test_store_meal_invalid_user_id(self):
        """測試無效的 user_id"""
        with pytest.raises(ValueError, match="user_id 不能為空"):
            store_meal("", {"apple": 52.0}, 52.0)
    
    def test_store_meal_invalid_foods(self):
        """測試無效的 foods 參數"""
        # 空字典
        with pytest.raises(ValueError, match="foods 必須是非空的字典"):
            store_meal("test_user", {}, 0.0)
        
        # 非字典類型
        with pytest.raises(ValueError, match="foods 必須是非空的字典"):
            store_meal("test_user", None, 0.0)
    
    def test_store_meal_negative_calories(self):
        """測試負數熱量"""
        with pytest.raises(ValueError, match="calories 不能為負數"):
            store_meal("test_user", {"apple": 52.0}, -52.0)


class TestGetHistory:
    """歷史記錄查詢測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """設置臨時資料庫並插入測試資料"""
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        init_database()
        
        # 插入測試資料
        self.test_user_id = "test_user_history"
        
        # 插入不同日期的記錄
        dates = [
            datetime.now() - timedelta(days=0),  # 今天
            datetime.now() - timedelta(days=2),  # 2天前
            datetime.now() - timedelta(days=5),  # 5天前
            datetime.now() - timedelta(days=10), # 10天前（超過默認7天）
        ]
        
        self.test_records = []
        for i, date in enumerate(dates):
            foods = {f"food_{i}": float(50 + i * 10)}
            calories = sum(foods.values())
            record_id = store_meal(
                self.test_user_id, 
                foods, 
                calories,
                date=date.isoformat()
            )
            self.test_records.append(record_id)
        
        yield
        data_storage.DB_PATH = self.original_db_path
    
    def test_get_history_default_days(self):
        """測試默認 7 天查詢"""
        history = get_history(self.test_user_id)
        
        # 應該返回 3 筆記錄（0, 2, 5 天前的記錄）
        assert len(history) == 3
        
        # 驗證返回格式
        for record in history:
            assert len(record) == 5  # id, date, foods, calories, created_at
            assert isinstance(record[0], int)  # id
            assert isinstance(record[1], str)  # date
            assert isinstance(record[2], dict)  # foods
            assert isinstance(record[3], float)  # calories
            assert isinstance(record[4], str)  # created_at
    
    def test_get_history_custom_days(self):
        """測試自定義天數查詢"""
        # 查詢最近 15 天
        history = get_history(self.test_user_id, days=15)
        
        # 應該返回所有 4 筆記錄
        assert len(history) == 4
    
    def test_get_history_order(self):
        """測試記錄排序（最新在前）"""
        history = get_history(self.test_user_id, days=15)
        
        # 驗證按日期降序排列
        dates = [record[1] for record in history]
        assert dates == sorted(dates, reverse=True)
    
    def test_get_history_empty(self):
        """測試查詢不存在的用戶"""
        history = get_history("non_existent_user")
        
        assert isinstance(history, list)
        assert len(history) == 0
    
    def test_get_history_invalid_user_id(self):
        """測試無效的 user_id"""
        with pytest.raises(ValueError, match="user_id 不能為空"):
            get_history("")
    
    def test_get_history_invalid_days(self):
        """測試無效的天數"""
        with pytest.raises(ValueError, match="days 必須大於 0"):
            get_history("test_user", days=0)
        
        with pytest.raises(ValueError, match="days 必須大於 0"):
            get_history("test_user", days=-1)


class TestGetMealById:
    """單筆記錄查詢測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """設置臨時資料庫"""
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        init_database()
        yield
        data_storage.DB_PATH = self.original_db_path
    
    def test_get_meal_by_id_success(self):
        """測試成功查詢"""
        # 先插入記錄
        foods = {"apple": 52.0, "banana": 89.0}
        calories = sum(foods.values())
        record_id = store_meal("test_user", foods, calories)
        
        # 查詢記錄
        meal = get_meal_by_id(record_id)
        
        assert meal is not None
        assert meal[0] == record_id
        assert meal[1] == "test_user"
        assert meal[3] == foods
        assert meal[4] == calories
    
    def test_get_meal_by_id_not_found(self):
        """測試查詢不存在的記錄"""
        meal = get_meal_by_id(99999)
        
        assert meal is None


class TestDeleteMeal:
    """刪除記錄測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """設置臨時資料庫"""
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        init_database()
        yield
        data_storage.DB_PATH = self.original_db_path
    
    def test_delete_meal_success(self):
        """測試成功刪除"""
        # 插入記錄
        record_id = store_meal("test_user", {"apple": 52.0}, 52.0)
        
        # 刪除記錄
        result = delete_meal(record_id)
        
        assert result is True
        
        # 驗證記錄已被刪除
        meal = get_meal_by_id(record_id)
        assert meal is None
    
    def test_delete_meal_not_found(self):
        """測試刪除不存在的記錄"""
        result = delete_meal(99999)
        
        assert result is False


class TestGetStatistics:
    """統計功能測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """設置臨時資料庫並插入測試資料"""
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        init_database()
        
        # 插入測試資料
        self.test_user_id = "test_user_stats"
        
        # 插入多筆記錄
        test_meals = [
            {"apple": 52.0, "banana": 89.0},  # 141 kcal
            {"apple": 52.0, "orange": 47.0},  # 99 kcal
            {"chicken": 165.0, "rice": 130.0}, # 295 kcal
        ]
        
        for foods in test_meals:
            calories = sum(foods.values())
            store_meal(self.test_user_id, foods, calories)
        
        yield
        data_storage.DB_PATH = self.original_db_path
    
    def test_get_statistics_basic(self):
        """測試基本統計"""
        stats = get_statistics(self.test_user_id, days=7)
        
        assert stats['total_meals'] == 3
        assert stats['total_calories'] == 141.0 + 99.0 + 295.0
        assert abs(stats['avg_calories'] - 178.33) < 0.1
        assert isinstance(stats['most_common_foods'], list)
    
    def test_get_statistics_most_common_foods(self):
        """測試最常見食物統計"""
        stats = get_statistics(self.test_user_id, days=7)
        
        # apple 出現 2 次，應該排第一
        most_common = dict(stats['most_common_foods'])
        assert 'apple' in most_common
        assert most_common['apple'] == 2
    
    def test_get_statistics_empty(self):
        """測試無記錄時的統計"""
        stats = get_statistics("non_existent_user", days=7)
        
        assert stats['total_meals'] == 0
        assert stats['total_calories'] == 0.0
        assert stats['avg_calories'] == 0.0
        assert stats['most_common_foods'] == []


class TestExportToJson:
    """資料匯出測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """設置臨時資料庫"""
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        init_database()
        
        # 插入測試資料
        store_meal("user_1", {"apple": 52.0}, 52.0)
        store_meal("user_2", {"banana": 89.0}, 89.0)
        
        self.export_path = tmp_path / "test_export.json"
        
        yield
        data_storage.DB_PATH = self.original_db_path
    
    def test_export_to_json(self):
        """測試 JSON 匯出"""
        output_path = export_to_json(self.export_path)
        
        # 驗證檔案存在
        assert Path(output_path).exists()
        
        # 驗證 JSON 內容
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 2
        
        # 驗證資料結構
        for record in data:
            assert 'id' in record
            assert 'user_id' in record
            assert 'date' in record
            assert 'foods' in record
            assert 'calories' in record
            assert 'created_at' in record


class TestErrorHandling:
    """錯誤處理測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """設置臨時資料庫"""
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        init_database()
        yield
        data_storage.DB_PATH = self.original_db_path
    
    def test_database_connection_error(self):
        """測試資料庫連接錯誤"""
        # 設置唯讀路徑（Windows 系統目錄）
        original_path = data_storage.DB_PATH
        data_storage.DB_PATH = Path("C:/Windows/System32/test_readonly.db")
        
        try:
            # 應該拋出權限錯誤
            with pytest.raises((PermissionError, sqlite3.OperationalError)):
                with data_storage.get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("CREATE TABLE test (id INTEGER)")
                    conn.commit()
        finally:
            data_storage.DB_PATH = original_path
    
    def test_invalid_json_in_foods(self):
        """測試 foods JSON 解析錯誤處理"""
        # 直接插入無效的 JSON
        with data_storage.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO meals (user_id, date, foods, calories)
                VALUES (?, ?, ?, ?)
            """, ("test_user", datetime.now().isoformat(), "invalid json", 100.0))
            conn.commit()
        
        # 查詢時應該返回空字典而不是拋出錯誤
        history = get_history("test_user")
        assert len(history) == 1
        assert history[0][2] == {}  # foods 應該是空字典


class TestIntegration:
    """整合測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """設置臨時資料庫"""
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_user_data.db"
        init_database()
        yield
        data_storage.DB_PATH = self.original_db_path
    
    def test_full_workflow(self):
        """測試完整工作流程"""
        user_id = "integration_test_user"
        
        # 1. 儲存多筆記錄
        meals = [
            {"apple": 52.0, "banana": 89.0},
            {"chicken": 165.0, "rice": 130.0},
            {"orange": 47.0}
        ]
        
        record_ids = []
        for foods in meals:
            calories = sum(foods.values())
            record_id = store_meal(user_id, foods, calories)
            record_ids.append(record_id)
        
        # 2. 查詢歷史
        history = get_history(user_id, days=7)
        assert len(history) == 3
        
        # 3. 獲取統計
        stats = get_statistics(user_id, days=7)
        assert stats['total_meals'] == 3
        assert stats['total_calories'] > 0
        
        # 4. 查詢單筆記錄
        meal = get_meal_by_id(record_ids[0])
        assert meal is not None
        assert meal[3] == meals[0]  # 驗證 foods
        
        # 5. 刪除記錄
        success = delete_meal(record_ids[0])
        assert success is True
        
        # 6. 驗證刪除後的查詢
        history_after = get_history(user_id, days=7)
        assert len(history_after) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
