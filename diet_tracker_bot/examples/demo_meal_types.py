#!/usr/bin/env python3
"""
餐次類型功能演示
================

展示新增的餐次類型分類、份量追蹤和智慧分析功能。
包括：
1. 餐次類型儲存 (breakfast, lunch, dinner, snack)
2. 份量大小追蹤
3. 前序餐點查詢
4. 多日營養趨勢分析

🔮 未來 RAG 向量檢索準備完成
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# 添加src目錄到路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

# 導入我們的模組
from data_storage import (
    init_database, 
    store_meal, 
    get_previous_meals,
    get_past_days,
    get_meal_by_id
)

def print_section(title: str):
    """打印區段標題"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")

def demonstrate_meal_types():
    """演示餐次類型功能"""
    print_section("餐次類型儲存演示")
    
    user_id = "demo_user_001"
    
    # 今日早餐
    breakfast_foods = {"燕麥片": 150.0, "牛奶": 60.0, "藍莓": 40.0}
    breakfast_calories = sum(breakfast_foods.values())
    breakfast_id = store_meal(
        user_id=user_id,
        foods=breakfast_foods,
        calories=breakfast_calories,
        meal_type="breakfast",
        portion_size=250.0
    )
    print(f"✅ 早餐記錄已儲存: ID={breakfast_id}")
    print(f"   食物: {breakfast_foods}")
    print(f"   總熱量: {breakfast_calories} kcal, 份量: 250g")
    
    # 今日午餐
    lunch_foods = {"雞胸肉": 200.0, "花椰菜": 25.0, "糙米飯": 110.0}
    lunch_calories = sum(lunch_foods.values())
    lunch_id = store_meal(
        user_id=user_id,
        foods=lunch_foods,
        calories=lunch_calories,
        meal_type="lunch",
        portion_size=300.0
    )
    print(f"✅ 午餐記錄已儲存: ID={lunch_id}")
    print(f"   食物: {lunch_foods}")
    print(f"   總熱量: {lunch_calories} kcal, 份量: 300g")
    
    # 下午點心
    snack_foods = {"蘋果": 52.0, "核桃": 185.0}
    snack_calories = sum(snack_foods.values())
    snack_id = store_meal(
        user_id=user_id,
        foods=snack_foods,
        calories=snack_calories,
        meal_type="snack",
        portion_size=80.0
    )
    print(f"✅ 點心記錄已儲存: ID={snack_id}")
    print(f"   食物: {snack_foods}")
    print(f"   總熱量: {snack_calories} kcal, 份量: 80g")
    
    return user_id

def demonstrate_previous_meals(user_id: str):
    """演示前序餐點查詢"""
    print_section("前序餐點智慧查詢")
    
    # 晚餐前查看已吃的餐點
    print("🍽️  晚餐前查詢今日已攝取餐點：")
    previous_meals = get_previous_meals(user_id, "dinner")
    
    total_calories = 0
    for i, meal in enumerate(previous_meals, 1):
        meal_id, date, foods, calories, portion_size, meal_type = meal
        total_calories += calories
        
        print(f"   {i}. {meal_type.upper()}: {calories} kcal ({portion_size}g)")
        for food, cal in foods.items():
            print(f"      - {food}: {cal} kcal")
    
    print(f"\n📊 今日已攝取總熱量: {total_calories} kcal")
    remaining_calories = 2000 - total_calories  # 假設每日目標 2000 kcal
    print(f"💡 建議晚餐熱量: 約 {remaining_calories} kcal")
    
    # 午餐時查看早餐
    print(f"\n🥪 午餐時查詢早餐記錄：")
    breakfast_only = get_previous_meals(user_id, "lunch")
    for meal in breakfast_only:
        meal_id, date, foods, calories, portion_size, meal_type = meal
        print(f"   早餐: {calories} kcal - {list(foods.keys())}")

def demonstrate_past_days_analysis(user_id: str):
    """演示多日營養分析"""
    print_section("多日營養趨勢分析")
    
    # 添加前幾天的記錄用於分析
    print("📅 創建歷史記錄...")
    
    # 昨天
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    store_meal(user_id, {"義大利麵": 350.0, "番茄醬": 30.0}, 380.0,
               date=yesterday, meal_type="lunch", portion_size=250.0)
    store_meal(user_id, {"烤魚": 180.0, "蔬菜沙拉": 50.0}, 230.0,
               date=yesterday, meal_type="dinner", portion_size=200.0)
    
    # 前天
    day_before = (datetime.now() - timedelta(days=2)).isoformat()
    store_meal(user_id, {"三明治": 280.0, "橙汁": 110.0}, 390.0,
               date=day_before, meal_type="breakfast", portion_size=180.0)
    store_meal(user_id, {"拉麵": 450.0}, 450.0,
               date=day_before, meal_type="dinner", portion_size=350.0)
    
    # 執行分析
    print("\n🔍 分析過去 3 天的飲食模式...")
    analysis = get_past_days(user_id, days=3)
    
    # 顯示每日摘要
    print(f"\n📈 每日營養摘要 (共 {analysis['analysis_period_days']} 天):")
    for day in analysis['daily_summaries']:
        print(f"   📅 {day['date']}: {day['total_calories']} kcal")
        for meal_type, count in day['meal_types'].items():
            if count > 0:
                print(f"      - {meal_type}: {count} 次")
    
    # 顯示營養趨勢
    trends = analysis['nutrition_trends']
    print(f"\n📊 營養趨勢分析:")
    print(f"   平均每日熱量: {trends['avg_daily_calories']:.1f} kcal")
    print(f"   最高單日熱量: {trends['max_daily_calories']:.1f} kcal")
    print(f"   最低單日熱量: {trends['min_daily_calories']:.1f} kcal")
    print(f"   熱量變異度: {trends['calorie_variance']:.1f}")
    
    # 顯示餐次統計
    print(f"\n🍽️ 餐次類型分布 (總計 {analysis['total_meals']} 餐):")
    for meal_type, percentage in analysis['meal_type_stats'].items():
        print(f"   {meal_type}: {percentage:.1f}%")
    
    # 顯示智慧建議
    print(f"\n💡 個性化營養建議:")
    for i, recommendation in enumerate(analysis['recommendations'], 1):
        print(f"   {i}. {recommendation}")
    
    print(f"\n📏 平均份量: {analysis['average_portion']}g")

def demonstrate_enhanced_meal_record():
    """演示增強的餐點記錄查詢"""
    print_section("增強記錄查詢功能")
    
    # 儲存一筆完整記錄
    user_id = "demo_user_002"
    foods = {"鮭魚": 200.0, "酪梨": 160.0, "藜麥": 120.0}
    calories = sum(foods.values())
    
    record_id = store_meal(
        user_id=user_id,
        foods=foods,
        calories=calories,
        meal_type="dinner",
        portion_size=280.0
    )
    
    # 查詢並顯示完整資訊
    meal = get_meal_by_id(record_id)
    if meal:
        print("🔍 餐點詳細資訊:")
        print(f"   記錄 ID: {meal[0]}")
        print(f"   用戶: {meal[1]}")
        print(f"   日期: {meal[2]}")
        print(f"   食物: {meal[3]}")
        print(f"   熱量: {meal[4]} kcal")
        print(f"   創建時間: {meal[5]}")
        print(f"   🚀 餐次類型: {meal[6]}")
        print(f"   🚀 份量大小: {meal[7]}g")

def demonstrate_rag_preparation():
    """演示 RAG 向量檢索準備"""
    print_section("未來 RAG 向量檢索擴展預覽")
    
    print("🔮 準備中的 AI 功能：")
    print()
    print("1. 🧠 語義相似檢索:")
    print("   - 使用 sentence-transformers 嵌入餐點描述")
    print("   - 向量資料庫 (Pinecone/Weaviate) 儲存嵌入")
    print("   - 智慧推薦相似營養搭配")
    print()
    print("2. 📊 機器學習趨勢預測:")
    print("   - 預測用戶營養需求趨勢")
    print("   - 個性化熱量建議")
    print("   - 營養缺口智慧填補")
    print()
    print("3. 🤖 智慧營養師助理:")
    print("   - 結合歷史資料的個性化建議")
    print("   - 相似用戶模式學習")
    print("   - 動態調整營養目標")
    
    print("\n💾 現有架構已為 RAG 擴展做好準備:")
    print("   ✅ 餐次類型分類完成")
    print("   ✅ 時序分析框架建立")
    print("   ✅ 向量嵌入預留欄位規劃")
    print("   ✅ 語義檢索接口設計完成")

def main():
    """主演示函數"""
    print("🍽️ 智慧營養追蹤系統 - 餐次類型功能演示")
    print("=" * 60)
    
    # 初始化資料庫
    init_database()
    print("✅ 資料庫初始化完成 (包含餐次功能遷移)")
    
    try:
        # 演示各功能
        user_id = demonstrate_meal_types()
        demonstrate_previous_meals(user_id)
        demonstrate_past_days_analysis(user_id)
        demonstrate_enhanced_meal_record()
        demonstrate_rag_preparation()
        
        print_section("演示完成")
        print("🎉 所有餐次類型功能演示完成！")
        print("📝 新功能摘要:")
        print("   ✅ 餐次類型分類 (breakfast/lunch/dinner/snack)")
        print("   ✅ 份量大小追蹤")
        print("   ✅ 前序餐點智慧查詢")
        print("   ✅ 多日營養趨勢分析")
        print("   ✅ 向後相容性保證")
        print("   ✅ RAG 向量檢索準備就緒")
        
    except Exception as e:
        print(f"❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()