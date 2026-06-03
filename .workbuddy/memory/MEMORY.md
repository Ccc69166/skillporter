# SkillPorter 项目记忆

## 项目概述
SkillPorter 是一个跨平台 Skill 转换工具，用于在不同 AI 平台之间转换 skill 文件。

## 支持的平台（v2.1.0）
1. **Claude Code**: ~/.claude/skills/ 目录，SKILL.md 格式，$VARIABLE_NAME 变量语法
2. **OpenAI Codex**: ~/.codex/skills/ 目录，openai.yaml + AGENTS.md 格式，{{variable_name}} 变量语法
3. **WorkBuddy**: ~/.workbuddy/skills/ 目录，SKILL.md 格式，$VARIABLE_NAME 变量语法
4. **CodeBuddy**: ~/.codebuddy/skills/ 目录，SKILL.md 格式，与 WorkBuddy 完全兼容
5. **Cursor**: .cursorrules 或 .cursor/rules/*.mdc 格式，无特定变量语法
6. **Cline**: .clinerules/*.md 格式，无特定变量语法
7. **KiloCode**: .kilo/rules/*.md 格式，无特定变量语法
8. **Kimi Code Agent**: ~/.kimi/skills/ 目录，SKILL.md 格式，与 Claude Skills 兼容
9. **通义灵码CLI**: ~/.qwen/skills/ 目录，SKILL.md 格式，与 Claude Skills 兼容
10. **Hermes**: ~/.hermes/skills/ 目录，hermes.yaml 配置格式

## 技术架构
- **核心模块**: core/schema.py (USS数据结构), core/parser.py (解析器基类), core/renderer.py (渲染器基类)
- **平台实现**: platforms/ 目录下每个平台有独立的子文件夹，包含 parser.py 和 renderer.py
- **GUI**: PyQt6 实现，gui/ 目录，支持拖拽和平台选择
- **CLI**: 已移除，仅保留 GUI

## 关键设计
1. **Universal Skill Schema (USS)**: 跨平台通用数据结构
2. **解析器注册表**: 自动检测文件格式并选择合适的解析器
3. **渲染器注册表**: 根据目标平台选择渲染器
4. **变量转换**: 自动转换不同平台的变量语法

## 开发注意事项
- 新增平台需要: 1) 在 schema.py 添加枚举值 2) 在 platforms/ 下创建子文件夹实现 parser 和 renderer 3) 更新 GUI 的 PLATFORMS 字典
- 变量映射需要在 renderer 的 get_variable_mapping() 中定义
- 工具映射需要在 renderer 的 get_tool_mapping() 中定义
- 路径映射需要在 renderer 的 get_path_mapping() 中定义

## 版本历史
- v2.1.0: 添加 7 个新平台支持，重组目录结构，移除 CLI
- v2.0.0: 初始版本，支持 Claude Code、OpenAI Codex、WorkBuddy
