#!/usr/bin/env python3
"""
手動整合測試 - 驗證完整功能流程
測試剛剛實作的功能：
1. 中文資料庫載入和搜尋
2. 餐次類型儲存和顯示
3. 歷史記錄顯示餐次而非ID
"""

import sys
from pathlib import Path

# 添加 src 到路徑
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from nutrition_calculator import NutritionCalculator
from data_storage import init_database, store_meal, get_history
import json


def test_chinese_database():
    """測試中文資料庫功能"""
    print("\n=== 測試 1: 中文資料庫載入和搜尋 ===")
    
    calculator = NutritionCalculator()
    
    # 檢查資料庫是否載入
    print(f"資料庫載入記錄數: {len(calculator.tfnd_data)}")
    
    if len(calculator.tfnd_data) > 0:
        # 顯示前3筆資料
        print("\n前3筆資料樣本:")
        for i, item in enumerate(calculator.tfnd_data[:3]):
            print(f"{i+1}. 樣品名稱: {item.get('樣品名稱', 'N/A')}")
            print(f"   俗名: {item.get('俗名', 'N/A')}")
            print(f"   熱量: {item.get('修正熱量(kcal)', item.get('熱量(kcal)', 'N/A'))}")
            print()
        
        # 測試中文搜尋
        print("測試中文搜尋:")
        test_foods = ["白米飯", "雞胸肉", "蘋果"]
        for food_name in test_foods:
            calories = calculator._query_tfnd_database(food_name)
            print(f"  {food_name}: {calories} kcal")
    else:
        print("❌ 資料庫未載入任何資料")
    
    print("✅ 中文資料庫測試完成\n")


def test_meal_type_storage():
    """測試餐次類型儲存"""
    print("=== 測試 2: 餐次類型儲存 ===")
    
    # 初始化資料庫
    init_database()
    
    # 儲存不同餐次的記錄
    test_user = "test_user_123"
    
    meals = [
        {
            "foods": {"白米飯": 183.0, "雞胸肉": 165.0},
            "calories": 348.0,
            "meal_type": "breakfast",
            "meal_type_custom": None
        },
        {
            "foods": {"蘋果": 52.0, "香蕉": 89.0},
            "calories": 141.0,
            "meal_type": "lunch",
            "meal_type_custom": None
        },
        {
            "foods": {"牛排": 271.0, "薯條": 312.0},
            "calories": 583.0,
            "meal_type": "dinner",
            "meal_type_custom": None
        },
        {
            "foods": {"餅乾": 150.0},
            "calories": 150.0,
            "meal_type": "other",
            "meal_type_custom": "下午茶"
        }
    ]
    
    record_ids = []
    for meal in meals:
        record_id = store_meal(
            user_id=test_user,
            foods=meal["foods"],
            calories=meal["calories"],
            meal_type=meal["meal_type"],
            meal_type_custom=meal["meal_type_custom"]
        )
        record_ids.append(record_id)
        meal_name = meal["meal_type_custom"] if meal["meal_type_custom"] else meal["meal_type"]
        print(f"✓ 已儲存 {meal_name}: ID={record_id}, {meal['calories']} kcal")
    
    print("✅ 餐次類型儲存測試完成\n")
    return test_user


def test_history_display(user_id):
    """測試歷史記錄顯示"""
    print("=== 測試 3: 歷史記錄顯示餐次類型 ===")
    
    # 查詢歷史記錄
    history = get_history(user_id, days=7)
    
    print(f"找到 {len(history)} 筆記錄:\n")
    
    meal_type_emoji = {
        'breakfast': '🌅',
        'lunch': '🌞',
        'dinner': '🌙',
        'snack': '🍿',
        'latenight': '🌃',
        'other': '✏️',
        'meal': '🍽️'
    }
    
    for record in history:
        record_id = record[0]
        date = record[1]
        foods = record[2]
        calories = record[3]
        meal_type = record[5] if len(record) > 5 else 'meal'
        meal_type_custom = record[6] if len(record) > 6 else None
        
        # 格式化餐次顯示
        emoji = meal_type_emoji.get(meal_type, '🍽️')
        if meal_type_custom:
            meal_display = f"{emoji} {meal_type_custom}"
        else:
            meal_names = {
                'breakfast': '早餐',
                'lunch': '午餐',
                'dinner': '晚餐',
                'snack': '點心',
                'latenight': '宵夜',
                'other': '其他',
                'meal': '餐點'
            }
            meal_display = f"{emoji} {meal_names.get(meal_type, '餐點')}"
        
        foods_str = ", ".join(f"{k}({v})" for k, v in foods.items())
        print(f"  #{record_id} - {meal_display}")
        print(f"    時間: {date}")
        print(f"    食物: {foods_str}")
        print(f"    總熱量: {calories} kcal")
        print()
    
    print("✅ 歷史記錄顯示測試完成\n")


def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("手動整合測試 - 驗證新功能")
    print("="*60)
    
    try:
        # 測試1: 中文資料庫
        test_chinese_database()
        
        # 測試2: 餐次類型儲存
        test_user = test_meal_type_storage()
        
        # 測試3: 歷史記錄顯示
        test_history_display(test_user)
        
        print("="*60)
        print("🎉 所有測試完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
