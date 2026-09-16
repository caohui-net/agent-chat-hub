#!/bin/bash
# 一键安装和配置Agent Chat Hub

set -e  # 遇到错误立即退出

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     Agent Chat Hub - 一键安装和配置脚本                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查Python版本
echo "🔍 检查Python版本..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python版本过低，需要 >= 3.10，当前: $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python版本: $PYTHON_VERSION"
echo ""

# 安装API客户端库
echo "📦 安装API客户端库..."
echo "   这可能需要几分钟时间..."
echo ""

pip3 install --quiet anthropic google-generativeai openai

echo "✅ API客户端库安装完成"
echo ""

# 检查是否已有API密钥
echo "🔑 检查API密钥配置..."
echo ""

HAS_ANTHROPIC=false
HAS_GOOGLE=false
HAS_OPENAI=false

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ ANTHROPIC_API_KEY 已设置"
    HAS_ANTHROPIC=true
else
    echo "⚠️  ANTHROPIC_API_KEY 未设置"
fi

if [ -n "$GOOGLE_API_KEY" ]; then
    echo "✅ GOOGLE_API_KEY 已设置"
    HAS_GOOGLE=true
else
    echo "⚠️  GOOGLE_API_KEY 未设置"
fi

if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OPENAI_API_KEY 已设置"
    HAS_OPENAI=true
else
    echo "⚠️  OPENAI_API_KEY 未设置"
fi

echo ""

# 如果没有任何API密钥，提示用户设置
if [ "$HAS_ANTHROPIC" = false ] && [ "$HAS_GOOGLE" = false ] && [ "$HAS_OPENAI" = false ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  警告: 没有配置任何API密钥"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "要使用Agent Chat Hub，你需要至少配置一个API密钥。"
    echo ""
    echo "推荐：配置 ANTHROPIC_API_KEY（用于Claude模型）"
    echo ""
    echo "配置方法："
    echo "  1. 临时设置（当前会话）："
    echo "     export ANTHROPIC_API_KEY=sk-ant-your-key-here"
    echo ""
    echo "  2. 永久设置（添加到 ~/.bashrc）："
    echo "     echo 'export ANTHROPIC_API_KEY=sk-ant-your-key-here' >> ~/.bashrc"
    echo "     source ~/.bashrc"
    echo ""
    echo "获取API密钥："
    echo "  • Anthropic Claude: https://console.anthropic.com/"
    echo "  • Google Gemini:    https://makersuite.google.com/"
    echo "  • OpenAI GPT:       https://platform.openai.com/"
    echo ""

    read -p "是否现在配置ANTHROPIC_API_KEY? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入你的ANTHROPIC_API_KEY: " ANTHROPIC_KEY

        if [ -n "$ANTHROPIC_KEY" ]; then
            export ANTHROPIC_API_KEY="$ANTHROPIC_KEY"

            # 询问是否永久保存
            read -p "是否永久保存到 ~/.bashrc? (y/n): " -n 1 -r
            echo ""

            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "export ANTHROPIC_API_KEY='$ANTHROPIC_KEY'" >> ~/.bashrc
                echo "✅ API密钥已保存到 ~/.bashrc"
            else
                echo "✅ API密钥已设置（仅当前会话）"
            fi
        fi
    fi
fi

echo ""

# 运行诊断
echo "🔍 运行系统诊断..."
echo ""

python3 diagnose_chat.py

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 安装完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 下一步："
echo ""
echo "  1. 如果还未配置API密钥，请先配置："
echo "     export ANTHROPIC_API_KEY=sk-ant-your-key-here"
echo ""
echo "  2. 启动应用："
echo "     python3 main.py"
echo ""
echo "  3. 在TUI界面中输入消息开始对话"
echo ""
echo "📚 更多信息请查看："
echo "  • CHAT_SOLUTION_SUMMARY.md  - 完整解决方案"
echo "  • QUICK_START.md            - 快速开始指南"
echo "  • INTEGRATION_SUMMARY.md    - 新功能说明"
echo ""
