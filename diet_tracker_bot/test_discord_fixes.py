#!/usr/bin/env python3
"""
Discord Bot 錯誤修復測試腳本
"""

import sys
from pathlib import Path
import logging

# 添加 src 到路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 設定基本日誌
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_nutrition_calculator():
    """測試營養計算器返回格式"""
    try:
        from nutrition_calculator import get_nutrition
        
        logger.info("測試營養計算器...")
        foods = ['apple', 'banana']
        result = get_nutrition(foods)
        
        logger.info(f"返回值類型: {type(result)}")
        logger.info(f"返回值: {result}")
        
        if isinstance(result, tuple) and len(result) == 2:
            nutrition_data, total_calories = result
            logger.info(f"✅ 營養資料: {nutrition_data}")
            logger.info(f"✅ 總熱量: {total_calories}")
            return True
        else:
            logger.error("❌ 返回格式不正確")
            return False
            
    except Exception as e:
        logger.error(f"❌ 營養計算器測試失敗: {e}")
        return False

def test_utils_handle_error():
    """測試 utils.handle_error 函數"""
    try:
        from utils import handle_error
        
        logger.info("測試錯誤處理函數...")
        
        # 測試不拋出異常的情況
        test_error = ValueError("測試錯誤")
        result = handle_error(test_error, "測試上下文", logger=logger, raise_error=False)
        logger.info("✅ handle_error 正常工作 (不拋出異常)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 錯誤處理函數測試失敗: {e}")
        return False

def test_data_storage():
    """測試資料存儲功能"""
    try:
        from data_storage import store_meal, get_history
        
        logger.info("測試資料存儲...")
        
        # 測試儲存
        test_foods = {"test_apple": 52.0, "test_banana": 89.0}
        meal_id = store_meal("test_discord_user", test_foods, 141.0)
        logger.info(f"✅ 記錄已儲存: ID={meal_id}")
        
        # 測試查詢
        history = get_history("test_discord_user", days=1)
        logger.info(f"✅ 查詢歷史: {len(history)} 筆記錄")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 資料存儲測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    logger.info("=" * 50)
    logger.info("Discord Bot 錯誤修復測試")
    logger.info("=" * 50)
    
    tests = [
        ("營養計算器", test_nutrition_calculator),
        ("錯誤處理函數", test_utils_handle_error),
        ("資料存儲", test_data_storage),
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
        logger.info("🎉 所有測試通過！Discord Bot 應該可以正常運行了")
    else:
        logger.info("⚠️  仍有問題需要修復")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)