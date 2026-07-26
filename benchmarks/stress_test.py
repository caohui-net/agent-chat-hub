"""
压力测试脚本 - 模拟高并发场景

测试场景：
1. 并发会话创建（100个用户）
2. 高频消息发送（持续5分钟）
3. 多Agent同时响应
"""
import time
import asyncio
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from src.core.config import ConfigManager
from src.core.models import ModelConfig, AgentConfig
from src.agents.coordinator import ResponseCoordinator, BudgetLimits
from src.agents.session import SessionManager

# 测试配置
NUM_CONCURRENT_USERS = 100
TEST_DURATION_SECONDS = 300  # 5分钟
MESSAGE_RATE_PER_USER = 0.5  # 每个用户每秒发送0.5条消息

# 性能监控
class PerformanceMonitor:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.errors = []
        self.lock = threading.Lock()

    def record_request(self, success: bool, response_time: float, error: str = None):
        with self.lock:
            self.total_requests += 1
            if success:
                self.successful_requests += 1
                self.response_times.append(response_time)
            else:
                self.failed_requests += 1
                if error:
                    self.errors.append(error)

    def get_stats(self):
        with self.lock:
            if not self.response_times:
                return {
                    "total_requests": self.total_requests,
                    "successful": self.successful_requests,
                    "failed": self.failed_requests,
                    "avg_response_time": 0,
                    "p50_response_time": 0,
                    "p95_response_time": 0,
                    "p99_response_time": 0,
                    "error_rate": 100.0 if self.total_requests > 0 else 0
                }

            sorted_times = sorted(self.response_times)
            n = len(sorted_times)

            return {
                "total_requests": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests,
                "avg_response_time": sum(sorted_times) / n,
                "p50_response_time": sorted_times[int(n * 0.5)],
                "p95_response_time": sorted_times[int(n * 0.95)],
                "p99_response_time": sorted_times[int(n * 0.99)],
                "error_rate": (self.failed_requests / self.total_requests) * 100
            }

monitor = PerformanceMonitor()

def simulate_user(user_id: int, duration: int):
    """模拟单个用户的行为"""
    config_dir = Path(f"/tmp/stress_test_user_{user_id}")
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 创建配置管理器
        config_manager = ConfigManager(config_dir)

        # 添加测试模型
        model = ModelConfig(
            model_id="test-model",
            provider="anthropic",
            display_name="Test Model",
            base_url="https://api.example.com",
            api_key_name="test_key"
        )
        config_manager.add_model(model)

        # 添加测试Agent
        agent = AgentConfig(
            agent_id=f"agent_{user_id}",
            name=f"Agent {user_id}",
            role="测试助手",
            role_type="coordinator",
            model_id="test-model",
            priority=100,
            active=True
        )
        config_manager.add_agent(agent)

        # 创建会话
        start_time = time.time()
        success = True
        error = None

        try:
            session_manager = SessionManager(config_manager)
            session = session_manager.create_session(f"User {user_id} Session")

            # 模拟消息发送
            messages_sent = 0
            while time.time() - start_time < duration:
                msg_start = time.time()
                try:
                    session_manager.add_message("user", f"Message {messages_sent} from user {user_id}")
                    messages_sent += 1
                    msg_time = time.time() - msg_start
                    monitor.record_request(True, msg_time)
                except Exception as e:
                    monitor.record_request(False, 0, str(e))

                # 控制消息发送速率
                time.sleep(1.0 / MESSAGE_RATE_PER_USER)

        except Exception as e:
            success = False
            error = str(e)
            monitor.record_request(False, time.time() - start_time, error)

    finally:
        # 清理临时配置
        import shutil
        if config_dir.exists():
            shutil.rmtree(config_dir, ignore_errors=True)

def stress_test_concurrent_sessions():
    """测试1：并发会话创建"""
    print("\n=== 压力测试：并发会话创建 ===")
    print(f"并发用户数: {NUM_CONCURRENT_USERS}")
    print(f"测试时长: {TEST_DURATION_SECONDS}秒")

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT_USERS) as executor:
        futures = [
            executor.submit(simulate_user, i, TEST_DURATION_SECONDS)
            for i in range(NUM_CONCURRENT_USERS)
        ]

        # 等待所有任务完成
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"用户任务失败: {e}")

    elapsed = time.time() - start_time
    stats = monitor.get_stats()

    print(f"\n总耗时: {elapsed:.2f}秒")
    print(f"总请求数: {stats['total_requests']}")
    print(f"成功: {stats['successful']}")
    print(f"失败: {stats['failed']}")
    print(f"错误率: {stats['error_rate']:.2f}%")
    print(f"平均响应时间: {stats['avg_response_time']*1000:.2f}ms")
    print(f"P50响应时间: {stats['p50_response_time']*1000:.2f}ms")
    print(f"P95响应时间: {stats['p95_response_time']*1000:.2f}ms")
    print(f"P99响应时间: {stats['p99_response_time']*1000:.2f}ms")
    print(f"吞吐量: {stats['successful']/elapsed:.2f}次/秒")

    return stats

def main():
    print("=" * 60)
    print("Agent Chat Hub - 压力测试")
    print("=" * 60)

    # 运行压力测试
    stats = stress_test_concurrent_sessions()

    print("\n" + "=" * 60)
    print("压力测试完成")
    print("=" * 60)

    # 性能评估
    if stats['error_rate'] < 1.0:
        print("✅ 系统稳定性：优秀")
    elif stats['error_rate'] < 5.0:
        print("⚠️  系统稳定性：良好")
    else:
        print("❌ 系统稳定性：需要优化")

    if stats['p95_response_time'] < 0.1:
        print("✅ 响应性能：优秀")
    elif stats['p95_response_time'] < 0.5:
        print("⚠️  响应性能：良好")
    else:
        print("❌ 响应性能：需要优化")

if __name__ == "__main__":
    main()
