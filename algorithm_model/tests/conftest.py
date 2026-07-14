"""
pytest 配置 - 确保正确导入路径
"""
import sys
import os

# 添加 algorithm_model 根目录到 path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
