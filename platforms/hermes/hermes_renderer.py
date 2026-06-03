"""
Hermes平台渲染器 - 渲染Skill为Hermes格式
================================================

将通用Skill格式转换为Hermes可识别的格式。

Hermes skill格式要求：
- 配置文件: hermes.yaml
- 格式: YAML配置
- 变量: 在YAML中定义
- 工具: 在YAML中定义

作者：Ccc
版本：1.0.0
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import yaml

from skillporter.core.renderer import BaseRenderer
from skillporter.core.schema import UniversalSkill, SkillPlatform, Variable, ToolPermission


class HermesRenderer(BaseRenderer):
    """
    Hermes Skill渲染器
    
    将通用Skill格式渲染为Hermes可识别的格式。
    """
    
    @property
    def platform(self) -> SkillPlatform:
        """返回目标平台类型"""
        return SkillPlatform.HERMES
    
    def render_skill(self, skill: UniversalSkill) -> Dict[str, str]:
        """
        渲染skill为Hermes格式
        
        Args:
            skill: 要渲染的UniversalSkill对象
            
        Returns:
            Dict[str, str]: 文件路径到内容的映射
        """
        files = {}
        
        # 1. 生成hermes.yaml配置文件
        config_content = self._generate_config(skill)
        files["hermes.yaml"] = config_content
        
        # 2. 生成SKILL.md指令文件（可选）
        if skill.instructions:
            skill_md = self._generate_skill_md(skill)
            files["SKILL.md"] = skill_md
        
        # 3. 生成脚本文件
        for script in skill.scripts:
            files[script.path] = script.content
        
        # 4. 生成参考文档
        for ref in skill.references:
            files[ref.path] = ref.content
        
        return files
    
    def render_to_file(self, skill: UniversalSkill, file_path: Union[str, Path]) -> None:
        """
        渲染skill并保存到单个文件
        
        对于Hermes，这会生成一个hermes.yaml文件。
        
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
        content = self._generate_config(transformed)
        
        # 写入文件
        self.write_file(content, file_path)
    
    def render_to_directory(self, skill: UniversalSkill, dir_path: Union[str, Path]) -> None:
        """
        渲染整个skill到目录
        
        会创建完整的目录结构：
        {skill-name}/
        ├── hermes.yaml
        ├── SKILL.md（可选）
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
    
    def _generate_config(self, skill: UniversalSkill) -> str:
        """
        生成hermes.yaml配置文件内容
        
        Args:
            skill: skill对象
            
        Returns:
            str: hermes.yaml文件内容
        """
        # 准备配置数据
        config_data = self._prepare_config(skill)
        
        # 生成YAML字符串
        yaml_str = yaml.dump(config_data, default_flow_style=False, allow_unicode=True)
        
        return yaml_str
    
    def _generate_skill_md(self, skill: UniversalSkill) -> str:
        """
        生成SKILL.md文件内容
        
        Args:
            skill: skill对象
            
        Returns:
            str: SKILL.md文件内容
        """
        # 准备YAML前言数据
        yaml_data = {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description
        }
        
        # 生成YAML字符串
        yaml_str = yaml.dump(yaml_data, default_flow_style=False, allow_unicode=True)
        
        # 生成完整内容
        content = f"---\n{yaml_str}---\n\n{skill.instructions}"
        
        return content
    
    def _prepare_config(self, skill: UniversalSkill) -> Dict[str, Any]:
        """
        准备配置数据
        
        Args:
            skill: skill对象
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        # 基础字段
        config = {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description
        }
        
        # 可选字段
        if skill.description_zh:
            config["description_zh"] = skill.description_zh
        if skill.description_en:
            config["description_en"] = skill.description_en
        if skill.version:
            config["version"] = skill.version
        if skill.author:
            config["author"] = skill.author
        if skill.tags:
            config["tags"] = skill.tags
        
        # 指令
        if skill.instructions:
            config["instructions"] = skill.instructions
        
        # 变量
        if skill.variables:
            config["parameters"] = {}
            for var in skill.variables:
                config["parameters"][var.name] = {
                    "type": var.type.value if var.type else "string",
                    "required": var.required,
                    "description": var.description or ""
                }
                if var.default is not None:
                    config["parameters"][var.name]["default"] = var.default
        
        # 工具权限
        if skill.allowed_tools:
            config["tools"] = [tool.name for tool in skill.allowed_tools]
        
        # 平台特有字段
        hermes_overrides = skill.get_platform_override(SkillPlatform.HERMES)
        if hermes_overrides:
            config.update(hermes_overrides)
        
        return config
    
    def get_variable_mapping(self) -> Dict[str, str]:
        """
        获取变量映射规则
        
        Hermes支持多种变量格式。
        
        Returns:
            Dict[str, str]: 源变量 -> 目标变量的映射
        """
        return {}
    
    def get_tool_mapping(self) -> Dict[str, str]:
        """
        获取工具名称映射
        
        Returns:
            Dict[str, str]: 源工具名 -> 目标工具名的映射
        """
        return {}
    
    def get_path_mapping(self) -> Dict[str, str]:
        """
        获取路径映射
        
        Hermes使用~/.hermes/skills/路径。
        
        Returns:
            Dict[str, str]: 源路径 -> 目标路径的映射
        """
        return {
            "~/.claude/skills/": "~/.hermes/skills/",
            "~/.codex/skills/": "~/.hermes/skills/",
            "~/.workbuddy/skills/": "~/.hermes/skills/"
        }
    
    def platform_specific_validation(self, skill: UniversalSkill) -> List[str]:
        """
        Hermes平台特定的验证逻辑
        
        Args:
            skill: 要验证的skill对象
            
        Returns:
            List[str]: 错误消息列表
        """
        errors = []
        
        return errors


# 注册渲染器
from skillporter.core.renderer import register_renderer
register_renderer(HermesRenderer())
