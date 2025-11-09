#!/usr/bin/env python3
"""
Diet Tracker Bot - AI 推薦引擎模組
==================================

這個模組負責基於用戶的飲食歷史生成個人化的健康建議，包括：
1. 飲食歷史分析
2. Google Gemini LLM 整合
3. 智能推薦生成
4. Fallback 規則引擎

設計原則：
- MVP 使用 Gemini API 提供 AI 驅動的推薦
- 設計結構化 prompt 模板確保輸出品質
- 提供 fallback 機制保證系統穩定性
- 支援未來擴展為複雜的營養學分析

未來擴展計畫：
1. 添加營養素平衡分析
2. 個人化健康目標設定
3. 時間序列趨勢分析
4. 多語言支援
5. 用戶偏好學習
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

# 導入專案共用工具
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))

from utils import handle_error, format_retrieved_text
from data_storage import get_history, get_statistics, get_previous_meals, get_past_days

# 嘗試導入 Gemini SDK
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# 載入環境變數
from dotenv import load_dotenv
load_dotenv(project_root / "config" / ".env")

# 模組級別的日誌器
logger = logging.getLogger(__name__)

# API 配置
GEMINI_API_KEY = os.getenv("GEMINI_KEY")
DEFAULT_MODEL = "gemini-2.0-flash"  # 使用快速版本提升回應速度

# Gemini 客戶端初始化
gemini_client = None
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_client = genai.GenerativeModel(DEFAULT_MODEL)
        logger.info("Google Gemini 客戶端初始化成功")
    except Exception as e:
        logger.warning(f"Gemini 客戶端初始化失敗: {e}")
        gemini_client = None
else:
    if not GEMINI_AVAILABLE:
        logger.warning("Google Generative AI SDK 未安裝")
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_KEY 環境變數未設定")


# ========== Prompt 模板設計 ==========

class PromptTemplates:
    """
    結構化 Prompt 模板類別
    
    設計原則：
    1. 確保 LLM 輸出結構化且一致
    2. 提供清晰的上下文和指令
    3. 支援未來的 prompt 工程優化
    4. 包含營養學專業知識
    """
    
    # RAG 增強推薦 Prompt (MVP 版本)
    RAG_RECOMMENDATION = """
你是營養師,根據用戶飲食歷史提供簡潔建議(限300字內)。

{retrieved_text}

當前餐點:
- 餐次: {meal_type}
- 食物: {current_foods}
- 熱量: {current_calories} kcal

請簡潔回答,格式如下:

🔍 **分析** (50字內):
[今日攝取+歷史模式評估]

💡 **建議** (100字內,3點):
1. [具體改善建議]
2. [下一餐建議]
3. [注意事項]

🍎 **推薦** (100字內):
[3種適合食物+簡短理由]

繁體中文,總字數不超過300字。
"""
    
    # 無歷史記錄時的 Fallback Prompt
    NO_HISTORY_RECOMMENDATION = """
你是一位專業的營養師。用戶目前沒有飲食歷史記錄，但剛剛記錄了一餐。(限300字內)。

當前餐點:
- 餐次: {meal_type}
- 食物: {current_foods}
- 熱量: {current_calories} kcal

請簡潔回答,格式如下:

🔍 **分析** (50字內):
[這餐營養評估]

💡 **建議** (100字內,3點):
1. [飲食改善]
2. [營養均衡]
3. [注意事項]

🍎 **推薦** (100字內):
[3種適合食物+簡短理由]

繁體中文,總字數不超過300字。
"""
    
    # 基礎推薦 Prompt (MVP 版本)
    BASIC_RECOMMENDATION = """
你是一位專業的營養師，請根據用戶的飲食歷史提供健康建議。

飲食歷史資料：
{history_json}

統計資訊：
- 總餐數：{total_meals}
- 平均熱量：{avg_calories:.1f} kcal
- 最常吃的食物：{common_foods}

請提供結構化的分析和建議，格式如下：

🔍 **飲食分析**：
[分析用戶的飲食模式、熱量攝取、食物多樣性等 (100字內精簡回答)]

💡 **健康建議**：
[提供一個精簡的具體的改善建議]

🍎 **推薦食物**：
[推薦3-5種適合的食物，說明營養價值(100字內)]

⚠️ **注意事項**：
[提醒需要注意的飲食習慣]

請用繁體中文回答，建議要實用且易於執行。
"""
    
    # 進階分析 Prompt (未來版本)
    ADVANCED_ANALYSIS = """
你是一位資深營養師，具備豐富的臨床經驗。請深度分析用戶的飲食習慣。

用戶資料：
- 飲食記錄：{history_json}
- 統計資訊：{stats_json}
- 目標設定：{goals}  // 未來功能
- 健康狀況：{health_status}  // 未來功能

分析維度：
1. 熱量平衡 (TDEE vs 攝取量)
2. 營養素分布 (碳水/蛋白質/脂肪比例)
3. 微量營養素評估
4. 飲食頻率與時間模式
5. 食物多樣性指數

輸出格式：結構化JSON，包含分析結果、風險評估、具體建議。
"""
    
    # Fallback 規則模板
    SIMPLE_FALLBACK = """
基於您的飲食記錄分析：

🔍 **飲食分析**：
根據最近 {days} 天的 {total_meals} 餐記錄，您的平均每餐熱量為 {avg_calories:.1f} kcal。

💡 **健康建議**：
1. 保持飲食均衡，建議每餐包含蛋白質、碳水化合物和健康脂肪
2. 增加蔬菜和水果的攝取量，提供豐富的維生素和纖維
3. 控制每餐熱量在適當範圍內 (300-600 kcal)
4. 保持規律的用餐時間

🍎 **推薦食物**：
- 瘦肉類：雞胸肉、魚類 (提供優質蛋白質)
- 全穀類：糙米、燕麥 (提供複合碳水化合物)
- 蔬菜類：綠葉蔬菜、胡蘿蔔 (提供維生素和礦物質)

⚠️ **注意事項**：
請諮詢專業營養師獲得更個人化的建議。
"""


# ========== 核心推薦引擎 ==========

def get_recommendation(user_id: str, 
                      meal_type: str = 'meal',
                      current_foods: Optional[Dict[str, float]] = None,
                      current_calories: float = 0.0,
                      days: int = 7,
                      use_advanced: bool = False) -> str:
    """
    生成個人化飲食推薦 (RAG 增強版)
    
    基於用戶的飲食歷史和當前餐點，使用 RAG (Retrieval-Augmented Generation)
    方法檢索相關歷史記錄，結合 AI 分析生成更精準的個人化建議。
    
    Args:
        user_id: 用戶唯一識別碼
        meal_type: 當前餐次類型 (breakfast/lunch/dinner/snack/latenight/other)
        current_foods: 當前餐點的食物字典 {food_name: calories}
        current_calories: 當前餐點總熱量
        days: 分析最近幾天的資料，預設 7 天
        use_advanced: 是否使用進階分析模式 (未來功能)
    
    Returns:
        str: 結構化的飲食推薦文字
    
    Raises:
        ValueError: 參數驗證失敗
    
    工作流程 (RAG Pipeline):
        1. 檢索 (Retrieval): 從資料庫獲取相關歷史記錄
           - get_previous_meals: 今日前序餐點
           - get_past_days: 過去幾天的飲食統計
        2. 格式化 (Format): 將檢索結果格式化為結構化文本
        3. 增強 (Augmentation): 將歷史上下文與當前餐點合併到 prompt
        4. 生成 (Generation): 呼叫 Gemini API 生成推薦
        5. Fallback: 失敗時使用規則型推薦
    
    使用範例:
        recommendation = get_recommendation(
            user_id='user_123',
            meal_type='breakfast',
            current_foods={'蛋餅': 250.0, '豆漿': 150.0},
            current_calories=400.0,
            days=7
        )
        
    未來擴展 (註解):
        - 使用 sentence-transformers 生成歷史和 prompt 的向量嵌入
        - 計算 cosine 相似度，篩選最相關的歷史記錄
        - 添加 FAISS 向量索引加速檢索
        - 實現語義搜尋而非簡單的時間序列檢索
        
        示例代碼 (未來):
        ```python
        from sentence_transformers import SentenceTransformer
        import faiss
        
        # 生成查詢嵌入
        model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        query_text = f"{meal_type} {list(current_foods.keys())}"
        query_embedding = model.encode([query_text])[0]
        
        # 在向量索引中搜尋相似記錄
        D, I = index.search(query_embedding.reshape(1, -1), k=5)
        relevant_meals = [history[idx] for idx in I[0]]
        ```
    """
    # 參數驗證
    if not user_id:
        raise ValueError("user_id 不能為空")
    
    if days <= 0:
        raise ValueError("days 必須大於 0")
    
    # 預設值設定
    if current_foods is None:
        current_foods = {}
    
    try:
        logger.info(f"開始生成 RAG 推薦: user_id={user_id}, meal_type={meal_type}, calories={current_calories}")
        
        # ===== 步驟1: 檢索相關歷史記錄 (Retrieval) =====
        
        # 檢索今日前序餐點
        previous_meals = []
        try:
            # 驗證 meal_type，無效值轉換為 'other'
            valid_meal_types = {'breakfast', 'lunch', 'dinner', 'snack', 'latenight', 'other'}
            validated_meal_type = meal_type if meal_type in valid_meal_types else 'other'
            
            if validated_meal_type != meal_type:
                logger.info(f"meal_type '{meal_type}' 不在有效清單中，已轉換為 'other'")
            
            previous_meals = get_previous_meals(user_id, validated_meal_type)
            logger.debug(f"檢索到 {len(previous_meals)} 筆前序餐點")
        except ValueError as e:
            # 若仍然發生 ValueError，嘗試用 'other' 重試
            logger.warning(f"檢索前序餐點失敗 (meal_type={meal_type}): {e}，嘗試使用 'other' 重試")
            try:
                previous_meals = get_previous_meals(user_id, 'other')
                logger.debug(f"使用 'other' 重試成功，檢索到 {len(previous_meals)} 筆前序餐點")
            except Exception as retry_error:
                logger.error(f"使用 'other' 重試仍失敗: {retry_error}")
        except Exception as e:
            logger.warning(f"檢索前序餐點失敗: {e}")
        
        # 檢索過去幾天的統計分析
        past_analysis = None
        try:
            past_analysis = get_past_days(user_id, days=days)
            logger.debug(f"檢索到過去 {days} 天的分析資料")
        except Exception as e:
            logger.warning(f"檢索歷史統計失敗: {e}")
        
        # ===== 步驟2: 格式化檢索結果 (Format) =====
        
        retrieved_text = format_retrieved_text(
            previous_meals=previous_meals,
            past_analysis=past_analysis,
            days=days
        )
        
        logger.debug(f"格式化檢索文本長度: {len(retrieved_text)} 字元")
        
        # ===== 步驟3 & 4: 構建 Prompt 並生成推薦 (Augmentation & Generation) =====
        
        # 優先嘗試 Gemini API
        if gemini_client:
            try:
                recommendation = _generate_rag_recommendation(
                    retrieved_text=retrieved_text,
                    meal_type=meal_type,
                    current_foods=current_foods,
                    current_calories=current_calories,
                    has_history=(len(previous_meals) > 0 or past_analysis is not None)
                )
                logger.info("成功使用 Gemini RAG 生成推薦")
                return recommendation
                
            except Exception as e:
                logger.warning(f"Gemini API 呼叫失敗: {e}")
                # 繼續執行 fallback
        
        # ===== 步驟5: Fallback 到規則型推薦 =====
        
        logger.info("使用規則型 fallback 生成推薦")
        return _generate_rule_based_rag_recommendation(
            retrieved_text=retrieved_text,
            meal_type=meal_type,
            current_foods=current_foods,
            current_calories=current_calories
        )
        
    except Exception as e:
        error_msg = f"生成 RAG 推薦失敗: user_id={user_id}"
        handle_error(e, error_msg, logger=logger, raise_error=False)
        return _generate_error_fallback()


def _generate_rag_recommendation(retrieved_text: str,
                                meal_type: str,
                                current_foods: Dict[str, float],
                                current_calories: float,
                                has_history: bool = True) -> str:
    """
    使用 Gemini AI 生成 RAG 增強推薦
    
    將檢索到的歷史上下文與當前餐點資訊合併，
    構建結構化 prompt 並呼叫 Gemini API。
    
    Args:
        retrieved_text: 格式化的歷史檢索結果
        meal_type: 餐次類型
        current_foods: 當前食物字典
        current_calories: 當前總熱量
        has_history: 是否有歷史記錄
    
    Returns:
        str: AI 生成的推薦文字
    
    Raises:
        Exception: API 呼叫失敗或回應解析錯誤
    """
    # 格式化當前食物清單
    foods_str = ", ".join([f"{name}({cal:.1f} kcal)" for name, cal in current_foods.items()])
    
    # 餐次類型中文映射
    meal_type_zh = {
        'breakfast': '早餐',
        'lunch': '午餐',
        'dinner': '晚餐',
        'snack': '點心',
        'latenight': '宵夜',
        'other': '其他',
        'meal': '餐點'
    }.get(meal_type, meal_type)
    
    # 選擇 prompt 模板
    if has_history:
        prompt_template = PromptTemplates.RAG_RECOMMENDATION
        prompt = prompt_template.format(
            retrieved_text=retrieved_text,
            meal_type=meal_type_zh,
            current_foods=foods_str or "無",
            current_calories=current_calories
        )
    else:
        # 無歷史記錄時使用 fallback prompt
        prompt_template = PromptTemplates.NO_HISTORY_RECOMMENDATION
        prompt = prompt_template.format(
            meal_type=meal_type_zh,
            current_foods=foods_str or "無",
            current_calories=current_calories
        )
    
    logger.debug(f"構建的 RAG prompt 長度: {len(prompt)} 字元")
    
    # 呼叫 Gemini API
    try:
        response = gemini_client.generate_content(prompt)
        
        # 檢查回應
        if not response.text:
            raise ValueError("Gemini API 回傳空白回應")
        
        recommendation = response.text.strip()
        
        # 驗證回應品質
        if len(recommendation) < 50:
            raise ValueError("Gemini API 回應過短，可能品質不佳")
        
        logger.debug(f"Gemini API 回應長度: {len(recommendation)} 字元")
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Gemini API 處理失敗: {e}")
        raise


def _format_history_for_prompt(history: List[Tuple]) -> Dict[str, Any]:
    """
    格式化飲食歷史資料用於 prompt 構建
    
    將資料庫回傳的原始資料轉換為結構化 JSON 格式，
    便於 LLM 理解和分析。
    
    Args:
        history: 從 get_history 回傳的記錄列表
    
    Returns:
        Dict: 結構化的歷史資料
    
    資料格式:
        {
            "meals": [
                {
                    "date": "2024-11-06",
                    "time": "12:30",
                    "foods": {"apple": 52.0, "banana": 89.0},
                    "total_calories": 141.0
                }
            ],
            "date_range": "2024-10-30 to 2024-11-06",
            "total_records": 7
        }
    """
    meals = []
    
    for record in history:
        record_id, date_str, foods, calories, created_at = record
        
        # 解析日期
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            date_part = date_obj.strftime("%Y-%m-%d")
            time_part = date_obj.strftime("%H:%M")
        except:
            date_part = date_str.split('T')[0] if 'T' in date_str else date_str
            time_part = "未知"
        
        meal_data = {
            "date": date_part,
            "time": time_part,
            "foods": foods,
            "total_calories": calories
        }
        meals.append(meal_data)
    
    # 計算日期範圍
    if meals:
        dates = [meal["date"] for meal in meals]
        date_range = f"{min(dates)} 到 {max(dates)}"
    else:
        date_range = "無資料"
    
    return {
        "meals": meals,
        "date_range": date_range,
        "total_records": len(meals)
    }


def _generate_ai_recommendation(history_data: Dict[str, Any], 
                              stats: Dict[str, Any],
                              use_advanced: bool = False) -> str:
    """
    使用 Gemini AI 生成推薦
    
    構建結構化 prompt 並呼叫 Gemini API 生成個人化建議。
    
    Args:
        history_data: 格式化的飲食歷史資料
        stats: 統計資訊
        use_advanced: 是否使用進階分析模式
    
    Returns:
        str: AI 生成的推薦文字
    
    Raises:
        Exception: API 呼叫失敗或回應解析錯誤
    """
    # 準備 prompt 資料
    history_json = json.dumps(history_data, ensure_ascii=False, indent=2)
    
    # 格式化常見食物清單
    common_foods_str = ", ".join([
        f"{food}({count}次)" 
        for food, count in stats.get('most_common_foods', [])[:5]
    ])
    
    # 選擇 prompt 模板
    if use_advanced:
        # 未來功能：進階分析
        prompt_template = PromptTemplates.ADVANCED_ANALYSIS
        stats_json = json.dumps(stats, ensure_ascii=False, indent=2)
        prompt = prompt_template.format(
            history_json=history_json,
            stats_json=stats_json,
            goals="維持健康",  # 預設值
            health_status="一般"  # 預設值
        )
    else:
        # MVP 版本：基礎推薦
        prompt_template = PromptTemplates.BASIC_RECOMMENDATION
        prompt = prompt_template.format(
            history_json=history_json,
            total_meals=stats.get('total_meals', 0),
            avg_calories=stats.get('avg_calories', 0),
            common_foods=common_foods_str or "無資料"
        )
    
    logger.debug("構建的 prompt 長度: %d 字元", len(prompt))
    
    # 呼叫 Gemini API
    try:
        response = gemini_client.generate_content(prompt)
        
        # 檢查回應
        if not response.text:
            raise ValueError("Gemini API 回傳空白回應")
        
        recommendation = response.text.strip()
        
        # 驗證回應品質
        if len(recommendation) < 50:
            raise ValueError("Gemini API 回應過短，可能品質不佳")
        
        logger.debug("Gemini API 回應長度: %d 字元", len(recommendation))
        
        return recommendation
        
    except Exception as e:
        logger.error(f"Gemini API 處理失敗: {e}")
        raise


def _generate_rule_based_rag_recommendation(retrieved_text: str,
                                           meal_type: str,
                                           current_foods: Dict[str, float],
                                           current_calories: float) -> str:
    """
    生成規則型 RAG 推薦 (Fallback 機制)
    
    當 AI API 不可用時，使用預定義規則結合檢索結果生成推薦。
    
    Args:
        retrieved_text: 格式化的歷史檢索結果
        meal_type: 餐次類型
        current_foods: 當前食物字典
        current_calories: 當前總熱量
    
    Returns:
        str: 規則型推薦文字
    """
    # 餐次類型中文映射
    meal_type_zh = {
        'breakfast': '早餐',
        'lunch': '午餐',
        'dinner': '晚餐',
        'snack': '點心',
        'latenight': '宵夜',
        'other': '其他',
        'meal': '餐點'
    }.get(meal_type, meal_type)
    
    # 格式化當前食物
    foods_str = ", ".join([f"{name}({cal:.1f} kcal)" for name, cal in current_foods.items()])
    
    # 構建基礎推薦
    recommendation = f"""
🔍 **飲食分析**：

當前餐點：{meal_type_zh}
食物：{foods_str or "無"}
總熱量：{current_calories:.1f} kcal

{retrieved_text}

💡 **健康建議**：
"""
    
    # 基於當前熱量的建議
    if current_calories > 600:
        recommendation += "1. 這餐熱量較高，下一餐建議選擇較清淡的食物\n"
    elif current_calories < 200:
        recommendation += "1. 這餐熱量較低，下一餐可適量增加營養\n"
    else:
        recommendation += "1. 這餐熱量適中，繼續保持均衡飲食\n"
    
    # 基於餐次類型的建議
    if meal_type == 'breakfast':
        recommendation += "2. 早餐要吃好，建議包含蛋白質和碳水化合物\n"
        recommendation += "3. 午餐可以增加蔬菜和優質蛋白質\n"
    elif meal_type == 'lunch':
        recommendation += "2. 午餐已用完，晚餐建議清淡一些\n"
        recommendation += "3. 晚餐可以選擇魚類或雞肉配蔬菜\n"
    elif meal_type == 'dinner':
        recommendation += "2. 晚餐不宜過飽，建議在睡前3小時用餐\n"
        recommendation += "3. 明日早餐建議營養豐富，開啟美好一天\n"
    else:
        recommendation += "2. 保持規律的用餐時間\n"
        recommendation += "3. 注意三餐均衡，避免暴飲暴食\n"
    
    # 添加一般建議
    recommendation += """
🍎 **推薦食物**：
- 蔬菜類：花椰菜、菠菜、番茄（提供維生素和纖維）
- 蛋白質：雞胸肉、魚類、豆腐（提供優質蛋白）
- 碳水化合物：糙米、地瓜、燕麥（提供持久能量）

⚠️ **注意事項**：
- 多喝水，保持每日 2000ml 以上
- 減少高糖、高鹽、高油食物
- 保持規律運動習慣
"""
    
    return recommendation
    """
    生成規則型推薦 (Fallback 機制)
    
    當 AI API 不可用時，使用預定義規則生成基礎推薦。
    確保系統在任何情況下都能提供有用的建議。
    
    Args:
        history_data: 格式化的飲食歷史資料
        stats: 統計資訊
        days: 分析天數
    
    Returns:
        str: 規則型推薦文字
    
    規則設計：
    1. 熱量分析：過高/過低/適中
    2. 飲食頻率：規律性評估
    3. 食物多樣性：重複性檢查
    4. 營養均衡：基本建議
    """
    total_meals = stats.get('total_meals', 0)
    avg_calories = stats.get('avg_calories', 0)
    common_foods = stats.get('most_common_foods', [])
    
    # 格式化常見食物
    common_foods_str = ", ".join([
        food for food, _ in common_foods[:3]
    ]) if common_foods else "資料不足"
    
    # 使用 fallback 模板
    recommendation = PromptTemplates.SIMPLE_FALLBACK.format(
        days=days,
        total_meals=total_meals,
        avg_calories=avg_calories
    )
    
    # 添加個人化分析
    analysis_notes = []
    
    # 熱量分析
    if avg_calories > 600:
        analysis_notes.append("您的平均熱量偏高，建議適量減少高熱量食物")
    elif avg_calories < 300:
        analysis_notes.append("您的平均熱量偏低，建議增加營養豐富的食物")
    else:
        analysis_notes.append("您的熱量攝取在合理範圍內")
    
    # 飲食頻率分析
    meals_per_day = total_meals / days if days > 0 else 0
    if meals_per_day < 2:
        analysis_notes.append("建議增加用餐頻率，保持規律飲食")
    elif meals_per_day > 5:
        analysis_notes.append("用餐頻率較高，注意控制每餐份量")
    
    # 食物多樣性分析
    unique_foods = len(set([food for food, _ in common_foods]))
    if unique_foods < 5:
        analysis_notes.append("建議增加食物種類，提升營養多樣性")
    
    # 最常吃的食物分析
    if common_foods:
        top_food = common_foods[0][0]
        analysis_notes.append(f"您最常吃 {top_food}，建議搭配其他食物平衡營養")
    
    # 添加個人化分析到推薦中
    if analysis_notes:
        recommendation += "\n\n📋 **個人化分析**：\n"
        for i, note in enumerate(analysis_notes, 1):
            recommendation += f"{i}. {note}\n"
    
    return recommendation


def _generate_no_history_message() -> str:
    """生成無歷史記錄時的訊息"""
    return """
🔍 **飲食分析**：
目前沒有飲食記錄可供分析。

💡 **開始建議**：
1. 開始記錄您的每餐飲食
2. 上傳食物圖片讓系統識別
3. 累積一週資料後獲得個人化推薦

🍎 **一般健康建議**：
- 均衡攝取蛋白質、碳水化合物和健康脂肪
- 每日攝取 5 份蔬菜水果
- 保持規律的用餐時間
- 適量飲水 (每日 2000ml 以上)

⚠️ **提醒**：
開始記錄飲食，讓我們為您提供更精準的建議！
"""


def _generate_error_fallback() -> str:
    """生成系統錯誤時的備用訊息"""
    return """
⚠️ **系統提醒**：
推薦系統暫時無法使用，請稍後再試。

💡 **基本健康建議**：
1. 保持飲食均衡，每餐包含蛋白質和蔬菜
2. 控制份量，避免暴飲暴食
3. 選擇原型食物，減少加工食品
4. 保持規律運動習慣

如需專業建議，請諮詢營養師或醫療專家。
"""


# ========== 輔助分析功能 ==========

def analyze_nutrition_trends(user_id: str, days: int = 30) -> Dict[str, Any]:
    """
    分析營養趨勢 (未來功能)
    
    進行深度的營養學分析，包括：
    - 熱量趨勢變化
    - 營養素平衡
    - 飲食規律性
    - 改善建議優先級
    
    Args:
        user_id: 用戶ID
        days: 分析期間
    
    Returns:
        Dict: 詳細的趨勢分析報告
    """
    # TODO: 實現營養趨勢分析
    # 1. 獲取長期歷史資料
    # 2. 計算營養素分布
    # 3. 分析時間序列趨勢
    # 4. 識別改善機會
    
    return {
        "status": "功能開發中",
        "description": "未來將提供深度營養趨勢分析"
    }


def generate_meal_suggestions(dietary_preferences: Dict[str, Any]) -> List[str]:
    """
    生成餐點建議 (未來功能)
    
    基於用戶偏好和營養需求，生成具體的餐點建議。
    
    Args:
        dietary_preferences: 用戶飲食偏好設定
    
    Returns:
        List[str]: 推薦餐點清單
    """
    # TODO: 實現智能餐點建議
    # 1. 分析用戶偏好
    # 2. 考慮營養需求
    # 3. 整合季節性食材
    # 4. 生成具體食譜
    
    return [
        "功能開發中：未來將提供個人化餐點建議",
        "將整合食譜資料庫和營養計算",
        "支援各種飲食限制和偏好"
    ]


# ========== 模組測試 ==========

if __name__ == "__main__":
    """
    模組測試程式
    
    運行方式：
        python src/recommendation_engine.py
    """
    # 設定日誌
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("=" * 60)
    logger.info("AI 推薦引擎測試")
    logger.info("=" * 60)
    
    # 測試用戶 ID
    test_user_id = "test_user_123"
    
    try:
        # 測試推薦生成
        logger.info("\n🧠 測試 AI 推薦生成...")
        
        recommendation = get_recommendation(test_user_id, days=7)
        
        logger.info("✅ 推薦生成成功")
        print("\n" + "=" * 50)
        print("📋 推薦結果：")
        print("=" * 50)
        print(recommendation)
        print("=" * 50)
        
        # 測試系統狀態
        logger.info(f"\n🔧 系統狀態檢查:")
        logger.info(f"  Gemini SDK 可用: {GEMINI_AVAILABLE}")
        logger.info(f"  API 金鑰設定: {'是' if GEMINI_API_KEY else '否'}")
        logger.info(f"  客戶端初始化: {'成功' if gemini_client else '失敗'}")
        
    except Exception as e:
        logger.error(f"測試失敗: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("測試完成！")
    logger.info("=" * 60)