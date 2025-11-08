#!/usr/bin/env python3
"""
Diet Tracker Bot - 資料儲存模組 (擴展版)
=====================================

負責處理用戶飲食記錄的儲存、查詢和統計功能。
使用 SQLite 作為 MVP 階段的資料庫，並提供 MongoDB 遷移路徑。

核心功能：
1. 用戶飲食記錄的 CRUD 操作（支援餐次類型和份量）
2. 歷史記錄查詢和統計（餐次相關分析）
3. 餐次智能檢索（前餐查詢、過去天數分析）
4. 資料匯出和備份
5. 資料庫初始化和管理

🚀 新增餐次功能：
- 餐次類型分類：breakfast, lunch, dinner, snack
- 份量記錄：支援自定義份量大小
- 餐次關聯查詢：同日前餐查詢、跨日分析
- 營養趨勢分析：按餐次和日期的統計功能

🔮 未來擴展準備（RAG 向量檢索）：
- 預留餐點描述欄位供 sentence-transformers 嵌入
- 語義相似餐點檢索（基於食物組合向量）
- 個人化餐點推薦（基於歷史偏好向量）
- 營養建議 RAG 檢索（基於營養狀態和目標向量）

設計原則：
- 使用事務確保資料一致性
- 提供詳細的錯誤處理和日誌記錄
- 支援未來的雲端資料庫遷移
- 優化查詢效能和索引設計
- 為 AI/RAG 功能預留擴展空間
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


def _migrate_add_meal_columns(cursor: sqlite3.Cursor) -> None:
    """
    向後相容遷移：為現有的 meals 表添加新欄位
    
    檢查表結構並添加遺失的欄位：
    - meal_type: 餐次類型（breakfast/lunch/dinner/snack）
    - portion_size: 份量大小，預設 100g
    
    Args:
        cursor: SQLite 資料庫游標
        
    Raises:
        sqlite3.Error: 添加欄位失敗
    """
    try:
        # 檢查現有欄位
        cursor.execute("PRAGMA table_info(meals)")
        existing_columns = {col[1] for col in cursor.fetchall()}
        
        # 添加 meal_type 欄位（如果不存在）
        if 'meal_type' not in existing_columns:
            cursor.execute("""
                ALTER TABLE meals 
                ADD COLUMN meal_type TEXT DEFAULT 'meal'
            """)
            logger.info("已添加 meal_type 欄位到現有資料庫")
            
        # 添加 portion_size 欄位（如果不存在）
        if 'portion_size' not in existing_columns:
            cursor.execute("""
                ALTER TABLE meals 
                ADD COLUMN portion_size REAL DEFAULT 100.0
            """)
            logger.info("已添加 portion_size 欄位到現有資料庫")
            
        logger.debug(f"資料庫遷移完成，現有欄位：{existing_columns}")
        
    except sqlite3.Error as e:
        handle_error(e, "資料庫遷移失敗", logger=logger, raise_error=True)


def init_database() -> None:
    """
    初始化資料庫結構（擴展版）
    
    創建必要的表格和索引。如果表格已存在則執行遷移添加新欄位。
    這個函數應該在應用程式啟動時執行一次。
    
    表結構 (擴展版):
    - meals: 用戶飲食記錄
        * id: INTEGER PRIMARY KEY (自動遞增)
        * user_id: TEXT (用戶唯一識別碼)
        * date: TEXT (ISO 8601 格式日期時間)
        * foods: TEXT (JSON 格式的食物清單)
        * calories: REAL (總熱量 kcal)
        * 🚀 meal_type: TEXT (餐次類型: breakfast, lunch, dinner, snack)
        * 🚀 portion_size: REAL DEFAULT 100 (份量大小，預設 100g)
        * created_at: TEXT (記錄創建時間)
    
    索引:
    - idx_meals_user_date: (user_id, date) 加速查詢
    - idx_meals_meal_type: (meal_type) 加速餐次查詢
    
    🔮 未來向量 RAG 擴展預留欄位：
    - meal_description: TEXT (餐點描述文字，供 sentence-transformers 嵌入)
    - embedding_vector: BLOB (向量嵌入，用於語義相似檢索)
    - nutrition_tags: TEXT (營養標籤 JSON，用於結構化檢索)
    
    Raises:
        sqlite3.Error: 資料庫初始化失敗
    
    未來擴展（MongoDB + Vector DB）:
        # MongoDB + Pinecone/Weaviate 向量檢索
        def init_mongodb_with_vectors():
            # 1. MongoDB 儲存結構化資料
            with get_mongo_connection() as db:
                meals_collection = db['meals']
                meals_collection.create_index([
                    ('user_id', 1), ('date', -1), ('meal_type', 1)
                ])
            
            # 2. 向量資料庫儲存嵌入
            import pinecone
            pinecone.create_index(
                name="meal-embeddings",
                dimension=384,  # sentence-transformers 維度
                metric="cosine"
            )
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 創建 meals 表（包含新欄位）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    foods TEXT NOT NULL,
                    calories REAL NOT NULL,
                    meal_type TEXT DEFAULT 'meal',
                    portion_size REAL DEFAULT 100.0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # 檢查並添加新欄位（向後相容遷移）
            _migrate_add_meal_columns(cursor)
            
            # 創建索引以加速查詢
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_meals_user_date 
                ON meals(user_id, date DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_meals_meal_type
                ON meals(meal_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_meals_user_type_date
                ON meals(user_id, meal_type, date DESC)
            """)
            
            # 提交變更
            conn.commit()
            
            logger.info("資料庫初始化完成（包含餐次功能）")
            logger.debug("已創建 meals 表和擴展索引")
            
    except sqlite3.Error as e:
        handle_error(e, "資料庫初始化失敗", logger=logger, raise_error=True)


# ========== CRUD 操作 ==========

def store_meal(user_id: str, 
               foods: Dict[str, float], 
               calories: float,
               date: Optional[str] = None,
               meal_type: Optional[str] = None,
               portion_size: Optional[float] = None) -> int:
    """
    儲存用戶的一餐飲食記錄（擴展版）
    
    Args:
        user_id: 用戶唯一識別碼（Discord User ID 或其他）
        foods: 食物字典 {食物名稱: 熱量}，例如 {'apple': 52.0, 'banana': 89.0}
        calories: 總熱量（kcal）
        date: 可選的日期時間字串（ISO 8601 格式），默認為當前時間
        🚀 meal_type: 餐次類型 ('breakfast', 'lunch', 'dinner', 'snack')，預設 'meal'
        🚀 portion_size: 份量大小（克），預設 100.0g
    
    Returns:
        int: 新記錄的 ID
    
    Raises:
        sqlite3.Error: 資料庫操作失敗
        ValueError: 參數驗證失敗
    
    使用範例:
        # 基本用法（向後相容）
        foods = {'apple': 52.0, 'banana': 89.0}
        total = sum(foods.values())
        record_id = store_meal('user_123', foods, total)
        
        # 新功能：指定餐次和份量
        breakfast_foods = {'oatmeal': 150.0, 'milk': 60.0}
        breakfast_calories = sum(breakfast_foods.values())
        record_id = store_meal(
            user_id='user_123',
            foods=breakfast_foods,
            calories=breakfast_calories,
            meal_type='breakfast',
            portion_size=200.0  # 200g
        )
        print(f"早餐記錄已儲存，ID: {record_id}")
    
    未來擴展（MongoDB + Vector RAG）:
        def store_meal_mongo_with_embedding(user_id: str, foods: Dict[str, float], 
                                          calories: float, meal_type: str = 'meal',
                                          meal_description: str = None) -> str:
            '''儲存到 MongoDB + 向量嵌入'''
            from sentence_transformers import SentenceTransformer
            
            # 1. 儲存結構化資料到 MongoDB
            with get_mongo_connection() as db:
                meals_collection = db['meals']
                
                meal_doc = {
                    'user_id': user_id,
                    'date': datetime.now().isoformat(),
                    'foods': foods,
                    'calories': calories,
                    'meal_type': meal_type,
                    'portion_size': portion_size,
                    'meal_description': meal_description,
                    'created_at': datetime.now()
                }
                
                result = meals_collection.insert_one(meal_doc)
                meal_id = str(result.inserted_id)
                
                # 2. 生成向量嵌入（用於語義檢索）
                if meal_description:
                    model = SentenceTransformer('all-MiniLM-L6-v2')
                    embedding = model.encode(meal_description)
                    
                    # 3. 儲存向量到 Pinecone/Weaviate
                    import pinecone
                    index = pinecone.Index("meal-embeddings")
                    index.upsert([(meal_id, embedding.tolist(), {
                        'user_id': user_id,
                        'meal_type': meal_type,
                        'calories': calories
                    })])
                
                return meal_id
    """
    # 參數驗證
    if not user_id:
        raise ValueError("user_id 不能為空")
    
    if not foods or not isinstance(foods, dict):
        raise ValueError("foods 必須是非空的字典")
    
    if calories < 0:
        raise ValueError("calories 不能為負數")
        
    # 餐次類型驗證
    valid_meal_types = {'breakfast', 'lunch', 'dinner', 'snack', 'meal'}
    if meal_type and meal_type not in valid_meal_types:
        raise ValueError(f"meal_type 必須是 {valid_meal_types} 之一，收到: {meal_type}")
    
    # 份量驗證
    if portion_size is not None and portion_size <= 0:
        raise ValueError("portion_size 必須大於 0")
    
    # 預設值設定
    if date is None:
        date = datetime.now().isoformat()
    if meal_type is None:
        meal_type = 'meal'
    if portion_size is None:
        portion_size = 100.0
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 將 foods 字典轉換為 JSON 字串
            foods_json = json.dumps(foods, ensure_ascii=False)
            
            # 插入記錄（包含新欄位）
            cursor.execute("""
                INSERT INTO meals (user_id, date, foods, calories, meal_type, portion_size)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, date, foods_json, calories, meal_type, portion_size))
            
            # 獲取新記錄的 ID
            record_id = cursor.lastrowid
            
            # 提交變更
            conn.commit()
            
            logger.info(f"已儲存飲食記錄: user_id={user_id}, meal_type={meal_type}, "
                       f"calories={calories} kcal, portion={portion_size}g, record_id={record_id}")
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


def get_meal_by_id(meal_id: int) -> Optional[Tuple[int, str, str, Dict[str, float], float, str, str, float]]:
    """
    根據 ID 獲取單筆飲食記錄（擴展版）
    
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
            🚀 - meal_type (str): 餐次類型
            🚀 - portion_size (float): 份量大小
    
    Raises:
        sqlite3.Error: 資料庫查詢失敗
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, date, foods, calories, created_at, meal_type, portion_size
                FROM meals
                WHERE id = ?
            """, (meal_id,))
            
            row = cursor.fetchone()
            
            if row is None:
                logger.debug(f"記錄不存在: meal_id={meal_id}")
                return None
            
            # 解析 JSON
            foods = json.loads(row['foods'])
            
            return (
                row['id'], 
                row['user_id'], 
                row['date'], 
                foods, 
                row['calories'], 
                row['created_at'],
                row['meal_type'] or 'meal',
                row['portion_size'] or 100.0
            )
            
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


# ========== 新增：餐次查詢功能 ==========

def get_previous_meals(user_id: str, current_meal_type: str) -> List[Tuple[int, str, Dict[str, float], float, float, str]]:
    """
    獲取用戶今日指定餐次類型之前的所有餐點
    
    用途：智慧營養建議，例如晚餐前查看已吃的早餐和午餐，計算剩餘熱量需求
    
    Args:
        user_id: 用戶唯一識別碼
        current_meal_type: 當前餐次類型 ('breakfast', 'lunch', 'dinner', 'snack')
    
    Returns:
        List[Tuple]: 餐點記錄列表，每個元組包含：
            - id (int): 記錄 ID
            - date (str): 日期時間
            - foods (Dict[str, float]): 食物字典
            - calories (float): 總熱量
            - portion_size (float): 份量大小
            - meal_type (str): 餐次類型
    
    Raises:
        sqlite3.Error: 資料庫查詢失敗
        ValueError: 參數驗證失敗
    
    使用範例:
        # 晚餐前查看今日已吃的餐點
        previous_meals = get_previous_meals('user_123', 'dinner')
        total_calories_today = sum(meal[3] for meal in previous_meals)
        print(f"今日已攝取: {total_calories_today} kcal")
        
        # 午餐時查看早餐
        breakfast_meals = get_previous_meals('user_123', 'lunch')
    
    🔮 未來 RAG 擴展：
        # 結合向量檢索推薦
        def get_previous_meals_with_recommendations(user_id: str, current_meal_type: str):
            previous = get_previous_meals(user_id, current_meal_type)
            
            # 使用向量檢索找相似的成功營養搭配
            similar_patterns = search_meal_patterns_by_similarity(
                user_meals=previous,
                target_meal_type=current_meal_type
            )
            
            return {
                'previous_meals': previous,
                'recommendations': similar_patterns
            }
    """
    # 參數驗證
    if not user_id:
        raise ValueError("user_id 不能為空")
    
    valid_meal_types = {'breakfast', 'lunch', 'dinner', 'snack'}
    if current_meal_type not in valid_meal_types:
        raise ValueError(f"current_meal_type 必須是 {valid_meal_types} 之一")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 獲取今日開始時間
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            
            # 定義餐次順序
            meal_order = {'breakfast': 1, 'lunch': 2, 'dinner': 3, 'snack': 4}
            current_order = meal_order.get(current_meal_type, 999)
            
            # 查詢今日之前餐次的記錄
            cursor.execute("""
                SELECT id, date, foods, calories, portion_size, meal_type
                FROM meals
                WHERE user_id = ? 
                AND date >= ?
                AND meal_type IN (
                    SELECT meal_type FROM (
                        SELECT 'breakfast' as meal_type, 1 as sort_order
                        UNION SELECT 'lunch', 2
                        UNION SELECT 'dinner', 3  
                        UNION SELECT 'snack', 4
                    ) meal_types
                    WHERE sort_order < ?
                )
                ORDER BY date ASC
            """, (user_id, today_start, current_order))
            
            # 獲取所有結果並解析
            rows = cursor.fetchall()
            results = []
            
            for row in rows:
                try:
                    foods = json.loads(row['foods'])
                    results.append((
                        row['id'], 
                        row['date'], 
                        foods,
                        row['calories'], 
                        row['portion_size'] or 100.0,
                        row['meal_type']
                    ))
                except json.JSONDecodeError as e:
                    logger.warning(f"記錄 {row['id']} 的 foods JSON 解析失敗: {e}")
            
            logger.info(f"查詢今日前序餐點: user_id={user_id}, meal_type={current_meal_type}, count={len(results)}")
            
            return results
            
    except sqlite3.Error as e:
        handle_error(e, f"查詢前序餐點失敗: user_id={user_id}", logger=logger, raise_error=True)


def get_past_days(user_id: str, days: int = 3) -> Dict[str, Any]:
    """
    獲取用戶過去 N 天的飲食模式和營養趨勢分析
    
    用途：營養趨勢分析、飲食習慣洞察、個性化建議基礎
    
    Args:
        user_id: 用戶唯一識別碼
        days: 查詢天數，預設 3 天
    
    Returns:
        Dict[str, Any]: 包含以下分析結果
            - daily_summaries: 每日摘要 List[Dict]
            - meal_type_stats: 餐次統計 Dict[str, float]
            - nutrition_trends: 營養趨勢 Dict[str, List[float]]
            - average_portion: 平均份量
            - total_meals: 總餐次數
            - recommendations: 改善建議
    
    Raises:
        sqlite3.Error: 資料庫查詢失敗
        ValueError: 參數驗證失敗
    
    使用範例:
        # 分析最近 3 天飲食
        analysis = get_past_days('user_123', days=3)
        print(f"平均每日熱量: {analysis['nutrition_trends']['avg_daily_calories']} kcal")
        print(f"最常見餐次: {analysis['meal_type_stats']}")
        
        # 一週趨勢分析
        weekly = get_past_days('user_123', days=7)
    
    🔮 未來 RAG 機器學習擴展：
        def get_past_days_with_ml_insights(user_id: str, days: int = 7):
            # 1. 獲取基本統計
            basic_stats = get_past_days(user_id, days)
            
            # 2. 使用 ML 模型預測趨勢
            from sklearn.linear_model import LinearRegression
            nutrition_predictor = LinearRegression()
            # ... 訓練模型預測未來營養需求
            
            # 3. 向量檢索相似用戶模式
            similar_users = find_similar_nutrition_patterns(basic_stats)
            
            # 4. 生成個性化建議
            ai_recommendations = generate_personalized_suggestions(
                user_history=basic_stats,
                similar_patterns=similar_users
            )
            
            return {
                **basic_stats,
                'ml_predictions': nutrition_predictor.predict(...),
                'ai_recommendations': ai_recommendations
            }
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
            
            # 查詢指定天數內的所有記錄
            cursor.execute("""
                SELECT id, date, foods, calories, meal_type, portion_size, created_at
                FROM meals
                WHERE user_id = ? AND date >= ?
                ORDER BY date DESC
            """, (user_id, start_date))
            
            rows = cursor.fetchall()
            
            # 初始化分析資料
            daily_summaries = {}
            meal_type_totals = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0, 'meal': 0}
            daily_calories = []
            daily_portions = []
            total_meals = len(rows)
            
            # 處理每筆記錄
            for row in rows:
                date_str = row['date'][:10]  # 取日期部分 YYYY-MM-DD
                meal_type = row['meal_type'] or 'meal'
                calories = row['calories']
                portion_size = row['portion_size'] or 100.0
                
                # 解析食物 JSON
                try:
                    foods = json.loads(row['foods'])
                except json.JSONDecodeError:
                    foods = {}
                
                # 日期分組統計
                if date_str not in daily_summaries:
                    daily_summaries[date_str] = {
                        'date': date_str,
                        'total_calories': 0,
                        'meals': [],
                        'meal_types': {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'snack': 0, 'meal': 0}
                    }
                
                daily_summaries[date_str]['total_calories'] += calories
                daily_summaries[date_str]['meal_types'][meal_type] += 1
                daily_summaries[date_str]['meals'].append({
                    'id': row['id'],
                    'meal_type': meal_type,
                    'foods': foods,
                    'calories': calories,
                    'portion_size': portion_size
                })
                
                # 累積統計
                meal_type_totals[meal_type] += 1
                daily_portions.append(portion_size)
            
            # 計算每日熱量
            daily_calories = [day_data['total_calories'] for day_data in daily_summaries.values()]
            
            # 計算營養趨勢
            nutrition_trends = {
                'daily_calories': daily_calories,
                'avg_daily_calories': sum(daily_calories) / len(daily_calories) if daily_calories else 0,
                'max_daily_calories': max(daily_calories) if daily_calories else 0,
                'min_daily_calories': min(daily_calories) if daily_calories else 0,
                'calorie_variance': _calculate_variance(daily_calories) if len(daily_calories) > 1 else 0
            }
            
            # 餐次統計百分比
            if total_meals > 0:
                meal_type_stats = {
                    meal_type: (count / total_meals) * 100 
                    for meal_type, count in meal_type_totals.items() 
                    if count > 0
                }
            else:
                meal_type_stats = {}
            
            # 平均份量
            average_portion = sum(daily_portions) / len(daily_portions) if daily_portions else 100.0
            
            # 生成改善建議
            recommendations = _generate_nutrition_recommendations(
                daily_summaries, nutrition_trends, meal_type_stats
            )
            
            result = {
                'daily_summaries': list(daily_summaries.values()),
                'meal_type_stats': meal_type_stats,
                'nutrition_trends': nutrition_trends,
                'average_portion': round(average_portion, 1),
                'total_meals': total_meals,
                'analysis_period_days': days,
                'recommendations': recommendations
            }
            
            logger.info(f"完成過去 {days} 天飲食分析: user_id={user_id}, meals={total_meals}")
            
            return result
            
    except sqlite3.Error as e:
        handle_error(e, f"分析過去飲食失敗: user_id={user_id}", logger=logger, raise_error=True)


def _calculate_variance(numbers: List[float]) -> float:
    """計算數值變異數"""
    if len(numbers) < 2:
        return 0
    mean = sum(numbers) / len(numbers)
    return sum((x - mean) ** 2 for x in numbers) / len(numbers)


def _generate_nutrition_recommendations(daily_summaries: Dict, trends: Dict, meal_stats: Dict) -> List[str]:
    """根據飲食分析生成個性化建議"""
    recommendations = []
    
    avg_calories = trends['avg_daily_calories']
    calorie_variance = trends['calorie_variance']
    
    # 熱量建議
    if avg_calories < 1200:
        recommendations.append("⚠️  平均熱量偏低，建議增加營養豐富的食物")
    elif avg_calories > 2500:
        recommendations.append("⚠️  平均熱量偏高，可考慮減少份量或選擇低熱量食物")
    
    # 穩定性建議
    if calorie_variance > 100000:  # 高變異
        recommendations.append("📊 熱量攝取變化較大，建議保持規律飲食")
    
    # 餐次建議
    if meal_stats.get('breakfast', 0) < 20:
        recommendations.append("🌅 建議增加早餐頻率，早餐有助於穩定血糖")
    
    if meal_stats.get('snack', 0) > 40:
        recommendations.append("🍎 點心較多，可考慮用正餐替代部分零食")
    
    # 預設建議
    if not recommendations:
        recommendations.append("✅ 飲食模式良好，繼續保持！")
    
    return recommendations


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
