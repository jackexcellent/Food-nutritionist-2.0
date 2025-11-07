#!/usr/bin/env python3
"""
Diet Tracker Discord Bot - Discord 機器人測試
===========================================

測試 Discord 機器人的完整性和正確性，包括：
1. 機器人初始化和配置
2. /track 命令核心功能
3. 圖片處理和附件處理
4. 模組整合測試
5. 錯誤處理機制
6. 用戶介面回應

設計原則：
- 使用 mock 避免實際 Discord API 呼叫
- 模擬真實的用戶互動場景
- 測試所有主要功能路徑
- 驗證錯誤處理和用戶反饋
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime
import asyncio

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

# 導入要測試的模組
import discord_bot
from discord_bot import DietTrackerBot, bot, track_food, help_command, bot_stats


# ==================== 測試 Fixtures ====================

@pytest.fixture
def mock_discord_context():
    """模擬 Discord 命令上下文"""
    ctx = Mock()
    ctx.author = Mock()
    ctx.author.id = 12345678901234567890
    ctx.send = AsyncMock()
    ctx.message = Mock()
    ctx.message.attachments = []
    return ctx


@pytest.fixture  
def mock_image_attachment():
    """模擬圖片附件"""
    attachment = Mock()
    attachment.filename = "food_image.jpg"
    attachment.size = 1024 * 1024  # 1MB
    attachment.read = AsyncMock(return_value=b"fake_image_data")
    return attachment


@pytest.fixture
def mock_modules():
    """模擬所有外部模組"""
    with patch('discord_bot.image_processor') as mock_image_processor, \
         patch('discord_bot.nutrition_calculator') as mock_nutrition_calculator, \
         patch('discord_bot.data_storage') as mock_data_storage, \
         patch('discord_bot.recommendation_engine') as mock_recommendation_engine, \
         patch('discord_bot.utils') as mock_utils:
        
        mocks = {
            'image_processor': mock_image_processor,
            'nutrition_calculator': mock_nutrition_calculator,
            'data_storage': mock_data_storage,
            'recommendation_engine': mock_recommendation_engine,
            'utils': mock_utils
        }
        # 設定模組的預設行為
        mocks['image_processor'].process_image.return_value = ['蘋果', '香蕉']
        mocks['nutrition_calculator'].get_nutrition.return_value = {
            '蘋果': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2},
            '香蕉': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3}
        }
        mocks['data_storage'].store_meal.return_value = 1001
        mocks['recommendation_engine'].get_recommendation.return_value = (
            "🔍 **飲食分析**：\n今天攝取的水果很好！\n\n"
            "💡 **健康建議**：\n1. 增加蛋白質攝取\n2. 多喝水\n3. 保持均衡飲食"
        )
        mocks['utils'].handle_error.return_value = "測試錯誤訊息"
        
        yield mocks


@pytest.fixture
def sample_nutrition_data():
    """測試用營養資料"""
    return {
        '蘋果': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2},
        '香蕉': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3}
    }


# ==================== 機器人核心測試 ====================

class TestDietTrackerBot:
    """Discord 機器人核心功能測試"""
    
    def test_bot_initialization(self):
        """測試機器人初始化"""
        # 創建新的機器人實例進行測試
        test_bot = DietTrackerBot()
        
        # 驗證基本屬性
        assert test_bot.command_prefix == '/'
        assert test_bot.user is None  # 未連接時為 None
        
        # 驗證統計資料初始化
        assert 'total_tracks' in test_bot.stats
        assert 'successful_analyses' in test_bot.stats
        assert 'errors' in test_bot.stats
        assert 'start_time' in test_bot.stats
        
        # 驗證初始值
        assert test_bot.stats['total_tracks'] == 0
        assert test_bot.stats['successful_analyses'] == 0
        assert test_bot.stats['errors'] == 0
        assert isinstance(test_bot.stats['start_time'], datetime)
    
    @pytest.mark.asyncio
    async def test_bot_ready_event(self):
        """測試機器人就緒事件"""
        test_bot = DietTrackerBot()
        
        # 模擬機器人用戶和伺服器
        test_bot.user = Mock()
        test_bot.user.id = 987654321
        test_bot.guilds = [Mock(), Mock()]  # 2個伺服器
        
        # 模擬狀態變更方法
        test_bot.change_presence = AsyncMock()
        
        # 測試 on_ready 方法
        await test_bot.on_ready()
        
        # 驗證狀態設定被呼叫
        test_bot.change_presence.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_global_error_handler(self):
        """測試全域錯誤處理"""
        test_bot = DietTrackerBot()
        
        # 模擬命令上下文
        ctx = Mock()
        ctx.send = AsyncMock()
        ctx.author = Mock()
        ctx.author.id = 123456789
        ctx.command = None
        
        # 測試不同類型的錯誤
        from discord.ext.commands import CommandNotFound, MissingRequiredArgument
        
        # 測試命令未找到錯誤
        await test_bot.on_command_error(ctx, CommandNotFound())
        ctx.send.assert_called_with("❓ 找不到該命令。使用 `/help` 查看可用命令。")
        
        # 重置 mock
        ctx.send.reset_mock()
        
        # 測試缺少參數錯誤
        await test_bot.on_command_error(ctx, MissingRequiredArgument(Mock()))
        ctx.send.assert_called_with("⚠️ 缺少必要參數。請檢查命令格式。")
        
        # 驗證錯誤計數增加
        assert test_bot.stats['errors'] >= 2


# ==================== Track 命令測試 ====================

class TestTrackCommand:
    """測試 /track 命令功能"""
    
    @pytest.mark.asyncio
    async def test_track_command_no_attachments(self, mock_discord_context):
        """測試沒有附件時的處理"""
        ctx = mock_discord_context
        ctx.message.attachments = []
        
        await track_food(ctx)
        
        # 驗證發送了提示訊息
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "請上傳食物圖片" in call_args
        assert "使用方式" in call_args
    
    @pytest.mark.asyncio
    async def test_track_command_invalid_file_type(self, mock_discord_context):
        """測試無效檔案類型處理"""
        ctx = mock_discord_context
        
        # 模擬無效檔案附件
        invalid_attachment = Mock()
        invalid_attachment.filename = "document.pdf"
        ctx.message.attachments = [invalid_attachment]
        
        # 模擬處理中訊息
        processing_msg = Mock()
        processing_msg.edit = AsyncMock()
        ctx.send = AsyncMock(return_value=processing_msg)
        
        await track_food(ctx)
        
        # 驗證錯誤訊息
        processing_msg.edit.assert_called()
        edit_call_args = processing_msg.edit.call_args[1]['content']
        assert "請上傳有效的圖片檔案" in edit_call_args
    
    @pytest.mark.asyncio
    async def test_track_command_file_too_large(self, mock_discord_context, mock_image_attachment):
        """測試檔案過大處理"""
        ctx = mock_discord_context
        
        # 設定過大的檔案
        mock_image_attachment.size = 50 * 1024 * 1024  # 50MB
        ctx.message.attachments = [mock_image_attachment]
        
        # 模擬處理中訊息
        processing_msg = Mock()
        processing_msg.edit = AsyncMock()
        ctx.send = AsyncMock(return_value=processing_msg)
        
        await track_food(ctx)
        
        # 驗證檔案大小錯誤
        processing_msg.edit.assert_called()
        edit_call_args = processing_msg.edit.call_args[1]['content']
        assert "圖片太大" in edit_call_args
    
    @pytest.mark.asyncio
    async def test_track_command_successful_flow(
        self, 
        mock_discord_context, 
        mock_image_attachment, 
        mock_modules,
        sample_nutrition_data
    ):
        """測試成功的完整流程"""
        ctx = mock_discord_context
        ctx.message.attachments = [mock_image_attachment]
        
        # 模擬處理中訊息
        processing_msg = Mock()
        processing_msg.edit = AsyncMock()
        ctx.send = AsyncMock(return_value=processing_msg)
        
        # 模擬臨時檔案
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test.jpg'
            
            with patch('os.path.exists', return_value=True):
                with patch('os.unlink'):
                    await track_food(ctx)
        
        # 驗證所有步驟都被執行
        mock_modules['image_processor'].process_image.assert_called_once()
        mock_modules['nutrition_calculator'].get_nutrition.assert_called_once()
        mock_modules['data_storage'].store_meal.assert_called_once()
        mock_modules['recommendation_engine'].get_recommendation.assert_called_once()
        
        # 驗證最終訊息包含預期內容
        final_edit_call = processing_msg.edit.call_args_list[-1]
        final_content = final_edit_call[1]['content']
        
        assert "✅ 飲食分析完成" in final_content
        assert "蘋果、香蕉" in final_content
        assert "141 kcal" in final_content  # 52 + 89
        assert "AI 個人化建議" in final_content
        
        # 驗證統計數據更新
        assert bot.stats['total_tracks'] > 0
        assert bot.stats['successful_analyses'] > 0
    
    @pytest.mark.asyncio
    async def test_track_command_no_foods_identified(
        self,
        mock_discord_context,
        mock_image_attachment,
        mock_modules
    ):
        """測試無法識別食物的情況"""
        ctx = mock_discord_context
        ctx.message.attachments = [mock_image_attachment]
        
        # 設定無法識別食物
        mock_modules['image_processor'].process_image.return_value = []
        
        # 模擬處理中訊息
        processing_msg = Mock()
        processing_msg.edit = AsyncMock()
        ctx.send = AsyncMock(return_value=processing_msg)
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test.jpg'
            
            await track_food(ctx)
        
        # 驗證錯誤訊息
        processing_msg.edit.assert_called()
        final_content = processing_msg.edit.call_args[1]['content']
        assert "無法識別圖片中的食物" in final_content
    
    @pytest.mark.asyncio 
    async def test_track_command_nutrition_data_error(
        self,
        mock_discord_context,
        mock_image_attachment,
        mock_modules
    ):
        """測試營養資料獲取失敗"""
        ctx = mock_discord_context
        ctx.message.attachments = [mock_image_attachment]
        
        # 設定營養資料獲取失敗
        mock_modules['nutrition_calculator'].get_nutrition.return_value = None
        
        # 模擬處理中訊息
        processing_msg = Mock()
        processing_msg.edit = AsyncMock()
        ctx.send = AsyncMock(return_value=processing_msg)
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test.jpg'
            
            await track_food(ctx)
        
        # 驗證錯誤訊息
        processing_msg.edit.assert_called()
        final_content = processing_msg.edit.call_args[1]['content']
        assert "無法取得營養資訊" in final_content
    
    @pytest.mark.asyncio
    async def test_track_command_exception_handling(
        self,
        mock_discord_context,
        mock_image_attachment,
        mock_modules
    ):
        """測試異常處理"""
        ctx = mock_discord_context
        ctx.message.attachments = [mock_image_attachment]
        
        # 模擬處理中訊息
        processing_msg = Mock()
        processing_msg.edit = AsyncMock()
        ctx.send = AsyncMock(return_value=processing_msg)
        
        # 設定模組拋出異常
        mock_modules['image_processor'].process_image.side_effect = Exception("測試異常")
        
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test.jpg'
            
            await track_food(ctx)
        
        # 驗證錯誤處理
        assert mock_modules['utils'].handle_error.called
        processing_msg.edit.assert_called()
        
        # 驗證錯誤統計更新
        assert bot.stats['errors'] > 0


# ==================== 其他命令測試 ====================

class TestOtherCommands:
    """測試其他機器人命令"""
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_discord_context):
        """測試 help 命令"""
        ctx = mock_discord_context
        
        await help_command(ctx)
        
        # 驗證發送了嵌入式訊息
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[1]
        embed = call_args.get('embed')
        
        assert embed is not None
        assert "飲食追蹤機器人說明" in embed.title
        assert len(embed.fields) > 0
    
    @pytest.mark.asyncio
    async def test_bot_stats_command_non_admin(self, mock_discord_context):
        """測試非管理員使用統計命令"""
        ctx = mock_discord_context
        ctx.author.guild_permissions = Mock()
        ctx.author.guild_permissions.administrator = False
        
        # 模擬 is_owner 檢查
        with patch.object(bot, 'is_owner', return_value=False):
            await bot_stats(ctx)
        
        # 驗證拒絕訊息
        ctx.send.assert_called_with("❌ 此命令僅限管理員使用")
    
    @pytest.mark.asyncio
    async def test_bot_stats_command_admin(self, mock_discord_context):
        """測試管理員使用統計命令"""
        ctx = mock_discord_context
        ctx.author.guild_permissions = Mock()
        ctx.author.guild_permissions.administrator = True
        
        # 設定機器人統計
        bot.stats.update({
            'total_tracks': 100,
            'successful_analyses': 85,
            'errors': 15
        })
        bot.guilds = [Mock(), Mock(), Mock()]  # 3個伺服器
        bot.users = [Mock() for _ in range(50)]  # 50個用戶
        
        await bot_stats(ctx)
        
        # 驗證統計訊息發送
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[1]
        embed = call_args.get('embed')
        
        assert embed is not None
        assert "機器人統計資訊" in embed.title


# ==================== 輔助函數測試 ====================

class TestUtilityFunctions:
    """測試輔助函數"""
    
    def test_is_valid_image_file(self):
        """測試圖片檔案驗證"""
        from discord_bot import _is_valid_image_file
        
        # 測試有效格式
        assert _is_valid_image_file("image.jpg") == True
        assert _is_valid_image_file("photo.jpeg") == True
        assert _is_valid_image_file("picture.png") == True
        assert _is_valid_image_file("gif.gif") == True
        assert _is_valid_image_file("image.webp") == True
        
        # 測試無效格式
        assert _is_valid_image_file("document.pdf") == False
        assert _is_valid_image_file("video.mp4") == False
        assert _is_valid_image_file("file.txt") == False
        assert _is_valid_image_file("noextension") == False
        
        # 測試大小寫不敏感
        assert _is_valid_image_file("IMAGE.JPG") == True
        assert _is_valid_image_file("Photo.PNG") == True
    
    def test_format_track_response(self, sample_nutrition_data):
        """測試追蹤回應格式化"""
        from discord_bot import _format_track_response
        
        foods = ['蘋果', '香蕉']
        total_calories = 141.0
        recommendation = (
            "🔍 **飲食分析**：\n水果攝取良好\n\n"
            "💡 **健康建議**：\n1. 增加蛋白質\n2. 多喝水\n"
            "🍎 **推薦食物**：\n雞胸肉、魚類\n"
            "⚠️ **注意事項**：\n保持均衡"
        )
        meal_id = 1001
        
        response = _format_track_response(
            foods, sample_nutrition_data, total_calories, recommendation, meal_id
        )
        
        # 驗證回應內容
        assert "✅ **飲食分析完成！**" in response
        assert "蘋果、香蕉" in response
        assert "141 kcal" in response
        assert "記錄 ID**: #1001" in response
        
        # 驗證營養詳情
        assert "蘋果**: 52 kcal" in response
        assert "香蕉**: 89 kcal" in response
        assert "蛋白質" in response and "碳水" in response and "脂肪" in response
    
    def test_extract_recommendation_summary(self):
        """測試推薦摘要提取"""
        from discord_bot import _extract_recommendation_summary
        
        # 測試完整推薦內容
        full_recommendation = (
            "🔍 **飲食分析**：\n您的飲食很均衡\n\n"
            "💡 **健康建議**：\n"
            "1. 增加蛋白質攝取量\n"
            "2. 多攝取維生素C\n" 
            "3. 保持規律運動\n"
            "🍎 **推薦食物**：\n雞肉、魚類\n"
            "⚠️ **注意事項**：\n避免過量"
        )
        
        summary = _extract_recommendation_summary(full_recommendation)
        
        # 驗證摘要內容
        assert "增加蛋白質攝取量" in summary
        assert "多攝取維生素C" in summary
        assert "保持規律運動" in summary
        assert summary.count("•") == 3  # 3個建議項目
        
        # 測試空內容
        empty_summary = _extract_recommendation_summary("")
        assert empty_summary == "暫無個人化建議"
        
        # 測試無結構化內容
        unstructured = "這是一段普通的推薦文字，沒有特定格式。"
        fallback_summary = _extract_recommendation_summary(unstructured)
        assert len(fallback_summary) <= 100  # 應該被截斷


# ==================== 機器人啟動測試 ====================

class TestBotStartup:
    """測試機器人啟動相關功能"""
    
    def test_run_bot_no_token(self):
        """測試沒有 token 時的處理"""
        from discord_bot import run_bot
        
        with pytest.raises(ValueError, match="請在 config/.env 中設定 DISCORD_TOKEN"):
            run_bot(token="")
    
    @patch('discord_bot.bot.run')
    def test_run_bot_with_token(self, mock_bot_run):
        """測試使用 token 啟動機器人"""
        from discord_bot import run_bot
        
        test_token = "test_token_123"
        run_bot(token=test_token)
        
        # 驗證機器人運行被調用
        mock_bot_run.assert_called_once_with(test_token)


# ==================== 整合測試 ====================

class TestIntegration:
    """整合測試"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_mock(
        self,
        mock_discord_context,
        mock_image_attachment,
        mock_modules
    ):
        """測試完整工作流程 (使用 mock)"""
        ctx = mock_discord_context
        ctx.message.attachments = [mock_image_attachment]
        
        # 模擬處理中訊息
        processing_msg = Mock()
        processing_msg.edit = AsyncMock()
        ctx.send = AsyncMock(return_value=processing_msg)
        
        # 記錄初始統計
        initial_tracks = bot.stats['total_tracks']
        initial_success = bot.stats['successful_analyses']
        
        # 執行完整流程
        with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
            mock_temp_file.return_value.__enter__.return_value.name = '/tmp/test.jpg'
            
            with patch('os.path.exists', return_value=True):
                with patch('os.unlink'):
                    await track_food(ctx)
        
        # 驗證統計更新
        assert bot.stats['total_tracks'] > initial_tracks
        assert bot.stats['successful_analyses'] > initial_success
        
        # 驗證所有模組被正確呼叫
        assert mock_modules['image_processor'].process_image.call_count == 1
        assert mock_modules['nutrition_calculator'].get_nutrition.call_count == 1
        assert mock_modules['data_storage'].store_meal.call_count == 1
        assert mock_modules['recommendation_engine'].get_recommendation.call_count == 1
    
    def test_environment_variables_loading(self):
        """測試環境變數載入"""
        # 驗證關鍵環境變數存在
        assert discord_bot.DISCORD_TOKEN is not None
        assert discord_bot.BOT_PREFIX == '/'
        
        # 驗證 intents 設定
        assert discord_bot.DEFAULT_INTENTS.message_content == True


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])