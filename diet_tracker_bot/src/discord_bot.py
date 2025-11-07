#!/usr/bin/env python3
"""
Diet Tracker Discord Bot - Discord 機器人模組
============================================

這個模組實現了 Discord 機器人的核心功能，整合所有系統組件
提供用戶友好的界面來追蹤飲食、查看歷史和獲得AI推薦。

主要功能：
1. /track 命令 - 食物圖片識別和營養分析 (MVP)
2. 未來擴展：/history, /stats, /recommend 等命令

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
                name="你的飲食健康 | /track 開始追蹤"
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


@bot.tree.command(name='track', description='上傳食物圖片進行營養分析和追蹤')
async def track_food(interaction: discord.Interaction, 圖片: discord.Attachment):
    """
    /track 斜槓命令 - MVP 核心功能
    
    處理用戶上傳的食物圖片，進行以下流程：
    1. 檢查附件 (圖片)
    2. 食物識別 (image_processor)
    3. 營養分析 (nutrition_calculator)
    4. 儲存記錄 (data_storage)
    5. AI 推薦 (recommendation_engine)
    6. 回傳結構化結果
    
    Args:
        interaction: Discord 斜槓命令互動
        圖片: 用戶上傳的食物圖片
    """
    try:
        bot.stats['total_tracks'] += 1
        user_id = str(interaction.user.id)
        
        # 檢查圖片參數
        if not 圖片:
            await interaction.response.send_message(
                "❌ **請提供食物圖片進行分析！**\n\n"
                "使用方式：\n"
                "1. 輸入 `/track`\n"
                "2. 在 `圖片` 參數中上傳食物圖片\n"
                "3. 等待 AI 分析結果\n\n"
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
            await interaction.edit_original_response(content="🔄 **步驟 1/4: 識別食物中...**")
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
            
            # 步驟 2: 營養分析
            await interaction.edit_original_response(content="🔄 **步驟 2/4: 計算營養成分...**")
            nutrition_result = nutrition_calculator.get_nutrition(foods)
            
            if not nutrition_result or len(nutrition_result) != 2:
                await interaction.edit_original_response(content="❌ 無法取得營養資訊，請稍後再試")
                return
            
            # 解包返回值: (營養字典, 總熱量)
            nutrition_data, total_calories = nutrition_result
            
            # 步驟 3: 儲存記錄
            await interaction.edit_original_response(content="🔄 **步驟 3/4: 儲存飲食記錄...**")
            # nutrition_data 已經是 {食物名稱: 熱量} 格式
            meal_id = data_storage.store_meal(user_id, nutrition_data, total_calories)
            
            # 步驟 4: 產生 AI 推薦
            await interaction.edit_original_response(content="🔄 **步驟 4/4: 生成個人化建議...**")
            recommendation = recommendation_engine.get_recommendation(user_id, days=7)
            
            # 建構回應訊息 (包含圖片)
            embed_response = _format_track_response(
                foods, nutrition_data, total_calories, recommendation, meal_id, 
                image_url=attachment.url
            )
            
            # 發送最終結果
            await interaction.edit_original_response(content=None, embed=embed_response)
            
            # 更新統計
            bot.stats['successful_analyses'] += 1
            
            logger.info(f"成功處理追蹤請求 - 用戶: {user_id}, 食物: {foods}, 熱量: {total_calories}")
            
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
        name="📷 /track",
        value="上傳食物圖片進行分析\n• 自動識別食物\n• 計算營養成分\n• 儲存飲食記錄\n• 生成個人化建議",
        inline=False
    )
    
    embed.add_field(
        name="❓ /help", 
        value="顯示此說明訊息",
        inline=True
    )
    
    embed.add_field(
        name="🔜 即將推出",
        value="• `/history` - 查看飲食歷史\n• `/stats` - 營養統計報告\n• `/recommend` - 獲得飲食建議",
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


def _format_track_response(
    foods: List[str], 
    nutrition_data: Dict[str, float], 
    total_calories: float,
    recommendation: str,
    meal_id: int,
    image_url: str = None
) -> discord.Embed:
    """
    格式化 track 命令的回應訊息為 Discord Embed
    
    Args:
        foods: 識別到的食物列表
        nutrition_data: 營養資訊字典 {食物名稱: 熱量}
        total_calories: 總熱量
        recommendation: AI 推薦內容
        meal_id: 餐點記錄 ID
        image_url: 用戶上傳的圖片 URL
    
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
        value=f"記錄 ID: #{meal_id}\n使用 `/history` 查看完整記錄",
        inline=False
    )
    
    embed.set_footer(text="💡 保持健康飲食，持續追蹤您的營養攝取")
    
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


# ==================== 未來擴展命令架構 ====================

@bot.tree.command(name='analyze', description='上傳食物圖片進行分析')
async def analyze_food(interaction: discord.Interaction, 圖片: discord.Attachment):
    """
    /analyze 命令 - 與 /track 相同的功能，提供替代命令名稱
    """
    # 重定向到 track_food 函數
    await track_food(interaction, 圖片)

@bot.tree.command(name='analyze3', description='三階段影像→料理風格→菜名→營養')
async def analyze3_food(interaction: discord.Interaction, 圖片: discord.Attachment):
    """
    /analyze3 命令 - 增強版三階段分析
    """
    embed = discord.Embed(
        title="🚧 三階段增強分析功能",
        description="此功能正在開發中，即將提供更精確的分析！",
        color=0xffa500
    )
    
    embed.add_field(
        name="🔍 第一階段 - 影像深度解析",
        value="• 高精度物體識別\n• 食物邊界檢測\n• 材質紋理分析",
        inline=False
    )
    
    embed.add_field(
        name="🍽️ 第二階段 - 料理風格識別", 
        value="• 中式、西式、日式等料理風格\n• 烹飪方式判定\n• 地域特色識別",
        inline=False
    )
    
    embed.add_field(
        name="📝 第三階段 - 精確菜名判定",
        value="• 完整菜名推測\n• 食材成分分析\n• 詳細營養計算",
        inline=False
    )
    
    if 圖片:
        embed.set_image(url=圖片.url)
    
    embed.set_footer(text="敬請期待這個強大的分析功能！")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
        value="• `/track` - 上傳食物圖片開始分析\n• `/help` - 查看所有功能",
        inline=False
    )
    
    embed.add_field(
        name="💡 小貼士",
        value="拍攝食物照片時，請確保光線充足、食物清晰可見，這樣我就能給您更準確的分析結果！",
        inline=False
    )
    
    embed.set_footer(text="讓我們一起建立健康的飲食習慣！ 🥗")
    
    await interaction.response.send_message(embed=embed)

# 未來功能的斜槓命令架構

# @bot.tree.command(name='history', description='查看您的飲食歷史記錄')
# async def view_history(interaction: discord.Interaction, 天數: int = 7):
#     """查看用戶飲食歷史 - 未來功能"""
#     await interaction.response.send_message("🚧 此功能正在開發中，敬請期待！", ephemeral=True)

# @bot.tree.command(name='recommend', description='獲得基於歷史的飲食建議')  
# async def get_recommendation(interaction: discord.Interaction):
#     """獲得 AI 推薦 - 未來功能"""
#     await interaction.response.send_message("🚧 此功能正在開發中，敬請期待！", ephemeral=True)


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