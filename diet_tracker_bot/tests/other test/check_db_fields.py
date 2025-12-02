import json

# 載入TFND資料
with open('data/tfnd_2024_fixed.json', encoding='utf-8') as f:
    data = json.load(f)

print("=== 資料庫欄位分析 ===\n")
print(f"總筆數: {len(data)}")
print(f"\n第1筆資料的所有欄位:")
print(list(data[0].keys())[:20])

print("\n\n=== 前5筆資料的名稱欄位 ===\n")
for i, item in enumerate(data[:5]):
    name_zh = item.get('name_zh', 'N/A')
    sample_name = item.get('樣品名稱', 'N/A')
    alias = item.get('俗名', 'N/A')
    print(f"{i+1}. name_zh='{name_zh}'")
    print(f"   樣品名稱='{sample_name}'")
    print(f"   俗名='{alias}'")
    print()

# 搜尋包含「魚」的食物
print("\n=== 搜尋包含「魚」的食物 ===\n")
fish_items = [item for item in data if '魚' in item.get('樣品名稱', '')]
for item in fish_items[:5]:
    print(f"- {item.get('樣品名稱')} (熱量: {item.get('熱量(kcal)', 0)})")
