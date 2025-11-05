#!/usr/bin/env python3
"""
Diet Tracker Bot - 資料儲存模組
================================

這個模組負責用戶飲食記錄的持久化儲存，包括：
1. SQLite 資料庫連接管理（MVP 階段）
2. 飲食記錄的儲存（CRUD 操作）
3. 歷史記錄查詢
4. 資料庫遷移工具

設計原則：
- MVP 使用 SQLite 提供輕量級資料儲存
- 設計可擴展的資料模型
- 提供清晰的遷移路徑到雲端資料庫

未來擴展計畫：
1. 遷移到 MongoDB（雲端部署）
2. 添加更多查詢過濾選項
3. 用戶偏好設定儲存
4. 資料匯出功能
5. 統計分析功能
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager

# 導入專案共用工具
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

from utils import handle_error

# 模組級別的日誌器
logger = logging.getLogger(__name__)

# 資料庫配置
DB_PATH = project_root / "data" / "user_data.db"
DEFAULT_HISTORY_DAYS = 7  # 預設查詢最近 7 天


# ========== 資料庫連接管理 ==========

@contextmanager
def get_db_connection():
    """
    資料庫連接上下文管理器
    
    提供安全的資料庫連接管理，自動處理連接關閉和錯誤。
    使用 context manager 確保連接正確關閉。
    
    Yields:
        sqlite3.Connection: 資料庫連接對象
    
    Raises:
        sqlite3.Error: 資料庫連接失敗
    
    使用範例:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM meals")
            results = cursor.fetchall()
    
    未來擴展（MongoDB）:
        from pymongo import MongoClient
        
        @contextmanager
        def get_mongo_connection():
            client = MongoClient('mongodb://localhost:27017/')
            db = client['diet_tracker']
            try:
                yield db
            finally:
                client.close()
    """
    conn = None
    try:
        # 確保資料目錄存在
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # 建立資料庫連接
        conn = sqlite3.connect(str(DB_PATH))
        
        # 設定 row_factory 使結果更易讀
        conn.row_factory = sqlite3.Row
        
        logger.debug(f"成功連接到資料庫: {DB_PATH}")
        
        yield conn
        
    except sqlite3.Error as e:
        error_msg = f"資料庫連接失敗: {str(e)}"
        handle_error(e, error_msg, logger=logger, raise_error=True)
        
    finally:
        if conn:
            conn.close()
            logger.debug("資料庫連接已關閉")


def init_database() -> None:
    """
    初始化資料庫結構
    
    創建必要的表格和索引。如果表格已存在則不做任何操作。
    這個函數應該在應用程式啟動時執行一次。
    
    表結構:
    - meals: 用戶飲食記錄
        * id: INTEGER PRIMARY KEY (自動遞增)
        * user_id: TEXT (用戶唯一識別碼)
        * date: TEXT (ISO 8601 格式日期時間)
        * foods: TEXT (JSON 格式的食物清單)
        * calories: REAL (總熱量 kcal)
        * created_at: TEXT (記錄創建時間)
    
    索引:
    - idx_meals_user_date: (user_id, date) 加速查詢
    
    Raises:
        sqlite3.Error: 資料庫初始化失敗
    
    未來擴展（MongoDB）:
        # MongoDB 不需要預先定義 schema，但可以創建索引
        def init_mongodb():
            with get_mongo_connection() as db:
                # 創建集合（如果不存在）
                meals_collection = db['meals']
                
                # 創建索引
                meals_collection.create_index([
                    ('user_id', 1),
                    ('date', -1)
                ])
                
                # 創建 TTL 索引（自動刪除舊記錄）
                meals_collection.create_index(
                    'created_at',
                    expireAfterSeconds=31536000  # 1 年
                )
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 創建 meals 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    foods TEXT NOT NULL,
                    calories REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # 創建索引以加速查詢
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_meals_user_date 
                ON meals(user_id, date DESC)
            """)
            
            # 提交變更
            conn.commit()
            
            logger.info("資料庫初始化完成")
            logger.debug("已創建 meals 表和索引")
            
    except sqlite3.Error as e:
        handle_error(e, "資料庫初始化失敗", logger=logger, raise_error=True)


# ========== CRUD 操作 ==========

def store_meal(user_id: str, 
               foods: Dict[str, float], 
               calories: float,
               date: Optional[str] = None) -> int:
    """
    儲存用戶的一餐飲食記錄
    
    Args:
        user_id: 用戶唯一識別碼（Discord User ID 或其他）
        foods: 食物字典 {食物名稱: 熱量}，例如 {'apple': 52.0, 'banana': 89.0}
        calories: 總熱量（kcal）
        date: 可選的日期時間字串（ISO 8601 格式），默認為當前時間
    
    Returns:
        int: 新記錄的 ID
    
    Raises:
        sqlite3.Error: 資料庫操作失敗
        ValueError: 參數驗證失敗
    
    使用範例:
        foods = {'apple': 52.0, 'banana': 89.0}
        total = sum(foods.values())
        record_id = store_meal('user_123', foods, total)
        print(f"記錄已儲存，ID: {record_id}")
    
    未來擴展（MongoDB）:
        def store_meal_mongo(user_id: str, foods: Dict[str, float], 
                           calories: float, date: Optional[str] = None) -> str:
            '''儲存到 MongoDB'''
            with get_mongo_connection() as db:
                meals_collection = db['meals']
                
                # 準備文檔
                meal_doc = {
                    'user_id': user_id,
                    'date': date or datetime.now().isoformat(),
                    'foods': foods,  # MongoDB 原生支援 dict
                    'calories': calories,
                    'created_at': datetime.now()
                }
                
                # 插入文檔
                result = meals_collection.insert_one(meal_doc)
                
                return str(result.inserted_id)
    """
    # 參數驗證
    if not user_id:
        raise ValueError("user_id 不能為空")
    
    if not foods or not isinstance(foods, dict):
        raise ValueError("foods 必須是非空的字典")
    
    if calories < 0:
        raise ValueError("calories 不能為負數")
    
    # 如果沒有提供日期，使用當前時間
    if date is None:
        date = datetime.now().isoformat()
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 將 foods 字典轉換為 JSON 字串
            foods_json = json.dumps(foods, ensure_ascii=False)
            
            # 插入記錄
            cursor.execute("""
                INSERT INTO meals (user_id, date, foods, calories)
                VALUES (?, ?, ?, ?)
            """, (user_id, date, foods_json, calories))
            
            # 獲取新記錄的 ID
            record_id = cursor.lastrowid
            
            # 提交變更
            conn.commit()
            
            logger.info(f"已儲存飲食記錄: user_id={user_id}, calories={calories} kcal, record_id={record_id}")
            logger.debug(f"食物清單: {foods}")
            
            return record_id
            
    except sqlite3.Error as e:
        handle_error(e, f"儲存飲食記錄失敗: user_id={user_id}", logger=logger, raise_error=True)
    except json.JSONEncodeError as e:
        handle_error(e, f"食物資料 JSON 編碼失敗: {foods}", logger=logger, raise_error=True)


def get_history(user_id: str, 
                days: int = DEFAULT_HISTORY_DAYS) -> List[Tuple[int, str, Dict[str, float], float, str]]:
    """
    獲取用戶的飲食歷史記錄
    
    Args:
        user_id: 用戶唯一識別碼
        days: 查詢最近幾天的記錄，默認 7 天
    
    Returns:
        List[Tuple]: 記錄列表，每個元組包含：
            - id (int): 記錄 ID
            - date (str): 日期時間
            - foods (Dict[str, float]): 食物字典
            - calories (float): 總熱量
            - created_at (str): 創建時間
    
    Raises:
        sqlite3.Error: 資料庫查詢失敗
        ValueError: 參數驗證失敗
    
    使用範例:
        # 獲取最近 7 天的記錄
        history = get_history('user_123')
        for record_id, date, foods, calories, created_at in history:
            print(f"{date}: {calories} kcal")
            for food, cal in foods.items():
                print(f"  - {food}: {cal} kcal")
        
        # 獲取最近 30 天的記錄
        history = get_history('user_123', days=30)
    
    未來擴展（MongoDB）:
        def get_history_mongo(user_id: str, days: int = 7) -> List[Dict]:
            '''從 MongoDB 查詢歷史'''
            with get_mongo_connection() as db:
                meals_collection = db['meals']
                
                # 計算日期範圍
                start_date = datetime.now() - timedelta(days=days)
                
                # 查詢文檔
                cursor = meals_collection.find({
                    'user_id': user_id,
                    'date': {'$gte': start_date.isoformat()}
                }).sort('date', -1)  # 按日期降序排列
                
                # 轉換為列表
                return list(cursor)
    """
    # 參數驗證
    if not user_id:
        raise ValueError("user_id 不能為空")
    
    if days <= 0:
        raise ValueError("days 必須大於 0")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 計算起始日期
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 查詢記錄
            cursor.execute("""
                SELECT id, date, foods, calories, created_at
                FROM meals
                WHERE user_id = ? AND date >= ?
                ORDER BY date DESC
            """, (user_id, start_date))
            
            # 獲取所有結果
            rows = cursor.fetchall()
            
            # 解析 JSON 並轉換為元組列表
            results = []
            for row in rows:
                record_id = row['id']
                date = row['date']
                foods_json = row['foods']
                calories = row['calories']
                created_at = row['created_at']
                
                # 解析 JSON
                try:
                    foods = json.loads(foods_json)
                except json.JSONDecodeError as e:
                    logger.warning(f"記錄 {record_id} 的 foods JSON 解析失敗: {e}")
                    foods = {}
                
                results.append((record_id, date, foods, calories, created_at))
            
            logger.info(f"查詢歷史記錄: user_id={user_id}, days={days}, count={len(results)}")
            
            return results
            
    except sqlite3.Error as e:
        handle_error(e, f"查詢歷史記錄失敗: user_id={user_id}", logger=logger, raise_error=True)


def get_meal_by_id(meal_id: int) -> Optional[Tuple[int, str, str, Dict[str, float], float, str]]:
    """
    根據 ID 獲取單筆飲食記錄
    
    Args:
        meal_id: 記錄 ID
    
    Returns:
        Optional[Tuple]: 記錄元組或 None（如果不存在）
            - id (int): 記錄 ID
            - user_id (str): 用戶 ID
            - date (str): 日期時間
            - foods (Dict[str, float]): 食物字典
            - calories (float): 總熱量
            - created_at (str): 創建時間
    
    Raises:
        sqlite3.Error: 資料庫查詢失敗
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, date, foods, calories, created_at
                FROM meals
                WHERE id = ?
            """, (meal_id,))
            
            row = cursor.fetchone()
            
            if row is None:
                logger.debug(f"記錄不存在: meal_id={meal_id}")
                return None
            
            # 解析 JSON
            foods = json.loads(row['foods'])
            
            return (row['id'], row['user_id'], row['date'], 
                   foods, row['calories'], row['created_at'])
            
    except sqlite3.Error as e:
        handle_error(e, f"查詢記錄失敗: meal_id={meal_id}", logger=logger, raise_error=True)


def delete_meal(meal_id: int) -> bool:
    """
    刪除飲食記錄
    
    Args:
        meal_id: 要刪除的記錄 ID
    
    Returns:
        bool: 是否成功刪除（True=成功，False=記錄不存在）
    
    Raises:
        sqlite3.Error: 資料庫操作失敗
    
    未來擴展（MongoDB）:
        def delete_meal_mongo(meal_id: str) -> bool:
            '''從 MongoDB 刪除記錄'''
            from bson.objectid import ObjectId
            
            with get_mongo_connection() as db:
                meals_collection = db['meals']
                
                result = meals_collection.delete_one({
                    '_id': ObjectId(meal_id)
                })
                
                return result.deleted_count > 0
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                logger.info(f"已刪除記錄: meal_id={meal_id}")
            else:
                logger.debug(f"記錄不存在，無法刪除: meal_id={meal_id}")
            
            return deleted
            
    except sqlite3.Error as e:
        handle_error(e, f"刪除記錄失敗: meal_id={meal_id}", logger=logger, raise_error=True)


# ========== 統計與分析 ==========

def get_statistics(user_id: str, days: int = 7) -> Dict[str, Any]:
    """
    獲取用戶的飲食統計資訊
    
    Args:
        user_id: 用戶唯一識別碼
        days: 統計最近幾天的資料
    
    Returns:
        Dict: 統計資訊，包含：
            - total_meals: 總餐數
            - total_calories: 總熱量
            - avg_calories: 平均每餐熱量
            - most_common_foods: 最常吃的食物清單
    
    未來擴展：
    - 營養素分布分析
    - 飲食習慣趨勢
    - 健康建議生成
    """
    history = get_history(user_id, days)
    
    if not history:
        return {
            'total_meals': 0,
            'total_calories': 0.0,
            'avg_calories': 0.0,
            'most_common_foods': []
        }
    
    # 統計計算
    total_meals = len(history)
    total_calories = sum(record[3] for record in history)
    avg_calories = total_calories / total_meals if total_meals > 0 else 0.0
    
    # 食物出現次數統計
    food_counts = {}
    for record in history:
        foods = record[2]
        for food_name in foods.keys():
            food_counts[food_name] = food_counts.get(food_name, 0) + 1
    
    # 排序找出最常見的食物
    most_common_foods = sorted(
        food_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10]  # 取前 10 名
    
    logger.info(f"統計完成: user_id={user_id}, days={days}, meals={total_meals}")
    
    return {
        'total_meals': total_meals,
        'total_calories': total_calories,
        'avg_calories': avg_calories,
        'most_common_foods': most_common_foods
    }


# ========== 資料庫遷移工具 ==========

def export_to_json(output_path: Optional[Path] = None) -> str:
    """
    將資料庫匯出為 JSON 格式
    
    用於資料備份或遷移到其他資料庫系統。
    
    Args:
        output_path: 輸出檔案路徑，默認為 data/exports/meals_export_<timestamp>.json
    
    Returns:
        str: 輸出檔案的路徑
    
    未來用途：
    - 遷移到 MongoDB
    - 資料備份
    - 資料分析匯出
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = project_root / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        output_path = export_dir / f"meals_export_{timestamp}.json"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM meals ORDER BY date DESC")
            rows = cursor.fetchall()
            
            # 轉換為字典列表
            data = []
            for row in rows:
                record = {
                    'id': row['id'],
                    'user_id': row['user_id'],
                    'date': row['date'],
                    'foods': json.loads(row['foods']),
                    'calories': row['calories'],
                    'created_at': row['created_at']
                }
                data.append(record)
            
            # 寫入 JSON 檔案
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"資料已匯出: {output_path} ({len(data)} 筆記錄)")
            
            return str(output_path)
            
    except Exception as e:
        handle_error(e, "資料匯出失敗", logger=logger, raise_error=True)


# ========== 模組初始化 ==========

# 確保資料庫在模組載入時初始化
try:
    init_database()
except Exception as e:
    logger.error(f"資料庫初始化失敗: {e}")
    logger.warning("資料儲存功能可能無法正常運作")


# ========== 測試/除錯用函數 ==========

if __name__ == "__main__":
    """
    模組測試程式
    
    運行方式：
        python src/data_storage.py
    """
    # 設定日誌
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 60)
    logger.info("資料儲存模組測試")
    logger.info("=" * 60)
    
    # 測試用戶 ID
    test_user_id = "test_user_123"
    
    # 測試 1: 儲存記錄
    logger.info("\n測試 1: 儲存飲食記錄")
    test_foods = {
        'apple': 52.0,
        'banana': 89.0,
        'orange': 47.0
    }
    test_calories = sum(test_foods.values())
    
    record_id = store_meal(test_user_id, test_foods, test_calories)
    logger.info(f"✅ 記錄已儲存: ID={record_id}")
    
    # 測試 2: 查詢歷史
    logger.info("\n測試 2: 查詢歷史記錄")
    history = get_history(test_user_id, days=7)
    logger.info(f"✅ 找到 {len(history)} 筆記錄")
    
    for rec_id, date, foods, calories, created_at in history:
        logger.info(f"  ID {rec_id}: {date} - {calories} kcal")
        for food, cal in foods.items():
            logger.info(f"    • {food}: {cal} kcal")
    
    # 測試 3: 統計資訊
    logger.info("\n測試 3: 統計資訊")
    stats = get_statistics(test_user_id, days=7)
    logger.info(f"✅ 統計結果:")
    logger.info(f"  總餐數: {stats['total_meals']}")
    logger.info(f"  總熱量: {stats['total_calories']:.1f} kcal")
    logger.info(f"  平均熱量: {stats['avg_calories']:.1f} kcal")
    logger.info(f"  最常吃的食物: {stats['most_common_foods'][:3]}")
    
    logger.info("\n" + "=" * 60)
    logger.info("測試完成！")
    logger.info("=" * 60)
