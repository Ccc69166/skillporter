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
