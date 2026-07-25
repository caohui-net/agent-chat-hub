#!/bin/bash
# agent-chat-hub 启动脚本
# 自动激活虚拟环境并启动应用

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "错误: 虚拟环境不存在，请先运行: python3 -m venv venv && source venv/bin/activate && pip install -e ."
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 启动应用
python main.py
