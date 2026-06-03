"""
Codex平台解析器 - 解析OpenAI Codex格式的Skill文件
================================================

Codex的skill文件结构：
- 位置: ~/.codex/skills/{skill-name}/
- 主文件: AGENTS.md 或 openai.yaml
- 格式: YAML配置 + Markdown指令
- 变量: {{args}}, {{context}}等
- 工具: 在openai.yaml中定义

Codex skill特点：
1. 使用openai.yaml作为配置文件
2. AGENTS.md作为主要指令文件
3. 支持parameters字段定义变量
4. 工具权限在配置中定义

作者：Senior Developer (高级开发工程师)
版本：1.0.0
"""

import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import yaml

from ..core.parser import BaseParser
from ..core.schema import UniversalSkill, SkillPlatform, Variable, ToolPermission, ResourceFile


class CodexParser(BaseParser):
    """
    Codex Skill解析器
    
    解析OpenAI Codex格式的skill文件，转换为通用Skill格式。
    """
    
    @property
    def platform(self) -> SkillPlatform:
        """返回支持的平台类型"""
        return SkillPlatform.CODEX
    
    def parse_file(self, file_path: Union[str, Path]) -> UniversalSkill:
        """
        解析单个Codex skill文件
        
        Codex skill可以是：
        1. openai.yaml（配置文件）
        2. AGENTS.md（指令文件）
        
        Args:
            file_path: skill文件路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Codex skill file not found: {file_path}")
        
        # 根据文件类型选择解析方式
        if path.name == "openai.yaml":
            return self._parse_openai_yaml(path)
        elif path.name == "AGENTS.md":
            return self._parse_agents_md(path)
        else:
            # 尝试自动检测
            content = self.read_file(path)
            if "openai" in content.lower() or "parameters" in content:
                return self._parse_openai_yaml(path)
            else:
                return self._parse_agents_md(path)
    
    def parse_directory(self, dir_path: Union[str, Path]) -> UniversalSkill:
        """
        解析整个Codex skill目录
        
        Codex skill目录结构：
        {skill-name}/
        ├── openai.yaml      # 配置文件（必需）
        ├── AGENTS.md         # 指令文件（可选）
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
            raise FileNotFoundError(f"Codex skill directory not found: {dir_path}")
        
        # 查找配置文件
        config_file = path / "openai.yaml"
        if not config_file.exists():
            # 尝试查找其他yaml文件
            yaml_files = list(path.glob("*.yaml")) + list(path.glob("*.yml"))
            if yaml_files:
                config_file = yaml_files[0]
            else:
                raise FileNotFoundError(f"No openai.yaml found in {dir_path}")
        
        # 解析配置文件
        skill = self._parse_openai_yaml(config_file)
        
        # 查找指令文件
        agents_file = path / "AGENTS.md"
        if agents_file.exists():
            agents_content = self.read_file(agents_file)
            _, instructions = self.parse_yaml_frontmatter(agents_content)
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
    
    def _parse_openai_yaml(self, file_path: Path) -> UniversalSkill:
        """
        解析openai.yaml配置文件
        
        Args:
            file_path: openai.yaml文件路径
            
        Returns:
            UniversalSkill: 解析后的通用skill对象
        """
        content = self.read_file(file_path)
        config = yaml.safe_load(content) or {}
        
        # 提取基础信息
        skill_id = config.get("id", self.extract_id_from_path(file_path.parent))
        name = config.get("name", skill_id)
        description = config.get("description", "")
        
        # 提取变量定义
        variables = self._extract_variables_from_config(config)
        
        # 提取工具权限
        allowed_tools = self._extract_tools_from_config(config)
        
        # 提取指令
        instructions = config.get("instructions", "")
        
        # 创建skill对象
        skill = UniversalSkill(
            id=skill_id,
            name=name,
            description=description,
            description_zh=config.get("description_zh"),
            description_en=config.get("description_en"),
            version=config.get("version"),
            author=config.get("author"),
            tags=config.get("tags", []),
            instructions=instructions,
            allowed_tools=allowed_tools,
            variables=variables,
            source_platform=SkillPlatform.CODEX,
            source_path=str(file_path)
        )
        
        # 提取平台特有字段
        platform_overrides = {}
        for key, value in config.items():
            if key not in ["id", "name", "description", "description_zh", "description_en",
                          "version", "author", "tags", "instructions", "parameters", "tools"]:
                platform_overrides[key] = value
        
        if platform_overrides:
            skill.set_platform_override(SkillPlatform.CODEX, platform_overrides)
        
        # 验证skill
        if not self.validate_skill(skill):
            errors = self.get_errors()
            raise ValueError(f"Invalid Codex skill: {'; '.join(errors)}")
        
        return skill
    
    def _parse_agents_md(self, file_path: Path) -> UniversalSkill:
        """
        解析AGENTS.md指令文件
        
        Args:
            file_path: AGENTS.md文件路径
            
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
            source_platform=SkillPlatform.CODEX,
            source_path=str(file_path)
        )
        
        return skill
    
    def extract_variables(self, content: str) -> List[Variable]:
        """
        从内容中提取变量定义
        
        Codex使用{{variable_name}}格式的变量。
        
        Args:
            content: 指令内容文本
            
        Returns:
            List[Variable]: 提取的变量列表
        """
        variables = []
        
        # 匹配Codex变量模式：{{variable_name}}
        pattern = r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}'
        matches = re.findall(pattern, content)
        
        # 去重并创建变量对象
        seen = set()
        for var_name in matches:
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
            config: openai.yaml配置数据
            
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
                    placeholder=f"{{{{{param_name}}}}}",
                    required=param_config.get("required", False),
                    description=param_config.get("description"),
                    type=param_config.get("type", "string"),
                    default=param_config.get("default")
                )
            else:
                # 简单格式
                variable = Variable(
                    name=param_name,
                    placeholder=f"{{{{{param_name}}}}}",
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
                        description=f"Codex tool: {tool_config}"
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
            config: openai.yaml配置数据
            
        Returns:
            List[ToolPermission]: 提取的工具权限列表
        """
        return self.extract_tools(config)
    
    def _get_variable_description(self, var_name: str) -> str:
        """获取变量描述"""
        descriptions = {
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
            "read_file": "read",
            "write_file": "write",
            "edit_file": "write",
            "list_files": "read",
            "search_files": "read",
            "search_content": "read",
            
            # 执行操作
            "execute_shell": "bash",
            "run_command": "bash",
            
            # 网络操作
            "fetch_url": "network",
            "search_web": "network",
            
            # 其他
            "ask_user": "interaction",
            "get_input": "interaction"
        }
        return tool_categories.get(tool_name, "other")


# 注册解析器
from ..core.parser import register_parser
register_parser(CodexParser())