from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QScrollArea,
                             QComboBox, QSpinBox, QDoubleSpinBox, QSlider,
                             QSizePolicy, QButtonGroup, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from api import api
from state import state
from theme import PRIMARY, TEXT_DIM, TEXT_FAINT, CARD, BORDER, BG_DEEP
from widgets.toast import Toast


class _GoalCard(QPushButton):
    def __init__(self, icon, title, desc, value, parent=None):
        super().__init__(parent)
        self.value = value
        self.setCheckable(True)
        self.setFixedHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)

        ic = QLabel(icon)
        ic.setStyleSheet(f"font-size: 24px; background: transparent;")
        ic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(ic)

        t = QLabel(title)
        t.setStyleSheet(f"font-weight: 600; font-size: 14px; background: transparent;")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(t)

        d = QLabel(desc)
        d.setStyleSheet(f"font-size: 11px; color: {TEXT_DIM}; background: transparent;")
        d.setWordWrap(True)
        d.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(d)

        self._refresh()
        self.toggled.connect(lambda _: self._refresh())

    def _refresh(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,107,107,0.1);
                    border: 2px solid {PRIMARY};
                    border-radius: 14px;
                    color: white;
                    text-align: left;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {CARD};
                    border: 1px solid {BORDER};
                    border-radius: 14px;
                    color: white;
                    text-align: left;
                }}
                QPushButton:hover {{
                    border-color: rgba(255,255,255,0.2);
                }}
            """)


class _GenderBtn(QPushButton):
    def __init__(self, icon, label, value, parent=None):
        super().__init__(parent)
        self.value = value
        self.setCheckable(True)
        self.setMinimumHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ic = QLabel(icon)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("font-size: 20px; background: transparent;")
        ic.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(ic)

        t = QLabel(label)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size: 12px; font-weight: 500; background: transparent;")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lay.addWidget(t)

        self._refresh()
        self.toggled.connect(lambda _: self._refresh())

    def _refresh(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,107,107,0.12);
                    border: 2px solid {PRIMARY};
                    border-radius: 12px;
                    color: {PRIMARY};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {CARD};
                    border: 1px solid {BORDER};
                    border-radius: 12px;
                    color: white;
                }}
                QPushButton:hover {{ border-color: rgba(255,255,255,0.2); }}
            """)


class ProfilePage(QWidget):
    register_success = pyqtSignal()
    goto_login       = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._complete_mode = False
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Başlık çubuğu ─────────────────────────────────────────────────
        hdr = QFrame()
        hdr.setFixedHeight(60)
        hdr.setObjectName("header")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(28, 0, 28, 0)

        bolt_lbl = QLabel("FitnessAsistanı")
        bolt_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {PRIMARY}; background: transparent;")
        hdr_lay.addWidget(bolt_lbl)
        hdr_lay.addStretch()

        back_btn = QPushButton("← Girişe Dön")
        back_btn.setObjectName("ghostBtn")
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.goto_login)
        hdr_lay.addWidget(back_btn)
        outer.addWidget(hdr)

        # ── Kaydırılabilir form ────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(32, 28, 32, 40)
        lay.setSpacing(28)

        title_lbl = QLabel("Profilini Oluştur")
        title_lbl.setStyleSheet("font-size: 26px; font-weight: 600; letter-spacing: -0.5px; background: transparent;")
        lay.addWidget(title_lbl)

        # ── BÖLÜM 1: Kimlik ───────────────────────────────────────────────
        lay.addWidget(self._section("1", "Kimlik Bilgileri",
                                    "Sana özel içerikler üretmek için temel bilgiler."))
        s1 = QFrame(); s1.setObjectName("card"); s1_lay = QVBoxLayout(s1)
        s1_lay.setContentsMargins(20, 18, 20, 18); s1_lay.setSpacing(14)

        s1_lay.addWidget(self._lbl("AD SOYAD"))
        self.name_inp = QLineEdit(); self.name_inp.setPlaceholderText("Ad Soyad"); self.name_inp.setMinimumHeight(44)
        s1_lay.addWidget(self.name_inp)

        self.cred_widget = QWidget()
        cred_row = QHBoxLayout(self.cred_widget)
        cred_row.setContentsMargins(0, 0, 0, 0)
        email_col = QVBoxLayout()
        email_col.addWidget(self._lbl("E-POSTA"))
        self.email_inp = QLineEdit(); self.email_inp.setPlaceholderText("ornek@email.com"); self.email_inp.setMinimumHeight(44)
        email_col.addWidget(self.email_inp)
        pw_col = QVBoxLayout()
        pw_col.addWidget(self._lbl("ŞİFRE"))
        self.pw_inp = QLineEdit(); self.pw_inp.setPlaceholderText("••••••••")
        self.pw_inp.setEchoMode(QLineEdit.EchoMode.Password); self.pw_inp.setMinimumHeight(44)
        pw_col.addWidget(self.pw_inp)
        cred_row.addLayout(email_col); cred_row.addLayout(pw_col)
        s1_lay.addWidget(self.cred_widget)

        s1_lay.addWidget(self._lbl("CİNSİYET"))
        gender_row = QHBoxLayout()
        self._gender_grp = QButtonGroup(self); self._gender_grp.setExclusive(True)
        self.gender_m  = _GenderBtn("", "Erkek",  "male")
        self.gender_f  = _GenderBtn("", "Kadın",  "female")
        self.gender_o  = _GenderBtn("", "Diğer",  "other")
        for b in (self.gender_m, self.gender_f, self.gender_o):
            self._gender_grp.addButton(b); gender_row.addWidget(b)
        self.gender_m.setChecked(True)
        s1_lay.addLayout(gender_row)

        nums_row = QHBoxLayout(); nums_row.setSpacing(12)
        for attr, lbl, mn, mx in [("age_spin","Yaş",10,100),
                                   ("height_spin","Boy (cm)",100,250),
                                   ("weight_spin","Kilo (kg)",30,250)]:
            col = QVBoxLayout()
            col.addWidget(self._lbl(lbl.upper()))
            sp = QSpinBox() if attr != "weight_spin" else QDoubleSpinBox()
            sp.setRange(mn, mx); sp.setValue(25 if attr=="age_spin" else (175 if attr=="height_spin" else 75))
            sp.setMinimumHeight(44)
            setattr(self, attr, sp); col.addWidget(sp); nums_row.addLayout(col)
        s1_lay.addLayout(nums_row)
        lay.addWidget(s1)

        # ── BÖLÜM 2: Hedef ────────────────────────────────────────────────
        lay.addWidget(self._section("2", "Hedefini Seç",
                                    "Sistem programlarını bu hedefe göre planlayacak."))
        goal_row = QHBoxLayout(); goal_row.setSpacing(12)
        self._goal_grp = QButtonGroup(self); self._goal_grp.setExclusive(True)
        self.goal_cut      = _GoalCard("", "Yağ Yak",      "Kalori açığı odaklı.", "cut")
        self.goal_bulk     = _GoalCard("", "Kas Yap",       "Protein yoğun beslenme.", "bulk")
        self.goal_maintain = _GoalCard("", "Formunu Koru", "Dengeli ve sağlıklı.", "maintain")
        for b in (self.goal_cut, self.goal_bulk, self.goal_maintain):
            self._goal_grp.addButton(b); goal_row.addWidget(b)
        self.goal_maintain.setChecked(True)
        lay.addLayout(goal_row)

        # ── BÖLÜM 3: Tercihler ────────────────────────────────────────────
        lay.addWidget(self._section("3", "Tercihler", "Antrenman ve beslenme alışkanlıkların."))
        s3 = QFrame(); s3.setObjectName("card"); s3_lay = QVBoxLayout(s3)
        s3_lay.setContentsMargins(20, 18, 20, 18); s3_lay.setSpacing(14)

        freq_row = QHBoxLayout()
        freq_row.addWidget(self._lbl("HAFTALIK ANTRENMAN"))
        freq_row.addStretch()
        self.freq_lbl = QLabel("4 gün / hafta")
        self.freq_lbl.setStyleSheet(f"""
            background: rgba(255,107,107,0.12); color: {PRIMARY};
            border-radius: 10px; padding: 4px 10px; font-size: 12px; font-weight: 600;
        """)
        freq_row.addWidget(self.freq_lbl)
        s3_lay.addLayout(freq_row)

        self.freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.freq_slider.setRange(1, 7); self.freq_slider.setValue(4)
        self.freq_slider.valueChanged.connect(
            lambda v: self.freq_lbl.setText(f"{v} gün / hafta"))
        s3_lay.addWidget(self.freq_slider)

        s3_lay.addWidget(self._lbl("BESLENME TERCİHİ"))
        self.diet_combo = QComboBox()
        self.diet_combo.addItems(["Dengeli (Karma)", "Yüksek Protein",
                                   "Düşük Karbonhidrat", "Vejetaryen", "Vegan"])
        self.diet_combo.setMinimumHeight(44)
        s3_lay.addWidget(self.diet_combo)
        lay.addWidget(s3)

        # ── Kaydet butonu ─────────────────────────────────────────────────
        self.save_btn = QPushButton("Profilimi Kaydet ve Devam Et")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setMinimumHeight(54)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._do_register)
        lay.addWidget(self.save_btn)

        self.toast = Toast(self)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        return l

    def _section(self, num, title, sub):
        row = QWidget()
        lay = QHBoxLayout(row); lay.setContentsMargins(0, 0, 0, 0)
        num_lbl = QLabel(num)
        num_lbl.setFixedSize(28, 28)
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_lbl.setStyleSheet(f"""
            background: {PRIMARY}; color: white;
            border-radius: 14px; font-weight: 600; font-size: 12px;
        """)
        col = QVBoxLayout()
        t = QLabel(title); t.setStyleSheet("font-size: 20px; font-weight: 600; background: transparent;")
        s = QLabel(sub); s.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
        col.addWidget(t); col.addWidget(s)
        lay.addWidget(num_lbl); lay.addSpacing(10); lay.addLayout(col); lay.addStretch()
        return row

    def _get_goal(self):
        for b in self._goal_grp.buttons():
            if b.isChecked(): return b.value
        return "maintain"

    def _get_gender(self):
        for b in self._gender_grp.buttons():
            if b.isChecked(): return b.value
        return "male"

    def _get_diet(self):
        mapping = {"Dengeli (Karma)": "balanced", "Yüksek Protein": "high_protein",
                   "Düşük Karbonhidrat": "low_carb", "Vejetaryen": "vegetarian", "Vegan": "vegan"}
        return mapping.get(self.diet_combo.currentText(), "balanced")

    def _do_register(self):
        name  = self.name_inp.text().strip()
        email = self.email_inp.text().strip()
        pw    = self.pw_inp.text()

        # Kullanıcı zaten giriş yapmışsa (profil eksik senaryosu) → auth adımını atla
        if state.token:
            if not name:
                self.toast.show_toast("Ad Soyad zorunludur.", "error")
                return
            self.save_btn.setText("Kaydediliyor..."); self.save_btn.setEnabled(False)
            self._on_auth_ok({"access_token": state.token, "user_id": state.user_id})
            return

        self.save_btn.setText("Kaydediliyor..."); self.save_btn.setEnabled(False)

        if not name or not email or not pw:
            self.toast.show_toast("Ad, e-posta ve şifre zorunludur.", "error")
            self.save_btn.setText("Profilimi Kaydet ve Devam Et"); self.save_btn.setEnabled(True)
            return
        if len(pw) < 6:
            self.toast.show_toast("Şifre en az 6 karakter olmalıdır.", "error")
            self.save_btn.setText("Profilimi Kaydet ve Devam Et"); self.save_btn.setEnabled(True)
            return

        api.post("/auth/register",
                 {"email": email, "password": pw, "full_name": name},
                 callback=self._on_auth_ok, error_cb=self._on_error)

    def _on_auth_ok(self, data):
        if data:
            state.token   = data.get("access_token")
            state.user_id = data.get("user_id")

        profile_data = {
            "full_name":            self.name_inp.text().strip(),
            "gender":               self._get_gender(),
            "age":                  self.age_spin.value(),
            "height_cm":            float(self.height_spin.value()),
            "weight_kg":            float(self.weight_spin.value()),
            "goal":                 self._get_goal(),
            "weekly_workout_days":  self.freq_slider.value(),
            "diet_preference":      self._get_diet(),
            "activity_level":       "moderate",
        }
        api.post("/user/profile", profile_data,
                 callback=self._on_profile_ok, error_cb=self._on_error)

    def _on_profile_ok(self, data):
        if data: state.profile = data
        btn_text = "Profilimi Oluştur ve Devam Et" if self._complete_mode else "Profilimi Kaydet ve Devam Et"
        self.save_btn.setText(btn_text)
        self.save_btn.setEnabled(True)
        self.register_success.emit()

    def _on_error(self, msg: str):
        btn_text = "Profilimi Oluştur ve Devam Et" if self._complete_mode else "Profilimi Kaydet ve Devam Et"
        self.save_btn.setText(btn_text)
        self.save_btn.setEnabled(True)
        self.toast.show_toast(msg, "error")

    def set_complete_mode(self, complete: bool):
        """complete=True: token var, e-posta/şifre alanlarını gizle."""
        self._complete_mode = complete
        self.cred_widget.setVisible(not complete)
        btn_text = "Profilimi Oluştur ve Devam Et" if complete else "Profilimi Kaydet ve Devam Et"
        self.save_btn.setText(btn_text)
        self.save_btn.setEnabled(True)
        self.name_inp.clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast.move((self.width() - self.toast.width()) // 2,
                        self.height() - self.toast.height() - 30)
