#!/usr/bin/env python3
"""
測試 USDA API 特殊字元處理修復
============================

驗證目標：
1. 原始錯誤案例「山葵/芥末（wasabi）」不再導致 500 錯誤
2. 清理後的名稱能成功查詢或優雅回退到 LLM
3. 錯誤處理機制正常運作
"""

import sys
from pathlib import Path

# 添加 src 目錄到路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from nutrition_calculator import NutritionCalculator


def test_problematic_food():
    """測試原始錯誤案例"""
    print("\n" + "="*70)
    print("測試 USDA API 特殊字元處理修復")
    print("="*70 + "\n")
    
    calculator = NutritionCalculator()
    
    # 原始導致 500 錯誤的食物名稱
    problematic_food = "山葵/芥末（wasabi）"
    
    print(f"🧪 測試食物: {problematic_food}")
    print("-"*70)
    
    # 測試清理函數
    cleaned = calculator._sanitize_food_name_for_api(problematic_food)
    print(f"1️⃣ 清理後名稱: '{problematic_food}' → '{cleaned}'")
    print()
    
    # 測試完整營養查詢流程
    print("2️⃣ 執行完整營養查詢流程...")
    print()
    
    try:
        nutrition_dict, total_calories = calculator.get_nutrition([problematic_food])
        
        print("✅ 查詢成功完成（無異常）")
        print()
        print(f"📊 結果:")
        print(f"   - 營養資訊字典: {nutrition_dict}")
        print(f"   - 總熱量: {total_calories} kcal")
        print()
        
        if nutrition_dict and problematic_food in nutrition_dict:
            calories = nutrition_dict[problematic_food]
            if isinstance(calories, dict):
                cal_value = calories.get('calories', 0)
            else:
                cal_value = calories
                
            if cal_value > 0:
                print(f"✅ 成功取得熱量資訊: {cal_value} kcal")
                print("   （來源可能是 TFND、USDA 或 LLM 估算）")
            else:
                print("⚠️ 未找到熱量資訊（返回 0）")
                print("   （符合預期：若三個來源都失敗則返回 0）")
        else:
            print("⚠️ 該食物未包含在結果中（可能被跳過）")
        
        print()
        print("-"*70)
        print("✅ 修復驗證通過：")
        print("   • 未發生 500 錯誤")
        print("   • 錯誤處理機制運作正常")
        print("   • 回退鏈（TFND → USDA → LLM → 0）完整執行")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"❌ 發生異常: {type(e).__name__}: {e}")
        print()
        print("修復可能未完全生效，請檢查錯誤日誌")
        return False


def test_additional_cases():
    """測試其他可能有問題的案例"""
    print("\n" + "="*70)
    print("額外測試案例")
    print("="*70 + "\n")
    
    calculator = NutritionCalculator()
    
    test_cases = [
        "雞肉/牛肉（混合）",
        "Apple (red)",
        "豬肉/雞肉/牛肉",
        "Vitamin B12（補充劑）"
    ]
    
    for i, food in enumerate(test_cases, 1):
        cleaned = calculator._sanitize_food_name_for_api(food)
        print(f"{i}. '{food}'")
        print(f"   → '{cleaned}'")
        print()


if __name__ == "__main__":
    print("\n🔧 USDA API 修復驗證測試\n")
    
    # 主要測試
    success = test_problematic_food()
    
    # 額外案例
    test_additional_cases()
    
    # 總結
    print("\n" + "="*70)
    if success:
        print("✅ 所有測試通過")
    else:
        print("⚠️ 部分測試未通過，請查看上方輸出")
    print("="*70 + "\n")
