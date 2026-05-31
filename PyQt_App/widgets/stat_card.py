from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from theme import CARD, BORDER, PRIMARY, TEXT_DIM, TEXT_FAINT


class StatCard(QFrame):
    """Üst kısımdaki ikon+başlık, büyük sayı değeri ve ilerleme çubuğu olan kart."""

    def __init__(self, title: str, icon: str, color: str = PRIMARY, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(200)
        self.setMinimumHeight(130)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(8)

        # ── Başlık satırı ──────────────────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        top_row.addWidget(title_lbl)
        top_row.addStretch()

        icon_frame = QFrame()
        icon_frame.setFixedSize(36, 36)
        icon_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,107,107,0.12);
                border-radius: 10px;
            }}
        """)
        _icon_lay = QVBoxLayout(icon_frame)
        _icon_lay.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"color: {color}; font-size: 18px; background: transparent;")
        _icon_lay.addWidget(icon_lbl)
        top_row.addWidget(icon_frame)
        root.addLayout(top_row)

        # ── Değer + hedef ──────────────────────────────────────────────────
        val_row = QHBoxLayout()
        val_row.setContentsMargins(0, 0, 0, 0)
        val_row.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self._val_lbl = QLabel("0")
        self._val_lbl.setStyleSheet(f"color: white; font-size: 32px; font-weight: 600; letter-spacing: -1px; background: transparent;")
        val_row.addWidget(self._val_lbl)

        self._unit_lbl = QLabel("")
        self._unit_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 13px; background: transparent;")
        self._unit_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)
        val_row.addWidget(self._unit_lbl)
        val_row.addStretch()
        root.addLayout(val_row)

        # ── Alt bilgi ──────────────────────────────────────────────────────
        self._info_lbl = QLabel("Veri yok")
        self._info_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 11px; background: transparent;")
        root.addWidget(self._info_lbl)

        # ── İlerleme çubuğu ───────────────────────────────────────────────
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)
        root.addWidget(self._bar)

    def update(self, value, unit: str = "", info: str = "", pct: float = 0):
        self._val_lbl.setText(str(value))
        self._unit_lbl.setText(f" {unit}" if unit else "")
        self._info_lbl.setText(info)
        self._bar.setValue(int(min(100, max(0, pct))))
