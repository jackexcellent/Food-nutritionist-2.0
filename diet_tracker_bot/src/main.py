"""
Diet Tracker Bot - 主程式入口點
================================

這是Discord飲食追蹤機器人的主要入口點，支援兩種運行模式：

1. **Discord Bot 模式** (預設)：啟動完整的 Discord 機器人
2. **CLI 測試模式**：命令列介面，用於開發和測試

MVP功能：
1. Discord Bot：完整的機器人界面，支援 /track 命令
2. CLI 測試：直接測試圖像到熱量的完整流程
3. 圖像處理：使用Azure Computer Vision識別食物
4. 營養計算：從TFND資料庫和USDA API查詢熱量
5. 資料儲存：SQLite 資料庫持久化
6. AI 推薦：Google Gemini LLM 個人化建議

使用方式：
- Discord Bot: python src/main.py
- CLI 測試: python src/main.py --cli --image path/to/image.jpg

未來擴展計畫：
1. 更多 Discord 命令 (/history, /stats, /profile)
2. 份量識別與計算
3. 進階 AI 推薦功能
4. 多語言支援
5. Web Dashboard
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
from data_storage import store_meal, get_history, get_statistics, init_database
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

def process_image_to_nutrition(image_path: str, logger: logging.Logger, user_id: str = None) -> Tuple[List[str], Dict[str, float], float, int]:
    """
    端到端處理：從圖像到營養資訊
    
    這是整合的核心函數，串接圖像處理和營養計算兩個階段：
    階段1: 圖像處理 -> 食物識別
    階段2: 營養計算 -> 熱量統計
    
    Args:
        image_path: 圖像檔案路徑
        logger: 日誌器實例
        user_id: 用戶識別碼，如果提供將儲存記錄到資料庫
    
    Returns:
        Tuple[List[str], Dict[str, float], float, int]: 
            - 食物清單 (英文名稱)
            - 營養資料字典 {食物: 熱量}
            - 總熱量
            - 記錄ID (如果儲存到資料庫)
    
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
            return [], {}, 0.0, None
        
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
        
        # ========== 階段 3: 儲存記錄 (可選) ==========
        record_id = None
        if user_id:
            logger.info("\n" + "=" * 60)
            logger.info("階段 3: 儲存飲食記錄")
            logger.info("=" * 60)
            
            try:
                # 確保資料庫已初始化
                init_database()
                
                # 儲存記錄
                logger.info(f"💾 儲存記錄到資料庫: 用戶 {user_id}")
                record_id = store_meal(user_id, nutrition_data, total_calories)
                logger.info(f"✅ 記錄已儲存: ID={record_id}")
                
            except Exception as e:
                logger.warning(f"⚠️  儲存記錄失敗: {e}")
                # 不影響主要功能，只記錄警告
        
        return food_items, nutrition_data, total_calories, record_id
        
    except FileNotFoundError as e:
        handle_error(e, "圖像檔案不存在", logger)
        raise
    except Exception as e:
        handle_error(e, "圖像到營養資訊處理失敗", logger)
        raise

def display_results(food_items: List[str], 
                   nutrition_data: Dict[str, float], 
                   total_calories: float,
                   logger: logging.Logger,
                   record_id: int = None,
                   user_id: str = None) -> None:
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
    
    # 顯示儲存資訊
    if record_id and user_id:
        logger.info(f"💾 記錄已儲存: ID={record_id} (用戶: {user_id})")
    
    logger.info("=" * 60)
    
    # 顯示資料來源說明
    logger.info("\n💡 資料來源:")
    logger.info("   • 圖像識別: Azure Computer Vision API")
    logger.info("   • 營養資料: TFND 台灣食品營養資料庫 + USDA FoodData Central")
    logger.info("   • 快取機制: 記憶體快取 (未來可升級為 Redis)")

def show_user_history(user_id: str, days: int, logger: logging.Logger) -> None:
    """
    顯示用戶歷史記錄
    
    Args:
        user_id: 用戶識別碼
        days: 查詢天數
        logger: 日誌器實例
    """
    logger.info("=" * 60)
    logger.info(f"📋 用戶歷史記錄: {user_id} (最近 {days} 天)")
    logger.info("=" * 60)
    
    try:
        # 確保資料庫已初始化
        init_database()
        
        # 查詢歷史記錄
        history = get_history(user_id, days)
        
        if not history:
            logger.info("📭 沒有找到歷史記錄")
            return
        
        logger.info(f"📊 找到 {len(history)} 筆記錄:\n")
        
        # 顯示每筆記錄
        for i, (record_id, date, foods, calories, created_at) in enumerate(history, 1):
            logger.info(f"📝 記錄 #{i} (ID: {record_id})")
            logger.info(f"   📅 日期: {date}")
            logger.info(f"   🔥 總熱量: {calories:.1f} kcal")
            logger.info(f"   🍽️  食物:")
            
            for food_name, food_calories in foods.items():
                logger.info(f"      • {food_name}: {food_calories} kcal")
            
            logger.info(f"   ⏰ 記錄時間: {created_at}")
            logger.info("-" * 40)
        
        # 顯示統計
        show_user_statistics(user_id, logger, days)
        
    except Exception as e:
        logger.error(f"❌ 查詢歷史記錄失敗: {e}")

def show_user_statistics(user_id: str, logger: logging.Logger, days: int = 7) -> None:
    """
    顯示用戶統計資訊
    
    Args:
        user_id: 用戶識別碼
        logger: 日誌器實例
        days: 統計天數
    """
    try:
        # 獲取統計資訊
        stats = get_statistics(user_id, days)
        
        logger.info(f"\n📊 統計資訊 (最近 {days} 天):")
        logger.info("=" * 40)
        logger.info(f"   總餐數: {stats['total_meals']}")
        logger.info(f"   總熱量: {stats['total_calories']:.1f} kcal")
        
        if stats['total_meals'] > 0:
            logger.info(f"   平均每餐: {stats['avg_calories']:.1f} kcal")
        
        if stats['most_common_foods']:
            logger.info(f"\n🏆 最常吃的食物:")
            for food, count in stats['most_common_foods'][:5]:
                logger.info(f"      • {food}: {count} 次")
        
    except Exception as e:
        logger.error(f"❌ 獲取統計資訊失敗: {e}")

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
        help='圖像檔案路徑 (支援 jpg, png, jpeg)'
    )
    
    parser.add_argument(
        '--user', '-u',
        type=str,
        help='用戶ID (如果提供將儲存記錄到資料庫)'
    )
    
    parser.add_argument(
        '--history', 
        action='store_true',
        help='顯示用戶歷史記錄 (需要配合 --user)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='歷史記錄查詢天數 (預設 7 天)'
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
    
    # 驗證參數組合
    if not args.image and not args.history:
        parser.error("必須指定 --image 或 --history 參數")
    
    if args.history and not args.user:
        parser.error("--history 參數需要配合 --user 指定用戶ID")
    
    # 設定日誌級別
    log_level = 'DEBUG' if args.debug else 'INFO'
    logger = setup_logging(log_level)
    
    # 顯示歡迎訊息
    logger.info("=" * 60)
    logger.info("Diet Tracker Bot - CLI 模式")
    logger.info("飲食追蹤機器人 - 圖像到熱量計算")
    logger.info("=" * 60)
    
    try:
        # 檢查是否要顯示歷史記錄
        if args.history:
            show_user_history(args.user, args.days, logger)
            return 0
        
        # 執行端到端處理
        food_items, nutrition_data, total_calories, record_id = process_image_to_nutrition(
            args.image, 
            logger,
            user_id=args.user
        )
        
        # 顯示結果
        if food_items:
            display_results(food_items, nutrition_data, total_calories, logger, 
                          record_id=record_id, user_id=args.user)
            logger.info("\n✅ 處理完成！")
            
            # 如果有用戶ID，額外顯示統計資訊
            if args.user:
                show_user_statistics(args.user, logger)
            
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

def run_discord_bot():
    """啟動 Discord 機器人模式"""
    try:
        from discord_bot import run_bot
        
        print("🤖 啟動 Discord 飲食追蹤機器人...")
        print("📝 使用 /track 命令開始追蹤飲食")
        print("🔗 邀請機器人到您的伺服器並開始使用！")
        print("⚠️  按 Ctrl+C 停止機器人\n")
        
        # 初始化資料庫
        init_database()
        
        # 啟動機器人
        run_bot()
        
    except ImportError as e:
        print(f"❌ 無法載入 Discord Bot 模組: {e}")
        print("💡 請安裝 discord.py: pip install discord.py")
        return 1
    except KeyboardInterrupt:
        print("\n👋 機器人已停止")
        return 0
    except Exception as e:
        print(f"❌ Discord Bot 啟動失敗: {e}")
        return 1


def main():
    """主函數 - 決定運行模式"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Discord 飲食追蹤機器人",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # 添加模式選擇參數
    parser.add_argument(
        '--cli', 
        action='store_true',
        help='使用 CLI 測試模式 (需要配合 --image 參數)'
    )
    
    # CLI 模式專用參數
    parser.add_argument(
        '--image', '-i',
        type=str,
        help='要分析的圖像檔案路徑 (CLI 模式使用)'
    )
    
    parser.add_argument(
        '--user', '-u',
        type=str,
        default='cli_user',
        help='用戶ID (CLI 模式使用，預設: cli_user)'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='啟用除錯模式 (CLI 模式使用)'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='設定日誌級別 (預設: INFO)'
    )
    
    args = parser.parse_args()
    
    # 設定日誌
    setup_logging(args.log_level)
    
    if args.cli:
        # CLI 測試模式
        if not args.image:
            print("❌ CLI 模式需要指定 --image 參數")
            parser.print_help()
            return 1
        
        print("🔧 CLI 測試模式")
        return run_cli_with_args(args)
    else:
        # Discord Bot 模式 (預設)
        return run_discord_bot()


def run_cli_with_args(args):
    """使用解析的參數運行 CLI 模式"""
    # 重新建構 sys.argv 以相容原有的 run_cli 函數
    original_argv = sys.argv[:]
    sys.argv = ['main.py', args.image]
    
    if args.debug:
        sys.argv.append('--debug')
    if args.user != 'cli_user':
        sys.argv.extend(['--user', args.user])
    sys.argv.extend(['--log-level', args.log_level])
    
    try:
        result = run_cli()
        return result
    finally:
        # 恢復原始 sys.argv
        sys.argv = original_argv


if __name__ == "__main__":
    # 主程式入口點
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 程式已中止")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)