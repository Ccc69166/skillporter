"""
SkillPorter GUI 样式定义
========================

专业配色方案，干净利落。
"""

# 主色调：深蓝灰 + 白底 + 蓝色强调
COLORS = {
    # 背景
    "bg_primary": "#FFFFFF",
    "bg_secondary": "#F5F7FA",
    "bg_card": "#FFFFFF",
    "bg_hover": "#EBF0F7",
    "bg_selected": "#D6E4F5",
    "bg_input": "#FFFFFF",

    # 文字
    "text_primary": "#1A1D23",
    "text_secondary": "#5A6270",
    "text_muted": "#8E95A0",
    "text_on_accent": "#FFFFFF",

    # 强调色
    "accent": "#3B7DD8",
    "accent_hover": "#2D6BC4",
    "accent_light": "#E8F0FB",
    "accent_success": "#34A853",
    "accent_warning": "#F5A623",
    "accent_error": "#E74C3C",

    # 边框
    "border": "#DDE1E8",
    "border_focus": "#3B7DD8",
    "border_light": "#ECEDF0",

    # 阴影
    "shadow": "rgba(0, 0, 0, 0.06)",
}

# 全局样式表
STYLESHEET = f"""
/* ===== 全局 ===== */
QWidget {{
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
    color: {COLORS["text_primary"]};
    background-color: {COLORS["bg_primary"]};
}}

/* ===== 主窗口 ===== */
QMainWindow {{
    background-color: {COLORS["bg_secondary"]};
}}

/* ===== 按钮 ===== */
QPushButton {{
    background-color: {COLORS["accent"]};
    color: {COLORS["text_on_accent"]};
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: bold;
    min-height: 18px;
}}
QPushButton:hover {{
    background-color: {COLORS["accent_hover"]};
}}
QPushButton:pressed {{
    background-color: {COLORS["accent_hover"]};
}}
QPushButton:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_muted"]};
}}

/* 次要按钮 */
QPushButton[secondary="true"] {{
    background-color: transparent;
    color: {COLORS["accent"]};
    border: 1.5px solid {COLORS["accent"]};
}}
QPushButton[secondary="true"]:hover {{
    background-color: {COLORS["accent_light"]};
}}

/* 成功按钮 */
QPushButton[success="true"] {{
    background-color: {COLORS["accent_success"]};
}}
QPushButton[success="true"]:hover {{
    background-color: #2D9648;
}}

/* ===== 标签 ===== */
QLabel {{
    background: transparent;
    border: none;
}}
QLabel[heading="true"] {{
    font-size: 18px;
    font-weight: bold;
    color: {COLORS["text_primary"]};
}}
QLabel[subheading="true"] {{
    font-size: 13px;
    color: {COLORS["text_secondary"]};
}}

/* ===== 输入框 ===== */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS["bg_input"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS["text_primary"]};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS["border_focus"]};
}}

/* ===== 复选框 ===== */
QCheckBox {{
    spacing: 8px;
    color: {COLORS["text_primary"]};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS["border"]};
    border-radius: 4px;
    background-color: {COLORS["bg_input"]};
}}
QCheckBox::indicator:hover {{
    border-color: {COLORS["accent"]};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
    image: none;
}}
QCheckBox::indicator:disabled {{
    background-color: {COLORS["bg_secondary"]};
    border-color: {COLORS["border"]};
}}

/* ===== 下拉框 ===== */
QComboBox {{
    background-color: {COLORS["bg_input"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 120px;
}}
QComboBox:focus {{
    border-color: {COLORS["border_focus"]};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_primary"]};
    border: 1px solid {COLORS["border"]};
    selection-background-color: {COLORS["bg_selected"]};
    selection-color: {COLORS["text_primary"]};
    outline: none;
}}

/* ===== 分组框 ===== */
QGroupBox {{
    font-weight: bold;
    border: 1.5px solid {COLORS["border"]};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    background-color: {COLORS["bg_card"]};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {COLORS["text_secondary"]};
}}

/* ===== 卡片 ===== */
QFrame[card="true"] {{
    background-color: {COLORS["bg_card"]};
    border: 1px solid {COLORS["border_light"]};
    border-radius: 8px;
    padding: 16px;
}}

/* ===== 列表 ===== */
QListWidget {{
    background-color: {COLORS["bg_input"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 6px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS["border_light"]};
}}
QListWidget::item:selected {{
    background-color: {COLORS["bg_selected"]};
    color: {COLORS["text_primary"]};
}}
QListWidget::item:hover {{
    background-color: {COLORS["bg_hover"]};
}}

/* ===== 文本预览 ===== */
QTextEdit[preview="true"] {{
    background-color: {COLORS["bg_secondary"]};
    border: 1.5px solid {COLORS["border"]};
    border-radius: 6px;
    font-family: "Cascadia Code", "Consolas", "Source Code Pro", monospace;
    font-size: 12px;
    line-height: 1.5;
    padding: 12px;
}}

/* ===== 进度条 ===== */
QProgressBar {{
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    text-align: center;
    background-color: {COLORS["bg_secondary"]};
    height: 8px;
}}
QProgressBar::chunk {{
    background-color: {COLORS["accent"]};
    border-radius: 3px;
}}

/* ===== 状态栏 ===== */
QStatusBar {{
    background-color: {COLORS["bg_card"]};
    border-top: 1px solid {COLORS["border_light"]};
    color: {COLORS["text_secondary"]};
    padding: 4px 12px;
}}

/* ===== 工具提示 ===== */
QToolTip {{
    background-color: {COLORS["text_primary"]};
    color: {COLORS["bg_primary"]};
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ===== ScrollBar ===== */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS["text_muted"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS["border"]};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS["text_muted"]};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""

# 高亮差异的 HTML 颜色
DIFF_ADDED_BG = "#E6F4EA"      # 新增：浅绿背景
DIFF_REMOVED_BG = "#FDECEA"    # 删除：浅红背景
DIFF_CHANGED_BG = "#FFF8E1"    # 修改：浅黄背景
DIFF_ADDED_TEXT = "#1E7E34"    # 新增文字
DIFF_REMOVED_TEXT = "#C62828"  # 删除文字
DIFF_CHANGED_TEXT = "#E65100"  # 修改文字
