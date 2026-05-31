from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QScrollArea,
                             QComboBox, QSpinBox, QDoubleSpinBox, QSlider,
                             QButtonGroup, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal

from api import api
from state import state
from theme import PRIMARY, TEXT_DIM, TEXT_FAINT, CARD, BORDER
from widgets.toast import Toast


class _GoalCard(QPushButton):
    def __init__(self, icon, title, value, parent=None):
        super().__init__(parent)
        self.value = value
        self.setCheckable(True)
        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel(title)
        t.setStyleSheet("font-size: 12px; font-weight: 600; background: transparent;")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t)
        self._refresh()
        self.toggled.connect(lambda _: self._refresh())

    def _refresh(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,107,107,0.1);
                    border: 2px solid {PRIMARY};
                    border-radius: 12px; color: white;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {CARD};
                    border: 1px solid {BORDER};
                    border-radius: 12px; color: white;
                }}
                QPushButton:hover {{ border-color: rgba(255,255,255,0.2); }}
            """)


class SettingsPage(QWidget):
    profile_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(64)
        hdr_lay = QHBoxLayout(hdr); hdr_lay.setContentsMargins(24, 0, 24, 0)
        title = QLabel("Profil Ayarları")
        title.setStyleSheet("font-size: 18px; font-weight: 600; background: transparent;")
        hdr_lay.addWidget(title); hdr_lay.addStretch()
        self.save_btn = QPushButton("Değişiklikleri Kaydet")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._save)
        hdr_lay.addWidget(self.save_btn)
        root.addWidget(hdr)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        root.addWidget(scroll, 1)

        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(28, 24, 28, 40); lay.setSpacing(20)

        lay.addWidget(self._section_lbl("Kişisel Bilgiler"))
        s1 = QFrame(); s1.setObjectName("card")
        s1_lay = QVBoxLayout(s1); s1_lay.setContentsMargins(20, 18, 20, 18); s1_lay.setSpacing(14)

        s1_lay.addWidget(self._lbl("AD SOYAD"))
        self.name_inp = QLineEdit(); self.name_inp.setMinimumHeight(44)
        s1_lay.addWidget(self.name_inp)

        nums_row = QHBoxLayout(); nums_row.setSpacing(12)
        for attr, label, mn, mx, default in [
            ("age_spin",    "YAŞ",        10, 100, 25),
            ("height_spin", "BOY (cm)",   100, 250, 175),
        ]:
            col = QVBoxLayout()
            col.addWidget(self._lbl(label))
            sp = QSpinBox(); sp.setRange(mn, mx); sp.setValue(default); sp.setMinimumHeight(44)
            setattr(self, attr, sp); col.addWidget(sp); nums_row.addLayout(col)

        w_col = QVBoxLayout()
        w_col.addWidget(self._lbl("KİLO (kg)"))
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(30, 300); self.weight_spin.setValue(75); self.weight_spin.setMinimumHeight(44)
        w_col.addWidget(self.weight_spin); nums_row.addLayout(w_col)
        s1_lay.addLayout(nums_row)
        lay.addWidget(s1)

        lay.addWidget(self._section_lbl("Hedefin"))
        goal_row = QHBoxLayout(); goal_row.setSpacing(10)
        self._goal_grp = QButtonGroup(self); self._goal_grp.setExclusive(True)
        self.goal_cut      = _GoalCard("", "Yağ Yak",   "cut")
        self.goal_bulk     = _GoalCard("", "Kas Yap",    "bulk")
        self.goal_maintain = _GoalCard("", "Form Koru",  "maintain")
        for b in (self.goal_cut, self.goal_bulk, self.goal_maintain):
            self._goal_grp.addButton(b); goal_row.addWidget(b)
        self.goal_maintain.setChecked(True)
        lay.addLayout(goal_row)

        lay.addWidget(self._section_lbl("Antrenman & Beslenme"))
        s3 = QFrame(); s3.setObjectName("card")
        s3_lay = QVBoxLayout(s3); s3_lay.setContentsMargins(20, 18, 20, 18); s3_lay.setSpacing(14)

        freq_row = QHBoxLayout()
        freq_row.addWidget(self._lbl("HAFTALIK ANTRENMAN GÜNÜ"))
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
        self.freq_slider.valueChanged.connect(lambda v: self.freq_lbl.setText(f"{v} gün / hafta"))
        s3_lay.addWidget(self.freq_slider)

        s3_lay.addWidget(self._lbl("AKTİVİTE SEVİYESİ"))
        self.activity_combo = QComboBox(); self.activity_combo.setMinimumHeight(44)
        self.activity_combo.addItems([
            "Hareketsiz (Masa başı)",
            "Az aktif (haftada 1-2)",
            "Orta aktif (haftada 3-5)",
            "Çok aktif (haftada 6-7)",
            "Profesyonel sporcu",
        ])
        s3_lay.addWidget(self.activity_combo)

        s3_lay.addWidget(self._lbl("BESLENME TERCİHİ"))
        self.diet_combo = QComboBox(); self.diet_combo.setMinimumHeight(44)
        self.diet_combo.addItems([
            "Dengeli (Karma)", "Yüksek Protein",
            "Düşük Karbonhidrat", "Vejetaryen", "Vegan",
        ])
        s3_lay.addWidget(self.diet_combo)
        lay.addWidget(s3)

        self.toast = Toast(self)

    def _lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        return l

    def _section_lbl(self, text):
        l = QLabel(text)
        l.setStyleSheet("font-size: 16px; font-weight: 600; background: transparent;")
        return l

    def _get_goal(self):
        for b in self._goal_grp.buttons():
            if b.isChecked():
                return b.value
        return "maintain"

    def _get_activity(self):
        mapping = {
            "Hareketsiz (Masa başı)":   "sedentary",
            "Az aktif (haftada 1-2)":   "light",
            "Orta aktif (haftada 3-5)": "moderate",
            "Çok aktif (haftada 6-7)":  "active",
            "Profesyonel sporcu":        "very_active",
        }
        return mapping.get(self.activity_combo.currentText(), "moderate")

    def _get_diet(self):
        mapping = {
            "Dengeli (Karma)":       "balanced",
            "Yüksek Protein":        "high_protein",
            "Düşük Karbonhidrat":    "low_carb",
            "Vejetaryen":            "vegetarian",
            "Vegan":                 "vegan",
        }
        return mapping.get(self.diet_combo.currentText(), "balanced")

    def load_data(self):
        api.get("/user/profile", self._on_profile, lambda _: None)

    def _on_profile(self, data):
        if not data:
            return
        state.profile = data
        self.name_inp.setText(data.get("full_name") or "")
        self.age_spin.setValue(data.get("age") or 25)
        self.height_spin.setValue(int(data.get("height_cm") or 175))
        self.weight_spin.setValue(float(data.get("weight_kg") or 75))
        self.freq_slider.setValue(data.get("weekly_workout_days") or 4)

        goal = data.get("goal", "maintain")
        for b in self._goal_grp.buttons():
            if b.value == goal:
                b.setChecked(True)

        act_map = {
            "sedentary":   "Hareketsiz (Masa başı)",
            "light":       "Az aktif (haftada 1-2)",
            "moderate":    "Orta aktif (haftada 3-5)",
            "active":      "Çok aktif (haftada 6-7)",
            "very_active": "Profesyonel sporcu",
        }
        act_tr = act_map.get(data.get("activity_level", "moderate"), "Orta aktif (haftada 3-5)")
        idx = self.activity_combo.findText(act_tr)
        if idx >= 0:
            self.activity_combo.setCurrentIndex(idx)

        diet_map = {
            "balanced":     "Dengeli (Karma)",
            "high_protein": "Yüksek Protein",
            "low_carb":     "Düşük Karbonhidrat",
            "vegetarian":   "Vejetaryen",
            "vegan":        "Vegan",
        }
        diet_tr = diet_map.get(data.get("diet_preference", "balanced"), "Dengeli (Karma)")
        idx = self.diet_combo.findText(diet_tr)
        if idx >= 0:
            self.diet_combo.setCurrentIndex(idx)

    def _save(self):
        self.save_btn.setText("Kaydediliyor..."); self.save_btn.setEnabled(False)
        payload = {
            "full_name":           self.name_inp.text().strip() or None,
            "age":                 self.age_spin.value(),
            "height_cm":           float(self.height_spin.value()),
            "weight_kg":           self.weight_spin.value(),
            "goal":                self._get_goal(),
            "weekly_workout_days": self.freq_slider.value(),
            "activity_level":      self._get_activity(),
            "diet_preference":     self._get_diet(),
        }
        api.put("/user/profile", payload,
                callback=self._on_saved, error_cb=self._on_err)

    def _on_saved(self, data):
        self.save_btn.setText("Değişiklikleri Kaydet"); self.save_btn.setEnabled(True)
        if data:
            state.profile = data
        self.toast.show_toast("Profil güncellendi", "success")
        self.profile_saved.emit()

    def _on_err(self, msg: str):
        self.save_btn.setText("Değişiklikleri Kaydet"); self.save_btn.setEnabled(True)
        self.toast.show_toast(msg, "error")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast.move((self.width() - self.toast.width()) // 2,
                        self.height() - self.toast.height() - 30)
