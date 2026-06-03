"""
SkillPorter 的特定平台解析器和渲染器

此软件包包含针对不同 AI 平台的实现：
- Claude Code
- OpenAI Codex
- WorkBuddy
- CodeBuddy
- Cursor
- Cline
- KiloCode
- Kimi Code Agent
- 通义灵码 CLI
- Hermes

每个平台都有自己的解析器（用于读取特定平台的格式）和渲染器（用于写入特定平台的格式）
"""

# Import all parsers and renderers to register them
from .claude import ClaudeParser, ClaudeRenderer
from .codex import CodexParser, CodexRenderer
from .workbuddy import WorkBuddyParser, WorkBuddyRenderer
from .codebuddy import CodeBuddyParser, CodeBuddyRenderer
from .cursor import CursorParser, CursorRenderer
from .cline import ClineParser, ClineRenderer
from .kilocode import KiloCodeParser, KiloCodeRenderer
from .kimi import KimiCodeAgentParser, KimiCodeAgentRenderer
from .qwen import QwenCodeParser, QwenCodeRenderer
from .hermes import HermesParser, HermesRenderer

__all__ = [
    "ClaudeParser",
    "ClaudeRenderer",
    "CodexParser",
    "CodexRenderer",
    "WorkBuddyParser",
    "WorkBuddyRenderer",
    "CodeBuddyParser",
    "CodeBuddyRenderer",
    "CursorParser",
    "CursorRenderer",
    "ClineParser",
    "ClineRenderer",
    "KiloCodeParser",
    "KiloCodeRenderer",
    "KimiCodeAgentParser",
    "KimiCodeAgentRenderer",
    "QwenCodeParser",
    "QwenCodeRenderer",
    "HermesParser",
    "HermesRenderer"
]