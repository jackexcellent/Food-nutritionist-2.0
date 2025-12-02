from src.nutrition_calculator import NutritionCalculator
import json

calc = NutritionCalculator()

test_foods = ['鯖魚', '白飯', '雞胸肉', '番茄']

print("=== 食物名稱匹配測試 ===\n")
for food in test_foods:
    result = calc._query_tfnd_database(food)
    if result:
        matched_name = result.get('樣品名稱', 'Unknown')
        nutrients = calc._extract_nutrients(result)
        print(f"搜尋: {food}")
        print(f"匹配: {matched_name}")
        print(f"營養: 熱量={nutrients['calories']:.1f} kcal, 蛋白質={nutrients['protein']:.1f}g, 碳水={nutrients['carbs']:.1f}g, 脂肪={nutrients['fat']:.1f}g")
        print()
    else:
        print(f"搜尋: {food} → 未找到\n")

print("\n=== 完整 get_nutrition 測試 ===\n")
result = calc.get_nutrition(['鯖魚', '白飯'])
print(json.dumps(result[0], indent=2, ensure_ascii=False))
print("\n總營養素:")
print(json.dumps(result[1], indent=2, ensure_ascii=False))
