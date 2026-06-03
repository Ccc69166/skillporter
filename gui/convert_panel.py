"""
转换面板 - 平台选择和转换控制
==============================

源平台 → 目标平台的选择，文件选择，转换按钮。
"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QFileDialog, QLineEdit,
    QFrame, QProgressBar, QRadioButton, QButtonGroup,
    QListWidget, QListWidgetItem, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon

from .styles import COLORS


# 平台信息
PLATFORMS = {
    "claude": {
        "name": "Claude Code",
        "color": "#D97706",
        "icon": "🟠",
        "path": "~/.claude/skills/",
    },
    "workbuddy": {
        "name": "WorkBuddy",
        "color": "#3B7DD8",
        "icon": "🔵",
        "path": "~/.workbuddy/skills/",
    },
    "codex": {
        "name": "OpenAI Codex",
        "color": "#10A37F",
        "icon": "🟢",
        "path": "~/.codex/skills/",
    },
}


class PlatformSelector(QFrame):
    """平台选择器组件"""

    platform_changed = pyqtSignal(str)

    def __init__(self, label: str, default: str = "claude", parent=None):
        super().__init__(parent)
        self.label_text = label
        self._setup_ui(default)

    def _setup_ui(self, default: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(self.label_text)
        label.setProperty("subheading", True)
        layout.addWidget(label)

        self.combo = QComboBox()
        self.combo.setMinimumHeight(38)
        self.combo.setStyleSheet(f"""
            QComboBox {{
                border: 1.5px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 8px 12px;
                background-color: {COLORS["bg_input"]};
                color: {COLORS["text_primary"]};
            }}
            QComboBox:focus {{
                border-color: {COLORS["border_focus"]};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border"]};
                selection-background-color: {COLORS["bg_selected"]};
                selection-color: {COLORS["text_primary"]};
                outline: none;
            }}
        """)
        for key, info in PLATFORMS.items():
            self.combo.addItem(f"{info['icon']}  {info['name']}", key)
        self.combo.setCurrentText(f"{PLATFORMS[default]['icon']}  {PLATFORMS[default]['name']}")
        self.combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(self.combo, 1)

    def _on_changed(self, index: int):
        platform_key = self.combo.currentData()
        self.platform_changed.emit(platform_key)

    def get_platform(self) -> str:
        return self.combo.currentData()

    def set_platform(self, platform: str):
        for i in range(self.combo.count()):
            if self.combo.itemData(i) == platform:
                self.combo.setCurrentIndex(i)
                break


class ConvertPanel(QWidget):
    """
    转换控制面板

    包含：源/目标平台选择、文件选择、转换模式、操作按钮。
    """

    # 信号
    convert_requested = pyqtSignal(dict)
    preview_requested = pyqtSignal(dict)
    deploy_requested = pyqtSignal(dict)
    settings_requested = pyqtSignal()
    source_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_path = None
        self._setup_ui()
        self.setAcceptDrops(True)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # === 平台选择区（QGridLayout：标签在 row 0，combo+按钮在 row 1）===
        platform_frame = QFrame()
        platform_frame.setProperty("card", True)
        platform_grid = QGridLayout(platform_frame)
        platform_grid.setContentsMargins(12, 12, 12, 12)
        platform_grid.setHorizontalSpacing(8)
        platform_grid.setVerticalSpacing(6)

        # Row 0: 标签
        from_label = QLabel("从")
        from_label.setProperty("subheading", True)
        platform_grid.addWidget(from_label, 0, 0)

        to_label = QLabel("转换为")
        to_label.setProperty("subheading", True)
        platform_grid.addWidget(to_label, 0, 2)

        # Row 1: combo + swap 按钮
        combo_style = f"""
            QComboBox {{
                border: 1.5px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 6px 4px;
                background-color: {COLORS["bg_input"]};
                color: {COLORS["text_primary"]};
            }}
            QComboBox:focus {{
                border-color: {COLORS["border_focus"]};
            }}
            QComboBox::drop-down {{
                width: 0px;
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border"]};
                selection-background-color: {COLORS["bg_selected"]};
                selection-color: {COLORS["text_primary"]};
                outline: none;
            }}
        """

        # 源平台 combo
        self.source_combo = QComboBox()
        self.source_combo.setMinimumHeight(38)
        self.source_combo.setStyleSheet(combo_style)
        for key, info in PLATFORMS.items():
            self.source_combo.addItem(f"{info['icon']}  {info['name']}", key)
        self.source_combo.setCurrentIndex(0)
        self.source_combo.currentIndexChanged.connect(
            lambda: self.source_selected.emit(self.source_combo.currentData() or "")
        )
        platform_grid.addWidget(self.source_combo, 1, 0)

        # 转换箭头按钮（与 combo 同行）
        swap_btn = QPushButton("⇄")
        swap_btn.setFixedSize(38, 38)
        swap_btn.setToolTip("交换源和目标平台")
        swap_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        swap_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS["bg_primary"]};
                color: {COLORS["accent"]};
                border: 1.5px solid {COLORS["accent"]};
                border-radius: 4px;
                font-size: 16px;
                font-weight: bold;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: {COLORS["accent_light"]};
            }}
        """)
        swap_btn.clicked.connect(self._swap_platforms)
        platform_grid.addWidget(swap_btn, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        # 目标平台 combo
        self.target_combo = QComboBox()
        self.target_combo.setMinimumHeight(38)
        self.target_combo.setStyleSheet(combo_style)
        for key, info in PLATFORMS.items():
            self.target_combo.addItem(f"{info['icon']}  {info['name']}", key)
        self.target_combo.setCurrentIndex(1)  # 默认 WorkBuddy
        platform_grid.addWidget(self.target_combo, 1, 2)

        # 列拉伸：combo 拉伸，按钮不拉伸
        platform_grid.setColumnStretch(0, 1)
        platform_grid.setColumnStretch(1, 0)
        platform_grid.setColumnStretch(2, 1)

        main_layout.addWidget(platform_frame)

        # === 文件选择区 ===
        file_frame = QFrame()
        file_frame.setProperty("card", True)
        file_layout = QVBoxLayout(file_frame)
        file_layout.setContentsMargins(16, 16, 16, 16)
        file_layout.setSpacing(8)

        file_label = QLabel("Skill 文件/文件夹")
        file_label.setProperty("subheading", True)
        file_layout.addWidget(file_label)

        file_input_layout = QHBoxLayout()
        file_input_layout.setSpacing(8)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("拖拽文件夹到此处，或点击浏览...")
        self.path_input.setMinimumHeight(38)
        self.path_input.setReadOnly(True)
        file_input_layout.addWidget(self.path_input)

        browse_btn = QPushButton("浏览")
        browse_btn.setProperty("secondary", True)
        browse_btn.setFixedHeight(38)
        browse_btn.clicked.connect(self._browse_files)
        file_input_layout.addWidget(browse_btn)

        file_layout.addLayout(file_input_layout)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(120)
        self.file_list.setVisible(False)
        file_layout.addWidget(self.file_list)

        main_layout.addWidget(file_frame)

        # === 转换模式（单选） ===
        mode_frame = QFrame()
        mode_frame.setProperty("card", True)
        mode_layout = QVBoxLayout(mode_frame)
        mode_layout.setContentsMargins(16, 16, 16, 16)
        mode_layout.setSpacing(8)

        mode_label = QLabel("转换模式")
        mode_label.setProperty("subheading", True)
        mode_layout.addWidget(mode_label)

        # 用 QRadioButton 实现互斥选择
        self.mode_group = QButtonGroup(self)

        self.rule_radio = QRadioButton("规则转换（快速，离线，免费）")
        self.rule_radio.setChecked(True)
        self.mode_group.addButton(self.rule_radio, 0)
        mode_layout.addWidget(self.rule_radio)

        self.api_radio = QRadioButton("API 智能转换（兜底，需联网，极低成本）")
        self.api_radio.setChecked(False)
        self.mode_group.addButton(self.api_radio, 1)
        mode_layout.addWidget(self.api_radio)

        # API 配置行
        api_config_layout = QHBoxLayout()
        api_config_layout.setSpacing(8)
        api_config_layout.addSpacing(24)  # 缩进

        self.settings_btn = QPushButton("配置 API")
        self.settings_btn.setProperty("secondary", True)
        self.settings_btn.setFixedHeight(28)
        self.settings_btn.clicked.connect(self.settings_requested.emit)
        api_config_layout.addWidget(self.settings_btn)

        api_config_layout.addStretch()

        # API 状态提示
        self.api_status_label = QLabel("")
        self.api_status_label.setProperty("subheading", True)
        api_config_layout.addWidget(self.api_status_label)

        mode_layout.addLayout(api_config_layout)

        main_layout.addWidget(mode_frame)

        # === 操作按钮 ===
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.setSpacing(12)

        btn_layout.addStretch()

        self.preview_btn = QPushButton("预览转换")
        self.preview_btn.setProperty("secondary", True)
        self.preview_btn.setFixedHeight(42)
        self.preview_btn.setMinimumWidth(120)
        self.preview_btn.clicked.connect(self._on_preview)
        btn_layout.addWidget(self.preview_btn)

        self.convert_btn = QPushButton("一键转换")
        self.convert_btn.setProperty("success", True)
        self.convert_btn.setFixedHeight(42)
        self.convert_btn.setMinimumWidth(120)
        self.convert_btn.clicked.connect(self._on_convert)
        btn_layout.addWidget(self.convert_btn)

        self.deploy_btn = QPushButton("导出到目标目录")
        self.deploy_btn.setFixedHeight(42)
        self.deploy_btn.setMinimumWidth(140)
        self.deploy_btn.clicked.connect(self._on_deploy)
        btn_layout.addWidget(self.deploy_btn)

        main_layout.addWidget(btn_frame)

        # === 进度条 ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        main_layout.addWidget(self.progress_bar)

        main_layout.addStretch()

    def _swap_platforms(self):
        """交换源和目标平台"""
        src_idx = self.source_combo.currentIndex()
        tgt_idx = self.target_combo.currentIndex()
        self.source_combo.setCurrentIndex(tgt_idx)
        self.target_combo.setCurrentIndex(src_idx)

    def _browse_files(self):
        """浏览选择文件/文件夹（只弹一个对话框）"""
        # 根据源平台自动定位到对应目录
        source_platform = self.source_combo.currentData()
        platform_info = PLATFORMS.get(source_platform, {})
        default_dir = str(Path(platform_info.get("path", "~/.workbuddy/skills/")).expanduser())

        dir_path = QFileDialog.getExistingDirectory(
            self, "选择 Skill 文件夹", default_dir,
            QFileDialog.Option.ShowDirsOnly
        )

        if dir_path:
            self._set_path(dir_path)

    def _set_path(self, path: str):
        """设置选中的路径"""
        self._selected_path = path
        self.path_input.setText(path)

        p = Path(path)
        self.file_list.clear()
        if p.is_dir():
            self.file_list.setVisible(True)
            # 只列出一层，不递归（避免刷屏）
            for f in sorted(p.iterdir()):
                if f.is_file() and f.suffix in (".md", ".yaml", ".yml"):
                    item = QListWidgetItem(f.name)
                    self.file_list.addItem(item)
                elif f.is_dir() and not f.name.startswith("."):
                    item = QListWidgetItem(f"📁 {f.name}/")
                    self.file_list.addItem(item)
        else:
            self.file_list.setVisible(False)

        self.source_selected.emit(path)

    def get_config(self) -> dict:
        """获取当前转换配置"""
        return {
            "source_platform": self.source_combo.currentData(),
            "target_platform": self.target_combo.currentData(),
            "source_path": self._selected_path,
            "use_rule": self.rule_radio.isChecked(),
            "use_api": self.api_radio.isChecked(),
        }

    def set_api_status(self, available: bool, provider: str = "", model: str = ""):
        """更新 API 状态显示"""
        if available:
            self.api_status_label.setText(f"✓ {provider} / {model}")
            self.api_status_label.setStyleSheet(f"color: {COLORS['accent_success']};")
        else:
            self.api_status_label.setText("✗ 未配置")
            self.api_status_label.setStyleSheet(f"color: {COLORS['text_muted']};")

    def set_converting(self, converting: bool):
        """设置转换中状态"""
        self.convert_btn.setEnabled(not converting)
        self.preview_btn.setEnabled(not converting)
        self.deploy_btn.setEnabled(not converting)
        self.progress_bar.setVisible(converting)
        if converting:
            self.progress_bar.setRange(0, 0)

    def _on_preview(self):
        if not self._selected_path:
            return
        self.preview_requested.emit(self.get_config())

    def _on_convert(self):
        if not self._selected_path:
            return
        self.convert_requested.emit(self.get_config())

    def _on_deploy(self):
        if not self._selected_path:
            return
        self.deploy_requested.emit(self.get_config())

    # === 拖拽支持 ===

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self._set_path(path)
