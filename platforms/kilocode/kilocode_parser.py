"""
KiloCode平台解析器 - 解析KiloCode格式的Skill文件
================================================

KiloCode的skill文件结构：
- 位置: .kilo/rules/*.md
- 格式: YAML前言 + Markdown内容
- 变量: 无特定变量语法
- 工具: 无特定工具定义

KiloCode skill特点：
1. 使用.kilo/rules/目录存放规则文件
2. 支持.md格式
3. 源自Roo Code，规则格式兼容
4. 主要用于定义编码规范和项目规则

作者：Ccc
版本：1.0.0
"""

import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import yaml

from skillporter.core.parser import BaseParser
from skillporter.core.schema import UniversalSkill, SkillPlatform, Variable, ToolPermission, ResourceFile


class KiloCodeParser(BaseParser):
    """
    KiloCode Skill解析器
    
    解析KiloCode格式的skill文件，转换为通用Skill格式。
    """
    
    @property
    def platform(self) -> SkillPlatform:
        """返回支持的平台类型"""
        return SkillPlatform.KILOCODE
    
    def parse_file(self, file_path: Union[str, Path]) -> UniversalSkill:
        """
        解析单个KiloCode skill文件
        
        KiloCode skill文件通常是.md格式。
        
        Args:
            file_path: skill文件路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"KiloCode skill file not found: {file_path}")
        
        content = self.read_file(path)
        
        # 尝试解析YAML前言
        yaml_data, markdown_content = self.parse_yaml_frontmatter(content)
        
        # 如果没有YAML前言，整个内容都是指令
        if not yaml_data:
            markdown_content = content
        
        # 提取基础信息
        skill_id = yaml_data.get("id", self.extract_id_from_path(file_path))
        name = yaml_data.get("name", skill_id)
        description = yaml_data.get("description", "KiloCode rules")
        
        # 提取变量
        variables = self.extract_variables(content)
        
        # 提取工具权限（KiloCode通常不定义工具）
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
            source_platform=SkillPlatform.KILOCODE,
            source_path=str(file_path)
        )
        
        # 提取平台特有字段
        platform_overrides = {}
        for key, value in yaml_data.items():
            if key not in ["id", "name", "description", "description_zh", "description_en",
                          "version", "author", "tags", "allowed-tools"]:
                platform_overrides[key] = value
        
        if platform_overrides:
            skill.set_platform_override(SkillPlatform.KILOCODE, platform_overrides)
        
        # 验证skill
        if not self.validate_skill(skill):
            errors = self.get_errors()
            raise ValueError(f"Invalid KiloCode skill: {'; '.join(errors)}")
        
        return skill
    
    def parse_directory(self, dir_path: Union[str, Path]) -> UniversalSkill:
        """
        解析整个KiloCode skill目录
        
        KiloCode skill目录结构：
        {skill-name}/
        ├── .kilo/rules/       # 规则目录
        │   ├── 01-coding.md   # 规则文件
        │   ├── 02-style.md
        │   └── ...
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
            raise FileNotFoundError(f"KiloCode skill directory not found: {dir_path}")
        
        # 查找.kilo/rules目录
        kilo_rules_dir = path / ".kilo" / "rules"
        if not kilo_rules_dir.exists():
            # 尝试查找其他.md文件
            md_files = list(path.glob("*.md"))
            if md_files:
                return self.parse_file(md_files[0])
            else:
                raise FileNotFoundError(f"No .kilo/rules directory found in {dir_path}")
        
        # 收集所有规则文件
        rule_files = sorted(kilo_rules_dir.glob("*.md"))
        
        if not rule_files:
            raise FileNotFoundError(f"No rule files found in {kilo_rules_dir}")
        
        # 合并所有规则文件内容
        combined_content = ""
        for rule_file in rule_files:
            content = self.read_file(rule_file)
            combined_content += f"\n\n---\n\n{content}"
        
        # 提取变量
        variables = self.extract_variables(combined_content)
        
        # 创建skill对象
        skill = UniversalSkill(
            id=self.extract_id_from_path(path),
            name=path.name,
            description="KiloCode rules collection",
            instructions=combined_content,
            variables=variables,
            source_platform=SkillPlatform.KILOCODE,
            source_path=str(path)
        )
        
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
        
        KiloCode不支持特定的变量语法，但可以识别一些通用模式。
        
        Args:
            content: 指令内容文本
            
        Returns:
            List[Variable]: 提取的变量列表
        """
        variables = []
        
        # 匹配$VARIABLE_NAME格式（兼容Claude）
        pattern1 = r'\$([A-Z_]+)'
        matches1 = re.findall(pattern1, content)
        
        # 匹配{{variable_name}}格式（兼容Codex）
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
        
        KiloCode通常不定义工具权限。
        
        Args:
            yaml_data: YAML前言数据
            
        Returns:
            List[ToolPermission]: 提取的工具权限列表
        """
        tools = []
        
        # 从allowed-tools字段提取（如果存在）
        allowed_tools = yaml_data.get("allowed-tools", [])
        
        if isinstance(allowed_tools, str):
            allowed_tools = [t.strip() for t in allowed_tools.split(",")]
        
        for tool_name in allowed_tools:
            if not tool_name:
                continue
            
            category = self._categorize_tool(tool_name)
            
            tool = ToolPermission(
                name=tool_name,
                category=category,
                description=f"KiloCode tool: {tool_name}"
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
from skillporter.core.parser import register_parser
register_parser(KiloCodeParser())
