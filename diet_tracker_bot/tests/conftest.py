#!/usr/bin/env python3
"""
Diet Tracker Bot - 測試輔助工具和 Fixtures
=========================================

提供測試中常用的輔助函數和 pytest fixtures。
包含測試資料生成、Mock 設定、測試環境管理等工具。

功能包括：
1. 測試資料生成器
2. Mock 對象工廠
3. 資料庫測試工具
4. 圖片測試工具  
5. 性能測試工具
6. 環境設定 fixtures
7. 清理工具

使用方式：
- 在測試檔案中導入需要的 fixtures
- 使用 pytest.mark.parametrize 與資料生成器
- 利用 Mock 工廠簡化 Mock 設定
"""

import os
import sys
import pytest
import tempfile
import json
import time
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
from typing import Dict, List, Any, Optional, Tuple
import logging

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

import utils
import data_storage

class TestDataGenerator:
    """測試資料生成器"""
    
    @staticmethod
    def generate_food_list(count: int = 5) -> List[str]:
        """生成食物名稱列表"""
        foods = [
            '蘋果', '香蕉', '橘子', '葡萄', '草莓', '芒果', '鳳梨', '櫻桃',
            '米飯', '麵條', '麵包', '饅頭', '餃子', '包子', '湯圓', '粥',
            '雞肉', '豬肉', '牛肉', '魚肉', '蝦子', '蛋', '豆腐', '牛奶',
            '青菜', '高麗菜', '菠菜', '紅蘿蔔', '馬鈴薯', '番茄', '洋蔥', '蒜頭'
        ]
        return foods[:count] if count <= len(foods) else foods * (count // len(foods) + 1)[:count]
    
    @staticmethod
    def generate_nutrition_data(foods: List[str]) -> Tuple[Dict[str, float], float]:
        """生成營養資料"""
        nutrition_data = {}
        total_calories = 0
        
        for food in foods:
            # 根據食物類型生成合理的熱量
            if food in ['米飯', '麵條', '麵包', '饅頭']:
                calories = np.random.uniform(120, 200)
            elif food in ['雞肉', '豬肉', '牛肉', '魚肉']:
                calories = np.random.uniform(150, 250)
            elif food in ['蘋果', '香蕉', '橘子']:
                calories = np.random.uniform(50, 100)
            else:
                calories = np.random.uniform(20, 150)
            
            nutrition_data[food] = round(calories, 1)
            total_calories += calories
        
        return nutrition_data, round(total_calories, 1)
    
    @staticmethod
    def generate_user_history(user_id: str, days: int = 7, meals_per_day: int = 3) -> List[Tuple]:
        """生成用戶歷史記錄"""
        history = []
        
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            
            for meal in range(meals_per_day):
                # 生成餐點資料
                foods = TestDataGenerator.generate_food_list(np.random.randint(1, 4))
                nutrition_data, total_calories = TestDataGenerator.generate_nutrition_data(foods)
                
                # 模擬資料庫記錄格式
                meal_record = (
                    day * meals_per_day + meal + 1,  # meal_id
                    user_id,
                    json.dumps(nutrition_data, ensure_ascii=False),
                    total_calories,
                    date.strftime('%Y-%m-%d %H:%M:%S')
                )
                history.append(meal_record)
        
        return history
    
    @staticmethod
    def generate_test_image(filename: str = None, size: Tuple[int, int] = (300, 300)) -> str:
        """生成測試用圖片"""
        # 創建隨機圖片
        img_array = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        # 儲存到暫存目錄
        if not filename:
            filename = f"test_image_{time.time()}.jpg"
        
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        img.save(temp_path, 'JPEG')
        
        return temp_path


class MockFactory:
    """Mock 對象工廠"""
    
    @staticmethod
    def create_discord_message_mock(content: str = "測試訊息", author_id: int = 123456789):
        """創建 Discord 訊息 Mock"""
        mock_author = Mock()
        mock_author.id = author_id
        mock_author.mention = f"<@{author_id}>"
        
        mock_message = Mock()
        mock_message.content = content
        mock_message.author = mock_author
        mock_message.attachments = []
        
        return mock_message
    
    @staticmethod
    def create_discord_attachment_mock(filename: str = "test.jpg", size: int = 1024):
        """創建 Discord 附件 Mock"""
        mock_attachment = Mock()
        mock_attachment.filename = filename
        mock_attachment.size = size
        mock_attachment.url = f"https://example.com/{filename}"
        
        # Mock save 方法
        async def mock_save(fp):
            # 創建測試圖片並儲存
            test_image_path = TestDataGenerator.generate_test_image(
                filename=f"downloaded_{filename}"
            )
            
            # 複製到目標檔案
            with open(test_image_path, 'rb') as src:
                with open(fp, 'wb') as dst:
                    dst.write(src.read())
            
            # 清理暫存檔案
            os.unlink(test_image_path)
        
        mock_attachment.save = mock_save
        return mock_attachment
    
    @staticmethod
    def create_image_processor_mock(foods: List[str] = None):
        """創建圖像處理器 Mock"""
        if foods is None:
            foods = TestDataGenerator.generate_food_list(2)
        
        mock_processor = Mock()
        mock_processor.process_image.return_value = foods
        return mock_processor
    
    @staticmethod
    def create_nutrition_calculator_mock(foods: List[str] = None):
        """創建營養計算器 Mock"""
        if foods is None:
            foods = TestDataGenerator.generate_food_list(2)
        
        nutrition_data, total_calories = TestDataGenerator.generate_nutrition_data(foods)
        
        mock_calculator = Mock()
        mock_calculator.get_nutrition.return_value = (nutrition_data, total_calories)
        return mock_calculator
    
    @staticmethod
    def create_recommendation_engine_mock(recommendation: str = None):
        """創建推薦引擎 Mock"""
        if recommendation is None:
            recommendation = "這是一個測試推薦，建議您保持均衡飲食並適量運動。"
        
        mock_engine = Mock()
        mock_engine.get_recommendation.return_value = recommendation
        return mock_engine


class DatabaseTestHelper:
    """資料庫測試輔助工具"""
    
    @staticmethod
    def create_test_database(db_path: str = None) -> str:
        """創建測試用資料庫"""
        if db_path is None:
            # 創建暫存資料庫
            fd, db_path = tempfile.mkstemp(suffix='.db')
            os.close(fd)
        
        # 初始化資料庫結構
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 創建表格
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                food_data TEXT NOT NULL,
                total_calories REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return db_path
    
    @staticmethod
    def populate_test_database(db_path: str, users: List[str] = None, 
                             days: int = 7, meals_per_day: int = 3):
        """填充測試資料到資料庫"""
        if users is None:
            users = ['test_user_1', 'test_user_2', 'test_user_3']
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        for user_id in users:
            history = TestDataGenerator.generate_user_history(user_id, days, meals_per_day)
            
            for meal_record in history:
                cursor.execute('''
                    INSERT INTO meals (user_id, food_data, total_calories, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', meal_record[1:])  # 跳過 meal_id
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def cleanup_test_database(db_path: str):
        """清理測試資料庫"""
        if os.path.exists(db_path):
            os.unlink(db_path)


# ============ Pytest Fixtures ============

@pytest.fixture(scope="session")
def test_data_dir():
    """測試資料目錄"""
    data_dir = Path(__file__).parent / "test_data"
    data_dir.mkdir(exist_ok=True)
    yield data_dir
    # 測試結束後清理


@pytest.fixture(scope="function")
def clean_environment():
    """清潔的測試環境"""
    # 測試前清理
    utils.clear_cache()
    
    yield
    
    # 測試後清理
    utils.clear_cache()
    
    # 清理暫存檔案
    temp_dir = Path(tempfile.gettempdir())
    for temp_file in temp_dir.glob("test_image_*.jpg"):
        try:
            temp_file.unlink()
        except:
            pass


@pytest.fixture(scope="function")
def test_database():
    """測試用資料庫"""
    db_path = DatabaseTestHelper.create_test_database()
    
    # 設定環境變數指向測試資料庫
    original_db_path = os.environ.get('DATABASE_PATH')
    os.environ['DATABASE_PATH'] = db_path
    
    # 重新初始化資料庫模組
    data_storage.init_database()
    
    yield db_path
    
    # 恢復原始設定
    if original_db_path:
        os.environ['DATABASE_PATH'] = original_db_path
    else:
        os.environ.pop('DATABASE_PATH', None)
    
    # 清理測試資料庫
    DatabaseTestHelper.cleanup_test_database(db_path)


@pytest.fixture(scope="function")
def populated_database(test_database):
    """填充了測試資料的資料庫"""
    DatabaseTestHelper.populate_test_database(
        test_database, 
        users=['user1', 'user2', 'user3'],
        days=7, 
        meals_per_day=3
    )
    
    yield test_database


@pytest.fixture(scope="function")
def test_logger():
    """測試用 logger"""
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    
    # 避免重複添加 handler
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    yield logger


@pytest.fixture(scope="function")
def mock_external_apis():
    """Mock 所有外部 API"""
    with patch('image_processor.process_image') as mock_image, \
         patch('nutrition_calculator.get_nutrition') as mock_nutrition, \
         patch('recommendation_engine.get_recommendation') as mock_recommendation:
        
        # 設定預設回傳值
        mock_image.return_value = ['蘋果', '香蕉']
        mock_nutrition.return_value = ({'蘋果': 52.0, '香蕉': 89.0}, 141.0)
        mock_recommendation.return_value = "這是一個測試推薦內容。"
        
        yield {
            'image_processor': mock_image,
            'nutrition_calculator': mock_nutrition,
            'recommendation_engine': mock_recommendation
        }


@pytest.fixture(scope="function")
def test_image_files():
    """測試用圖片檔案"""
    image_paths = []
    
    # 創建不同大小的測試圖片
    sizes = [(100, 100), (300, 300), (600, 600)]
    for i, size in enumerate(sizes):
        image_path = TestDataGenerator.generate_test_image(
            filename=f"test_fixture_{i}.jpg",
            size=size
        )
        image_paths.append(image_path)
    
    yield image_paths
    
    # 清理圖片檔案
    for image_path in image_paths:
        if os.path.exists(image_path):
            os.unlink(image_path)


@pytest.fixture(scope="function")
def performance_monitor():
    """性能監控器"""
    start_time = time.time()
    start_memory = utils.get_memory_usage()
    
    yield {
        'start_time': start_time,
        'start_memory': start_memory
    }
    
    # 記錄結束狀態
    end_time = time.time()
    end_memory = utils.get_memory_usage()
    
    duration = end_time - start_time
    memory_increase = end_memory - start_memory
    
    print(f"\n📊 性能統計:")
    print(f"   執行時間: {duration:.3f}s")
    print(f"   記憶體增長: {memory_increase:.1f}MB")


# ============ 參數化測試資料 ============

# 常用的測試食物組合
FOOD_COMBINATIONS = [
    ['蘋果'],
    ['蘋果', '香蕉'],
    ['米飯', '雞肉', '青菜'],
    ['麵條', '豬肉', '紅蘿蔔', '洋蔥'],
    ['麵包', '蛋', '牛奶', '草莓', '蜂蜜']
]

# 常用的用戶 ID
TEST_USER_IDS = [
    'test_user_1',
    'test_user_2', 
    'performance_test_user',
    'integration_test_user',
    'stress_test_user'
]

# 測試圖片大小
IMAGE_SIZES = [
    (100, 100),   # 小圖
    (300, 300),   # 標準
    (600, 600),   # 中圖
    (1200, 1200), # 大圖
    (2000, 2000)  # 特大圖
]

# 性能測試基準
PERFORMANCE_BENCHMARKS = {
    'image_processing_max_time': 3.0,      # 圖像處理最大時間 (秒)
    'nutrition_calc_max_time': 1.0,        # 營養計算最大時間 (秒)
    'database_write_max_time': 0.1,        # 資料庫寫入最大時間 (秒)
    'database_read_max_time': 0.5,         # 資料庫讀取最大時間 (秒)
    'recommendation_max_time': 5.0,        # 推薦生成最大時間 (秒)
    'max_memory_increase_mb': 100,         # 最大記憶體增長 (MB)
    'min_cache_speedup': 2.0,              # 最小快取加速比
    'min_success_rate': 0.95               # 最小成功率
}


# ============ 測試工具函數 ============

def assert_performance_benchmark(operation: str, duration: float, 
                               logger: logging.Logger = None):
    """驗證性能基準"""
    benchmark_key = f"{operation}_max_time"
    
    if benchmark_key in PERFORMANCE_BENCHMARKS:
        max_time = PERFORMANCE_BENCHMARKS[benchmark_key]
        
        if duration > max_time:
            message = f"性能未達標: {operation} 耗時 {duration:.3f}s > {max_time}s"
            if logger:
                logger.warning(message)
            pytest.fail(message)
        else:
            if logger:
                logger.info(f"✅ 性能達標: {operation} 耗時 {duration:.3f}s < {max_time}s")


def cleanup_test_files(*file_paths):
    """清理測試檔案"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"清理檔案失敗 {file_path}: {e}")


def validate_nutrition_data(nutrition_data: Dict[str, float], foods: List[str]) -> bool:
    """驗證營養資料格式"""
    if not isinstance(nutrition_data, dict):
        return False
    
    if len(nutrition_data) != len(foods):
        return False
    
    for food in foods:
        if food not in nutrition_data:
            return False
        
        if not isinstance(nutrition_data[food], (int, float)):
            return False
        
        if nutrition_data[food] < 0:
            return False
    
    return True


def validate_recommendation_format(recommendation: str) -> bool:
    """驗證推薦內容格式"""
    if not isinstance(recommendation, str):
        return False
    
    if len(recommendation.strip()) < 10:
        return False
    
    return True