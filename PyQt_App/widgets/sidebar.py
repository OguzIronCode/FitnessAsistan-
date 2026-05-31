from pathlib import Path
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from theme import CARD, BORDER, PRIMARY, TEXT_DIM, TEXT_FAINT, BG_DEEP

_LOGO_PATH = str(Path(__file__).parent.parent.parent / "FitnessAsistani_Logo.png")

NAV_ITEMS = [
    (0, "Ana Sayfa",    "home"),
    (1, "Antrenman",    "workout"),
    (2, "Beslenme",     "nutrition"),
    (3, "AI Asistan",   "ai"),
    (4, "Analiz",       "analytics"),
    (5, "Ayarlar",      "settings"),
]


class SidebarWidget(QFrame):
    nav_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(230)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────────
        logo_frame = QFrame()
        logo_frame.setFixedHeight(64)
        logo_frame.setStyleSheet(f"border: none; border-bottom: 1px solid {BORDER}; background: transparent;")
        logo_lay = QHBoxLayout(logo_frame)
        logo_lay.setContentsMargins(16, 0, 16, 0)

        bolt = QLabel()
        bolt.setFixedSize(38, 38)
        bolt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _px = QPixmap(_LOGO_PATH)
        if not _px.isNull():
            bolt.setPixmap(_px.scaled(34, 34, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        else:
            bolt.setText("FA")
            bolt.setStyleSheet(f"background: rgba(255,107,107,0.12); color: {PRIMARY}; border-radius: 10px; font-size: 13px; font-weight: 700;")

        brand = QLabel("FitnessAsistanı")
        brand.setStyleSheet("font-size: 15px; font-weight: 600; letter-spacing: -0.5px;")
        logo_lay.addWidget(bolt)
        logo_lay.addSpacing(8)
        logo_lay.addWidget(brand)
        logo_lay.addStretch()
        root.addWidget(logo_frame)

        # ── Navigasyon ────────────────────────────────────────────────────
        root.addSpacing(8)
        self._btns: list[QPushButton] = []
        for idx, label, key in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(46)
            btn.clicked.connect(lambda checked, i=idx: self._on_nav(i))
            self._btns.append(btn)
            root.addWidget(btn)

        root.addStretch()

        # ── Alt: Yeni Antrenman + Çıkış ───────────────────────────────────
        bot_frame = QFrame()
        bot_frame.setStyleSheet(f"border: none; border-top: 1px solid {BORDER}; background: transparent;")
        bot_lay = QVBoxLayout(bot_frame)
        bot_lay.setContentsMargins(12, 10, 12, 12)
        bot_lay.setSpacing(4)

        new_workout_btn = QPushButton("Yeni Antrenman")
        new_workout_btn.setObjectName("primaryBtn")
        new_workout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_workout_btn.setMinimumHeight(40)
        new_workout_btn.clicked.connect(lambda: self._on_nav(1))
        bot_lay.addWidget(new_workout_btn)

        self.logout_btn = QPushButton("Çıkış Yap")
        self.logout_btn.setObjectName("navBtn")
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.setMinimumHeight(40)
        self.logout_btn.setStyleSheet(f"color: #f87171;")
        bot_lay.addWidget(self.logout_btn)

        root.addWidget(bot_frame)

        # Başlangıçta ilk sekme aktif
        self.set_active(0)

    def set_active(self, index: int):
        for i, btn in enumerate(self._btns):
            btn.setObjectName("navBtnActive" if i == index else "navBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _on_nav(self, index: int):
        self.set_active(index)
        self.nav_changed.emit(index)
