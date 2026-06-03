# SkillPorter

跨平台 Skill 转换工具 - 在不同 AI 编程助手之间无缝迁移你的技能配置

## 简介

SkillPorter 是一款图形化工具，帮助开发者在不同 AI 编程平台之间转换 Skill 配置文件。无论你使用 Claude Code、Cursor、Cline 还是其他 AI 助手，都可以轻松迁移你的自定义规则和指令。

## 支持平台

| 平台 | 格式 | 路径 |
|------|------|------|
| **Claude Code** | SKILL.md | ~/.claude/skills/ |
| **OpenAI Codex** | openai.yaml + AGENTS.md | ~/.codex/skills/ |
| **WorkBuddy** | SKILL.md | ~/.workbuddy/skills/ |
| **CodeBuddy** | SKILL.md | ~/.codebuddy/skills/ |
| **Cursor** | .cursorrules | 项目根目录 |
| **Cline** | .clinerules/*.md | 项目根目录 |
| **KiloCode** | .kilo/rules/*.md | 项目根目录 |
| **Kimi Code Agent** | SKILL.md | ~/.kimi/skills/ |
| **通义灵码 CLI** | SKILL.md | ~/.qwen/skills/ |
| **Hermes** | hermes.yaml | ~/.hermes/skills/ |

## 功能特性

- 🔄 **一键转换** - 选择源平台和目标平台，即可完成转换
- 👀 **实时预览** - 转换前可预览结果
- 📁 **批量支持** - 支持单文件或整个 Skill 目录
- 🎯 **智能识别** - 自动检测源文件格式
- 🛡️ **变量映射** - 自动转换不同平台的变量语法
- 📦 **一键导出** - 直接导出到目标平台目录

## 安装

### 环境要求

- Python 3.9+
- PyQt6

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/skillporter.git
cd skillporter

# 安装依赖
pip install PyQt6 pyyaml
```

## 使用方法

### 启动 GUI

```bash
python gui_launcher.py
```

### 转换流程

1. **选择源平台** - 从下拉菜单选择源 Skill 的平台
2. **选择目标平台** - 选择要转换到的平台
3. **选择文件/文件夹** - 浏览或拖拽 Skill 文件
4. **预览转换** - 点击「预览转换」查看结果
5. **导出** - 点击「导出到目标目录」保存

## 项目结构

```
skillporter/
├── core/                    # 核心模块
│   ├── schema.py           # 通用 Skill 数据结构 (USS)
│   ├── parser.py           # 解析器基类
│   └── renderer.py         # 渲染器基类
├── platforms/               # 平台实现
│   ├── claude/             # Claude Code
│   ├── codex/              # OpenAI Codex
│   ├── workbuddy/          # WorkBuddy
│   ├── codebuddy/          # CodeBuddy
│   ├── cursor/             # Cursor
│   ├── cline/              # Cline
│   ├── kilocode/           # KiloCode
│   ├── kimi/               # Kimi Code Agent
│   ├── qwen/               # 通义灵码 CLI
│   └── hermes/             # Hermes
├── gui/                     # 图形界面
├── config.py               # 配置管理
└── gui_launcher.py         # 启动入口
```

## 技术架构

- **Universal Skill Schema (USS)** - 跨平台通用数据结构
- **解析器注册表** - 自动检测并选择合适的解析器
- **渲染器注册表** - 根据目标平台选择渲染器
- **变量转换引擎** - 自动映射不同平台的变量语法

## 开发

### 添加新平台

1. 在 `core/schema.py` 的 `SkillPlatform` 枚举中添加新平台
2. 在 `platforms/` 下创建新目录，实现 `parser.py` 和 `renderer.py`
3. 更新 `gui/convert_panel.py` 的 `PLATFORMS` 字典

### 运行测试

```bash
python -m pytest tests/
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
