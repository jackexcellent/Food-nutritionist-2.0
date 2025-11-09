#!/usr/bin/env python3
"""
Diet Tracker Discord Bot - Discord 機器人模組
============================================

這個模組實現了 Discord 機器人的核心功能，整合所有系統組件
提供用戶友好的界面來追蹤飲食、查看歷史和獲得AI推薦。

主要功能：
1. /analyze 命令 - 食物圖片識別和營養分析 (MVP)
2. /history 命令 - 查看飲食歷史記錄
3. 未來擴展：/stats, /recommend 等命令

設計原則：
- 模組化設計，易於添加新命令
- 完善的錯誤處理和用戶反饋
- 整合所有現有系統組件
- 支援未來功能擴展

作者: GitHub Copilot
日期: 2024-11-07
"""

import os
import asyncio
import tempfile
import logging
from io import BytesIO
from datetime import datetime
from typing import Optional, List, Dict, Any

import discord
from discord.ext import commands
from dotenv import load_dotenv

# 導入專案模組
import utils
import image_processor
import nutrition_calculator
import data_storage
import recommendation_engine

# 載入環境變數
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# 設定日誌
logger = logging.getLogger(__name__)

# Bot 配置
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DEFAULT_INTENTS = discord.Intents.default()
DEFAULT_INTENTS.message_content = True  # 需要讀取訊息內容

class DietTrackerBot(commands.Bot):
    """
    飲食追蹤 Discord 機器人主類別
    
    這個類別繼承自 discord.py 的 Bot，並添加了
    飲食追蹤相關的功能和狀態管理。
    """
    
    def __init__(self):
        """初始化機器人"""
        super().__init__(
            command_prefix='!',  # 保留前綴命令作為備用
            intents=DEFAULT_INTENTS,
            help_command=None  # 自定義幫助命令
        )
        
        # 初始化統計數據
        self.stats = {
            'total_tracks': 0,
            'successful_analyses': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # 加載所有命令
        self._setup_commands()
        
        logger.info("飲食追蹤機器人已初始化")
    
    def _setup_commands(self):
        """設定所有機器人命令"""
        # 這個方法在未來可以用來批量註冊命令
        pass
    
    async def on_ready(self):
        """機器人準備就緒時的回調"""
        logger.info(f'✅ 機器人已上線: {self.user} (ID: {self.user.id})')
        logger.info(f'🔗 連接到 {len(self.guilds)} 個伺服器')
        
        # 同步斜槓命令到 Discord
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ 已同步 {len(synced)} 個斜槓命令")
        except Exception as e:
            logger.error(f"❌ 同步斜槓命令失敗: {e}")
        
        # 設定機器人狀態
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="你的飲食健康 | /analyze 開始分析"
            )
        )
    
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """全域錯誤處理"""
        self.stats['errors'] += 1
        
        # 記錄詳細錯誤 (不重新拋出異常)
        try:
            utils.handle_error(error, "Discord命令錯誤", logger=logger, raise_error=False)
        except:
            # 如果 utils.handle_error 有問題，直接記錄
            logger.error(f"Discord命令錯誤: {str(error)}")
        
        # 向用戶發送友好的錯誤訊息
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("❓ 找不到該命令。使用 `!help` 查看可用命令。")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("⚠️ 缺少必要參數。請檢查命令格式。")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("⚠️ 參數格式錯誤。請檢查命令格式。")
        else:
            await ctx.send(f"❌ 發生錯誤：{str(error)}")
        
        logger.error(f"命令錯誤 - 用戶: {ctx.author.id}, 命令: {ctx.command}, 錯誤: {error}")


# 建立機器人實例
bot = DietTrackerBot()


@bot.tree.command(name='analyze', description='上傳食物圖片進行營養分析和追蹤')
async def analyze_food(interaction: discord.Interaction, 圖片: discord.Attachment):
    """
    /analyze 斜槓命令 - MVP 核心功能（含餐次詢問）
    
    處理用戶上傳的食物圖片，進行以下流程：
    1. 檢查附件 (圖片)
    2. 食物識別 (image_processor)
    3. 📋 詢問餐次類型 (breakfast/lunch/dinner/snack)
    4. 🔍 VLM 識別份量 (克)
    5. 營養分析 (nutrition_calculator，依份量調整)
    6. 儲存記錄 (data_storage，包含餐次和份量)
    7. AI 推薦 (recommendation_engine)
    8. 回傳結構化結果
    
    Args:
        interaction: Discord 斜槓命令互動
        圖片: 用戶上傳的食物圖片
        
    未來擴展：
        - 🤖 使用 datetime.now().hour 自動推斷餐次
          (<12: breakfast, 12-17: lunch, 17-21: dinner, else: snack)
        - 🎯 學習用戶的用餐習慣自動建議餐次
        - 📊 提供餐次統計和建議
    """
    try:
        bot.stats['total_tracks'] += 1
        user_id = str(interaction.user.id)
        
        # 檢查圖片參數
        if not 圖片:
            await interaction.response.send_message(
                "❌ **請提供食物圖片進行分析！**\n\n"
                "使用方式：\n"
                "1. 輸入 `/analyze`\n"
                "2. 在 `圖片` 參數中上傳食物圖片\n"
                "3. 回答餐次問題（早餐/午餐/晚餐/點心）\n"
                "4. 等待 AI 分析結果\n\n"
                "💡 支援 JPG, PNG 等常見格式",
                ephemeral=True
            )
            return
        
        # 發送處理中訊息
        await interaction.response.send_message("🔄 **正在分析您的食物圖片...**\n請稍候，這可能需要幾秒鐘時間。")
        
        # 使用傳入的圖片附件
        attachment = 圖片
        
        # 驗證檔案類型
        if not _is_valid_image_file(attachment.filename):
            await interaction.edit_original_response(content="❌ 請上傳有效的圖片檔案 (jpg, jpeg, png, webp)")
            return
        
        # 驗證檔案大小 (10MB限制)
        max_size = int(os.getenv('MAX_IMAGE_SIZE_MB', 10)) * 1024 * 1024
        if attachment.size > max_size:
            await interaction.edit_original_response(content=f"❌ 圖片太大，請上傳小於 {max_size//1024//1024}MB 的圖片")
            return
        
        # 下載並儲存到臨時檔案
        image_data = await attachment.read()
        temp_path = None
        
        try:
            # 建立臨時檔案
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            # 步驟 1: 食物識別
            await interaction.edit_original_response(content="🔄 **步驟 1/6: 識別食物中...**")
            foods = image_processor.process_image(temp_path)
            
            if not foods:
                await interaction.edit_original_response(
                    content="❓ **無法識別圖片中的食物**\n\n"
                           "請嘗試：\n"
                           "• 確保圖片清晰\n"
                           "• 食物佔據畫面主體\n"
                           "• 光線充足\n"
                           "• 或手動輸入食物名稱"
                )
                return
            
            # 步驟 2: 詢問餐次類型
            await interaction.edit_original_response(
                content="🔄 **步驟 2/6: 食物識別完成！**\n\n"
                       f"✅ 識別到的食物: {', '.join(foods)}\n\n"
                       "📋 **請問這是什麼餐次？**\n"
                       "請回覆：`早餐`、`午餐`、`晚餐` 或 `點心`"
            )
            
            # 等待用戶回應（MVP：手動詢問，未來可自動推斷）
            meal_type = await _ask_meal_type(interaction, user_id)
            
            # 取得 view 中儲存的自定義餐次名稱
            custom_meal_name = None
            if hasattr(bot, '_last_meal_view') and bot._last_meal_view:
                custom_meal_name = bot._last_meal_view.custom_meal
            
            if not meal_type:
                # 用戶未回應或超時，使用預設值
                meal_type = 'meal'
                await interaction.followup.send(
                    "⏰ **未收到回應，使用預設餐次類型**",
                    ephemeral=True
                )
            
            # 步驟 3: VLM 識別份量
            await interaction.edit_original_response(
                content=f"🔄 **步驟 3/6: 正在分析食物份量...**\n\n"
                       f"識別的食物: {', '.join(foods)}\n"
                       f"餐次類型: {_format_meal_type_chinese(meal_type)}"
            )
            
            # TODO: 使用 VLM 識別份量（暫時使用預設值）
            # 未來擴展：整合 VLM API 進行視覺份量估計
            portion_size = await _estimate_portion_from_image(temp_path, foods)
            
            # 步驟 4: 營養分析（依份量調整）
            await interaction.edit_original_response(
                content=f"🔄 **步驟 4/6: 計算營養成分...**\n\n"
                       f"識別的食物: {', '.join(foods)}\n"
                       f"餐次類型: {_format_meal_type_chinese(meal_type)}\n"
                       f"估計份量: {portion_size:.0f}g"
            )
            
            nutrition_result = nutrition_calculator.get_nutrition(foods)
            
            if not nutrition_result or len(nutrition_result) != 2:
                await interaction.edit_original_response(content="❌ 無法取得營養資訊，請稍後再試")
                return
            
            # 解包返回值: (營養字典, 總熱量)
            nutrition_data, total_calories = nutrition_result
            
            # 檢查是否有任何食物找到熱量資訊
            if not nutrition_data or total_calories == 0:
                # 沒有任何食物有熱量資訊
                food_list_text = ', '.join(foods)
                await interaction.edit_original_response(
                    content=f"❌ **無法獲取熱量資訊**\n\n"
                           f"識別的食物: {food_list_text}\n\n"
                           f"這些食物在資料庫（TFND、USDA）和AI估算中都找不到熱量資訊。\n"
                           f"請嘗試：\n"
                           f"• 使用更具體的食物名稱\n"
                           f"• 拍攝更清晰的照片\n"
                           f"• 確保照片中食物清晰可見"
                )
                return
            
            # 根據份量調整營養數據（預設為100g基準）
            portion_factor = portion_size / 100.0
            adjusted_nutrition_data = {
                food: calories * portion_factor 
                for food, calories in nutrition_data.items()
            }
            adjusted_total_calories = total_calories * portion_factor
            
            # 步驟 5: 儲存記錄（包含餐次和份量）
            await interaction.edit_original_response(
                content=f"🔄 **步驟 5/6: 儲存飲食記錄...**\n\n"
                       f"餐次: {_format_meal_type_chinese(meal_type)}\n"
                       f"份量: {portion_size:.0f}g\n"
                       f"熱量: {adjusted_total_calories:.0f} kcal"
            )
            
            meal_id = data_storage.store_meal(
                user_id=user_id,
                foods=adjusted_nutrition_data,
                calories=adjusted_total_calories,
                meal_type=meal_type,
                meal_type_custom=custom_meal_name,
                portion_size=portion_size
            )
            
            # 步驟 6: 產生 AI 推薦
            await interaction.edit_original_response(
                content="🔄 **步驟 6/6: 生成個人化建議...**"
            )
            recommendation = recommendation_engine.get_recommendation(user_id, days=7)
            
            # 建構回應訊息 (包含圖片、餐次和份量資訊)
            embed_response = _format_track_response(
                foods=foods,
                nutrition_data=adjusted_nutrition_data,
                total_calories=adjusted_total_calories,
                recommendation=recommendation,
                meal_id=meal_id,
                image_url=attachment.url,
                meal_type=meal_type,
                portion_size=portion_size
            )
            
            # 發送最終結果
            await interaction.edit_original_response(content=None, embed=embed_response)
            
            # 更新統計
            bot.stats['successful_analyses'] += 1
            
            logger.info(
                f"成功處理追蹤請求 - 用戶: {user_id}, 食物: {foods}, "
                f"餐次: {meal_type}, 份量: {portion_size}g, 熱量: {adjusted_total_calories:.0f}"
            )
            
        finally:
            # 清理臨時檔案
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"無法刪除臨時檔案 {temp_path}: {e}")
    
    except Exception as e:
        bot.stats['errors'] += 1
        
        try:
            utils.handle_error(e, "Discord track命令錯誤", logger=logger, raise_error=False)
        except:
            logger.error(f"Track命令錯誤: {str(e)}")
        
        try:
            await interaction.edit_original_response(
                content="❌ **處理過程中發生錯誤**\n"
                       "請稍後再試，或聯繫管理員。"
            )
        except:
            try:
                await interaction.followup.send("❌ 處理過程中發生錯誤，請稍後再試。")
            except:
                pass  # 如果連 followup 也失敗，就靜默處理
        
        logger.error(f"Track命令錯誤 - 用戶: {interaction.user.id}, 錯誤: {str(e)}")


@bot.tree.command(name='help', description='顯示機器人說明和可用命令')
async def help_command(interaction: discord.Interaction):
    """自訂幫助斜槓命令"""
    embed = discord.Embed(
        title="🤖 飲食追蹤機器人說明",
        description="透過 AI 技術追蹤您的飲食並獲得個人化建議",
        color=0x00ff00
    )
    
    embed.add_field(
        name="📷 /analyze",
        value="上傳食物圖片進行分析\n• 自動識別食物\n• 計算營養成分\n• 儲存飲食記錄\n• 生成個人化建議",
        inline=False
    )
    
    embed.add_field(
        name="📋 /history",
        value="查看飲食歷史記錄\n• 顯示最近的用餐記錄\n• 營養攝取統計\n• 可指定查看天數（預設7天）",
        inline=False
    )
    
    embed.add_field(
        name="🤖 /recommend",
        value="獲得個人化飲食建議\n• 基於歷史記錄的 RAG 推薦\n• 分析飲食習慣和趨勢\n• 提供具體的飲食改善建議\n• 可指定目標餐次和分析天數",
        inline=False
    )
    
    embed.add_field(
        name="🤖 其他命令",
        value="• `/hello` - 打招呼互動\n• `/help` - 顯示此說明",
        inline=False
    )

    
    embed.set_footer(text="💡 小提示：上傳清晰的食物圖片可獲得更準確的分析結果")
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name='stats', description='顯示機器人使用統計 (管理員限定)')
async def bot_stats(interaction: discord.Interaction):
    """機器人統計資訊 (管理員功能)"""
    if not await _is_admin_or_owner_interaction(interaction):
        await interaction.response.send_message("❌ 此命令僅限管理員使用", ephemeral=True)
        return
    
    uptime = datetime.now() - bot.stats['start_time']
    
    embed = discord.Embed(
        title="📊 機器人統計資訊",
        color=0x3498db
    )
    
    embed.add_field(name="🕐 運行時間", value=str(uptime).split('.')[0], inline=True)
    embed.add_field(name="📈 總追蹤次數", value=bot.stats['total_tracks'], inline=True)
    embed.add_field(name="✅ 成功分析", value=bot.stats['successful_analyses'], inline=True)
    embed.add_field(name="❌ 錯誤次數", value=bot.stats['errors'], inline=True)
    embed.add_field(name="🏠 伺服器數量", value=len(bot.guilds), inline=True)
    embed.add_field(name="👥 用戶數量", value=len(bot.users), inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ==================== 輔助函數 ====================

def _is_valid_image_file(filename: str) -> bool:
    """檢查檔案是否為有效的圖片格式"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    return any(filename.lower().endswith(ext) for ext in valid_extensions)


class MealTypeView(discord.ui.View):
    """餐次選擇按鈕視圖"""
    
    def __init__(self):
        super().__init__(timeout=60.0)
        self.meal_type = None
        self.custom_meal = None
    
    @discord.ui.button(label="🌅 早餐", style=discord.ButtonStyle.primary)
    async def breakfast_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.meal_type = 'breakfast'
        await interaction.response.edit_message(content="✅ 已選擇：**早餐**", view=None)
        self.stop()
    
    @discord.ui.button(label="🌞 午餐", style=discord.ButtonStyle.primary)
    async def lunch_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.meal_type = 'lunch'
        await interaction.response.edit_message(content="✅ 已選擇：**午餐**", view=None)
        self.stop()
    
    @discord.ui.button(label="🌙 晚餐", style=discord.ButtonStyle.primary)
    async def dinner_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.meal_type = 'dinner'
        await interaction.response.edit_message(content="✅ 已選擇：**晚餐**", view=None)
        self.stop()
    
    @discord.ui.button(label="🍿 點心", style=discord.ButtonStyle.secondary)
    async def snack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.meal_type = 'snack'
        await interaction.response.edit_message(content="✅ 已選擇：**點心**", view=None)
        self.stop()
    
    @discord.ui.button(label="🌃 宵夜", style=discord.ButtonStyle.secondary)
    async def latenight_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.meal_type = 'latenight'
        await interaction.response.edit_message(content="✅ 已選擇：**宵夜**", view=None)
        self.stop()
    
    @discord.ui.button(label="✏️ 其他", style=discord.ButtonStyle.success, row=1)
    async def other_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 顯示模態框讓用戶輸入自定義餐次
        modal = CustomMealModal()
        await interaction.response.send_modal(modal)
        await modal.wait()
        
        if modal.custom_meal:
            self.meal_type = 'other'
            self.custom_meal = modal.custom_meal
            # 編輯原始訊息以移除按鈕
            await interaction.edit_original_response(
                content=f"✅ 已選擇：**{self.custom_meal}**", 
                view=None
            )
        else:
            self.meal_type = 'meal'
            await interaction.edit_original_response(
                content="✅ 已選擇：**一般餐點**", 
                view=None
            )
        
        self.stop()


class CustomMealModal(discord.ui.Modal, title="自定義餐次"):
    """自定義餐次輸入模態框"""
    
    meal_name = discord.ui.TextInput(
        label="請輸入餐次名稱",
        placeholder="例如：下午茶、早午餐、運動後補充等",
        required=True,
        max_length=20
    )
    
    def __init__(self):
        super().__init__()
        self.custom_meal = None
    
    async def on_submit(self, interaction: discord.Interaction):
        self.custom_meal = self.meal_name.value
        await interaction.response.send_message(
            f"✅ 已選擇：**{self.custom_meal}**", 
            ephemeral=True
        )


async def _ask_meal_type(interaction: discord.Interaction, user_id: str) -> Optional[str]:
    """
    詢問用戶餐次類型（使用按鈕選單）
    
    Args:
        interaction: Discord interaction 物件
        user_id: 用戶 ID
    
    Returns:
        餐次類型 ('breakfast', 'lunch', 'dinner', 'snack', 'latenight', 'other') 或 'meal'
    """
    try:
        # 創建按鈕視圖
        view = MealTypeView()
        
        # 儲存到 bot 以便後續取得自定義餐次名稱
        bot._last_meal_view = view
        
        # 發送選擇訊息
        await interaction.followup.send(
            "🍽️ **請選擇餐次類型**\n"
            "請點擊下方按鈕選擇，或點選「其他」自行輸入",
            view=view,
            ephemeral=False
        )
        
        # 等待用戶選擇
        await view.wait()
        
        # 返回選擇結果
        if view.meal_type:
            return view.meal_type
        else:
            logger.warning(f"用戶 {user_id} 未選擇餐次類型（超時）")
            return 'meal'  # 超時使用預設值
            
    except Exception as e:
        utils.handle_error(e, "詢問餐次類型錯誤", logger=logger, raise_error=False)
        return 'meal'


def _parse_meal_type_input(content: str) -> Optional[str]:
    """
    解析用戶輸入的餐次類型
    
    Args:
        content: 用戶輸入的文字（已轉小寫）
    
    Returns:
        標準化的餐次類型或 None
    """
    # 早餐關鍵字
    if any(keyword in content for keyword in ['早', 'breakfast', '早餐', 'morning']):
        return 'breakfast'
    
    # 午餐關鍵字
    if any(keyword in content for keyword in ['午', 'lunch', '午餐', '中餐', 'noon']):
        return 'lunch'
    
    # 晚餐關鍵字
    if any(keyword in content for keyword in ['晚', 'dinner', '晚餐', 'evening', 'supper']):
        return 'dinner'
    
    # 點心關鍵字
    if any(keyword in content for keyword in ['點', 'snack', '點心', '零食', '宵夜']):
        return 'snack'
    
    return None


def _parse_meal_type_from_chinese(meal_input: str) -> str:
    """
    從中文輸入解析餐次類型 (用於 /recommend 命令)
    
    Args:
        meal_input: 用戶輸入的餐次文字
    
    Returns:
        標準化的餐次類型
    """
    if not meal_input:
        return 'meal'
    
    meal_input_lower = meal_input.lower().strip()
    
    # 使用現有的解析函數
    parsed = _parse_meal_type_input(meal_input_lower)
    
    return parsed if parsed else 'meal'


def _parse_recommendation_sections(recommendation: str) -> Dict[str, str]:
    """
    解析推薦內容為不同區段
    
    Args:
        recommendation: 完整的推薦內容
    
    Returns:
        包含各區段的字典 {'analysis': str, 'suggestions': str, 'foods': str, 'warnings': str}
    """
    sections = {
        'analysis': '',
        'suggestions': '',
        'foods': '',
        'warnings': ''
    }
    
    if not recommendation:
        return sections
    
    lines = recommendation.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # 識別區段標題
        if '飲食分析' in line or '🔍' in line:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'analysis'
            current_content = []
        elif '健康建議' in line or '💡' in line:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'suggestions'
            current_content = []
        elif '推薦食物' in line or '🍎' in line:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'foods'
            current_content = []
        elif '注意事項' in line or '⚠️' in line:
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content)
            current_section = 'warnings'
            current_content = []
        elif line and current_section:
            # 添加內容到當前區段
            current_content.append(line)
    
    # 保存最後一個區段
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content)
    
    return sections


def _split_recommendation_text(text: str, max_length: int = 1024) -> List[str]:
    """
    將長文本分割為多個區段以符合 Discord Embed 限制
    
    Args:
        text: 要分割的文字
        max_length: 每個區段的最大長度
    
    Returns:
        分割後的文字列表
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def _extract_action_items(recommendation: str) -> str:
    """
    從推薦中提取行動項目
    
    Args:
        recommendation: 推薦內容
    
    Returns:
        格式化的行動項目文字
    """
    if not recommendation:
        return ""
    
    action_keywords = ['建議', '應該', '可以', '試試', '嘗試', '多吃', '少吃', '避免', '增加', '減少']
    action_items = []
    
    lines = recommendation.split('\n')
    
    for line in lines:
        line = line.strip()
        # 尋找包含行動關鍵字的行
        if any(keyword in line for keyword in action_keywords):
            # 清理行號和項目符號
            clean_line = line.lstrip('0123456789.-•*# ').strip()
            if clean_line and len(clean_line) > 10:  # 過濾太短的行
                # 如果還沒有項目符號,添加一個
                if not clean_line.startswith(('•', '-', '*')):
                    clean_line = f"• {clean_line}"
                
                if clean_line not in action_items and len(action_items) < 5:  # 最多5項
                    action_items.append(clean_line)
    
    return '\n'.join(action_items) if action_items else ""


def _format_meal_type_chinese(meal_type: str, custom_name: str = None) -> str:
    """
    將餐次類型轉換為中文顯示
    
    Args:
        meal_type: 餐次類型
        custom_name: 自定義餐次名稱（如果 meal_type 為 'other'）
    
    Returns:
        中文餐次名稱
    """
    if meal_type == 'other' and custom_name:
        return f'✏️ {custom_name}'
    
    meal_type_map = {
        'breakfast': '🌅 早餐',
        'lunch': '🌞 午餐',
        'dinner': '🌙 晚餐',
        'snack': '🍿 點心',
        'latenight': '🌃 宵夜',
        'meal': '🍽️ 餐點'
    }
    return meal_type_map.get(meal_type, '🍽️ 餐點')


async def _estimate_portion_from_image(image_path: str, foods: List[str]) -> float:
    """
    從圖片估計食物份量
    
    MVP 版本：使用預設值 100g
    未來擴展：整合 VLM (Vision Language Model) API 進行視覺份量估計
    
    Args:
        image_path: 圖片檔案路徑
        foods: 識別到的食物列表
    
    Returns:
        估計的份量（克）
        
    未來 VLM 整合範例 (註解保留):
        # 1. 使用 GPT-4V 或 Claude Vision 分析圖片
        # 2. Prompt: "請估計圖片中食物的總重量（克）"
        # 3. 解析 VLM 回應並返回數值
        
        try:
            # 調用 VLM API
            vlm_response = await vlm_api.analyze_portion(image_path, foods)
            portion_grams = vlm_response.get('portion_grams', 100.0)
            
            # 驗證範圍 (10g - 2000g)
            if 10 <= portion_grams <= 2000:
                return portion_grams
            else:
                logger.warning(f"VLM返回異常份量: {portion_grams}g，使用預設值")
                return 100.0
                
        except Exception as e:
            utils.handle_error(e, "VLM份量估計錯誤", logger=logger, raise_error=False)
            return 100.0
    """
    # MVP: 返回預設值
    # TODO: 整合 VLM API 進行視覺份量估計
    logger.info(f"使用預設份量 100g（未來將整合 VLM 估計）")
    return 100.0


def _format_track_response(
    foods: List[str], 
    nutrition_data: Dict[str, float], 
    total_calories: float,
    recommendation: str,
    meal_id: int,
    image_url: str = None,
    meal_type: str = 'meal',
    portion_size: float = 100.0
) -> discord.Embed:
    """
    格式化 track 命令的回應訊息為 Discord Embed（含餐次和份量資訊）
    
    Args:
        foods: 識別到的食物列表
        nutrition_data: 營養資訊字典 {食物名稱: 熱量}
        total_calories: 總熱量
        recommendation: AI 推薦內容
        meal_id: 餐點記錄 ID
        image_url: 用戶上傳的圖片 URL
        meal_type: 餐次類型
        portion_size: 份量大小（克）
    
    Returns:
        格式化的 Discord Embed 物件
    """
    
    # 建立 Embed
    embed = discord.Embed(
        title="✅ 飲食分析完成！",
        color=0x00ff7f,  # 春綠色
        timestamp=datetime.now()
    )
    
    # 如果有圖片 URL，設定為縮圖
    if image_url:
        embed.set_image(url=image_url)
    
    # 餐次和份量資訊
    meal_info = f"{_format_meal_type_chinese(meal_type)} | 📏 份量: {portion_size:.0f}g"
    embed.add_field(
        name="🕐 餐次資訊",
        value=meal_info,
        inline=False
    )
    
    # 建構食物清單
    food_list = "、".join(foods) if foods else "未識別"
    embed.add_field(
        name="🔍 識別結果",
        value=food_list,
        inline=False
    )
    
    # 建構營養詳情
    nutrition_details = []
    for food_name, calories in nutrition_data.items():
        nutrition_details.append(f"• **{food_name}**: {calories:.1f} kcal")
    
    nutrition_text = "\n".join(nutrition_details) if nutrition_details else "無詳細資訊"
    embed.add_field(
        name="📊 營養分析",
        value=nutrition_text,
        inline=False
    )
    
    # 總熱量
    embed.add_field(
        name="🔥 總熱量",
        value=f"{total_calories:.0f} kcal",
        inline=True
    )
    
    # 截取推薦內容的關鍵部分
    recommendation_summary = _extract_recommendation_summary(recommendation)
    embed.add_field(
        name="🤖 AI 個人化建議",
        value=recommendation_summary,
        inline=False
    )
    
    # 記錄資訊
    embed.add_field(
        name="📝 記錄資訊",
        value=f"使用 `/history` 查看完整記錄",
        inline=False
    )
    
    embed.set_footer(text="💡 保持健康飲食，持續追蹤您的營養攝取 (本系統所產生之結果僅供參考)")
    
    return embed


def _extract_recommendation_summary(recommendation: str) -> str:
    """
    從完整的 AI 推薦中提取關鍵摘要
    
    Args:
        recommendation: 完整的 AI 推薦內容
        
    Returns:
        摘要內容
    """
    if not recommendation:
        return "暫無個人化建議"
    
    # 尋找健康建議部分
    lines = recommendation.split('\n')
    summary_lines = []
    in_suggestion_section = False
    
    for line in lines:
        line = line.strip()
        if '健康建議' in line or '💡' in line:
            in_suggestion_section = True
            continue
        elif in_suggestion_section:
            if line.startswith(('1.', '2.', '3.', '-', '•')):
                # 清理並添加建議項目
                clean_line = line.lstrip('123456789.-• ').strip()
                if clean_line and len(summary_lines) < 3:  # 限制最多3條建議
                    summary_lines.append(f"• {clean_line}")
            elif line.startswith('🍎') or line.startswith('⚠️'):
                break  # 到達下一個區段
    
    if summary_lines:
        return '\n'.join(summary_lines)
    else:
        # 如果無法解析，返回前100字符
        return recommendation[:100] + "..." if len(recommendation) > 100 else recommendation


async def _is_admin_or_owner(ctx: commands.Context) -> bool:
    """檢查用戶是否為管理員或機器人擁有者 (前綴命令版本)"""
    return (
        ctx.author.guild_permissions.administrator or 
        await bot.is_owner(ctx.author)
    )

async def _is_admin_or_owner_interaction(interaction: discord.Interaction) -> bool:
    """檢查用戶是否為管理員或機器人擁有者 (斜槓命令版本)"""
    return (
        interaction.user.guild_permissions.administrator or 
        await bot.is_owner(interaction.user)
    )



@bot.tree.command(name='history', description='查看您的飲食歷史記錄')
async def history_command(interaction: discord.Interaction, 天數: int = 7):
    """
    /history 命令 - 查看用戶飲食歷史記錄
    
    Args:
        interaction: Discord 斜槓命令互動
        天數: 查看最近幾天的記錄，預設 7 天
    """
    try:
        user_id = str(interaction.user.id)
        
        # 參數驗證
        if 天數 <= 0 or 天數 > 365:
            await interaction.response.send_message(
                "❌ **天數參數錯誤**\n\n天數必須在 1-365 之間",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message("🔍 **正在查詢您的飲食記錄...**")
        
        # 查詢歷史記錄
        history_records = data_storage.get_history(user_id, 天數)
        
        if not history_records:
            embed = discord.Embed(
                title="📋 飲食歷史記錄",
                description=f"最近 {天數} 天內沒有飲食記錄",
                color=0xffa500
            )
            embed.add_field(
                name="💡 開始記錄",
                value="使用 `/analyze` 命令上傳食物圖片開始記錄您的飲食！",
                inline=False
            )
            await interaction.edit_original_response(content=None, embed=embed)
            return
        
        # 建立歷史記錄 Embed
        embed = discord.Embed(
            title="📋 您的飲食歷史記錄",
            description=f"最近 {天數} 天的飲食記錄（共 {len(history_records)} 筆）",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        # 計算總統計
        total_meals = len(history_records)
        total_calories = sum(record[3] for record in history_records)  # record[3] 是 calories
        avg_calories = total_calories / total_meals if total_meals > 0 else 0
        
        # 統計摘要
        embed.add_field(
            name="📊 統計摘要",
            value=f"• **總餐數**: {total_meals} 餐\n"
                  f"• **總熱量**: {total_calories:.0f} kcal\n"
                  f"• **平均熱量**: {avg_calories:.0f} kcal/餐",
            inline=False
        )
        
        # 顯示最近的記錄（最多5筆）
        recent_records = history_records[:5]
        
        for i, (record_id, date, foods, calories, created_at, meal_type, meal_type_custom) in enumerate(recent_records):
            # 解析日期
            try:
                meal_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                formatted_date = meal_date.strftime("%m月%d日 %H:%M")
            except:
                formatted_date = date[:16]  # 備用格式
            
            # 格式化餐次類型
            meal_display = _format_meal_type_chinese(meal_type or 'meal', meal_type_custom)
            
            # 建構食物列表
            if isinstance(foods, dict):
                food_list = []
                for food_name, food_calories in foods.items():
                    food_list.append(f"• {food_name}: {food_calories:.0f} kcal")
                foods_text = "\n".join(food_list) if food_list else "無詳細資訊"
            else:
                foods_text = "資料格式錯誤"
            
            embed.add_field(
                name=f"{meal_display} | {formatted_date}",
                value=f"{foods_text}\n**總計**: {calories:.0f} kcal",
                inline=False
            )
        
        # 如果有更多記錄，顯示提示
        if len(history_records) > 5:
            embed.add_field(
                name="📝 更多記錄",
                value=f"還有 {len(history_records) - 5} 筆記錄，使用較小的天數參數查看更詳細的記錄",
                inline=False
            )
        
        embed.set_footer(text="💡 使用 /analyze 命令添加新的飲食記錄")
        
        await interaction.edit_original_response(content=None, embed=embed)
        
        logger.info(f"用戶 {user_id} 查詢了 {天數} 天的歷史記錄，共 {len(history_records)} 筆")
        
    except Exception as e:
        logger.error(f"History命令錯誤 - 用戶: {interaction.user.id}, 錯誤: {str(e)}")
        
        try:
            await interaction.edit_original_response(
                content="❌ **查詢歷史記錄時發生錯誤**\n請稍後再試，或聯繫管理員。"
            )
        except:
            try:
                await interaction.followup.send("❌ 查詢歷史記錄時發生錯誤，請稍後再試。")
            except:
                pass


@bot.tree.command(name='recommend', description='獲得個人化飲食建議')
@discord.app_commands.describe(
    meal='想要建議的餐次 (早餐/午餐/晚餐/點心)',
    days='分析最近幾天的記錄 (預設 7 天)'
)
async def recommend_command(interaction: discord.Interaction, meal: str = None, days: int = 7):
    """
    /recommend 命令 - 基於歷史的個人化 RAG 推薦
    
    整合 RAG (Retrieval-Augmented Generation) 推薦引擎,
    根據用戶的飲食歷史提供個人化的飲食建議。
    
    Args:
        interaction: Discord 斜槓命令互動
        meal: 想要建議的餐次 (早餐/午餐/晚餐/點心),不提供則分析整體飲食
        days: 分析最近幾天的記錄,預設 7 天
    """
    try:
        user_id = str(interaction.user.id)
        
        # 參數驗證
        if days <= 0 or days > 30:
            await interaction.response.send_message(
                "❌ **天數參數錯誤**\n\n天數必須在 1-30 之間",
                ephemeral=True
            )
            return
        
        await interaction.response.send_message("🔄 **正在分析您的飲食歷史...**\n請稍候,AI 正在為您生成個人化建議")
        
        # 解析餐次類型
        meal_type = _parse_meal_type_from_chinese(meal) if meal else 'meal'
        
        # 獲取當前餐點資訊 (如果有)
        history_records = data_storage.get_history(user_id, 1)
        current_foods = None
        current_calories = 0.0
        
        if history_records and len(history_records) > 0:
            # 使用最近一筆記錄作為當前參考
            latest_record = history_records[0]
            current_foods = latest_record[2]  # foods dict
            current_calories = latest_record[3]  # calories
        
        # 呼叫 RAG 推薦引擎
        await interaction.edit_original_response(
            content="🤖 **AI 正在生成個人化建議...**\n"
                   f"• 分析天數: {days} 天\n"
                   f"• 目標餐次: {_format_meal_type_chinese(meal_type)}\n"
                   "• 整合歷史數據中..."
        )
        
        recommendation = recommendation_engine.get_recommendation(
            user_id=user_id,
            meal_type=meal_type,
            current_foods=current_foods,
            current_calories=current_calories,
            days=days
        )
        
        # 檢查是否有歷史記錄
        all_history = data_storage.get_history(user_id, days)
        has_history = all_history and len(all_history) > 0
        
        # 建立推薦結果 Embed
        embed = discord.Embed(
            title="🤖 個人化飲食建議",
            description=f"基於您最近 {days} 天的飲食記錄",
            color=0x9b59b6,  # 紫色
            timestamp=datetime.now()
        )
        
        # 添加分析範圍資訊
        if has_history:
            embed.add_field(
                name="📊 分析範圍",
                value=f"• **天數**: {days} 天\n"
                      f"• **記錄數**: {len(all_history)} 筆\n"
                      f"• **目標餐次**: {_format_meal_type_chinese(meal_type)}",
                inline=False
            )
        else:
            embed.add_field(
                name="ℹ️ 提示",
                value=f"您是新用戶或最近 {days} 天內沒有記錄。\n以下是基於一般營養原則的建議。",
                inline=False
            )
        
        # 解析並格式化推薦內容
        recommendation_sections = _parse_recommendation_sections(recommendation)
        
        # 飲食分析
        if recommendation_sections.get('analysis'):
            analysis_text = recommendation_sections['analysis']
            # 限制長度以符合 Discord Embed 限制
            if len(analysis_text) > 1024:
                analysis_text = analysis_text[:1021] + "..."
            embed.add_field(
                name="🔍 飲食分析",
                value=analysis_text,
                inline=False
            )
        
        # 健康建議
        if recommendation_sections.get('suggestions'):
            suggestions_text = recommendation_sections['suggestions']
            if len(suggestions_text) > 1024:
                suggestions_text = suggestions_text[:1021] + "..."
            embed.add_field(
                name="💡 健康建議",
                value=suggestions_text,
                inline=False
            )
        
        # 推薦食物
        if recommendation_sections.get('foods'):
            foods_text = recommendation_sections['foods']
            if len(foods_text) > 1024:
                foods_text = foods_text[:1021] + "..."
            embed.add_field(
                name="🍎 推薦食物",
                value=foods_text,
                inline=False
            )
        
        # 注意事項
        if recommendation_sections.get('warnings'):
            warnings_text = recommendation_sections['warnings']
            if len(warnings_text) > 1024:
                warnings_text = warnings_text[:1021] + "..."
            embed.add_field(
                name="⚠️ 注意事項",
                value=warnings_text,
                inline=False
            )
        
        # 如果沒有解析到任何區段,顯示原始推薦
        if not any(recommendation_sections.values()):
            # 分段顯示原始推薦
            chunks = _split_recommendation_text(recommendation, 1024)
            for i, chunk in enumerate(chunks[:3]):  # 最多3個區段
                embed.add_field(
                    name=f"💬 建議 ({i+1}/{len(chunks)})" if len(chunks) > 1 else "💬 個人化建議",
                    value=chunk,
                    inline=False
                )
        
        # 行動建議
        action_items = _extract_action_items(recommendation)
        if action_items:
            embed.add_field(
                name="✅ 下一步行動",
                value=action_items,
                inline=False
            )
        else:
            embed.add_field(
                name="✅ 下一步",
                value="• 使用 `/analyze` 上傳今日餐點\n"
                      "• 使用 `/history` 查看飲食記錄\n"
                      "• 持續記錄以獲得更精準建議",
                inline=False
            )
        
        embed.set_footer(text="💡 建議會根據您的飲食記錄持續優化 (本系統所產生之結果僅供參考)")
        
        await interaction.edit_original_response(content=None, embed=embed)
        
        logger.info(
            f"用戶 {user_id} 請求個人化推薦 - "
            f"餐次: {meal_type}, 天數: {days}, 歷史記錄: {len(all_history) if all_history else 0} 筆"
        )
        
    except Exception as e:
        logger.error(f"Recommend命令錯誤 - 用戶: {interaction.user.id}, 錯誤: {str(e)}")
        
        try:
            await interaction.edit_original_response(
                content="❌ **生成建議時發生錯誤**\n請稍後再試,或聯繫管理員。"
            )
        except:
            try:
                await interaction.followup.send("❌ 生成建議時發生錯誤,請稍後再試。")
            except:
                pass


@bot.tree.command(name='ask', description='向營養師提問')
async def ask_nutritionist(interaction: discord.Interaction, 問題: str):
    """
    /ask 命令 - AI 營養諮詢
    """
    await interaction.response.send_message(f"🤖 **營養師 AI 回答您的問題**\n\n**問題**: {問題}\n\n🚧 此功能正在開發中，即將提供專業的營養諮詢服務！", ephemeral=True)

@bot.tree.command(name='hello', description='打招呼 - 與營養師互動')
async def hello_command(interaction: discord.Interaction):
    """
    /hello 命令 - 友好互動
    """
    embed = discord.Embed(
        title="👋 您好！我是您的 AI 營養師",
        description="很高興為您服務！我可以幫助您追蹤飲食並提供營養建議。",
        color=0x2ecc71
    )
    
    embed.add_field(
        name="🚀 開始使用",
        value="• `/analyze` - 上傳食物圖片開始分析\n• `/history` - 查看飲食記錄\n• `/help` - 查看所有功能",
        inline=False
    )
    
    embed.add_field(
        name="💡 小貼士",
        value="拍攝食物照片時，請確保光線充足、食物清晰可見，這樣我就能給您更準確的分析結果！",
        inline=False
    )
    
    embed.set_footer(text="讓我們一起建立健康的飲食習慣！ 🥗")
    
    await interaction.response.send_message(embed=embed)


# ==================== 機器人啟動函數 ====================

def run_bot(token: str = None):
    """
    啟動 Discord 機器人
    
    Args:
        token: Discord Bot Token，如果未提供則從環境變數讀取
    """
    bot_token = token or DISCORD_TOKEN
    
    if not bot_token:
        logger.error("❌ 未找到 Discord Bot Token")
        raise ValueError("請在 config/.env 中設定 DISCORD_TOKEN")
    
    logger.info("🚀 正在啟動飲食追蹤機器人...")
    
    try:
        bot.run(bot_token)
    except discord.LoginFailure:
        logger.error("❌ Discord Token 無效，請檢查配置")
        raise
    except Exception as e:
        logger.error(f"❌ 機器人啟動失敗: {e}")
        raise


if __name__ == "__main__":
    # 直接運行此檔案時啟動機器人
    run_bot()