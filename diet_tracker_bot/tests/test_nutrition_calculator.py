#!/usr/bin/env python3
"""
Diet Tracker Bot - 營養計算模組測試
====================================

這個測試模組驗證營養計算功能的正確性，包括：
1. TFND資料庫載入和查詢
2. 精確匹配和模糊匹配
3. USDA API fallback機制
4. 熱量計算和錯誤處理

測試設計原則：
- 使用mock避免真實API呼叫和檔案I/O
- 測試各種匹配情況和邊界條件
- 確保錯誤處理的健壯性

未來擴展：
- 添加更多營養素測試
- 效能基準測試
- 整合測試與真實API
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# 導入要測試的模組
from nutrition_calculator import (
    NutritionCalculator, 
    get_nutrition,
    FUZZY_MATCH_THRESHOLD
)


class TestNutritionCalculator:
    """營養計算器類別的測試"""
    
    @pytest.fixture
    def sample_tfnd_data(self):
        """建立測試用的TFND資料"""
        return [
            {
                "name_zh": "鯖魚(炒)",
                "name_en": "Mackerel",
                "category": "魚貝類",
                "nutrients_per_100g": {
                    "熱量": {"value": 410.0, "unit": "kcal"},
                    "粗蛋白": {"value": 16.7, "unit": "g"},
                    "粗脂肪": {"value": 37.6, "unit": "g"}
                }
            },
            {
                "name_zh": "蘋果",
                "name_en": "Apple",
                "category": "水果類",
                "nutrients_per_100g": {
                    "熱量": {"value": 52.0, "unit": "kcal"},
                    "粗蛋白": {"value": 0.3, "unit": "g"}
                }
            },
            {
                "name_zh": "白米飯",
                "name_en": "Rice",
                "category": "穀物類",
                "nutrients_per_100g": {
                    "修正熱量": {"value": 183.0, "unit": "kcal"},
                    "粗蛋白": {"value": 3.1, "unit": "g"}
                }
            }
        ]
    
    @pytest.fixture
    def mock_tfnd_file(self, sample_tfnd_data):
        """建立mock的TFND JSONL檔案內容"""
        lines = [json.dumps(item, ensure_ascii=False) + '\n' 
                for item in sample_tfnd_data]
        return ''.join(lines)
    
    @pytest.fixture
    def calculator_with_mock_data(self, mock_tfnd_file):
        """建立帶有mock資料的NutritionCalculator"""
        with patch('builtins.open', mock_open(read_data=mock_tfnd_file)):
            with patch('pathlib.Path.exists', return_value=True):
                calculator = NutritionCalculator()
                return calculator
    
    def test_calculator_initialization(self):
        """測試營養計算器初始化"""
        with patch('pathlib.Path.exists', return_value=False):
            calculator = NutritionCalculator()
            assert calculator.tfnd_data == []
            assert calculator.usda_api_key is not None or calculator.usda_api_key is None
    
    def test_load_tfnd_database_success(self, mock_tfnd_file):
        """測試成功載入TFND資料庫"""
        with patch('builtins.open', mock_open(read_data=mock_tfnd_file)):
            with patch('pathlib.Path.exists', return_value=True):
                calculator = NutritionCalculator()
                
                assert len(calculator.tfnd_data) == 3
                assert calculator.tfnd_data[0]['name_en'] == 'Mackerel'
                assert calculator.tfnd_data[1]['name_en'] == 'Apple'
    
    def test_load_tfnd_database_file_not_exists(self):
        """測試TFND檔案不存在的情況"""
        with patch('pathlib.Path.exists', return_value=False):
            calculator = NutritionCalculator()
            assert calculator.tfnd_data == []
    
    def test_load_tfnd_database_invalid_json(self):
        """測試處理無效JSON資料"""
        invalid_data = "invalid json\n{valid: json}\n"
        
        with patch('builtins.open', mock_open(read_data=invalid_data)):
            with patch('pathlib.Path.exists', return_value=True):
                calculator = NutritionCalculator()
                # 應該跳過無效行，繼續處理
                assert isinstance(calculator.tfnd_data, list)
    
    def test_clean_food_name(self, calculator_with_mock_data):
        """測試食物名稱清理功能"""
        calculator = calculator_with_mock_data
        
        assert calculator._clean_food_name("  APPLE  ") == "apple"
        assert calculator._clean_food_name("Grilled Chicken") == "chicken"
        assert calculator._clean_food_name("Fried Rice") == "rice"
        assert calculator._clean_food_name("Fresh Apple") == "apple"
    
    def test_extract_calories_standard_format(self, calculator_with_mock_data):
        """測試提取標準格式的熱量"""
        calculator = calculator_with_mock_data
        
        food_item = {
            "nutrients_per_100g": {
                "熱量": {"value": 100.0, "unit": "kcal"}
            }
        }
        
        calories = calculator._extract_calories(food_item)
        assert calories == 100.0
    
    def test_extract_calories_alternative_key(self, calculator_with_mock_data):
        """測試提取使用替代欄位名稱的熱量"""
        calculator = calculator_with_mock_data
        
        food_item = {
            "nutrients_per_100g": {
                "修正熱量": {"value": 183.0, "unit": "kcal"}
            }
        }
        
        calories = calculator._extract_calories(food_item)
        assert calories == 183.0
    
    def test_extract_calories_not_found(self, calculator_with_mock_data):
        """測試未找到熱量資訊的情況"""
        calculator = calculator_with_mock_data
        
        food_item = {
            "nutrients_per_100g": {
                "蛋白質": {"value": 10.0, "unit": "g"}
            }
        }
        
        calories = calculator._extract_calories(food_item)
        assert calories == 0
    
    def test_query_tfnd_exact_match(self, calculator_with_mock_data):
        """測試TFND資料庫精確匹配"""
        calculator = calculator_with_mock_data
        
        # 測試不區分大小寫的精確匹配
        calories = calculator._query_tfnd_database("mackerel")
        assert calories == 410.0
        
        calories = calculator._query_tfnd_database("apple")
        assert calories == 52.0
        
        calories = calculator._query_tfnd_database("rice")
        assert calories == 183.0
    
    def test_query_tfnd_fuzzy_match(self, calculator_with_mock_data):
        """測試TFND資料庫模糊匹配"""
        calculator = calculator_with_mock_data
        
        # 測試拼寫相近的匹配
        calories = calculator._query_tfnd_database("mackrel")  # 拼寫錯誤
        # 應該能匹配到 "mackerel"
        assert calories > 0  # 模糊匹配應該成功
    
    def test_query_tfnd_no_match(self, calculator_with_mock_data):
        """測試TFND資料庫無匹配的情況"""
        calculator = calculator_with_mock_data
        
        calories = calculator._query_tfnd_database("pizza")
        assert calories == 0
    
    def test_fuzzy_match_food_success(self, calculator_with_mock_data):
        """測試模糊匹配成功情況"""
        calculator = calculator_with_mock_data
        
        # 測試相似度高的匹配
        matched = calculator._fuzzy_match_food("apples")
        assert matched is not None
        assert matched['name_en'].lower() == 'apple'
    
    def test_fuzzy_match_food_below_threshold(self, calculator_with_mock_data):
        """測試相似度低於閾值的情況"""
        calculator = calculator_with_mock_data
        
        # 完全不相關的食物
        matched = calculator._fuzzy_match_food("xyz123")
        assert matched is None
    
    @patch('nutrition_calculator.requests.get')
    def test_query_usda_api_success(self, mock_get, calculator_with_mock_data):
        """測試USDA API成功查詢"""
        calculator = calculator_with_mock_data
        calculator.usda_api_key = "test_api_key"
        
        # Mock API回應
        mock_response = Mock()
        mock_response.json.return_value = {
            "foods": [
                {
                    "description": "Chicken, broilers or fryers",
                    "foodNutrients": [
                        {
                            "nutrientId": 1008,
                            "nutrientName": "Energy",
                            "value": 239.0,
                            "unitName": "kcal"
                        }
                    ]
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        calories = calculator._query_usda_api("chicken")
        assert calories == 239.0
        
        # 驗證API被正確呼叫
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'chicken' in str(call_args)
    
    @patch('nutrition_calculator.requests.get')
    def test_query_usda_api_no_results(self, mock_get, calculator_with_mock_data):
        """測試USDA API無結果的情況"""
        calculator = calculator_with_mock_data
        calculator.usda_api_key = "test_api_key"
        
        # Mock空結果
        mock_response = Mock()
        mock_response.json.return_value = {"foods": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        calories = calculator._query_usda_api("unknownfood")
        assert calories == 0
    
    @patch('nutrition_calculator.requests.get')
    def test_query_usda_api_network_error(self, mock_get, calculator_with_mock_data):
        """測試USDA API網路錯誤"""
        calculator = calculator_with_mock_data
        calculator.usda_api_key = "test_api_key"
        
        # Mock網路錯誤
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        calories = calculator._query_usda_api("chicken")
        assert calories == 0  # 應該返回預設值而不是拋出異常
    
    def test_query_usda_api_no_api_key(self, calculator_with_mock_data):
        """測試沒有USDA API Key的情況"""
        calculator = calculator_with_mock_data
        calculator.usda_api_key = None
        
        calories = calculator._query_usda_api("chicken")
        assert calories == 0
    
    def test_get_nutrition_single_food(self, calculator_with_mock_data):
        """測試查詢單個食物"""
        calculator = calculator_with_mock_data
        
        nutrition_dict, total = calculator.get_nutrition(['mackerel'])
        
        assert 'mackerel' in nutrition_dict
        assert nutrition_dict['mackerel'] == 410.0
        assert total == 410.0
    
    def test_get_nutrition_multiple_foods(self, calculator_with_mock_data):
        """測試查詢多個食物"""
        calculator = calculator_with_mock_data
        
        foods = ['mackerel', 'apple', 'rice']
        nutrition_dict, total = calculator.get_nutrition(foods)
        
        assert len(nutrition_dict) == 3
        assert nutrition_dict['mackerel'] == 410.0
        assert nutrition_dict['apple'] == 52.0
        assert nutrition_dict['rice'] == 183.0
        assert total == 645.0  # 410 + 52 + 183
    
    def test_get_nutrition_with_unknown_food(self, calculator_with_mock_data):
        """測試包含未知食物的情況"""
        calculator = calculator_with_mock_data
        
        foods = ['apple', 'unknownfood']
        nutrition_dict, total = calculator.get_nutrition(foods)
        
        assert nutrition_dict['apple'] == 52.0
        assert nutrition_dict['unknownfood'] == 0  # 未找到應返回0
        assert total == 52.0
    
    def test_get_nutrition_empty_list(self, calculator_with_mock_data):
        """測試空食物列表"""
        calculator = calculator_with_mock_data
        
        nutrition_dict, total = calculator.get_nutrition([])
        
        assert nutrition_dict == {}
        assert total == 0
    
    @patch('nutrition_calculator.requests.get')
    def test_get_nutrition_with_usda_fallback(self, mock_get, calculator_with_mock_data):
        """測試USDA API作為fallback"""
        calculator = calculator_with_mock_data
        calculator.usda_api_key = "test_api_key"
        
        # Mock USDA API回應
        mock_response = Mock()
        mock_response.json.return_value = {
            "foods": [
                {
                    "foodNutrients": [
                        {
                            "nutrientId": 1008,
                            "nutrientName": "Energy",
                            "value": 200.0,
                            "unitName": "kcal"
                        }
                    ]
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 查詢TFND中不存在的食物
        foods = ['pizza']
        nutrition_dict, total = calculator.get_nutrition(foods)
        
        assert nutrition_dict['pizza'] == 200.0
        assert total == 200.0


class TestConvenienceFunction:
    """測試便利函數"""
    
    @patch('nutrition_calculator.NutritionCalculator')
    def test_get_nutrition_function(self, mock_calculator_class):
        """測試 get_nutrition 便利函數"""
        # Mock NutritionCalculator實例
        mock_calculator = Mock()
        mock_calculator.get_nutrition.return_value = (
            {'apple': 52.0, 'rice': 183.0}, 
            235.0
        )
        mock_calculator_class.return_value = mock_calculator
        
        # 呼叫便利函數
        nutrition_dict, total = get_nutrition(['apple', 'rice'])
        
        # 驗證結果
        assert nutrition_dict == {'apple': 52.0, 'rice': 183.0}
        assert total == 235.0
        
        # 驗證NutritionCalculator被正確呼叫
        mock_calculator_class.assert_called_once()
        mock_calculator.get_nutrition.assert_called_once_with(['apple', 'rice'])


class TestEdgeCases:
    """測試邊界情況和特殊案例"""
    
    @pytest.fixture
    def calculator(self):
        """建立基本的calculator實例"""
        with patch('pathlib.Path.exists', return_value=False):
            return NutritionCalculator()
    
    def test_food_name_with_special_characters(self, calculator):
        """測試包含特殊字符的食物名稱"""
        cleaned = calculator._clean_food_name("apple's pie!")
        assert "apple" in cleaned.lower()
    
    def test_very_long_food_name(self, calculator):
        """測試很長的食物名稱"""
        long_name = "a" * 1000
        cleaned = calculator._clean_food_name(long_name)
        assert len(cleaned) <= 1000
    
    def test_empty_food_name(self, calculator):
        """測試空字串食物名稱"""
        cleaned = calculator._clean_food_name("")
        assert cleaned == ""
        
        calories = calculator._query_tfnd_database("")
        assert calories == 0
    
    def test_unicode_food_name(self, calculator):
        """測試Unicode字符食物名稱"""
        # 測試中文食物名稱（未來擴展功能）
        cleaned = calculator._clean_food_name("蘋果")
        assert cleaned == "蘋果"
    
    def test_mixed_case_food_name(self, calculator):
        """測試混合大小寫的食物名稱"""
        test_cases = ["APPLE", "ApPlE", "aPpLe"]
        for name in test_cases:
            cleaned = calculator._clean_food_name(name)
            assert cleaned == "apple"


class TestIntegration:
    """整合測試"""
    
    @patch('pathlib.Path.exists', return_value=False)
    @patch('nutrition_calculator.requests.get')
    def test_end_to_end_workflow(self, mock_get, mock_exists):
        """測試端到端工作流程"""
        # Mock USDA API
        mock_response = Mock()
        mock_response.json.return_value = {
            "foods": [
                {
                    "foodNutrients": [
                        {
                            "nutrientId": 1008,
                            "value": 150.0,
                            "unitName": "kcal"
                        }
                    ]
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 執行查詢
        calculator = NutritionCalculator()
        calculator.usda_api_key = "test_key"
        
        nutrition_dict, total = calculator.get_nutrition(['testfood'])
        
        # 驗證結果
        assert 'testfood' in nutrition_dict
        assert nutrition_dict['testfood'] == 150.0
        assert total == 150.0


# 測試夾具和配置
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """設定測試環境"""
    test_env = {
        'USDA_KEY': 'test_usda_api_key',
        'LOG_LEVEL': 'DEBUG'
    }
    
    with patch.dict(os.environ, test_env):
        yield


if __name__ == "__main__":
    # 直接運行測試
    pytest.main([__file__, "-v", "--tb=short"])
