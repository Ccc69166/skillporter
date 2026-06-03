"""
Universal Skill Schema (USS) - 跨平台通用Skill数据结构
==================================================

这是SkillPorter工具的核心数据结构，定义了能兼容所有AI平台的通用Skill表示。
所有平台的skill文件都会先被解析成USS格式，然后再转换为目标平台的格式。

设计原则：
1. 平台无关性：不偏向任何特定平台
2. 可扩展性：通过platform_overrides支持平台特有字段
3. 完整性：包含skill的所有必要信息（指令、变量、资源文件等）

作者：Senior Developer (高级开发工程师)
版本：1.0.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import json
import yaml


class SkillPlatform(Enum):
    """支持的AI平台枚举"""
    WORKBUDDY = "workbuddy"
    CLAUDE = "claude"
    CODEX = "codex"


class VariableType(Enum):
    """变量类型枚举"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class Variable:
    """
    Skill变量定义
    
    用于描述skill中的占位符变量，支持不同平台的变量语法转换。
    例如：Claude的 $ARGUMENTS <-> Codex的 {{args}}
    
    属性:
        name: 变量名称（如 "arguments"）
        placeholder: 占位符语法（如 "$ARGUMENTS" 或 "{{args}}"）
        required: 是否必需
        description: 变量描述
        type: 变量类型
        default: 默认值
    """
    name: str
    placeholder: str
    required: bool = True
    description: Optional[str] = None
    type: VariableType = VariableType.STRING
    default: Optional[Any] = None


@dataclass
class ResourceFile:
    """
    资源文件定义
    
    用于描述skill附带的脚本或参考文档。
    支持相对路径和绝对路径。
    
    属性:
        path: 文件路径（相对于skill目录）
        content: 文件内容
        file_type: 文件类型（script/reference）
        description: 文件描述
    """
    path: str
    content: str
    file_type: str = "script"  # "script" 或 "reference"
    description: Optional[str] = None


@dataclass
class ToolPermission:
    """
    工具权限定义
    
    定义skill可以使用的工具和权限。
    不同平台的工具名称不同，需要映射转换。
    
    属性:
        name: 工具名称（在目标平台中的名称）
        category: 工具类别（read/write/bash/mcp等）
        description: 工具描述
        platform_specific: 平台特有配置
    """
    name: str
    category: str
    description: Optional[str] = None
    platform_specific: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UniversalSkill:
    """
    通用Skill数据结构（USS）
    
    这是跨平台Skill的核心表示，包含所有平台共有的字段。
    平台特有字段应放在platform_overrides中。
    
    使用示例:
        skill = UniversalSkill(
            id="my-skill",
            name="My Skill",
            description="A sample skill",
            instructions="# Instructions\\nDo something...",
            allowed_tools=[ToolPermission("Read", "read")]
        )
    """
    
    # === 基础标识字段 ===
    id: str  # 唯一标识符
    name: str  # 显示名称
    description: str = ""  # 技能描述（可选）
    
    # === 可选元数据 ===
    description_zh: Optional[str] = None  # 中文描述
    description_en: Optional[str] = None  # 英文描述
    version: Optional[str] = None  # 版本号
    author: Optional[str] = None  # 作者
    tags: List[str] = field(default_factory=list)  # 标签
    
    # === 权限与工具 ===
    allowed_tools: List[ToolPermission] = field(default_factory=list)
    
    # === 指令主体 ===
    instructions: str = ""  # Markdown格式的指令文本
    
    # === 变量定义 ===
    variables: List[Variable] = field(default_factory=list)
    
    # === 附加资源 ===
    scripts: List[ResourceFile] = field(default_factory=list)
    references: List[ResourceFile] = field(default_factory=list)
    
    # === 平台特有覆写 ===
    platform_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # === 转换元数据 ===
    source_platform: Optional[SkillPlatform] = None  # 来源平台
    source_path: Optional[str] = None  # 原始文件路径
    conversion_history: List[Dict[str, Any]] = field(default_factory=list)  # 转换历史
    
    def add_tool(self, name: str, category: str, description: Optional[str] = None) -> None:
        """添加工具权限"""
        tool = ToolPermission(name=name, category=category, description=description)
        self.allowed_tools.append(tool)
    
    def add_variable(self, name: str, placeholder: str, required: bool = True, 
                    description: Optional[str] = None) -> None:
        """添加变量定义"""
        variable = Variable(
            name=name,
            placeholder=placeholder,
            required=required,
            description=description
        )
        self.variables.append(variable)
    
    def add_script(self, path: str, content: str, description: Optional[str] = None) -> None:
        """添加脚本文件"""
        script = ResourceFile(
            path=path,
            content=content,
            file_type="script",
            description=description
        )
        self.scripts.append(script)
    
    def add_reference(self, path: str, content: str, description: Optional[str] = None) -> None:
        """添加参考文档"""
        reference = ResourceFile(
            path=path,
            content=content,
            file_type="reference",
            description=description
        )
        self.references.append(reference)
    
    def get_platform_override(self, platform: SkillPlatform) -> Dict[str, Any]:
        """获取平台特有配置"""
        return self.platform_overrides.get(platform.value, {})
    
    def set_platform_override(self, platform: SkillPlatform, config: Dict[str, Any]) -> None:
        """设置平台特有配置"""
        self.platform_overrides[platform.value] = config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "description_zh": self.description_zh,
            "description_en": self.description_en,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "instructions": self.instructions,
            "allowed_tools": [
                {
                    "name": tool.name,
                    "category": tool.category,
                    "description": tool.description,
                    "platform_specific": tool.platform_specific
                }
                for tool in self.allowed_tools
            ],
            "variables": [
                {
                    "name": var.name,
                    "placeholder": var.placeholder,
                    "required": var.required,
                    "description": var.description,
                    "type": var.type.value,
                    "default": var.default
                }
                for var in self.variables
            ],
            "scripts": [
                {
                    "path": script.path,
                    "content": script.content,
                    "file_type": script.file_type,
                    "description": script.description
                }
                for script in self.scripts
            ],
            "references": [
                {
                    "path": ref.path,
                    "content": ref.content,
                    "file_type": ref.file_type,
                    "description": ref.description
                }
                for ref in self.references
            ],
            "platform_overrides": self.platform_overrides,
            "source_platform": self.source_platform.value if self.source_platform else None,
            "source_path": self.source_path,
            "conversion_history": self.conversion_history
        }
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON格式"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def to_yaml(self) -> str:
        """转换为YAML格式"""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UniversalSkill':
        """从字典创建USS实例"""
        # 解析工具权限
        allowed_tools = []
        for tool_data in data.get("allowed_tools", []):
            tool = ToolPermission(
                name=tool_data["name"],
                category=tool_data["category"],
                description=tool_data.get("description"),
                platform_specific=tool_data.get("platform_specific", {})
            )
            allowed_tools.append(tool)
        
        # 解析变量
        variables = []
        for var_data in data.get("variables", []):
            variable = Variable(
                name=var_data["name"],
                placeholder=var_data["placeholder"],
                required=var_data.get("required", True),
                description=var_data.get("description"),
                type=VariableType(var_data.get("type", "string")),
                default=var_data.get("default")
            )
            variables.append(variable)
        
        # 解析资源文件
        scripts = []
        for script_data in data.get("scripts", []):
            script = ResourceFile(
                path=script_data["path"],
                content=script_data["content"],
                file_type=script_data.get("file_type", "script"),
                description=script_data.get("description")
            )
            scripts.append(script)
        
        references = []
        for ref_data in data.get("references", []):
            reference = ResourceFile(
                path=ref_data["path"],
                content=ref_data["content"],
                file_type=ref_data.get("file_type", "reference"),
                description=ref_data.get("description")
            )
            references.append(reference)
        
        # 创建实例
        skill = cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            description_zh=data.get("description_zh"),
            description_en=data.get("description_en"),
            version=data.get("version"),
            author=data.get("author"),
            tags=data.get("tags", []),
            instructions=data.get("instructions", ""),
            allowed_tools=allowed_tools,
            variables=variables,
            scripts=scripts,
            references=references,
            platform_overrides=data.get("platform_overrides", {}),
            source_platform=SkillPlatform(data["source_platform"]) if data.get("source_platform") else None,
            source_path=data.get("source_path"),
            conversion_history=data.get("conversion_history", [])
        )
        
        return skill
    
    @classmethod
    def from_json(cls, json_str: str) -> 'UniversalSkill':
        """从JSON字符串创建USS实例"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'UniversalSkill':
        """从YAML字符串创建USS实例"""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
    
    def validate(self) -> List[str]:
        """验证USS数据的完整性，返回错误列表"""
        errors = []
        
        # 必需字段检查
        if not self.id:
            errors.append("id is required")
        if not self.name:
            errors.append("name is required")
        
        # ID格式检查（允许中文和基本字符，只禁止危险字符）
        if self.id:
            import re as _re
            # 只检查是否包含控制字符或路径分隔符等危险字符
            if _re.search(r'[\x00-\x1f/\\<>:"|?*]', self.id):
                errors.append(f"id contains invalid characters: {self.id}")
        
        # 版本格式检查（如果提供）
        if self.version:
            parts = self.version.split(".")
            if len(parts) != 3 or not all(part.isdigit() for part in parts):
                errors.append("version must be in semantic format (e.g., 1.0.0)")
        
        # 变量占位符检查
        for var in self.variables:
            if not var.placeholder:
                errors.append(f"variable '{var.name}' must have a placeholder")
        
        return errors
    
    def __str__(self) -> str:
        return f"UniversalSkill(id='{self.id}', name='{self.name}', version='{self.version}')"
    
    def __repr__(self) -> str:
        return self.__str__()


# 便捷函数
def create_skill(id: str, name: str, description: str, instructions: str = "") -> UniversalSkill:
    """快速创建skill实例"""
    return UniversalSkill(
        id=id,
        name=name,
        description=description,
        instructions=instructions
    )


def load_skill_from_file(file_path: str) -> UniversalSkill:
    """从文件加载skill（支持JSON和YAML）"""
    import pathlib
    
    path = pathlib.Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Skill file not found: {file_path}")
    
    content = path.read_text(encoding="utf-8")
    
    if path.suffix.lower() == ".json":
        return UniversalSkill.from_json(content)
    elif path.suffix.lower() in [".yaml", ".yml"]:
        return UniversalSkill.from_yaml(content)
    else:
        # 尝试JSON，失败则尝试YAML
        try:
            return UniversalSkill.from_json(content)
        except json.JSONDecodeError:
            return UniversalSkill.from_yaml(content)


def save_skill_to_file(skill: UniversalSkill, file_path: str) -> None:
    """保存skill到文件（根据扩展名选择格式）"""
    import pathlib
    
    path = pathlib.Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if path.suffix.lower() == ".json":
        content = skill.to_json()
    elif path.suffix.lower() in [".yaml", ".yml"]:
        content = skill.to_yaml()
    else:
        # 默认使用JSON
        content = skill.to_json()
        path = path.with_suffix(".json")
    
    path.write_text(content, encoding="utf-8")
    print(f"Skill saved to: {path}")