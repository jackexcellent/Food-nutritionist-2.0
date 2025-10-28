"""
Diet Tracker Bot - 主程式入口點
================================

這是Discord飲食追蹤機器人的主要入口點。
目前為MVP版本，提供CLI介面來測試圖像到熱量的完整流程。

MVP功能：
1. CLI入口：接受圖像路徑
2. 圖像處理：使用Azure Computer Vision識別食物
3. 營養計算：從TFND資料庫和USDA API查詢熱量
4. 結果輸出：顯示食物清單、各項熱量、總熱量

未來擴展計畫：
1. 完整的Discord Bot實現
2. 份量識別與計算
3. 用戶歷史追蹤
4. AI推薦系統
5. 多語言支援
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Tuple, List
from dotenv import load_dotenv

# 添加src目錄到Python路徑，確保模組可以正確導入
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

# 載入環境變數（必須在導入其他模組之前）
config_path = project_root / "config" / ".env"
load_dotenv(config_path)

# 導入專案模組
from image_processor import process_image  # 使用模組級函數而不是類別
from nutrition_calculator import get_nutrition
from utils import handle_error, get_cached_nutrition, set_cached_nutrition

def setup_logging(log_level: str = 'INFO'):
    """
    設定應用程式日誌系統
    
    Args:
        log_level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    配置說明：
    - 日誌級別可通過參數傳入，預設為 INFO
    - 支援彩色輸出（如果安裝了colorlog）
    - 未來可擴展為檔案日誌、遠端日誌等
    """
    log_level = log_level.upper()
    
    # 取得根 logger 並清除現有的處理器（避免重複）
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, log_level))
    
    # 嘗試使用彩色日誌輸出
    try:
        import colorlog
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s%(reset)s - %(cyan)s%(name)s%(reset)s - %(log_color)s%(levelname)s%(reset)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'white',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            },
            secondary_log_colors={},
            style='%'
        ))
        root_logger.addHandler(handler)
        
    except ImportError:
        # 如果沒有colorlog，使用標準日誌格式
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        root_logger.addHandler(handler)
    
    # 設定第三方套件的日誌級別
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('azure').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("日誌系統初始化完成")
    return logger

def validate_environment():
    """
    驗證必要的環境變數是否已設定
    
    這個函數檢查所有必要的API金鑰和配置是否存在。
    在生產環境中，缺少任何必要配置都會導致程式終止。
    
    未來擴展：
    - 添加配置檔案驗證
    - 支援多環境配置（開發、測試、生產）
    - 動態配置重載
    """
    required_vars = [
        'AZURE_KEY',
        'AZURE_ENDPOINT', 
        'USDA_KEY',
        'GEMINI_KEY',
        'DISCORD_TOKEN'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger = logging.getLogger(__name__)
        logger.warning(f"缺少環境變數: {', '.join(missing_vars)}")
        logger.info("請檢查 config/.env 檔案並設定必要的API金鑰")
        # 在開發階段，我們只警告而不終止程式
        # 在生產環境中，可以取消註解下面這行來強制終止
        # sys.exit(1)
    
    return len(missing_vars) == 0

def process_image_to_nutrition(image_path: str, logger: logging.Logger) -> Tuple[List[str], Dict[str, float], float]:
    """
    端到端處理：從圖像到營養資訊
    
    這是整合的核心函數，串接圖像處理和營養計算兩個階段：
    階段1: 圖像處理 -> 食物識別
    階段2: 營養計算 -> 熱量統計
    
    Args:
        image_path: 圖像檔案路徑
        logger: 日誌器實例
    
    Returns:
        Tuple[List[str], Dict[str, float], float]: 
            - 食物清單 (英文名稱)
            - 營養資料字典 {食物: 熱量}
            - 總熱量
    
    Raises:
        FileNotFoundError: 圖像檔案不存在
        Exception: 處理過程中的各種錯誤
    """
    try:
        # ========== 階段 1: 圖像處理與食物識別 ==========
        logger.info("=" * 60)
        logger.info("階段 1: 圖像處理與食物識別")
        logger.info("=" * 60)
        
        # 驗證圖像檔案存在
        if not Path(image_path).exists():
            raise FileNotFoundError(f"找不到圖像檔案: {image_path}")
        
        logger.info("📸 載入圖像: {}".format(os.path.basename(image_path)))
        
        # 處理圖像並識別食物（直接使用模組函數）
        logger.info("🔍 使用 Azure Computer Vision 識別食物...")
        food_items = process_image(image_path)
        
        if not food_items:
            logger.warning("⚠️  未能識別出任何食物")
            return [], {}, 0.0
        
        logger.info(f"✅ 成功識別 {len(food_items)} 種食物")
        logger.info(f"   食物清單: {', '.join(food_items)}")
        
        # ========== 階段 2: 營養計算與熱量統計 ==========
        logger.info("\n" + "=" * 60)
        logger.info("階段 2: 營養計算與熱量統計")
        logger.info("=" * 60)
        
        # 使用快取優化查詢效能
        logger.info("📊 查詢營養資料...")
        logger.info("   - 優先查詢快取")
        logger.info("   - TFND 資料庫精確/模糊匹配")
        logger.info("   - USDA API fallback")
        
        # 計算營養資訊
        nutrition_data, total_calories = get_nutrition(food_items)
        
        logger.info(f"✅ 營養計算完成")
        
        return food_items, nutrition_data, total_calories
        
    except FileNotFoundError as e:
        handle_error(e, "圖像檔案不存在", logger)
        raise
    except Exception as e:
        handle_error(e, "圖像到營養資訊處理失敗", logger)
        raise

def display_results(food_items: List[str], 
                   nutrition_data: Dict[str, float], 
                   total_calories: float,
                   logger: logging.Logger) -> None:
    """
    格式化顯示處理結果
    
    Args:
        food_items: 識別出的食物清單
        nutrition_data: 營養資料字典
        total_calories: 總熱量
        logger: 日誌器實例
    """
    logger.info("\n" + "=" * 60)
    logger.info("📋 處理結果摘要")
    logger.info("=" * 60)
    
    # 顯示食物清單
    logger.info(f"\n�️  識別的食物清單 ({len(food_items)} 項):")
    for i, food in enumerate(food_items, 1):
        logger.info(f"   {i}. {food}")
    
    # 顯示各項熱量
    logger.info(f"\n🔥 營養資訊 (每 100g):")
    for food, calories in nutrition_data.items():
        status = "✅" if calories > 0 else "⚠️"
        logger.info(f"   {status} {food:15s} : {calories:6.1f} kcal")
    
    # 顯示總熱量
    logger.info(f"\n📊 總熱量: {total_calories:.1f} kcal")
    logger.info("=" * 60)
    
    # 顯示資料來源說明
    logger.info("\n💡 資料來源:")
    logger.info("   • 圖像識別: Azure Computer Vision API")
    logger.info("   • 營養資料: TFND 台灣食品營養資料庫 + USDA FoodData Central")
    logger.info("   • 快取機制: 記憶體快取 (未來可升級為 Redis)")

def run_cli():
    """
    CLI 模式主函數
    
    提供命令列介面來測試完整的圖像到熱量計算流程。
    這是 MVP 階段的主要測試方式。
    
    使用範例：
        python src/main.py --image test_images/apple.jpg
        python src/main.py --image test_images/meal.jpg --debug
    """
    # 設定命令列參數解析
    parser = argparse.ArgumentParser(
        description='Diet Tracker Bot - 飲食追蹤機器人 CLI 工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  基本使用:
    python src/main.py --image test_images/apple.jpg
  
  啟用除錯模式:
    python src/main.py --image test_images/meal.jpg --debug
  
  查看版本資訊:
    python src/main.py --version

功能說明:
  1. 載入並預處理圖像
  2. 使用 Azure Computer Vision 識別食物
  3. 從 TFND 資料庫查詢營養資訊
  4. 顯示食物清單、各項熱量和總熱量
        """
    )
    
    parser.add_argument(
        '--image', '-i',
        type=str,
        required=True,
        help='圖像檔案路徑 (支援 jpg, png, jpeg)'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='啟用除錯模式 (顯示詳細日誌)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='Diet Tracker Bot v1.0.0 (MVP)'
    )
    
    args = parser.parse_args()
    
    # 設定日誌級別
    log_level = 'DEBUG' if args.debug else 'INFO'
    logger = setup_logging(log_level)
    
    # 顯示歡迎訊息
    logger.info("=" * 60)
    logger.info("Diet Tracker Bot - CLI 模式")
    logger.info("飲食追蹤機器人 - 圖像到熱量計算")
    logger.info("=" * 60)
    
    try:
        # 執行端到端處理
        food_items, nutrition_data, total_calories = process_image_to_nutrition(
            args.image, 
            logger
        )
        
        # 顯示結果
        if food_items:
            display_results(food_items, nutrition_data, total_calories, logger)
            logger.info("\n✅ 處理完成！")
            return 0
        else:
            logger.warning("\n⚠️  未能識別出任何食物，請嘗試其他圖像")
            return 1
            
    except FileNotFoundError:
        logger.error(f"\n❌ 錯誤: 找不到圖像檔案 '{args.image}'")
        logger.info("請檢查檔案路徑是否正確")
        return 1
    except Exception as e:
        logger.error(f"\n❌ 處理失敗: {str(e)}")
        if args.debug:
            import traceback
            logger.debug(f"詳細錯誤:\n{traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    # CLI 模式：運行命令列介面
    sys.exit(run_cli())