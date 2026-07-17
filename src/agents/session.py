"""
会话管理器 - 管理对话历史和会话状态
"""
from typing import List, Optional
from time import time
from pathlib import Path
import json
import structlog

from src.core.models import SessionConfig, Message, AgentConfig
from src.core.config import ConfigManager
from src.agents.coordinator import ResponseCoordinator
from src.agents.executor import AgentExecutor

logger = structlog.get_logger()


class SessionManager:
    """
    会话管理器

    职责：
    - 管理对话历史
    - 协调agent响应
    - 持久化会话状态
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        coordinator: ResponseCoordinator,
        executor: AgentExecutor,
        session_dir: Optional[Path] = None
    ):
        """初始化会话管理器

        Args:
            config_manager: 配置管理器
            coordinator: 响应协调器
            executor: Agent执行器
            session_dir: 会话存储目录
        """
        self.config_manager = config_manager
        self.coordinator = coordinator
        self.executor = executor
        self.session_dir = session_dir or Path.home() / ".agent-chat-hub" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.current_session: Optional[SessionConfig] = None
        self.current_round = 0

    def create_session(self, title: str = "新对话") -> SessionConfig:
        """创建新会话

        Args:
            title: 会话标题

        Returns:
            新创建的会话配置
        """
        session_id = f"session_{int(time() * 1000)}"
        session = SessionConfig(
            session_id=session_id,
            title=title,
            created_at=time(),
            updated_at=time(),
        )
        self.current_session = session
        self.current_round = 0

        logger.info("session_created", session_id=session_id, title=title)
        return session

    def add_message(self, role: str, content: str, agent_id: Optional[str] = None) -> None:
        """添加消息到当前会话

        Args:
            role: 消息角色 (user/assistant/system)
            content: 消息内容
            agent_id: Agent ID (如果是assistant消息)
        """
        if not self.current_session:
            raise ValueError("没有活动会话")

        message = Message(
            role=role,
            content=content,
            agent_id=agent_id,
            timestamp=time()
        )
        self.current_session.messages.append(message)
        self.current_session.updated_at = time()

    def process_user_input(self, user_input: str) -> List[str]:
        """处理用户输入并获取agent响应

        Args:
            user_input: 用户输入内容

        Returns:
            Agent响应列表

        Raises:
            ValueError: 会话或agent配置错误
        """
        if not self.current_session:
            raise ValueError("没有活动会话")

        # 添加用户消息
        self.add_message(role="user", content=user_input)

        # 开始新一轮
        self.current_round += 1
        self.coordinator.start_round(
            session_id=self.current_session.session_id,
            round_num=self.current_round
        )

        # 获取所有可用的agents
        available_agents = self.config_manager.list_agents(active_only=True)
        if not available_agents:
            logger.warning("no_active_agents")
            return ["错误：没有可用的agent"]

        # 使用协调器选择agents
        selected_agents, stop_reason = self.coordinator.select_agents(available_agents)

        if stop_reason:
            logger.info("round_stopped", reason=stop_reason.value)
            return [f"对话已停止：{stop_reason.value}"]

        responses = []
        for agent_config in selected_agents:
            try:
                # 执行agent调用
                response = self.executor.execute(
                    agent_config,
                    self.current_session.messages
                )

                # 记录调用（估算token数）
                estimated_tokens = len(user_input) + len(response)
                self.coordinator.record_call(
                    agent_config.agent_id,
                    tokens_used=estimated_tokens
                )

                # 添加assistant消息
                self.add_message(
                    role="assistant",
                    content=response,
                    agent_id=agent_config.agent_id
                )

                responses.append(f"[{agent_config.name}]\n{response}")

                logger.info(
                    "agent_responded",
                    agent_id=agent_config.agent_id,
                    response_length=len(response)
                )

            except Exception as e:
                error_msg = f"Agent {agent_config.name} 执行失败: {e}"
                logger.error("agent_execution_failed", agent_id=agent_config.agent_id, error=str(e))
                responses.append(f"[{agent_config.name}] ❌ {error_msg}")

        # 标记轮次完成
        self.coordinator.mark_round_complete()

        return responses

    def save_session(self) -> None:
        """保存当前会话到磁盘"""
        if not self.current_session:
            return

        session_file = self.session_dir / f"{self.current_session.session_id}.json"

        # 转换为字典
        session_dict = {
            "session_id": self.current_session.session_id,
            "title": self.current_session.title,
            "active_agent_ids": self.current_session.active_agent_ids,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "agent_id": msg.agent_id,
                    "timestamp": msg.timestamp
                }
                for msg in self.current_session.messages
            ],
            "created_at": self.current_session.created_at,
            "updated_at": self.current_session.updated_at,
        }

        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_dict, f, ensure_ascii=False, indent=2)

        logger.info("session_saved", session_id=self.current_session.session_id, file=str(session_file))

    def load_session(self, session_id: str) -> SessionConfig:
        """从磁盘加载会话

        Args:
            session_id: 会话ID

        Returns:
            加载的会话配置

        Raises:
            FileNotFoundError: 会话文件不存在
        """
        session_file = self.session_dir / f"{session_id}.json"

        if not session_file.exists():
            raise FileNotFoundError(f"会话不存在: {session_id}")

        with open(session_file, 'r', encoding='utf-8') as f:
            session_dict = json.load(f)

        # 重建Message对象
        messages = [
            Message(
                role=msg["role"],
                content=msg["content"],
                agent_id=msg.get("agent_id"),
                timestamp=msg["timestamp"]
            )
            for msg in session_dict["messages"]
        ]

        # 重建SessionConfig对象
        session = SessionConfig(
            session_id=session_dict["session_id"],
            title=session_dict["title"],
            active_agent_ids=session_dict.get("active_agent_ids", []),
            messages=messages,
            created_at=session_dict["created_at"],
            updated_at=session_dict["updated_at"],
        )

        self.current_session = session
        self.current_round = len([m for m in messages if m.role == "user"])

        logger.info("session_loaded", session_id=session_id, message_count=len(messages))
        return session

    def get_message_history(self) -> List[str]:
        """获取格式化的对话历史

        Returns:
            格式化的消息列表
        """
        if not self.current_session:
            return []

        history = []
        for msg in self.current_session.messages:
            if msg.role == "user":
                history.append(f"👤 用户: {msg.content}")
            elif msg.role == "assistant":
                agent_name = msg.agent_id or "Agent"
                history.append(f"🤖 {agent_name}: {msg.content}")

        return history
