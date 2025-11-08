#!/usr/bin/env python3
"""
Diet Tracker Bot - Utils 模組測試
=================================

測試 utils.py 中的工具函數，包括日誌系統、快取機制、錯誤處理等。

測試範圍：
1. 日誌系統測試
2. 快取機制測試  
3. 錯誤處理測試
4. 文件操作測試
5. 輔助工具函數測試
"""

import os
import sys
import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
import logging

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

import utils

@pytest.mark.unit
class TestLoggingSystem:
    """測試日誌系統"""
    
    def test_setup_logging_basic(self):
        """測試基本日誌設定"""
        logger = utils.setup_logging("INFO")
        
        assert logger is not None
        assert logger.name == "utils"
        # 只測試函數能夠正常執行
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
    
    def test_setup_logging_debug_level(self):
        """測試除錯等級日誌設定"""
        logger = utils.setup_logging("DEBUG")
        
        assert logger is not None
        assert hasattr(logger, 'debug')
    
    def test_log_function_call(self):
        """測試函數呼叫日誌"""
        logger = utils.setup_logging("INFO")
        
        # 不應該拋出異常
        utils.log_function_call("test_function", {"arg1": "value1"}, logger)
        utils.log_function_call("test_function", {}, logger)
    
    def test_log_step_functions(self):
        """測試步驟日誌函數"""
        logger = utils.setup_logging("INFO")
        
        # 測試各種步驟日誌函數
        utils.log_step_start("測試步驟", "詳細內容", logger)
        utils.log_step_success("測試步驟", "成功結果", logger)
        utils.log_step_error("測試步驟", "錯誤訊息", logger)


@pytest.mark.unit
@pytest.mark.cache
class TestCacheSystem:
    """測試快取系統"""
    
    def setup_method(self):
        """每個測試前清理快取"""
        utils.clear_cache()
    
    def test_cache_basic_operations(self):
        """測試基本快取操作"""
        # 測試設定和取得
        utils.set_cached_nutrition("apple", 52.0, "TFND")
        result = utils.get_cached_nutrition("apple")
        
        assert result is not None
        assert result == 52.0
    
    def test_cache_miss(self):
        """測試快取未命中"""
        result = utils.get_cached_nutrition("nonexistent_food")
        assert result is None
    
    def test_cache_expiry_simulation(self):
        """測試快取過期機制（模擬）"""
        utils.set_cached_nutrition("banana", 89.0, "USDA")
        
        # 驗證快取存在
        result = utils.get_cached_nutrition("banana")
        assert result is not None
        
        # 清理快取後應該不存在
        utils.clear_cache()
        result = utils.get_cached_nutrition("banana")
        assert result is None
    
    def test_cache_stats(self):
        """測試快取統計"""
        utils.clear_cache()
        
        # 添加一些快取項目
        utils.set_cached_nutrition("apple", 52.0, "TFND")
        utils.set_cached_nutrition("banana", 89.0, "USDA")
        
        stats = utils.get_cache_stats()
        
        assert 'size' in stats
        assert 'max_size' in stats
        assert 'ttl_hours' in stats
        assert stats['size'] >= 2  # 至少有兩個項目


@pytest.mark.unit
class TestErrorHandling:
    """測試錯誤處理"""
    
    def test_handle_error_basic(self):
        """測試基本錯誤處理"""
        test_error = ValueError("測試錯誤")
        logger = utils.setup_logging("INFO")
        
        # 不拋出異常的情況
        result = utils.handle_error(
            test_error, 
            "測試操作", 
            logger, 
            raise_error=False, 
            default_return="default"
        )
        
        assert result == "default"
    
    def test_handle_error_with_raise(self):
        """測試帶拋出的錯誤處理"""
        test_error = ValueError("測試錯誤")
        logger = utils.setup_logging("INFO")
        
        # 應該拋出異常
        with pytest.raises(ValueError):
            utils.handle_error(
                test_error, 
                "測試操作", 
                logger, 
                raise_error=True
            )


@pytest.mark.unit
class TestUtilityFunctions:
    """測試輔助工具函數"""
    
    def test_get_memory_usage(self):
        """測試記憶體使用量取得"""
        if not hasattr(utils, 'get_memory_usage'):
            pytest.skip("get_memory_usage function not implemented yet")
        
        try:
            memory_usage = utils.get_memory_usage()
            assert isinstance(memory_usage, (int, float))
            assert memory_usage > 0  # 記憶體使用量應該大於0
        except ImportError:
            # 如果沒有 psutil 模組，跳過測試
            pytest.skip("psutil not available")
    
    def test_format_bytes(self):
        """測試位元組格式化"""
        if hasattr(utils, 'format_bytes'):
            assert utils.format_bytes(1024) == "1.0 KB"
            assert utils.format_bytes(1048576) == "1.0 MB"
            assert utils.format_bytes(1073741824) == "1.0 GB"
    
    def test_create_temp_filename(self):
        """測試臨時檔案名稱生成"""
        if hasattr(utils, 'create_temp_filename'):
            filename1 = utils.create_temp_filename("jpg")
            filename2 = utils.create_temp_filename("jpg")
            
            # 兩個檔名應該不同
            assert filename1 != filename2
            assert filename1.endswith(".jpg")


@pytest.mark.unit
class TestLoggingHelpers:
    """測試日誌輔助函數"""
    
    def setup_method(self):
        """每個測試前設定日誌"""
        self.logger = utils.setup_logging("INFO")
    
    def test_log_food_recognition(self):
        """測試食物識別日誌"""
        foods = ["蘋果", "香蕉"]
        confidence = 0.95
        
        # 不應該拋出異常
        utils.log_food_recognition(foods, confidence, self.logger)
        utils.log_food_recognition([], 0.0, self.logger)
    
    def test_log_nutrition_calculation(self):
        """測試營養計算日誌"""
        utils.log_nutrition_calculation("蘋果", 52.0, self.logger)
    
    def test_log_data_storage(self):
        """測試資料儲存日誌"""
        utils.log_data_storage("user_123", 1, 150.0, self.logger)
    
    def test_log_ai_recommendation(self):
        """測試AI推薦日誌"""
        utils.log_ai_recommendation("user_123", 200, "gemini", self.logger)
    
    def test_log_discord_interaction(self):
        """測試Discord互動日誌"""
        utils.log_discord_interaction("user_123", "track", "success", self.logger)
    
    def test_log_performance_metric(self):
        """測試效能指標日誌"""
        utils.log_performance_metric("測試操作", 1.23, self.logger)


@pytest.mark.unit
class TestFileOperations:
    """測試檔案操作"""
    
    def test_ensure_directory_exists(self):
        """測試目錄確保存在"""
        if hasattr(utils, 'ensure_directory_exists'):
            with tempfile.TemporaryDirectory() as temp_dir:
                test_dir = os.path.join(temp_dir, "test_subdir")
                
                # 目錄不存在
                assert not os.path.exists(test_dir)
                
                # 呼叫函數
                utils.ensure_directory_exists(test_dir)
                
                # 目錄應該存在
                assert os.path.exists(test_dir)
    
    def test_safe_file_write(self):
        """測試安全檔案寫入"""
        if hasattr(utils, 'safe_file_write'):
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # 寫入測試內容
                success = utils.safe_file_write(temp_path, "測試內容")
                assert success == True
                
                # 驗證內容
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    assert content == "測試內容"
                
            finally:
                # 清理檔案
                if os.path.exists(temp_path):
                    os.unlink(temp_path)