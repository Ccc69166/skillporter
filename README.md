# SkillPorter

**[English](#english)** | **中文**

---

<a id="chinese"></a>

# SkillPorter - 跨平台 Skill 转换工具

在不同 AI 编程助手之间无缝迁移你的技能配置。支持 Claude Code、Cursor、Cline、Kimi Code Agent 等 10+ 平台。

## 功能特性

- 🔄 **一键转换** - 选择源平台和目标平台，即可完成 Skill 配置转换
- 👀 **实时预览** - 转换前可预览结果，确认无误后再导出
- 📁 **批量支持** - 支持单文件或整个 Skill 目录转换
- 🎯 **智能识别** - 自动检测源文件格式，无需手动指定
- 🛡️ **变量映射** - 自动转换不同平台的变量语法（如 `$ARGUMENTS` ↔ `{{args}}`）
- 📦 **一键导出** - 直接导出到目标平台目录

## 支持平台

| 平台 | 格式 | 路径 |
|------|------|------|
| Claude Code | SKILL.md | ~/.claude/skills/ |
| OpenAI Codex | openai.yaml + AGENTS.md | ~/.codex/skills/ |
| WorkBuddy | SKILL.md | ~/.workbuddy/skills/ |
| CodeBuddy | SKILL.md | ~/.codebuddy/skills/ |
| Cursor | .cursorrules | 项目根目录 |
| Cline | .clinerules/*.md | 项目根目录 |
| KiloCode | .kilo/rules/*.md | 项目根目录 |
| Kimi Code Agent | SKILL.md | ~/.kimi/skills/ |
| 通义灵码 CLI | SKILL.md | ~/.qwen/skills/ |
| Hermes | hermes.yaml | ~/.hermes/skills/ |

## 快速开始

### 环境要求

- Python 3.9+
- PyQt6

### 安装

```bash
# 克隆仓库
git clone https://github.com/YOUR_USERNAME/skillporter.git
cd skillporter

# 安装依赖
pip install PyQt6 pyyaml
```

### 启动

```bash
python gui_launcher.py
```

## 使用说明

### 转换流程

1. **选择源平台** - 从下拉菜单选择源 Skill 的平台
2. **选择目标平台** - 选择要转换到的平台
3. **选择文件/文件夹** - 浏览或拖拽 Skill 文件到窗口
4. **预览转换** - 点击「预览转换」查看结果
5. **导出** - 点击「导出到目标目录」保存

### 转换模式

| 模式 | 说明 |
|------|------|
| 规则转换 | 快速、离线、免费，基于预设规则转换 |
| API 智能转换 | 需联网，使用 LLM API 兜底处理复杂转换 |

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
│   ├── main_window.py      # 主窗口
│   ├── convert_panel.py    # 转换面板
│   ├── preview_panel.py    # 预览面板
│   └── settings_dialog.py  # 设置对话框
├── config.py               # 配置管理
└── gui_launcher.py         # 启动入口
```

## 技术架构

- **Universal Skill Schema (USS)** - 跨平台通用数据结构，所有平台的 Skill 都会先转换为 USS 格式
- **解析器注册表** - 自动检测文件格式并选择合适的解析器
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

## 版本历史

| 版本 | 说明 |
|------|------|
| 1.0 | 初始版本，支持 10 个平台转换 |

## 许可证

MIT License

---

<a id="english"></a>

# SkillPorter - Cross-Platform Skill Conversion Tool

Seamlessly migrate your skill configurations between different AI programming assistants. Supports 10+ platforms including Claude Code, Cursor, Cline, and Kimi Code Agent.

## Features

- 🔄 **One-Click Conversion** - Select source and target platforms, then convert instantly
- 👀 **Real-time Preview** - Preview results before exporting
- 📁 **Batch Support** - Convert single files or entire Skill directories
- 🎯 **Smart Detection** - Auto-detect source file format
- 🛡️ **Variable Mapping** - Auto-convert variable syntax across platforms (e.g., `$ARGUMENTS` ↔ `{{args}}`)
- 📦 **Quick Export** - Export directly to target platform directory

## Supported Platforms

| Platform | Format | Path |
|----------|--------|------|
| Claude Code | SKILL.md | ~/.claude/skills/ |
| OpenAI Codex | openai.yaml + AGENTS.md | ~/.codex/skills/ |
| WorkBuddy | SKILL.md | ~/.workbuddy/skills/ |
| CodeBuddy | SKILL.md | ~/.codebuddy/skills/ |
| Cursor | .cursorrules | Project root |
| Cline | .clinerules/*.md | Project root |
| KiloCode | .kilo/rules/*.md | Project root |
| Kimi Code Agent | SKILL.md | ~/.kimi/skills/ |
| Tongyi Lingma CLI | SKILL.md | ~/.qwen/skills/ |
| Hermes | hermes.yaml | ~/.hermes/skills/ |

## Quick Start

### Requirements

- Python 3.9+
- PyQt6

### Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/skillporter.git
cd skillporter

# Install dependencies
pip install PyQt6 pyyaml
```

### Launch

```bash
python gui_launcher.py
```

## Usage

### Conversion Workflow

1. **Select Source Platform** - Choose the source Skill's platform from dropdown
2. **Select Target Platform** - Choose the platform to convert to
3. **Select File/Folder** - Browse or drag-and-drop Skill files
4. **Preview Conversion** - Click "Preview Conversion" to see results
5. **Export** - Click "Export to Target Directory" to save

### Conversion Modes

| Mode | Description |
|------|-------------|
| Rule-based | Fast, offline, free conversion based on preset rules |
| API Smart | Online, uses LLM API as fallback for complex conversions |

## Project Structure

```
skillporter/
├── core/                    # Core modules
│   ├── schema.py           # Universal Skill Schema (USS)
│   ├── parser.py           # Parser base class
│   └── renderer.py         # Renderer base class
├── platforms/               # Platform implementations
│   ├── claude/             # Claude Code
│   ├── codex/              # OpenAI Codex
│   ├── workbuddy/          # WorkBuddy
│   ├── codebuddy/          # CodeBuddy
│   ├── cursor/             # Cursor
│   ├── cline/              # Cline
│   ├── kilocode/           # KiloCode
│   ├── kimi/               # Kimi Code Agent
│   ├── qwen/               # Tongyi Lingma CLI
│   └── hermes/             # Hermes
├── gui/                     # Graphical interface
│   ├── main_window.py      # Main window
│   ├── convert_panel.py    # Conversion panel
│   ├── preview_panel.py    # Preview panel
│   └── settings_dialog.py  # Settings dialog
├── config.py               # Configuration management
└── gui_launcher.py         # Entry point
```

## Architecture

- **Universal Skill Schema (USS)** - Cross-platform universal data structure; all Skills are first converted to USS format
- **Parser Registry** - Auto-detect file format and select appropriate parser
- **Renderer Registry** - Select renderer based on target platform
- **Variable Conversion Engine** - Auto-map variable syntax across platforms

## Development

### Adding a New Platform

1. Add new platform to `SkillPlatform` enum in `core/schema.py`
2. Create new directory under `platforms/` with `parser.py` and `renderer.py`
3. Update `PLATFORMS` dictionary in `gui/convert_panel.py`

### Running Tests

```bash
python -m pytest tests/
```

## Changelog

| Version | Description |
|---------|-------------|
| 1.0 | Initial release, supports 10 platforms |

## License

MIT License
