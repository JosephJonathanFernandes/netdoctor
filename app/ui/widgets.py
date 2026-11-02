"""Shared stat/result tile widgets for NetDoctor pages."""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget


class StatCard(QWidget):
    """A stat card: icon, title, big value, and subtitle."""

    def __init__(self, title: str, value: str = "n/a", subtitle: str = "", icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("stat_tile")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(14)

        self.icon_label = QLabel(icon or "📊")
        self.icon_label.setStyleSheet("font-size: 22px;")
        self.icon_label.setFixedSize(36, 36)

        info = QVBoxLayout()
        info.setSpacing(4)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("muted")
        self.title_label.setStyleSheet("font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;")
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 21px; font-weight: 800;")
        self.sub_label = QLabel(subtitle)
        self.sub_label.setObjectName("muted")
        self.sub_label.setStyleSheet("font-size: 11px;")
        info.addWidget(self.title_label)
        info.addWidget(self.value_label)
        info.addWidget(self.sub_label)

        layout.addWidget(self.icon_label)
        layout.addLayout(info)
        layout.addStretch()

    def set_value(self, value: str, subtitle: str | None = None) -> None:
        self.value_label.setText(value)
        if subtitle is not None:
            self.sub_label.setText(subtitle)


class MetricTile(QWidget):
    """A single result tile: title + value + status hint."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("stat_tile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("muted")
        self.title_label.setStyleSheet("font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;")
        self.value_label = QLabel("—")
        self.value_label.setStyleSheet("font-size: 20px; font-weight: 800;")
        self.hint_label = QLabel("pending")
        self.hint_label.setObjectName("muted")
        self.hint_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.hint_label)

    def set_value(self, value: str, hint: str = "") -> None:
        self.value_label.setText(value)
        if hint:
            self.hint_label.setText(hint)
