#!/usr/bin/env python3
"""
Diet Tracker Bot - 測試執行腳本
=============================

統一的測試執行介面，提供不同類型和等級的測試選項。
支援單元測試、整合測試、性能測試、完整測試套件等。

使用方式：
    python run_tests.py --help                 # 顯示所有選項
    python run_tests.py --unit                 # 只運行單元測試
    python run_tests.py --integration          # 只運行整合測試
    python run_tests.py --performance          # 只運行性能測試
    python run_tests.py --e2e                  # 只運行端到端測試
    python run_tests.py --all                  # 運行所有測試
    python run_tests.py --fast                 # 快速測試 (跳過慢速測試)
    python run_tests.py --coverage             # 生成覆蓋率報告
    python run_tests.py --verbose              # 詳細輸出

設計目標：
- 提供簡單易用的測試介面
- 支援不同測試場景和需求
- 生成清晰的測試報告
- 整合覆蓋率分析
- 性能基準驗證
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from datetime import datetime
import platform

# 添加src目錄到Python路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

import utils

class TestRunner:
    """測試執行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test_reports"
        
        # 確保報告目錄存在
        self.reports_dir.mkdir(exist_ok=True)
        
        # 設定日誌
        self.logger = utils.setup_logging("INFO")
    
    def run_command(self, cmd: list, capture_output: bool = False) -> tuple:
        """執行命令並返回結果"""
        self.logger.info(f"🚀 執行命令: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            if capture_output:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    cwd=self.project_root
                )
                success = result.returncode == 0
                output = result.stdout + result.stderr
            else:
                result = subprocess.run(cmd, cwd=self.project_root)
                success = result.returncode == 0
                output = ""
            
            duration = time.time() - start_time
            
            if success:
                self.logger.info(f"✅ 命令執行成功 (耗時 {duration:.1f}s)")
            else:
                self.logger.error(f"❌ 命令執行失敗 (耗時 {duration:.1f}s)")
                if output:
                    self.logger.error(f"錯誤輸出: {output[:500]}...")
            
            return success, output, duration
            
        except Exception as e:
            self.logger.error(f"💥 命令執行異常: {e}")
            return False, str(e), 0
    
    def check_dependencies(self) -> bool:
        """檢查測試依賴"""
        self.logger.info("🔍 檢查測試依賴...")
        
        # 檢查 pytest 是否可用
        success, _, _ = self.run_command(["python", "-m", "pytest", "--version"], capture_output=True)
        if not success:
            self.logger.error("❌ pytest 未安裝，請先安裝: pip install pytest")
            return False
        
        # 檢查其他依賴
        required_packages = [
            "pytest-cov",
            "pytest-asyncio", 
            "psutil",
            "numpy",
            "pillow"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.logger.warning(f"⚠️  缺少測試依賴: {missing_packages}")
            self.logger.info("💡 建議安裝: pip install " + " ".join(missing_packages))
        
        return True
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = False) -> tuple:
        """運行單元測試"""
        self.logger.info("🧪 運行單元測試...")
        
        cmd = [
            "python", "-m", "pytest", 
            "tests/test_utils.py",
            "tests/test_image_processor.py", 
            "tests/test_nutrition_calculator.py",
            "tests/test_data_storage.py",
            "tests/test_recommendation_engine.py",
            "-m", "unit",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=html:test_reports/unit_coverage",
                "--cov-report=xml:test_reports/unit_coverage.xml"
            ])
        
        return self.run_command(cmd)
    
    def run_integration_tests(self, verbose: bool = False, coverage: bool = False) -> tuple:
        """運行整合測試"""
        self.logger.info("🔗 運行整合測試...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_discord_bot.py",
            "tests/test_main.py", 
            "-m", "integration",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
            
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=html:test_reports/integration_coverage",
                "--cov-report=xml:test_reports/integration_coverage.xml"
            ])
        
        return self.run_command(cmd)
    
    def run_e2e_tests(self, verbose: bool = False) -> tuple:
        """運行端到端測試"""
        self.logger.info("🎯 運行端到端測試...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_end_to_end.py",
            "-m", "e2e",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd)
    
    def run_performance_tests(self, verbose: bool = False) -> tuple:
        """運行性能測試"""
        self.logger.info("⚡ 運行性能測試...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py",
            "-m", "performance",
            "--tb=line"  # 性能測試用更簡潔的輸出
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd)
    
    def run_all_tests(self, verbose: bool = False, coverage: bool = False, 
                     skip_slow: bool = False) -> tuple:
        """運行所有測試"""
        self.logger.info("🚀 運行完整測試套件...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        if skip_slow:
            cmd.extend(["-m", "not slow"])
        
        if coverage:
            cmd.extend([
                "--cov=src",
                "--cov-report=html:test_reports/full_coverage",
                "--cov-report=xml:test_reports/full_coverage.xml",
                "--cov-report=term-missing"
            ])
        
        return self.run_command(cmd)
    
    def run_fast_tests(self, verbose: bool = False) -> tuple:
        """運行快速測試 (跳過慢速和外部依賴測試)"""
        self.logger.info("⚡ 運行快速測試...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/",
            "-m", "not slow and not external",
            "--tb=short"
        ]
        
        if verbose:
            cmd.append("-v")
        
        return self.run_command(cmd)
    
    def generate_test_report(self, results: dict):
        """生成測試報告"""
        self.logger.info("📊 生成測試報告...")
        
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_file = self.reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# Diet Tracker Bot 測試報告\n\n")
            f.write(f"**報告時間:** {report_time}\n")
            f.write(f"**系統環境:** {platform.system()} {platform.release()}\n")
            f.write(f"**Python 版本:** {sys.version}\n\n")
            
            f.write(f"## 測試結果摘要\n\n")
            
            total_passed = 0
            total_failed = 0
            total_duration = 0
            
            for test_type, (success, output, duration) in results.items():
                status = "✅ 通過" if success else "❌ 失敗"
                f.write(f"- **{test_type}:** {status} (耗時: {duration:.1f}s)\n")
                
                if success:
                    total_passed += 1
                else:
                    total_failed += 1
                
                total_duration += duration
            
            f.write(f"\n**總計:** {total_passed} 通過, {total_failed} 失敗, 總耗時: {total_duration:.1f}s\n\n")
            
            # 詳細結果
            f.write(f"## 詳細測試結果\n\n")
            for test_type, (success, output, duration) in results.items():
                f.write(f"### {test_type}\n")
                f.write(f"- **狀態:** {'通過' if success else '失敗'}\n")
                f.write(f"- **執行時間:** {duration:.1f}s\n")
                
                if not success and output:
                    f.write(f"- **錯誤輸出:**\n```\n{output[:1000]}...\n```\n")
                
                f.write("\n")
        
        self.logger.info(f"📄 測試報告已儲存: {report_file}")
        return report_file
    
    def check_system_environment(self):
        """檢查系統環境"""
        self.logger.info("🔍 檢查系統環境...")
        
        # 檢查 Python 版本
        python_version = sys.version_info
        self.logger.info(f"🐍 Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        if python_version < (3, 8):
            self.logger.warning("⚠️  建議使用 Python 3.8 或更高版本")
        
        # 檢查可用記憶體
        try:
            import psutil
            memory = psutil.virtual_memory()
            self.logger.info(f"💾 系統記憶體: {memory.total / (1024**3):.1f}GB (可用: {memory.available / (1024**3):.1f}GB)")
            
            if memory.available < 1 * (1024**3):  # 1GB
                self.logger.warning("⚠️  可用記憶體較少，可能影響測試性能")
        except ImportError:
            pass
        
        # 檢查專案結構
        required_dirs = ['src', 'tests', 'config']
        missing_dirs = []
        
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            self.logger.error(f"❌ 缺少必要目錄: {missing_dirs}")
            return False
        
        # 檢查核心模組
        core_modules = [
            'src/utils.py',
            'src/image_processor.py', 
            'src/nutrition_calculator.py',
            'src/data_storage.py',
            'src/recommendation_engine.py',
            'src/discord_bot.py',
            'src/main.py'
        ]
        
        missing_modules = []
        for module_path in core_modules:
            if not (self.project_root / module_path).exists():
                missing_modules.append(module_path)
        
        if missing_modules:
            self.logger.error(f"❌ 缺少核心模組: {missing_modules}")
            return False
        
        self.logger.info("✅ 系統環境檢查通過")
        return True


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="Diet Tracker Bot 測試執行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
測試類型說明：
  --unit        單元測試 - 測試個別函數和類別
  --integration 整合測試 - 測試模組間交互
  --e2e         端到端測試 - 測試完整用戶流程
  --performance 性能測試 - 測試執行速度和資源使用
  --all         所有測試 - 完整測試套件
  --fast        快速測試 - 跳過慢速測試

範例用法：
  python run_tests.py --unit --verbose           # 詳細運行單元測試
  python run_tests.py --all --coverage          # 運行所有測試並生成覆蓋率
  python run_tests.py --fast                    # 快速測試（開發時使用）
  python run_tests.py --performance             # 只運行性能測試
        """
    )
    
    # 測試類型選項
    test_group = parser.add_argument_group('測試類型')
    test_group.add_argument('--unit', action='store_true', help='運行單元測試')
    test_group.add_argument('--integration', action='store_true', help='運行整合測試')
    test_group.add_argument('--e2e', action='store_true', help='運行端到端測試')
    test_group.add_argument('--performance', action='store_true', help='運行性能測試')
    test_group.add_argument('--all', action='store_true', help='運行所有測試')
    test_group.add_argument('--fast', action='store_true', help='運行快速測試')
    
    # 選項
    options_group = parser.add_argument_group('選項')
    options_group.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
    options_group.add_argument('--coverage', '-c', action='store_true', help='生成覆蓋率報告')
    options_group.add_argument('--no-report', action='store_true', help='不生成測試報告')
    options_group.add_argument('--skip-env-check', action='store_true', help='跳過環境檢查')
    
    args = parser.parse_args()
    
    # 如果沒有指定測試類型，預設運行快速測試
    if not any([args.unit, args.integration, args.e2e, args.performance, args.all, args.fast]):
        args.fast = True
        print("💡 未指定測試類型，預設運行快速測試。使用 --help 查看所有選項。\n")
    
    # 創建測試執行器
    runner = TestRunner()
    
    # 檢查環境
    if not args.skip_env_check:
        if not runner.check_system_environment():
            print("❌ 系統環境檢查失敗")
            return 1
        
        if not runner.check_dependencies():
            print("❌ 依賴檢查失敗")
            return 1
    
    # 執行測試
    results = {}
    overall_success = True
    
    try:
        if args.unit:
            success, output, duration = runner.run_unit_tests(args.verbose, args.coverage)
            results['單元測試'] = (success, output, duration)
            overall_success &= success
        
        if args.integration:
            success, output, duration = runner.run_integration_tests(args.verbose, args.coverage)
            results['整合測試'] = (success, output, duration)
            overall_success &= success
        
        if args.e2e:
            success, output, duration = runner.run_e2e_tests(args.verbose)
            results['端到端測試'] = (success, output, duration)
            overall_success &= success
        
        if args.performance:
            success, output, duration = runner.run_performance_tests(args.verbose)
            results['性能測試'] = (success, output, duration)
            overall_success &= success
        
        if args.all:
            success, output, duration = runner.run_all_tests(args.verbose, args.coverage, False)
            results['完整測試'] = (success, output, duration)
            overall_success &= success
        
        if args.fast:
            success, output, duration = runner.run_fast_tests(args.verbose)
            results['快速測試'] = (success, output, duration)
            overall_success &= success
        
    except KeyboardInterrupt:
        print("\n⏹️  測試被用戶中斷")
        return 1
    except Exception as e:
        print(f"💥 測試執行異常: {e}")
        return 1
    
    # 生成報告
    if results and not args.no_report:
        try:
            runner.generate_test_report(results)
        except Exception as e:
            print(f"⚠️  生成報告失敗: {e}")
    
    # 輸出結果摘要
    if results:
        print("\n" + "="*60)
        print("📊 測試結果摘要")
        print("="*60)
        
        for test_type, (success, _, duration) in results.items():
            status = "✅ 通過" if success else "❌ 失敗"
            print(f"{test_type}: {status} (耗時: {duration:.1f}s)")
        
        if overall_success:
            print("\n🎉 所有測試通過！")
        else:
            print("\n💥 部分測試失敗，請檢查詳細輸出")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())