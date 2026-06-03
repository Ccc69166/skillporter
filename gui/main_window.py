"""
SkillPorter 主窗口
===================

组装所有面板，处理业务逻辑。
"""

import re
import sys
import shutil
from pathlib import Path
from typing import Optional, Dict

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStatusBar, QMessageBox,
    QFileDialog, QApplication, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from .styles import COLORS, STYLESHEET
from .convert_panel import ConvertPanel, PLATFORMS
from .preview_panel import PreviewPanel
from .settings_dialog import SettingsDialog
from .api_converter import APIConverter

# 导入核心转换引擎
from ..core.parser import auto_parse, get_parser
from ..core.renderer import convert_skill, render_skill
from ..core.schema import SkillPlatform
from ..config import get_config


def _get_parser_for_platform(platform: str):
    """根据用户选择的平台获取 parser，而不是靠自动检测"""
    platform_map = {
        "claude": SkillPlatform.CLAUDE,
        "workbuddy": SkillPlatform.WORKBUDDY,
        "codex": SkillPlatform.CODEX,
    }
    target = platform_map.get(platform)
    if target:
        parser = get_parser(target)
        if parser:
            return parser
    # 兜底：用 auto_parse 的逻辑
    return None


def _sanitize_skill_id(skill_id: str) -> str:
    """清洗 skill ID，把中文和特殊字符替换为合法字符"""
    # 替换空格为连字符
    sanitized = skill_id.replace(" ", "-")
    # 只保留字母、数字、连字符、下划线
    sanitized = re.sub(r'[^a-zA-Z0-9_\-\u4e00-\u9fff]', '-', sanitized)
    # 去掉连续的连字符
    sanitized = re.sub(r'-+', '-', sanitized)
    # 去掉首尾连字符
    sanitized = sanitized.strip('-')
    # 如果清洗后为空，用默认值
    if not sanitized:
        sanitized = "converted-skill"
    return sanitized


class ConvertWorker(QThread):
    """后台转换线程"""

    finished = pyqtSignal(dict)   # 成功
    error = pyqtSignal(str)       # 失败

    def __init__(self, config: dict, mode: str = "rule"):
        super().__init__()
        self.config = config
        self.mode = mode

    def run(self):
        try:
            source_path = self.config["source_path"]
            source_platform = self.config["source_platform"]
            target_platform = self.config["target_platform"]

            result = {
                "source_platform": source_platform,
                "target_platform": target_platform,
                "source_path": source_path,
                "files": {},
                "method": "",
                "warnings": [],
                "skill_info": {},
            }

            # 用用户选的平台 parser，不用 auto_parse
            parser = _get_parser_for_platform(source_platform)
            path = Path(source_path)

            if parser:
                if path.is_dir():
                    skill = parser.parse_directory(path)
                else:
                    skill = parser.parse_file(path)
            else:
                # 兜底
                skill = auto_parse(source_path)

            # 清洗 ID
            if skill.id:
                skill.id = _sanitize_skill_id(skill.id)

            result["skill_info"] = {
                "id": skill.id,
                "name": skill.name,
                "description": skill.description[:100] if skill.description else "",
                "tools_count": len(skill.allowed_tools),
                "variables_count": len(skill.variables),
                "scripts_count": len(skill.scripts),
            }

            # 规则转换
            if self.mode in ("rule", "both"):
                target_enum = SkillPlatform(target_platform)
                files = convert_skill(skill, target_enum)
                result["files"] = files
                result["method"] = "规则转换"

                warnings = self._check_conversion_quality(skill, files, target_platform)
                result["warnings"] = warnings

                if self.mode == "rule" or not warnings:
                    self.finished.emit(result)
                    return

            # API 转换（兜底）
            if self.mode in ("api", "both"):
                api_converter = APIConverter()
                if not api_converter.is_available():
                    if self.mode == "api":
                        self.error.emit("API 未配置。请先在设置中配置 LLM API 密钥。")
                        return
                    self.finished.emit(result)
                    return

                source_files = self._read_source_files(source_path)
                main_content = source_files.get("SKILL.md", "") or source_files.get("AGENTS.md", "")
                if not main_content:
                    main_content = list(source_files.values())[0] if source_files else ""

                api_result = api_converter.convert(
                    source_content=main_content,
                    source_platform=source_platform,
                    target_platform=target_platform,
                    source_files=source_files,
                )

                if api_result.success:
                    api_files = self._parse_api_files(api_result.content, target_platform)
                    result["files"] = api_files
                    result["method"] = "API 智能转换"
                    result["api_info"] = {
                        "tokens": api_result.tokens_used,
                        "cost": api_result.cost_estimate,
                    }
                elif self.mode == "api":
                    self.error.emit(api_result.error)
                    return
                else:
                    result["warnings"].append(f"API 转换失败，使用规则转换结果: {api_result.error}")

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))

    def _check_conversion_quality(self, skill, files: dict, target_platform: str) -> list:
        warnings = []
        if target_platform == "codex":
            if "openai.yaml" not in files:
                warnings.append("缺少 openai.yaml 配置文件")
        else:
            if "SKILL.md" not in files:
                warnings.append("缺少 SKILL.md 文件")

        for file_content in files.values():
            if target_platform == "codex":
                remaining = re.findall(r'\$[A-Z_]+', file_content)
                if remaining:
                    warnings.append(f"存在未转换的变量: {', '.join(set(remaining))}")
                    break

        return warnings

    def _read_source_files(self, source_path: str) -> Dict[str, str]:
        files = {}
        p = Path(source_path)

        if p.is_file():
            files[p.name] = p.read_text(encoding="utf-8")
            return files

        for f in p.rglob("*"):
            if f.is_file() and f.suffix in (".md", ".yaml", ".yml", ".py", ".sh", ".txt", ".json"):
                rel = f.relative_to(p)
                try:
                    files[str(rel)] = f.read_text(encoding="utf-8")
                except:
                    pass

        return files

    def _parse_api_files(self, content: str, target_platform: str) -> Dict[str, str]:
        files = {}

        pattern = r'===FILE:(.+?)===\n(.*?)===END==='
        matches = re.findall(pattern, content, re.DOTALL)

        if matches:
            for file_path, file_content in matches:
                files[file_path.strip()] = file_content.strip()
        else:
            if target_platform == "codex":
                files["openai.yaml"] = content.strip()
            else:
                files["SKILL.md"] = content.strip()

        return files


class MainWindow(QMainWindow):
    """SkillPorter 主窗口"""

    def __init__(self):
        super().__init__()
        self._worker: Optional[ConvertWorker] = None
        self._last_result: Optional[dict] = None
        self._api_converter = APIConverter()
        self._setup_ui()
        self._update_api_status()

    def _setup_ui(self):
        self.setWindowTitle("SkillPorter - 跨平台 Skill 转换器")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 8)
        main_layout.setSpacing(12)

        # === 顶部标题 ===
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("SkillPorter")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {COLORS["accent"]};
        """)
        header_layout.addWidget(title)

        subtitle = QLabel("跨平台 Skill 转换器")
        subtitle.setProperty("subheading", True)
        subtitle.setStyleSheet("font-size: 14px; margin-left: 8px;")
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        version_label = QLabel("v2.0")
        version_label.setStyleSheet(f"""
            background-color: {COLORS["accent_light"]};
            color: {COLORS["accent"]};
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: bold;
        """)
        header_layout.addWidget(version_label)

        main_layout.addWidget(header)

        # === 主内容区 ===
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(4)

        self.convert_panel = ConvertPanel()
        self.convert_panel.setMinimumWidth(360)
        self.convert_panel.setMaximumWidth(480)

        # 连接信号
        self.convert_panel.preview_requested.connect(self._on_preview)
        self.convert_panel.convert_requested.connect(self._on_convert)
        self.convert_panel.deploy_requested.connect(self._on_deploy)
        self.convert_panel.settings_requested.connect(self._open_settings)
        self.convert_panel.source_selected.connect(self._on_source_selected)

        content_splitter.addWidget(self.convert_panel)

        self.preview_panel = PreviewPanel()
        content_splitter.addWidget(self.preview_panel)

        content_splitter.setSizes([380, 820])

        main_layout.addWidget(content_splitter, 1)

        # === 状态栏 ===
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def _update_api_status(self):
        status = self._api_converter.get_status()
        self.convert_panel.set_api_status(
            status["available"],
            status.get("provider", ""),
            status.get("model", "")
        )

    def _open_settings(self):
        dialog = SettingsDialog(self)
        # 弹出时顶部贴屏幕上方
        QTimer.singleShot(0, lambda: dialog.move(dialog.x(), 0))
        dialog.exec()
        self._update_api_status()

    def _on_source_selected(self, path: str):
        """源文件选择后，自动加载预览"""
        source_content = self._read_preview_content(path)
        if source_content:
            self.preview_panel.set_source_content(source_content)
            self.status_bar.showMessage(f"已加载源文件: {path}")

    def _on_preview(self, config: dict):
        if not config.get("source_path"):
            QMessageBox.warning(self, "提示", "请先选择 Skill 文件或文件夹")
            return

        self.convert_panel.set_converting(True)
        self.status_bar.showMessage("正在预览转换...")

        # 确定模式
        mode = "rule"
        if config.get("use_api") and not config.get("use_rule"):
            mode = "api"

        self._worker = ConvertWorker(config, mode)
        self._worker.finished.connect(self._on_convert_finished)
        self._worker.error.connect(self._on_convert_error)
        self._worker.start()

    def _on_convert(self, config: dict):
        self._on_preview(config)

    def _on_deploy(self, config: dict):
        if not config.get("source_path"):
            QMessageBox.warning(self, "提示", "请先选择 Skill 文件或文件夹")
            return

        if not self._last_result:
            QMessageBox.information(self, "提示", "请先点击「预览转换」查看结果")
            return

        target_platform = config["target_platform"]
        platform_info = PLATFORMS.get(target_platform, {})
        default_dir = str(Path(platform_info.get("path", "~/.workbuddy/skills/")).expanduser())

        output_dir = QFileDialog.getExistingDirectory(
            self, "选择导出目录", default_dir,
            QFileDialog.Option.ShowDirsOnly
        )

        if not output_dir:
            return

        try:
            out_path = Path(output_dir)
            skill_info = self._last_result.get("skill_info", {})
            skill_id = skill_info.get("id", "converted-skill")
            skill_dir = out_path / skill_id

            if skill_dir.exists():
                reply = QMessageBox.question(
                    self, "确认覆盖",
                    f"目录已存在: {skill_dir}\n是否覆盖？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            skill_dir.mkdir(parents=True, exist_ok=True)

            files = self._last_result.get("files", {})
            for file_path, content in files.items():
                full_path = skill_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")

            QMessageBox.information(
                self, "导出成功",
                f"✓ 已导出 {len(files)} 个文件到:\n{skill_dir}"
            )
            self.status_bar.showMessage(f"导出成功: {skill_dir}")

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出失败:\n{str(e)}")

    def _on_convert_finished(self, result: dict):
        self._last_result = result
        self.convert_panel.set_converting(False)

        method = result.get("method", "")
        warnings = result.get("warnings", [])
        skill_info = result.get("skill_info", {})
        files = result.get("files", {})

        # 目标内容
        target_content = ""
        for path, content in files.items():
            target_content += f"{'='*40}\n📄 {path}\n{'='*40}\n{content}\n\n"

        self.preview_panel.set_target_content(target_content)

        status_parts = [
            f"✓ {method}",
            f"Skill: {skill_info.get('name', 'unknown')}",
            f"生成 {len(files)} 个文件",
        ]

        api_info = result.get("api_info", {})
        if api_info:
            status_parts.append(f"消耗 {api_info.get('tokens', 0)} tokens ({api_info.get('cost', '')})")

        if warnings:
            status_parts.append(f"⚠ {len(warnings)} 个警告")

        self.status_bar.showMessage("  |  ".join(status_parts))

        if warnings:
            warning_text = "\n".join(f"• {w}" for w in warnings)
            QMessageBox.warning(self, "转换警告", f"转换完成，但有以下警告:\n\n{warning_text}")

    def _on_convert_error(self, error: str):
        self.convert_panel.set_converting(False)
        self.preview_panel.set_target_error(error)
        self.status_bar.showMessage(f"✗ 转换失败: {error}")

    def _read_preview_content(self, source_path: str) -> str:
        p = Path(source_path)
        if not p.exists():
            return ""

        if p.is_file():
            try:
                return p.read_text(encoding="utf-8")
            except:
                return "(无法读取文件)"

        # 目录：列出所有文本文件内容
        content = ""
        text_suffixes = {".md", ".yaml", ".yml", ".py", ".sh", ".txt", ".json"}
        for f in sorted(p.rglob("*")):
            if f.is_file() and f.suffix in text_suffixes:
                rel = f.relative_to(p)
                content += f"{'='*40}\n📄 {rel}\n{'='*40}\n"
                try:
                    content += f.read_text(encoding="utf-8")
                except:
                    content += "(无法读取)"
                content += "\n\n"

        return content


def run_gui():
    """启动 GUI"""
    app = QApplication(sys.argv)
    app.setApplicationName("SkillPorter")
    app.setApplicationVersion("2.0")

    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
