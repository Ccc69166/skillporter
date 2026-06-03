"""
SkillPorter - 跨平台Skill转换工具
==================================

在不同AI平台之间转换skill文件，支持：
- WorkBuddy
- Claude Code
- OpenAI Codex
- CodeBuddy
- Cursor
- Cline
- KiloCode
- Kimi Code Agent
- 通义灵码CLI
- Hermes

核心功能：
1. 解析不同平台的skill格式
2. 转换为通用中间表示（USS）
3. 渲染为目标平台格式
4. 同步到目标平台目录

作者：Ccc
版本：2.1.0
"""

__version__ = "2.1.0"
__author__ = "Senior Developer"

# 导入核心模块
from .core.schema import UniversalSkill, SkillPlatform
from .core.parser import auto_parse, get_parser
from .core.renderer import render_skill, convert_skill, get_renderer
from .config import (
    ConfigManager, get_config, update_config, save_config,
    get_supported_providers, get_provider_models, setup_llm,
    SUPPORTED_MODELS
)

# 导入GUI（延迟导入，避免强制依赖 PyQt6）
def run_gui():
    """启动 GUI 界面"""
    from .gui.main_window import run_gui as _run_gui
    _run_gui()

# 导入平台特定模块（用于注册解析器和渲染器）
from .platforms import (
    ClaudeParser, ClaudeRenderer,
    CodexParser, CodexRenderer,
    WorkBuddyParser, WorkBuddyRenderer,
    CodeBuddyParser, CodeBuddyRenderer,
    CursorParser, CursorRenderer,
    ClineParser, ClineRenderer,
    KiloCodeParser, KiloCodeRenderer,
    KimiCodeAgentParser, KimiCodeAgentRenderer,
    QwenCodeParser, QwenCodeRenderer,
    HermesParser, HermesRenderer
)

__all__ = [
    # 核心类
    "UniversalSkill",
    "SkillPlatform",
    
    # 核心函数
    "auto_parse",
    "get_parser",
    "render_skill",
    "convert_skill",
    "get_renderer",
    
    # 配置
    "ConfigManager",
    "get_config",
    "update_config",
    "save_config",
    "get_supported_providers",
    "get_provider_models",
    "setup_llm",
    "SUPPORTED_MODELS",
    
    # 平台解析器
    "ClaudeParser",
    "CodexParser",
    "WorkBuddyParser",
    "CodeBuddyParser",
    "CursorParser",
    "ClineParser",
    "KiloCodeParser",
    "KimiCodeAgentParser",
    "QwenCodeParser",
    "HermesParser",
    
    # 平台渲染器
    "ClaudeRenderer",
    "CodexRenderer",
    "WorkBuddyRenderer",
    "CodeBuddyRenderer",
    "CursorRenderer",
    "ClineRenderer",
    "KiloCodeRenderer",
    "KimiCodeAgentRenderer",
    "QwenCodeRenderer",
    "HermesRenderer",

    # GUI
    "run_gui",
]


def get_version() -> str:
    """获取版本号"""
    return __version__


def get_supported_platforms() -> list:
    """获取支持的平台列表"""
    return [platform.value for platform in SkillPlatform]