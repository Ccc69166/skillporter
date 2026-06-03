"""
Hermes平台解析器 - 解析Hermes格式的Skill文件
================================================

Hermes的skill文件结构：
- 位置: ~/.hermes/skills/{skill-name}/ 或 hermes.yaml
- 格式: YAML配置文件
- 变量: 在YAML中定义
- 工具: 在YAML中定义

Hermes skill特点：
1. 使用YAML配置文件格式
2. 支持多层级配置
3. 支持子Agent委托
4. 支持多种LLM提供商

作者：Ccc
版本：1.0.0
"""

import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import yaml

from skillporter.core.parser import BaseParser
from skillporter.core.schema import UniversalSkill, SkillPlatform, Variable, ToolPermission, ResourceFile


class HermesParser(BaseParser):
    """
    Hermes Skill解析器
    
    解析Hermes格式的skill文件，转换为通用Skill格式。
    """
    
    @property
    def platform(self) -> SkillPlatform:
        """返回支持的平台类型"""
        return SkillPlatform.HERMES
    
    def parse_file(self, file_path: Union[str, Path]) -> UniversalSkill:
        """
        解析单个Hermes skill文件
        
        Hermes skill文件通常是YAML格式。
        
        Args:
            file_path: skill文件路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Hermes skill file not found: {file_path}")
        
        content = self.read_file(path)
        
        # 尝试解析YAML
        try:
            yaml_data = yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in Hermes skill file: {e}")
        
        # 提取基础信息
        skill_id = yaml_data.get("id", self.extract_id_from_path(path))
        name = yaml_data.get("name", skill_id)
        description = yaml_data.get("description", "")
        
        # 提取变量
        variables = self._extract_variables_from_config(yaml_data)
        
        # 提取工具权限
        allowed_tools = self._extract_tools_from_config(yaml_data)
        
        # 提取指令
        instructions = yaml_data.get("instructions", yaml_data.get("prompt", ""))
        
        # 创建skill对象
        skill = UniversalSkill(
            id=skill_id,
            name=name,
            description=description,
            description_zh=yaml_data.get("description_zh"),
            description_en=yaml_data.get("description_en"),
            version=yaml_data.get("version"),
            author=yaml_data.get("author"),
            tags=yaml_data.get("tags", []),
            instructions=instructions,
            allowed_tools=allowed_tools,
            variables=variables,
            source_platform=SkillPlatform.HERMES,
            source_path=str(path)
        )
        
        # 提取平台特有字段
        platform_overrides = {}
        for key, value in yaml_data.items():
            if key not in ["id", "name", "description", "description_zh", "description_en",
                          "version", "author", "tags", "instructions", "prompt", "parameters", "tools"]:
                platform_overrides[key] = value
        
        if platform_overrides:
            skill.set_platform_override(SkillPlatform.HERMES, platform_overrides)
        
        # 验证skill
        if not self.validate_skill(skill):
            errors = self.get_errors()
            raise ValueError(f"Invalid Hermes skill: {'; '.join(errors)}")
        
        return skill
    
    def parse_directory(self, dir_path: Union[str, Path]) -> UniversalSkill:
        """
        解析整个Hermes skill目录
        
        Hermes skill目录结构：
        {skill-name}/
        ├── hermes.yaml       # 主配置文件
        ├── SKILL.md          # 指令文件（可选）
        ├── scripts/          # 脚本目录（可选）
        │   └── *.py, *.sh等
        └── references/       # 参考文档（可选）
            └── *.md, *.txt等
        
        Args:
            dir_path: skill目录路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象，包含所有资源文件
        """
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Hermes skill directory not found: {dir_path}")
        
        # 查找配置文件
        config_file = path / "hermes.yaml"
        if not config_file.exists():
            # 尝试查找其他yaml文件
            yaml_files = list(path.glob("*.yaml")) + list(path.glob("*.yml"))
            if yaml_files:
                config_file = yaml_files[0]
            else:
                # 尝试查找SKILL.md
                skill_file = path / "SKILL.md"
                if skill_file.exists():
                    return self._parse_skill_md(skill_file)
                else:
                    raise FileNotFoundError(f"No hermes.yaml or SKILL.md found in {dir_path}")
        
        # 解析配置文件
        skill = self.parse_file(config_file)
        
        # 查找指令文件
        skill_file = path / "SKILL.md"
        if skill_file.exists():
            skill_content = self.read_file(skill_file)
            _, instructions = self.parse_yaml_frontmatter(skill_content)
            skill.instructions = instructions
        
        # 收集资源文件
        scripts_dir = path / "scripts"
        references_dir = path / "references"
        
        # 解析脚本文件
        if scripts_dir.exists():
            for script_file in scripts_dir.iterdir():
                if script_file.is_file():
                    content = self.read_file(script_file)
                    relative_path = script_file.relative_to(path)
                    skill.add_script(
                        path=str(relative_path),
                        content=content,
                        description=f"Script: {script_file.name}"
                    )
        
        # 解析参考文档
        if references_dir.exists():
            for ref_file in references_dir.iterdir():
                if ref_file.is_file():
                    content = self.read_file(ref_file)
                    relative_path = ref_file.relative_to(path)
                    skill.add_reference(
                        path=str(relative_path),
                        content=content,
                        description=f"Reference: {ref_file.name}"
                    )
        
        return skill
    
    def _parse_skill_md(self, file_path: Path) -> UniversalSkill:
        """
        解析SKILL.md文件
        
        Args:
            file_path: SKILL.md文件路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象
        """
        content = self.read_file(file_path)
        yaml_data, markdown_content = self.parse_yaml_frontmatter(content)
        
        # 提取基础信息
        skill_id = yaml_data.get("id", self.extract_id_from_path(file_path.parent))
        name = yaml_data.get("name", skill_id)
        description = yaml_data.get("description", "")
        
        # 提取变量
        variables = self.extract_variables(content)
        
        # 提取工具权限
        allowed_tools = self.extract_tools(yaml_data)
        
        # 创建skill对象
        skill = UniversalSkill(
            id=skill_id,
            name=name,
            description=description,
            description_zh=yaml_data.get("description_zh"),
            description_en=yaml_data.get("description_en"),
            version=yaml_data.get("version"),
            author=yaml_data.get("author"),
            tags=yaml_data.get("tags", []),
            instructions=markdown_content,
            allowed_tools=allowed_tools,
            variables=variables,
            source_platform=SkillPlatform.HERMES,
            source_path=str(file_path)
        )
        
        return skill
    
    def extract_variables(self, content: str) -> List[Variable]:
        """
        从内容中提取变量定义
        
        Hermes支持多种变量格式。
        
        Args:
            content: 指令内容文本
            
        Returns:
            List[Variable]: 提取的变量列表
        """
        variables = []
        
        # 匹配$VARIABLE_NAME格式
        pattern1 = r'\$([A-Z_]+)'
        matches1 = re.findall(pattern1, content)
        
        # 匹配{{variable_name}}格式
        pattern2 = r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}'
        matches2 = re.findall(pattern2, content)
        
        # 去重并创建变量对象
        seen = set()
        
        # 处理$格式变量
        for var_name in matches1:
            if var_name not in seen:
                seen.add(var_name)
                placeholder = f"${var_name}"
                required = var_name in ["ARGUMENTS"]
                description = self._get_variable_description(var_name)
                
                variable = Variable(
                    name=var_name.lower(),
                    placeholder=placeholder,
                    required=required,
                    description=description
                )
                variables.append(variable)
        
        # 处理{{}}格式变量
        for var_name in matches2:
            if var_name not in seen:
                seen.add(var_name)
                placeholder = f"{{{{{var_name}}}}}"
                required = var_name in ["args", "arguments"]
                description = self._get_variable_description(var_name)
                
                variable = Variable(
                    name=var_name,
                    placeholder=placeholder,
                    required=required,
                    description=description
                )
                variables.append(variable)
        
        return variables
    
    def _extract_variables_from_config(self, config: Dict[str, Any]) -> List[Variable]:
        """
        从配置中提取变量定义
        
        Args:
            config: YAML配置数据
            
        Returns:
            List[Variable]: 提取的变量列表
        """
        variables = []
        
        # 从parameters字段提取
        parameters = config.get("parameters", {})
        for param_name, param_config in parameters.items():
            if isinstance(param_config, dict):
                variable = Variable(
                    name=param_name,
                    placeholder=f"${param_name.upper()}",
                    required=param_config.get("required", False),
                    description=param_config.get("description"),
                    type=param_config.get("type", "string"),
                    default=param_config.get("default")
                )
            else:
                # 简单格式
                variable = Variable(
                    name=param_name,
                    placeholder=f"${param_name.upper()}",
                    required=False,
                    description=str(param_config)
                )
            variables.append(variable)
        
        return variables
    
    def extract_tools(self, content: str) -> List[ToolPermission]:
        """
        从内容中提取工具权限
        
        Args:
            content: 文件内容（YAML头或整个文件）
            
        Returns:
            List[ToolPermission]: 提取的工具权限列表
        """
        tools = []
        
        # 从YAML头提取
        if isinstance(content, dict):
            yaml_data = content
        else:
            yaml_data, _ = self.parse_yaml_frontmatter(content)
        
        # 从tools字段提取
        tools_config = yaml_data.get("tools", [])
        
        if isinstance(tools_config, list):
            for tool_config in tools_config:
                if isinstance(tool_config, str):
                    tool = ToolPermission(
                        name=tool_config,
                        category=self._categorize_tool(tool_config),
                        description=f"Hermes tool: {tool_config}"
                    )
                elif isinstance(tool_config, dict):
                    tool = ToolPermission(
                        name=tool_config.get("name", ""),
                        category=tool_config.get("category", "other"),
                        description=tool_config.get("description")
                    )
                tools.append(tool)
        
        return tools
    
    def _extract_tools_from_config(self, config: Dict[str, Any]) -> List[ToolPermission]:
        """
        从配置中提取工具权限
        
        Args:
            config: YAML配置数据
            
        Returns:
            List[ToolPermission]: 提取的工具权限列表
        """
        return self.extract_tools(config)
    
    def _get_variable_description(self, var_name: str) -> str:
        """获取变量描述"""
        descriptions = {
            # $格式变量
            "ARGUMENTS": "User-provided arguments",
            "CONTEXT": "Current context information",
            "FILE_PATH": "Path to the current file",
            "SELECTION": "Selected text in the editor",
            "WORKSPACE": "Workspace root path",
            "USER": "Current user information",
            
            # {{}}格式变量
            "args": "User-provided arguments",
            "arguments": "User-provided arguments",
            "context": "Current context information",
            "file_path": "Path to the current file",
            "selection": "Selected text",
            "workspace": "Workspace root path",
            "user": "Current user information"
        }
        return descriptions.get(var_name, f"Variable: {var_name}")
    
    def _categorize_tool(self, tool_name: str) -> str:
        """确定工具类别"""
        tool_categories = {
            # 文件操作
            "Read": "read",
            "Write": "write",
            "Edit": "write",
            "Glob": "read",
            "Grep": "read",
            
            # 执行操作
            "Bash": "bash",
            "PowerShell": "bash",
            
            # 交互操作
            "AskUserQuestion": "interaction",
            
            # 网络操作
            "WebFetch": "network",
            "WebSearch": "network",
            
            # 其他
            "Skill": "skill",
            "ToolSearch": "utility"
        }
        return tool_categories.get(tool_name, "other")


# 注册解析器
from skillporter.core.parser import register_parser
register_parser(HermesParser())
