"""
配置管理模块 - SkillPorter全局配置
=================================

管理用户设置、平台配置、LLM API密钥等。
支持配置文件的读取、写入和验证。

配置文件位置: ~/.skillporter/config.yaml

作者：Senior Developer (高级开发工程师)
版本：1.0.0
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """
    LLM API配置
    
    用于按需付费的LLM增强功能。
    用户需要自己提供API密钥。
    
    支持的提供商:
    - openai: OpenAI GPT系列
    - deepseek: DeepSeek系列（国产模型，推荐）
    - zhipu: 智谱GLM系列（国产模型）
    - anthropic: Claude系列
    - qwen: 通义千问系列（国产模型）
    """
    provider: str = "deepseek"  # 默认使用国产DeepSeek
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # 自定义API地址（用于私有部署或国内代理）
    model: str = "deepseek-chat"  # 默认DeepSeek Chat
    max_tokens: int = 1000
    temperature: float = 0.3
    enabled: bool = False  # 默认关闭，用户手动开启


# 支持的LLM模型配置
SUPPORTED_MODELS = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"],
        "default_model": "gpt-3.5-turbo"
    },
    "deepseek": {
        "name": "DeepSeek（推荐）",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
        "default_model": "deepseek-chat"
    },
    "zhipu": {
        "name": "智谱AI",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4", "glm-4-flash", "glm-3-turbo"],
        "default_model": "glm-4-flash"
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"],
        "default_model": "qwen-turbo"
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
        "default_model": "claude-3-haiku-20240307"
    },
    "google": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
        "default_model": "gemini-1.5-flash"
    },
    "kimi": {
        "name": "Kimi（月之暗面）",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "default_model": "moonshot-v1-8k"
    },
    "mimo": {
        "name": "小米MiMo",
        "base_url": "https://api.mimo.ai/v1",
        "models": ["mimo-7b", "mimo-13b", "mimo-70b"],
        "default_model": "mimo-7b"
    }
}


@dataclass
class PlatformConfig:
    """
    平台配置
    
    存储各个AI平台的路径和设置。
    """
    workbuddy_path: str = "~/.workbuddy/skills/"
    claude_path: str = "~/.claude/skills/"
    codex_path: str = "~/.codex/skills/"
    
    # 平台特定设置
    workbuddy_settings: Dict[str, Any] = field(default_factory=dict)
    claude_settings: Dict[str, Any] = field(default_factory=dict)
    codex_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitConfig:
    """
    Git集成配置
    
    用于向后兼容和版本控制。
    """
    enabled: bool = True
    auto_commit: bool = False
    commit_message_template: str = "SkillPorter: Convert {skill_id} from {source} to {target}"


@dataclass
class SkillPorterConfig:
    """
    SkillPorter主配置
    
    包含所有配置项，支持序列化到YAML文件。
    """
    # 基础配置
    version: str = "1.0.0"
    config_dir: str = "~/.skillporter"
    
    # 子配置
    llm: LLMConfig = field(default_factory=LLMConfig)
    platforms: PlatformConfig = field(default_factory=PlatformConfig)
    git: GitConfig = field(default_factory=GitConfig)
    
    # 用户偏好
    default_source_platform: Optional[str] = None
    default_target_platform: Optional[str] = None
    verbose: bool = False
    color_output: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "version": self.version,
            "config_dir": self.config_dir,
            "llm": {
                "provider": self.llm.provider,
                "api_key": self.llm.api_key,
                "model": self.llm.model,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
                "enabled": self.llm.enabled
            },
            "platforms": {
                "workbuddy_path": self.platforms.workbuddy_path,
                "claude_path": self.platforms.claude_path,
                "codex_path": self.platforms.codex_path,
                "workbuddy_settings": self.platforms.workbuddy_settings,
                "claude_settings": self.platforms.claude_settings,
                "codex_settings": self.platforms.codex_settings
            },
            "git": {
                "enabled": self.git.enabled,
                "auto_commit": self.git.auto_commit,
                "commit_message_template": self.git.commit_message_template
            },
            "default_source_platform": self.default_source_platform,
            "default_target_platform": self.default_target_platform,
            "verbose": self.verbose,
            "color_output": self.color_output
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SkillPorterConfig':
        """从字典创建配置实例"""
        config = cls()
        
        # 更新版本和目录
        config.version = data.get("version", config.version)
        config.config_dir = data.get("config_dir", config.config_dir)
        
        # 更新LLM配置
        llm_data = data.get("llm", {})
        config.llm = LLMConfig(
            provider=llm_data.get("provider", config.llm.provider),
            api_key=llm_data.get("api_key", config.llm.api_key),
            model=llm_data.get("model", config.llm.model),
            max_tokens=llm_data.get("max_tokens", config.llm.max_tokens),
            temperature=llm_data.get("temperature", config.llm.temperature),
            enabled=llm_data.get("enabled", config.llm.enabled)
        )
        
        # 更新平台配置
        platforms_data = data.get("platforms", {})
        config.platforms = PlatformConfig(
            workbuddy_path=platforms_data.get("workbuddy_path", config.platforms.workbuddy_path),
            claude_path=platforms_data.get("claude_path", config.platforms.claude_path),
            codex_path=platforms_data.get("codex_path", config.platforms.codex_path),
            workbuddy_settings=platforms_data.get("workbuddy_settings", {}),
            claude_settings=platforms_data.get("claude_settings", {}),
            codex_settings=platforms_data.get("codex_settings", {})
        )
        
        # 更新Git配置
        git_data = data.get("git", {})
        config.git = GitConfig(
            enabled=git_data.get("enabled", config.git.enabled),
            auto_commit=git_data.get("auto_commit", config.git.auto_commit),
            commit_message_template=git_data.get("commit_message_template", config.git.commit_message_template)
        )
        
        # 更新用户偏好
        config.default_source_platform = data.get("default_source_platform")
        config.default_target_platform = data.get("default_target_platform")
        config.verbose = data.get("verbose", config.verbose)
        config.color_output = data.get("color_output", config.color_output)
        
        return config


class ConfigManager:
    """
    配置管理器
    
    负责配置文件的读取、写入和验证。
    支持多级配置（全局、项目、环境变量）。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为 ~/.skillporter/config.yaml
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / ".skillporter" / "config.yaml"
        
        self.config: Optional[SkillPorterConfig] = None
    
    def load_config(self) -> SkillPorterConfig:
        """
        加载配置文件
        
        如果配置文件不存在，创建默认配置。
        
        Returns:
            SkillPorterConfig: 配置实例
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                self.config = SkillPorterConfig.from_dict(data)
            except (yaml.YAMLError, IOError) as e:
                print(f"Warning: Could not load config file: {e}")
                self.config = SkillPorterConfig()
        else:
            self.config = SkillPorterConfig()
        
        # 应用环境变量覆盖
        self._apply_env_vars()
        
        return self.config
    
    def save_config(self, config: Optional[SkillPorterConfig] = None) -> None:
        """
        保存配置到文件
        
        Args:
            config: 要保存的配置实例，如果为None则保存当前配置
        """
        if config:
            self.config = config
        
        if not self.config:
            raise ValueError("No config to save")
        
        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存到文件
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config.to_dict(), f, default_flow_style=False, allow_unicode=True)
        
        print(f"Config saved to: {self.config_path}")
    
    def get_config(self) -> SkillPorterConfig:
        """
        获取当前配置
        
        如果未加载，先加载配置。
        
        Returns:
            SkillPorterConfig: 配置实例
        """
        if not self.config:
            self.load_config()
        return self.config
    
    def update_config(self, **kwargs) -> None:
        """
        更新配置项
        
        Args:
            **kwargs: 要更新的配置项
        """
        if not self.config:
            self.load_config()
        
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif "." in key:
                # 支持嵌套配置，如 "llm.api_key"
                parts = key.split(".")
                obj = self.config
                for part in parts[:-1]:
                    if hasattr(obj, part):
                        obj = getattr(obj, part)
                    else:
                        break
                else:
                    if hasattr(obj, parts[-1]):
                        setattr(obj, parts[-1], value)
    
    def _apply_env_vars(self) -> None:
        """
        应用环境变量覆盖
        
        支持的环境变量：
        - SKILLPORTER_LLM_API_KEY: LLM API密钥
        - SKILLPORTER_LLM_PROVIDER: LLM提供商
        - SKILLPORTER_WORKBUDDY_PATH: WorkBuddy skills路径
        - SKILLPORTER_CLAUDE_PATH: Claude skills路径
        - SKILLPORTER_CODEX_PATH: Codex skills路径
        """
        if not self.config:
            return
        
        # LLM配置
        if os.getenv("SKILLPORTER_LLM_API_KEY"):
            self.config.llm.api_key = os.getenv("SKILLPORTER_LLM_API_KEY")
            self.config.llm.enabled = True
        
        if os.getenv("SKILLPORTER_LLM_PROVIDER"):
            self.config.llm.provider = os.getenv("SKILLPORTER_LLM_PROVIDER")
        
        # 平台路径
        if os.getenv("SKILLPORTER_WORKBUDDY_PATH"):
            self.config.platforms.workbuddy_path = os.getenv("SKILLPORTER_WORKBUDDY_PATH")
        
        if os.getenv("SKILLPORTER_CLAUDE_PATH"):
            self.config.platforms.claude_path = os.getenv("SKILLPORTER_CLAUDE_PATH")
        
        if os.getenv("SKILLPORTER_CODEX_PATH"):
            self.config.platforms.codex_path = os.getenv("SKILLPORTER_CODEX_PATH")
    
    def validate_config(self) -> List[str]:
        """
        验证配置的有效性
        
        Returns:
            List[str]: 错误消息列表，空列表表示验证通过
        """
        if not self.config:
            self.load_config()
        
        errors = []
        
        # 验证LLM配置（如果启用）
        if self.config.llm.enabled:
            if not self.config.llm.api_key:
                errors.append("LLM API key is required when LLM is enabled")
            if not self.config.llm.provider:
                errors.append("LLM provider is required when LLM is enabled")
        
        # 验证平台路径
        for platform_name, path in [
            ("workbuddy", self.config.platforms.workbuddy_path),
            ("claude", self.config.platforms.claude_path),
            ("codex", self.config.platforms.codex_path)
        ]:
            try:
                expanded_path = Path(path).expanduser()
                # 这里只是验证路径格式，不检查是否存在
            except Exception as e:
                errors.append(f"Invalid {platform_name} path: {e}")
        
        return errors


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config() -> SkillPorterConfig:
    """获取全局配置"""
    return config_manager.get_config()


def update_config(**kwargs) -> None:
    """更新全局配置"""
    config_manager.update_config(**kwargs)


def save_config() -> None:
    """保存全局配置"""
    config_manager.save_config()


def get_supported_providers() -> Dict[str, Dict[str, Any]]:
    """获取支持的LLM提供商列表"""
    return SUPPORTED_MODELS


def get_provider_models(provider: str) -> List[str]:
    """获取指定提供商的模型列表"""
    if provider in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[provider]["models"]
    return []


def setup_llm(provider: str, api_key: str, model: Optional[str] = None, base_url: Optional[str] = None) -> None:
    """
    快速设置LLM配置
    
    Args:
        provider: 提供商名称 (openai/deepseek/zhipu/qwen/anthropic)
        api_key: API密钥
        model: 模型名称（可选，使用默认模型）
        base_url: 自定义API地址（可选）
    """
    if provider not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported provider: {provider}. Supported: {list(SUPPORTED_MODELS.keys())}")
    
    provider_info = SUPPORTED_MODELS[provider]
    
    update_config(**{
        "llm.provider": provider,
        "llm.api_key": api_key,
        "llm.model": model or provider_info["default_model"],
        "llm.base_url": base_url or provider_info["base_url"],
        "llm.enabled": True
    })
    save_config()