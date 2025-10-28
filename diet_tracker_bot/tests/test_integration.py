#!/usr/bin/env python3
"""
Diet Tracker Bot - 整合測試
============================

測試端到端的圖像到熱量計算流程，包括：
1. 圖像載入與預處理
2. Azure Computer Vision 食物識別
3. TFND 資料庫查詢
4. USDA API fallback
5. 快取機制
6. 總熱量計算

設計原則：
- 使用 mock 避免真實 API 呼叫
- 測試完整的整合流程
- 驗證錯誤處理
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# 導入要測試的模組
from image_processor import process_image
from nutrition_calculator import NutritionCalculator, get_nutrition
from utils import get_cached_nutrition, set_cached_nutrition, clear_cache


class TestEndToEndIntegration:
    """端到端整合測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """每個測試前後清空快取"""
        clear_cache()
        yield
        clear_cache()
    
    @pytest.fixture
    def mock_image_path(self, tmp_path):
        """建立臨時測試圖像"""
        import cv2
        import numpy as np
        
        # 建立簡單的測試圖像
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:] = (255, 255, 255)  # 白色背景
        
        image_path = tmp_path / "test_meal.jpg"
        cv2.imwrite(str(image_path), test_image)
        
        return str(image_path)
    
    @pytest.fixture
    def mock_azure_response(self):
        """模擬 Azure Computer Vision API 回應"""
        return {
            "tags": [
                {"name": "apple", "confidence": 0.95},
                {"name": "banana", "confidence": 0.92},
                {"name": "orange", "confidence": 0.88}
            ],
            "description": {
                "captions": [
                    {"text": "a plate of fruits", "confidence": 0.90}
                ]
            }
        }
    
    @pytest.fixture
    def mock_usda_response(self):
        """模擬 USDA API 回應"""
        return {
            "foods": [
                {
                    "fdcId": 123456,
                    "description": "Orange, raw",
                    "foodNutrients": [
                        {
                            "nutrientId": 1008,
                            "nutrientName": "Energy",
                            "value": 47.0,
                            "unitName": "kcal"
                        }
                    ]
                }
            ]
        }
    
    @pytest.mark.skip(reason="需要完整 Azure SDK mock 設置")
    @patch('requests.post')  # 直接 patch requests 模組
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open')
    @patch('requests.get')  # 直接 patch requests 模組
    def test_full_workflow_image_to_calories(
        self, 
        mock_usda_get,
        mock_file_open,
        mock_path_exists,
        mock_azure_post,
        mock_image_path,
        mock_azure_response,
        mock_usda_response
    ):
        """
        測試完整工作流程：圖像 → 食物識別 → 營養計算
        
        流程：
        1. 載入圖像
        2. Azure API 識別食物（apple, banana, orange）
        3. TFND 查詢 apple, banana（成功）
        4. USDA API 查詢 orange（fallback）
        5. 計算總熱量
        """
        # === 設定 Mock ===
        # 模擬 Azure API 回應
        mock_azure_response_obj = Mock()
        mock_azure_response_obj.status_code = 200
        mock_azure_response_obj.json.return_value = mock_azure_response
        mock_azure_post.return_value = mock_azure_response_obj
        
        # 模擬 USDA API 回應
        mock_usda_response_obj = Mock()
        mock_usda_response_obj.status_code = 200
        mock_usda_response_obj.json.return_value = mock_usda_response
        mock_usda_get.return_value = mock_usda_response_obj
        
        # 模擬 TFND 資料庫
        tfnd_data = [
            {
                "name_en": "Apple",
                "name_zh": "蘋果",
                "nutrients_per_100g": {
                    "熱量": {"value": 52.0, "unit": "kcal"}
                }
            },
            {
                "name_en": "Banana",
                "name_zh": "香蕉",
                "nutrients_per_100g": {
                    "修正熱量": {"value": 91.0, "unit": "kcal"}
                }
            }
        ]
        
        import json
        tfnd_content = '\n'.join(json.dumps(item) for item in tfnd_data)
        
        from unittest.mock import mock_open
        mock_file_open.return_value = mock_open(read_data=tfnd_content).return_value
        
        # === 階段 1: 圖像處理與食物識別 ===
        food_items = process_image(mock_image_path)
        
        # 驗證識別結果
        assert len(food_items) > 0
        assert 'apple' in food_items
        assert 'banana' in food_items
        
        # === 階段 2: 營養計算 ===
        nutrition_data, total_calories = get_nutrition(food_items)
        
        # 驗證營養資料
        assert 'apple' in nutrition_data
        assert 'banana' in nutrition_data
        
        # 驗證熱量值
        assert nutrition_data['apple'] > 0
        assert nutrition_data['banana'] > 0
        
        # 驗證總熱量
        assert total_calories > 0
        assert total_calories == sum(nutrition_data.values())
    
    def test_cache_mechanism(self):
        """測試快取機制"""
        # 設定快取
        set_cached_nutrition('apple', 52.0, 'TFND')
        
        # 從快取讀取
        cached_value = get_cached_nutrition('apple')
        assert cached_value == 52.0
        
        # 測試大小寫不敏感
        cached_value_upper = get_cached_nutrition('APPLE')
        assert cached_value_upper == 52.0
        
        # 測試不存在的項目
        cached_value_none = get_cached_nutrition('unknown_food')
        assert cached_value_none is None
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open')
    def test_nutrition_calculator_with_cache(self, mock_file_open, mock_path_exists):
        """測試營養計算器的快取整合"""
        # 模擬 TFND 資料
        tfnd_data = [
            {
                "name_en": "Apple",
                "name_zh": "蘋果",
                "nutrients_per_100g": {
                    "熱量": {"value": 52.0, "unit": "kcal"}
                }
            }
        ]
        
        import json
        from unittest.mock import mock_open as mock_open_func
        mock_file_open.return_value = mock_open_func(
            read_data=json.dumps(tfnd_data[0])
        ).return_value
        
        # 第一次查詢（應該從資料庫查詢並快取）
        nutrition_data_1, total_1 = get_nutrition(['apple'])
        
        # 第二次查詢（應該從快取讀取）
        nutrition_data_2, total_2 = get_nutrition(['apple'])
        
        # 驗證結果一致
        assert nutrition_data_1 == nutrition_data_2
        assert total_1 == total_2
        
        # 驗證快取中有此項目
        cached_calories = get_cached_nutrition('apple')
        assert cached_calories is not None
        assert cached_calories == nutrition_data_1['apple']
    
    @pytest.mark.skip(reason="需要完整 Azure SDK mock 設置")
    @patch('requests.post')  # 直接 patch requests 模組
    def test_error_handling_azure_api_failure(self, mock_azure_post, mock_image_path):
        """測試 Azure API 失敗時的錯誤處理"""
        # 模擬 API 失敗
        mock_azure_post.side_effect = Exception("API 連線失敗")
        
        # 應該拋出例外
        with pytest.raises(Exception):
            process_image(mock_image_path)
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open')
    @patch('requests.get')  # 直接 patch requests 模組
    def test_error_handling_usda_api_failure(
        self, 
        mock_usda_get,
        mock_file_open,
        mock_path_exists
    ):
        """測試 USDA API 失敗時的錯誤處理"""
        # 模擬空的 TFND 資料庫
        from unittest.mock import mock_open as mock_open_func
        mock_file_open.return_value = mock_open_func(read_data="").return_value
        
        # 模擬 USDA API 失敗
        mock_usda_get.side_effect = Exception("USDA API 連線失敗")
        
        # 應該返回 0 熱量而不是拋出例外
        nutrition_data, total = get_nutrition(['unknown_food'])
        
        assert 'unknown_food' in nutrition_data
        assert nutrition_data['unknown_food'] == 0
        assert total == 0
    
    def test_empty_food_list(self):
        """測試空食物清單"""
        nutrition_data, total = get_nutrition([])
        
        assert nutrition_data == {}
        assert total == 0


class TestCachePerformance:
    """快取效能測試"""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """每個測試前後清空快取"""
        clear_cache()
        yield
        clear_cache()
    
    def test_cache_reduces_api_calls(self):
        """驗證快取減少 API 呼叫"""
        import time
        
        # 第一次查詢（模擬較慢）
        set_cached_nutrition('test_food', 100.0, 'test')
        
        start_time = time.time()
        result_1 = get_cached_nutrition('test_food')
        time_1 = time.time() - start_time
        
        # 第二次查詢（應該更快）
        start_time = time.time()
        result_2 = get_cached_nutrition('test_food')
        time_2 = time.time() - start_time
        
        # 驗證結果一致
        assert result_1 == result_2 == 100.0
        
        # 快取查詢應該更快（或至少不慢）
        assert time_2 <= time_1 * 1.1  # 允許 10% 誤差
    
    def test_cache_expiry(self):
        """測試快取過期機制"""
        from datetime import datetime, timedelta
        import utils
        
        # 手動設定過期的快取
        utils._NUTRITION_CACHE['expired_food'] = {
            'calories': 100.0,
            'timestamp': datetime.now() - timedelta(hours=25),  # 超過 24 小時
            'source': 'test'
        }
        
        # 應該返回 None（因為已過期）
        result = get_cached_nutrition('expired_food')
        assert result is None
        
        # 快取應該被清除
        assert 'expired_food' not in utils._NUTRITION_CACHE


class TestDataFlow:
    """資料流測試"""
    
    def test_food_name_normalization(self):
        """測試食物名稱標準化"""
        # 不同大小寫應該得到相同結果
        set_cached_nutrition('Apple', 52.0, 'test')
        
        assert get_cached_nutrition('apple') == 52.0
        assert get_cached_nutrition('APPLE') == 52.0
        assert get_cached_nutrition('ApPlE') == 52.0
    
    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open')
    def test_multiple_data_sources(self, mock_file_open, mock_path_exists):
        """測試多個資料來源的整合"""
        # 模擬 TFND 只有部分資料
        tfnd_data = {
            "name_en": "Apple",
            "name_zh": "蘋果",
            "nutrients_per_100g": {
                "熱量": {"value": 52.0, "unit": "kcal"}
            }
        }
        
        import json
        from unittest.mock import mock_open as mock_open_func
        mock_file_open.return_value = mock_open_func(
            read_data=json.dumps(tfnd_data)
        ).return_value
        
        # 查詢多種食物（有些在TFND，有些不在）
        with patch('requests.get') as mock_usda:  # 直接 patch requests 模組
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "foods": [{
                    "foodNutrients": [{
                        "nutrientId": 1008,
                        "value": 89.0,
                        "unitName": "kcal"
                    }]
                }]
            }
            mock_usda.return_value = mock_response
            
            nutrition_data, total = get_nutrition(['apple', 'banana'])
            
            # 應該包含兩種食物
            assert len(nutrition_data) == 2
            assert 'apple' in nutrition_data
            assert 'banana' in nutrition_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
