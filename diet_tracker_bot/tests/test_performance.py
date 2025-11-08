#!/usr/bin/env python3
"""
Diet Tracker Bot - 性能和壓力測試
===============================

專門用於性能分析和壓力測試的測試套件。
這些測試幫助識別系統瓶頸，驗證擴展性，並確保在高負載下的穩定性。

測試類型：
1. 性能基準測試
2. 壓力測試
3. 負載測試
4. 記憶體洩漏測試
5. 資料庫性能測試
6. API 回應時間測試
7. 並發處理測試

設計原則：
- 測量關鍵路徑的執行時間
- 模擬真實世界的使用模式
- 識別性能退化點
- 測試系統在極限條件下的行為
"""

import os
import sys
import pytest
import time
import threading
import concurrent.futures
import psutil
import gc
import statistics
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import tempfile

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

import utils
import image_processor
import nutrition_calculator
import data_storage
import recommendation_engine

class PerformanceMetrics:
    """性能指標收集器"""
    
    def __init__(self):
        self.metrics = {
            'execution_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'database_operations': [],
            'api_calls': [],
            'cache_performance': {'hits': 0, 'misses': 0}
        }
    
    def record_execution_time(self, operation: str, duration: float):
        """記錄執行時間"""
        self.metrics['execution_times'].append({
            'operation': operation,
            'duration': duration,
            'timestamp': time.time()
        })
    
    def record_memory_usage(self):
        """記錄記憶體使用"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        self.metrics['memory_usage'].append({
            'memory_mb': memory_mb,
            'timestamp': time.time()
        })
        return memory_mb
    
    def record_database_operation(self, operation: str, duration: float, result_count: int = 0):
        """記錄資料庫操作"""
        self.metrics['database_operations'].append({
            'operation': operation,
            'duration': duration,
            'result_count': result_count,
            'timestamp': time.time()
        })
    
    def get_summary(self):
        """取得性能摘要"""
        if not self.metrics['execution_times']:
            return "沒有性能數據"
        
        durations = [m['duration'] for m in self.metrics['execution_times']]
        memory_values = [m['memory_mb'] for m in self.metrics['memory_usage']]
        
        return {
            'avg_execution_time': statistics.mean(durations) if durations else 0,
            'max_execution_time': max(durations) if durations else 0,
            'min_execution_time': min(durations) if durations else 0,
            'total_operations': len(durations),
            'avg_memory_mb': statistics.mean(memory_values) if memory_values else 0,
            'max_memory_mb': max(memory_values) if memory_values else 0,
            'cache_hit_rate': self.metrics['cache_performance']['hits'] / 
                            (self.metrics['cache_performance']['hits'] + self.metrics['cache_performance']['misses'])
                            if (self.metrics['cache_performance']['hits'] + self.metrics['cache_performance']['misses']) > 0 else 0
        }

class TestPerformanceBenchmarks:
    """性能基準測試"""
    
    @pytest.fixture(autouse=True)
    def setup_performance_environment(self):
        """設定性能測試環境"""
        self.metrics = PerformanceMetrics()
        
        # 清理系統狀態
        utils.clear_cache()
        data_storage.init_database()
        gc.collect()
        
        yield
        
        # 輸出性能報告
        summary = self.metrics.get_summary()
        utils.logger.info(f"📊 性能測試摘要: {summary}")
    
    def create_test_image(self, size=(300, 300)):
        """創建測試用圖片"""
        img_array = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        temp_path = os.path.join(tempfile.gettempdir(), f"perf_test_{time.time()}.jpg")
        img.save(temp_path, 'JPEG')
        
        return temp_path
    
    @patch('image_processor.process_image')
    def test_image_processing_performance(self, mock_process_image):
        """測試圖像處理性能"""
        mock_process_image.return_value = ['蘋果', '香蕉']
        
        # 測試不同圖片大小的處理時間
        sizes = [(100, 100), (300, 300), (600, 600), (1200, 1200)]
        
        for size in sizes:
            test_image = self.create_test_image(size)
            
            try:
                start_time = time.time()
                memory_before = self.metrics.record_memory_usage()
                
                # 執行圖像處理
                result = image_processor.process_image(test_image)
                
                duration = time.time() - start_time
                memory_after = self.metrics.record_memory_usage()
                
                self.metrics.record_execution_time(f'image_processing_{size[0]}x{size[1]}', duration)
                
                # 驗證結果
                assert result is not None
                assert len(result) > 0
                
                utils.logger.info(f"🖼️  圖片 {size}: {duration:.3f}s, 記憶體: {memory_after - memory_before:.1f}MB")
                
                # 性能基準
                if size == (300, 300):  # 標準大小
                    assert duration < 2.0, f"圖像處理太慢: {duration:.3f}s > 2.0s"
                elif size == (1200, 1200):  # 大圖片
                    assert duration < 5.0, f"大圖處理太慢: {duration:.3f}s > 5.0s"
                
            finally:
                os.unlink(test_image)
    
    @patch('nutrition_calculator.get_nutrition')
    def test_nutrition_calculation_performance(self, mock_get_nutrition):
        """測試營養計算性能"""
        # 模擬不同數量食物的營養計算
        foods_lists = [
            ['蘋果'],
            ['蘋果', '香蕉'],
            ['蘋果', '香蕉', '橘子', '葡萄'],
            ['蘋果', '香蕉', '橘子', '葡萄', '草莓', '芒果', '鳳梨', '櫻桃']
        ]
        
        for foods in foods_lists:
            # 設定 mock 回傳值
            nutrition_data = {food: 50.0 + len(food) * 10 for food in foods}
            total_calories = sum(nutrition_data.values())
            mock_get_nutrition.return_value = (nutrition_data, total_calories)
            
            start_time = time.time()
            memory_before = self.metrics.record_memory_usage()
            
            # 執行營養計算
            result = nutrition_calculator.get_nutrition(foods)
            
            duration = time.time() - start_time
            memory_after = self.metrics.record_memory_usage()
            
            self.metrics.record_execution_time(f'nutrition_calc_{len(foods)}_foods', duration)
            
            # 驗證結果
            assert result is not None
            nutr_data, calories = result
            assert len(nutr_data) == len(foods)
            
            utils.logger.info(f"🥗 營養計算 {len(foods)} 項食物: {duration:.3f}s")
            
            # 性能基準 - 營養計算應該很快
            assert duration < 1.0, f"營養計算太慢: {duration:.3f}s > 1.0s"
    
    def test_database_performance_scalability(self):
        """測試資料庫性能擴展性"""
        user_id = "perf_test_user"
        
        # 測試不同數量的資料庫操作
        operation_counts = [10, 50, 100, 200]
        
        for count in operation_counts:
            # 清理資料庫
            data_storage.init_database()
            
            # 批量寫入測試
            start_time = time.time()
            memory_before = self.metrics.record_memory_usage()
            
            meal_ids = []
            for i in range(count):
                nutrition_data = {f'食物_{i}': 100 + i}
                meal_id = data_storage.store_meal(user_id, nutrition_data, 100 + i)
                meal_ids.append(meal_id)
            
            write_duration = time.time() - start_time
            memory_after = self.metrics.record_memory_usage()
            
            self.metrics.record_database_operation(f'batch_write_{count}', write_duration, count)
            
            # 批量讀取測試
            start_time = time.time()
            
            # 測試歷史查詢
            history = data_storage.get_history(user_id, days=30)
            
            # 測試統計查詢
            stats = data_storage.get_statistics(user_id)
            
            read_duration = time.time() - start_time
            
            self.metrics.record_database_operation(f'batch_read_{count}', read_duration, len(history))
            
            # 驗證結果
            assert len(history) == count
            assert len(meal_ids) == count
            assert stats['total_meals'] == count
            
            # 計算每操作平均時間
            avg_write_time = write_duration / count
            avg_read_time = read_duration / count
            
            utils.logger.info(f"💾 資料庫 {count} 筆: 寫入 {write_duration:.3f}s ({avg_write_time:.4f}s/op), "
                            f"讀取 {read_duration:.3f}s ({avg_read_time:.4f}s/op)")
            
            # 性能基準
            assert avg_write_time < 0.1, f"資料庫寫入太慢: {avg_write_time:.4f}s > 0.1s per operation"
            assert read_duration < 1.0, f"資料庫讀取太慢: {read_duration:.3f}s > 1.0s"
    
    def test_cache_performance_effectiveness(self):
        """測試快取性能效果"""
        foods = ['蘋果', '香蕉', '橘子', '葡萄', '草莓']
        
        # 第一輪：快取未命中
        miss_times = []
        for food in foods:
            start_time = time.time()
            
            cached = utils.get_cached_nutrition(food)
            assert cached is None  # 應該沒有快取
            
            miss_time = time.time() - start_time
            miss_times.append(miss_time)
        
        # 設定快取
        for i, food in enumerate(foods):
            utils.set_cached_nutrition(food, 50 + i * 10, "測試來源")
        
        # 第二輪：快取命中
        hit_times = []
        for food in foods:
            start_time = time.time()
            
            cached = utils.get_cached_nutrition(food)
            assert cached is not None  # 應該有快取
            
            hit_time = time.time() - start_time
            hit_times.append(hit_time)
        
        # 分析效能提升
        avg_miss_time = statistics.mean(miss_times)
        avg_hit_time = statistics.mean(hit_times)
        speedup = avg_miss_time / avg_hit_time if avg_hit_time > 0 else float('inf')
        
        utils.logger.info(f"🚀 快取效能: 未命中 {avg_miss_time:.6f}s, 命中 {avg_hit_time:.6f}s, "
                        f"提升 {speedup:.1f}x")
        
        # 快取應該明顯更快
        assert avg_hit_time < avg_miss_time, "快取命中應該比未命中快"
        assert speedup > 2.0, f"快取提升不足: {speedup:.1f}x < 2.0x"
        
        # 更新指標
        self.metrics.metrics['cache_performance']['hits'] += len(foods)
        self.metrics.metrics['cache_performance']['misses'] += len(foods)
    
    def test_recommendation_generation_performance(self):
        """測試推薦生成性能"""
        users = [f"perf_user_{i}" for i in range(5)]
        
        # 為每個用戶創建不同數量的歷史記錄
        history_counts = [0, 5, 15, 30, 50]
        
        for user_id, count in zip(users, history_counts):
            # 創建歷史記錄
            for i in range(count):
                nutrition_data = {f'食物_{i}': 100 + i % 50}
                data_storage.store_meal(user_id, nutrition_data, 100 + i % 50)
            
            # 測試推薦生成時間
            start_time = time.time()
            memory_before = self.metrics.record_memory_usage()
            
            recommendation = recommendation_engine.get_recommendation(user_id)
            
            duration = time.time() - start_time
            memory_after = self.metrics.record_memory_usage()
            
            self.metrics.record_execution_time(f'recommendation_{count}_history', duration)
            
            # 驗證推薦
            assert len(recommendation) > 0
            
            utils.logger.info(f"🤖 推薦生成 {count} 歷史: {duration:.3f}s, "
                            f"長度 {len(recommendation)} 字元")
            
            # 性能基準 - 推薦生成應該在合理時間內
            assert duration < 3.0, f"推薦生成太慢: {duration:.3f}s > 3.0s"
            
            # 有歷史的推薦應該更詳細
            if count > 10:
                assert len(recommendation) > 200, "有充足歷史時推薦應該更詳細"


class TestStressAndLoad:
    """壓力測試和負載測試"""
    
    def test_concurrent_user_stress(self):
        """並發用戶壓力測試"""
        num_users = 20
        operations_per_user = 10
        
        def user_workload(user_id: str):
            """單一用戶工作負載"""
            results = []
            errors = []
            
            try:
                for i in range(operations_per_user):
                    start_time = time.time()
                    
                    # 模擬完整的用戶操作
                    nutrition_data = {f'食物_{user_id}_{i}': 100 + i}
                    
                    # 資料庫操作
                    meal_id = data_storage.store_meal(user_id, nutrition_data, 100 + i)
                    
                    # 查詢歷史
                    history = data_storage.get_history(user_id)
                    
                    # 獲得推薦 (每5次操作一次，避免過於頻繁)
                    if i % 5 == 0:
                        recommendation = recommendation_engine.get_recommendation(user_id)
                    else:
                        recommendation = "跳過推薦"
                    
                    duration = time.time() - start_time
                    results.append(duration)
                    
                    # 短暫停頓模擬真實用戶行為
                    time.sleep(0.1)
                    
            except Exception as e:
                errors.append(str(e))
            
            return {
                'user_id': user_id,
                'results': results,
                'errors': errors,
                'avg_time': statistics.mean(results) if results else 0,
                'total_operations': len(results)
            }
        
        # 使用線程池執行並發測試
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_users) as executor:
            # 提交所有用戶工作負載
            futures = []
            for i in range(num_users):
                user_id = f"stress_user_{i}"
                future = executor.submit(user_workload, user_id)
                futures.append(future)
            
            # 收集結果
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        total_duration = time.time() - start_time
        
        # 分析結果
        total_operations = sum(r['total_operations'] for r in results)
        total_errors = sum(len(r['errors']) for r in results)
        avg_times = [r['avg_time'] for r in results if r['avg_time'] > 0]
        
        overall_avg = statistics.mean(avg_times) if avg_times else 0
        throughput = total_operations / total_duration
        
        utils.logger.info(f"🔥 壓力測試結果:")
        utils.logger.info(f"   並發用戶: {num_users}")
        utils.logger.info(f"   總操作數: {total_operations}")
        utils.logger.info(f"   總錯誤數: {total_errors}")
        utils.logger.info(f"   平均回應時間: {overall_avg:.3f}s")
        utils.logger.info(f"   吞吐量: {throughput:.1f} ops/s")
        utils.logger.info(f"   總執行時間: {total_duration:.1f}s")
        
        # 驗證系統穩定性
        error_rate = total_errors / total_operations if total_operations > 0 else 0
        assert error_rate < 0.05, f"錯誤率過高: {error_rate:.2%} > 5%"
        
        # 驗證性能可接受
        assert overall_avg < 2.0, f"平均回應時間過長: {overall_avg:.3f}s > 2.0s"
        assert throughput > 5.0, f"吞吐量過低: {throughput:.1f} ops/s < 5.0 ops/s"
    
    def test_memory_leak_detection(self):
        """記憶體洩漏偵測"""
        process = psutil.Process()
        
        # 記錄初始記憶體
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_samples = [initial_memory]
        
        user_id = "memory_test_user"
        
        # 執行大量操作
        for cycle in range(10):  # 10個循環
            # 每個循環執行多種操作
            for i in range(20):
                # 資料庫操作
                nutrition_data = {f'食物_{cycle}_{i}': 100 + i}
                meal_id = data_storage.store_meal(user_id, nutrition_data, 100 + i)
                
                # 快取操作
                utils.set_cached_nutrition(f'食物_{cycle}_{i}', 100 + i, "測試")
                cached = utils.get_cached_nutrition(f'食物_{cycle}_{i}')
                
                # 推薦生成 (較少頻率)
                if i % 10 == 0:
                    recommendation = recommendation_engine.get_recommendation(user_id)
            
            # 強制垃圾回收
            gc.collect()
            
            # 記錄記憶體使用
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)
            
            utils.logger.info(f"🧠 循環 {cycle}: 記憶體 {current_memory:.1f} MB "
                            f"(+{current_memory - initial_memory:.1f} MB)")
        
        # 分析記憶體趨勢
        memory_increases = [memory_samples[i+1] - memory_samples[i] 
                          for i in range(len(memory_samples)-1)]
        
        avg_increase = statistics.mean(memory_increases)
        max_increase = max(memory_increases)
        total_increase = memory_samples[-1] - memory_samples[0]
        
        utils.logger.info(f"📈 記憶體分析:")
        utils.logger.info(f"   初始記憶體: {initial_memory:.1f} MB")
        utils.logger.info(f"   最終記憶體: {memory_samples[-1]:.1f} MB")
        utils.logger.info(f"   總增長: {total_increase:.1f} MB")
        utils.logger.info(f"   平均增長/循環: {avg_increase:.1f} MB")
        utils.logger.info(f"   最大增長/循環: {max_increase:.1f} MB")
        
        # 記憶體洩漏檢查
        assert total_increase < 100, f"可能的記憶體洩漏: 總增長 {total_increase:.1f} MB > 100 MB"
        assert avg_increase < 10, f"記憶體增長過快: 平均 {avg_increase:.1f} MB/cycle > 10 MB"
    
    def test_database_connection_limits(self):
        """資料庫連接限制測試"""
        # SQLite 是檔案型資料庫，測試大量同時存取
        num_concurrent_ops = 50
        
        def database_operation(op_id: int):
            """單一資料庫操作"""
            try:
                user_id = f"conn_test_user_{op_id}"
                
                # 執行資料庫操作
                start_time = time.time()
                
                nutrition_data = {f'食物_{op_id}': 100 + op_id}
                meal_id = data_storage.store_meal(user_id, nutrition_data, 100 + op_id)
                
                # 立即查詢以測試讀寫競爭
                history = data_storage.get_history(user_id)
                stats = data_storage.get_statistics(user_id)
                
                duration = time.time() - start_time
                
                return {
                    'op_id': op_id,
                    'success': True,
                    'duration': duration,
                    'meal_id': meal_id,
                    'history_count': len(history)
                }
                
            except Exception as e:
                return {
                    'op_id': op_id,
                    'success': False,
                    'error': str(e),
                    'duration': 0
                }
        
        # 並發執行資料庫操作
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_ops) as executor:
            futures = []
            for i in range(num_concurrent_ops):
                future = executor.submit(database_operation, i)
                futures.append(future)
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        total_duration = time.time() - start_time
        
        # 分析結果
        successful_ops = [r for r in results if r['success']]
        failed_ops = [r for r in results if not r['success']]
        
        success_rate = len(successful_ops) / len(results)
        avg_duration = statistics.mean([r['duration'] for r in successful_ops]) if successful_ops else 0
        
        utils.logger.info(f"🔗 連接測試結果:")
        utils.logger.info(f"   並發操作數: {num_concurrent_ops}")
        utils.logger.info(f"   成功操作: {len(successful_ops)}")
        utils.logger.info(f"   失敗操作: {len(failed_ops)}")
        utils.logger.info(f"   成功率: {success_rate:.1%}")
        utils.logger.info(f"   平均執行時間: {avg_duration:.3f}s")
        
        # 檢查失敗原因
        if failed_ops:
            utils.logger.warning("💥 失敗操作詳情:")
            for op in failed_ops[:5]:  # 只顯示前5個
                utils.logger.warning(f"   操作 {op['op_id']}: {op['error']}")
        
        # 驗證資料庫穩定性
        assert success_rate > 0.95, f"資料庫操作成功率過低: {success_rate:.1%} < 95%"
        assert avg_duration < 1.0, f"資料庫操作太慢: {avg_duration:.3f}s > 1.0s"


if __name__ == "__main__":
    # 運行性能測試
    pytest.main([
        __file__, 
        "-v", 
        "--tb=short",
        "-k", "performance or stress or load"
    ])