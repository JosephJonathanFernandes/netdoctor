"""Modern glassmorphism theme and widget helpers for NetDoctor.

A polished, dark-by-default desktop aesthetic with subtle borders, rounded cards,
drop shadows, and theme-aware matplotlib charts.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QFrame, QGraphicsDropShadowEffect

# ---------------------------------------------------------------------- #
# Palette
# ---------------------------------------------------------------------- #
DARK = {
    "window": "#0f0f17",      # near-black background
    "surface": "#1a1a2e",     # card surface
    "surface_alt": "#23233a", # slightly lighter surface
    "border": "#33334a",      # subtle borders
    "border_focus": "#89b4fa",# focus/accent border
    "text": "#e4e4e7",        # primary text
    "text_muted": "#94a3b8",  # secondary text
    "accent": "#89b4fa",      # blue accent
    "accent_hover": "#7ec8f5",
    "accent_glow": "rgba(137, 180, 250, 0.35)",
    "success": "#34d399",
    "success_bg": "rgba(52, 211, 153, 0.15)",
    "warning": "#fbbf24",
    "warning_bg": "rgba(251, 191, 36, 0.15)",
    "error": "#f87171",
    "error_bg": "rgba(248, 113, 113, 0.15)",
    "ink": "#0f0f17",         # text on accent
}

LIGHT = {
    "window": "#f8fafc",
    "surface": "#ffffff",
    "surface_alt": "#f1f5f9",
    "border": "#cbd5e1",
    "border_focus": "#3b82f6",
    "text": "#0f172a",
    "text_muted": "#64748b",
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "accent_glow": "rgba(59, 130, 246, 0.25)",
    "success": "#10b981",
    "success_bg": "rgba(16, 185, 129, 0.15)",
    "warning": "#f59e0b",
    "warning_bg": "rgba(245, 158, 11, 0.15)",
    "error": "#ef4444",
    "error_bg": "rgba(239, 68, 68, 0.15)",
    "ink": "#ffffff",
}


def palette_dict(dark: bool = True) -> dict:
    return DARK if dark else LIGHT


# ---------------------------------------------------------------------- #
# Stylesheets
# ---------------------------------------------------------------------- #


def _qss(colors: dict) -> str:
    c = colors
    return f"""
    QMainWindow {{
        background-color: {c['window']};
    }}
    QWidget {{
        background-color: transparent;
        color: {c['text']};
        font-size: 13px;
        font-family: 'Segoe UI', 'Inter', sans-serif;
    }}
    QLabel {{
        color: {c['text']};
        background-color: transparent;
    }}
    QLabel#muted {{
        color: {c['text_muted']};
    }}
    QLabel#h1 {{
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: {c['text']};
    }}
    QLabel#h2 {{
        font-size: 15px;
        font-weight: 600;
        color: {c['text']};
    }}
    QLabel#caption {{
        font-size: 11px;
        color: {c['text_muted']};
    }}
    QPushButton {{
        background-color: {c['surface_alt']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 10px 16px;
        min-height: 38px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        border-color: {c['border_focus']};
        background-color: {c['surface']};
    }}
    QPushButton:pressed {{
        background-color: {c['surface_alt']};
    }}
    QPushButton#primary {{
        background-color: {c['accent']};
        color: {c['ink']};
        border: none;
        font-weight: 700;
    }}
    QPushButton#primary:hover {{
        background-color: {c['accent_hover']};
    }}
    QPushButton#primary:pressed {{
        background-color: {c['accent_hover']};
    }}
    QPushButton#danger {{
        background-color: {c['error']};
        color: {c['ink']};
        border: none;
        font-weight: 700;
    }}
    QPushButton#danger:hover {{
        background-color: #dc2626;
    }}
    QPushButton#ghost {{
        background-color: transparent;
        border: 1px solid {c['border']};
        color: {c['text']};
    }}
    QPushButton#ghost:hover {{
        background-color: {c['surface_alt']};
        border-color: {c['border_focus']};
    }}
    QPushButton#sidebar {{
        background-color: transparent;
        border: none;
        border-radius: 10px;
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton#sidebar:checked {{
        background-color: {c['surface_alt']};
        border-left: 4px solid {c['accent']};
        color: {c['accent']};
    }}
    QPushButton#sidebar:hover:!checked {{
        background-color: rgba(255,255,255,0.03);
    }}
    QFrame#card {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 14px;
    }}
    QFrame#card:hover {{
        border-color: {c['border_focus']};
    }}
    QFrame#card_flat {{
        background-color: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 10px;
    }}
    QFrame#card_flat:hover {{
        background-color: {c['surface']};
        border-color: {c['border_focus']};
    }}
    QFrame#stat_tile {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
    }}
    QFrame#stat_tile:hover {{
        border-color: {c['border_focus']};
    }}
    QListWidget {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        outline: none;
        padding: 6px;
    }}
    QListWidget::item {{
        border: none;
        border-radius: 8px;
        padding: 10px 12px;
        background-color: transparent;
    }}
    QListWidget::item:selected {{
        background-color: {c['accent']};
        color: {c['ink']};
    }}
    QListWidget::item:hover {{
        background-color: rgba(255,255,255,0.04);
    }}
    QHeaderView::section {{
        background-color: {c['surface_alt']};
        color: {c['text_muted']};
        border: none;
        border-bottom: 1px solid {c['border']};
        padding: 8px 10px;
        font-weight: 700;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    QTableView {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        gridline-color: {c['border']};
        selection-background-color: {c['accent']};
        selection-color: {c['ink']};
    }}
    QTableView::item {{
        border: none;
        padding: 8px 10px;
    }}
    QScrollBar:vertical {{
        background: {c['window']};
        width: 10px;
        border-radius: 5px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 5px;
        min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c['text_muted']};
    }}
    QComboBox, QSpinBox, QDoubleSpinBox {{
        background-color: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 6px 10px;
        color: {c['text']};
        min-height: 32px;
    }}
    QComboBox:hover, QSpinBox:hover {{
        border-color: {c['border_focus']};
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
        border: 1px solid {c['border']};
        border-radius: 6px;
        background-color: {c['surface_alt']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c['accent']};
        border-color: {c['accent']};
    }}
    QGroupBox {{
        border: 1px solid {c['border']};
        border-radius: 12px;
        margin-top: 18px;
        padding-top: 14px;
        color: {c['text']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        padding: 0 8px;
        color: {c['text_muted']};
        font-size: 12px;
        font-weight: 700;
    }}
    QStatusBar {{
        background-color: {c['surface_alt']};
        color: {c['text_muted']};
        border-top: 1px solid {c['border']};
    }}
    QProgressBar {{
        background-color: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        text-align: center;
        color: {c['text']};
        min-height: 8px;
    }}
    QProgressBar::chunk {{
        background-color: {c['accent']};
        border-radius: 6px;
    }}
    QToolTip {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 6px;
        font-size: 11px;
    }}
    """


def dark_stylesheet() -> str:
    return _qss(DARK)


def light_stylesheet() -> str:
    return _qss(LIGHT)


def apply_theme(app: QApplication, dark: bool = True) -> None:
    app.setStyleSheet(dark_stylesheet() if dark else light_stylesheet())
    palette = QPalette()
    base = QColor("#0f0f17" if dark else "#f8fafc")
    text = QColor("#e4e4e7" if dark else "#0f172a")
    palette.setColor(QPalette.Window, base)
    palette.setColor(QPalette.WindowText, text)
    app.setPalette(palette)


# ---------------------------------------------------------------------- #
# Widget helpers
# ---------------------------------------------------------------------- #


def make_card(parent=None) -> QFrame:
    card = QFrame(parent)
    card.setObjectName("card")
    card.setFrameShape(QFrame.NoFrame)
    return card


def make_flat_card(parent=None) -> QFrame:
    card = QFrame(parent)
    card.setObjectName("card_flat")
    card.setFrameShape(QFrame.NoFrame)
    return card


def add_shadow(widget, blur: float = 24, offset_y: float = 6, color_alpha: int = 80) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(0)
    effect.setYOffset(offset_y)
    effect.setColor(QColor(0, 0, 0, color_alpha))
    widget.setGraphicsEffect(effect)


def status_badge_color(status: str, colors: dict) -> str:
    return {
        "pass": colors["success"],
        "warn": colors["warning"],
        "fail": colors["error"],
        "completed": colors["success"],
        "failed": colors["error"],
        "cancelled": colors["text_muted"],
        "running": colors["accent"],
        "pending": colors["text_muted"],
    }.get(status, colors["text_muted"])
