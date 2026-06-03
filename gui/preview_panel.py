"""
预览面板 - 双栏对比显示
========================

左边显示源文件内容，右边显示转换后的内容。
支持差异高亮和语法着色。
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLabel, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QSyntaxHighlighter

from .styles import COLORS, DIFF_ADDED_BG, DIFF_REMOVED_BG, DIFF_CHANGED_BG


class MarkdownHighlighter(QSyntaxHighlighter):
    """简单的 Markdown 语法高亮"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        # YAML frontmatter 分隔符
        separator_fmt = QTextCharFormat()
        separator_fmt.setForeground(QColor("#8E95A0"))
        self.rules.append((r'^---\s*$', separator_fmt))

        # YAML key
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#3B7DD8"))
        key_fmt.setFontWeight(QFont.Weight.Bold)
        self.rules.append((r'^[\w-]+:', key_fmt))

        # Markdown 标题
        heading_fmt = QTextCharFormat()
        heading_fmt.setForeground(QColor("#1A1D23"))
        heading_fmt.setFontWeight(QFont.Weight.Bold)
        self.rules.append((r'^#{1,6}\s+.+$', heading_fmt))

        # 变量 $VARIABLE
        var_fmt = QTextCharFormat()
        var_fmt.setForeground(QColor("#E65100"))
        var_fmt.setFontWeight(QFont.Weight.Bold)
        self.rules.append((r'\$[A-Z_]+', var_fmt))
        self.rules.append((r'\{\{[a-zA-Z_]+\}\}', var_fmt))

        # 工具名称
        tool_fmt = QTextCharFormat()
        tool_fmt.setForeground(QColor("#7B1FA2"))
        self.rules.append(
            (r'\b(Read|Write|Edit|Bash|Glob|Grep|AskUserQuestion|WebFetch|WebSearch|'
             r'read_file|write_file|edit_file|execute_shell|list_files|search_content|ask_user)\b',
             tool_fmt)
        )

        # 代码块
        code_fmt = QTextCharFormat()
        code_fmt.setForeground(QColor("#2E7D32"))
        code_fmt.setFontFamily("Cascadia Code")
        self.rules.append((r'`[^`]+`', code_fmt))

        # 列表项
        list_fmt = QTextCharFormat()
        list_fmt.setForeground(QColor("#5A6270"))
        self.rules.append((r'^\s*[-*]\s', list_fmt))

        # 注释
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#8E95A0"))
        comment_fmt.setFontItalic(True)
        self.rules.append((r'^#.*$', comment_fmt))

    def highlightBlock(self, text: str):
        import re
        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, fmt)


class PreviewPanel(QWidget):
    """
    双栏预览面板

    左边源文件，右边目标文件，中间分隔。
    """

    # 当源文件内容改变时发出信号
    content_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 分隔器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)

        # 左侧：源文件预览
        left_panel = self._create_panel("源文件", "source")
        self.source_text: QTextEdit = left_panel.findChild(QTextEdit, "source_text")

        # 右侧：目标文件预览
        right_panel = self._create_panel("转换结果", "target")
        self.target_text: QTextEdit = right_panel.findChild(QTextEdit, "target_text")

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([1, 1])  # 均分

        layout.addWidget(splitter)

        # 添加语法高亮
        self.source_highlighter = MarkdownHighlighter(self.source_text.document())
        self.target_highlighter = MarkdownHighlighter(self.target_text.document())

    def _create_panel(self, title: str, name: str) -> QWidget:
        """创建单侧面板"""
        panel = QFrame()
        panel.setProperty("card", True)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标题栏
        header = QFrame()
        header.setFixedHeight(36)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS["bg_secondary"]};
                border-bottom: 1px solid {COLORS["border_light"]};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)

        label = QLabel(title)
        label.setProperty("subheading", True)
        header_layout.addWidget(label)
        header_layout.addStretch()

        layout.addWidget(header)

        # 文本编辑区
        text_edit = QTextEdit()
        text_edit.setObjectName(f"{name}_text")
        text_edit.setProperty("preview", True)
        text_edit.setReadOnly(True)
        text_edit.setPlaceholderText("选择文件后显示内容...")
        text_edit.setFont(QFont("Cascadia Code", 11))

        layout.addWidget(text_edit)

        return panel

    def set_source_content(self, content: str):
        """设置源文件内容"""
        self.source_text.setPlainText(content)
        self.content_changed.emit(content)

    def set_target_content(self, content: str):
        """设置目标文件内容"""
        self.target_text.setPlainText(content)

    def set_target_error(self, error: str):
        """设置目标面板为错误状态"""
        self.target_text.setHtml(
            f'<div style="color: {COLORS["accent_error"]}; padding: 20px;">'
            f'<b>转换失败</b><br><br>{error}</div>'
        )

    def set_target_loading(self, message: str = "正在转换..."):
        """设置目标面板为加载状态"""
        self.target_text.setHtml(
            f'<div style="color: {COLORS["text_muted"]}; padding: 20px; text-align: center;">'
            f'<br><br>{message}</div>'
        )

    def clear(self):
        """清空所有内容"""
        self.source_text.clear()
        self.target_text.clear()

    def highlight_differences(self, source: str, target: str):
        """高亮显示差异（简单版本：按行对比）"""
        source_lines = source.splitlines()
        target_lines = target.splitlines()

        # 这里只是简单标记，不做复杂 diff
        # 主要用于给用户一个直观的感觉
        self.set_source_content(source)
        self.set_target_content(target)
