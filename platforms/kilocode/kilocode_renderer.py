"""
KiloCode平台渲染器 - 渲染Skill为KiloCode格式
================================================

将通用Skill格式转换为KiloCode可识别的格式。

KiloCode skill格式要求：
- 目录: .kilo/rules/
- 文件: *.md
- 格式: YAML前言 + Markdown内容
- 变量: 无特定变量语法
- 工具: 无特定工具定义

作者：Ccc
版本：1.0.0
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import yaml

from skillporter.core.renderer import BaseRenderer
from skillporter.core.schema import UniversalSkill, SkillPlatform, Variable, ToolPermission


class KiloCodeRenderer(BaseRenderer):
    """
    KiloCode Skill渲染器
    
    将通用Skill格式渲染为KiloCode可识别的格式。
    """
    
    @property
    def platform(self) -> SkillPlatform:
        """返回目标平台类型"""
        return SkillPlatform.KILOCODE
    
    def render_skill(self, skill: UniversalSkill) -> Dict[str, str]:
        """
        渲染skill为KiloCode格式
        
        Args:
            skill: 要渲染的UniversalSkill对象
            
        Returns:
            Dict[str, str]: 文件路径到内容的映射
        """
        files = {}
        
        # 生成.kilo/rules/目录下的规则文件
        rules_content = self._generate_rules(skill)
        files[".kilo/rules/01-rules.md"] = rules_content
        
        # 生成脚本文件
        for script in skill.scripts:
            files[script.path] = script.content
        
        # 生成参考文档
        for ref in skill.references:
            files[ref.path] = ref.content
        
        return files
    
    def render_to_file(self, skill: UniversalSkill, file_path: Union[str, Path]) -> None:
        """
        渲染skill并保存到单个文件
        
        对于KiloCode，这会生成一个规则文件。
        
        Args:
            skill: 要渲染的skill对象
            file_path: 输出文件路径
        """
        if not self.validate_before_render(skill):
            errors = self.get_errors()
            raise RuntimeError(f"Validation failed: {'; '.join(errors)}")
        
        # 应用转换
        transformed = self.apply_transforms(skill)
        
        # 生成内容
        content = self._generate_rules(transformed)
        
        # 写入文件
        self.write_file(content, file_path)
    
    def render_to_directory(self, skill: UniversalSkill, dir_path: Union[str, Path]) -> None:
        """
        渲染整个skill到目录
        
        会创建完整的目录结构：
        {skill-name}/
        ├── .kilo/rules/
        │   └── 01-rules.md
        ├── scripts/
        └── references/
        
        Args:
            skill: 要渲染的skill对象
            dir_path: 输出目录路径
        """
        if not self.validate_before_render(skill):
            errors = self.get_errors()
            raise RuntimeError(f"Validation failed: {'; '.join(errors)}")
        
        # 应用转换
        transformed = self.apply_transforms(skill)
        
        # 创建目录
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        
        # 生成所有文件
        files = self.render_skill(transformed)
        
        # 写入文件
        for file_path, content in files.items():
            full_path = path / file_path
            self.write_file(content, full_path)
    
    def _generate_rules(self, skill: UniversalSkill) -> str:
        """
        生成规则文件内容
        
        Args:
            skill: skill对象
            
        Returns:
            str: 规则文件内容
        """
        # 准备YAML前言数据
        yaml_data = self._prepare_yaml_frontmatter(skill)
        
        # 生成YAML字符串
        yaml_str = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True)
        
        # 生成完整内容
        content = f"---\n{yaml_str}---\n\n{skill.instructions}"
        
        return content
    
    def _prepare_yaml_frontmatter(self, skill: UniversalSkill) -> Dict[str, Any]:
        """
        准备YAML前言数据
        
        Args:
            skill: skill对象
            
        Returns:
            Dict[str, Any]: YAML前言数据
        """
        # 基础字段
        yaml_data = {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description
        }
        
        # 可选字段
        if skill.description_zh:
            yaml_data["description_zh"] = skill.description_zh
        if skill.description_en:
            yaml_data["description_en"] = skill.description_en
        if skill.version:
            yaml_data["version"] = skill.version
        if skill.author:
            yaml_data["author"] = skill.author
        if skill.tags:
            yaml_data["tags"] = skill.tags
        
        # 工具权限（KiloCode通常不定义工具）
        if skill.allowed_tools:
            yaml_data["allowed-tools"] = [tool.name for tool in skill.allowed_tools]
        
        # 平台特有字段
        kilocode_overrides = skill.get_platform_override(SkillPlatform.KILOCODE)
        if kilocode_overrides:
            yaml_data.update(kilocode_overrides)
        
        return yaml_data
    
    def get_variable_mapping(self) -> Dict[str, str]:
        """
        获取变量映射规则
        
        KiloCode不支持特定的变量语法。
        
        Returns:
            Dict[str, str]: 源变量 -> 目标变量的映射
        """
        return {}
    
    def get_tool_mapping(self) -> Dict[str, str]:
        """
        获取工具名称映射
        
        KiloCode不定义工具。
        
        Returns:
            Dict[str, str]: 源工具名 -> 目标工具名的映射
        """
        return {}
    
    def get_path_mapping(self) -> Dict[str, str]:
        """
        获取路径映射
        
        KiloCode使用.kilo/rules/目录。
        
        Returns:
            Dict[str, str]: 源路径 -> 目标路径的映射
        """
        return {}
    
    def platform_specific_validation(self, skill: UniversalSkill) -> List[str]:
        """
        KiloCode平台特定的验证逻辑
        
        Args:
            skill: 要验证的skill对象
            
        Returns:
            List[str]: 错误消息列表
        """
        errors = []
        
        # KiloCode不支持工具权限定义
        if skill.allowed_tools:
            # 这是一个警告，不是错误
            self.warnings.append("KiloCode does not support tool permissions. Tools will be ignored.")
        
        return errors


# 注册渲染器
from skillporter.core.renderer import register_renderer
register_renderer(KiloCodeRenderer())
