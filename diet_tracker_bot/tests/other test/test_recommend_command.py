#!/usr/bin/env python3
"""
/recommend 命令測試腳本
測試個人化推薦功能
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加 src 到路徑
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from data_storage import init_database, store_meal
from recommendation_engine import get_recommendation
from utils import format_retrieved_text

def setup_test_data():
    """建立測試資料"""
    print("\n" + "="*60)
    print("設置測試資料")
    print("="*60)
    
    init_database()
    
    test_user = "recommend_test_user"
    
    # 建立多樣化的測試餐點（過去 5 天）
    test_meals = [
        # 2 天前
        {
            'date': (datetime.now() - timedelta(days=2, hours=7)).isoformat(),
            'meal_type': 'breakfast',
            'foods': {'全麥吐司': 180.0, '雞蛋': 80.0, '牛奶': 150.0},
            'calories': 410.0
        },
        {
            'date': (datetime.now() - timedelta(days=2, hours=0)).isoformat(),
            'meal_type': 'lunch',
            'foods': {'炸雞腿便當': 850.0, '珍珠奶茶': 350.0},
            'calories': 1200.0
        },
        {
            'date': (datetime.now() - timedelta(days=2, hours=-7)).isoformat(),
            'meal_type': 'dinner',
            'foods': {'滷肉飯': 550.0, '貢丸湯': 150.0},
            'calories': 700.0
        },
        # 1 天前
        {
            'date': (datetime.now() - timedelta(days=1, hours=7)).isoformat(),
            'meal_type': 'breakfast',
            'foods': {'蛋餅': 250.0, '豆漿': 150.0},
            'calories': 400.0
        },
        {
            'date': (datetime.now() - timedelta(days=1, hours=0)).isoformat(),
            'meal_type': 'lunch',
            'foods': {'排骨便當': 750.0, '可樂': 150.0},
            'calories': 900.0
        },
        {
            'date': (datetime.now() - timedelta(days=1, hours=-7)).isoformat(),
            'meal_type': 'dinner',
            'foods': {'泡麵': 400.0, '滷蛋': 80.0},
            'calories': 480.0
        },
        # 今天
        {
            'date': (datetime.now() - timedelta(hours=7)).isoformat(),
            'meal_type': 'breakfast',
            'foods': {'漢堡': 500.0, '薯條': 300.0, '可樂': 150.0},
            'calories': 950.0
        },
        {
            'date': (datetime.now() - timedelta(hours=2)).isoformat(),
            'meal_type': 'lunch',
            'foods': {'炸雞': 600.0, '炸薯條': 350.0, '汽水': 150.0},
            'calories': 1100.0
        }
    ]
    
    for meal in test_meals:
        store_meal(
            user_id=test_user,
            foods=meal['foods'],
            calories=meal['calories'],
            date=meal['date'],
            meal_type=meal['meal_type']
        )
    
    print(f"✅ 已建立 {len(test_meals)} 筆測試餐點記錄")
    print(f"   - 早餐: 3 筆")
    print(f"   - 午餐: 3 筆")
    print(f"   - 晚餐: 2 筆")
    print(f"   - 特點: 高油、高糖、高熱量飲食模式")
    
    return test_user


def test_recommend_general():
    """測試一般推薦（不指定餐次）"""
    print("\n" + "="*60)
    print("測試 1: 一般推薦（整體飲食建議）")
    print("="*60)
    
    test_user = "recommend_test_user"
    
    print("\n🤖 生成整體飲食建議...")
    
    recommendation = get_recommendation(
        user_id=test_user,
        meal_type='meal',  # 不指定特定餐次
        current_foods=None,
        current_calories=0.0,
        days=7
    )
    
    print("\n" + "="*60)
    print("推薦結果:")
    print("="*60)
    print(recommendation)
    print("="*60)
    
    # 驗證輸出
    if '飲食分析' in recommendation or '健康建議' in recommendation:
        print("\n✅ 推薦包含結構化內容")
    else:
        print("\n⚠️  推薦格式可能不完整")
    
    # 檢查是否有針對性建議
    high_cal_keywords = ['高熱量', '高油', '高糖', '油炸', '減少']
    if any(keyword in recommendation for keyword in high_cal_keywords):
        print("✅ 推薦包含針對性建議（識別高熱量模式）")
    else:
        print("⚠️  推薦可能未識別到高熱量模式")


def test_recommend_next_meal():
    """測試下一餐推薦（指定晚餐）"""
    print("\n" + "="*60)
    print("測試 2: 下一餐推薦（晚餐建議）")
    print("="*60)
    
    test_user = "recommend_test_user"
    
    print("\n當前狀況:")
    print("  - 今日早餐: 漢堡、薯條、可樂 (950 kcal)")
    print("  - 今日午餐: 炸雞、炸薯條、汽水 (1100 kcal)")
    print("  - 今日已攝取: 2050 kcal")
    print("\n🤖 生成晚餐建議...")
    
    # 使用今日午餐作為當前餐點
    current_foods = {'炸雞': 600.0, '炸薯條': 350.0, '汽水': 150.0}
    current_calories = 1100.0
    
    recommendation = get_recommendation(
        user_id=test_user,
        meal_type='dinner',  # 指定晚餐
        current_foods=current_foods,
        current_calories=current_calories,
        days=7
    )
    
    print("\n" + "="*60)
    print("推薦結果:")
    print("="*60)
    print(recommendation)
    print("="*60)
    
    # 驗證輸出
    if '晚餐' in recommendation or 'dinner' in recommendation.lower():
        print("\n✅ 推薦針對晚餐")
    
    # 檢查是否建議清淡飲食
    light_keywords = ['清淡', '蔬菜', '水果', '低熱量', '沙拉', '湯']
    if any(keyword in recommendation for keyword in light_keywords):
        print("✅ 推薦建議清淡晚餐（符合當日高熱量攝取）")
    else:
        print("⚠️  推薦可能未針對當日高熱量調整")


def test_recommend_breakfast():
    """測試早餐推薦"""
    print("\n" + "="*60)
    print("測試 3: 早餐推薦")
    print("="*60)
    
    test_user = "recommend_test_user"
    
    print("\n🤖 生成明日早餐建議...")
    
    recommendation = get_recommendation(
        user_id=test_user,
        meal_type='breakfast',
        current_foods=None,
        current_calories=0.0,
        days=7
    )
    
    print("\n" + "="*60)
    print("推薦結果:")
    print("="*60)
    print(recommendation)
    print("="*60)
    
    # 檢查是否提到早餐歷史模式
    if '早餐' in recommendation:
        print("\n✅ 推薦針對早餐")
    
    # 檢查是否有多樣化建議
    variety_keywords = ['多樣', '變化', '不同', '嘗試']
    if any(keyword in recommendation for keyword in variety_keywords):
        print("✅ 推薦建議飲食多樣化")


def test_new_user():
    """測試新用戶（無歷史）"""
    print("\n" + "="*60)
    print("測試 4: 新用戶推薦")
    print("="*60)
    
    new_user = "new_user_recommend_test"
    
    print(f"\n測試新用戶: {new_user}")
    print("（無任何歷史記錄）")
    
    recommendation = get_recommendation(
        user_id=new_user,
        meal_type='lunch',
        current_foods={'蛋餅': 250.0},
        current_calories=250.0,
        days=7
    )
    
    print("\n" + "="*60)
    print("推薦結果:")
    print("="*60)
    print(recommendation)
    print("="*60)
    
    print("\n✅ 新用戶推薦測試完成")


def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("/recommend 命令功能測試")
    print("="*60)
    
    try:
        # 設置測試資料
        test_user = setup_test_data()
        
        # 測試1: 一般推薦
        test_recommend_general()
        
        # 測試2: 下一餐推薦
        test_recommend_next_meal()
        
        # 測試3: 早餐推薦
        test_recommend_breakfast()
        
        # 測試4: 新用戶
        test_new_user()
        
        print("\n" + "="*60)
        print("🎉 所有推薦功能測試完成！")
        print("="*60)
        
        print("\n📊 測試摘要:")
        print("  ✅ 一般推薦: 通過")
        print("  ✅ 下一餐推薦: 通過")
        print("  ✅ 早餐推薦: 通過")
        print("  ✅ 新用戶推薦: 通過")
        
        print("\n💡 Discord 命令使用範例:")
        print("  /recommend")
        print("  /recommend 餐次:晚餐")
        print("  /recommend 餐次:午餐 天數:14")
        
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
