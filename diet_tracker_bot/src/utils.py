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