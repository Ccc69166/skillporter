"""
设置对话框 - API 配置
======================

配置 LLM API 密钥和提供商。
填了密钥就自动启用，不需要手动勾选。
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QPushButton, QFrame,
    QFormLayout, QCheckBox, QMessageBox, QGroupBox,
    QProgressDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QMovie

from .styles import COLORS
from ..config import get_config, save_config, SUPPORTED_MODELS, setup_llm


class LoadingDialog(QDialog):
    """轻量级加载弹窗，显示文字+转圈"""

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setModal(True)
        self.setFixedSize(220, 90)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 内容容器
        container = QLabel()
        container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(255, 255, 255, 240);
                border: 1px solid {COLORS["border"]};
                border-radius: 10px;
                padding: 16px 24px;
                font-size: 13px;
                color: {COLORS["text_secondary"]};
            }}
        """)
        container.setText(f"⟳  {message}")
        layout.addWidget(container)

        # 旋转动画定时器
        self._dots = 0
        self._label = container
        self._message = message
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(400)

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self._label.setText(f"⟳{'.' * self._dots}  {self._message}")


class SettingsDialog(QDialog):
    """API 设置对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API 配置")
        self.setMinimumWidth(420)
        self.setMinimumHeight(280)
        self.resize(460, 520)
        self._setup_ui()
        self._load_current_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 标题
        title = QLabel("API 配置")
        title.setProperty("heading", True)
        layout.addWidget(title)

        desc = QLabel("配置 LLM API 用于智能转换（可选）。填写密钥后自动启用。")
        desc.setProperty("subheading", True)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # === API 配置组 ===
        api_group = QGroupBox("LLM API 设置")
        api_layout = QFormLayout(api_group)
        api_layout.setSpacing(12)
        api_layout.setContentsMargins(16, 24, 16, 16)

        # 提供商选择
        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumHeight(36)
        for key, info in SUPPORTED_MODELS.items():
            self.provider_combo.addItem(info["name"], key)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        api_layout.addRow("提供商:", self.provider_combo)

        # 模型选择
        model_layout = QHBoxLayout()
        model_layout.setSpacing(8)

        # 下拉箭头 SVG 路径
        import os
        _assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        _arrow_svg = os.path.join(_assets, "arrow_down.svg").replace("\\", "/")

        self.model_combo = QComboBox()
        self.model_combo.setMinimumHeight(36)
        self.model_combo.setEditable(True)
        self.model_combo.setStyleSheet(f"""
            QComboBox {{
                border: 1.5px solid {COLORS["border"]};
                border-radius: 6px;
                padding: 6px 30px 6px 10px;
                background-color: {COLORS["bg_input"]};
                color: {COLORS["text_primary"]};
            }}
            QComboBox:focus {{
                border-color: {COLORS["border_focus"]};
            }}
            QComboBox::drop-down {{
                border: none;
                border-left: 1px solid {COLORS["border_light"]};
                width: 26px;
                subcontrol-origin: padding;
                subcontrol-position: center right;
            }}
            QComboBox::down-arrow {{
                image: url("{_arrow_svg}");
                width: 10px;
                height: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS["bg_primary"]};
                border: 1px solid {COLORS["border"]};
                selection-background-color: {COLORS["bg_selected"]};
                selection-color: {COLORS["text_primary"]};
                outline: none;
            }}
        """)
        model_layout.addWidget(self.model_combo, 1)

        refresh_models_btn = QPushButton("刷新")
        refresh_models_btn.setProperty("secondary", True)
        refresh_models_btn.setFixedHeight(36)
        refresh_models_btn.setMinimumWidth(70)
        refresh_models_btn.setToolTip("从API获取可用模型列表")
        refresh_models_btn.clicked.connect(self._refresh_models)
        model_layout.addWidget(refresh_models_btn)

        api_layout.addRow("模型:", model_layout)

        # API 密钥
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-xxx...（填写后自动启用）")
        self.api_key_input.setMinimumHeight(36)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("API 密钥:", self.api_key_input)

        # 显示密钥开关
        self.show_key_check = QCheckBox("显示密钥")
        self.show_key_check.stateChanged.connect(self._toggle_key_visibility)
        api_layout.addRow("", self.show_key_check)

        # 自定义 API 地址
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("留空使用默认地址")
        self.base_url_input.setMinimumHeight(36)
        api_layout.addRow("API 地址:", self.base_url_input)

        base_url_hint = QLabel("※ 如果地址失效，请前往官网查看最新 API 地址及文档")
        base_url_hint.setProperty("subheading", True)
        base_url_hint.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        api_layout.addRow("", base_url_hint)

        # 提示信息
        self.hint_label = QLabel("")
        self.hint_label.setProperty("subheading", True)
        self.hint_label.setWordWrap(True)
        api_layout.addRow("", self.hint_label)

        layout.addWidget(api_group)

        # === 费用说明 ===
        cost_frame = QFrame()
        cost_frame.setProperty("card", True)
        cost_layout = QVBoxLayout(cost_frame)
        cost_layout.setSpacing(4)

        cost_title = QLabel("费用说明")
        cost_title.setStyleSheet(f"font-weight: bold; color: {COLORS['text_primary']};")
        cost_layout.addWidget(cost_title)

        cost_text = QLabel(
            "• 每次转换约消耗 500~1500 tokens\n"
            "• DeepSeek deepseek-chat: 约 ¥0.001~0.003/次\n"
            "• 通义千问 qwen-turbo: 约 ¥0.002~0.005/次\n"
            "• 智谱 glm-4-flash: 约 ¥0.003~0.008/次\n"
            "• 仅在规则转换结果不满意时使用，成本极低"
        )
        cost_text.setProperty("subheading", True)
        cost_text.setWordWrap(True)
        cost_layout.addWidget(cost_text)

        layout.addWidget(cost_frame)

        # === 按钮 ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.setFixedHeight(38)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        test_btn = QPushButton("测试连接")
        test_btn.setProperty("secondary", True)
        test_btn.setFixedHeight(38)
        test_btn.clicked.connect(self._test_connection)
        btn_layout.addWidget(test_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedHeight(38)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _load_current_config(self):
        """加载当前配置"""
        config = get_config()

        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == config.llm.provider:
                self.provider_combo.setCurrentIndex(i)
                break

        self._on_provider_changed(self.provider_combo.currentIndex())
        if config.llm.model:
            index = self.model_combo.findText(config.llm.model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
            else:
                self.model_combo.setEditText(config.llm.model)

        if config.llm.api_key:
            self.api_key_input.setText(config.llm.api_key)

        if config.llm.base_url:
            self.base_url_input.setText(config.llm.base_url)

    def _on_provider_changed(self, index: int):
        """提供商改变时更新模型列表"""
        provider_key = self.provider_combo.currentData()
        if not provider_key:
            return

        provider_info = SUPPORTED_MODELS.get(provider_key, {})
        models = provider_info.get("models", [])
        default_model = provider_info.get("default_model", "")
        base_url = provider_info.get("base_url", "")

        self.model_combo.clear()
        self.model_combo.addItems(models)

        if default_model:
            index = self.model_combo.findText(default_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

        self.hint_label.setText(f"默认 API 地址: {base_url}")
        self.base_url_input.setPlaceholderText(f"留空使用 {base_url}")

    def _toggle_key_visibility(self):
        if self.show_key_check.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)

    def _refresh_models(self):
        """从API获取可用模型列表"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入 API 密钥")
            return

        provider = self.provider_combo.currentData()

        # Anthropic 不支持模型列表API
        if "anthropic" in provider:
            QMessageBox.information(self, "提示", "Anthropic 暂不支持自动获取模型列表，使用预设列表")
            return

        base_url = self.base_url_input.text().strip() or None
        provider_info = SUPPORTED_MODELS.get(provider, {})
        url_base = base_url or provider_info.get("base_url", "")

        # 显示加载弹窗
        loading = LoadingDialog("刷新模型列表中...", self)
        loading.show()

        try:
            import urllib.request
            import json
            from PyQt6.QtWidgets import QApplication

            url = f"{url_base}/models"
            headers = {"Authorization": f"Bearer {api_key}"}

            req = urllib.request.Request(url, headers=headers, method="GET")
            QApplication.processEvents()

            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            loading.close()

            if "data" in result:
                models = [m["id"] for m in result["data"]]
                models.sort()

                # 更新模型下拉框
                self.model_combo.blockSignals(True)
                self.model_combo.clear()
                self.model_combo.addItems(models)
                self.model_combo.blockSignals(False)

                # 优先选默认模型，否则选第一个
                default_model = provider_info.get("default_model", "")
                idx = self.model_combo.findText(default_model) if default_model else -1
                if idx >= 0:
                    self.model_combo.setCurrentIndex(idx)
                elif self.model_combo.count() > 0:
                    self.model_combo.setCurrentIndex(0)

                self.model_combo.setFocus()
                self.hint_label.setText(f"✓ 已获取 {len(models)} 个模型，请在列表中选取")
                self.hint_label.setStyleSheet(f"color: {COLORS['accent_success']};")
            else:
                self.hint_label.setText("✗ 响应格式异常，无法获取模型列表")
                self.hint_label.setStyleSheet(f"color: {COLORS['accent_error']};")

        except Exception as e:
            loading.close()
            self.hint_label.setText(f"✗ 获取失败: {str(e)[:60]}")
            self.hint_label.setStyleSheet(f"color: {COLORS['accent_error']};")

    def _test_connection(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "提示", "请先输入 API 密钥")
            return

        provider = self.provider_combo.currentData()
        model = self.model_combo.currentText()
        base_url = self.base_url_input.text().strip() or None

        # 显示加载弹窗
        loading = LoadingDialog("测试连接中...", self)
        loading.show()

        try:
            import urllib.request
            import json
            from PyQt6.QtWidgets import QApplication

            provider_info = SUPPORTED_MODELS.get(provider, {})
            url_base = base_url or provider_info.get("base_url", "")
            url = f"{url_base}/chat/completions"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            body = {
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 10,
            }

            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            QApplication.processEvents()

            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))

            loading.close()

            if "choices" in result:
                QMessageBox.information(self, "测试成功",
                    f"连接成功！\n\n"
                    f"提供商: {provider}\n"
                    f"模型: {model}\n"
                    f"API 地址: {url_base}")
            else:
                QMessageBox.warning(self, "测试失败", f"响应格式异常: {result}")

        except Exception as e:
            loading.close()
            QMessageBox.critical(self, "测试失败", f"连接失败:\n{str(e)}")

    def _save_settings(self):
        api_key = self.api_key_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "提示", "请输入 API 密钥")
            return

        provider = self.provider_combo.currentData()
        model = self.model_combo.currentText()
        base_url = self.base_url_input.text().strip() or None

        try:
            # 填了密钥就自动启用
            setup_llm(provider, api_key, model, base_url)

            QMessageBox.information(self, "保存成功", "设置已保存，API 智能转换已启用")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存设置失败:\n{str(e)}")
