#!/usr/bin/env python3
"""
測試 USDA API 食物名稱清理功能
============================

測試目標：
1. 特殊字元清理（括號、斜線等）
2. 邊界情況處理
3. 清理後仍保留關鍵資訊
"""

import sys
from pathlib import Path

# 添加 src 目錄到路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from nutrition_calculator import NutritionCalculator


class TestFoodNameSanitization:
    """測試食物名稱清理功能"""
    
    def setup_method(self):
        """初始化測試"""
        self.calculator = NutritionCalculator()
    
    def test_sanitize_with_parentheses_and_slash(self):
        """測試包含括號和斜線的名稱"""
        # 原始錯誤案例
        original = "山葵/芥末（wasabi）"
        cleaned = self.calculator._sanitize_food_name_for_api(original)
        
        # 應該移除括號和斜線，但保留英文關鍵字
        assert "(" not in cleaned
        assert ")" not in cleaned
        assert "（" not in cleaned
        assert "）" not in cleaned
        assert "/" not in cleaned
        assert "wasabi" in cleaned.lower()
        print(f"✓ 清理成功: '{original}' -> '{cleaned}'")
    
    def test_sanitize_with_english_parentheses(self):
        """測試英文括號"""
        original = "Banana (ripe)"
        cleaned = self.calculator._sanitize_food_name_for_api(original)
        
        # 保留英文內容
        assert "ripe" in cleaned.lower()
        assert "banana" in cleaned.lower()
        print(f"✓ 清理成功: '{original}' -> '{cleaned}'")
    
    def test_sanitize_with_chinese_parentheses(self):
        """測試中文括號"""
        original = "蘋果（紅色）"
        cleaned = self.calculator._sanitize_food_name_for_api(original)
        
        # 移除非英文括號內容
        assert "（" not in cleaned
        assert "）" not in cleaned
        assert "蘋果" in cleaned
        print(f"✓ 清理成功: '{original}' -> '{cleaned}'")
    
    def test_sanitize_with_slash(self):
        """測試斜線"""
        test_cases = [
            ("雞肉/牛肉", "雞肉 牛肉"),
            ("Apple/Banana", "Apple Banana"),
        ]
        
        for original, expected_content in test_cases:
            cleaned = self.calculator._sanitize_food_name_for_api(original)
            assert "/" not in cleaned
            # 檢查所有部分都保留
            for part in expected_content.split():
                assert part in cleaned
            print(f"✓ 清理成功: '{original}' -> '{cleaned}'")
    
    def test_sanitize_with_mixed_special_chars(self):
        """測試混合特殊字元"""
        original = "豬肉/牛肉（熟的）/雞肉"
        cleaned = self.calculator._sanitize_food_name_for_api(original)
        
        # 應該移除所有特殊字元
        assert "/" not in cleaned
        assert "（" not in cleaned
        assert "）" not in cleaned
        # 主要食物名稱應該保留
        assert "豬肉" in cleaned or "牛肉" in cleaned or "雞肉" in cleaned
        print(f"✓ 清理成功: '{original}' -> '{cleaned}'")
    
    def test_sanitize_preserves_normal_names(self):
        """測試正常名稱不受影響"""
        test_names = [
            "Apple",
            "香蕉",
            "Chicken breast",
            "白飯"
        ]
        
        for name in test_names:
            cleaned = self.calculator._sanitize_food_name_for_api(name)
            assert name.strip() == cleaned.strip()
            print(f"✓ 正常名稱不變: '{name}'")
    
    def test_sanitize_empty_or_whitespace(self):
        """測試空白或僅空格的輸入"""
        test_cases = ["", "   ", "\t\n"]
        
        for original in test_cases:
            cleaned = self.calculator._sanitize_food_name_for_api(original)
            # 空輸入應該返回原始值（避免完全空白）
            assert cleaned == original
            print(f"✓ 空白輸入處理: '{repr(original)}' -> '{repr(cleaned)}'")
    
    def test_sanitize_only_special_chars(self):
        """測試只有特殊字元的輸入"""
        original = "（）/（）"
        cleaned = self.calculator._sanitize_food_name_for_api(original)
        
        # 如果清理後為空，應返回原始名稱
        assert cleaned == original
        print(f"✓ 純特殊字元處理: '{original}' -> '{cleaned}'")
    
    def test_sanitize_with_numbers(self):
        """測試包含數字的名稱"""
        original = "Vitamin B12（補充劑）"
        cleaned = self.calculator._sanitize_food_name_for_api(original)
        
        # 數字應該保留
        assert "B12" in cleaned or "12" in cleaned
        assert "Vitamin" in cleaned
        print(f"✓ 數字保留: '{original}' -> '{cleaned}'")
    
    def test_sanitize_multiple_spaces(self):
        """測試多餘空格處理"""
        original = "Apple    Banana   Cherry"
        cleaned = self.calculator._sanitize_food_name_for_api(original)
        
        # 多餘空格應該被合併
        assert "  " not in cleaned
        assert "Apple" in cleaned
        assert "Banana" in cleaned
        assert "Cherry" in cleaned
        print(f"✓ 空格正規化: '{original}' -> '{cleaned}'")


def run_tests():
    """執行所有測試"""
    import pytest
    
    print("\n" + "="*60)
    print("測試 USDA API 食物名稱清理功能")
    print("="*60 + "\n")
    
    # 執行測試
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
