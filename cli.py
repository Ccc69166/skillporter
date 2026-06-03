"""
SkillPorter CLI - 跨平台Skill转换工具命令行接口
===============================================

这是一个模仿git风格的命令行工具，用于在不同AI平台之间转换skill文件。

核心功能：
1. import - 从源平台导入skill
2. convert - 将skill转换为目标平台格式
3. sync - 同步skill到目标平台
4. status - 查看skill状态
5. config - 管理配置
6. init - 初始化配置

使用示例：
    # 从Claude导入skill到WorkBuddy
    skillporter import claude my-skill
    
    # 将skill转换为Codex格式
    skillporter convert my-skill codex
    
    # 同步skill到目标平台
    skillporter sync my-skill workbuddy
    
    # 查看skill状态
    skillporter status my-skill
    
    # 配置LLM API密钥
    skillporter config set llm.api_key sk-xxx

作者：Senior Developer (高级开发工程师)
版本：1.0.0
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import yaml

from .config import (
    ConfigManager, get_config, update_config, save_config,
    get_supported_providers, get_provider_models, setup_llm,
    SUPPORTED_MODELS
)
from .core.schema import UniversalSkill, SkillPlatform
from .core.parser import auto_parse, get_parser
from .core.renderer import render_skill, convert_skill, get_renderer


class SkillPorterCLI:
    """
    SkillPorter命令行接口
    
    提供类似git的命令行体验，支持以下命令：
    - import: 从源平台导入skill
    - convert: 转换skill格式
    - sync: 同步skill到目标平台
    - status: 查看skill状态
    - config: 管理配置
    - init: 初始化配置
    - list: 列出所有skill
    - validate: 验证skill格式
    """
    
    def __init__(self):
        """初始化CLI"""
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # 设置命令解析器
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        创建命令行参数解析器
        
        Returns:
            argparse.ArgumentParser: 参数解析器
        """
        parser = argparse.ArgumentParser(
            prog="skillporter",
            description="跨平台Skill转换工具 - 在WorkBuddy、Claude、Codex之间转换skill文件",
            epilog="""
示例:
  skillporter import claude my-skill        # 从Claude导入skill
  skillporter convert my-skill codex        # 转换为Codex格式
  skillporter sync my-skill workbuddy       # 同步到WorkBuddy
  skillporter status my-skill               # 查看skill状态
  skillporter config set llm.api_key sk-xxx # 设置LLM API密钥
            """
        )
        
        # 添加版本参数
        parser.add_argument(
            "--version", "-v",
            action="version",
            version="SkillPorter 1.0.0"
        )
        
        # 添加详细输出参数
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="显示详细输出"
        )
        
        # 添加无颜色参数
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="禁用彩色输出"
        )
        
        # 创建子命令解析器
        subparsers = parser.add_subparsers(
            dest="command",
            help="可用命令"
        )
        
        # import命令
        import_parser = subparsers.add_parser(
            "import",
            help="从源平台导入skill",
            description="""
从源平台导入skill文件。

源平台可以是：
- claude: 从Claude Code导入
  * 本地路径: ~/.claude/skills/{skill-name}/
  * GitHub URL: https://raw.githubusercontent.com/anthropics/claude-code/main/skills/...
  * 说明: Claude Code的官方skill存储在GitHub仓库中，用户可以通过此URL获取官方示例
  
- codex: 从OpenAI Codex导入
  * 本地路径: ~/.codex/skills/{skill-name}/
  
- workbuddy: 从WorkBuddy导入
  * 本地路径: ~/.workbuddy/skills/{skill-name}/
            """
        )
        import_parser.add_argument(
            "source",
            choices=["claude", "codex", "workbuddy"],
            help="源平台"
        )
        import_parser.add_argument(
            "skill_name",
            help="skill名称或路径"
        )
        import_parser.add_argument(
            "--output", "-o",
            help="输出目录路径"
        )
        import_parser.add_argument(
            "--name",
            help="指定skill名称（可选）"
        )
        
        # convert命令
        convert_parser = subparsers.add_parser(
            "convert",
            help="转换skill格式",
            description="将skill转换为目标平台格式。"
        )
        convert_parser.add_argument(
            "skill_path",
            help="skill文件或目录路径"
        )
        convert_parser.add_argument(
            "target",
            choices=["claude", "codex", "workbuddy"],
            nargs="?",
            help="目标平台（或使用 --to）"
        )
        convert_parser.add_argument(
            "--to",
            dest="target_alt",
            choices=["claude", "codex", "workbuddy"],
            help="目标平台（替代位置参数）"
        )
        convert_parser.add_argument(
            "--output", "-o",
            help="输出路径"
        )
        convert_parser.add_argument(
            "--in-place",
            action="store_true",
            help="原地转换（覆盖原文件）"
        )
        
        # sync命令
        sync_parser = subparsers.add_parser(
            "sync",
            help="同步skill到目标平台",
            description="将skill同步到目标平台的skills目录。"
        )
        sync_parser.add_argument(
            "skill_path",
            help="skill文件或目录路径"
        )
        sync_parser.add_argument(
            "target",
            choices=["claude", "codex", "workbuddy"],
            help="目标平台"
        )
        sync_parser.add_argument(
            "--force",
            action="store_true",
            help="强制覆盖已存在的skill"
        )
        sync_parser.add_argument(
            "--backup",
            action="store_true",
            help="备份已存在的skill"
        )
        
        # status命令
        status_parser = subparsers.add_parser(
            "status",
            help="查看skill状态",
            description="查看skill的详细状态信息。"
        )
        status_parser.add_argument(
            "skill_path",
            help="skill文件或目录路径"
        )
        status_parser.add_argument(
            "--json",
            action="store_true",
            help="以JSON格式输出"
        )
        
        # config命令
        config_parser = subparsers.add_parser(
            "config",
            help="管理配置",
            description="管理SkillPorter配置。"
        )
        config_subparsers = config_parser.add_subparsers(
            dest="config_command",
            help="配置命令"
        )
        
        # config get
        config_get_parser = config_subparsers.add_parser(
            "get",
            help="获取配置值"
        )
        config_get_parser.add_argument(
            "key",
            help="配置键（如 llm.api_key）"
        )
        
        # config set
        config_set_parser = config_subparsers.add_parser(
            "set",
            help="设置配置值"
        )
        config_set_parser.add_argument(
            "key",
            help="配置键（如 llm.api_key）"
        )
        config_set_parser.add_argument(
            "value",
            help="配置值"
        )
        
        # config list
        config_list_parser = config_subparsers.add_parser(
            "list",
            help="列出所有配置"
        )
        
        # config init
        config_init_parser = config_subparsers.add_parser(
            "init",
            help="初始化配置文件"
        )
        config_init_parser.add_argument(
            "--force",
            action="store_true",
            help="强制覆盖已存在的配置"
        )
        
        # list命令
        list_parser = subparsers.add_parser(
            "list",
            help="列出所有skill",
            description="列出指定平台的所有skill。"
        )
        list_parser.add_argument(
            "platform",
            choices=["claude", "codex", "workbuddy", "all"],
            help="平台"
        )
        list_parser.add_argument(
            "--path",
            help="指定skills目录路径"
        )
        
        # validate命令
        validate_parser = subparsers.add_parser(
            "validate",
            help="验证skill格式",
            description="验证skill文件格式是否正确。"
        )
        validate_parser.add_argument(
            "skill_path",
            help="skill文件或目录路径"
        )
        
        # llm命令 - 快速配置LLM
        llm_parser = subparsers.add_parser(
            "llm",
            help="配置LLM API（用于增强转换）",
            description="""
配置LLM API密钥，用于增强转换功能。

支持的提供商:
  - deepseek  DeepSeek（推荐，国产模型）
  - zhipu     智谱GLM（国产模型）
  - qwen      通义千问（国产模型）
  - openai    OpenAI GPT系列
  - anthropic Claude系列

示例:
  # 查看支持的模型列表
  skillporter llm list
  
  # 快速配置DeepSeek
  skillporter llm setup deepseek sk-xxx
  
  # 配置智谱GLM
  skillporter llm setup zhipu xxx
  
  # 查看当前配置
  skillporter llm status
            """
        )
        llm_subparsers = llm_parser.add_subparsers(
            dest="llm_command",
            help="LLM配置命令"
        )
        
        # llm list - 列出支持的模型
        llm_list_parser = llm_subparsers.add_parser(
            "list",
            help="列出支持的LLM模型"
        )
        
        # llm setup - 快速设置LLM
        llm_setup_parser = llm_subparsers.add_parser(
            "setup",
            help="快速设置LLM配置"
        )
        llm_setup_parser.add_argument(
            "provider",
            choices=["openai", "deepseek", "zhipu", "qwen", "anthropic"],
            help="LLM提供商"
        )
        llm_setup_parser.add_argument(
            "api_key",
            help="API密钥"
        )
        llm_setup_parser.add_argument(
            "--model",
            help="指定模型（可选，使用默认模型）"
        )
        llm_setup_parser.add_argument(
            "--base-url",
            help="自定义API地址（可选）"
        )
        
        # llm status - 查看当前配置
        llm_status_parser = llm_subparsers.add_parser(
            "status",
            help="查看当前LLM配置"
        )
        
        return parser
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        运行CLI
        
        Args:
            args: 命令行参数列表，如果为None则使用sys.argv
            
        Returns:
            int: 退出码（0表示成功，非0表示失败）
        """
        try:
            # 解析参数
            parsed_args = self.parser.parse_args(args)
            
            # 应用全局参数
            if parsed_args.verbose:
                self.config.verbose = True
            
            if parsed_args.no_color:
                self.config.color_output = False
            
            # 执行命令
            if not parsed_args.command:
                self.parser.print_help()
                return 0
            
            # 根据命令分发
            command_map = {
                "import": self._cmd_import,
                "convert": self._cmd_convert,
                "sync": self._cmd_sync,
                "status": self._cmd_status,
                "config": self._cmd_config,
                "list": self._cmd_list,
                "validate": self._cmd_validate,
                "llm": self._cmd_llm
            }
            
            handler = command_map.get(parsed_args.command)
            if handler:
                return handler(parsed_args)
            else:
                print(f"Unknown command: {parsed_args.command}")
                return 1
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130
        except Exception as e:
            print(f"Error: {e}")
            if self.config.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def _cmd_import(self, args) -> int:
        """
        执行import命令
        
        从源平台导入skill文件。
        
        Args:
            args: 解析后的参数
            
        Returns:
            int: 退出码
        """
        print(f"Importing skill from {args.source}: {args.skill_name}")
        
        try:
            # 确定源路径
            source_path = self._resolve_source_path(args.source, args.skill_name)
            
            # 解析skill
            skill = auto_parse(source_path)
            
            # 确定输出路径
            if args.output:
                output_path = Path(args.output)
            else:
                # 默认输出到当前目录
                output_path = Path.cwd() / skill.id
            
            # 保存skill
            from .core.schema import save_skill_to_file
            save_skill_to_file(skill, str(output_path / "skill.json"))
            
            print(f"✓ Skill imported successfully: {skill.id}")
            print(f"  Source: {source_path}")
            print(f"  Output: {output_path}")
            
            return 0
            
        except Exception as e:
            print(f"✗ Import failed: {e}")
            return 1
    
    def _cmd_convert(self, args) -> int:
        """
        执行convert命令
        
        将skill转换为目标平台格式。
        
        Args:
            args: 解析后的参数
            
        Returns:
            int: 退出码
        """
        # 支持 --to 参数作为 target 的替代
        target = args.target or args.target_alt
        if not target:
            print("✗ 请指定目标平台，例如: skillporter convert skill workbuddy")
            return 1
        print(f"Converting skill to {target}: {args.skill_path}")
        
        try:
            # 解析源skill
            skill = auto_parse(args.skill_path)
            
            # 确定目标平台
            target_platform = SkillPlatform(target)
            
            # 确定输出路径
            if args.output:
                output_path = Path(args.output)
            elif args.in_place:
                output_path = Path(args.skill_path)
            else:
                # 默认输出到当前目录
                output_path = Path.cwd() / f"{skill.id}_{target}"
            
            # 转换并保存
            render_skill(skill, target_platform, output_path)
            
            print(f"✓ Skill converted successfully: {skill.id}")
            print(f"  Source: {args.skill_path}")
            print(f"  Target: {target}")
            print(f"  Output: {output_path}")
            
            return 0
            
        except Exception as e:
            print(f"✗ Conversion failed: {e}")
            return 1
    
    def _cmd_sync(self, args) -> int:
        """
        执行sync命令
        
        将skill同步到目标平台的skills目录。
        
        Args:
            args: 解析后的参数
            
        Returns:
            int: 退出码
        """
        print(f"Syncing skill to {args.target}: {args.skill_path}")
        
        try:
            # 解析源skill
            skill = auto_parse(args.skill_path)
            
            # 确定目标平台
            target_platform = SkillPlatform(args.target)
            
            # 获取目标平台的skills目录
            target_dir = self._get_platform_skills_dir(args.target)
            
            # 检查是否已存在
            skill_dir = target_dir / skill.id
            if skill_dir.exists():
                if not args.force:
                    print(f"✗ Skill already exists: {skill_dir}")
                    print(f"  Use --force to overwrite")
                    return 1
                
                # 备份已存在的skill
                if args.backup:
                    backup_path = skill_dir.with_suffix(".backup")
                    import shutil
                    shutil.copytree(skill_dir, backup_path)
                    print(f"  Backup created: {backup_path}")
            
            # 转换并同步
            render_skill(skill, target_platform, skill_dir)
            
            print(f"✓ Skill synced successfully: {skill.id}")
            print(f"  Source: {args.skill_path}")
            print(f"  Target: {skill_dir}")
            
            return 0
            
        except Exception as e:
            print(f"✗ Sync failed: {e}")
            return 1
    
    def _cmd_status(self, args) -> int:
        """
        执行status命令
        
        查看skill的详细状态信息。
        
        Args:
            args: 解析后的参数
            
        Returns:
            int: 退出码
        """
        try:
            # 解析skill
            skill = auto_parse(args.skill_path)
            
            # 输出状态信息
            if args.json:
                # JSON格式输出
                status = {
                    "id": skill.id,
                    "name": skill.name,
                    "description": skill.description,
                    "version": skill.version,
                    "author": skill.author,
                    "tags": skill.tags,
                    "source_platform": skill.source_platform.value if skill.source_platform else None,
                    "source_path": skill.source_path,
                    "variables_count": len(skill.variables),
                    "tools_count": len(skill.allowed_tools),
                    "scripts_count": len(skill.scripts),
                    "references_count": len(skill.references),
                    "conversion_history": skill.conversion_history
                }
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                # 人类可读格式输出
                print(f"Skill: {skill.id}")
                print(f"  Name: {skill.name}")
                print(f"  Description: {skill.description[:100]}...")
                if skill.version:
                    print(f"  Version: {skill.version}")
                if skill.author:
                    print(f"  Author: {skill.author}")
                if skill.tags:
                    print(f"  Tags: {', '.join(skill.tags)}")
                print(f"  Source Platform: {skill.source_platform.value if skill.source_platform else 'Unknown'}")
                print(f"  Source Path: {skill.source_path}")
                print(f"  Variables: {len(skill.variables)}")
                print(f"  Tools: {len(skill.allowed_tools)}")
                print(f"  Scripts: {len(skill.scripts)}")
                print(f"  References: {len(skill.references)}")
                
                if skill.conversion_history:
                    print(f"  Conversion History:")
                    for i, conv in enumerate(skill.conversion_history, 1):
                        print(f"    {i}. {conv.get('from', 'Unknown')} → {conv.get('to', 'Unknown')}")
                        print(f"       at {conv.get('timestamp', 'Unknown')}")
            
            return 0
            
        except Exception as e:
            print(f"✗ Status check failed: {e}")
            return 1
    
    def _cmd_config(self, args) -> int:
        """
        执行config命令
        
        管理SkillPorter配置。
        
        Args:
            args: 解析后的参数
            
        Returns:
            int: 退出码
        """
        if not args.config_command:
            print("Available config commands: get, set, list, init")
            return 1
        
        try:
            if args.config_command == "get":
                return self._config_get(args.key)
            elif args.config_command == "set":
                return self._config_set(args.key, args.value)
            elif args.config_command == "list":
                return self._config_list()
            elif args.config_command == "init":
                return self._config_init(args.force)
            else:
                print(f"Unknown config command: {args.config_command}")
                return 1
                
        except Exception as e:
            print(f"✗ Config command failed: {e}")
            return 1
    
    def _cmd_list(self, args) -> int:
        """
        执行list命令
        
        列出指定平台的所有skill。
        
        Args:
            args: 解析后的参数
            
        Returns:
            int: 退出码
        """
        try:
            # 确定skills目录
            if args.path:
                skills_dir = Path(args.path)
            else:
                skills_dir = self._get_platform_skills_dir(args.platform)
            
            if not skills_dir.exists():
                print(f"Skills directory not found: {skills_dir}")
                return 1
            
            # 列出所有skill
            print(f"Skills in {args.platform}:")
            print(f"  Directory: {skills_dir}")
            print()
            
            skill_count = 0
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        try:
                            skill = auto_parse(skill_dir)
                            print(f"  • {skill.id}")
                            print(f"    Name: {skill.name}")
                            print(f"    Description: {skill.description[:50]}...")
                            skill_count += 1
                        except Exception as e:
                            print(f"  • {skill_dir.name} (error: {e})")
            
            print(f"\nTotal: {skill_count} skills")
            return 0
            
        except Exception as e:
            print(f"✗ List failed: {e}")
            return 1
    
    def _cmd_validate(self, args) -> int:
        """
        执行validate命令
        
        验证skill文件格式是否正确。
        
        Args:
            args: 解析后的参数
            
        Returns:
            int: 退出码
        """
        try:
            # 解析skill
            skill = auto_parse(args.skill_path)
            
            # 验证skill
            errors = skill.validate()
            
            if errors:
                print(f"✗ Validation failed for: {args.skill_path}")
                for error in errors:
                    print(f"  • {error}")
                return 1
            else:
                print(f"✓ Validation passed: {skill.id}")
                return 0
                
        except Exception as e:
            print(f"✗ Validation error: {e}")
            return 1
    
    def _resolve_source_path(self, source: str, skill_name: str) -> Path:
        """
        解析源路径
        
        Args:
            source: 源平台
            skill_name: skill名称或路径
            
        Returns:
            Path: 解析后的路径
        """
        # 如果是完整路径，直接使用
        if Path(skill_name).exists():
            return Path(skill_name)
        
        # 否则，根据平台确定路径
        platform_paths = {
            "claude": self.config.platforms.claude_path,
            "codex": self.config.platforms.codex_path,
            "workbuddy": self.config.platforms.workbuddy_path
        }
        
        base_path = Path(platform_paths[source]).expanduser()
        skill_path = base_path / skill_name
        
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill not found: {skill_path}")
        
        return skill_path
    
    def _get_platform_skills_dir(self, platform: str) -> Path:
        """
        获取平台skills目录
        
        Args:
            platform: 平台名称
            
        Returns:
            Path: skills目录路径
        """
        platform_paths = {
            "claude": self.config.platforms.claude_path,
            "codex": self.config.platforms.codex_path,
            "workbuddy": self.config.platforms.workbuddy_path
        }
        
        return Path(platform_paths[platform]).expanduser()
    
    def _config_get(self, key: str) -> int:
        """获取配置值"""
        try:
            # 支持嵌套键，如 "llm.api_key"
            keys = key.split(".")
            value = self.config
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    print(f"✗ Config key not found: {key}")
                    return 1
            
            print(f"{key}: {value}")
            return 0
            
        except Exception as e:
            print(f"✗ Config get failed: {e}")
            return 1
    
    def _config_set(self, key: str, value: str) -> int:
        """设置配置值"""
        try:
            # 尝试转换值类型
            if value.lower() in ["true", "false"]:
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit():
                value = float(value)
            
            # 更新配置
            update_config(**{key: value})
            save_config()
            
            print(f"✓ Config updated: {key} = {value}")
            return 0
            
        except Exception as e:
            print(f"✗ Config set failed: {e}")
            return 1
    
    def _config_list(self) -> int:
        """列出所有配置"""
        try:
            config_dict = self.config.to_dict()
            print(yaml.dump(config_dict, default_flow_style=False, allow_unicode=True))
            return 0
            
        except Exception as e:
            print(f"✗ Config list failed: {e}")
            return 1
    
    def _config_init(self, force: bool = False) -> int:
        """初始化配置文件"""
        try:
            config_path = self.config_manager.config_path
            
            if config_path.exists() and not force:
                print(f"✗ Config file already exists: {config_path}")
                print(f"  Use --force to overwrite")
                return 1
            
            # 创建默认配置
            self.config_manager.save_config()
            
            print(f"✓ Config file created: {config_path}")
            return 0
            
        except Exception as e:
            print(f"✗ Config init failed: {e}")
            return 1
    
    def _cmd_llm(self, args) -> int:
        """
        执行llm命令
        
        管理LLM API配置。
        
        Args:
            args: 解析后的参数
            
        Returns:
            int: 退出码
        """
        if not args.llm_command:
            print("Available llm commands: list, setup, status")
            print("Use 'skillporter llm --help' for more info")
            return 1
        
        try:
            if args.llm_command == "list":
                return self._llm_list()
            elif args.llm_command == "setup":
                return self._llm_setup(args.provider, args.api_key, args.model, args.base_url)
            elif args.llm_command == "status":
                return self._llm_status()
            else:
                print(f"Unknown llm command: {args.llm_command}")
                return 1
                
        except Exception as e:
            print(f"✗ LLM command failed: {e}")
            return 1
    
    def _llm_list(self) -> int:
        """列出支持的LLM模型"""
        print("支持的LLM提供商和模型:")
        print()
        
        for provider_id, provider_info in SUPPORTED_MODELS.items():
            print(f"  {provider_id:12} - {provider_info['name']}")
            print(f"  {'':12}   默认模型: {provider_info['default_model']}")
            print(f"  {'':12}   API地址: {provider_info['base_url']}")
            print(f"  {'':12}   可用模型:")
            for model in provider_info['models']:
                print(f"  {'':12}     • {model}")
            print()
        
        print("使用方法:")
        print("  skillporter llm setup <provider> <api_key>")
        print("  skillporter llm setup deepseek sk-xxx")
        
        return 0
    
    def _llm_setup(self, provider: str, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None) -> int:
        """快速设置LLM配置"""
        try:
            setup_llm(provider, api_key, model, base_url)
            
            provider_info = SUPPORTED_MODELS.get(provider, {})
            print(f"✓ LLM配置成功！")
            print(f"  提供商: {provider_info.get('name', provider)}")
            print(f"  模型: {model or provider_info.get('default_model', 'default')}")
            print(f"  API地址: {base_url or provider_info.get('base_url', 'default')}")
            print()
            print("现在可以使用LLM增强转换功能了！")
            
            return 0
            
        except Exception as e:
            print(f"✗ LLM setup failed: {e}")
            return 1
    
    def _llm_status(self) -> int:
        """查看当前LLM配置"""
        try:
            llm_config = self.config.llm
            
            print("当前LLM配置:")
            print()
            print(f"  状态: {'✓ 已启用' if llm_config.enabled else '✗ 未启用'}")
            print(f"  提供商: {llm_config.provider}")
            print(f"  模型: {llm_config.model}")
            print(f"  API地址: {llm_config.base_url or '默认'}")
            print(f"  API密钥: {'✓ 已设置' if llm_config.api_key else '✗ 未设置'}")
            print(f"  最大Token: {llm_config.max_tokens}")
            print(f"  温度: {llm_config.temperature}")
            print()
            
            if not llm_config.enabled:
                print("提示: 使用 'skillporter llm setup' 配置LLM以启用增强功能")
            
            return 0
            
        except Exception as e:
            print(f"✗ LLM status failed: {e}")
            return 1


def main():
    """主函数"""
    cli = SkillPorterCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()