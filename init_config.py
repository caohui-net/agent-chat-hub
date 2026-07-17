#!/usr/bin/env python3
"""
配置初始化脚本 - 帮助用户快速配置第一个agent
"""
import sys
from pathlib import Path

from src.core.config import ConfigManager
from src.core.models import ModelConfig, AgentConfig


def init_config():
    """初始化配置"""
    print("=== Agent Chat Hub 配置初始化 ===\n")

    config_dir = Path.home() / ".agent-chat-hub"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_manager = ConfigManager(config_dir=config_dir)
    config_manager.load_configs()

    # 检查是否已有配置
    if config_manager.list_models() and config_manager.list_agents():
        print("✓ 配置已存在")
        print(f"  - 模型数: {len(config_manager.list_models())}")
        print(f"  - Agent数: {len(config_manager.list_agents())}")
        print("\n使用 'python main.py' 启动应用")
        return

    print("首次运行，需要配置至少一个模型和agent\n")

    # 1. 配置模型
    print("1. 配置模型")
    print("   支持的provider: anthropic, openai")
    provider = input("   选择provider (anthropic/openai) [anthropic]: ").strip() or "anthropic"

    if provider == "anthropic":
        model_id = input("   模型ID [claude-3-5-sonnet-20241022]: ").strip() or "claude-3-5-sonnet-20241022"
        base_url = "https://api.anthropic.com"
        api_key_name = "anthropic_api_key"
    else:
        model_id = input("   模型ID [gpt-4]: ").strip() or "gpt-4"
        base_url = "https://api.openai.com"
        api_key_name = "openai_api_key"

    print(f"\n   请输入 {provider} API密钥:")
    api_key = input("   API Key: ").strip()

    if not api_key:
        print("   ✗ API密钥不能为空")
        sys.exit(1)

    # 保存API密钥到keyring
    config_manager.set_api_key(api_key_name, api_key)
    print(f"   ✓ API密钥已保存到系统密钥环")

    # 添加模型配置
    model_config = ModelConfig(
        model_id=model_id,
        provider=provider,
        display_name=f"{provider.title()} - {model_id}",
        base_url=base_url,
        api_key_name=api_key_name,
        max_tokens=4096,
        temperature=1.0,
    )
    config_manager.add_model(model_config)
    print(f"   ✓ 模型配置已添加: {model_id}")

    # 2. 配置Agent
    print("\n2. 配置Agent")
    agent_name = input("   Agent名称 [助手]: ").strip() or "助手"
    agent_role = input("   Agent角色 [assistant]: ").strip() or "assistant"

    agent_config = AgentConfig(
        agent_id="agent_default",
        name=agent_name,
        role=agent_role,
        model_id=model_id,
        priority=100,
        active=True,
        system_prompt="你是一个有帮助的AI助手。"
    )
    config_manager.add_agent(agent_config)
    print(f"   ✓ Agent配置已添加: {agent_name}")

    # 保存配置
    config_manager.save_configs()
    print(f"\n✓ 配置已保存到: {config_dir}")
    print("\n使用 'python main.py' 启动应用")


if __name__ == "__main__":
    try:
        init_config()
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        sys.exit(1)
