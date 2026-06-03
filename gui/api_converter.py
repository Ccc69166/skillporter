"""
API 智能转换模块
================

当规则转换结果不满意时，使用 LLM API 进行智能转换。
支持 DeepSeek、智谱、通义千问、OpenAI、Anthropic。

费用极低：一个 skill 的转换大概消耗 500-1500 tokens，
DeepSeek deepseek-chat 大约 0.001-0.003 元/次。

作者：SkillPorter
版本：1.0.0
"""

import json
import re
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..config import get_config, SUPPORTED_MODELS


@dataclass
class APIConvertResult:
    """API 转换结果"""
    success: bool
    content: str = ""           # 转换后的完整文件内容
    error: str = ""             # 错误信息
    tokens_used: int = 0        # 消耗的 token 数
    cost_estimate: str = ""     # 费用估算


class APIConverter:
    """
    API 智能转换器
    
    将 skill 文件内容发送给 LLM，让它根据目标平台格式重新生成。
    作为规则转换的兜底方案。
    """

    # 各平台格式说明（喂给 LLM 的 prompt）
    PLATFORM_GUIDES = {
        "claude": """Claude Code Skill 格式要求：
1. 主文件必须是 SKILL.md
2. 使用 YAML frontmatter（---包裹）存储元数据
3. YAML 头包含：id, name, description, description_zh, description_en, version, author, tags
4. 工具权限在 YAML 头的 allowed-tools 字段，用列表格式
5. 工具名称：Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, WebFetch, WebSearch, PowerShell, Skill, ToolSearch
6. 变量语法：$ARGUMENTS, $CONTEXT, $FILE_PATH, $SELECTION, $WORKSPACE, $USER
7. 指令正文在 YAML 头之后，用 Markdown 格式
8. 安装路径：~/.claude/skills/{skill-name}/""",

        "workbuddy": """WorkBuddy Skill 格式要求：
1. 主文件必须是 SKILL.md
2. 使用 YAML frontmatter（---包裹）存储元数据
3. YAML 头包含：id, name, description, description_zh, description_en, version, author, tags
4. 工具权限在 YAML 头的 allowed-tools 字段，用列表格式
5. 工具名称：Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion, WebFetch, WebSearch, PowerShell, Skill, ToolSearch
6. 变量语法：$ARGUMENTS, $CONTEXT, $FILE_PATH, $SELECTION, $WORKSPACE, $USER
7. 指令正文在 YAML 头之后，用 Markdown 格式
8. 安装路径：~/.workbuddy/skills/{skill-name}/
9. 支持中英文双语描述（description_zh, description_en）""",

        "codex": """OpenAI Codex Skill 格式要求：
1. 使用两个文件：openai.yaml（配置）+ AGENTS.md（指令）
2. openai.yaml 包含：id, name, description, version, author, tags, parameters, tools
3. parameters 字段定义变量，每个变量有 type, required, description
4. tools 字段用对象列表格式，每个工具有 name, category, description
5. 工具名称：read_file, write_file, edit_file, list_files, search_files, search_content, execute_shell, run_command, fetch_url, search_web, ask_user, get_input
6. 变量语法：{{args}}, {{context}}, {{file_path}}, {{selection}}, {{workspace}}, {{user}}
7. AGENTS.md 使用 YAML frontmatter + Markdown 指令正文
8. 安装路径：~/.codex/skills/{skill-name}/"""
    }

    # 变量映射参考
    VARIABLE_MAP = {
        "$ARGUMENTS": "{{args}}",
        "$CONTEXT": "{{context}}",
        "$FILE_PATH": "{{file_path}}",
        "$SELECTION": "{{selection}}",
        "$WORKSPACE": "{{workspace}}",
        "$USER": "{{user}}",
    }

    # 工具映射参考
    TOOL_MAP = {
        "Read": "read_file",
        "Write": "write_file",
        "Edit": "edit_file",
        "Bash": "execute_shell",
        "Glob": "list_files",
        "Grep": "search_content",
        "AskUserQuestion": "ask_user",
        "WebFetch": "fetch_url",
        "WebSearch": "search_web",
        "PowerShell": "execute_shell",
    }

    def __init__(self):
        self._config = None

    @property
    def config(self):
        if self._config is None:
            self._config = get_config()
        return self._config

    def is_available(self) -> bool:
        """检查 API 是否可用（已配置且启用）"""
        return self.config.llm.enabled and bool(self.config.llm.api_key)

    def get_status(self) -> Dict[str, Any]:
        """获取 API 配置状态"""
        return {
            "enabled": self.config.llm.enabled,
            "provider": self.config.llm.provider,
            "model": self.config.llm.model,
            "has_key": bool(self.config.llm.api_key),
            "available": self.is_available(),
        }

    def convert(
        self,
        source_content: str,
        source_platform: str,
        target_platform: str,
        source_files: Optional[Dict[str, str]] = None,
    ) -> APIConvertResult:
        """
        使用 LLM API 转换 skill 内容

        Args:
            source_content: 源 SKILL.md 或主文件内容
            source_platform: 源平台 (claude/workbuddy/codex)
            target_platform: 目标平台
            source_files: 所有源文件 {路径: 内容}，用于多文件转换

        Returns:
            APIConvertResult: 转换结果
        """
        if not self.is_available():
            return APIConvertResult(
                success=False,
                error="API 未配置。请先在设置中配置 LLM API 密钥。"
            )

        # 构建 prompt
        prompt = self._build_prompt(
            source_content, source_platform, target_platform, source_files
        )

        # 调用 API
        try:
            response, tokens_used = self._call_api(prompt)
        except Exception as e:
            return APIConvertResult(
                success=False,
                error=f"API 调用失败: {str(e)}"
            )

        # 解析响应
        result = self._parse_response(response, target_platform)
        result.tokens_used = tokens_used
        result.cost_estimate = self._estimate_cost(tokens_used)

        return result

    def _build_prompt(
        self,
        source_content: str,
        source_platform: str,
        target_platform: str,
        source_files: Optional[Dict[str, str]] = None,
    ) -> str:
        """构建发送给 LLM 的 prompt"""

        target_guide = self.PLATFORM_GUIDES.get(target_platform, "")

        # 变量和工具映射表
        var_map_str = "\n".join(f"  {k} → {v}" for k, v in self.VARIABLE_MAP.items())
        tool_map_str = "\n".join(f"  {k} → {v}" for k, v in self.TOOL_MAP.items())

        prompt = f"""你是一个跨平台 AI Skill 格式转换专家。请将以下 {source_platform} 格式的 skill 转换为 {target_platform} 格式。

## 目标平台格式要求

{target_guide}

## 关键映射规则

变量映射：
{var_map_str}

工具名称映射：
{tool_map_str}

## 转换要求

1. 保持指令内容的语义完全不变，只调整格式
2. 正确转换所有变量占位符
3. 正确转换所有工具名称
4. 保留所有元数据（id, name, description, version, author, tags 等）
5. 如果目标平台支持 description_zh/description_en，保留它们
6. 输出格式要求见下方

## 输出格式

如果目标平台是 Claude 或 WorkBuddy，输出一个 SKILL.md 文件内容，用以下格式：
===FILE: SKILL.md===
(文件内容)
===END===

如果目标平台是 Codex，输出两个文件：
===FILE: openai.yaml===
(文件内容)
===END===
===FILE: AGENTS.md===
(文件内容)
===END===

如果源文件中有 scripts/ 或 references/ 目录下的文件，也要转换并输出：
===FILE: scripts/xxx.py===
(文件内容)
===END===

## 源文件内容

"""

        # 添加源文件
        if source_files and len(source_files) > 1:
            prompt += f"源 skill 包含 {len(source_files)} 个文件：\n\n"
            for file_path, content in source_files.items():
                prompt += f"===SOURCE: {file_path}===\n{content}\n===END===\n\n"
        else:
            prompt += f"```\n{source_content}\n```\n"

        prompt += "\n请直接输出转换后的文件内容，不要添加额外解释。"

        return prompt

    def _call_api(self, prompt: str) -> Tuple[str, int]:
        """
        调用 LLM API

        Returns:
            (response_content, tokens_used)
        """
        import urllib.request
        import urllib.error

        llm_config = self.config.llm
        provider_info = SUPPORTED_MODELS.get(llm_config.provider, {})
        base_url = llm_config.base_url or provider_info.get("base_url", "")
        model = llm_config.model

        # 构建请求
        url = f"{base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {llm_config.api_key}",
        }

        body = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的跨平台 AI Skill 格式转换工具。严格按照用户要求的格式输出，不要添加额外解释或 markdown 代码块。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": llm_config.max_tokens * 3,  # 转换需要更多 token
            "temperature": llm_config.temperature,
        }

        # Anthropic 使用不同格式
        if llm_config.provider == "anthropic":
            return self._call_anthropic_api(prompt, base_url, llm_config.api_key, model)

        # 发送请求
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        content = result["choices"][0]["message"]["content"]
        tokens_used = result.get("usage", {}).get("total_tokens", 0)

        return content, tokens_used

    def _call_anthropic_api(self, prompt: str, base_url: str, api_key: str, model: str) -> Tuple[str, int]:
        """Anthropic API 使用不同格式"""
        import urllib.request

        url = f"{base_url}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        body = {
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }

        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        content = result["content"][0]["text"]
        tokens_used = result.get("usage", {}).get("input_tokens", 0) + result.get("usage", {}).get("output_tokens", 0)

        return content, tokens_used

    def _parse_response(self, response: str, target_platform: str) -> APIConvertResult:
        """解析 LLM 响应，提取文件内容"""
        files = {}

        # 匹配 ===FILE: xxx=== ... ===END=== 格式
        pattern = r'===FILE:\s*(.+?)===\s*\n(.*?)===END==='
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            for file_path, content in matches:
                files[file_path.strip()] = content.strip()
        else:
            # 如果 LLM 没有按格式输出，尝试直接使用整个响应
            if target_platform in ("claude", "workbuddy"):
                files["SKILL.md"] = response.strip()
            else:
                # Codex 有两个文件，这种情况比较棘手
                # 尝试按 --- 分割
                parts = response.split("---\nopenai.yaml")
                if len(parts) >= 2:
                    files["openai.yaml"] = "openai.yaml".join(parts[1].split("AGENTS.md")[0]).strip()
                    if "AGENTS.md" in response:
                        files["AGENTS.md"] = response.split("AGENTS.md")[1].strip()
                else:
                    files["SKILL.md"] = response.strip()

        if not files:
            return APIConvertResult(
                success=False,
                error="无法从 API 响应中提取文件内容"
            )

        # 返回主文件内容
        main_file = "SKILL.md" if target_platform != "codex" else "openai.yaml"
        main_content = files.get(main_file, "")

        # 将所有文件信息编码到 content 中
        if len(files) > 1:
            # 多文件：用特殊标记分隔
            combined = ""
            for path, content in files.items():
                combined += f"===FILE:{path}===\n{content}\n===END===\n"
            main_content = combined

        return APIConvertResult(
            success=True,
            content=main_content,
        )

    def _estimate_cost(self, tokens_used: int) -> str:
        """估算费用（人民币）"""
        if tokens_used == 0:
            return "未知"

        provider = self.config.llm.provider

        # 每百万 token 的价格（人民币，大致）
        price_map = {
            "deepseek": 1.0,      # deepseek-chat 约 1元/百万token
            "zhipu": 5.0,          # glm-4-flash 约 5元/百万token
            "qwen": 2.0,           # qwen-turbo 约 2元/百万token
            "openai": 7.0,         # gpt-3.5-turbo 约 7元/百万token
            "anthropic": 1.5,      # claude-3-haiku 约 1.5元/百万token
        }

        price_per_million = price_map.get(provider, 5.0)
        cost = (tokens_used / 1_000_000) * price_per_million

        if cost < 0.01:
            return f"约 ¥{cost:.4f}"
        return f"约 ¥{cost:.2f}"
