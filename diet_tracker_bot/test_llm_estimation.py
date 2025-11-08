#!/usr/bin/env python3
"""
測試 LLM 熱量估算功能
"""

import sys
import logging
from pathlib import Path

# 設置路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 配置日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from nutrition_calculator import NutritionCalculator

def test_llm_estimation():
    """測試 LLM 估算功能"""
    
    print("\n" + "="*60)
    print("測試 LLM 熱量估算功能")
    print("="*60 + "\n")
    
    calculator = NutritionCalculator()
    
    # 測試案例：包含已知食物和未知食物
    test_foods = [
        # TFND 或 USDA 可能找到的食物
        "apple",
        "rice",
        "chicken",
        
        # TFND 和 USDA 都找不到的食物（需要 LLM 估算）
        "dragon fruit sushi roll",  # 創意料理
        "unicorn cake",  # 虛構食物
        "xyzabc123",  # 無意義字串
    ]
    
    print(f"測試食物列表: {test_foods}\n")
    print("-"*60)
    
    nutrition_dict, total_calories = calculator.get_nutrition(test_foods)
    
    print("\n" + "-"*60)
    print("測試結果:")
    print("-"*60)
    
    if nutrition_dict:
        print("\n✅ 找到熱量資訊的食物:")
        for food, calories in nutrition_dict.items():
            print(f"  • {food}: {calories:.1f} kcal")
    else:
        print("\n❌ 沒有食物找到熱量資訊")
    
    # 檢查哪些食物沒找到
    not_found = [f for f in test_foods if f not in nutrition_dict]
    if not_found:
        print("\n⚠️  無法獲取熱量資訊的食物:")
        for food in not_found:
            print(f"  • {food}")
    
    print(f"\n🔥 總熱量: {total_calories:.1f} kcal")
    print("\n" + "="*60)
    print("測試完成")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_llm_estimation()
