# ── Renk Paleti ──────────────────────────────────────────────────────────────
BG       = "#1e1e2e"
BG_DEEP  = "#15151f"
CARD     = "#2b2b3b"
CARD2    = "#3b3b4f"
BORDER   = "#333344"
PRIMARY  = "#ff6b6b"
PRIM_DRK = "#c4304a"
AI_CLR   = "#7c3aed"
TEXT     = "#f1f5f9"
TEXT_DIM = "#94a3b8"
TEXT_FAINT = "#64748b"
SUCCESS  = "#4ade80"
ERROR    = "#f87171"
WARN     = "#fb923c"

STYLESHEET = f"""
/* ── Temel ─────────────────────────────────────────────────────────────── */
* {{
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}}
QWidget {{
    background-color: {BG};
    color: {TEXT};
}}
QMainWindow {{
    background-color: {BG_DEEP};
}}
QDialog {{
    background-color: {CARD};
}}

/* ── Scroll ─────────────────────────────────────────────────────────────── */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_FAINT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{ height: 0; }}

/* ── Giriş Alanları ─────────────────────────────────────────────────────── */
QLineEdit {{
    background-color: rgba(15, 15, 25, 200);
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    color: {TEXT};
    font-size: 13px;
}}
QLineEdit:focus {{
    border: 1px solid {PRIMARY};
}}
QLineEdit:disabled {{
    color: {TEXT_FAINT};
}}

/* ── Butonlar ───────────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 13px;
}}
QPushButton:hover  {{ background-color: {CARD2}; }}
QPushButton:pressed {{ background-color: {CARD}; }}
QPushButton:disabled {{ color: {TEXT_FAINT}; background-color: {CARD}; }}

QPushButton#primaryBtn {{
    background-color: {PRIMARY};
    color: white;
    border: none;
    font-weight: 600;
    padding: 12px 20px;
    border-radius: 10px;
}}
QPushButton#primaryBtn:hover  {{ background-color: #ff8585; }}
QPushButton#primaryBtn:pressed {{ background-color: {PRIM_DRK}; }}
QPushButton#primaryBtn:disabled {{ background-color: #7a3535; color: #aaa; }}

QPushButton#ghostBtn {{
    background-color: transparent;
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QPushButton#ghostBtn:hover {{ background-color: {CARD}; }}

QPushButton#iconBtn {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 6px;
    color: {TEXT_DIM};
    font-size: 18px;
}}
QPushButton#iconBtn:hover {{
    background-color: {CARD};
    color: {TEXT};
}}

QPushButton#navBtn {{
    background-color: transparent;
    color: {TEXT_DIM};
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    text-align: left;
    padding: 13px 18px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#navBtn:hover {{
    background-color: rgba(59,59,79,0.5);
    color: {TEXT};
}}
QPushButton#navBtnActive {{
    background-color: {CARD2};
    color: white;
    border: none;
    border-left: 3px solid {PRIMARY};
    border-radius: 0;
    text-align: left;
    padding: 13px 18px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#dangerBtn {{
    background-color: rgba(248,113,113,0.1);
    color: {ERROR};
    border: 1px solid rgba(248,113,113,0.3);
    border-radius: 8px;
    padding: 8px 14px;
}}
QPushButton#dangerBtn:hover {{ background-color: rgba(248,113,113,0.2); }}

/* ── Seçim Kutuları ─────────────────────────────────────────────────────── */
QComboBox {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT};
    min-height: 38px;
}}
QComboBox:focus {{ border: 1px solid {PRIMARY}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_DIM};
    margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD2};
    border: 1px solid {BORDER};
    selection-background-color: rgba(255,107,107,0.2);
    selection-color: {TEXT};
    color: {TEXT};
    outline: none;
    padding: 4px;
}}

/* ── Spin Box ───────────────────────────────────────────────────────────── */
QSpinBox, QDoubleSpinBox {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    color: {TEXT};
    min-height: 38px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {PRIMARY}; }}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background-color: {CARD2};
    border: none;
    width: 24px;
    border-radius: 4px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: rgba(255,107,107,0.2);
}}

/* ── Etiket / Frame ─────────────────────────────────────────────────────── */
QLabel {{ background: transparent; color: {TEXT}; border: none; border-radius: 0; }}

QFrame#card {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QFrame#cardAI {{
    background-color: rgba(124,58,237,0.08);
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 12px;
}}
QFrame#cardPrimary {{
    background-color: rgba(255,107,107,0.06);
    border: 1px solid rgba(255,107,107,0.25);
    border-radius: 12px;
}}
QFrame#sidebar {{
    background-color: {CARD};
    border-right: 1px solid {BORDER};
}}
QFrame#header {{
    background-color: rgba(30,30,46,180);
    border-bottom: 1px solid {BORDER};
}}
QFrame#divider {{
    background-color: {BORDER};
    max-height: 1px;
    min-height: 1px;
}}

/* ── İlerleme Çubuğu ────────────────────────────────────────────────────── */
QProgressBar {{
    background-color: rgba(255,255,255,0.06);
    border: none;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {PRIMARY};
    border-radius: 3px;
}}
QProgressBar#proteinBar::chunk {{ background-color: #a78bfa; }}
QProgressBar#carbBar::chunk    {{ background-color: #60a5fa; }}
QProgressBar#fatBar::chunk     {{ background-color: {WARN}; }}

/* ── Slider ─────────────────────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: rgba(255,255,255,0.08);
    height: 6px;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {PRIMARY};
    width: 20px;
    height: 20px;
    border-radius: 10px;
    margin-top: -7px;
    margin-bottom: -7px;
}}
QSlider::sub-page:horizontal {{
    background: {PRIMARY};
    border-radius: 3px;
}}

/* ── Metin ──────────────────────────────────────────────────────────────── */
QTextEdit {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    color: {TEXT};
    padding: 10px;
    font-size: 13px;
}}
QTextEdit:focus {{ border: 1px solid {PRIMARY}; }}

/* ── Tablo ──────────────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    color: {TEXT};
}}
QTableWidget::item {{ padding: 8px; }}
QTableWidget::item:selected {{
    background-color: rgba(255,107,107,0.15);
    color: {TEXT};
}}
QHeaderView::section {{
    background-color: {BG_DEEP};
    color: {TEXT_FAINT};
    border: none;
    border-right: 1px solid {BORDER};
    padding: 10px 12px;
    font-size: 11px;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 1px;
}}

/* ── Liste ──────────────────────────────────────────────────────────────── */
QListWidget {{
    background: transparent;
    border: none;
}}
QListWidget::item {{
    border-radius: 8px;
    padding: 10px 12px;
    margin: 2px 0;
    border: 1px solid transparent;
}}
QListWidget::item:hover {{ background-color: rgba(255,255,255,0.03); }}
QListWidget::item:selected {{
    background-color: rgba(255,107,107,0.1);
    border: 1px solid rgba(255,107,107,0.3);
    color: {TEXT};
}}
"""
