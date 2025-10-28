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

# Google Gemini imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Generative AI SDK 未安裝，請執行: pip install google-generativeai")

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
    2. Azure/Google API呼叫
    3. 結果解析和過濾
    
    未來擴展：
    - 支援多個AI服務提供商（Google Vision, AWS Rekognition）
    - 本地AI模型整合
    - 圖像品質評估
    """
    
    def __init__(self):
        """初始化圖像處理器"""
        self.azure_client = None
        self.gemini_model = None
        self.max_image_size = (800, 600)  # 標準預處理尺寸
        self.enhancement_enabled = True   # 啟用圖像增強
        
        # 初始化Azure Computer Vision客戶端
        if AZURE_AVAILABLE:
            self._initialize_azure_client()
        else:
            logger.warning("Azure SDK 不可用，圖像識別功能將受限")
        
        # 初始化 Gemini Vision 模型
        if GEMINI_AVAILABLE:
            self._initialize_gemini_model()
        else:
            logger.warning("Gemini SDK 不可用，將無法使用進階食物識別")
    
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
    
    def _initialize_gemini_model(self) -> None:
        """
        初始化 Google Gemini Vision 模型
        
        Gemini 具有更強大的視覺理解能力，特別適合識別具體的食物種類。
        """
        try:
            gemini_key = os.getenv('GEMINI_KEY')
            
            if not gemini_key:
                logger.error("Gemini API金鑰未設定")
                return
            
            # 配置 Gemini API
            genai.configure(api_key=gemini_key)
            
            # 使用 Gemini 2.0 Flash 模型 (支援視覺輸入)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            
            logger.info("Gemini Vision 模型初始化成功")
            
        except Exception as e:
            handle_error(e, "初始化 Gemini Vision 模型", 
                        logger=logger, raise_error=False)
    
    def analyze_image_with_gemini(self, image_path: str) -> List[str]:
        """
        使用 Gemini Vision 進行詳細的食物識別
        
        Gemini 能夠識別具體的食物名稱，特別是亞洲食物。
        
        Args:
            image_path (str): 圖像檔案路徑
        
        Returns:
            List[str]: 識別出的具體食物名稱列表
        """
        if not self.gemini_model:
            logger.error("Gemini模型未初始化")
            return []
        
        try:
            from PIL import Image
            
            # 載入圖像
            img = Image.open(image_path)
            
            # 構建詳細的提示詞
            prompt = """請仔細分析這張食物圖片，並列出圖片中所有可以看到的食物項目。

要求：
1. 請用中文和英文雙語列出每種食物
2. 盡可能具體，例如：不要只說"豆腐"，要說"臭豆腐"或"油炸豆腐"
3. 列出所有可見的配菜和醬料
4. 如果有多個相同食物，請標注數量
5. 格式：食物名稱（英文名稱）

請按照這個格式回答，每行一個食物項目：
- 食物名稱（English Name）
"""
            
            # 發送請求
            response = self.gemini_model.generate_content([prompt, img])
            
            if response and response.text:
                logger.debug(f"Gemini 原始回應:\n{response.text}")
                
                # 解析響應文本
                food_items = self._parse_gemini_response(response.text)
                logger.info(f"✨ Gemini 識別出 {len(food_items)} 個具體食物")
                
                return food_items
            else:
                logger.warning("Gemini 未返回有效響應")
                return []
            
        except Exception as e:
            return handle_error(e, "Gemini Vision API 呼叫", 
                              logger=logger, raise_error=False, default_return=[])
    
    def _parse_gemini_response(self, response_text: str) -> List[str]:
        """
        解析 Gemini 的響應文本，提取食物項目
        
        Args:
            response_text (str): Gemini 返回的文本
        
        Returns:
            List[str]: 解析出的食物項目列表
        """
        food_items = []
        lines = response_text.strip().split('\n')
        
        # 過濾掉開頭的禮貌性回應或說明文字
        skip_phrases = ['好的', '我來', '分析', '以下是', '讓我', '這張圖', '根據', '可以看到']
        
        for line in lines:
            line = line.strip()
            
            # 跳過空行
            if not line or len(line) < 3:
                continue
            
            # 跳過禮貌性開頭(通常不含括號)
            if any(phrase in line for phrase in skip_phrases) and '(' not in line:
                continue
            
            # 移除項目符號
            if line.startswith(('- ', '* ', '• ')):
                line = line.lstrip('-*• ')
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                line = line.lstrip('0123456789. ')
            
            # 只保留包含食物描述的行(通常包含括號或中文食物名稱)
            if line and (('(' in line and ')' in line) or any('\u4e00' <= c <= '\u9fff' for c in line)):
                food_items.append(line)
        
        return food_items
    
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
            
            # 圖像增強：提升對比度和亮度（而不是模糊）
            enhanced_image = self._enhance_image_quality(resized_image)
            
            logger.debug(f"預處理後圖像尺寸: {enhanced_image.shape}")
            
            # 保存預處理後的圖像用於偵錯
            temp_path = save_temp_image(enhanced_image, "preprocessed_image.jpg")
            logger.debug(f"預處理圖像已保存到: {temp_path}")
            
            return enhanced_image
            
        except Exception as e:
            return handle_error(e, f"預處理圖像 {image_path}", 
                              logger=logger, raise_error=False, default_return=None)

    def _enhance_image_quality(self, image: np.ndarray) -> np.ndarray:
        """
        增強圖像品質而不降低清晰度
        
        執行以下增強步驟：
        1. 自動對比度調整（CLAHE）
        2. 輕微銳化處理
        3. 色彩平衡調整
        
        Args:
            image (np.ndarray): 輸入圖像
        
        Returns:
            np.ndarray: 增強後的圖像
        """
        try:
            # 轉換到 LAB 色彩空間進行亮度增強
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            
            # 應用 CLAHE（對比度限制自適應直方圖均衡化）到亮度通道
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_l = clahe.apply(l_channel)
            
            # 合併通道並轉換回 BGR
            enhanced_lab = cv2.merge([enhanced_l, a_channel, b_channel])
            enhanced_image = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
            
            # 輕微銳化（增強細節而不產生噪點）
            kernel = np.array([[-0.1, -0.1, -0.1],
                             [-0.1,  1.8, -0.1],
                             [-0.1, -0.1, -0.1]])
            sharpened = cv2.filter2D(enhanced_image, -1, kernel)
            
            # 混合原圖和銳化圖像（85% 銳化 + 15% 原圖）
            final_image = cv2.addWeighted(sharpened, 0.85, enhanced_image, 0.15, 0)
            
            logger.debug("圖像品質增強完成：對比度提升 + 輕微銳化")
            return final_image
            
        except Exception as e:
            logger.warning(f"圖像增強失敗，使用原圖: {e}")
            return image

    def analyze_image_with_azure(self, image_data) -> List[str]:
        """
        使用Azure Computer Vision API分析圖像
        
        將圖像數據發送到Azure API進行分析，提取食物相關的標籤和描述。
        使用詳細的食物識別prompt來獲取更精確的食物名稱、份量和成分信息。
        
        Args:
            image_data: 圖像的二進制數據流（BytesIO 物件）
        
        Returns:
            List[str]: 識別出的詳細食物資訊列表
        
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
            # 重置流位置到開頭
            image_data.seek(0)
            
            # 使用Azure Computer Vision API進行詳細的食物分析
            # 獲取多種視覺特徵以提供更完整的食物資訊
            analysis = self.azure_client.analyze_image_in_stream(
                image_data,
                visual_features=['Tags', 'Description', 'Categories', 'Objects'],
                language='zh'  # 使用中文，有助於識別亞洲食物
                # 注意：移除了details參數，因為Azure Computer Vision v3.2 API不支援'Food'作為details值
            )
            
            food_items = []
            detailed_descriptions = []
            
            # 首先記錄所有 API 返回的原始數據以便調試
            logger.debug("=== Azure API 原始返回數據 ===")
            
            # 檢查並記錄標籤信息
            if hasattr(analysis, 'tags') and analysis.tags:
                logger.debug(f"發現 {len(analysis.tags)} 個標籤:")
                for i, tag in enumerate(analysis.tags[:10]):  # 只顯示前10個
                    confidence = getattr(tag, 'confidence', 0.0)
                    logger.debug(f"  標籤 {i+1}: {tag.name} (置信度: {confidence:.3f})")
                
                food_tags = self._extract_detailed_food_from_tags(analysis.tags)
                food_items.extend(food_tags)
                logger.debug(f"從標籤提取到 {len(food_tags)} 個食物項目")
            else:
                logger.debug("沒有找到標籤信息")
            
            # 檢查並記錄描述信息
            if hasattr(analysis, 'description') and analysis.description:
                logger.debug("描述信息:")
                if hasattr(analysis.description, 'captions') and analysis.description.captions:
                    for i, caption in enumerate(analysis.description.captions):
                        confidence = getattr(caption, 'confidence', 0.0)
                        logger.debug(f"  描述 {i+1}: {caption.text} (置信度: {confidence:.3f})")
                
                detailed_food_info = self._extract_detailed_food_descriptions(analysis.description)
                detailed_descriptions.extend(detailed_food_info)
                logger.debug(f"從描述提取到 {len(detailed_food_info)} 個詳細描述")
            else:
                logger.debug("沒有找到描述信息")
            
            # 檢查並記錄物件檢測信息
            if hasattr(analysis, 'objects') and analysis.objects:
                logger.debug(f"發現 {len(analysis.objects)} 個物件:")
                for i, obj in enumerate(analysis.objects[:5]):  # 只顯示前5個
                    confidence = getattr(obj, 'confidence', 0.0)
                    logger.debug(f"  物件 {i+1}: {obj.object_property} (置信度: {confidence:.3f})")
                
                object_foods = self._extract_food_from_objects(analysis.objects)
                food_items.extend(object_foods)
                logger.debug(f"從物件檢測提取到 {len(object_foods)} 個食物項目")
            else:
                logger.debug("沒有找到物件檢測信息")
            
            # 檢查分類信息
            if hasattr(analysis, 'categories') and analysis.categories:
                logger.debug(f"發現 {len(analysis.categories)} 個分類:")
                for i, category in enumerate(analysis.categories):
                    score = getattr(category, 'score', 0.0)
                    logger.debug(f"  分類 {i+1}: {category.name} (分數: {score:.3f})")
            else:
                logger.debug("沒有找到分類信息")
            
            logger.debug("=== 原始數據記錄完畢 ===")
            
            # 合併所有食物資訊
            all_food_info = food_items + detailed_descriptions
            
            # 去除重複項目並進行智能過濾
            unique_foods = list(set(all_food_info))
            filtered_foods = self._filter_and_enhance_food_items(unique_foods)
            
            logger.info(f"Azure API 識別出 {len(filtered_foods)} 個詳細食物項目")
            for food in filtered_foods:
                logger.debug(f"識別食物: {food}")
            
            return filtered_foods
            
        except Exception as e:
            return handle_error(e, "Azure Computer Vision API 呼叫", 
                              logger=logger, raise_error=False, default_return=[])
    
    def _extract_detailed_food_from_tags(self, tags) -> List[str]:
        """
        從Azure API標籤中提取詳細的食物相關項目
        
        過濾出與食物相關的標籤，並包含置信度和詳細資訊。
        
        Args:
            tags: Azure API返回的標籤列表
        
        Returns:
            List[str]: 包含詳細資訊的食物標籤列表
        """
        # 擴展的食物關鍵詞，包含更具體的食物類型和亞洲食物
        food_keywords = {
            # 基本類別
            'food', 'dish', 'meal', 'cuisine', 'ingredient', 'fruit', 'vegetable',
            'meat', 'fish', 'bread', 'rice', 'pasta', 'soup', 'salad', 'dessert',
            'drink', 'beverage', 'snack', 'breakfast', 'lunch', 'dinner',
            
            # 具體食物
            'chicken', 'beef', 'pork', 'salmon', 'tuna', 'apple', 'banana',
            'orange', 'tomato', 'carrot', 'broccoli', 'potato', 'noodles',
            'sandwich', 'pizza', 'burger', 'sushi', 'cake', 'cookie', 'cheese',
            
            # 亞洲食物關鍵詞
            'tofu', 'bean curd', 'soy', 'soybean', 'tempeh', 'edamame',
            'fermented', 'pickled', 'kimchi', 'pickle', 'cabbage',
            'dumpling', 'wonton', 'bun', 'roll', 'spring roll',
            'fried', 'steamed', 'stir fry', 'stir-fry',
            'asian', 'chinese', 'japanese', 'korean', 'taiwanese', 'thai',
            'street food', 'vendor', 'hawker',
            'seaweed', 'kelp', 'miso', 'wasabi', 'ginger', 'garlic',
            'sauce', 'soy sauce', 'chili', 'spicy',
        }
        
        # 非食物關鍵詞，需要排除
        non_food_keywords = {
            'person', 'table', 'plate', 'bowl', 'cup', 'utensil', 'restaurant',
            'kitchen', 'background', 'indoor', 'outdoor', 'hand', 'finger'
        }
        
        food_items = []
        
        for tag in tags:
            tag_name = tag.name.lower().strip()
            confidence = getattr(tag, 'confidence', 0.0)
            
            # 降低置信度閾值以獲取更多可能的食物項目
            if confidence < 0.2:
                continue
            
            # 檢查是否為食物相關標籤
            is_food_related = any(keyword in tag_name for keyword in food_keywords)
            is_non_food = any(keyword in tag_name for keyword in non_food_keywords)
            
            if is_food_related and not is_non_food:
                # 根據置信度添加詳細資訊
                if confidence >= 0.7:
                    food_detail = f"{tag_name} (高置信度: {confidence:.2f})"
                elif confidence >= 0.5:
                    food_detail = f"{tag_name} (中置信度: {confidence:.2f})"
                else:
                    food_detail = f"{tag_name} (可能性: {confidence:.2f})"
                
                food_items.append(food_detail)
                logger.debug(f"詳細食物標籤: {food_detail}")
        
        return food_items
    
    def _extract_food_from_tags(self, tags) -> List[str]:
        """
        從Azure API標籤中提取食物相關項目（舊版本，保持兼容性）
        
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
        
        non_food_keywords = {
            'person', 'table', 'plate', 'bowl', 'cup', 'utensil', 'restaurant',
            'kitchen', 'background', 'indoor', 'outdoor'
        }
        
        food_items = []
        
        for tag in tags:
            tag_name = tag.name.lower().strip()
            confidence = getattr(tag, 'confidence', 0.0)
            
            if confidence < 0.3:
                continue
            
            is_food_related = any(keyword in tag_name for keyword in food_keywords)
            is_non_food = any(keyword in tag_name for keyword in non_food_keywords)
            
            if is_food_related and not is_non_food:
                food_items.append(tag_name)
                logger.debug(f"食物標籤: {tag_name} (置信度: {confidence:.2f})")
        
        return food_items
    
    def _extract_detailed_food_descriptions(self, description) -> List[str]:
        """
        從Azure API描述中提取詳細的食物相關資訊
        
        分析圖像描述文字，提取詳細的食物名稱、份量和成分資訊。
        
        Args:
            description: Azure API返回的描述對象
        
        Returns:
            List[str]: 從描述中提取的詳細食物資訊
        """
        food_descriptions = []
        
        # 處理主要描述
        if hasattr(description, 'captions') and description.captions:
            for caption in description.captions:
                if hasattr(caption, 'text'):
                    text = caption.text
                    confidence = getattr(caption, 'confidence', 0.0)
                    
                    # 分析描述文字以提取詳細資訊
                    detailed_info = self._analyze_food_description(text, confidence)
                    if detailed_info:
                        food_descriptions.extend(detailed_info)
        
        return food_descriptions
    
    def _analyze_food_description(self, description_text: str, confidence: float) -> List[str]:
        """
        詳細分析描述文字以提取食物資訊
        
        Args:
            description_text (str): 描述文字
            confidence (float): 描述的置信度
        
        Returns:
            List[str]: 提取的詳細食物資訊
        """
        detailed_foods = []
        text = description_text.lower()
        
        # 份量相關關鍵詞
        portion_keywords = {
            'bowl', 'plate', 'cup', 'glass', 'slice', 'piece', 'serving',
            'portion', 'small', 'large', 'medium', 'big', 'little', 'full',
            'half', 'quarter', 'whole', 'single', 'double', 'triple'
        }
        
        # 烹飪方式關鍵詞
        cooking_methods = {
            'fried', 'grilled', 'baked', 'steamed', 'boiled', 'roasted',
            'sautéed', 'raw', 'fresh', 'cooked', 'prepared'
        }
        
        # 成分和配菜關鍵詞
        ingredient_keywords = {
            'with', 'and', 'topped', 'served', 'garnished', 'mixed',
            'contains', 'includes', 'accompanied'
        }
        
        # 基本食物提取
        basic_foods = self._extract_foods_from_text(text)
        
        # 分析份量資訊
        portion_info = []
        for portion in portion_keywords:
            if portion in text:
                portion_info.append(portion)
        
        # 分析烹飪方式
        cooking_info = []
        for method in cooking_methods:
            if method in text:
                cooking_info.append(method)
        
        # 組合詳細資訊
        if basic_foods:
            base_description = f"描述: {description_text}"
            if confidence >= 0.5:
                base_description += f" (高可信度: {confidence:.2f})"
            else:
                base_description += f" (可信度: {confidence:.2f})"
            
            detailed_foods.append(base_description)
            
            # 為每個識別的食物添加詳細資訊
            for food in basic_foods:
                food_detail = f"食物: {food}"
                
                if portion_info:
                    food_detail += f" | 份量描述: {', '.join(portion_info)}"
                
                if cooking_info:
                    food_detail += f" | 烹飪方式: {', '.join(cooking_info)}"
                
                detailed_foods.append(food_detail)
        
        return detailed_foods
    
    def _extract_food_from_descriptions(self, description) -> List[str]:
        """
        從Azure API描述中提取食物相關項目（舊版本，保持兼容性）
        
        Args:
            description: Azure API返回的描述對象
        
        Returns:
            List[str]: 從描述中提取的食物項目
        """
        food_items = []
        
        if hasattr(description, 'captions') and description.captions:
            for caption in description.captions:
                if hasattr(caption, 'text'):
                    text = caption.text.lower()
                    potential_foods = self._extract_foods_from_text(text)
                    food_items.extend(potential_foods)
        
        return food_items
    
    def _extract_foods_from_text(self, text: str) -> List[str]:
        """
        從文字中提取食物名稱
        
        使用擴展的關鍵詞匹配提取食物名稱，特別針對亞洲食物。
        
        Args:
            text (str): 要分析的文字
        
        Returns:
            List[str]: 提取的食物名稱列表
        """
        # 擴展的食物關鍵詞列表，包含中文和英文常見食物
        common_foods = {
            # 基本食物
            'apple', 'banana', 'orange', 'rice', 'chicken', 'beef', 'pork',
            'fish', 'salmon', 'tuna', 'bread', 'pasta', 'noodles', 'soup',
            'salad', 'vegetables', 'broccoli', 'carrot', 'potato', 'tomato',
            'cheese', 'milk', 'egg', 'beans', 'nuts',
            
            # 亞洲食物 - 特別加強
            'tofu', 'bean curd', 'fermented tofu', 'stinky tofu', '豆腐', '臭豆腐',
            'kimchi', 'pickle', 'pickled', 'fermented', 'cabbage', '泡菜', '醃菜',
            'dumpling', 'wonton', 'bun', 'steamed bun', '餃子', '包子', '饅頭',
            'spring roll', 'egg roll', '春捲', '蛋捲',
            'fried rice', 'congee', 'porridge', '炒飯', '粥',
            'noodle soup', 'ramen', 'pho', '麵', '拉麵', '河粉',
            'soy', 'soybean', 'edamame', '黃豆', '毛豆',
            'seaweed', 'kelp', '海帶', '紫菜',
            'miso', 'tempeh', '味噌', '天貝',
            
            # 醬料和調味料
            'sauce', 'soy sauce', 'chili', 'garlic', 'ginger',
            '醬油', '辣椒', '大蒜', '薑',
            
            # 街頭小吃
            'street food', 'snack', 'fried food', '小吃', '炸物',
        }
        
        found_foods = []
        text_lower = text.lower()
        
        # 先嘗試匹配較長的片語（如 "stinky tofu"）
        for food in sorted(common_foods, key=len, reverse=True):
            if food in text_lower:
                found_foods.append(food)
        
        # 去除重複
        found_foods = list(dict.fromkeys(found_foods))
        
        return found_foods
    
    def _extract_food_from_objects(self, objects) -> List[str]:
        """
        從Azure API物件檢測中提取食物相關項目
        
        分析檢測到的物件，提取食物項目和位置資訊。
        
        Args:
            objects: Azure API返回的物件列表
        
        Returns:
            List[str]: 從物件檢測中提取的食物項目
        """
        food_objects = []
        
        for obj in objects:
            object_name = obj.object_property.lower().strip()
            confidence = getattr(obj, 'confidence', 0.0)
            
            # 檢查是否為食物相關物件
            food_related_objects = {
                'apple', 'banana', 'orange', 'sandwich', 'pizza', 'burger',
                'cake', 'cookie', 'bread', 'donut', 'hot dog', 'taco'
            }
            
            if object_name in food_related_objects and confidence >= 0.3:
                # 獲取物件位置資訊
                if hasattr(obj, 'rectangle'):
                    rect = obj.rectangle
                    location_info = f"物件: {object_name} (位置: x={rect.x}, y={rect.y}, 寬={rect.w}, 高={rect.h}, 置信度: {confidence:.2f})"
                else:
                    location_info = f"物件: {object_name} (置信度: {confidence:.2f})"
                
                food_objects.append(location_info)
                logger.debug(f"檢測到食物物件: {location_info}")
        
        return food_objects
    
    def _filter_and_enhance_food_items(self, food_items: List[str]) -> List[str]:
        """
        增強版的食物項目過濾和整理函數
        
        保留詳細資訊並進行智能過濾。
        
        Args:
            food_items (List[str]): 原始食物項目列表
        
        Returns:
            List[str]: 過濾和增強後的食物項目列表
        """
        if not food_items:
            return []
        
        # 分類不同類型的資訊
        simple_foods = []
        detailed_descriptions = []
        object_detections = []
        confidence_foods = []
        
        for item in food_items:
            if item.startswith('描述:'):
                detailed_descriptions.append(item)
            elif item.startswith('食物:'):
                detailed_descriptions.append(item)
            elif item.startswith('物件:'):
                object_detections.append(item)
            elif '置信度' in item or '可信度' in item or '可能性' in item:
                confidence_foods.append(item)
            else:
                simple_foods.append(item)
        
        # 組合結果，保持詳細資訊的完整性
        result = []
        
        # 添加詳細描述（最重要的資訊）
        if detailed_descriptions:
            result.extend(detailed_descriptions)
        
        # 添加物件檢測結果
        if object_detections:
            result.extend(object_detections)
        
        # 添加有置信度的食物項目
        if confidence_foods:
            result.extend(confidence_foods)
        
        # 添加簡單的食物名稱（去重）
        if simple_foods:
            unique_simple = list(set(simple_foods))
            result.extend(unique_simple)
        
        logger.debug(f"詳細過濾結果 - 總項目: {len(result)}")
        logger.debug(f"  描述: {len(detailed_descriptions)} 項")
        logger.debug(f"  物件: {len(object_detections)} 項") 
        logger.debug(f"  置信度食物: {len(confidence_foods)} 項")
        logger.debug(f"  簡單食物: {len(set(simple_foods))} 項")
        
        return result
    
    def _filter_food_items(self, food_items: List[str]) -> List[str]:
        """
        過濾和清理食物項目列表（舊版本，保持兼容性）
        
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
    2. 調用Azure API進行詳細的食物識別
    3. 解析和整理結果，包含食物名稱、份量、成分等詳細資訊
    
    Args:
        image_path (str): 圖像檔案路徑
    
    Returns:
        List[str]: 識別出的詳細食物資訊列表，包含：
                  - 完整的圖像描述和置信度
                  - 具體食物項目及其份量資訊
                  - 物件檢測結果和位置資訊
                  - 烹飪方式和成分描述
    
    使用範例:
        foods = process_image("my_meal.jpg")
        for food_info in foods:
            print(f"食物資訊: {food_info}")
    
    未來擴展：
    - 支援URL圖像
    - 批量處理多張圖像
    - 返回結構化的食物資訊字典
    - 本地AI模型fallback
    - 營養成分自動計算
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
        
        # 初始化結果列表
        all_food_items = []
        
        # === 方法 1: Azure Computer Vision API ===
        # Azure 提供通用的視覺理解和場景描述
        if processor.azure_client:
            logger.info("📊 使用 Azure Computer Vision API 進行分析...")
            
            # 將處理後的圖像轉換為bytes格式並包裝成類似檔案的物件
            _, buffer = cv2.imencode('.jpg', processed_image)
            image_bytes = buffer.tobytes()
            
            # 將bytes包裝成BytesIO對象，讓Azure API能讀取
            from io import BytesIO
            image_stream = BytesIO(image_bytes)
            
            azure_foods = processor.analyze_image_with_azure(image_stream)
            all_food_items.extend(azure_foods)
            logger.info(f"✅ Azure API 識別出 {len(azure_foods)} 個項目")
        else:
            logger.warning("⚠️ Azure客戶端不可用")
        
        # === 方法 2: Google Gemini Vision API ===
        # Gemini 提供更詳細的食物識別，特別是亞洲食物
        if processor.gemini_model:
            logger.info("✨ 使用 Gemini Vision API 進行詳細食物識別...")
            
            # 保存預處理後的圖像到臨時檔案供 Gemini 使用
            temp_image_path = save_temp_image(processed_image, "gemini_input.jpg")
            
            gemini_foods = processor.analyze_image_with_gemini(temp_image_path)
            all_food_items.extend(gemini_foods)
            logger.info(f"✅ Gemini API 識別出 {len(gemini_foods)} 個具體食物")
        else:
            logger.warning("⚠️ Gemini 模型不可用")
        
        # === 合併和去重 ===
        # 移除重複項目，優先保留更詳細的描述
        if all_food_items:
            # 簡單去重(保持順序，Gemini 結果在後面，優先度更高)
            seen = set()
            unique_foods = []
            
            # 先處理Azure結果(通用描述)
            for food in all_food_items:
                food_lower = food.lower()
                # 簡單的去重邏輯:如果包含相似的關鍵詞，跳過
                if not any(existing in food_lower or food_lower in existing 
                          for existing in seen):
                    unique_foods.append(food)
                    seen.add(food_lower)
            
            logger.info(f"🎯 最終識別出 {len(unique_foods)} 個不重複的食物項目")
            return unique_foods
        else:
            logger.warning("未能識別出任何食物項目")
            return []
        
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