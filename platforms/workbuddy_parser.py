"""
WorkBuddy平台解析器 - 解析WorkBuddy格式的Skill文件
==================================================

WorkBuddy的skill文件结构：
- 位置: ~/.workbuddy/skills/{skill-name}/SKILL.md
- 格式: Markdown + YAML前言
- 变量: $ARGUMENTS 或其他
- 工具: 在YAML前言的allowed-tools字段中定义

WorkBuddy skill特点：
1. 支持中英文双语描述（description_zh, description_en）
2. 支持更丰富的元数据字段
3. 变量语法与Claude类似
4. 工具权限在YAML前言中定义

作者：Senior Developer (高级开发工程师)
版本：1.0.0
"""

import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import yaml

from ..core.parser import BaseParser
from ..core.schema import UniversalSkill, SkillPlatform, Variable, ToolPermission, ResourceFile


class WorkBuddyParser(BaseParser):
    """
    WorkBuddy Skill解析器
    
    解析WorkBuddy格式的skill文件，转换为通用Skill格式。
    """
    
    @property
    def platform(self) -> SkillPlatform:
        """返回支持的平台类型"""
        return SkillPlatform.WORKBUDDY
    
    def parse_file(self, file_path: Union[str, Path]) -> UniversalSkill:
        """
        解析单个WorkBuddy skill文件
        
        WorkBuddy skill文件通常是SKILL.md，包含YAML前言和Markdown内容。
        
        Args:
            file_path: SKILL.md文件路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"WorkBuddy skill file not found: {file_path}")
        
        content = self.read_file(path)
        yaml_data, markdown_content = self.parse_yaml_frontmatter(content)
        
        # 提取基础信息
        skill_id = yaml_data.get("id", self.extract_id_from_path(path.parent))
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
            source_platform=SkillPlatform.WORKBUDDY,
            source_path=str(path)
        )
        
        # 提取平台特有字段
        platform_overrides = {}
        for key, value in yaml_data.items():
            if key not in ["id", "name", "description", "description_zh", "description_en",
                          "version", "author", "tags", "allowed-tools"]:
                platform_overrides[key] = value
        
        if platform_overrides:
            skill.set_platform_override(SkillPlatform.WORKBUDDY, platform_overrides)
        
        # 验证skill
        if not self.validate_skill(skill):
            errors = self.get_errors()
            raise ValueError(f"Invalid WorkBuddy skill: {'; '.join(errors)}")
        
        return skill
    
    def parse_directory(self, dir_path: Union[str, Path]) -> UniversalSkill:
        """
        解析整个WorkBuddy skill目录
        
        WorkBuddy skill目录结构：
        {skill-name}/
        ├── SKILL.md           # 主skill文件
        ├── scripts/           # 脚本目录（可选）
        │   └── *.py, *.sh等
        └── references/        # 参考文档（可选）
            └── *.md, *.txt等
        
        Args:
            dir_path: skill目录路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象，包含所有资源文件
        """
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"WorkBuddy skill directory not found: {dir_path}")
        
        # 查找SKILL.md文件
        skill_file = path / "SKILL.md"
        if not skill_file.exists():
            # 尝试查找其他.md文件
            md_files = list(path.glob("*.md"))
            if md_files:
                skill_file = md_files[0]
            else:
                raise FileNotFoundError(f"No SKILL.md found in {dir_path}")
        
        # 解析主文件
        skill = self.parse_file(skill_file)
        
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
    
    def extract_variables(self, content: str) -> List[Variable]:
        """
        从内容中提取变量定义
        
        WorkBuddy支持多种变量格式：
        - $VARIABLE_NAME（类似Claude）
        - {{variable_name}}（类似Codex）
        
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
    
    def extract_tools(self, yaml_data: Dict[str, Any]) -> List[ToolPermission]:
        """
        从YAML数据中提取工具权限
        
        WorkBuddy在YAML前言的allowed-tools字段中定义工具权限。
        
        Args:
            yaml_data: YAML前言数据
            
        Returns:
            List[ToolPermission]: 提取的工具权限列表
        """
        tools = []
        
        # 获取allowed-tools字段
        allowed_tools = yaml_data.get("allowed-tools", [])
        
        if isinstance(allowed_tools, str):
            # 如果是字符串，按逗号分割
            allowed_tools = [t.strip() for t in allowed_tools.split(",")]
        
        for tool_name in allowed_tools:
            if not tool_name:
                continue
            
            # 确定工具类别
            category = self._categorize_tool(tool_name)
            
            tool = ToolPermission(
                name=tool_name,
                category=category,
                description=f"WorkBuddy tool: {tool_name}"
            )
            tools.append(tool)
        
        return tools
    
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
from ..core.parser import register_parser
register_parser(WorkBuddyParser())