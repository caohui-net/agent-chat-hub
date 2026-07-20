"""CLI入口点"""
import sys
import os

# 将项目根目录添加到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from main import main

if __name__ == "__main__":
    main()
