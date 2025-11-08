#!/usr/bin/env python3
"""
Diet Tracker Bot - 營養計算模組
================================

這個模組負責計算食物的營養資訊，包括：
1. 從台灣食品營養成分資料庫(TFND)查詢營養資訊
2. 使用模糊匹配找出最接近的食物
3. Fallback到USDA FoodData Central API
4. 計算總熱量

設計原則：
- MVP從簡單的熱量計算開始
- 優先使用本地資料庫(TFND)
- 模糊匹配提高匹配率
- API作為後備方案

未來擴展計畫：
1. 添加更多營養素（蛋白質、脂肪、碳水化合物）
2. 支援中英文食物名稱翻譯（googletrans）
3. 份量計算（依據識別的份量調整營養值）
4. 營養素建議攝取量比較
5. 本地快取API結果
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# 模糊匹配庫
try:
    from fuzzywuzzy import process, fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    import difflib
    logging.warning("fuzzywuzzy 未安裝，使用 difflib 作為替代。建議執行: pip install fuzzywuzzy python-Levenshtein")

# 導入專案共用工具
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

from utils import handle_error, get_cached_nutrition, set_cached_nutrition

# 載入環境變數
config_path = project_root / "config" / ".env"
load_dotenv(config_path)

# 模組級別的日誌器
logger = logging.getLogger(__name__)

# 常數定義
TFND_DATA_PATH = project_root / "data" / "tfnd_2024_fixed.json"
USDA_API_BASE_URL = "https://api.nal.usda.gov/fdc/v1"
FUZZY_MATCH_THRESHOLD = 80  # 模糊匹配閾值（0-100）
DEFAULT_CALORIES = 0  # 找不到資料時的預設熱量


class NutritionCalculator:
    """
    營養計算器類別
    
    負責查詢和計算食物營養資訊：
    1. 載入TFND資料庫
    2. 精確/模糊匹配食物名稱
    3. 呼叫USDA API作為fallback
    4. 計算總熱量
    
    未來擴展：
    - 支援多種營養素查詢
    - 快取API結果
    - 批量查詢優化
    """
    
    def __init__(self):
        """初始化營養計算器"""
        self.tfnd_data = None
        self.usda_api_key = os.getenv('USDA_KEY')
        
        # 載入TFND資料庫
        self._load_tfnd_database()
    
    def _load_tfnd_database(self) -> None:
        """
        載入台灣食品營養成分資料庫（2024版）
        
        從 JSON 檔案讀取資料（中文版）
        儲存為 list of dicts 格式以便查詢。
        
        新版資料格式：
        {
            "樣品名稱": "大麥仁",
            "俗名": "小薏仁,洋薏仁,珍珠薏仁",
            "熱量(kcal)": 364.6228,
            "粗蛋白(g)": 8.5578,
            ...
        }
        """
        try:
            if not TFND_DATA_PATH.exists():
                logger.warning(f"TFND資料庫檔案不存在: {TFND_DATA_PATH}")
                self.tfnd_data = []
                return
            
            # 載入 JSON 檔案
            with open(TFND_DATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 過濾掉標題行（第一筆資料）
            if data and len(data) > 0:
                # 檢查第一筆是否為標題行（所有值都是字串且等於欄位名）
                first_item = data[0]
                if all(isinstance(v, str) and v == k for k, v in first_item.items()):
                    self.tfnd_data = data[1:]  # 跳過標題行
                    logger.debug("已跳過TFND資料庫標題行")
                else:
                    self.tfnd_data = data
            else:
                self.tfnd_data = []
            
            logger.info(f"成功載入TFND資料庫（2024版）: {len(self.tfnd_data)} 筆食物資料")
            
        except Exception as e:
            handle_error(e, "載入TFND資料庫", logger=logger, raise_error=False)
            self.tfnd_data = []
    
    def get_nutrition(self, food_list: List[str]) -> Tuple[Dict[str, float], float]:
        """
        獲取食物列表的營養資訊
        
        這是主要的入口函數，處理完整的營養查詢流程：
        1. 優先檢查快取
        2. 對每個食物嘗試精確匹配
        3. 如果失敗，使用模糊匹配
        4. 如果仍失敗，呼叫USDA API
        5. 將結果存入快取
        6. 計算總熱量
        
        Args:
            food_list (List[str]): 食物名稱列表（英文，如 ['mackerel', 'apple']）
        
        Returns:
            Tuple[Dict[str, float], float]: 
                - 字典: {食物名稱: 熱量(kcal)}
                - 總熱量(kcal)
        
        使用範例:
            calculator = NutritionCalculator()
            nutrition_dict, total = calculator.get_nutrition(['mackerel', 'apple'])
            print(f"鯖魚: {nutrition_dict['mackerel']} kcal")
            print(f"總熱量: {total} kcal")
        
        未來擴展：
        - 支援中文食物名稱輸入
        - 返回更多營養素資訊
        - 支援份量參數調整營養值
        """
        logger.info(f"開始計算 {len(food_list)} 種食物的營養資訊")
        
        nutrition_dict = {}
        
        for food_name in food_list:
            try:
                # 清理食物名稱
                clean_food_name = self._clean_food_name(food_name)
                
                # === 步驟1: 檢查快取 ===
                cached_calories = get_cached_nutrition(clean_food_name)
                if cached_calories is not None:
                    nutrition_dict[food_name] = cached_calories
                    logger.info(f"✅ {food_name}: {cached_calories:.1f} kcal (來源: 快取)")
                    continue
                
                # === 步驟2: 嘗試從TFND資料庫查詢 ===
                calories = self._query_tfnd_database(clean_food_name)
                source = 'TFND'
                
                # === 步驟3: 如果TFND查詢失敗，嘗試USDA API ===
                if calories == 0:
                    logger.info(f"TFND未找到 '{clean_food_name}'，嘗試USDA API")
                    calories = self._query_usda_api(clean_food_name)
                    source = 'USDA'
                
                # === 步驟4: 存入快取供未來使用 ===
                set_cached_nutrition(clean_food_name, calories, source)
                
                nutrition_dict[food_name] = calories
                logger.info(f"✅ {food_name}: {calories:.1f} kcal (來源: {source})")
                
            except Exception as e:
                handle_error(e, f"查詢食物 '{food_name}' 的營養資訊", 
                           logger=logger, raise_error=False)
                nutrition_dict[food_name] = DEFAULT_CALORIES
        
        # 計算總熱量
        total_calories = sum(nutrition_dict.values())
        logger.info(f"總熱量: {total_calories} kcal")
        
        return nutrition_dict, total_calories
    
    def _clean_food_name(self, food_name: str) -> str:
        """
        清理食物名稱以提高匹配率
        
        Args:
            food_name (str): 原始食物名稱
        
        Returns:
            str: 清理後的食物名稱（小寫、去除多餘空格）
        """
        # 轉小寫、去除前後空格
        cleaned = food_name.lower().strip()
        
        # 移除常見的描述詞（未來擴展：提取這些資訊用於份量計算）
        # 如 "grilled chicken" -> "chicken"
        descriptors = ['fried', 'grilled', 'baked', 'steamed', 'boiled', 'roasted',
                      'raw', 'fresh', 'cooked', 'prepared', 'stir', 'stir-fried']
        
        words = cleaned.split()
        filtered_words = [w for w in words if w not in descriptors]
        
        if filtered_words:
            cleaned = ' '.join(filtered_words)
        
        return cleaned
    
    def _query_tfnd_database(self, food_name: str) -> float:
        """
        從TFND資料庫查詢食物熱量（支援中文）
        
        查詢流程：
        1. 嘗試中文精確匹配 (樣品名稱、俗名)
        2. 如果失敗，使用模糊匹配找最接近的食物（閾值>80%）
        3. 從欄位提取熱量值
        
        Args:
            food_name (str): 食物名稱（中文）
        
        Returns:
            float: 熱量(kcal)，找不到時返回0
        """
        if not self.tfnd_data:
            logger.warning("TFND資料庫為空，無法查詢")
            return 0
        
        # 步驟1：嘗試精確匹配（中文）
        for item in self.tfnd_data:
            # 檢查樣品名稱
            name_zh = str(item.get('樣品名稱', '')).lower()
            # 檢查俗名（可能包含多個用逗號分隔）
            aliases = str(item.get('俗名', '')).lower()
            
            food_name_lower = food_name.lower()
            
            # 精確匹配樣品名稱
            if food_name_lower in name_zh or name_zh in food_name_lower:
                calories = self._extract_calories(item)
                logger.info(f"✓ 精確匹配（樣品名稱）: '{food_name}' -> '{item.get('樣品名稱')}' ({calories} kcal)")
                return calories
            
            # 精確匹配俗名
            if aliases and (food_name_lower in aliases or any(food_name_lower in alias for alias in aliases.split(','))):
                calories = self._extract_calories(item)
                logger.info(f"✓ 精確匹配（俗名）: '{food_name}' -> '{item.get('樣品名稱')}' ({calories} kcal)")
                return calories
        
        # 步驟2：模糊匹配
        logger.debug(f"精確匹配失敗，嘗試模糊匹配: '{food_name}'")
        matched_item = self._fuzzy_match_food(food_name)
        
        if matched_item:
            calories = self._extract_calories(matched_item)
            logger.info(f"✓ 模糊匹配: '{food_name}' -> '{matched_item.get('樣品名稱')}' ({calories} kcal)")
            return calories
        
        logger.debug(f"TFND資料庫未找到匹配: '{food_name}'")
        return 0
    
    def _fuzzy_match_food(self, food_name: str) -> Optional[Dict[str, Any]]:
        """
        使用模糊匹配找出最接近的食物（中文）
        
        使用 fuzzywuzzy 或 difflib 進行模糊匹配。
        只返回相似度 >= FUZZY_MATCH_THRESHOLD 的結果。
        
        Args:
            food_name (str): 食物名稱（中文）
        
        Returns:
            Optional[Dict]: 匹配的食物資料，找不到時返回None
        """
        if not self.tfnd_data:
            return None
        
        # 建立食物名稱列表（包含樣品名稱和俗名）
        food_names = []
        food_items_map = {}  # 名稱到item的映射
        
        for item in self.tfnd_data:
            name_zh = str(item.get('樣品名稱', ''))
            if name_zh:
                food_names.append(name_zh)
                food_items_map[name_zh] = item
            
            # 也加入俗名
            aliases = str(item.get('俗名', ''))
            if aliases:
                for alias in aliases.split(','):
                    alias = alias.strip()
                    if alias:
                        food_names.append(alias)
                        food_items_map[alias] = item
        
        if FUZZYWUZZY_AVAILABLE:
            # 使用 fuzzywuzzy
            result = process.extractOne(food_name, food_names, scorer=fuzz.ratio)
            
            if result and result[1] >= FUZZY_MATCH_THRESHOLD:
                matched_name, score = result[0], result[1]
                logger.debug(f"Fuzzy match: '{food_name}' -> '{matched_name}' (score: {score})")
                return food_items_map.get(matched_name)
        else:
            # 使用 difflib 作為替代
            matches = difflib.get_close_matches(
                food_name, food_names, n=1, cutoff=FUZZY_MATCH_THRESHOLD/100
            )
            
            if matches:
                matched_name = matches[0]
                logger.debug(f"Difflib match: '{food_name}' -> '{matched_name}'")
                return food_items_map.get(matched_name)
        
        return None
    
    def _extract_calories(self, food_item: Dict[str, Any]) -> float:
        """
        從食物資料中提取熱量值（2024版）
        
        Args:
            food_item (Dict): 食物資料字典
        
        Returns:
            float: 熱量(kcal)，找不到時返回0
        """
        # 新版資料格式直接從欄位取得
        calorie_keys = ['修正熱量(kcal)', '熱量(kcal)']
        
        for key in calorie_keys:
            if key in food_item:
                calorie_value = food_item[key]
                
                # 處理可能的資料類型
                if isinstance(calorie_value, (int, float)):
                    return float(calorie_value)
                elif isinstance(calorie_value, str):
                    try:
                        return float(calorie_value)
                    except ValueError:
                        logger.warning(f"無法轉換熱量值: {calorie_value}")
                        continue
        
        logger.warning(f"未找到熱量資訊: {food_item.get('樣品名稱', 'Unknown')}")
        return 0
    
    def _query_usda_api(self, food_name: str) -> float:
        """
        從USDA FoodData Central API查詢食物熱量
        
        當TFND資料庫找不到匹配時，作為fallback方案。
        使用USDA的食物搜尋API獲取熱量資訊。
        
        API文檔: https://fdc.nal.usda.gov/api-guide.html
        
        Args:
            food_name (str): 食物名稱（英文）
        
        Returns:
            float: 熱量(kcal)，查詢失敗時返回0
        
        未來擴展：
        - 快取API結果避免重複查詢
        - 實作重試機制
        - 處理API速率限制
        - 支援更多營養素查詢
        """
        if not self.usda_api_key:
            logger.warning("USDA API Key 未設定，無法查詢USDA資料庫")
            return 0
        
        try:
            # 構建API請求
            url = f"{USDA_API_BASE_URL}/foods/search"
            params = {
                'query': food_name,
                'api_key': self.usda_api_key,
                'pageSize': 1  # 只取第一個結果
            }
            
            logger.debug(f"查詢USDA API: {food_name}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 解析API回應
            if 'foods' in data and len(data['foods']) > 0:
                food = data['foods'][0]
                food_nutrients = food.get('foodNutrients', [])
                
                # 查找能量/熱量營養素
                # USDA nutrient ID: 1008 = Energy (kcal)
                for nutrient in food_nutrients:
                    nutrient_name = nutrient.get('nutrientName', '').lower()
                    nutrient_id = nutrient.get('nutrientId', 0)
                    
                    if 'energy' in nutrient_name or nutrient_id == 1008:
                        value = nutrient.get('value', 0)
                        
                        # 檢查單位，可能是kcal或kJ
                        unit = nutrient.get('unitName', '').lower()
                        if 'kj' in unit:
                            # 轉換 kJ 到 kcal (1 kcal ≈ 4.184 kJ)
                            value = value / 4.184
                        
                        logger.info(f"✓ USDA API: '{food_name}' -> {value:.1f} kcal")
                        return float(value)
            
            logger.info(f"USDA API 未找到匹配: '{food_name}'")
            return 0
            
        except requests.exceptions.RequestException as e:
            handle_error(e, f"USDA API 請求失敗: {food_name}", 
                        logger=logger, raise_error=False)
            return 0
        except Exception as e:
            handle_error(e, f"處理USDA API回應失敗: {food_name}", 
                        logger=logger, raise_error=False)
            return 0


# 便利函數供外部直接使用
def get_nutrition(food_list: List[str]) -> Tuple[Dict[str, float], float]:
    """
    獲取食物列表的營養資訊（便利函數）
    
    這是模組的主要入口點，創建NutritionCalculator實例並執行查詢。
    
    Args:
        food_list (List[str]): 食物名稱列表（英文）
    
    Returns:
        Tuple[Dict[str, float], float]: (營養字典, 總熱量)
    
    使用範例:
        from nutrition_calculator import get_nutrition
        
        foods = ['mackerel', 'apple', 'rice']
        nutrition_dict, total = get_nutrition(foods)
        
        for food, calories in nutrition_dict.items():
            print(f"{food}: {calories} kcal")
        print(f"總計: {total} kcal")
    """
    calculator = NutritionCalculator()
    return calculator.get_nutrition(food_list)


def main():
    """
    命令列測試入口點
    
    允許從命令列直接測試營養計算功能：
    python -m src.nutrition_calculator mackerel apple rice
    
    未來擴展：
    - 支援從檔案讀取食物列表
    - 輸出格式選項（JSON、CSV等）
    - 互動式查詢模式
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='測試營養計算功能')
    parser.add_argument('foods', nargs='+', help='食物名稱列表（英文）')
    parser.add_argument('--debug', action='store_true', help='啟用詳細日誌')
    
    args = parser.parse_args()
    
    # 設定日誌級別
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 查詢營養資訊
    print(f"\n🔍 正在查詢 {len(args.foods)} 種食物的營養資訊...")
    print("=" * 50)
    
    nutrition_dict, total_calories = get_nutrition(args.foods)
    
    # 顯示結果
    print("\n📊 營養資訊:")
    for food, calories in nutrition_dict.items():
        print(f"  • {food}: {calories:.1f} kcal")
    
    print(f"\n🔥 總熱量: {total_calories:.1f} kcal")
    print("=" * 50)


if __name__ == "__main__":
    main()
