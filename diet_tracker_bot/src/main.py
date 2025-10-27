"""
Diet Tracker Bot - 主程式入口點
================================

這是Discord飲食追蹤機器人的主要入口點。
目前為MVP版本，提供基本的環境設定和日誌配置。

未來擴展計畫：
1. 完整的Discord Bot實現
2. 圖像識別整合
3. 營養數據分析
4. 用戶歷史追蹤
5. AI推薦系統
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 添加src目錄到Python路徑，確保模組可以正確導入
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

# 載入環境變數
config_path = project_root / "config" / ".env"
load_dotenv(config_path)

def setup_logging():
    """
    設定應用程式日誌系統
    
    配置說明：
    - 日誌級別由環境變數 LOG_LEVEL 控制
    - 支援彩色輸出（如果安裝了colorlog）
    - 未來可擴展為檔案日誌、遠端日誌等
    """
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # 嘗試使用彩色日誌輸出
    try:
        import colorlog
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, log_level))
        
    except ImportError:
        # 如果沒有colorlog，使用標準日誌格式
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
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

def main():
    """
    主程式函數
    
    目前功能：
    1. 初始化日誌系統
    2. 驗證環境配置
    3. 顯示歡迎訊息
    
    未來擴展：
    1. 啟動Discord Bot
    2. 初始化資料庫連接
    3. 載入AI模型
    4. 設定定時任務
    5. 啟動Web API（如果需要）
    """
    # 初始化日誌系統
    logger = setup_logging()
    
    # 顯示歡迎訊息
    logger.info("=" * 50)
    logger.info("Diet Tracker Discord Bot v1.0.0 (MVP)")
    logger.info("飲食追蹤Discord機器人 - 初始化中...")
    logger.info("=" * 50)
    
    # 驗證環境配置
    if validate_environment():
        logger.info("✅ 環境配置驗證通過")
    else:
        logger.warning("⚠️  部分環境配置缺失，請檢查 config/.env 檔案")
    
    # 顯示專案資訊
    logger.info(f"專案根目錄: {project_root}")
    logger.info(f"配置檔案: {config_path}")
    
    # MVP階段：顯示功能開發進度
    logger.info("\n📋 MVP功能開發進度:")
    logger.info("✅ 專案架構建立")
    logger.info("✅ 圖像處理模組 (階段1完成)")
    logger.info("✅ Azure Computer Vision API 整合")
    logger.info("✅ 圖像預處理功能 (OpenCV)")
    logger.info("⏳ Discord Bot 核心功能")
    logger.info("⏳ 營養數據查詢與計算") 
    logger.info("⏳ 用戶歷史記錄儲存")
    logger.info("⏳ AI驅動的個人化推薦")
    
    # 顯示新增功能
    logger.info("\n🆕 階段1新增功能:")
    logger.info("  • 圖像預處理 (調整大小、去噪)")
    logger.info("  • Azure Computer Vision API 整合")
    logger.info("  • 食物識別結果解析和過濾")
    logger.info("  • 臨時圖像檔案管理")
    logger.info("  • 完整的錯誤處理和日誌記錄")
    logger.info("  • 命令列測試介面")
    
    # 測試提示
    logger.info("\n🧪 測試新功能:")
    logger.info("  python -m src.image_processor your_image.jpg")
    logger.info("  pytest tests/test_image_processor.py")
    
    # 未來在這裡添加Bot啟動邏輯
    # 例如：
    # from .bot import DietTrackerBot
    # bot = DietTrackerBot()
    # bot.run(os.getenv('DISCORD_TOKEN'))
    
    logger.info("\n🚀 系統初始化完成！")
    logger.info("目前為MVP開發階段，請繼續實現各項功能模組。")

if __name__ == "__main__":
    main()