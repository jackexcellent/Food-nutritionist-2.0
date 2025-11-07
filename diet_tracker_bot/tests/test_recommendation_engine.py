#!/usr/bin/env python3
"""
Diet Tracker Bot - AI 推薦引擎測試
=================================

測試 AI 推薦引擎的完整性和正確性，包括：
1. Gemini API 整合
2. 推薦生成邏輯
3. Fallback 機制
4. Prompt 模板
5. 錯誤處理
6. 資料格式化

設計原則：
- 使用 mock 避免真實 API 呼叫
- 測試所有主要功能路徑
- 驗證錯誤處理機制
- 確保輸出格式正確
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# 導入要測試的模組
import recommendation_engine
from recommendation_engine import (
    get_recommendation,
    _format_history_for_prompt,
    _generate_ai_recommendation,
    _generate_rule_based_recommendation,
    _generate_no_history_message,
    _generate_error_fallback,
    PromptTemplates
)


# Global fixtures for all test classes
@pytest.fixture
def sample_history_data():
    """測試用飲食歷史資料"""
    now = datetime.now()
    return [
        (1, (now - timedelta(days=2)).isoformat(), 
         {"apple": 52.0, "chicken": 165.0}, 217.0, now.isoformat()),
        (2, (now - timedelta(days=1)).isoformat(), 
         {"banana": 89.0, "rice": 130.0}, 219.0, now.isoformat()),
        (3, now.isoformat(), 
         {"orange": 47.0, "fish": 140.0}, 187.0, now.isoformat())
    ]

@pytest.fixture
def sample_stats_data():
    """測試用統計資料"""
    return {
        'total_meals': 3,
        'total_calories': 623.0,
        'avg_calories': 207.67,
        'most_common_foods': [
            ('apple', 1), ('chicken', 1), ('banana', 1)
        ]
    }


class TestRecommendationEngine:
    """AI 推薦引擎核心功能測試"""
    
    def test_recommendation_engine_initialization(self):
        """測試推薦引擎初始化"""
        # 驗證模組正確載入
        assert hasattr(recommendation_engine, 'get_recommendation')
        assert hasattr(recommendation_engine, 'PromptTemplates')
        
        # 驗證 Prompt 模板存在
        assert hasattr(PromptTemplates, 'BASIC_RECOMMENDATION')
        assert hasattr(PromptTemplates, 'SIMPLE_FALLBACK')
    
    def test_format_history_for_prompt(self, sample_history_data):
        """測試飲食歷史格式化功能"""
        formatted_data = _format_history_for_prompt(sample_history_data)
        
        # 驗證資料結構
        assert isinstance(formatted_data, dict)
        assert 'meals' in formatted_data
        assert 'date_range' in formatted_data
        assert 'total_records' in formatted_data
        
        # 驗證記錄數量
        assert formatted_data['total_records'] == 3
        assert len(formatted_data['meals']) == 3
        
        # 驗證餐點資料結構
        meal = formatted_data['meals'][0]
        assert 'date' in meal
        assert 'time' in meal
        assert 'foods' in meal
        assert 'total_calories' in meal
        
        # 驗證食物資料
        assert isinstance(meal['foods'], dict)
        assert meal['total_calories'] > 0
    
    def test_format_history_empty_data(self):
        """測試空飲食歷史的處理"""
        formatted_data = _format_history_for_prompt([])
        
        assert formatted_data['total_records'] == 0
        assert formatted_data['meals'] == []
        assert formatted_data['date_range'] == "無資料"


class TestGeminiApiIntegration:
    """Gemini API 整合測試"""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """模擬 Gemini 客戶端"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """
🔍 **飲食分析**：
您最近3天的飲食記錄顯示平均每餐約207kcal，整體熱量適中。

💡 **健康建議**：
1. 增加蔬菜攝取量，提供更多纖維和維生素
2. 保持蛋白質來源的多樣性
3. 適量增加全穀類食物

🍎 **推薦食物**：
- 綠葉蔬菜：菠菜、花椰菜
- 優質蛋白質：豆腐、雞蛋
- 健康脂肪：酪梨、堅果

⚠️ **注意事項**：
保持飲食均衡，避免單一食物過量攝取。
"""
        mock_client.generate_content.return_value = mock_response
        return mock_client
    
    @patch('recommendation_engine.get_history')
    @patch('recommendation_engine.get_statistics')
    def test_gemini_api_success(self, mock_get_stats, mock_get_history, 
                               sample_history_data, sample_stats_data, mock_gemini_client):
        """測試 Gemini API 成功回應"""
        # 設定 mock 資料
        mock_get_history.return_value = sample_history_data
        mock_get_stats.return_value = sample_stats_data
        
        # 模擬 Gemini 客戶端
        with patch.object(recommendation_engine, 'gemini_client', mock_gemini_client):
            recommendation = get_recommendation('test_user')
        
        # 驗證結果
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0
        assert '飲食分析' in recommendation
        assert '健康建議' in recommendation
        
        # 驗證 API 被呼叫
        mock_gemini_client.generate_content.assert_called_once()
    
    @patch('recommendation_engine.get_history')
    @patch('recommendation_engine.get_statistics')
    def test_gemini_api_failure_fallback(self, mock_get_stats, mock_get_history,
                                        sample_history_data, sample_stats_data):
        """測試 Gemini API 失敗時的 fallback"""
        # 設定 mock 資料
        mock_get_history.return_value = sample_history_data
        mock_get_stats.return_value = sample_stats_data
        
        # 模擬 API 失敗
        mock_client = MagicMock()
        mock_client.generate_content.side_effect = Exception("API 連接失敗")
        
        with patch.object(recommendation_engine, 'gemini_client', mock_client):
            recommendation = get_recommendation('test_user')
        
        # 驗證 fallback 正常運作
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0
        assert '飲食分析' in recommendation  # fallback 模板也包含此內容
    
    def test_generate_ai_recommendation_with_mock(self, mock_gemini_client, 
                                                 sample_stats_data):
        """測試 AI 推薦生成邏輯"""
        history_data = {
            "meals": [
                {
                    "date": "2024-11-06",
                    "time": "12:30",
                    "foods": {"apple": 52.0, "chicken": 165.0},
                    "total_calories": 217.0
                }
            ],
            "date_range": "2024-11-06 到 2024-11-06",
            "total_records": 1
        }
        
        with patch.object(recommendation_engine, 'gemini_client', mock_gemini_client):
            result = _generate_ai_recommendation(history_data, sample_stats_data)
        
        # 驗證結果
        assert isinstance(result, str)
        assert len(result) > 50  # 確保回應足夠詳細
        
        # 驗證 prompt 被正確構建和傳送
        mock_gemini_client.generate_content.assert_called_once()
        
        # 獲取傳送的 prompt
        call_args = mock_gemini_client.generate_content.call_args
        prompt = call_args[0][0]
        
        # 驗證 prompt 包含必要資訊
        assert 'apple' in prompt
        assert 'chicken' in prompt
        assert '217.0' in prompt
    
    def test_gemini_api_empty_response(self, sample_stats_data):
        """測試 Gemini API 回傳空白回應"""
        history_data = {"meals": [], "date_range": "", "total_records": 0}
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""  # 空白回應
        mock_client.generate_content.return_value = mock_response
        
        with patch.object(recommendation_engine, 'gemini_client', mock_client):
            with pytest.raises(ValueError, match="回傳空白回應"):
                _generate_ai_recommendation(history_data, sample_stats_data)


class TestRuleBasedFallback:
    """規則型 Fallback 機制測試"""
    
    def test_rule_based_recommendation_normal_case(self, sample_stats_data):
        """測試正常情況的規則型推薦"""
        history_data = {
            "meals": [{"foods": {"apple": 52.0}, "total_calories": 52.0}],
            "total_records": 1
        }
        
        recommendation = _generate_rule_based_recommendation(
            history_data, sample_stats_data, days=7
        )
        
        # 驗證基本結構
        assert isinstance(recommendation, str)
        assert '飲食分析' in recommendation
        assert '健康建議' in recommendation
        assert '推薦食物' in recommendation
        
        # 驗證個人化內容
        assert '207.7' in recommendation  # 平均熱量
        assert '3' in recommendation      # 總餐數
    
    def test_rule_based_high_calorie_analysis(self):
        """測試高熱量情況的分析"""
        high_calorie_stats = {
            'total_meals': 5,
            'avg_calories': 750.0,  # 高熱量
            'most_common_foods': [('pizza', 3)]
        }
        
        history_data = {"meals": [], "total_records": 0}
        
        recommendation = _generate_rule_based_recommendation(
            history_data, high_calorie_stats, days=7
        )
        
        # 驗證高熱量警告
        assert '偏高' in recommendation or '減少' in recommendation
    
    def test_rule_based_low_calorie_analysis(self):
        """測試低熱量情況的分析"""
        low_calorie_stats = {
            'total_meals': 2,
            'avg_calories': 150.0,  # 低熱量
            'most_common_foods': [('apple', 2)]
        }
        
        history_data = {"meals": [], "total_records": 0}
        
        recommendation = _generate_rule_based_recommendation(
            history_data, low_calorie_stats, days=7
        )
        
        # 驗證低熱量建議
        assert '偏低' in recommendation or '增加' in recommendation
    
    def test_rule_based_low_meal_frequency(self):
        """測試用餐頻率過低的情況"""
        low_frequency_stats = {
            'total_meals': 5,  # 7天只吃5餐
            'avg_calories': 400.0,
            'most_common_foods': []
        }
        
        history_data = {"meals": [], "total_records": 0}
        
        recommendation = _generate_rule_based_recommendation(
            history_data, low_frequency_stats, days=7
        )
        
        # 驗證頻率建議
        assert '用餐頻率' in recommendation or '規律' in recommendation


class TestPromptTemplates:
    """Prompt 模板測試"""
    
    def test_basic_recommendation_template(self):
        """測試基礎推薦模板"""
        template = PromptTemplates.BASIC_RECOMMENDATION
        
        # 驗證模板包含必要佔位符
        assert '{history_json}' in template
        assert '{total_meals}' in template
        assert '{avg_calories:.1f}' in template
        assert '{common_foods}' in template
        
        # 驗證結構化輸出格式
        assert '**飲食分析**' in template
        assert '**健康建議**' in template
        assert '**推薦食物**' in template
        assert '**注意事項**' in template
    
    def test_simple_fallback_template(self):
        """測試簡單 fallback 模板"""
        template = PromptTemplates.SIMPLE_FALLBACK
        
        # 驗證模板包含必要佔位符
        assert '{days}' in template
        assert '{total_meals}' in template
        assert '{avg_calories:.1f}' in template
        
        # 測試模板格式化
        formatted = template.format(
            days=7,
            total_meals=10,
            avg_calories=300.5
        )
        
        assert '7 天' in formatted
        assert '10 餐' in formatted
        assert '300.5' in formatted
    
    def test_advanced_analysis_template(self):
        """測試進階分析模板 (未來功能)"""
        template = PromptTemplates.ADVANCED_ANALYSIS
        
        # 驗證進階功能佔位符
        assert '{goals}' in template
        assert '{health_status}' in template
        assert '{stats_json}' in template


class TestSpecialCases:
    """特殊情況處理測試"""
    
    @patch('recommendation_engine.get_history')
    def test_no_history_case(self, mock_get_history):
        """測試無飲食歷史的情況"""
        mock_get_history.return_value = []  # 空歷史
        
        recommendation = get_recommendation('new_user')
        
        # 驗證無歷史訊息
        assert isinstance(recommendation, str)
        assert '沒有飲食記錄' in recommendation or '開始記錄' in recommendation
    
    def test_no_history_message_content(self):
        """測試無歷史記錄訊息內容"""
        message = _generate_no_history_message()
        
        assert isinstance(message, str)
        assert '飲食分析' in message
        assert '開始建議' in message
        assert '一般健康建議' in message
    
    def test_error_fallback_message(self):
        """測試錯誤 fallback 訊息"""
        message = _generate_error_fallback()
        
        assert isinstance(message, str)
        assert '系統提醒' in message or '錯誤' in message
        assert '健康建議' in message
    
    @patch('recommendation_engine.get_history')
    @patch('recommendation_engine.get_statistics')
    def test_api_and_fallback_both_fail(self, mock_get_stats, mock_get_history):
        """測試 API 和 fallback 都失敗的情況"""
        # 模擬資料獲取失敗
        mock_get_history.side_effect = Exception("資料庫連接失敗")
        
        recommendation = get_recommendation('test_user')
        
        # 應該返回錯誤 fallback 訊息
        assert isinstance(recommendation, str)
        assert len(recommendation) > 0


class TestParameterValidation:
    """參數驗證測試"""
    
    def test_empty_user_id(self):
        """測試空用戶 ID"""
        with pytest.raises(ValueError, match="user_id 不能為空"):
            get_recommendation("")
    
    def test_invalid_days(self):
        """測試無效天數"""
        with pytest.raises(ValueError, match="days 必須大於 0"):
            get_recommendation("test_user", days=0)
        
        with pytest.raises(ValueError, match="days 必須大於 0"):
            get_recommendation("test_user", days=-1)
    
    @patch('recommendation_engine.get_history')
    @patch('recommendation_engine.get_statistics')
    def test_valid_parameters(self, mock_get_stats, mock_get_history):
        """測試有效參數"""
        mock_get_history.return_value = []
        mock_get_stats.return_value = {}
        
        # 這些呼叫應該不會拋出異常
        get_recommendation("valid_user", days=1)
        get_recommendation("valid_user", days=30)
        get_recommendation("valid_user", days=365)


class TestIntegration:
    """整合測試"""
    
    @patch('recommendation_engine.get_history')
    @patch('recommendation_engine.get_statistics')
    def test_full_workflow_with_fallback(self, mock_get_stats, mock_get_history):
        """測試完整工作流程 (使用 fallback)"""
        # 設定測試資料
        sample_history = [
            (1, datetime.now().isoformat(), 
             {"apple": 52.0, "banana": 89.0}, 141.0, datetime.now().isoformat())
        ]
        
        sample_stats = {
            'total_meals': 1,
            'total_calories': 141.0,
            'avg_calories': 141.0,
            'most_common_foods': [('apple', 1), ('banana', 1)]
        }
        
        mock_get_history.return_value = sample_history
        mock_get_stats.return_value = sample_stats
        
        # 確保 Gemini 客戶端不可用，強制使用 fallback
        with patch.object(recommendation_engine, 'gemini_client', None):
            recommendation = get_recommendation('test_user', days=7)
        
        # 驗證結果
        assert isinstance(recommendation, str)
        assert len(recommendation) > 100  # 確保有足夠內容
        assert 'apple' in recommendation or 'banana' in recommendation
        assert '141' in recommendation
    
    def test_system_availability_check(self):
        """測試系統可用性檢查"""
        # 檢查模組是否正確導入
        assert hasattr(recommendation_engine, 'GEMINI_AVAILABLE')
        assert hasattr(recommendation_engine, 'GEMINI_API_KEY')
        
        # 驗證這些是布林值或字串
        assert isinstance(recommendation_engine.GEMINI_AVAILABLE, bool)
        assert recommendation_engine.GEMINI_API_KEY is None or isinstance(recommendation_engine.GEMINI_API_KEY, str)


class TestPerformance:
    """效能測試"""
    
    @patch('recommendation_engine.get_history')
    @patch('recommendation_engine.get_statistics')
    def test_large_history_handling(self, mock_get_stats, mock_get_history):
        """測試大量歷史資料的處理"""
        # 生成大量測試資料 (100 筆記錄)
        large_history = []
        for i in range(100):
            date = (datetime.now() - timedelta(days=i)).isoformat()
            large_history.append((
                i, date, {"food_" + str(i): float(50 + i)}, float(50 + i), date
            ))
        
        mock_get_history.return_value = large_history
        mock_get_stats.return_value = {
            'total_meals': 100,
            'total_calories': 5000.0,
            'avg_calories': 50.0,
            'most_common_foods': [('food_1', 1)]
        }
        
        # 測試處理時間 (應該在合理範圍內)
        import time
        start_time = time.time()
        
        with patch.object(recommendation_engine, 'gemini_client', None):
            recommendation = get_recommendation('test_user', days=100)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 驗證結果和效能
        assert isinstance(recommendation, str)
        assert processing_time < 5.0  # 應在 5 秒內完成


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])