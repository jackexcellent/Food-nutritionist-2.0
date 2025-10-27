"""
Diet Tracker Bot - 圖像處理模組
==============================

這個模組負責處理食物圖像識別的核心功能，包括：
1. 圖像預處理（調整大小、去噪）
2. Azure Computer Vision API整合
3. 食物識別結果解析

設計原則：
- 模組化設計，易於測試和維護
- 詳細的錯誤處理和日誌記錄
- 支援未來擴展（替換API、本地模型等）

未來擴展計畫：
1. 支援多種圖像格式
2. 本地AI模型fallback
3. 圖像增強和前處理優化
4. 多語言食物名稱識別
5. 批量圖像處理
"""

import os
import sys
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Tuple
from dotenv import load_dotenv

# Azure Computer Vision imports
try:
    from azure.cognitiveservices.vision.computervision import ComputerVisionClient
    from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
    from msrest.authentication import CognitiveServicesCredentials
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logging.warning("Azure Computer Vision SDK 未安裝，請執行: pip install azure-cognitiveservices-vision-computervision")

# 導入專案共用工具
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

from utils import handle_error, save_temp_image

# 載入環境變數
config_path = project_root / "config" / ".env"
load_dotenv(config_path)

# 模組級別的日誌器
logger = logging.getLogger(__name__)

class ImageProcessor:
    """
    圖像處理器類別
    
    負責處理食物圖像識別的完整流程：
    1. 圖像預處理
    2. Azure API呼叫
    3. 結果解析和過濾
    
    未來擴展：
    - 支援多個AI服務提供商（Google Vision, AWS Rekognition）
    - 本地AI模型整合
    - 圖像品質評估
    """
    
    def __init__(self):
        """初始化圖像處理器"""
        self.azure_client = None
        self.max_image_size = (800, 600)  # 標準預處理尺寸
        self.blur_kernel_size = (5, 5)   # 高斯模糊核心大小
        
        # 初始化Azure Computer Vision客戶端
        if AZURE_AVAILABLE:
            self._initialize_azure_client()
        else:
            logger.warning("Azure SDK 不可用，圖像識別功能將受限")
    
    def _initialize_azure_client(self) -> None:
        """
        初始化Azure Computer Vision客戶端
        
        從環境變數載入API金鑰和端點，建立認證客戶端。
        如果初始化失敗，會記錄錯誤但不會中斷程式執行。
        
        未來擴展：
        - 支援多個Azure區域的自動故障轉移
        - API金鑰輪換機制
        - 連接池和重試策略
        """
        try:
            azure_key = os.getenv('AZURE_KEY')
            azure_endpoint = os.getenv('AZURE_ENDPOINT')
            
            if not azure_key or not azure_endpoint:
                logger.error("Azure API金鑰或端點未設定")
                return
            
            # 建立認證和客戶端
            credentials = CognitiveServicesCredentials(azure_key)
            self.azure_client = ComputerVisionClient(azure_endpoint, credentials)
            
            logger.info("Azure Computer Vision 客戶端初始化成功")
            
        except Exception as e:
            handle_error(e, "初始化Azure Computer Vision客戶端", 
                        logger=logger, raise_error=False)
    
    def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        預處理圖像
        
        執行以下預處理步驟：
        1. 讀取圖像檔案
        2. 調整圖像大小到標準尺寸
        3. 應用高斯模糊去噪
        4. 驗證圖像品質
        
        Args:
            image_path (str): 圖像檔案路徑
        
        Returns:
            Optional[np.ndarray]: 預處理後的圖像陣列，失敗時返回None
        
        未來擴展：
        - 自動曝光和對比度調整
        - 圖像旋轉校正
        - 多種圖像增強濾鏡
        - 圖像品質評分
        """
        try:
            # 檢查檔案是否存在
            if not Path(image_path).exists():
                logger.error(f"圖像檔案不存在: {image_path}")
                return None
            
            # 讀取圖像
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"無法讀取圖像檔案: {image_path}")
                return None
            
            logger.debug(f"原始圖像尺寸: {image.shape}")
            
            # 調整圖像大小到標準尺寸
            resized_image = cv2.resize(image, self.max_image_size, 
                                     interpolation=cv2.INTER_LANCZOS4)
            
            # 應用高斯模糊去噪（輕微模糊，保持細節）
            blurred_image = cv2.GaussianBlur(resized_image, self.blur_kernel_size, 0)
            
            logger.debug(f"預處理後圖像尺寸: {blurred_image.shape}")
            
            # 保存預處理後的圖像用於偵錯
            temp_path = save_temp_image(blurred_image, "preprocessed_image.jpg")
            logger.debug(f"預處理圖像已保存到: {temp_path}")
            
            return blurred_image
            
        except Exception as e:
            return handle_error(e, f"預處理圖像 {image_path}", 
                              logger=logger, raise_error=False, default_return=None)
    
    def analyze_image_with_azure(self, image_data) -> List[str]:
        """
        使用Azure Computer Vision API分析圖像
        
        將圖像數據發送到Azure API進行分析，提取食物相關的標籤和描述。
        
        Args:
            image_data: 圖像的二進制數據流（BytesIO 物件）
        
        Returns:
            List[str]: 識別出的食物名稱列表
        
        未來擴展：
        - 支援自訂置信度閾值
        - 多語言結果支援
        - 營養成分預估
        - 食物份量識別
        """
        if not self.azure_client:
            logger.error("Azure客戶端未初始化")
            return []
        
        try:
            # 使用Azure Computer Vision API分析圖像
            # 獲取標籤（tags）- 包含食物相關關鍵詞
            analysis = self.azure_client.analyze_image_in_stream(
                image_data,
                visual_features=['Tags', 'Description', 'Categories']
            )
            
            food_items = []
            
            # 從標籤中提取食物相關項目
            if hasattr(analysis, 'tags') and analysis.tags:
                food_tags = self._extract_food_from_tags(analysis.tags)
                food_items.extend(food_tags)
                logger.debug(f"從標籤提取到 {len(food_tags)} 個食物項目")
            
            # 從描述中提取食物相關項目
            if hasattr(analysis, 'description') and analysis.description:
                food_descriptions = self._extract_food_from_descriptions(analysis.description)
                food_items.extend(food_descriptions)
                logger.debug(f"從描述提取到 {len(food_descriptions)} 個食物項目")
            
            # 去除重複項目並過濾
            unique_foods = list(set(food_items))
            filtered_foods = self._filter_food_items(unique_foods)
            
            logger.info(f"Azure API 識別出 {len(filtered_foods)} 個食物項目: {filtered_foods}")
            return filtered_foods
            
        except Exception as e:
            return handle_error(e, "Azure Computer Vision API 呼叫", 
                              logger=logger, raise_error=False, default_return=[])
    
    def _extract_food_from_tags(self, tags) -> List[str]:
        """
        從Azure API標籤中提取食物相關項目
        
        過濾出與食物相關的標籤，排除非食物項目。
        
        Args:
            tags: Azure API返回的標籤列表
        
        Returns:
            List[str]: 食物相關標籤列表
        """
        food_keywords = {
            'food', 'dish', 'meal', 'cuisine', 'ingredient', 'fruit', 'vegetable',
            'meat', 'fish', 'bread', 'rice', 'pasta', 'soup', 'salad', 'dessert',
            'drink', 'beverage', 'snack', 'breakfast', 'lunch', 'dinner'
        }
        
        # 非食物關鍵詞，需要排除
        non_food_keywords = {
            'person', 'table', 'plate', 'bowl', 'cup', 'utensil', 'restaurant',
            'kitchen', 'background', 'indoor', 'outdoor'
        }
        
        food_items = []
        
        for tag in tags:
            tag_name = tag.name.lower().strip()
            confidence = getattr(tag, 'confidence', 0.0)
            
            # 置信度篩選（可調整）
            if confidence < 0.3:
                continue
            
            # 檢查是否為食物相關標籤
            is_food_related = any(keyword in tag_name for keyword in food_keywords)
            is_non_food = any(keyword in tag_name for keyword in non_food_keywords)
            
            if is_food_related and not is_non_food:
                food_items.append(tag_name)
                logger.debug(f"食物標籤: {tag_name} (置信度: {confidence:.2f})")
        
        return food_items
    
    def _extract_food_from_descriptions(self, description) -> List[str]:
        """
        從Azure API描述中提取食物相關項目
        
        分析圖像描述文字，提取可能的食物名稱。
        
        Args:
            description: Azure API返回的描述對象
        
        Returns:
            List[str]: 從描述中提取的食物項目
        """
        food_items = []
        
        # 處理主要描述
        if hasattr(description, 'captions') and description.captions:
            for caption in description.captions:
                if hasattr(caption, 'text'):
                    # 簡單的關鍵詞提取（未來可用NLP改進）
                    text = caption.text.lower()
                    potential_foods = self._extract_foods_from_text(text)
                    food_items.extend(potential_foods)
        
        return food_items
    
    def _extract_foods_from_text(self, text: str) -> List[str]:
        """
        從文字中提取食物名稱
        
        使用簡單的關鍵詞匹配提取食物名稱。
        未來可以使用更複雜的NLP技術。
        
        Args:
            text (str): 要分析的文字
        
        Returns:
            List[str]: 提取的食物名稱列表
        """
        # 常見食物關鍵詞列表（可擴展）
        common_foods = {
            'apple', 'banana', 'orange', 'rice', 'chicken', 'beef', 'pork',
            'fish', 'salmon', 'tuna', 'bread', 'pasta', 'noodles', 'soup',
            'salad', 'vegetables', 'broccoli', 'carrot', 'potato', 'tomato',
            'cheese', 'milk', 'egg', 'tofu', 'beans', 'nuts'
        }
        
        found_foods = []
        words = text.split()
        
        for word in words:
            clean_word = word.strip('.,!?()[]{}').lower()
            if clean_word in common_foods:
                found_foods.append(clean_word)
        
        return found_foods
    
    def _filter_food_items(self, food_items: List[str]) -> List[str]:
        """
        過濾和清理食物項目列表
        
        移除重複、無效或不相關的項目。
        
        Args:
            food_items (List[str]): 原始食物項目列表
        
        Returns:
            List[str]: 過濾後的食物項目列表
        """
        if not food_items:
            return []
        
        # 移除重複並轉為小寫
        unique_items = list(set(item.lower().strip() for item in food_items))
        
        # 過濾掉太短或太長的項目
        filtered_items = [
            item for item in unique_items 
            if 2 <= len(item) <= 30 and item.isalpha()
        ]
        
        # 按字母順序排序
        filtered_items.sort()
        
        logger.debug(f"過濾前: {len(food_items)} 項目，過濾後: {len(filtered_items)} 項目")
        
        return filtered_items

def process_image(image_path: str) -> List[str]:
    """
    處理圖像並識別食物的主要函數
    
    這是模組的主要入口點，執行完整的圖像處理流程：
    1. 預處理圖像
    2. 調用Azure API進行識別
    3. 解析和過濾結果
    
    Args:
        image_path (str): 圖像檔案路徑
    
    Returns:
        List[str]: 識別出的食物名稱列表
    
    使用範例:
        foods = process_image("my_meal.jpg")
        print(f"識別出的食物: {foods}")
    
    未來擴展：
    - 支援URL圖像
    - 批量處理多張圖像
    - 返回置信度分數
    - 本地模型fallback
    """
    logger.info(f"開始處理圖像: {image_path}")
    
    try:
        # 初始化圖像處理器
        processor = ImageProcessor()
        
        # 預處理圖像
        processed_image = processor.preprocess_image(image_path)
        if processed_image is None:
            logger.error("圖像預處理失敗")
            return []
        
        # 將處理後的圖像轉換為bytes格式並包裝成類似檔案的物件
        _, buffer = cv2.imencode('.jpg', processed_image)
        image_bytes = buffer.tobytes()
        
        # 將bytes包裝成BytesIO對象，讓Azure API能讀取
        from io import BytesIO
        image_stream = BytesIO(image_bytes)
        
        # 使用Azure API分析圖像
        if processor.azure_client:
            food_list = processor.analyze_image_with_azure(image_stream)
        else:
            logger.warning("Azure客戶端不可用，返回空列表")
            food_list = []
        
        logger.info(f"圖像處理完成，識別出 {len(food_list)} 個食物項目")
        return food_list
        
    except Exception as e:
        return handle_error(e, f"處理圖像 {image_path}", 
                          logger=logger, raise_error=False, default_return=[])

def main():
    """
    命令列測試入口點
    
    允許從命令列直接測試圖像處理功能：
    python -m src.image_processor test_image.jpg
    
    未來擴展：
    - 支援多個圖像檔案
    - 輸出格式選項（JSON、CSV等）
    - 批量處理模式
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='測試圖像處理功能')
    parser.add_argument('image_path', help='要處理的圖像檔案路徑')
    parser.add_argument('--debug', action='store_true', help='啟用詳細日誌')
    
    args = parser.parse_args()
    
    # 設定日誌級別
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 處理圖像
    print(f"\n🔍 正在分析圖像: {args.image_path}")
    food_list = process_image(args.image_path)
    
    # 顯示結果
    if food_list:
        print(f"\n✅ 識別出的食物項目:")
        for i, food in enumerate(food_list, 1):
            print(f"  {i}. {food}")
    else:
        print("\n❌ 未識別出任何食物項目")
    
    print(f"\n📊 總計: {len(food_list)} 個食物項目")

if __name__ == "__main__":
    main()