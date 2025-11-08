"""
Diet Tracker Bot - 共用工具函數
==============================

提供整個專案共用的工具函數，包括錯誤處理、日誌配置等基礎功能。

設計原則：
- 函數應該是純函數或副作用最小
- 提供詳細的錯誤信息和日誌
- 支援未來擴展和配置
"""

import logging
import traceback
from typing import Any, Optional, Callable, Union
from functools import wraps
import os
from pathlib import Path
from datetime import datetime, timedelta

# ========== 簡易快取系統 (MVP) ==========
# 全域字典快取，用於暫存常見食物的營養資訊
# 
# 設計說明：
# - MVP 階段使用記憶體內的 dict 快取
# - 鍵值: 食物名稱 (小寫)
# - 值: {'calories': float, 'timestamp': datetime, 'source': str}
#
# 未來擴展計畫：
# 1. 使用 Redis 替換記憶體快取 (支援分散式部署)
# 2. 實作 TTL (Time-To-Live) 自動過期機制
# 3. LRU (Least Recently Used) 快取淘汰策略
# 4. 快取統計與監控 (命中率、大小等)
# 5. 持久化快取到資料庫
#
# Redis 遷移範例:
# import redis
# cache = redis.Redis(host='localhost', port=6379, db=0)
# cache.setex(f'nutrition:{food_name}', 3600, json.dumps(nutrition_data))

_NUTRITION_CACHE: dict = {}

# 快取設定
CACHE_TTL_HOURS = 24  # 快取有效期（小時）
CACHE_MAX_SIZE = 1000  # 最大快取項目數

def setup_logging(log_level: str = "INFO", 
                  log_format: Optional[str] = None,
                  enable_file_logging: bool = True,
                  module_name: str = __name__) -> logging.Logger:
    """
    設定並配置日誌系統
    
    Args:
        log_level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 自定義日誌格式
        enable_file_logging: 是否啟用檔案日誌記錄
    
    Returns:
        logging.Logger: 配置好的日誌器
    
    未來擴展：
    - 支援遠端日誌服務（如ELK Stack）
    - 添加日誌輪轉功能
    - 支援結構化日誌（JSON格式）
    """
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 設定基本日誌配置
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(__name__)
    
    # 如果啟用檔案日誌
    if enable_file_logging:
        project_root = Path(__file__).parent.parent
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(
            log_dir / "diet_tracker_bot.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
        
        logger.info("檔案日誌記錄已啟用")
    
    return logger

def handle_error(error: Exception, 
                 context: str = "",
                 logger: Optional[logging.Logger] = None,
                 raise_error: bool = True,
                 default_return: Any = None) -> Any:
    """
    統一的錯誤處理函數
    
    Args:
        error: 捕獲的例外
        context: 錯誤發生的上下文描述
        logger: 日誌器實例，如果為None則創建新的
        raise_error: 是否重新拋出例外
        default_return: 如果不拋出例外，返回的預設值
    
    Returns:
        Any: 如果不拋出例外，返回default_return
    
    Raises:
        Exception: 如果raise_error為True，重新拋出原例外
    
    使用範例：
        try:
            result = risky_operation()
        except Exception as e:
            return handle_error(e, "執行危險操作時", raise_error=False, default_return={})
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    # 建構錯誤訊息
    error_msg = f"錯誤發生"
    if context:
        error_msg += f" - {context}"
    error_msg += f": {str(error)}"
    
    # 記錄錯誤
    logger.error(error_msg)
    
    # 記錄詳細的堆疊追蹤（僅在DEBUG級別）
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"詳細錯誤堆疊:\n{traceback.format_exc()}")
    
    if raise_error:
        raise error
    else:
        logger.info(f"錯誤已處理，返回預設值: {default_return}")
        return default_return

def retry_on_failure(max_retries: int = 3, 
                     delay: float = 1.0,
                     exponential_backoff: bool = True) -> Callable:
    """
    重試裝飾器 - 在函數失敗時自動重試
    
    Args:
        max_retries: 最大重試次數
        delay: 重試間隔時間（秒）
        exponential_backoff: 是否使用指數退避策略
    
    Returns:
        Callable: 裝飾器函數
    
    使用範例：
        @retry_on_failure(max_retries=3, delay=2.0)
        def call_external_api():
            # API呼叫邏輯
            pass
    
    未來擴展：
    - 支援特定例外類型的重試
    - 添加重試回調函數
    - 支援非同步函數
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(func.__module__)
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"函數 {func.__name__} 在 {max_retries} 次重試後仍然失敗")
                        raise e
                    
                    wait_time = delay * (2 ** attempt if exponential_backoff else 1)
                    logger.warning(f"函數 {func.__name__} 第 {attempt + 1} 次執行失敗，{wait_time} 秒後重試: {str(e)}")
                    
                    import time
                    time.sleep(wait_time)
            
        return wrapper
    return decorator

def validate_environment_variable(var_name: str, 
                                  required: bool = True,
                                  default_value: Optional[str] = None) -> Optional[str]:
    """
    驗證並獲取環境變數
    
    Args:
        var_name: 環境變數名稱
        required: 是否為必要變數
        default_value: 預設值（如果變數不存在）
    
    Returns:
        Optional[str]: 環境變數值或預設值
    
    Raises:
        ValueError: 如果必要變數不存在且無預設值
    """
    value = os.getenv(var_name, default_value)
    
    if required and value is None:
        raise ValueError(f"必要的環境變數 '{var_name}' 未設定")
    
    return value

def safe_json_load(json_str: str, 
                   default_value: Any = None,
                   logger: Optional[logging.Logger] = None) -> Any:
    """
    安全的JSON解析函數
    
    Args:
        json_str: JSON字串
        default_value: 解析失敗時的預設值
        logger: 日誌器實例
    
    Returns:
        Any: 解析後的對象或預設值
    """
    import json
    
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"JSON解析失敗: {str(e)}")
        return default_value

def format_file_size(size_bytes: int) -> str:
    """
    格式化檔案大小為人類可讀的格式
    
    Args:
        size_bytes: 檔案大小（位元組）
    
    Returns:
        str: 格式化的檔案大小字串
    
    範例：
        format_file_size(1024) -> "1.0 KB"
        format_file_size(1048576) -> "1.0 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def save_temp_image(image_data, filename: str = "temp.jpg") -> str:
    """
    保存臨時圖像檔案
    
    將處理後的圖像數據保存到temp目錄，用於偵錯和臨時儲存。
    這個函數確保temp目錄存在，並提供安全的檔案寫入。
    
    Args:
        image_data: 圖像數據（numpy array 或 bytes）
        filename (str): 檔案名稱，預設為 "temp.jpg"
    
    Returns:
        str: 保存的檔案完整路徑
    
    Raises:
        ValueError: 如果image_data格式不支援
        IOError: 如果檔案寫入失敗
    
    使用範例:
        import cv2
        image = cv2.imread("input.jpg")
        temp_path = save_temp_image(image, "processed_image.jpg")
        print(f"圖像已保存到: {temp_path}")
    
    未來擴展：
    - 支援多種圖像格式 (PNG, WEBP等)
    - 自動檔案名稱生成（時間戳）
    - 圖像壓縮選項
    - 雲端儲存整合
    """
    import cv2
    import numpy as np
    
    # 確保temp目錄存在
    project_root = Path(__file__).parent.parent
    temp_dir = project_root / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    # 建構完整檔案路徑
    file_path = temp_dir / filename
    
    logger = logging.getLogger(__name__)
    
    try:
        # 處理不同類型的圖像數據
        if isinstance(image_data, np.ndarray):
            # OpenCV numpy array 格式
            logger.debug(f"保存numpy array圖像，形狀: {image_data.shape}")
            success = cv2.imwrite(str(file_path), image_data)
            if not success:
                raise IOError(f"cv2.imwrite 失敗，無法保存到 {file_path}")
                
        elif isinstance(image_data, bytes):
            # 二進制圖像數據
            logger.debug(f"保存二進制圖像數據，大小: {len(image_data)} bytes")
            with open(file_path, 'wb') as f:
                f.write(image_data)
                
        else:
            # 不支援的數據類型
            raise ValueError(f"不支援的圖像數據類型: {type(image_data)}")
        
        # 驗證檔案是否成功保存
        if not file_path.exists():
            raise IOError(f"檔案保存失敗，檔案不存在: {file_path}")
        
        file_size = file_path.stat().st_size
        logger.debug(f"圖像成功保存: {file_path} ({format_file_size(file_size)})")
        
        return str(file_path)
        
    except Exception as e:
        error_msg = f"保存臨時圖像失敗: {filename}"
        logger.error(f"{error_msg} - {str(e)}")
        raise IOError(f"{error_msg}") from e

def create_project_directories() -> None:
    """
    確保專案所需的目錄結構存在
    
    這個函數檢查並創建所有必要的目錄，
    包括臨時檔案目錄、日誌目錄等。
    
    未來擴展：
    - 支援自定義目錄結構
    - 添加目錄權限檢查
    - 支援雲端儲存目錄
    """
    project_root = Path(__file__).parent.parent
    
    directories = [
        project_root / "logs",
        project_root / "temp",
        project_root / "data" / "cache",
        project_root / "data" / "exports"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(__name__)
    logger.debug(f"確保項目目錄結構完整: {[str(d) for d in directories]}")

def get_cached_nutrition(food_name: str) -> Optional[float]:
    """
    從快取中獲取食物的營養資訊
    
    Args:
        food_name: 食物名稱（會自動轉為小寫）
    
    Returns:
        Optional[float]: 熱量值（kcal），如果不在快取中或已過期則返回 None
    
    使用範例：
        calories = get_cached_nutrition('apple')
        if calories is None:
            calories = query_from_database('apple')
            set_cached_nutrition('apple', calories)
    
    未來擴展：
    - 支援多種營養素（蛋白質、脂肪、碳水）
    - Redis 快取整合
    - 快取預熱機制
    """
    global _NUTRITION_CACHE
    
    cache_key = food_name.lower()
    logger = logging.getLogger(__name__)
    
    if cache_key in _NUTRITION_CACHE:
        cached_data = _NUTRITION_CACHE[cache_key]
        
        # 檢查快取是否過期
        cache_age = datetime.now() - cached_data['timestamp']
        if cache_age < timedelta(hours=CACHE_TTL_HOURS):
            logger.debug(f"快取命中: {food_name} = {cached_data['calories']} kcal "
                        f"(來源: {cached_data['source']}, "
                        f"已快取 {cache_age.seconds // 3600} 小時)")
            return cached_data['calories']
        else:
            # 快取已過期，移除
            logger.debug(f"快取過期: {food_name} (已超過 {CACHE_TTL_HOURS} 小時)")
            del _NUTRITION_CACHE[cache_key]
    
    logger.debug(f"快取未命中: {food_name}")
    return None

def set_cached_nutrition(food_name: str, calories: float, source: str = 'unknown') -> None:
    """
    將食物營養資訊存入快取
    
    Args:
        food_name: 食物名稱（會自動轉為小寫）
        calories: 熱量值（kcal）
        source: 資料來源（如 'TFND', 'USDA', 'cache'）
    
    說明：
    - 如果快取已滿，會自動清理最舊的項目
    - 每次設定都會更新時間戳
    
    未來擴展：
    - LRU 淘汰策略
    - 快取大小監控
    - 批次寫入 Redis
    """
    global _NUTRITION_CACHE
    
    cache_key = food_name.lower()
    logger = logging.getLogger(__name__)
    
    # 檢查快取大小限制
    if len(_NUTRITION_CACHE) >= CACHE_MAX_SIZE:
        # 簡易清理策略：移除最舊的項目
        # 未來可改為 LRU 策略
        oldest_key = min(_NUTRITION_CACHE.keys(), 
                        key=lambda k: _NUTRITION_CACHE[k]['timestamp'])
        del _NUTRITION_CACHE[oldest_key]
        logger.debug(f"快取已滿，移除最舊項目: {oldest_key}")
    
    # 存入快取
    _NUTRITION_CACHE[cache_key] = {
        'calories': calories,
        'timestamp': datetime.now(),
        'source': source
    }
    
    logger.debug(f"快取已更新: {food_name} = {calories} kcal (來源: {source})")

def get_cache_stats() -> dict:
    """
    獲取快取統計資訊
    
    Returns:
        dict: 包含快取大小、命中率等統計資訊
    
    未來擴展：
    - 命中率計算
    - 記憶體使用統計
    - 快取效能監控
    """
    global _NUTRITION_CACHE
    
    return {
        'size': len(_NUTRITION_CACHE),
        'max_size': CACHE_MAX_SIZE,
        'ttl_hours': CACHE_TTL_HOURS,
        'items': list(_NUTRITION_CACHE.keys())
    }

def clear_cache() -> None:
    """
    清空所有快取
    
    使用場景：
    - 測試環境重置
    - 手動刷新資料
    - 記憶體清理
    """
    global _NUTRITION_CACHE
    
    _NUTRITION_CACHE.clear()
    logger = logging.getLogger(__name__)
    logger.info("快取已清空")

# ========== 全面日誌輔助函數 ==========

def log_function_call(func_name: str, args: dict = None, logger: logging.Logger = None):
    """記錄函數呼叫"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    args_str = f" with args: {args}" if args else ""
    logger.info(f"🔧 呼叫函數: {func_name}{args_str}")

def log_step_start(step_name: str, details: str = "", logger: logging.Logger = None):
    """記錄步驟開始"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    details_str = f" - {details}" if details else""
    logger.info(f"▶️  開始步驟: {step_name}{details_str}")

def log_step_success(step_name: str, result: Any = None, logger: logging.Logger = None):
    """記錄步驟成功"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    result_str = f" -> {result}" if result is not None else ""
    logger.info(f"✅ 步驟完成: {step_name}{result_str}")

def log_step_error(step_name: str, error: Exception, logger: logging.Logger = None):
    """記錄步驟錯誤"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.error(f"❌ 步驟失敗: {step_name} - {str(error)}")

def log_food_recognition(foods: list, confidence: float = None, logger: logging.Logger = None):
    """記錄食物識別結果"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    foods_str = "、".join(foods) if foods else "無"
    confidence_str = f" (信心度: {confidence:.2f})" if confidence else ""
    logger.info(f"🔍 識別食物: {foods_str}{confidence_str}")

def log_nutrition_calculation(food: str, calories: float, logger: logging.Logger = None):
    """記錄營養計算"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info(f"📊 營養計算: {food} -> {calories:.1f} kcal")

def log_data_storage(user_id: str, meal_id: int, total_calories: float, logger: logging.Logger = None):
    """記錄資料儲存"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info(f"💾 儲存餐點: 用戶 {user_id}, 餐點 #{meal_id}, 總熱量 {total_calories:.1f} kcal")

def log_ai_recommendation(user_id: str, recommendation_length: int, source: str = "AI", logger: logging.Logger = None):
    """記錄AI推薦"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info(f"🤖 生成推薦: 用戶 {user_id}, 來源 {source}, 長度 {recommendation_length} 字元")

def log_discord_interaction(user_id: str, command: str, success: bool = True, logger: logging.Logger = None):
    """記錄Discord互動"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    status = "成功" if success else "失敗"
    logger.info(f"💬 Discord 互動: 用戶 {user_id}, 命令 {command}, 狀態 {status}")

def log_performance_metric(operation: str, duration: float, logger: logging.Logger = None):
    """記錄性能指標"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info(f"⚡ 性能指標: {operation} 耗時 {duration:.2f} 秒")

def log_cache_operation(operation: str, key: str, hit: bool = None, logger: logging.Logger = None):
    """記錄快取操作"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if hit is not None:
        result = "命中" if hit else "未命中"
        logger.info(f"🗃️  快取 {result}: {operation} -> {key}")
    else:
        logger.info(f"🗃️  快取操作: {operation} -> {key}")

# ========== RAG 檢索結果格式化 ==========

def format_retrieved_text(previous_meals: list, 
                          past_analysis: Optional[dict] = None,
                          days: int = 7) -> str:
    """
    格式化 RAG 檢索結果為結構化文本
    
    將從資料庫檢索的歷史記錄和統計分析格式化為
    易於 LLM 理解的結構化文本，用於 prompt 增強。
    
    Args:
        previous_meals: 前序餐點列表 (來自 get_previous_meals)
        past_analysis: 過去幾天的分析資料 (來自 get_past_days)
        days: 分析天數
    
    Returns:
        str: 格式化的檢索結果文本
    
    文本格式範例:
        ```
        飲食歷史檢索結果：
        
        今日前序餐點：
        1. 早餐 (07:30): 蛋餅(250 kcal), 豆漿(150 kcal) - 總計 400 kcal
        2. 午餐 (12:15): 雞腿便當(650 kcal) - 總計 650 kcal
        今日已攝取總熱量：1050 kcal
        
        過去 7 天飲食統計：
        - 總餐數：21 餐
        - 平均每日熱量：1850 kcal
        - 最高每日熱量：2200 kcal
        - 最低每日熱量：1500 kcal
        - 最常吃的食物：白米飯(12次), 雞胸肉(8次), 花椰菜(6次)
        ```
    
    未來擴展 (註解):
        使用向量嵌入進行語義相似度篩選：
        
        ```python
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        # 初始化多語言模型
        model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        
        # 生成當前查詢的嵌入
        query_text = f"建議下一餐吃什麼"
        query_embedding = model.encode([query_text])[0]
        
        # 為每筆歷史記錄生成嵌入
        history_texts = [
            f"{meal['meal_type']} {list(meal['foods'].keys())}"
            for meal in previous_meals
        ]
        history_embeddings = model.encode(history_texts)
        
        # 計算 cosine 相似度
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            history_embeddings
        )[0]
        
        # 篩選最相關的 top-k 記錄
        top_k = 5
        top_indices = np.argsort(similarities)[-top_k:]
        relevant_meals = [previous_meals[i] for i in top_indices]
        
        # 只格式化最相關的記錄
        return format_relevant_meals(relevant_meals)
        ```
        
        使用 FAISS 加速向量檢索：
        
        ```python
        import faiss
        
        # 建立向量索引
        dimension = 512  # 嵌入維度
        index = faiss.IndexFlatL2(dimension)
        
        # 添加歷史記錄嵌入到索引
        index.add(history_embeddings)
        
        # 快速檢索最相似的 k 個記錄
        D, I = index.search(query_embedding.reshape(1, -1), k=5)
        relevant_meals = [previous_meals[idx] for idx in I[0]]
        ```
    """
    logger = logging.getLogger(__name__)
    
    # 初始化輸出文本
    output = "飲食歷史檢索結果：\n\n"
    
    # ===== 格式化前序餐點 =====
    if previous_meals and len(previous_meals) > 0:
        output += "今日前序餐點：\n"
        
        total_today_calories = 0.0
        
        # 餐次類型中文映射
        meal_type_zh = {
            'breakfast': '早餐',
            'lunch': '午餐',
            'dinner': '晚餐',
            'snack': '點心',
            'latenight': '宵夜',
            'other': '其他',
            'meal': '餐點'
        }
        
        for idx, meal in enumerate(previous_meals, 1):
            try:
                # 解析餐點資料 (根據 get_previous_meals 回傳格式)
                # Tuple structure: (id, date, foods, calories, portion_size, meal_type)
                meal_id = meal[0]
                date_str = meal[1]
                foods = meal[2]  # Dict[str, float]
                calories = meal[3]  # float
                portion_size = meal[4]  # float
                meal_type = meal[5]  # str
                
                # 解析時間
                try:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    time_str = date_obj.strftime("%H:%M")
                except:
                    time_str = "未知時間"
                
                # 餐次名稱
                meal_name = meal_type_zh.get(meal_type, meal_type)
                
                # 格式化食物清單
                foods_str = ", ".join([f"{name}({cal:.1f} kcal)" for name, cal in foods.items()])
                
                output += f"{idx}. {meal_name} ({time_str}): {foods_str} - 總計 {calories:.1f} kcal\n"
                total_today_calories += calories
                
            except Exception as e:
                logger.warning(f"格式化餐點資料時發生錯誤: {e}")
                continue
        
        output += f"今日已攝取總熱量：{total_today_calories:.1f} kcal\n\n"
    else:
        output += "今日尚無前序餐點記錄\n\n"
    
    # ===== 格式化過去幾天統計 =====
    if past_analysis and isinstance(past_analysis, dict):
        try:
            output += f"過去 {days} 天飲食統計：\n"
            
            # 總餐數
            total_meals = past_analysis.get('total_meals', 0)
            output += f"- 總餐數：{total_meals} 餐\n"
            
            # 營養趨勢
            trends = past_analysis.get('nutrition_trends', {})
            if trends:
                avg_cal = trends.get('avg_daily_calories', 0)
                max_cal = trends.get('max_daily_calories', 0)
                min_cal = trends.get('min_daily_calories', 0)
                
                output += f"- 平均每日熱量：{avg_cal:.1f} kcal\n"
                output += f"- 最高每日熱量：{max_cal:.1f} kcal\n"
                output += f"- 最低每日熱量：{min_cal:.1f} kcal\n"
            
            # 餐次類型統計
            meal_stats = past_analysis.get('meal_type_stats', {})
            if meal_stats:
                output += "- 餐次分布：\n"
                for meal_type, percentage in meal_stats.items():
                    meal_name = {
                        'breakfast': '早餐',
                        'lunch': '午餐',
                        'dinner': '晚餐',
                        'snack': '點心',
                        'latenight': '宵夜',
                        'other': '其他',
                        'meal': '餐點'
                    }.get(meal_type, meal_type)
                    output += f"  * {meal_name}: {percentage:.1f}%\n"
            
            # 每日摘要（最近3天）
            daily_summaries = past_analysis.get('daily_summaries', [])
            if daily_summaries and len(daily_summaries) > 0:
                output += f"\n最近 {min(3, len(daily_summaries))} 天詳細記錄：\n"
                for summary in daily_summaries[:3]:
                    date = summary.get('date', '未知')
                    meals = summary.get('meals', 0)
                    calories = summary.get('total_calories', 0)
                    output += f"- {date}: {meals} 餐, {calories:.1f} kcal\n"
            
        except Exception as e:
            logger.warning(f"格式化過去統計時發生錯誤: {e}")
            output += "過去統計資料格式化失敗\n"
    else:
        output += f"過去 {days} 天無足夠統計資料\n"
    
    logger.debug(f"格式化檢索文本完成，長度: {len(output)} 字元")
    
    return output


# ========== 性能測試輔助函數 ==========

def simulate_multi_user_load(users: int = 10, requests_per_user: int = 5):
    """
    模擬多用戶負載測試
    
    Args:
        users: 模擬用戶數量
        requests_per_user: 每個用戶的請求數量
    
    注意：
    - 這是性能測試的基礎框架
    - 實際測試需要結合具體業務邏輯
    - SQLite 在高並發下可能成為瓶頸
    - 未來考慮遷移到 PostgreSQL/MongoDB
    """
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️  性能測試模擬: {users} 用戶, 每用戶 {requests_per_user} 請求")
    logger.warning("💡 SQLite 並發限制: 考慮升級至 PostgreSQL/MongoDB")

def check_database_bottlenecks():
    """
    檢查資料庫性能瓶頸
    
    SQLite 限制：
    - 單一寫入者限制
    - 檔案鎖定機制
    - 不適合高並發場景
    
    建議升級路徑：
    - PostgreSQL: 成熟關聯式資料庫
    - MongoDB: NoSQL 彈性方案
    - 雲端資料庫: Azure SQL, AWS RDS
    """
    logger = logging.getLogger(__name__)
    logger.info("🔍 資料庫性能檢查:")
    logger.info("  - SQLite: 適合 MVP 和小規模使用")
    logger.info("  - 瓶頸: 並發寫入限制")
    logger.info("  - 建議: 用戶數 >100 時考慮 PostgreSQL")

# 模組級別的日誌器
logger = logging.getLogger(__name__)

# 在模組載入時執行基本設定
if os.getenv('ENABLE_DETAILED_LOGGING', 'False').lower() == 'true':
    setup_logging(log_level=os.getenv('LOG_LEVEL', 'INFO'))

logger.info("Utils模組已載入，共用工具函數已就緒")