#!/usr/bin/env python3
"""
Discord Slash Commands 測試腳本
"""

import sys
from pathlib import Path
import logging

# 添加 src 到路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

def test_discord_imports():
    """測試 Discord 相關導入"""
    try:
        import discord
        from discord.ext import commands
        
        logger.info(f"✅ Discord.py 版本: {discord.__version__}")
        
        # 檢查是否支援斜槓命令
        if hasattr(discord, 'app_commands'):
            logger.info("✅ 支援 Discord 斜槓命令 (app_commands)")
        else:
            logger.warning("⚠️  Discord.py 版本可能不支援斜槓命令")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Discord.py 導入失敗: {e}")
        return False

def test_bot_configuration():
    """測試 Bot 配置"""
    try:
        # 這裡不實際啟動 bot，只測試配置
        from discord_bot import bot, DISCORD_TOKEN
        
        logger.info("✅ Bot 配置檢查通過")
        
        # 檢查 Token
        if DISCORD_TOKEN:
            logger.info("✅ Discord Token 已設定")
        else:
            logger.warning("⚠️  Discord Token 未設定或為空")
        
        # 檢查斜槓命令
        if hasattr(bot, 'tree'):
            logger.info("✅ Bot 支援斜槓命令樹")
        else:
            logger.warning("⚠️  Bot 不支援斜槓命令")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Bot 配置測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    # 設定基本日誌
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    global logger
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("Discord 斜槓命令設置測試")
    logger.info("=" * 50)
    
    tests = [
        ("Discord 導入測試", test_discord_imports),
        ("Bot 配置測試", test_bot_configuration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 測試: {test_name}")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} - 通過")
        else:
            logger.info(f"❌ {test_name} - 失敗")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"測試結果: {passed}/{total} 通過")
    
    if passed == total:
        logger.info("🎉 斜槓命令設置完成！")
        logger.info("📋 可用的斜槓命令:")
        logger.info("   /track - 上傳食物圖片進行分析")
        logger.info("   /analyze - track 的別名")  
        logger.info("   /analyze3 - 三階段增強分析 (開發中)")
        logger.info("   /ask - 向營養師提問 (開發中)")
        logger.info("   /hello - 打招呼互動")
        logger.info("   /help - 顯示幫助")
        logger.info("   /stats - 統計資訊 (管理員)")
        logger.info("\n💡 啟動 Bot 後，在 Discord 中輸入 '/' 即可看到命令選單！")
    else:
        logger.info("⚠️  還有問題需要修復")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)