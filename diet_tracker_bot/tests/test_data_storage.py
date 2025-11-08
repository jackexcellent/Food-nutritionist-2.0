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
        export_to_json,
        get_previous_meals,  # 新增
        get_past_days       # 新增
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
        export_to_json,
        get_previous_meals,  # 新增
        get_past_days       # 新增
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


# ========== 餐次功能擴展測試 ==========

class TestMealTypeFeatures:
    """測試新增的餐次類型和份量功能"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """每個測試前後設置臨時資料庫"""
        # 設置臨時資料庫路徑
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_meal_type.db"
        
        # 初始化測試資料庫
        init_database()
        
        yield
        
        # 恢復原始資料庫路徑
        data_storage.DB_PATH = self.original_db_path
    
    def test_store_meal_with_meal_type_and_portion(self):
        """測試儲存包含餐次類型和份量的記錄"""
        user_id = "user_meal_type_test"
        
        # 測試早餐
        breakfast_foods = {"oatmeal": 150.0, "milk": 60.0}
        breakfast_calories = sum(breakfast_foods.values())
        
        record_id = store_meal(
            user_id=user_id,
            foods=breakfast_foods,
            calories=breakfast_calories,
            meal_type="breakfast",
            portion_size=200.0
        )
        
        assert record_id is not None
        
        # 驗證記錄
        meal = get_meal_by_id(record_id)
        assert meal is not None
        assert meal[6] == "breakfast"  # meal_type 在索引 6
        assert meal[7] == 200.0       # portion_size 在索引 7
        
    def test_meal_type_validation(self):
        """測試餐次類型驗證"""
        user_id = "user_validation_test"
        foods = {"apple": 52.0}
        calories = 52.0
        
        # 有效的餐次類型
        valid_types = ['breakfast', 'lunch', 'dinner', 'snack', 'meal']
        for meal_type in valid_types:
            record_id = store_meal(user_id, foods, calories, meal_type=meal_type)
            assert record_id is not None
        
        # 無效的餐次類型
        with pytest.raises(ValueError, match="meal_type 必須是"):
            store_meal(user_id, foods, calories, meal_type="invalid_type")
    
    def test_portion_size_validation(self):
        """測試份量驗證"""
        user_id = "user_portion_test"
        foods = {"apple": 52.0}
        calories = 52.0
        
        # 有效份量
        record_id = store_meal(user_id, foods, calories, portion_size=150.0)
        assert record_id is not None
        
        # 無效份量（負數）
        with pytest.raises(ValueError, match="portion_size 必須大於 0"):
            store_meal(user_id, foods, calories, portion_size=-10.0)
        
        # 無效份量（零）
        with pytest.raises(ValueError, match="portion_size 必須大於 0"):
            store_meal(user_id, foods, calories, portion_size=0)
    
    def test_backward_compatibility(self):
        """測試向後相容性（不提供新參數）"""
        user_id = "user_compat_test"
        foods = {"banana": 89.0}
        calories = 89.0
        
        # 不提供新參數，應該使用預設值
        record_id = store_meal(user_id, foods, calories)
        assert record_id is not None
        
        # 驗證預設值
        meal = get_meal_by_id(record_id)
        assert meal is not None
        assert meal[6] == "meal"    # 預設 meal_type
        assert meal[7] == 100.0    # 預設 portion_size


class TestPreviousMeals:
    """測試 get_previous_meals 功能"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """每個測試前後設置臨時資料庫"""
        # 設置臨時資料庫路徑
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_previous_meals.db"
        
        # 初始化測試資料庫
        init_database()
        
        yield
        
        # 恢復原始資料庫路徑
        data_storage.DB_PATH = self.original_db_path
    
    def test_get_previous_meals_basic(self):
        """測試基本前序餐點查詢"""
        user_id = "user_previous_test"
        
        # 添加今日早餐
        breakfast_id = store_meal(
            user_id, {"oatmeal": 150.0}, 150.0, meal_type="breakfast"
        )
        
        # 添加今日午餐  
        lunch_id = store_meal(
            user_id, {"sandwich": 300.0}, 300.0, meal_type="lunch"
        )
        
        # 查詢晚餐前的餐點（應該包含早餐和午餐）
        previous = get_previous_meals(user_id, "dinner")
        assert len(previous) == 2
        
        # 驗證順序（應該按時間排序）
        meal_types = [meal[5] for meal in previous]  # meal_type 在索引 5
        assert "breakfast" in meal_types
        assert "lunch" in meal_types
        
        # 查詢午餐前的餐點（應該只包含早餐）
        previous_lunch = get_previous_meals(user_id, "lunch")
        assert len(previous_lunch) == 1
        assert previous_lunch[0][5] == "breakfast"  # meal_type
        
        # 查詢早餐前的餐點（應該為空）
        previous_breakfast = get_previous_meals(user_id, "breakfast")
        assert len(previous_breakfast) == 0
    
    def test_get_previous_meals_different_days(self):
        """測試跨日期的前序餐點查詢（不應該包含昨天的）"""
        user_id = "user_multiday_test"
        
        # 昨天的晚餐
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        yesterday_id = store_meal(
            user_id, {"pasta": 400.0}, 400.0, 
            date=yesterday, meal_type="dinner"
        )
        
        # 今天的早餐
        today_breakfast_id = store_meal(
            user_id, {"cereal": 200.0}, 200.0, meal_type="breakfast"
        )
        
        # 查詢今日午餐前的餐點（應該只包含今日早餐，不包含昨日晚餐）
        previous = get_previous_meals(user_id, "lunch")
        assert len(previous) == 1
        assert previous[0][0] == today_breakfast_id  # 記錄 ID
    
    def test_get_previous_meals_validation(self):
        """測試參數驗證"""
        # 空 user_id
        with pytest.raises(ValueError, match="user_id 不能為空"):
            get_previous_meals("", "dinner")
        
        # 無效餐次類型
        with pytest.raises(ValueError, match="current_meal_type 必須是"):
            get_previous_meals("user_test", "invalid_meal")


class TestPastDaysAnalysis:
    """測試 get_past_days 分析功能"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """每個測試前後設置臨時資料庫"""
        # 設置臨時資料庫路徑
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_past_days.db"
        
        # 初始化測試資料庫
        init_database()
        
        yield
        
        # 恢復原始資料庫路徑
        data_storage.DB_PATH = self.original_db_path
    
    def test_get_past_days_basic(self):
        """測試基本過去天數分析"""
        user_id = "user_analysis_test"
        
        # 添加多天的餐點記錄
        today = datetime.now()
        
        # 今天
        store_meal(user_id, {"breakfast": 200.0}, 200.0, meal_type="breakfast")
        store_meal(user_id, {"lunch": 300.0}, 300.0, meal_type="lunch")
        
        # 昨天
        yesterday = (today - timedelta(days=1)).isoformat()
        store_meal(user_id, {"dinner": 400.0}, 400.0, 
                  date=yesterday, meal_type="dinner")
        
        # 前天
        day_before = (today - timedelta(days=2)).isoformat()
        store_meal(user_id, {"snack": 100.0}, 100.0,
                  date=day_before, meal_type="snack")
        
        # 分析過去 3 天
        analysis = get_past_days(user_id, days=3)
        
        # 驗證基本結構
        assert 'daily_summaries' in analysis
        assert 'meal_type_stats' in analysis
        assert 'nutrition_trends' in analysis
        assert 'total_meals' in analysis
        assert 'recommendations' in analysis
        
        # 驗證數據
        assert analysis['total_meals'] == 4
        assert len(analysis['daily_summaries']) <= 3  # 最多3天
        assert analysis['nutrition_trends']['avg_daily_calories'] > 0
        
    def test_get_past_days_statistics(self):
        """測試統計計算的正確性"""
        user_id = "user_stats_test"
        
        # 添加一致的餐點（便於計算驗證）
        for day_offset in range(3):
            date = (datetime.now() - timedelta(days=day_offset)).isoformat()
            # 每天 500 kcal
            store_meal(user_id, {"meal": 500.0}, 500.0, date=date)
        
        analysis = get_past_days(user_id, days=3)
        
        # 驗證平均熱量
        assert analysis['nutrition_trends']['avg_daily_calories'] == 500.0
        assert analysis['nutrition_trends']['max_daily_calories'] == 500.0
        assert analysis['nutrition_trends']['min_daily_calories'] == 500.0
        assert analysis['nutrition_trends']['calorie_variance'] == 0.0  # 完全一致
        
    def test_get_past_days_meal_type_stats(self):
        """測試餐次類型統計"""
        user_id = "user_mealtype_stats_test"
        
        # 添加不同餐次類型
        store_meal(user_id, {"b1": 100.0}, 100.0, meal_type="breakfast")
        store_meal(user_id, {"b2": 100.0}, 100.0, meal_type="breakfast")  # 2個早餐
        store_meal(user_id, {"l1": 200.0}, 200.0, meal_type="lunch")      # 1個午餐
        store_meal(user_id, {"d1": 300.0}, 300.0, meal_type="dinner")     # 1個晚餐
        # 總共 4 餐
        
        analysis = get_past_days(user_id, days=7)
        
        meal_stats = analysis['meal_type_stats']
        assert meal_stats['breakfast'] == 50.0  # 2/4 = 50%
        assert meal_stats['lunch'] == 25.0      # 1/4 = 25%
        assert meal_stats['dinner'] == 25.0     # 1/4 = 25%
        
    def test_get_past_days_validation(self):
        """測試參數驗證"""
        # 空 user_id
        with pytest.raises(ValueError, match="user_id 不能為空"):
            get_past_days("", 3)
        
        # 無效天數
        with pytest.raises(ValueError, match="days 必須大於 0"):
            get_past_days("user_test", 0)
        
        with pytest.raises(ValueError, match="days 必須大於 0"):
            get_past_days("user_test", -1)
    
    def test_get_past_days_empty_result(self):
        """測試空結果處理"""
        user_id = "user_empty_test"
        
        # 沒有任何記錄
        analysis = get_past_days(user_id, days=7)
        
        assert analysis['total_meals'] == 0
        assert analysis['daily_summaries'] == []
        assert analysis['meal_type_stats'] == {}
        assert analysis['nutrition_trends']['avg_daily_calories'] == 0
        assert len(analysis['recommendations']) > 0  # 應該有預設建議


class TestDatabaseMigration:
    """測試資料庫遷移功能"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """每個測試前後設置臨時資料庫"""
        # 設置臨時資料庫路徑
        self.original_db_path = data_storage.DB_PATH
        data_storage.DB_PATH = tmp_path / "test_migration.db"
        
        # 初始化測試資料庫
        init_database()
        
        yield
        
        # 恢復原始資料庫路徑
        data_storage.DB_PATH = self.original_db_path
    
    def test_migration_adds_new_columns(self):
        """測試遷移是否正確添加新欄位"""
        # 初始化資料庫會觸發遷移
        init_database()
        
        # 檢查新欄位是否存在
        with data_storage.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(meals)")
            columns = {col[1] for col in cursor.fetchall()}
            
            assert 'meal_type' in columns
            assert 'portion_size' in columns
    
    def test_migration_backward_compatibility(self):
        """測試遷移後的向後相容性"""
        # 遷移後應該能正常儲存和查詢
        user_id = "migration_test_user"
        foods = {"test_food": 100.0}
        
        # 舊格式（不提供新參數）
        record_id = store_meal(user_id, foods, 100.0)
        assert record_id is not None
        
        # 新格式
        record_id2 = store_meal(
            user_id, foods, 100.0, 
            meal_type="breakfast", 
            portion_size=150.0
        )
        assert record_id2 is not None
        
        # 查詢應該正常工作
        history = get_history(user_id, days=1)
        assert len(history) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
