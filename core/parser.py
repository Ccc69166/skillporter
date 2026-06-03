"""
Parser基类 - Skill解析器抽象接口
==============================

所有平台特定的解析器都应该继承此基类。
提供统一的解析接口和通用工具方法。

设计模式：模板方法模式（Template Method Pattern）
- parse() 是模板方法，定义解析流程
- 各个步骤由子类实现具体逻辑

作者：Senior Developer (高级开发工程师)
版本：1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import re
import yaml
from .schema import UniversalSkill, SkillPlatform, Variable, ToolPermission


class BaseParser(ABC):
    """
    解析器基类
    
    定义所有解析器必须实现的接口。
    子类需要实现以下方法：
    - platform: 返回支持的平台类型
    - parse_file: 解析单个文件
    - parse_directory: 解析整个skill目录
    - extract_variables: 提取变量定义
    - extract_tools: 提取工具权限
    """
    
    def __init__(self):
        """初始化解析器"""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    @property
    @abstractmethod
    def platform(self) -> SkillPlatform:
        """返回此解析器支持的平台类型"""
        pass
    
    @abstractmethod
    def parse_file(self, file_path: Union[str, Path]) -> UniversalSkill:
        """
        解析单个skill文件
        
        Args:
            file_path: skill文件路径（通常是SKILL.md）
            
        Returns:
            UniversalSkill: 解析后的通用skill对象
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误
        """
        pass
    
    @abstractmethod
    def parse_directory(self, dir_path: Union[str, Path]) -> UniversalSkill:
        """
        解析整个skill目录
        
        会递归扫描目录，解析SKILL.md和所有资源文件（scripts、references）。
        
        Args:
            dir_path: skill目录路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象，包含所有资源文件
        """
        pass
    
    @abstractmethod
    def extract_variables(self, content: str) -> List[Variable]:
        """
        从内容中提取变量定义
        
        不同平台使用不同的变量语法：
        - Claude: $ARGUMENTS, $CONTEXT
        - Codex: {{args}}, {{context}}
        - WorkBuddy: $ARGUMENTS 或其他
        
        Args:
            content: 指令内容文本
            
        Returns:
            List[Variable]: 提取的变量列表
        """
        pass
    
    @abstractmethod
    def extract_tools(self, content: str) -> List[ToolPermission]:
        """
        从内容中提取工具权限
        
        不同平台的工具声明方式不同：
        - Claude: 在YAML头的allowed-tools字段
        - WorkBuddy: 在YAML头的allowed-tools字段
        - Codex: 在openai.yaml中定义
        
        Args:
            content: 文件内容（YAML头或整个文件）
            
        Returns:
            List[ToolPermission]: 提取的工具权限列表
        """
        pass
    
    def read_file(self, file_path: Union[str, Path]) -> str:
        """
        读取文件内容（通用工具方法）
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件内容
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return path.read_text(encoding="utf-8")
    
    def parse_yaml_frontmatter(self, content: str) -> tuple:
        """
        解析YAML前言（Markdown文件中的YAML头部）
        
        许多skill文件使用YAML前言来存储元数据：
        ---
        name: my-skill
        description: A sample skill
        ---
        # Instructions
        ...
        
        Args:
            content: 文件内容
            
        Returns:
            tuple: (yaml_data, markdown_content)
                - yaml_data: 解析后的YAML字典
                - markdown_content: 剩余的Markdown内容
        """
        # 匹配YAML前言
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)
        
        if not match:
            # 没有YAML前言，整个内容都是Markdown
            return {}, content
        
        yaml_str = match.group(1)
        markdown_content = match.group(2)
        
        try:
            yaml_data = yaml.safe_load(yaml_str) or {}
        except yaml.YAMLError as e:
            self.warnings.append(f"YAML parsing error: {e}")
            yaml_data = {}
        
        return yaml_data, markdown_content
    
    def extract_id_from_path(self, path: Union[str, Path]) -> str:
        """
        从路径提取skill ID
        
        通常skill ID就是目录名或文件名（不含扩展名）。
        
        Args:
            path: 文件或目录路径
            
        Returns:
            str: skill ID
        """
        path = Path(path)
        
        if path.is_dir():
            return path.name
        else:
            # 移除扩展名
            return path.stem
    
    def clean_content(self, content: str) -> str:
        """
        清理内容，移除不需要的空白和格式问题
        
        Args:
            content: 原始内容
            
        Returns:
            str: 清理后的内容
        """
        # 移除开头和结尾的空白
        content = content.strip()
        
        # 移除多余的空行（保留最多两个连续空行）
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
    
    def validate_skill(self, skill: UniversalSkill) -> bool:
        """
        验证skill的有效性
        
        Args:
            skill: 要验证的skill对象
            
        Returns:
            bool: 是否有效
        """
        errors = skill.validate()
        
        if errors:
            for error in errors:
                self.errors.append(f"Validation error: {error}")
            return False
        
        return True
    
    def get_errors(self) -> List[str]:
        """获取所有错误"""
        return self.errors.copy()
    
    def get_warnings(self) -> List[str]:
        """获取所有警告"""
        return self.warnings.copy()
    
    def clear_messages(self) -> None:
        """清空错误和警告消息"""
        self.errors.clear()
        self.warnings.clear()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(platform={self.platform.value})"
    
    def __repr__(self) -> str:
        return self.__str__()


class ParserRegistry:
    """
    解析器注册表
    
    管理所有可用的解析器实例。
    根据平台类型或文件路径自动选择合适的解析器。
    """
    
    def __init__(self):
        """初始化注册表"""
        self._parsers: Dict[SkillPlatform, BaseParser] = {}
    
    def register(self, parser: BaseParser) -> None:
        """
        注册解析器
        
        Args:
            parser: 解析器实例
        """
        self._parsers[parser.platform] = parser
    
    def get_parser(self, platform: SkillPlatform) -> Optional[BaseParser]:
        """
        获取指定平台的解析器
        
        Args:
            platform: 平台类型
            
        Returns:
            Optional[BaseParser]: 解析器实例，如果未注册则返回None
        """
        return self._parsers.get(platform)
    
    def get_parser_for_file(self, file_path: Union[str, Path]) -> Optional[BaseParser]:
        """
        根据文件路径自动选择解析器
        
        根据文件内容和路径特征来判断应该使用哪个解析器。
        如果无法确定平台，会尝试使用WorkBuddy解析器（最灵活）。
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[BaseParser]: 合适的解析器，如果无法判断则返回None
        """
        path = Path(file_path)
        if not path.exists():
            return None
        
        # 处理目录路径：查找目录中的skill文件
        if path.is_dir():
            # 按优先级查找skill文件
            skill_files = [
                path / "SKILL.md",
                path / "skill.md",
                path / "openai.yaml",
                path / "AGENTS.md"
            ]
            
            for skill_file in skill_files:
                if skill_file.exists():
                    return self.get_parser_for_file(skill_file)
            
            # 如果没有找到标准文件，尝试查找任何.md或.yaml文件
            for ext in ["*.md", "*.yaml", "*.yml"]:
                md_files = list(path.glob(ext))
                if md_files:
                    return self.get_parser_for_file(md_files[0])
            
            # 空目录或没有skill文件，使用WorkBuddy解析器作为默认
            return self._parsers.get(SkillPlatform.WORKBUDDY)
        
        # 处理文件路径
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None
        
        # 检测平台特征
        if self._is_workbuddy_skill(content, path):
            return self._parsers.get(SkillPlatform.WORKBUDDY)
        elif self._is_claude_skill(content, path):
            return self._parsers.get(SkillPlatform.CLAUDE)
        elif self._is_codex_skill(content, path):
            return self._parsers.get(SkillPlatform.CODEX)
        
        # 如果无法确定平台，尝试使用WorkBuddy解析器（最灵活）
        # 这是因为WorkBuddy支持多种变量格式
        workbuddy_parser = self._parsers.get(SkillPlatform.WORKBUDDY)
        if workbuddy_parser:
            # 尝试解析，如果失败则返回None
            try:
                # 只是测试是否能解析，不实际创建skill
                if "id:" in content and "name:" in content:
                    return workbuddy_parser
            except:
                pass
        
        return None
    
    def _is_workbuddy_skill(self, content: str, path: Path) -> bool:
        """检测是否为WorkBuddy skill"""
        # WorkBuddy skill通常包含特定的字段
        indicators = [
            "description_zh" in content,
            "description_en" in content,
            "~/.workbuddy/skills/" in content,
            "AskUserQuestion" in content,
            # 通用指标：包含YAML前言和allowed-tools
            "allowed-tools" in content,
            "id:" in content and "name:" in content and "description:" in content
        ]
        # 如果包含至少2个指标，或者包含通用指标
        return sum(indicators) >= 2 or (indicators[4] and indicators[5])
    
    def _is_claude_skill(self, content: str, path: Path) -> bool:
        """检测是否为Claude skill"""
        indicators = [
            "~/.claude/skills/" in content,
            ".claude/skills/" in content,
            "Claude Code" in content,
            # Claude特有的变量格式
            "$ARGUMENTS" in content or "$CONTEXT" in content
        ]
        return sum(indicators) >= 1
    
    def _is_codex_skill(self, content: str, path: Path) -> bool:
        """检测是否为Codex skill"""
        # Codex使用不同的文件结构
        indicators = [
            "AGENTS.md" in path.name,
            "openai.yaml" in path.name,
            "parameters" in content and "type" in content,
            # Codex特有的变量格式
            "{{args}}" in content or "{{context}}" in content
        ]
        return sum(indicators) >= 1
    
    def list_parsers(self) -> List[BaseParser]:
        """列出所有已注册的解析器"""
        return list(self._parsers.values())
    
    def __str__(self) -> str:
        platforms = [p.value for p in self._parsers.keys()]
        return f"ParserRegistry(platforms={platforms})"


# 全局解析器注册表实例
registry = ParserRegistry()


def register_parser(parser: BaseParser) -> None:
    """注册解析器到全局注册表"""
    registry.register(parser)


def get_parser(platform: SkillPlatform) -> Optional[BaseParser]:
    """从全局注册表获取解析器"""
    return registry.get_parser(platform)


def auto_parse(file_path: Union[str, Path]) -> UniversalSkill:
    """
    自动检测并解析skill文件
    
    这是最简单的使用接口，自动选择合适的解析器。
    
    Args:
        file_path: skill文件或目录路径
        
    Returns:
        UniversalSkill: 解析后的通用skill对象
        
    Raises:
        ValueError: 无法识别文件格式
        FileNotFoundError: 文件不存在
    """
    parser = registry.get_parser_for_file(file_path)
    
    if parser is None:
        raise ValueError(f"Unable to determine parser for: {file_path}")
    
    path = Path(file_path)
    if path.is_dir():
        return parser.parse_directory(path)
    else:
        return parser.parse_file(path)