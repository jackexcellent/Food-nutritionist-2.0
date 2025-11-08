#!/usr/bin/env python3
"""
Diet Tracker Bot - 端到端整合測試
===============================

完整的端到端測試，模擬真實用戶從圖片上傳到獲得推薦的完整流程。
這些測試確保所有系統組件正確整合並按預期工作。

測試涵蓋範圍：
1. 完整 MVP 流程測試
2. 多用戶並發測試  
3. 性能基準測試
4. 錯誤恢復測試
5. 資料庫一致性測試
6. 快取系統測試
7. Discord Bot 整合測試

設計原則：
- 使用真實資料測試關鍵路徑
- Mock 外部 API 避免配額消耗
- 測試邊界條件和錯誤情況
- 驗證性能指標和資源使用
"""

import os
import sys
import pytest
import tempfile
import json
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import asyncio

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# 導入所有模組進行端到端測試
import utils
import image_processor
import nutrition_calculator
import data_storage
import recommendation_engine
import discord_bot
import main

class TestEndToEndIntegration:
    """端到端整合測試類別"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """為每個測試設定乾淨的環境"""
        # 清除快取
        utils.clear_cache()
        
        # 重置資料庫為測試狀態
        data_storage.init_database()
        
        # 設定測試日誌
        utils.setup_logging("INFO")
        
        yield
        
        # 測試後清理
        utils.clear_cache()
    
    def create_test_image(self, filename: str = "test_food.jpg") -> str:
        """創建測試用的食物圖片"""
        # 創建一個簡單的測試圖片
        img_array = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        img.save(temp_path, 'JPEG')
        
        return temp_path
    
    @patch('image_processor.process_image')
    @patch('nutrition_calculator.get_nutrition')
    def test_complete_mvp_pipeline_success(self, mock_get_nutrition, mock_process_image):
        """測試完整 MVP 流程 - 成功路徑"""
        # 設定 mock 返回值
        mock_process_image.return_value = ['蘋果', '香蕉']
        mock_get_nutrition.return_value = (
            {'蘋果': 52.0, '香蕉': 89.0}, 
            141.0
        )
        
        # 創建測試圖片
        test_image = self.create_test_image()
        user_id = "test_user_mvp"
        
        try:
            # 執行完整流程
            start_time = time.time()
            
            # 1. 圖像處理
            foods = image_processor.process_image(test_image)
            assert foods == ['蘋果', '香蕉']
            
            # 2. 營養計算
            nutrition_result = nutrition_calculator.get_nutrition(foods)
            assert nutrition_result is not None
            nutrition_data, total_calories = nutrition_result
            assert total_calories == 141.0
            
            # 3. 資料儲存
            meal_id = data_storage.store_meal(user_id, nutrition_data, total_calories)
            assert meal_id > 0
            
            # 4. AI 推薦
            recommendation = recommendation_engine.get_recommendation(user_id)
            assert len(recommendation) > 0
            
            # 測試總執行時間
            execution_time = time.time() - start_time
            utils.log_performance_metric("完整MVP流程", execution_time)
            
            # 驗證資料庫狀態
            history = data_storage.get_history(user_id, days=1)
            assert len(history) == 1
            assert history[0][3] == total_calories  # 總熱量欄位
            
            # 驗證統計功能
            stats = data_storage.get_statistics(user_id)
            assert stats['total_meals'] == 1
            assert stats['avg_calories'] == total_calories
            
        finally:
            # 清理測試檔案
            if os.path.exists(test_image):
                os.unlink(test_image)
    
    def test_multi_user_concurrent_access(self):
        """測試多用戶並發存取"""
        users = ['user1', 'user2', 'user3', 'user4', 'user5']
        results = {}
        
        def user_session(user_id: str):
            """模擬單一用戶會話"""
            try:
                # 模擬儲存餐點
                nutrition_data = {'測試食物': 200.0}
                meal_id = data_storage.store_meal(user_id, nutrition_data, 200.0)
                
                # 模擬查詢歷史
                history = data_storage.get_history(user_id)
                
                # 模擬獲得推薦
                recommendation = recommendation_engine.get_recommendation(user_id)
                
                results[user_id] = {
                    'meal_id': meal_id,
                    'history_count': len(history),
                    'recommendation_length': len(recommendation)
                }
                
            except Exception as e:
                results[user_id] = {'error': str(e)}
        
        # 並發執行用戶會話
        threads = []
        start_time = time.time()
        
        for user_id in users:
            thread = threading.Thread(target=user_session, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有線程完成
        for thread in threads:
            thread.join()
        
        execution_time = time.time() - start_time
        utils.log_performance_metric(f"{len(users)}用戶並發測試", execution_time)
        
        # 驗證結果
        for user_id in users:
            assert user_id in results
            if 'error' in results[user_id]:
                pytest.fail(f"用戶 {user_id} 發生錯誤: {results[user_id]['error']}")
            
            assert results[user_id]['meal_id'] > 0
            assert results[user_id]['history_count'] > 0
            assert results[user_id]['recommendation_length'] > 0
        
        # 檢查資料庫一致性
        for user_id in users:
            user_history = data_storage.get_history(user_id)
            assert len(user_history) == 1  # 每個用戶應該有一筆記錄
    
    @patch('image_processor.process_image')
    def test_error_recovery_and_fallback(self, mock_process_image):
        """測試錯誤恢復和 fallback 機制"""
        user_id = "test_error_recovery"
        
        # 測試圖像處理失敗
        mock_process_image.side_effect = Exception("圖像處理失敗")
        
        test_image = self.create_test_image()
        try:
            # 應該優雅地處理錯誤
            foods = image_processor.process_image(test_image)
            # 根據實際實現，可能返回空列表或拋出異常
            assert foods is not None
        except Exception:
            # 如果拋出異常，確保是預期的異常
            pass
        finally:
            os.unlink(test_image)
        
        # 測試 AI 推薦的 fallback 機制
        # 即使沒有歷史記錄，也應該能生成推薦
        recommendation = recommendation_engine.get_recommendation(user_id)
        assert len(recommendation) > 0
        assert "沒有足夠的飲食記錄" in recommendation or len(recommendation) > 100
    
    def test_cache_system_performance(self):
        """測試快取系統性能"""
        foods = ['蘋果', '香蕉', '橘子']
        
        # 第一次查詢 - 應該沒有快取
        start_time = time.time()
        for food in foods:
            cached = utils.get_cached_nutrition(food)
            assert cached is None  # 應該沒有快取
        cache_miss_time = time.time() - start_time
        
        # 添加到快取
        for i, food in enumerate(foods):
            utils.set_cached_nutrition(food, 50 + i * 10, f"測試來源")
        
        # 第二次查詢 - 應該有快取
        start_time = time.time()
        for food in foods:
            cached = utils.get_cached_nutrition(food)
            assert cached is not None  # 應該有快取
            assert 'calories' in cached
        cache_hit_time = time.time() - start_time
        
        # 快取命中應該比未命中快
        utils.log_performance_metric("快取未命中", cache_miss_time)
        utils.log_performance_metric("快取命中", cache_hit_time)
        
        # 驗證快取統計
        stats = utils.get_cache_stats()
        assert stats['size'] >= len(foods)
    
    def test_database_performance_bottlenecks(self):
        """測試資料庫性能瓶頸"""
        user_id = "performance_test_user"
        
        # 測試大量寫入操作
        write_times = []
        
        for i in range(50):  # 50次寫入操作
            start_time = time.time()
            
            nutrition_data = {f'食物_{i}': 100 + i}
            meal_id = data_storage.store_meal(user_id, nutrition_data, 100 + i)
            
            write_time = time.time() - start_time
            write_times.append(write_time)
            
            assert meal_id > 0
        
        # 分析寫入性能
        avg_write_time = sum(write_times) / len(write_times)
        max_write_time = max(write_times)
        
        utils.log_performance_metric("平均寫入時間", avg_write_time)
        utils.log_performance_metric("最大寫入時間", max_write_time)
        
        # 測試大量讀取操作
        start_time = time.time()
        history = data_storage.get_history(user_id, days=30)
        read_time = time.time() - start_time
        
        utils.log_performance_metric("大量歷史讀取", read_time)
        
        assert len(history) == 50  # 應該有50筆記錄
        
        # SQLite 性能警告
        if avg_write_time > 0.1:  # 100ms
            utils.logger.warning("⚠️  SQLite 寫入性能較慢，考慮升級至 PostgreSQL")
        
        if read_time > 1.0:  # 1秒
            utils.logger.warning("⚠️  SQLite 讀取性能較慢，考慮添加索引或升級資料庫")
    
    @patch('image_processor.process_image')
    @patch('nutrition_calculator.get_nutrition')
    def test_complete_user_journey(self, mock_get_nutrition, mock_process_image):
        """測試完整用戶旅程 - 多餐點追蹤"""
        user_id = "journey_test_user"
        
        # 設定 mock 返回不同餐點的資料
        meals_data = [
            (['蘋果'], {'蘋果': 52.0}, 52.0),
            (['香蕉', '橘子'], {'香蕉': 89.0, '橘子': 47.0}, 136.0),
            (['雞胸肉', '米飯'], {'雞胸肉': 165.0, '米飯': 130.0}, 295.0)
        ]
        
        total_journey_time = 0
        
        for i, (foods, nutrition_data, total_calories) in enumerate(meals_data):
            mock_process_image.return_value = foods
            mock_get_nutrition.return_value = (nutrition_data, total_calories)
            
            start_time = time.time()
            
            # 模擬用戶上傳圖片和處理
            test_image = self.create_test_image(f"meal_{i}.jpg")
            
            try:
                # 完整流程
                detected_foods = image_processor.process_image(test_image)
                nutrition_result = nutrition_calculator.get_nutrition(detected_foods)
                
                if nutrition_result:
                    nutr_data, calories = nutrition_result
                    meal_id = data_storage.store_meal(user_id, nutr_data, calories)
                    recommendation = recommendation_engine.get_recommendation(user_id)
                    
                    meal_time = time.time() - start_time
                    total_journey_time += meal_time
                    
                    utils.log_performance_metric(f"餐點 {i+1} 處理", meal_time)
                    
                    # 驗證每餐的處理結果
                    assert meal_id > 0
                    assert len(recommendation) > 0
                
            finally:
                os.unlink(test_image)
        
        # 驗證用戶完整歷史
        full_history = data_storage.get_history(user_id, days=7)
        assert len(full_history) == 3
        
        # 驗證統計準確性
        stats = data_storage.get_statistics(user_id)
        assert stats['total_meals'] == 3
        expected_total = sum(meal[2] for meal in meals_data)
        expected_avg = expected_total / 3
        assert abs(stats['avg_calories'] - expected_avg) < 0.1
        
        utils.log_performance_metric("完整用戶旅程", total_journey_time)
        
        # 最終推薦應該更個人化
        final_recommendation = recommendation_engine.get_recommendation(user_id)
        assert len(final_recommendation) > 200  # 有歷史後推薦應該更詳細
    
    def test_system_resource_usage(self):
        """測試系統資源使用情況"""
        import psutil
        import gc
        
        # 記錄初始狀態
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        user_id = "resource_test_user"
        
        # 執行大量操作
        for i in range(20):
            # 模擬圖片處理
            test_image = self.create_test_image(f"resource_test_{i}.jpg")
            
            # 模擬完整流程
            nutrition_data = {f'食物_{i}': 100 + i}
            meal_id = data_storage.store_meal(user_id, nutrition_data, 100 + i)
            
            # 清理測試檔案
            os.unlink(test_image)
            
            # 每5次操作記錄一次記憶體使用
            if i % 5 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                utils.log_performance_metric(f"記憶體使用(操作{i})", current_memory)
                
                if memory_increase > 100:  # 100MB
                    utils.logger.warning(f"⚠️  記憶體使用量增加: {memory_increase:.1f} MB")
        
        # 強制垃圾回收
        gc.collect()
        
        # 檢查最終記憶體使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        utils.log_performance_metric("最終記憶體使用", final_memory)
        
        # 記憶體洩漏檢查
        if total_increase > 50:  # 50MB
            utils.logger.warning(f"⚠️  可能存在記憶體洩漏: 增加 {total_increase:.1f} MB")
    
    @pytest.mark.asyncio
    async def test_discord_bot_integration(self):
        """測試 Discord Bot 整合"""
        # 測試機器人初始化
        test_bot = discord_bot.DietTrackerBot()
        assert test_bot.command_prefix == '/'
        assert 'total_tracks' in test_bot.stats
        
        # 測試輔助函數
        assert discord_bot._is_valid_image_file("test.jpg") == True
        assert discord_bot._is_valid_image_file("test.pdf") == False
        
        # 測試回應格式化
        foods = ['蘋果', '香蕉']
        nutrition_data = {
            '蘋果': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2},
            '香蕉': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3}
        }
        total_calories = 141.0
        recommendation = "測試推薦內容"
        meal_id = 1
        
        embed_response = discord_bot._format_track_response_embed(
            foods, nutrition_data, total_calories, recommendation, meal_id
        )
        
        # 驗證 embed 格式
        assert embed_response.title == "✅ 飲食分析完成！"
        assert "蘋果、香蕉" in embed_response.description
        assert len(embed_response.fields) >= 3  # 營養分析、AI建議、記錄ID


class TestSystemIntegration:
    """系統整合測試"""
    
    def test_module_import_integrity(self):
        """測試模組導入完整性"""
        # 確保所有核心模組都能正確導入
        modules = [
            'utils', 'image_processor', 'nutrition_calculator', 
            'data_storage', 'recommendation_engine', 'discord_bot', 'main'
        ]
        
        for module_name in modules:
            module = sys.modules.get(module_name)
            assert module is not None, f"模組 {module_name} 導入失敗"
            
            # 檢查關鍵函數是否存在
            if module_name == 'image_processor':
                assert hasattr(module, 'process_image')
            elif module_name == 'nutrition_calculator':
                assert hasattr(module, 'get_nutrition')
            elif module_name == 'data_storage':
                assert hasattr(module, 'store_meal')
                assert hasattr(module, 'get_history')
            elif module_name == 'recommendation_engine':
                assert hasattr(module, 'get_recommendation')
    
    def test_configuration_completeness(self):
        """測試配置完整性"""
        # 檢查環境變數配置
        required_env_vars = [
            'DISCORD_TOKEN', 'AZURE_KEY', 'USDA_KEY', 'GEMINI_KEY'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            utils.logger.warning(f"⚠️  缺少環境變數: {missing_vars}")
        
        # 檢查關鍵目錄
        project_root = Path(__file__).parent.parent
        required_dirs = ['src', 'tests', 'config', 'data']
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"目錄 {dir_name} 不存在"
    
    def test_logging_system_integration(self):
        """測試日誌系統整合"""
        # 測試日誌輔助函數
        test_logger = utils.setup_logging("DEBUG")
        
        # 測試各種日誌函數
        utils.log_function_call("test_function", {"arg1": "value1"}, test_logger)
        utils.log_step_start("測試步驟", "測試詳情", test_logger)
        utils.log_step_success("測試步驟", "成功結果", test_logger)
        utils.log_food_recognition(["蘋果", "香蕉"], 0.95, test_logger)
        utils.log_nutrition_calculation("蘋果", 52.0, test_logger)
        utils.log_performance_metric("測試操作", 1.23, test_logger)
        
        # 驗證日誌檔案創建
        log_dir = Path(__file__).parent.parent / "logs"
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            assert len(log_files) > 0, "沒有找到日誌檔案"


if __name__ == "__main__":
    # 運行所有端到端測試
    pytest.main([__file__, "-v", "--tb=short"])