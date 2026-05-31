from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QCheckBox,
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from api import api

_LOGO_PATH = str(Path(__file__).parent.parent.parent / "FitnessAsistani_Logo.png")
from state import state
from theme import PRIMARY, TEXT_DIM, TEXT_FAINT, CARD, BORDER, BG_DEEP
from widgets.toast import Toast


class LoginPage(QWidget):
    login_success  = pyqtSignal()
    goto_register  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # Arka plan gradyanı
        self.setStyleSheet(f"""
            LoginPage {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a0d12, stop:0.5 #15151f, stop:1 #0f0f1e
                );
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Üst başlık çubuğu ─────────────────────────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(32, 24, 32, 16)

        logo_row = QHBoxLayout()
        bolt_lbl = QLabel()
        bolt_lbl.setFixedSize(36, 36)
        bolt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _px = QPixmap(_LOGO_PATH)
        if not _px.isNull():
            bolt_lbl.setPixmap(_px.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation))
        else:
            bolt_lbl.setText("FA")
            bolt_lbl.setStyleSheet(f"background: rgba(255,107,107,0.12); color: {PRIMARY}; border-radius: 10px; font-weight: 700;")
        brand_lbl = QLabel("FitnessAsistanı")
        brand_lbl.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        logo_row.addWidget(bolt_lbl)
        logo_row.addSpacing(8)
        logo_row.addWidget(brand_lbl)
        header.addLayout(logo_row)
        header.addStretch()

        reg_lbl = QLabel("Hesabın yok mu?")
        reg_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
        reg_btn = QPushButton("Kayıt ol →")
        reg_btn.setObjectName("ghostBtn")
        reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reg_btn.clicked.connect(self.goto_register)
        header.addWidget(reg_lbl)
        header.addSpacing(4)
        header.addWidget(reg_btn)
        root.addLayout(header)

        root.addStretch()

        # ── Kart merkezi ──────────────────────────────────────────────────
        center = QHBoxLayout()
        center.addStretch()

        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(420)
        card.setStyleSheet(f"""
            QFrame {{
                background: rgba(35,15,15,200);
                border: 1px solid rgba(255,107,107,0.22);
                border-radius: 22px;
            }}
            QLabel {{
                background: transparent;
                border: none;
                border-radius: 0;
            }}
            QCheckBox {{
                background: transparent;
                border: none;
            }}
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(36, 36, 36, 36)
        card_lay.setSpacing(12)

        # İkon
        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _px2 = QPixmap(_LOGO_PATH)
        if not _px2.isNull():
            icon_lbl.setPixmap(_px2.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation))
        else:
            icon_lbl.setText("FA")
            icon_lbl.setStyleSheet(f"""
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {PRIMARY}, stop:1 {CARD});
                color: white; border-radius: 32px; font-size: 20px; font-weight: 700; padding: 12px;
            """)
        icon_lbl.setFixedSize(64, 64)
        icon_row = QHBoxLayout()
        icon_row.addStretch()
        icon_row.addWidget(icon_lbl)
        icon_row.addStretch()
        card_lay.addLayout(icon_row)
        card_lay.addSpacing(4)

        title = QLabel("Hoş Geldiniz")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 600; letter-spacing: -0.5px; background: transparent;")
        card_lay.addWidget(title)

        sub = QLabel("Fitness yolculuğuna kaldığın yerden devam et")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
        card_lay.addWidget(sub)
        card_lay.addSpacing(8)

        # E-posta
        email_lbl = QLabel("E-POSTA")
        email_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        card_lay.addWidget(email_lbl)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@email.com")
        self.email_input.setMinimumHeight(48)
        card_lay.addWidget(self.email_input)

        # Şifre
        pw_lbl = QLabel("ŞİFRE")
        pw_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        card_lay.addWidget(pw_lbl)

        pw_row = QHBoxLayout()
        pw_row.setContentsMargins(0, 0, 0, 0)
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("••••••••")
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_input.setMinimumHeight(48)
        pw_row.addWidget(self.pw_input)
        self.eye_btn = QPushButton("Göster")
        self.eye_btn.setObjectName("iconBtn")
        self.eye_btn.setFixedSize(64, 48)
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_btn.clicked.connect(self._toggle_pw)
        pw_row.addWidget(self.eye_btn)
        card_lay.addLayout(pw_row)

        # Beni hatırla
        remember_cb = QCheckBox("Beni hatırla")
        remember_cb.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
        card_lay.addWidget(remember_cb)
        card_lay.addSpacing(4)

        # Giriş butonu
        self.login_btn = QPushButton("Giriş Yap  →")
        self.login_btn.setObjectName("primaryBtn")
        self.login_btn.setMinimumHeight(52)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._do_login)
        card_lay.addWidget(self.login_btn)

        # Enter ile giriş
        self.email_input.returnPressed.connect(self._do_login)
        self.pw_input.returnPressed.connect(self._do_login)

        center.addWidget(card)
        center.addStretch()
        root.addLayout(center)
        root.addStretch()

        # Toast bildirimi
        self.toast = Toast(self)

    def _toggle_pw(self):
        if self.pw_input.echoMode() == QLineEdit.EchoMode.Password:
            self.pw_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_btn.setText("Gizle")
        else:
            self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_btn.setText("Göster")

    def _do_login(self):
        email = self.email_input.text().strip()
        pw    = self.pw_input.text()
        if not email or not pw:
            self.toast.show_toast("E-posta ve şifre boş bırakılamaz.", "error")
            return

        self.login_btn.setText("Giriş yapılıyor...")
        self.login_btn.setEnabled(False)

        api.post("/auth/login", {"email": email, "password": pw},
                 callback=self._on_success, error_cb=self._on_error)

    def _on_success(self, data):
        if data:
            state.token   = data.get("access_token")
            state.user_id = data.get("user_id")
        self.login_btn.setText("Giriş Yap  →")
        self.login_btn.setEnabled(True)
        self.login_success.emit()

    def _on_error(self, msg: str):
        self.login_btn.setText("Giriş Yap  →")
        self.login_btn.setEnabled(True)
        self.toast.show_toast(msg, "error")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast.move((self.width() - self.toast.width()) // 2,
                        self.height() - self.toast.height() - 30)
