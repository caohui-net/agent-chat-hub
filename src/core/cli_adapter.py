"""
通过CLI调用AI服务的适配器
支持: claude, codex, gemini CLI工具
"""
import asyncio
import json
import structlog
from typing import List, Dict, Optional
from pathlib import Path
import shutil

logger = structlog.get_logger()


class CLIAdapter:
    """CLI工具适配器 - 通过命令行调用AI服务"""

    def __init__(self):
        """初始化适配器并检查CLI工具可用性"""
        self.available_clis = self._check_available_clis()
        logger.info("cli_adapter_initialized", available=self.available_clis)

    def _check_available_clis(self) -> Dict[str, bool]:
        """检查哪些CLI工具可用"""
        return {
            "claude": shutil.which("claude") is not None,
            "codex": shutil.which("codex") is not None,
            "gemini": shutil.which("gemini") is not None,
        }

    def is_available(self, provider: str) -> bool:
        """检查指定provider的CLI是否可用

        Args:
            provider: 'anthropic', 'openai', 'gemini' 等

        Returns:
            CLI工具是否可用
        """
        cli_map = {
            "anthropic": "claude",
            "openai": "codex",
            "gemini": "gemini",
            "gemini-http": "gemini",
        }
        cli_name = cli_map.get(provider)
        return self.available_clis.get(cli_name, False)

    async def call_claude(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        model: str = "claude-opus-4-8",
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> tuple[str, Dict]:
        """通过Claude CLI调用Claude模型

        Args:
            messages: 消息列表
            system_prompt: 系统提示词
            model: 模型ID
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            (响应内容, token使用统计)
        """
        # 构建提示词（将消息合并）
        prompt = self._build_prompt(messages)

        # 如果有系统提示词，加到prompt开头
        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"

        # 构建命令 - 使用 -p/--print 进行非交互式输出
        cmd = ["claude", "-p", prompt, "--model", model]

        logger.info("calling_claude_cli", command=" ".join(cmd[:2]))

        try:
            # 执行命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error("claude_cli_failed", error=error_msg)
                raise Exception(f"Claude CLI调用失败: {error_msg}")

            response = stdout.decode('utf-8').strip()

            # CLI不返回token统计，使用估算
            token_usage = self._estimate_tokens(prompt, response)

            return response, token_usage

        except Exception as e:
            logger.error("claude_cli_error", error=str(e))
            raise

    async def call_codex(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        model: str = "gpt-5.6-sol",
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> tuple[str, Dict]:
        """通过Codex CLI调用OpenAI模型

        Args:
            messages: 消息列表
            system_prompt: 系统提示词
            model: 模型ID
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            (响应内容, token使用统计)
        """
        # 构建提示词
        prompt = self._build_prompt(messages)

        # Codex将system prompt加到prompt前
        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"

        # 构建命令 - codex exec 需要prompt作为参数
        cmd = ["codex", "exec", "--model", model, prompt]

        logger.info("calling_codex_cli", command=" ".join(cmd[:4]))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL  # 明确不使用stdin
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error("codex_cli_failed", error=error_msg, returncode=process.returncode)
                raise Exception(f"Codex CLI调用失败 (code {process.returncode}): {error_msg}")

            response = stdout.decode('utf-8').strip()

            # 如果响应为空，记录警告
            if not response:
                logger.warning("codex_cli_empty_response", stderr=stderr.decode('utf-8'))
                response = "[Codex无响应]"

            token_usage = self._estimate_tokens(prompt, response)

            return response, token_usage

        except Exception as e:
            logger.error("codex_cli_error", error=str(e))
            raise

    async def call_gemini(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        model: str = "gemini-3.1-pro-preview",
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> tuple[str, Dict]:
        """通过Gemini CLI调用Gemini模型

        Args:
            messages: 消息列表
            system_prompt: 系统提示词
            model: 模型ID
            max_tokens: 最大token数
            temperature: 温度参数

        Returns:
            (响应内容, token使用统计)
        """
        # 构建提示词
        prompt = self._build_prompt(messages)

        # Gemini将system prompt加到prompt前
        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"

        # 构建命令 - 使用 -p/--prompt 进行非交互式输出
        cmd = ["gemini", "-p", prompt, "--model", model]

        logger.info("calling_gemini_cli", command=" ".join(cmd[:2]))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error("gemini_cli_failed", error=error_msg)
                raise Exception(f"Gemini CLI调用失败: {error_msg}")

            response = stdout.decode('utf-8').strip()
            token_usage = self._estimate_tokens(prompt, response)

            return response, token_usage

        except Exception as e:
            logger.error("gemini_cli_error", error=str(e))
            raise

    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        """将消息列表合并为单个提示词

        Args:
            messages: 消息列表

        Returns:
            合并后的提示词
        """
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                parts.append(f"User: {content}")
            elif role == "assistant":
                parts.append(f"Assistant: {content}")

        return "\n\n".join(parts)

    def _estimate_tokens(self, prompt: str, response: str) -> Dict:
        """估算token使用（粗略估计：4个字符≈1个token）

        Args:
            prompt: 输入提示词
            response: 输出响应

        Returns:
            Token使用统计
        """
        input_tokens = len(prompt) // 4
        output_tokens = len(response) // 4

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }


# 全局单例
_cli_adapter = None


def get_cli_adapter() -> CLIAdapter:
    """获取CLI适配器单例"""
    global _cli_adapter
    if _cli_adapter is None:
        _cli_adapter = CLIAdapter()
    return _cli_adapter
