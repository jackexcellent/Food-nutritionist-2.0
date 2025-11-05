#!/usr/bin/env python3
"""
查看 user_data.db 資料庫內容的工具腳本
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
import sys

# 資料庫路徑
DB_PATH = Path("data/user_data.db")

def view_all_tables():
    """顯示資料庫中的所有表格"""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 獲取所有表格名稱
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print("🗄️  資料庫表格:")
            print("=" * 50)
            for table in tables:
                print(f"📋 {table['name']}")
            print()
            
    except sqlite3.Error as e:
        print(f"❌ 查詢表格失敗: {e}")

def view_table_schema(table_name):
    """顯示表格結構"""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            print(f"📋 表格 '{table_name}' 結構:")
            print("-" * 50)
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
            print()
            
    except sqlite3.Error as e:
        print(f"❌ 查詢表格結構失敗: {e}")

def view_meals_data():
    """顯示 meals 表格的所有資料"""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 獲取記錄總數
            cursor.execute("SELECT COUNT(*) as count FROM meals")
            count = cursor.fetchone()['count']
            
            if count == 0:
                print("📭 meals 表格是空的，沒有記錄")
                return
            
            print(f"📊 meals 表格內容 (共 {count} 筆記錄):")
            print("=" * 80)
            
            # 獲取所有記錄
            cursor.execute("""
                SELECT id, user_id, date, foods, calories, created_at
                FROM meals 
                ORDER BY date DESC
            """)
            
            records = cursor.fetchall()
            
            for i, record in enumerate(records, 1):
                print(f"\n📝 記錄 #{i} (ID: {record['id']})")
                print(f"   👤 用戶ID: {record['user_id']}")
                print(f"   📅 日期: {record['date']}")
                print(f"   🔥 熱量: {record['calories']:.1f} kcal")
                print(f"   ⏰ 創建時間: {record['created_at']}")
                
                # 解析食物 JSON
                try:
                    foods = json.loads(record['foods'])
                    print("   🍽️  食物:")
                    for food_name, food_calories in foods.items():
                        print(f"      • {food_name}: {food_calories} kcal")
                except json.JSONDecodeError as e:
                    print(f"      ❌ 食物資料解析失敗: {e}")
                
                print("-" * 60)
            
    except sqlite3.Error as e:
        print(f"❌ 查詢 meals 資料失敗: {e}")

def view_user_statistics():
    """顯示用戶統計資訊"""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 用戶統計
            cursor.execute("""
                SELECT 
                    user_id,
                    COUNT(*) as meal_count,
                    SUM(calories) as total_calories,
                    AVG(calories) as avg_calories,
                    MIN(date) as first_meal,
                    MAX(date) as last_meal
                FROM meals 
                GROUP BY user_id
                ORDER BY meal_count DESC
            """)
            
            users = cursor.fetchall()
            
            if not users:
                print("📭 沒有用戶資料")
                return
            
            print("👥 用戶統計:")
            print("=" * 80)
            
            for user in users:
                print(f"\n👤 用戶: {user['user_id']}")
                print(f"   📊 記錄數: {user['meal_count']}")
                print(f"   🔥 總熱量: {user['total_calories']:.1f} kcal")
                print(f"   📈 平均熱量: {user['avg_calories']:.1f} kcal/餐")
                print(f"   🗓️  首次記錄: {user['first_meal']}")
                print(f"   🗓️  最新記錄: {user['last_meal']}")
            
    except sqlite3.Error as e:
        print(f"❌ 查詢用戶統計失敗: {e}")

def main():
    """主函數"""
    print("🥗 Diet Tracker Bot - 資料庫查看器")
    print("=" * 80)
    
    # 檢查資料庫檔案是否存在
    if not DB_PATH.exists():
        print(f"❌ 資料庫檔案不存在: {DB_PATH}")
        print("請先運行應用程式以創建資料庫")
        return
    
    print(f"📁 資料庫位置: {DB_PATH.absolute()}")
    print(f"📏 檔案大小: {DB_PATH.stat().st_size} bytes")
    print()
    
    # 顯示表格
    view_all_tables()
    
    # 顯示 meals 表格結構
    view_table_schema("meals")
    
    # 顯示資料
    view_meals_data()
    
    # 顯示統計
    view_user_statistics()
    
    print("\n✅ 查看完成!")

if __name__ == "__main__":
    main()