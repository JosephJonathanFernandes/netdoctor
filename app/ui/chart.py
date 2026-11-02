"""Matplotlib canvas widget for NetDoctor charts.

Theme-matched, transparent background charts sized to fit inside cards.
"""

from __future__ import annotations

from typing import Optional

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import pyplot as plt

from app.ui.theme import palette_dict


class MplCanvas(FigureCanvas):
    def __init__(self, width: float = 5, height: float = 2.6, dpi: int = 100, dark: bool = True):
        self._dark = dark
        self._colors = palette_dict(dark)

        plt.rcParams.update({
            "font.size": 8,
            "font.family": "sans-serif",
            "text.color": self._colors["text"],
            "axes.labelcolor": self._colors["text_muted"],
            "xtick.color": self._colors["text_muted"],
            "ytick.color": self._colors["text_muted"],
            "axes.edgecolor": self._colors["border"],
        })

        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.figure.patch.set_facecolor("none")
        self._axes = self.figure.add_subplot(111)
        self._axes.set_facecolor("none")
        self._apply_style()
        self._axes.set_xticks([])
        self._axes.set_yticks([])

        super().__init__(self.figure)
        self.setStyleSheet("background: transparent; border: none;")

    def clear(self) -> None:
        self._axes.clear()
        self._apply_style()
        self.figure.tight_layout()
        self.draw()

    def _apply_style(self) -> None:
        c = self._colors
        self._axes.grid(True, color=c["border"], linewidth=0.5, alpha=0.6)
        for spine in self._axes.spines.values():
            spine.set_color(c["border"])
        self._axes.tick_params(axis="x", colors=c["text_muted"])
        self._axes.tick_params(axis="y", colors=c["text_muted"])
        self._axes.set_xticks([])
        self._axes.set_yticks([])

    def plot_line(
        self,
        x,
        y,
        color=None,
        label: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        self.clear()
        c = self._colors
        line_color = color or c["accent"]
        self._axes.plot(x, y, color=line_color, linewidth=1.8, label=label)
        if xlabel:
            self._axes.set_xlabel(xlabel)
        if ylabel:
            self._axes.set_ylabel(ylabel)
        if title:
            self._axes.set_title(title, color=c["text"], fontsize=10, pad=8)
        if label:
            self._axes.legend(fontsize=7, frameon=False, loc="upper left")
        self._apply_style()
        self.figure.tight_layout()
        self.draw()

    def plot_empty(self, message: str = "No data available") -> None:
        self.clear()
        c = self._colors
        self._axes.text(
            0.5, 0.5, message,
            transform=self._axes.transAxes,
            ha="center", va="center",
            color=c["text_muted"],
            fontsize=9,
        )
        self.figure.tight_layout()
        self.draw()
