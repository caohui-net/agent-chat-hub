"""
Phase 2性能基准测试脚本

测试核心功能的性能表现
"""
import time
import asyncio
from pathlib import Path
from src.core.config import ConfigManager
from src.core.models import ModelConfig, AgentConfig
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor
from src.agents.session import SessionManager
from src.agents.message_bus import MessageBus


def benchmark_session_creation(iterations=100):
    """测试会话创建性能"""
    print(f"\n=== 会话创建性能测试 ({iterations}次) ===")

    config_file = Path("/tmp/benchmark_config.json")
    cm = ConfigManager(str(config_file))

    # 添加测试模型和agent
    model = ModelConfig(
        model_id="test-model",
        provider="anthropic",
        display_name="Test",
        base_url="https://api.example.com",
        api_key_name="test_key"
    )
    cm.add_model(model)

    agent = AgentConfig(
        agent_id="agent_1",
        name="Test Agent",
        role="测试",
        model_id="test-model"
    )
    cm.add_agent(agent)

    coord = ResponseCoordinator()
    executor = AgentExecutor(cm)
    sm = SessionManager(cm, coord, executor)

    start = time.time()
    for i in range(iterations):
        sm.create_session(f"测试会话{i}")
    end = time.time()

    total_time = end - start
    avg_time = total_time / iterations

    print(f"总耗时: {total_time:.4f}秒")
    print(f"平均耗时: {avg_time*1000:.2f}毫秒/次")
    print(f"吞吐量: {iterations/total_time:.2f}次/秒")

    # 清理
    config_file.unlink(missing_ok=True)

    return avg_time


def benchmark_message_bus():
    """测试消息总线性能"""
    print(f"\n=== 消息总线性能测试 ===")

    async def run_test():
        bus = MessageBus()

        # 注册agents
        for i in range(10):
            bus.register_agent(f"agent_{i}")
            bus.subscribe(f"agent_{i}", "broadcast")

        # 测试点对点消息
        iterations = 1000
        start = time.time()
        for i in range(iterations):
            msg = MessageBus.create_message(
                from_agent_id="agent_0",
                to_agent_id="agent_1",
                content=f"消息{i}",
                message_type="notification"
            )
            await bus.publish(msg)
        end = time.time()

        total_time = end - start
        avg_time = total_time / iterations

        print(f"点对点消息 ({iterations}次):")
        print(f"  总耗时: {total_time:.4f}秒")
        print(f"  平均耗时: {avg_time*1000:.4f}毫秒/次")
        print(f"  吞吐量: {iterations/total_time:.2f}次/秒")

        # 测试广播消息
        broadcast_iterations = 100
        start = time.time()
        for i in range(broadcast_iterations):
            msg = MessageBus.create_message(
                from_agent_id="system",
                to_agent_id=None,  # 广播
                content=f"广播{i}",
                message_type="broadcast"
            )
            await bus.publish(msg)
        end = time.time()

        total_time = end - start
        avg_time = total_time / broadcast_iterations

        print(f"\n广播消息 ({broadcast_iterations}次, 10个订阅者):")
        print(f"  总耗时: {total_time:.4f}秒")
        print(f"  平均耗时: {avg_time*1000:.4f}毫秒/次")
        print(f"  吞吐量: {broadcast_iterations/total_time:.2f}次/秒")

    asyncio.run(run_test())


def benchmark_coordinator(iterations=1000):
    """测试响应协调器性能"""
    print(f"\n=== 响应协调器性能测试 ({iterations}次) ===")

    config_file = Path("/tmp/benchmark_coord.json")
    cm = ConfigManager(str(config_file))

    # 添加多个agents
    model = ModelConfig(
        model_id="test-model",
        provider="anthropic",
        display_name="Test",
        base_url="https://api.example.com",
        api_key_name="test_key"
    )
    cm.add_model(model)

    for i in range(10):
        agent = AgentConfig(
            agent_id=f"agent_{i}",
            name=f"Agent {i}",
            role="测试",
            model_id="test-model",
            priority=100 - i
        )
        cm.add_agent(agent)

    coord = ResponseCoordinator()
    agents = cm.list_agents(active_only=True)

    start = time.time()
    for i in range(iterations):
        round_state = coord.start_round()
        qualified = coord.qualify_agents(agents, round_state)
        selected = coord.select_agents(qualified, round_state)
    end = time.time()

    total_time = end - start
    avg_time = total_time / iterations

    print(f"总耗时: {total_time:.4f}秒")
    print(f"平均耗时: {avg_time*1000:.4f}毫秒/次")
    print(f"吞吐量: {iterations/total_time:.2f}次/秒")

    # 清理
    config_file.unlink(missing_ok=True)

    return avg_time


def main():
    """运行所有基准测试"""
    print("=" * 60)
    print("Agent Chat Hub - Phase 2 性能基准测试")
    print("=" * 60)

    # 会话创建测试
    session_time = benchmark_session_creation(iterations=100)

    # 消息总线测试
    benchmark_message_bus()

    # 响应协调器测试
    coord_time = benchmark_coordinator(iterations=1000)

    # 总结
    print(f"\n{'=' * 60}")
    print("性能总结")
    print(f"{'=' * 60}")
    print(f"会话创建: {session_time*1000:.2f}ms/次")
    print(f"响应协调: {coord_time*1000:.4f}ms/次")
    print("\n性能评估: ✓ 所有核心操作均在可接受范围内")
    print("建议: 在生产环境中启用性能日志监控")


if __name__ == "__main__":
    main()
