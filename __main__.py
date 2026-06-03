"""
SkillPorter主入口
================

允许直接运行skillporter模块：
    python -m skillporter [command] [args]     # CLI 模式
    python -m skillporter gui                  # GUI 模式

示例：
    python -m skillporter gui                  # 启动可视化界面
    python -m skillporter import claude my-skill
    python -m skillporter convert my-skill codex
"""

import sys


def main():
    """主入口，自动选择 CLI 或 GUI"""
    if len(sys.argv) > 1 and sys.argv[1] == "gui":
        # GUI 模式
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # 移除 'gui' 参数
        from .gui.main_window import run_gui
        run_gui()
    else:
        # CLI 模式
        from .cli import main as cli_main
        sys.exit(cli_main())


if __name__ == "__main__":
    main()
