"""
Diet Tracker Discord Bot - 安裝設定檔
===================================

這個檔案用於專案的打包和分發，允許使用pip安裝這個專案。

安裝方式：
1. 開發模式安裝：pip install -e .
2. 正常安裝：pip install .

未來可用於：
- 創建wheel分發包
- 上傳到PyPI
- 在其他專案中作為依賴使用
"""

from setuptools import setup, find_packages
from pathlib import Path

# 讀取README檔案作為長描述
this_directory = Path(__file__).parent
long_description = (this_directory / "docs" / "README.md").read_text(encoding='utf-8')

# 讀取requirements.txt中的依賴
with open('requirements.txt') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="diet-tracker-discord-bot",
    version="1.0.0",
    author="Food Nutritionist Team",
    author_email="your-email@example.com",
    description="一個基於AI的Discord飲食追蹤機器人",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/diet-tracker-bot",
    
    # 套件配置
    packages=find_packages(),
    include_package_data=True,
    
    # Python版本要求
    python_requires=">=3.11",
    
    # 依賴套件
    install_requires=requirements,
    
    # 額外依賴群組
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-asyncio>=0.21.1',
            'pytest-cov>=4.1.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.5.0',
        ],
        'production': [
            'gunicorn>=21.0.0',  # 如果需要Web介面
            'sentry-sdk>=1.30.0',  # 錯誤追蹤
        ],
    },
    
    # 專案分類
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    
    # 關鍵字
    keywords="discord bot nutrition diet tracking ai food recognition",
    
    # 專案首頁
    project_urls={
        "Bug Reports": "https://github.com/yourusername/diet-tracker-bot/issues",
        "Source": "https://github.com/yourusername/diet-tracker-bot",
        "Documentation": "https://diet-tracker-bot.readthedocs.io/",
    },
    
    # 命令行入口點 (未來實現)
    entry_points={
        'console_scripts': [
            'diet-tracker-bot=src.main:main',
        ],
    },
    
    # 包含非Python檔案
    package_data={
        'src': ['data/*.jsonl', 'config/*.env.template'],
    },
    
    # 專案資料檔案
    data_files=[
        ('config', ['config/.env']),
        ('data', ['data/tfnd_clean.jsonl']),
    ],
    
    # 支援zip_safe=False以確保資料檔案正確載入
    zip_safe=False,
)