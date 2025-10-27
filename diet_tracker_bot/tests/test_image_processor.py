"""
Diet Tracker Bot - 圖像處理模組測試
==================================

這個測試模組驗證圖像處理功能的正確性，包括：
1. 圖像預處理功能測試
2. Azure API整合測試（使用mock）
3. 食物識別結果解析測試

測試設計原則：
- 使用mock避免真實API呼叫
- 測試各種邊界情況和錯誤處理
- 確保模組在沒有依賴的情況下也能運行

未來擴展：
- 添加圖像品質評估測試
- 多語言識別結果測試
- 效能基準測試
- 整合測試與真實API
"""

import pytest
import numpy as np
import cv2
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# 導入要測試的模組
from image_processor import ImageProcessor, process_image
from utils import save_temp_image, format_file_size

class TestImageProcessor:
    """圖像處理器類別的測試"""
    
    @pytest.fixture
    def sample_image(self):
        """建立測試用的樣本圖像"""
        # 建立一個簡單的彩色測試圖像 (100x100, 3通道)
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        # 添加一些顏色區塊模擬食物
        image[20:80, 20:80] = [0, 255, 0]  # 綠色區塊（蔬菜）
        image[30:70, 30:70] = [0, 0, 255]  # 紅色區塊（水果）
        return image
    
    @pytest.fixture
    def temp_image_file(self, sample_image):
        """建立臨時圖像檔案"""
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, sample_image)
            yield tmp_file.name
        # 清理臨時檔案
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)
    
    @pytest.fixture
    def processor(self):
        """建立ImageProcessor實例"""
        with patch('image_processor.AZURE_AVAILABLE', True):
            processor = ImageProcessor()
            return processor
    
    def test_processor_initialization(self):
        """測試圖像處理器初始化"""
        # 測試沒有Azure SDK的情況
        with patch('image_processor.AZURE_AVAILABLE', False):
            processor = ImageProcessor()
            assert processor.azure_client is None
            assert processor.max_image_size == (800, 600)
            assert processor.blur_kernel_size == (5, 5)
    
    def test_preprocess_image_success(self, processor, temp_image_file):
        """測試圖像預處理成功情況"""
        processed = processor.preprocess_image(temp_image_file)
        
        assert processed is not None
        assert isinstance(processed, np.ndarray)
        assert processed.shape[:2] == processor.max_image_size[::-1]  # (height, width)
        assert len(processed.shape) == 3  # 彩色圖像
    
    def test_preprocess_image_file_not_exists(self, processor):
        """測試處理不存在的檔案"""
        non_existent_file = "non_existent_image.jpg"
        result = processor.preprocess_image(non_existent_file)
        
        assert result is None
    
    def test_preprocess_image_invalid_file(self, processor):
        """測試處理無效的圖像檔案"""
        # 建立一個非圖像檔案
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_file.write(b"This is not an image")
            tmp_file.flush()
            
            result = processor.preprocess_image(tmp_file.name)
            assert result is None
        
        # 清理
        os.unlink(tmp_file.name)
    
    @patch('image_processor.ComputerVisionClient')
    def test_azure_client_initialization(self, mock_cv_client):
        """測試Azure客戶端初始化"""
        # 模擬環境變數
        with patch.dict(os.environ, {
            'AZURE_KEY': 'test_key',
            'AZURE_ENDPOINT': 'https://test.endpoint.com'
        }):
            processor = ImageProcessor()
            
            # 驗證客戶端被正確初始化
            assert processor.azure_client is not None
    
    def test_azure_client_missing_credentials(self, caplog):
        """測試缺少Azure憑證的情況"""
        # 清除環境變數
        with patch.dict(os.environ, {}, clear=True):
            processor = ImageProcessor()
            
            assert processor.azure_client is None
            assert "Azure API金鑰或端點未設定" in caplog.text
    
    @patch('image_processor.ComputerVisionClient')
    def test_analyze_image_with_azure_success(self, mock_cv_client, processor):
        """測試Azure API成功分析圖像"""
        # 建立mock分析結果
        mock_analysis = Mock()
        mock_analysis.tags = [
            Mock(name='apple', confidence=0.8),
            Mock(name='fruit', confidence=0.7),
            Mock(name='red apple', confidence=0.6),
            Mock(name='table', confidence=0.5)  # 應該被過濾掉
        ]
        mock_analysis.description = Mock()
        mock_analysis.description.captions = [
            Mock(text='A red apple on a table')
        ]
        
        # 設定mock客戶端
        mock_client = Mock()
        mock_client.analyze_image_in_stream.return_value = mock_analysis
        processor.azure_client = mock_client
        
        # 測試分析
        test_image_data = b"fake_image_data"
        result = processor.analyze_image_with_azure(test_image_data)
        
        # 驗證結果
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'apple' in result
        assert 'table' not in result  # 應該被過濾掉
    
    def test_analyze_image_without_client(self, processor):
        """測試沒有Azure客戶端時的分析"""
        processor.azure_client = None
        
        test_image_data = b"fake_image_data"
        result = processor.analyze_image_with_azure(test_image_data)
        
        assert result == []
    
    def test_extract_food_from_tags(self, processor):
        """測試從標籤提取食物項目"""
        # 建立測試標籤
        mock_tags = [
            Mock(name='apple', confidence=0.8),
            Mock(name='fruit', confidence=0.7),
            Mock(name='table', confidence=0.9),  # 非食物
            Mock(name='bread', confidence=0.4),
            Mock(name='soup', confidence=0.2),   # 置信度太低
        ]
        
        result = processor._extract_food_from_tags(mock_tags)
        
        assert 'apple' in result
        assert 'fruit' in result
        assert 'bread' in result
        assert 'table' not in result  # 非食物項目
        assert 'soup' not in result   # 置信度太低
    
    def test_extract_foods_from_text(self, processor):
        """測試從文字提取食物名稱"""
        test_text = "A delicious apple and banana with some rice"
        result = processor._extract_foods_from_text(test_text)
        
        assert 'apple' in result
        assert 'banana' in result
        assert 'rice' in result
    
    def test_filter_food_items(self, processor):
        """測試食物項目過濾"""
        test_items = [
            'apple', 'APPLE', 'apple',  # 重複項目
            'a',  # 太短
            'this_is_a_very_long_food_name_that_should_be_filtered_out',  # 太長
            'banana123',  # 包含數字
            'carrot',
            ''  # 空字串
        ]
        
        result = processor._filter_food_items(test_items)
        
        assert 'apple' in result
        assert result.count('apple') == 1  # 去重
        assert 'carrot' in result
        assert 'a' not in result  # 太短
        assert 'banana123' not in result  # 包含數字
        assert len([item for item in result if len(item) > 30]) == 0  # 沒有太長的項目

class TestProcessImageFunction:
    """測試主要的process_image函數"""
    
    @pytest.fixture
    def sample_image_file(self):
        """建立測試圖像檔案"""
        # 建立測試圖像
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[20:80, 20:80] = [255, 0, 0]  # 藍色區塊
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, image)
            yield tmp_file.name
        
        # 清理
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)
    
    @patch('image_processor.ImageProcessor')
    def test_process_image_success(self, mock_processor_class, sample_image_file):
        """測試process_image函數成功執行"""
        # 設定mock處理器
        mock_processor = Mock()
        mock_processor.preprocess_image.return_value = np.zeros((600, 800, 3), dtype=np.uint8)
        mock_processor.azure_client = Mock()
        mock_processor.analyze_image_with_azure.return_value = ['apple', 'banana']
        mock_processor_class.return_value = mock_processor
        
        # 測試函數
        result = process_image(sample_image_file)
        
        # 驗證結果
        assert isinstance(result, list)
        assert 'apple' in result
        assert 'banana' in result
    
    @patch('image_processor.ImageProcessor')
    def test_process_image_preprocess_failure(self, mock_processor_class, sample_image_file):
        """測試圖像預處理失敗的情況"""
        # 設定mock處理器，預處理失敗
        mock_processor = Mock()
        mock_processor.preprocess_image.return_value = None
        mock_processor_class.return_value = mock_processor
        
        # 測試函數
        result = process_image(sample_image_file)
        
        # 驗證結果
        assert result == []
    
    @patch('image_processor.ImageProcessor')
    def test_process_image_no_azure_client(self, mock_processor_class, sample_image_file):
        """測試沒有Azure客戶端的情況"""
        # 設定mock處理器，沒有Azure客戶端
        mock_processor = Mock()
        mock_processor.preprocess_image.return_value = np.zeros((600, 800, 3), dtype=np.uint8)
        mock_processor.azure_client = None
        mock_processor_class.return_value = mock_processor
        
        # 測試函數
        result = process_image(sample_image_file)
        
        # 驗證結果
        assert result == []

class TestUtilsFunctions:
    """測試utils模組中的相關函數"""
    
    def test_save_temp_image_numpy_array(self):
        """測試保存numpy array圖像"""
        # 建立測試圖像
        test_image = np.zeros((50, 50, 3), dtype=np.uint8)
        test_image[:, :] = [255, 0, 0]  # 藍色圖像
        
        # 保存圖像
        filename = "test_numpy_image.jpg"
        result_path = save_temp_image(test_image, filename)
        
        # 驗證結果
        assert os.path.exists(result_path)
        assert filename in result_path
        
        # 驗證圖像可以重新讀取
        loaded_image = cv2.imread(result_path)
        assert loaded_image is not None
        assert loaded_image.shape == test_image.shape
        
        # 清理
        os.unlink(result_path)
    
    def test_save_temp_image_bytes(self):
        """測試保存bytes圖像數據"""
        # 建立測試圖像並轉換為bytes
        test_image = np.zeros((50, 50, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', test_image)
        image_bytes = buffer.tobytes()
        
        # 保存圖像
        filename = "test_bytes_image.jpg"
        result_path = save_temp_image(image_bytes, filename)
        
        # 驗證結果
        assert os.path.exists(result_path)
        assert filename in result_path
        
        # 驗證檔案大小
        file_size = os.path.getsize(result_path)
        assert file_size > 0
        
        # 清理
        os.unlink(result_path)
    
    def test_save_temp_image_invalid_data(self):
        """測試保存無效數據類型"""
        invalid_data = "This is not image data"
        
        with pytest.raises(ValueError, match="不支援的圖像數據類型"):
            save_temp_image(invalid_data, "test.jpg")
    
    def test_format_file_size(self):
        """測試檔案大小格式化功能"""
        from utils import format_file_size
        
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(500) == "500.0 B"
        assert format_file_size(1073741824) == "1.0 GB"

class TestIntegration:
    """整合測試"""
    
    def test_end_to_end_mock_workflow(self):
        """測試端到端的mock工作流程"""
        # 建立測試圖像
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, test_image)
            
            # 使用mock測試完整流程
            with patch('image_processor.ComputerVisionClient'):
                with patch.object(ImageProcessor, 'analyze_image_with_azure') as mock_analyze:
                    mock_analyze.return_value = ['mocked_food_1', 'mocked_food_2']
                    
                    # 執行完整流程
                    result = process_image(tmp_file.name)
                    
                    # 驗證結果
                    assert isinstance(result, list)
                    assert len(result) == 2
                    assert 'mocked_food_1' in result
                    assert 'mocked_food_2' in result
        
        # 清理
        os.unlink(tmp_file.name)

# 測試夾具和配置
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """設定測試環境"""
    # 確保測試環境變數
    test_env = {
        'AZURE_KEY': 'test_azure_key',
        'AZURE_ENDPOINT': 'https://test.cognitiveservices.azure.com/',
        'LOG_LEVEL': 'DEBUG'
    }
    
    with patch.dict(os.environ, test_env):
        yield

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """自動清理測試產生的臨時檔案"""
    yield
    
    # 清理temp目錄中的測試檔案
    project_root = Path(__file__).parent.parent
    temp_dir = project_root / "temp"
    
    if temp_dir.exists():
        for file in temp_dir.glob("test_*"):
            try:
                file.unlink()
            except:
                pass  # 忽略清理錯誤

if __name__ == "__main__":
    # 直接運行測試
    pytest.main([__file__, "-v", "--tb=short"])