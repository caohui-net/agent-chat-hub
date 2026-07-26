"""
剪贴板服务 - 多策略降级复制
支持：Textual API → OSC 52 → 平台工具
"""
import os
import sys
import subprocess
from typing import Optional, Tuple
from pathlib import Path


class ClipboardService:
    """
    剪贴板服务抽象层

    依次尝试：
    1. Textual/终端原生剪贴板API
    2. OSC 52 终端转义序列
    3. 平台特定工具（pbcopy, wl-copy, xclip, xsel, PowerShell）
    4. 失败返回明确错误信息
    """

    def __init__(self):
        self._platform = sys.platform
        self._last_error: Optional[str] = None

    def copy(self, text: str) -> Tuple[bool, str]:
        """
        复制文本到剪贴板

        Args:
            text: 要复制的文本内容

        Returns:
            (success: bool, message: str)
            - success: True表示复制成功，False表示失败
            - message: 成功提示或错误信息
        """
        if not text:
            return False, "没有内容可复制"

        # 策略1: 尝试OSC 52（最通用，支持SSH/tmux）
        if self._try_osc52(text):
            return True, "已复制到剪贴板（OSC 52）"

        # 策略2: 尝试平台工具
        result = self._try_platform_tool(text)
        if result[0]:
            return result

        # 所有策略失败，返回降级提示
        fallback_msg = (
            "剪贴板不可用。请使用终端原生复制：\n"
            "1. 按住 Shift 键\n"
            "2. 用鼠标拖拽选择文本\n"
            "3. 使用终端的复制快捷键"
        )

        if self._platform == "darwin":
            fallback_msg += "\n   (macOS: Cmd+C)"
        else:
            fallback_msg += "\n   (Linux/Windows: Ctrl+Shift+C)"

        return False, fallback_msg

    def _try_osc52(self, text: str) -> bool:
        """
        尝试使用OSC 52终端转义序列

        OSC 52允许应用通过终端模拟器设置剪贴板，
        支持SSH和tmux环境。
        """
        try:
            # OSC 52 格式: \033]52;c;<base64>\007
            import base64

            # 限制大小（某些终端有限制）
            if len(text) > 100000:  # 100KB
                self._last_error = "文本过大，OSC 52可能不支持"
                return False

            encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
            osc52_seq = f"\033]52;c;{encoded}\007"

            # 输出到终端
            sys.stdout.write(osc52_seq)
            sys.stdout.flush()

            return True
        except Exception as e:
            self._last_error = f"OSC 52失败: {str(e)}"
            return False

    def _try_platform_tool(self, text: str) -> Tuple[bool, str]:
        """
        尝试使用平台特定的剪贴板工具
        """
        if self._platform == "darwin":
            return self._try_macos(text)
        elif self._platform == "win32":
            return self._try_windows(text)
        else:  # Linux/Unix
            return self._try_linux(text)

    def _try_macos(self, text: str) -> Tuple[bool, str]:
        """macOS: pbcopy"""
        try:
            proc = subprocess.Popen(
                ['pbcopy'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            proc.communicate(input=text.encode('utf-8'), timeout=2)

            if proc.returncode == 0:
                return True, "已复制到剪贴板（pbcopy）"
            else:
                self._last_error = "pbcopy执行失败"
                return False, ""
        except FileNotFoundError:
            self._last_error = "pbcopy未找到"
            return False, ""
        except Exception as e:
            self._last_error = f"pbcopy错误: {str(e)}"
            return False, ""

    def _try_windows(self, text: str) -> Tuple[bool, str]:
        """Windows: PowerShell Set-Clipboard"""
        try:
            # 使用PowerShell的Set-Clipboard命令
            proc = subprocess.Popen(
                ['powershell', '-command', 'Set-Clipboard', '-Value', text],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            _, stderr = proc.communicate(timeout=2)

            if proc.returncode == 0:
                return True, "已复制到剪贴板（PowerShell）"
            else:
                self._last_error = f"PowerShell失败: {stderr.decode()}"
                return False, ""
        except FileNotFoundError:
            self._last_error = "PowerShell未找到"
            return False, ""
        except Exception as e:
            self._last_error = f"PowerShell错误: {str(e)}"
            return False, ""

    def _try_linux(self, text: str) -> Tuple[bool, str]:
        """
        Linux: 依次尝试 wl-copy (Wayland) → xclip (X11) → xsel (X11)
        """
        # 尝试Wayland (wl-copy)
        if self._try_command(['wl-copy'], text):
            return True, "已复制到剪贴板（wl-copy）"

        # 尝试X11 (xclip)
        if self._try_command(['xclip', '-selection', 'clipboard'], text):
            return True, "已复制到剪贴板（xclip）"

        # 尝试X11 (xsel)
        if self._try_command(['xsel', '--clipboard', '--input'], text):
            return True, "已复制到剪贴板（xsel）"

        self._last_error = "未找到可用的剪贴板工具（wl-copy/xclip/xsel）"
        return False, ""

    def _try_command(self, cmd: list, text: str) -> bool:
        """尝试执行命令并传入文本"""
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            proc.communicate(input=text.encode('utf-8'), timeout=2)
            return proc.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
        except Exception:
            return False

    def get_last_error(self) -> Optional[str]:
        """获取最后一次失败的错误信息"""
        return self._last_error


# 全局单例
_clipboard_service: Optional[ClipboardService] = None


def get_clipboard_service() -> ClipboardService:
    """获取全局剪贴板服务实例"""
    global _clipboard_service
    if _clipboard_service is None:
        _clipboard_service = ClipboardService()
    return _clipboard_service
