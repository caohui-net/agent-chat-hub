#!/usr/bin/env python3
"""
快速诊断chat功能的问题
"""
from pathlib import Path
import sys


def check_environment():
    """检查运行环境"""
    print("=" * 60)
    print("环境检查")
    print("=" * 60)

    issues = []

    # 1. 检查Python版本
    import sys
    python_version = sys.version_info
    print(f"✓ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    if python_version < (3, 10):
        issues.append("⚠️ Python版本过低，建议3.10+")

    # 2. 检查必要的包
    required_packages = [
        "textual",
        "anthropic",
        "google.generativeai",
        "openai",
        "pydantic",
        "aiosqlite",
        "structlog",
    ]

    print("\n检查依赖包:")
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - 未安装")
            issues.append(f"缺少依赖: {package}")

    # 3. 检查配置目录
    config_dir = Path.home() / ".agent-chat-hub"
    print(f"\n配置目录: {config_dir}")
    if config_dir.exists():
        print(f"  ✓ 存在")

        # 检查配置文件
        config_file = config_dir / "config.json"
        if config_file.exists():
            print(f"  ✓ config.json 存在")
        else:
            print(f"  ⚠️ config.json 不存在（将使用默认配置）")

        # 检查agents配置
        agents_file = config_dir / "agents.json"
        if agents_file.exists():
            print(f"  ✓ agents.json 存在")

            # 读取并验证agents配置
            import json
            try:
                with open(agents_file) as f:
                    agents_data = json.load(f)
                    print(f"  ✓ agents.json 有效 ({len(agents_data.get('agents', []))} 个agents)")
            except Exception as e:
                print(f"  ✗ agents.json 无效: {e}")
                issues.append(f"agents.json格式错误: {e}")
        else:
            print(f"  ⚠️ agents.json 不存在（将使用默认配置）")
    else:
        print(f"  ⚠️ 不存在（将在首次运行时创建）")

    # 4. 检查API密钥
    print("\nAPI密钥检查:")
    import os

    api_keys = {
        "Anthropic": "ANTHROPIC_API_KEY",
        "Google": "GOOGLE_API_KEY",
        "OpenAI": "OPENAI_API_KEY",
    }

    has_any_key = False
    for service, env_var in api_keys.items():
        if os.environ.get(env_var):
            print(f"  ✓ {service} API密钥已设置")
            has_any_key = True
        else:
            print(f"  ✗ {service} API密钥未设置 ({env_var})")

    if not has_any_key:
        issues.append("⚠️ 没有设置任何API密钥，agents将无法工作")

    # 5. 检查核心模块
    print("\n核心模块检查:")
    core_modules = [
        "src.core.config",
        "src.agents.coordinator",
        "src.agents.executor",
        "src.agents.session",
        "src.tui.app",
        "src.core.agent_context",
        "src.core.agent_status",
        "src.core.retry_policy",
        "src.core.token_tracker",
        "src.core.mention_matcher",
    ]

    for module in core_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except Exception as e:
            print(f"  ✗ {module}: {e}")
            issues.append(f"模块导入失败: {module}")

    return issues


def check_integration():
    """检查新集成的功能"""
    print("\n" + "=" * 60)
    print("新功能集成检查")
    print("=" * 60)

    issues = []

    try:
        from src.core.agent_context import ContextManager
        print("✓ ContextManager (Agent隔离)")
    except Exception as e:
        print(f"✗ ContextManager: {e}")
        issues.append("ContextManager未正确集成")

    try:
        from src.core.agent_status import AgentStatusManager
        print("✓ AgentStatusManager (状态管理)")
    except Exception as e:
        print(f"✗ AgentStatusManager: {e}")
        issues.append("AgentStatusManager未正确集成")

    try:
        from src.core.retry_policy import RetryPolicy
        print("✓ RetryPolicy (重试机制)")
    except Exception as e:
        print(f"✗ RetryPolicy: {e}")
        issues.append("RetryPolicy未正确集成")

    try:
        from src.core.token_tracker import TokenTracker
        print("✓ TokenTracker (Token追踪)")
    except Exception as e:
        print(f"✗ TokenTracker: {e}")
        issues.append("TokenTracker未正确集成")

    try:
        from src.core.mention_matcher import MentionMatcher
        print("✓ MentionMatcher (@mention增强)")
    except Exception as e:
        print(f"✗ MentionMatcher: {e}")
        issues.append("MentionMatcher未正确集成")

    try:
        from src.tui.agent_status_panel import AgentStatusPanel, TokenStatsPanel
        print("✓ AgentStatusPanel & TokenStatsPanel (TUI面板)")
    except Exception as e:
        print(f"✗ TUI面板: {e}")
        issues.append("TUI面板未正确集成")

    return issues


def main():
    """运行诊断"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║          Agent Chat Hub - 快速诊断                            ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    # 环境检查
    env_issues = check_environment()

    # 集成检查
    integration_issues = check_integration()

    # 总结
    all_issues = env_issues + integration_issues

    print("\n" + "=" * 60)
    print("诊断结果")
    print("=" * 60)

    if not all_issues:
        print("\n✅ 所有检查通过！Chat功能应该可以正常使用。")
        print("\n💡 启动方式:")
        print("   1. TUI界面: python3 main.py")
        print("   2. 测试脚本: python3 test_chat_functionality.py")
    else:
        print(f"\n⚠️ 发现 {len(all_issues)} 个问题:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")

        print("\n💡 建议:")
        if any("依赖" in issue for issue in all_issues):
            print("   - 运行: pip install -r requirements.txt")
        if any("API密钥" in issue for issue in all_issues):
            print("   - 设置API密钥:")
            print("     export ANTHROPIC_API_KEY=your_key")
            print("     export GOOGLE_API_KEY=your_key")
            print("     export OPENAI_API_KEY=your_key")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
