"""
Renderer基类 - Skill渲染器抽象接口
=================================

所有平台特定的渲染器都应该继承此基类。
提供统一的渲染接口和通用工具方法。

设计模式：策略模式（Strategy Pattern）
- 不同的渲染器实现不同的输出策略
- 通过组合使用，可以灵活地转换到任意目标平台

作者：Senior Developer (高级开发工程师)
版本：1.0.0
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from .schema import UniversalSkill, SkillPlatform, Variable, ToolPermission


class BaseRenderer(ABC):
    """
    渲染器基类
    
    定义所有渲染器必须实现的接口。
    子类需要实现以下方法：
    - platform: 返回目标平台类型
    - render_skill: 渲染skill为平台特定格式
    - render_to_file: 渲染并保存到文件
    - render_to_directory: 渲染整个skill到目录
    """
    
    def __init__(self):
        """初始化渲染器"""
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    @property
    @abstractmethod
    def platform(self) -> SkillPlatform:
        """返回此渲染器的目标平台类型"""
        pass
    
    @abstractmethod
    def render_skill(self, skill: UniversalSkill) -> Dict[str, str]:
        """
        渲染skill为平台特定格式
        
        Args:
            skill: 要渲染的UniversalSkill对象
            
        Returns:
            Dict[str, str]: 文件路径到内容的映射
                - key: 相对于skill目录的文件路径
                - value: 文件内容
                
        示例:
            {
                "SKILL.md": "# My Skill\\n...",
                "scripts/helper.py": "print('hello')",
                "references/guide.md": "# Guide\\n..."
            }
        """
        pass
    
    @abstractmethod
    def render_to_file(self, skill: UniversalSkill, file_path: Union[str, Path]) -> None:
        """
        渲染skill并保存到单个文件
        
        对于某些平台（如Claude），skill可能只包含一个SKILL.md文件。
        
        Args:
            skill: 要渲染的skill对象
            file_path: 输出文件路径
        """
        pass
    
    @abstractmethod
    def render_to_directory(self, skill: UniversalSkill, dir_path: Union[str, Path]) -> None:
        """
        渲染整个skill到目录
        
        会创建完整的目录结构，包括SKILL.md和所有资源文件。
        
        Args:
            skill: 要渲染的skill对象
            dir_path: 输出目录路径
        """
        pass
    
    def validate_before_render(self, skill: UniversalSkill) -> bool:
        """
        渲染前验证skill的有效性
        
        Args:
            skill: 要验证的skill对象
            
        Returns:
            bool: 是否可以安全渲染
        """
        # 基础验证
        errors = skill.validate()
        if errors:
            for error in errors:
                self.errors.append(f"Pre-render validation error: {error}")
            return False
        
        # 平台特定验证（子类可以重写）
        platform_errors = self.platform_specific_validation(skill)
        if platform_errors:
            self.errors.extend(platform_errors)
            return False
        
        return True
    
    def platform_specific_validation(self, skill: UniversalSkill) -> List[str]:
        """
        平台特定的验证逻辑
        
        子类可以重写此方法以添加平台特定的验证规则。
        
        Args:
            skill: 要验证的skill对象
            
        Returns:
            List[str]: 错误消息列表，空列表表示验证通过
        """
        return []
    
    def transform_variables(self, skill: UniversalSkill) -> UniversalSkill:
        """
        转换变量占位符到目标平台格式
        
        不同平台使用不同的变量语法：
        - Claude: $ARGUMENTS
        - Codex: {{args}}
        - WorkBuddy: $ARGUMENTS
        
        此方法将skill中的变量占位符转换为目标平台格式。
        
        Args:
            skill: 要转换的skill对象（会创建副本）
            
        Returns:
            UniversalSkill: 转换后的skill对象
        """
        # 创建副本，避免修改原始对象
        transformed = UniversalSkill.from_dict(skill.to_dict())
        
        # 获取变量映射规则
        var_mapping = self.get_variable_mapping()
        
        # 转换指令中的变量
        if var_mapping:
            for source_var, target_var in var_mapping.items():
                transformed.instructions = transformed.instructions.replace(source_var, target_var)
        
        # 转换变量定义
        for var in transformed.variables:
            if var.placeholder in var_mapping:
                var.placeholder = var_mapping[var.placeholder]
        
        return transformed
    
    def transform_tools(self, skill: UniversalSkill) -> UniversalSkill:
        """
        转换工具名称到目标平台格式
        
        不同平台的工具名称不同：
        - Claude: Read, Write, Bash, AskUserQuestion
        - Codex: read_file, write_file, execute_shell
        - WorkBuddy: Read, Write, Bash, AskUserQuestion
        
        Args:
            skill: 要转换的skill对象（会创建副本）
            
        Returns:
            UniversalSkill: 转换后的skill对象
        """
        transformed = UniversalSkill.from_dict(skill.to_dict())
        
        # 获取工具映射规则
        tool_mapping = self.get_tool_mapping()
        
        if tool_mapping:
            for tool in transformed.allowed_tools:
                if tool.name in tool_mapping:
                    original_name = tool.name
                    tool.name = tool_mapping[original_name]
                    # 记录转换历史
                    tool.platform_specific["original_name"] = original_name
        
        return transformed
    
    def transform_paths(self, skill: UniversalSkill) -> UniversalSkill:
        """
        转换路径引用到目标平台格式
        
        不同平台使用不同的路径：
        - Claude: ~/.claude/skills/
        - Codex: ~/.codex/skills/
        - WorkBuddy: ~/.workbuddy/skills/
        
        Args:
            skill: 要转换的skill对象（会创建副本）
            
        Returns:
            UniversalSkill: 转换后的skill对象
        """
        transformed = UniversalSkill.from_dict(skill.to_dict())
        
        # 获取路径映射
        path_mapping = self.get_path_mapping()
        
        if path_mapping:
            for source_path, target_path in path_mapping.items():
                transformed.instructions = transformed.instructions.replace(source_path, target_path)
        
        return transformed
    
    def get_variable_mapping(self) -> Dict[str, str]:
        """
        获取变量映射规则
        
        子类应该重写此方法以提供平台特定的映射。
        
        Returns:
            Dict[str, str]: 源变量 -> 目标变量的映射
        """
        return {}
    
    def get_tool_mapping(self) -> Dict[str, str]:
        """
        获取工具名称映射
        
        子类应该重写此方法以提供平台特定的映射。
        
        Returns:
            Dict[str, str]: 源工具名 -> 目标工具名的映射
        """
        return {}
    
    def get_path_mapping(self) -> Dict[str, str]:
        """
        获取路径映射
        
        子类应该重写此方法以提供平台特定的映射。
        
        Returns:
            Dict[str, str]: 源路径 -> 目标路径的映射
        """
        return {}
    
    def apply_transforms(self, skill: UniversalSkill) -> UniversalSkill:
        """
        应用所有必要的转换
        
        这是一个便捷方法，依次应用变量、工具和路径转换。
        
        Args:
            skill: 要转换的原始skill对象
            
        Returns:
            UniversalSkill: 完全转换后的skill对象
        """
        # 先转换变量
        transformed = self.transform_variables(skill)
        
        # 再转换工具
        transformed = self.transform_tools(transformed)
        
        # 最后转换路径
        transformed = self.transform_paths(transformed)
        
        # 添加转换记录
        transformed.conversion_history.append({
            "from": skill.source_platform.value if skill.source_platform else "unknown",
            "to": self.platform.value,
            "timestamp": datetime.now().isoformat(),
            "transformations": ["variables", "tools", "paths"]
        })
        
        return transformed
    
    def write_file(self, content: str, file_path: Union[str, Path]) -> None:
        """
        写入文件（通用工具方法）
        
        Args:
            content: 文件内容
            file_path: 输出文件路径
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        path.write_text(content, encoding="utf-8")
    
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


class RendererRegistry:
    """
    渲染器注册表
    
    管理所有可用的渲染器实例。
    根据目标平台选择合适的渲染器。
    """
    
    def __init__(self):
        """初始化注册表"""
        self._renderers: Dict[SkillPlatform, BaseRenderer] = {}
    
    def register(self, renderer: BaseRenderer) -> None:
        """
        注册渲染器
        
        Args:
            renderer: 渲染器实例
        """
        self._renderers[renderer.platform] = renderer
    
    def get_renderer(self, platform: SkillPlatform) -> Optional[BaseRenderer]:
        """
        获取指定平台的渲染器
        
        Args:
            platform: 目标平台类型
            
        Returns:
            Optional[BaseRenderer]: 渲染器实例，如果未注册则返回None
        """
        return self._renderers.get(platform)
    
    def list_renderers(self) -> List[BaseRenderer]:
        """列出所有已注册的渲染器"""
        return list(self._renderers.values())
    
    def __str__(self) -> str:
        platforms = [p.value for p in self._renderers.keys()]
        return f"RendererRegistry(platforms={platforms})"


# 全局渲染器注册表实例
registry = RendererRegistry()


def register_renderer(renderer: BaseRenderer) -> None:
    """注册渲染器到全局注册表"""
    registry.register(renderer)


def get_renderer(platform: SkillPlatform) -> Optional[BaseRenderer]:
    """从全局注册表获取渲染器"""
    return registry.get_renderer(platform)


def render_skill(skill: UniversalSkill, target_platform: SkillPlatform, 
                output_path: Union[str, Path]) -> None:
    """
    渲染skill到指定平台格式并保存
    
    这是最简单的使用接口。
    
    Args:
        skill: 要渲染的skill对象
        target_platform: 目标平台
        output_path: 输出路径（文件或目录）
        
    Raises:
        ValueError: 无法找到合适的渲染器
        RuntimeError: 渲染失败
    """
    renderer = registry.get_renderer(target_platform)
    
    if renderer is None:
        raise ValueError(f"No renderer available for platform: {target_platform.value}")
    
    # 验证
    if not renderer.validate_before_render(skill):
        errors = renderer.get_errors()
        raise RuntimeError(f"Validation failed: {'; '.join(errors)}")
    
    # 应用转换
    transformed = renderer.apply_transforms(skill)
    
    # 渲染输出
    path = Path(output_path)
    
    if path.is_dir() or (not path.exists() and not path.suffix):
        # 输出到目录
        renderer.render_to_directory(transformed, path)
    else:
        # 输出到文件
        renderer.render_to_file(transformed, path)


def convert_skill(skill: UniversalSkill, target_platform: SkillPlatform) -> Dict[str, str]:
    """
    转换skill为目标平台格式（不保存到文件）
    
    Args:
        skill: 要转换的skill对象
        target_platform: 目标平台
        
    Returns:
        Dict[str, str]: 文件路径到内容的映射
        
    Raises:
        ValueError: 无法找到合适的渲染器
    """
    renderer = registry.get_renderer(target_platform)
    
    if renderer is None:
        raise ValueError(f"No renderer available for platform: {target_platform.value}")
    
    # 验证
    if not renderer.validate_before_render(skill):
        errors = renderer.get_errors()
        raise RuntimeError(f"Validation failed: {'; '.join(errors)}")
    
    # 应用转换
    transformed = renderer.apply_transforms(skill)
    
    # 渲染（不保存）
    return renderer.render_skill(transformed)