"""
Platform-specific parsers and renderers for SkillPorter

This package contains implementations for different AI platforms:
- WorkBuddy
- Claude Code
- OpenAI Codex

Each platform has its own parser (to read platform-specific formats)
and renderer (to write platform-specific formats).
"""

# Import all parsers and renderers to register them
from .claude_parser import ClaudeParser
from .claude_renderer import ClaudeRenderer
from .codex_parser import CodexParser
from .codex_renderer import CodexRenderer
from .workbuddy_parser import WorkBuddyParser
from .workbuddy_renderer import WorkBuddyRenderer

__all__ = [
    "ClaudeParser",
    "ClaudeRenderer",
    "CodexParser",
    "CodexRenderer",
    "WorkBuddyParser",
    "WorkBuddyRenderer"
]