from src.nutrition_calculator import NutritionCalculator
import json

calc = NutritionCalculator()

# 測試多種食物
test_cases = [
    ['雞胸肉', '花椰菜', '糙米飯'],  # 健身餐
    ['豬肉', '高麗菜', '番茄'],      # 家常菜
    ['鮭魚', '蘋果', '牛奶'],        # 混合餐
]

print("=== 多種食物組合測試 ===\n")
for i, foods in enumerate(test_cases, 1):
    print(f"【測試 {i}】: {', '.join(foods)}")
    nutrition_dict, totals = calc.get_nutrition(foods)
    
    for food_name, nutrients in nutrition_dict.items():
        print(f"  • {food_name}: {nutrients['calories']:.0f} kcal | "
              f"P:{nutrients['protein']:.1f}g | "
              f"C:{nutrients['carbs']:.1f}g | "
              f"F:{nutrients['fat']:.1f}g")
    
    print(f"  ✓ 總計: {totals['calories']:.0f} kcal | "
          f"P:{totals['protein']:.1f}g | "
          f"C:{totals['carbs']:.1f}g | "
          f"F:{totals['fat']:.1f}g")
    print()
