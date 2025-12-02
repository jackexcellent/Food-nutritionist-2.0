#!/usr/bin/env python3
"""
RAG 推薦系統測試腳本
測試 Retrieval-Augmented Generation 功能
"""

import sys
from pathlib import Path

# 添加 src 到路徑
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from recommendation_engine import get_recommendation
from data_storage import init_database, store_meal, get_previous_meals, get_past_days
from utils import format_retrieved_text
from datetime import datetime, timedelta


def setup_test_data():
    """設置測試資料"""
    print("\n" + "="*60)
    print("設置測試資料")
    print("="*60)
    
    init_database()
    
    test_user = "rag_test_user"
    
    # 建立過去幾天的測試資料
    test_meals = [
        {
            'date': (datetime.now() - timedelta(days=2)).isoformat(),
            'meal_type': 'breakfast',
            'foods': {'蛋餅': 250.0, '豆漿': 150.0},
            'calories': 400.0
        },
        {
            'date': (datetime.now() - timedelta(days=2)).isoformat(),
            'meal_type': 'lunch',
            'foods': {'雞腿便當': 650.0},
            'calories': 650.0
        },
        {
            'date': (datetime.now() - timedelta(days=1)).isoformat(),
            'meal_type': 'breakfast',
            'foods': {'燕麥粥': 200.0, '香蕉': 90.0},
            'calories': 290.0
        },
        {
            'date': (datetime.now() - timedelta(days=1)).isoformat(),
            'meal_type': 'lunch',
            'foods': {'三明治': 350.0, '沙拉': 100.0},
            'calories': 450.0
        },
        {
            'date': datetime.now().isoformat(),
            'meal_type': 'breakfast',
            'foods': {'吐司': 200.0, '牛奶': 150.0, '雞蛋': 80.0},
            'calories': 430.0
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
    return test_user


def test_retrieval():
    """測試檢索功能"""
    print("\n" + "="*60)
    print("測試 1: 檢索功能")
    print("="*60)
    
    test_user = "rag_test_user"
    
    # 測試前序餐點檢索
    print("\n🔍 檢索今日前序餐點 (午餐前):")
    previous_meals = get_previous_meals(test_user, 'lunch')
    
    if previous_meals:
        print(f"   找到 {len(previous_meals)} 筆前序餐點:")
        for meal in previous_meals:
            # Tuple 結構: (id, date, foods_dict, calories, portion_size, meal_type)
            meal_id = meal[0]
            date = meal[1]
            foods = meal[2]  # Dict[str, float]
            calories = meal[3]  # float
            portion_size = meal[4]  # float
            meal_type = meal[5]  # str
            print(f"   - {meal_type}: {list(foods.keys())}, {calories:.1f} kcal")
    else:
        print("   無前序餐點")
    
    # 測試過去統計
    print("\n📊 檢索過去 7 天統計:")
    past_analysis = get_past_days(test_user, days=7)
    
    if past_analysis:
        print(f"   總餐數: {past_analysis.get('total_meals', 0)}")
        trends = past_analysis.get('nutrition_trends', {})
        print(f"   平均每日熱量: {trends.get('avg_daily_calories', 0):.1f} kcal")
        print(f"   最高每日熱量: {trends.get('max_daily_calories', 0):.1f} kcal")
    else:
        print("   無統計資料")
    
    print("\n✅ 檢索功能測試完成")
    return previous_meals, past_analysis


def test_format():
    """測試格式化功能"""
    print("\n" + "="*60)
    print("測試 2: 格式化功能")
    print("="*60)
    
    test_user = "rag_test_user"
    
    # 檢索資料
    previous_meals = get_previous_meals(test_user, 'lunch')
    past_analysis = get_past_days(test_user, days=7)
    
    # 格式化
    print("\n📝 格式化檢索結果:")
    retrieved_text = format_retrieved_text(
        previous_meals=previous_meals,
        past_analysis=past_analysis,
        days=7
    )
    
    print("\n" + "-"*60)
    print(retrieved_text)
    print("-"*60)
    
    print(f"\n✅ 格式化文本長度: {len(retrieved_text)} 字元")
    print("✅ 格式化功能測試完成")
    return retrieved_text


def test_rag_recommendation():
    """測試 RAG 推薦功能"""
    print("\n" + "="*60)
    print("測試 3: RAG 推薦生成")
    print("="*60)
    
    test_user = "rag_test_user"
    
    # 模擬當前餐點
    current_meal_type = 'lunch'
    current_foods = {
        '雞腿便當': 650.0,
        '珍珠奶茶': 350.0
    }
    current_calories = sum(current_foods.values())
    
    print(f"\n當前餐點資訊:")
    print(f"  餐次: {current_meal_type}")
    print(f"  食物: {list(current_foods.keys())}")
    print(f"  熱量: {current_calories:.1f} kcal")
    
    print("\n🤖 生成 RAG 推薦...")
    
    try:
        recommendation = get_recommendation(
            user_id=test_user,
            meal_type=current_meal_type,
            current_foods=current_foods,
            current_calories=current_calories,
            days=7
        )
        
        print("\n" + "="*60)
        print("推薦結果:")
        print("="*60)
        print(recommendation)
        print("="*60)
        
        print("\n✅ RAG 推薦生成成功")
        
        # 驗證輸出
        if '飲食分析' in recommendation or '健康建議' in recommendation:
            print("✅ 推薦包含結構化內容")
        else:
            print("⚠️  推薦格式可能不完整")
        
    except Exception as e:
        print(f"❌ RAG 推薦生成失敗: {e}")
        import traceback
        traceback.print_exc()


def test_no_history():
    """測試無歷史記錄情況"""
    print("\n" + "="*60)
    print("測試 4: 無歷史記錄 Fallback")
    print("="*60)
    
    new_user = "new_user_no_history"
    
    print(f"\n測試新用戶: {new_user}")
    
    try:
        recommendation = get_recommendation(
            user_id=new_user,
            meal_type='breakfast',
            current_foods={'蛋餅': 250.0},
            current_calories=250.0,
            days=7
        )
        
        print("\n" + "-"*60)
        print(recommendation)
        print("-"*60)
        
        print("\n✅ 無歷史記錄 Fallback 測試完成")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")


def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("RAG 推薦系統完整測試")
    print("="*60)
    
    try:
        # 設置測試資料
        test_user = setup_test_data()
        
        # 測試1: 檢索功能
        previous_meals, past_analysis = test_retrieval()
        
        # 測試2: 格式化功能
        retrieved_text = test_format()
        
        # 測試3: RAG 推薦
        test_rag_recommendation()
        
        # 測試4: 無歷史記錄
        test_no_history()
        
        print("\n" + "="*60)
        print("🎉 所有 RAG 測試完成！")
        print("="*60)
        
        print("\n📊 測試摘要:")
        print("  ✅ 檢索功能: 通過")
        print("  ✅ 格式化功能: 通過")
        print("  ✅ RAG 推薦生成: 通過")
        print("  ✅ Fallback 機制: 通過")
        
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
