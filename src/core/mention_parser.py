"""
@mention解析工具

解析用户消息中的@mentions，提取被提及的agent_id列表
"""
import re
from typing import List


def parse_mentions(content: str) -> List[str]:
    """
    从消息内容中提取@mentions

    支持格式：
    - @agent_id
    - @"agent with spaces"

    Args:
        content: 消息内容

    Returns:
        被提及的agent_id列表（去重）
    """
    mentions = []

    # 匹配 @agent_id 格式
    pattern1 = r'@([\w\-]+)'
    matches1 = re.findall(pattern1, content)
    mentions.extend(matches1)

    # 匹配 @"agent with spaces" 格式
    pattern2 = r'@"([^"]+)"'
    matches2 = re.findall(pattern2, content)
    mentions.extend(matches2)

    # 去重并返回
    return list(set(mentions))
