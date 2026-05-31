from datetime import date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QFrame, QPushButton, QListWidget,
                             QListWidgetItem, QDialog, QDialogButtonBox,
                             QSpinBox, QDoubleSpinBox, QComboBox, QSplitter,
                             QSizePolicy, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from exercise_images import find_image

from api import api
from state import state
from theme import (BG, CARD, CARD2, BORDER, PRIMARY, TEXT, TEXT_DIM,
                   TEXT_FAINT, SUCCESS, AI_CLR)
from widgets.toast import Toast


class WorkoutPage(QWidget):
    workout_finished = pyqtSignal()   # antrenman bitince home/analytics yenile

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_workout_id: str | None = None
        self._active_program: dict | None = None
        self._exercises: list[dict] = []
        self._current_ex_idx: int = 0
        self._elapsed_sec: int = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Aktif antrenman banner ─────────────────────────────────────────
        self.banner = QFrame()
        self.banner.setObjectName("cardPrimary")
        self.banner.setFixedHeight(64)
        self.banner.hide()
        ban_lay = QHBoxLayout(self.banner); ban_lay.setContentsMargins(20, 0, 20, 0)

        icon_lbl = QLabel(""); icon_lbl.setStyleSheet(f"""
            background: rgba(255,107,107,0.12); border-radius: 10px;
            font-size: 20px; padding: 6px; color: {PRIMARY};
        """); icon_lbl.setFixedSize(40, 40); icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ban_lay.addWidget(icon_lbl); ban_lay.addSpacing(12)

        self.ban_name = QLabel("Antrenman devam ediyor")
        self.ban_name.setStyleSheet("font-weight: 600; font-size: 14px; background: transparent;")
        ban_lay.addWidget(self.ban_name); ban_lay.addStretch()

        self.timer_lbl = QLabel("00:00")
        self.timer_lbl.setStyleSheet(f"""
            background: rgba(255,107,107,0.12); color: {PRIMARY};
            border-radius: 10px; padding: 4px 12px; font-weight: 600; font-family: monospace;
        """)
        ban_lay.addWidget(self.timer_lbl)
        ban_lay.addSpacing(10)

        self.finish_btn = QPushButton("Bitir")
        self.finish_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(74,222,128,0.1);
                color: {SUCCESS};
                border: 1px solid rgba(74,222,128,0.3);
                border-radius: 8px; padding: 6px 14px;
            }}
            QPushButton:hover {{ background: rgba(74,222,128,0.2); }}
        """)
        self.finish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.finish_btn.clicked.connect(self._finish_workout)
        ban_lay.addWidget(self.finish_btn)
        root.addWidget(self.banner)

        # ── Ana içerik ────────────────────────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {BORDER}; }}")
        root.addWidget(splitter, 1)

        # ── Sol: Egzersiz listesi ──────────────────────────────────────────
        left = QWidget()
        left.setMinimumWidth(280); left.setMaximumWidth(380)
        lft_lay = QVBoxLayout(left); lft_lay.setContentsMargins(16, 16, 16, 16); lft_lay.setSpacing(12)

        lft_hdr = QHBoxLayout()
        self.list_title = QLabel("Antrenman Egzersizleri")
        self.list_title.setStyleSheet("font-size: 17px; font-weight: 600; background: transparent;")
        self.count_lbl = QLabel("0 / 0")
        self.count_lbl.setStyleSheet(f"""
            background: rgba(255,107,107,0.12); color: {PRIMARY};
            border-radius: 10px; padding: 3px 10px; font-size: 12px; font-weight: 600;
        """)
        lft_hdr.addWidget(self.list_title); lft_hdr.addStretch(); lft_hdr.addWidget(self.count_lbl)
        lft_lay.addLayout(lft_hdr)

        self.sub_lbl = QLabel("Program seçilince egzersizler görünecek.")
        self.sub_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 12px; background: transparent;")
        self.sub_lbl.setWordWrap(True)
        lft_lay.addWidget(self.sub_lbl)

        self.ex_list = QListWidget()
        self.ex_list.setSpacing(2)
        self.ex_list.itemClicked.connect(self._on_ex_clicked)
        lft_lay.addWidget(self.ex_list, 1)

        prog_btn = QPushButton("Program Seç")
        prog_btn.setObjectName("primaryBtn"); prog_btn.setMinimumHeight(42)
        prog_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prog_btn.clicked.connect(self._open_programs)
        lft_lay.addWidget(prog_btn)
        splitter.addWidget(left)

        # ── Sağ: Egzersiz detayı + set kaydı ─────────────────────────────
        right = QScrollArea(); right.setWidgetResizable(True)
        self.right_content = QWidget()
        rgt_lay = QVBoxLayout(self.right_content)
        rgt_lay.setContentsMargins(24, 20, 24, 24); rgt_lay.setSpacing(16)

        # Boş durum
        self.empty_lbl = QLabel("Sol panelden bir egzersiz seçin\nveya program başlatın.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 15px; line-height: 2; background: transparent;")
        rgt_lay.addStretch(); rgt_lay.addWidget(self.empty_lbl); rgt_lay.addStretch()

        right.setWidget(self.right_content)
        splitter.addWidget(right)
        splitter.setSizes([320, 700])

        self.toast = Toast(self)

    def _open_programs(self):
        dlg = ProgramDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.selected_program:
            self._start_program(dlg.selected_program)

    def _start_program(self, program: dict):
        self._active_program = program
        title = program.get("title", "Antrenman")

        # Antrenman kaydı oluştur
        today = date.today().isoformat()
        api.post("/workouts",
                 {"date": today, "program_id": program.get("id"), "notes": title},
                 callback=self._on_workout_created, error_cb=self._on_err)

        # Egzersizler
        api.post("/ai/generate-exercises", {},
                 callback=self._on_exercises, error_cb=self._on_err,
                 params={"title": title, "goal": program.get("goal",""),
                         "equipment": program.get("equipment",""),
                         "level": program.get("level",""),
                         "duration_min": program.get("time_per_workout", 45)})

    def _on_workout_created(self, data):
        if data:
            self._active_workout_id = data.get("id")
            name = (self._active_program or {}).get("title","Antrenman")
            self.ban_name.setText(name)
            self.banner.show()
            self._elapsed_sec = 0
            self._timer.start(1000)

    def _on_exercises(self, data):
        exs = (data or {}).get("exercises", [])
        self._exercises = exs
        self._current_ex_idx = 0
        self.ex_list.clear()
        for i, ex in enumerate(exs):
            item = QListWidgetItem(f"  {i+1}. {ex.get('name','?')}  —  {ex.get('sets',3)}×{ex.get('reps','10')}")
            self.ex_list.addItem(item)

        self.count_lbl.setText(f"0 / {len(exs)}")
        self.sub_lbl.setText(f"{len(exs)} egzersiz  ·  {(self._active_program or {}).get('time_per_workout',45)} dk")
        self.list_title.setText((self._active_program or {}).get("title", "Antrenman"))
        if exs:
            self.ex_list.setCurrentRow(0)
            self._show_exercise(0)

    def _on_ex_clicked(self, item):
        idx = self.ex_list.row(item)
        self._show_exercise(idx)

    def _show_exercise(self, idx: int):
        if idx >= len(self._exercises): return
        self._current_ex_idx = idx
        ex = self._exercises[idx]

        # Sağ paneli temizle — alt layout içindeki widget'lar da dahil
        lay = self.right_content.layout()
        while lay.count():
            lay.takeAt(0)
        for child in self.right_content.findChildren(QWidget):
            child.deleteLater()

        lay = self.right_content.layout()
        ex_name = ex.get("name", "?")

        # ── Üst satır: başlık + görsel ────────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Sol: başlık + bilgi
        left_col = QVBoxLayout()

        name_lbl = QLabel(ex_name)
        name_lbl.setStyleSheet("font-size: 22px; font-weight: 600; background: transparent;")
        name_lbl.setWordWrap(True)
        left_col.addWidget(name_lbl)
        top_row.addLayout(left_col, 1)

        # Sağ: görsel
        img_path = find_image(ex_name)
        if img_path:
            img_frame = QFrame()
            img_frame.setFixedSize(220, 160)
            img_frame.setStyleSheet(f"""
                QFrame {{
                    background: {CARD};
                    border: 1px solid {BORDER};
                    border-radius: 12px;
                }}
                QLabel {{ background: transparent; border: none; border-radius: 0; }}
            """)
            _wl = QVBoxLayout(img_frame)
            _wl.setContentsMargins(4, 4, 4, 4)
            img_lbl = QLabel()
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setStyleSheet("background: transparent;")
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(212, 152,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                img_lbl.setPixmap(pixmap)
            else:
                img_lbl.setText("Görsel yok")
                img_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 12px; background: transparent;")
            _wl.addWidget(img_lbl)
            top_row.addWidget(img_frame, 0, Qt.AlignmentFlag.AlignTop)
        else:
            no_img = QFrame()
            no_img.setFixedSize(220, 160)
            no_img.setStyleSheet(f"""
                QFrame {{
                    background: rgba(255,255,255,0.03);
                    border: 1px dashed {BORDER};
                    border-radius: 12px;
                }}
                QLabel {{ background: transparent; border: none; border-radius: 0; }}
            """)
            _nl = QVBoxLayout(no_img)
            _nl.setContentsMargins(0, 0, 0, 0)
            ph = QLabel("Görsel yok")
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ph.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 12px; background: transparent;")
            _nl.addWidget(ph)
            top_row.addWidget(no_img, 0, Qt.AlignmentFlag.AlignTop)

        lay.addLayout(top_row)

        # Bilgi
        info_row = QHBoxLayout()
        for label, val in [("Kas Grubu", ex.get("muscle_group","Genel")),
                           ("Set", str(ex.get("sets",3))),
                           ("Tekrar", str(ex.get("reps","10-12"))),
                           ("Dinlenme", f"{ex.get('rest_sec',60)}sn")]:
            chip = QFrame(); chip.setStyleSheet(f"""
                QFrame {{
                    background: {CARD};
                    border: 1px solid {BORDER};
                    border-radius: 10px;
                }}
                QLabel {{ background: transparent; border: none; border-radius: 0; }}
            """)
            ch_lay = QVBoxLayout(chip); ch_lay.setContentsMargins(12, 8, 12, 8); ch_lay.setSpacing(2)
            lbl = QLabel(label.upper()); lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent;")
            val_lbl = QLabel(val); val_lbl.setStyleSheet(f"font-weight: 600; font-size: 15px; background: transparent;")
            ch_lay.addWidget(lbl); ch_lay.addWidget(val_lbl)
            info_row.addWidget(chip)
        info_row.addStretch()
        lay.addLayout(info_row)

        # İpucu
        tip = ex.get("tip","")
        if tip:
            tip_card = QFrame(); tip_card.setObjectName("card")
            t_lay = QHBoxLayout(tip_card); t_lay.setContentsMargins(14, 12, 14, 12)
            tip_lbl = QLabel(tip); tip_lbl.setWordWrap(True)
            tip_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
            t_lay.addWidget(tip_lbl)
            lay.addWidget(tip_card)

        # Set kayıt formu
        form_title = QLabel("Set Kaydet")
        form_title.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        lay.addWidget(form_title)

        set_card = QFrame(); set_card.setObjectName("card")
        sc_lay = QGridLayout(set_card); sc_lay.setContentsMargins(16, 14, 16, 14); sc_lay.setSpacing(10)

        sc_lay.addWidget(self._form_lbl("SET NO"), 0, 0)
        sc_lay.addWidget(self._form_lbl("TEKRAR"), 0, 1)
        sc_lay.addWidget(self._form_lbl("AĞIRLIK (kg)"), 0, 2)

        self._set_num = QSpinBox(); self._set_num.setRange(1,20); self._set_num.setValue(1); self._set_num.setMinimumHeight(44)
        self._reps_spin = QSpinBox(); self._reps_spin.setRange(1,100)
        try:
            self._reps_spin.setValue(int(str(ex.get("reps","10")).split("-")[0]))
        except Exception:
            self._reps_spin.setValue(10)
        self._reps_spin.setMinimumHeight(44)
        self._weight_spin = QDoubleSpinBox(); self._weight_spin.setRange(0,500); self._weight_spin.setValue(20)
        self._weight_spin.setSingleStep(2.5); self._weight_spin.setMinimumHeight(44)

        sc_lay.addWidget(self._set_num,    1, 0)
        sc_lay.addWidget(self._reps_spin,  1, 1)
        sc_lay.addWidget(self._weight_spin,1, 2)
        lay.addWidget(set_card)

        log_btn = QPushButton("Seti Kaydet")
        log_btn.setObjectName("primaryBtn"); log_btn.setMinimumHeight(48)
        log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        log_btn.clicked.connect(lambda: self._log_set(ex.get("name","?")))
        lay.addWidget(log_btn)

        lay.addStretch()

    def _form_lbl(self, text):
        l = QLabel(text); l.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        return l

    def _log_set(self, ex_name: str):
        if not self._active_workout_id:
            self.toast.show_toast("Önce antrenman başlatın!", "error"); return
        payload = {
            "workout_id":   self._active_workout_id,
            "exercise_name": ex_name,
            "set_number":   self._set_num.value(),
            "reps":         self._reps_spin.value(),
            "weight_kg":    self._weight_spin.value(),
        }
        api.post("/workouts/sets", payload,
                 callback=lambda _: (self.toast.show_toast("Set kaydedildi!", "success"),
                                     self._set_num.setValue(self._set_num.value() + 1)),
                 error_cb=self._on_err)

    def _finish_workout(self):
        if not self._active_workout_id: return
        self._timer.stop()
        dur = self._elapsed_sec // 60

        def _on_finished(_):
            self.toast.show_toast(f"Antrenman bitti! {dur} dk", "success")
            self._reset_workout()
            self.workout_finished.emit()   # home + analytics'i güncelle

        api.patch(f"/workouts/{self._active_workout_id}/finish",
                  params={"duration_min": max(1, dur)},
                  callback=_on_finished,
                  error_cb=self._on_err)

    def _reset_workout(self):
        self._active_workout_id = None
        self._active_program = None
        self._elapsed_sec = 0
        self.banner.hide()

    def _tick(self):
        self._elapsed_sec += 1
        m, s = divmod(self._elapsed_sec, 60)
        self.timer_lbl.setText(f"{m:02d}:{s:02d}")

    def _on_err(self, msg: str):
        self.toast.show_toast(msg, "error")

    def showEvent(self, event):
        super().showEvent(event)
        if self._active_workout_id:
            self.banner.show()
            if not self._timer.isActive():
                self._timer.start(1000)


class ProgramDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Program Seç")
        self.setMinimumSize(680, 520)
        self.selected_program = None
        self._build_ui()
        self._load_programs()

    def _build_ui(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(20, 20, 20, 20); lay.setSpacing(14)

        t = QLabel("Antrenman Programı Seç")
        t.setStyleSheet("font-size: 18px; font-weight: 600; background: transparent;")
        lay.addWidget(t)

        filter_row = QHBoxLayout()
        self.goal_combo = QComboBox()
        self.goal_combo.addItems(["Tüm Hedefler","Bodybuilding","Powerbuilding","Athletics","Muscle & Sculpting"])
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Tüm Seviyeler","Beginner","Intermediate","Advanced"])
        self.equip_combo = QComboBox()
        self.equip_combo.addItems(["Tüm Ekipmanlar","Full Gym","At Home","Dumbbell Only"])
        for c in [self.goal_combo, self.level_combo, self.equip_combo]:
            c.setMinimumHeight(38); filter_row.addWidget(c)
        srch_btn = QPushButton("Filtrele"); srch_btn.setMinimumHeight(38)
        srch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        srch_btn.clicked.connect(self._load_programs)
        filter_row.addWidget(srch_btn)
        lay.addLayout(filter_row)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.prog_content = QWidget()
        self.prog_lay = QVBoxLayout(self.prog_content); self.prog_lay.setContentsMargins(0,0,0,0); self.prog_lay.setSpacing(8)
        self.prog_lay.addStretch()
        self.scroll.setWidget(self.prog_content)
        lay.addWidget(self.scroll, 1)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def _load_programs(self):
        params = {}
        g = self.goal_combo.currentText()
        if g != "Tüm Hedefler": params["goal"] = g
        l = self.level_combo.currentText()
        if l != "Tüm Seviyeler": params["level"] = l
        e = self.equip_combo.currentText()
        if e != "Tüm Ekipmanlar": params["equipment"] = e
        api.get("/exercises/programs", self._on_programs, lambda _: None, params=params)

    def _on_programs(self, data):
        progs = (data or {}).get("programs", [])
        while self.prog_lay.count() > 1:
            item = self.prog_lay.takeAt(0)
            if item and item.widget(): item.widget().deleteLater()
        if not progs:
            empty = QLabel("Bu filtreye uygun program bulunamadı.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 13px; padding: 20px;")
            self.prog_lay.insertWidget(0, empty)
            return
        for p in progs:
            self.prog_lay.insertWidget(self.prog_lay.count()-1, self._prog_card(p))

    def _prog_card(self, p: dict) -> QFrame:
        card = QFrame(); card.setObjectName("card")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border-color: {PRIMARY};
                background: rgba(255,107,107,0.05);
            }}
            QLabel {{ background: transparent; border: none; border-radius: 0; }}
        """)
        lay = QHBoxLayout(card); lay.setContentsMargins(16, 14, 16, 14)

        info = QVBoxLayout()
        t = QLabel(p.get("title","?")); t.setStyleSheet("font-weight: 600; font-size: 14px; background: transparent;")
        d = QLabel(p.get("description","")); d.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
        d.setWordWrap(True)
        info.addWidget(t); info.addWidget(d)

        pills = QHBoxLayout()
        for pill_text, color in [
            (p.get("level",""), TEXT_FAINT),
            (p.get("goal",""), PRIMARY),
            (f"{p.get('time_per_workout',45)} dk", "#60a5fa"),
        ]:
            if pill_text:
                lbl = QLabel(pill_text)
                lbl.setStyleSheet(f"""
                    background: rgba(255,255,255,0.06);
                    color: {color};
                    border-radius: 8px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: 500;
                """)
                pills.addWidget(lbl)
        pills.addStretch()
        info.addLayout(pills)
        lay.addLayout(info, 1)

        sel_btn = QPushButton("Seç →")
        sel_btn.setObjectName("primaryBtn"); sel_btn.setFixedSize(80, 36)
        sel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sel_btn.clicked.connect(lambda _, prog=p: (setattr(self, "selected_program", prog), self.accept()))
        lay.addWidget(sel_btn)
        return card
