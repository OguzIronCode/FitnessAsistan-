from datetime import date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QFrame, QPushButton, QGridLayout,
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from api import api
from state import state
from theme import (BG, CARD, BORDER, PRIMARY, AI_CLR,
                   TEXT, TEXT_DIM, TEXT_FAINT, SUCCESS)
from widgets.stat_card import StatCard
from widgets.toast import Toast

DAYS_TR = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"]
MONTHS_TR = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
             "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
MEAL_NAMES = {"breakfast": "Kahvaltı", "lunch": "Öğle", "dinner": "Akşam", "snack": "Ara Öğün"}


class _ProfilePopup(QFrame):
    goto_settings    = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(230)
        self.hide()
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 14px;
            }}
            QLabel {{ background: transparent; border: none; border-radius: 0; }}
            QFrame QPushButton {{
                text-align: left;
                padding: 8px 12px;
                border-radius: 8px;
                font-size: 13px;
                border: none;
                background: transparent;
                color: white;
            }}
            QFrame QPushButton:hover {{
                background: rgba(255,255,255,0.07);
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(8)

        top = QHBoxLayout(); top.setSpacing(12)
        self.avatar_lbl = QLabel("")
        self.avatar_lbl.setFixedSize(48, 48)
        self.avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_lbl.setStyleSheet(f"""
            background: rgba(255,107,107,0.15);
            border-radius: 24px; font-size: 16px; font-weight: 600;
            color: {PRIMARY};
        """)
        top.addWidget(self.avatar_lbl)

        info = QVBoxLayout(); info.setSpacing(2)
        self.name_lbl = QLabel("—")
        self.name_lbl.setStyleSheet("font-weight: 600; font-size: 13px; background: transparent;")
        self.goal_lbl = QLabel("—")
        self.goal_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        info.addWidget(self.name_lbl); info.addWidget(self.goal_lbl)
        top.addLayout(info); top.addStretch()
        lay.addLayout(top)

        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER}; border: none; border-radius: 0;")
        lay.addWidget(sep)

        settings_btn = QPushButton("Profil Ayarları")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(lambda: (self.hide(), self.goto_settings.emit()))
        lay.addWidget(settings_btn)

        logout_btn = QPushButton("Çıkış Yap")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                color: #ef4444; background: transparent; border: none;
                text-align: left; padding: 8px 12px; border-radius: 8px; font-size: 13px;
            }}
            QPushButton:hover {{ background: rgba(239,68,68,0.10); }}
        """)
        logout_btn.clicked.connect(lambda: (self.hide(), self.logout_requested.emit()))
        lay.addWidget(logout_btn)

    def update_profile(self, name: str, goal: str):
        parts = (name or "?").split()
        initials = "".join(p[0].upper() for p in parts[:2])
        self.avatar_lbl.setText(initials)
        self.name_lbl.setText(name or "—")
        goal_map = {
            "cut":      "Yağ Yakma",
            "bulk":     "Kas Yapma",
            "maintain": "Form Koruma",
        }
        self.goal_lbl.setText(goal_map.get(goal, goal or "—"))

    def show_below(self, btn: "QWidget"):
        gp = btn.mapToGlobal(QPoint(btn.width() - self.width(), btn.height() + 6))
        self.move(self.parent().mapFromGlobal(gp))
        self.adjustSize()
        self.raise_()
        self.show()


class WeeklyChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 2.4), facecolor=CARD)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111, facecolor=CARD)
        self._style_axes()

    def _style_axes(self):
        ax = self.ax
        ax.tick_params(colors=TEXT_FAINT, labelsize=10)
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        ax.set_facecolor(CARD)
        self.fig.tight_layout(pad=1.5)

    def plot(self, perf_data: list):
        self.ax.clear()
        self._style_axes()
        if not perf_data:
            self.ax.text(0.5, 0.5, "Veri yok", color=TEXT_FAINT,
                         ha="center", va="center", transform=self.ax.transAxes)
            self.draw()
            return

        labels  = [DAYS_TR[i % 7] for i in range(len(perf_data))]
        cal     = [p.get("calories", 0) for p in perf_data]

        xs = range(len(labels))
        self.ax.fill_between(xs, cal, alpha=0.25, color=PRIMARY)
        self.ax.plot(xs, cal, color=PRIMARY, linewidth=2.5, marker="o",
                     markersize=5, markerfacecolor=PRIMARY)
        self.ax.set_xticks(list(xs))
        self.ax.set_xticklabels(labels)
        self.ax.yaxis.grid(True, color=BORDER, linestyle="--", alpha=0.5)
        self.ax.set_ylim(bottom=0)
        self.draw()


class HomePage(QWidget):
    goto_workout     = pyqtSignal()
    goto_settings    = pyqtSignal()
    logout_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup = _ProfilePopup(self)
        self._popup.goto_settings.connect(self.goto_settings)
        self._popup.logout_requested.connect(self.logout_requested)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(52)
        hdr_lay = QHBoxLayout(hdr); hdr_lay.setContentsMargins(20, 0, 16, 0)
        logo = QLabel("FitnessAsistanı")
        logo.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {PRIMARY}; background: transparent;")
        hdr_lay.addWidget(logo); hdr_lay.addStretch()
        self._avatar_btn = QPushButton("")
        self._avatar_btn.setFixedSize(38, 38)
        self._avatar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._avatar_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,107,107,0.12);
                border: 1px solid rgba(255,107,107,0.3);
                border-radius: 19px;
                font-size: 13px;
                font-weight: 600;
                color: {PRIMARY};
            }}
            QPushButton:hover {{
                background: rgba(255,107,107,0.22);
            }}
        """)
        self._avatar_btn.clicked.connect(self._toggle_popup)
        hdr_lay.addWidget(self._avatar_btn)
        outer.addWidget(hdr)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(28, 24, 28, 32)
        lay.setSpacing(20)

        now = date.today()
        date_lbl = QLabel(f"{DAYS_TR[now.weekday()]}, {now.day} {MONTHS_TR[now.month-1]} {now.year}")
        date_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
        lay.addWidget(date_lbl)

        self.welcome_lbl = QLabel("Tekrar hoş geldin")
        self.welcome_lbl.setStyleSheet("font-size: 28px; font-weight: 600; letter-spacing: -0.5px; background: transparent;")
        lay.addWidget(self.welcome_lbl)

        self.sub_lbl = QLabel("Yükleniyor...")
        self.sub_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 14px; background: transparent;")
        lay.addWidget(self.sub_lbl)

        stats_grid = QGridLayout()
        stats_grid.setSpacing(14)
        self.card_cal     = StatCard("Günlük Kalori",    "", PRIMARY)
        self.card_time    = StatCard("Antrenman Süresi",  "", "#60a5fa")
        self.card_workout = StatCard("Bu Hafta",          "", SUCCESS)
        self.card_protein = StatCard("Protein",           "", "#a78bfa")
        for i, c in enumerate([self.card_cal, self.card_time,
                                self.card_workout, self.card_protein]):
            stats_grid.addWidget(c, 0, i)
        lay.addLayout(stats_grid)

        mid_row = QHBoxLayout(); mid_row.setSpacing(16)

        chart_card = QFrame(); chart_card.setObjectName("card")
        chart_card_lay = QVBoxLayout(chart_card); chart_card_lay.setContentsMargins(16, 16, 16, 12)
        chart_title = QLabel("Haftalık Performans")
        chart_title.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        chart_sub = QLabel("Son 7 günlük kalori tüketimi")
        chart_sub.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
        chart_card_lay.addWidget(chart_title)
        chart_card_lay.addWidget(chart_sub)
        self.chart = WeeklyChart()
        self.chart.setMinimumHeight(200)
        chart_card_lay.addWidget(self.chart)
        mid_row.addWidget(chart_card, 2)

        ai_card = QFrame(); ai_card.setObjectName("cardAI")
        ai_lay = QVBoxLayout(ai_card); ai_lay.setContentsMargins(20, 20, 20, 20); ai_lay.setSpacing(12)
        ai_top = QHBoxLayout()
        ai_ico = QLabel("AI")
        ai_ico.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {PRIMARY}, stop:1 {AI_CLR});
            border-radius: 10px; font-size: 13px; font-weight: 600; padding: 8px;
            color: white;
        """)
        ai_ico.setFixedSize(40, 40)
        ai_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_pill = QLabel("AI")
        ai_pill.setStyleSheet(f"""
            background: rgba(124,58,237,0.2); color: #a78bfa;
            border-radius: 8px; padding: 3px 10px; font-size: 11px; font-weight: 600;
        """)
        ai_top.addWidget(ai_ico); ai_top.addStretch(); ai_top.addWidget(ai_pill)
        ai_lay.addLayout(ai_top)

        ai_title = QLabel("AI Antrenör Notu")
        ai_title.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        self.ai_tip_lbl = QLabel("AI notu yükleniyor...")
        self.ai_tip_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; line-height: 1.6; background: transparent;")
        self.ai_tip_lbl.setWordWrap(True)
        ai_lay.addWidget(ai_title)
        ai_lay.addWidget(self.ai_tip_lbl)
        ai_lay.addStretch()

        workout_btn = QPushButton("Bugünkü Antrenmanı Aç")
        workout_btn.setObjectName("primaryBtn")
        workout_btn.setMinimumHeight(42)
        workout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        workout_btn.clicked.connect(self.goto_workout)
        ai_lay.addWidget(workout_btn)
        mid_row.addWidget(ai_card, 1)
        lay.addLayout(mid_row)

        plan_row = QHBoxLayout(); plan_row.setSpacing(16)

        meal_card = QFrame(); meal_card.setObjectName("card")
        meal_lay = QVBoxLayout(meal_card); meal_lay.setContentsMargins(18, 16, 18, 16); meal_lay.setSpacing(10)
        mt = QHBoxLayout()
        t2 = QLabel("Bugünün Beslenmesi"); t2.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        mt.addWidget(t2); mt.addStretch()
        meal_lay.addLayout(mt)
        self.meal_list_lbl = QLabel("Henüz öğün eklenmedi.")
        self.meal_list_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 12px; background: transparent;")
        self.meal_list_lbl.setWordWrap(True)
        meal_lay.addWidget(self.meal_list_lbl)
        plan_row.addWidget(meal_card, 1)

        wo_card = QFrame(); wo_card.setObjectName("card")
        wo_lay = QVBoxLayout(wo_card); wo_lay.setContentsMargins(18, 16, 18, 16); wo_lay.setSpacing(10)
        wt = QHBoxLayout()
        t3 = QLabel("Bugünün Antrenmanı"); t3.setStyleSheet("font-size: 14px; font-weight: 600; background: transparent;")
        wt.addWidget(t3); wt.addStretch()
        wo_lay.addLayout(wt)
        self.wo_list_lbl = QLabel("Bugün antrenman yapılmadı.")
        self.wo_list_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 12px; background: transparent;")
        self.wo_list_lbl.setWordWrap(True)
        wo_lay.addWidget(self.wo_list_lbl)
        plan_row.addWidget(wo_card, 1)

        streak_card = QFrame(); streak_card.setObjectName("card")
        streak_lay = QVBoxLayout(streak_card); streak_lay.setContentsMargins(18, 16, 18, 16)
        sh = QHBoxLayout()
        sh.addWidget(QLabel("BU HAFTA"))
        sh.addStretch()
        streak_lay.addLayout(sh)
        self.streak_num = QLabel("0")
        self.streak_num.setStyleSheet("font-size: 44px; font-weight: 600; letter-spacing: -2px; background: transparent;")
        self.streak_sub = QLabel("antrenman")
        self.streak_sub.setStyleSheet(f"color: {TEXT_DIM}; font-size: 14px; background: transparent;")
        streak_lay.addWidget(self.streak_num)
        streak_lay.addWidget(self.streak_sub)
        streak_lay.addStretch()
        plan_row.addWidget(streak_card)
        lay.addLayout(plan_row)

        self.toast = Toast(self)

    def load_data(self):
        today = date.today().isoformat()
        api.get("/analytics/summary",  self._on_summary, self._on_err)
        api.get("/user/profile",        self._on_profile, self._on_err)
        api.get(f"/meals?date={today}", self._on_meals,   self._on_err)
        api.get("/workouts?limit=5",    self._on_workouts, self._on_err)
        api.get("/analytics/weekly-performance?days=7", self._on_perf, self._on_err)
        api.get("/ai/daily-tip",        self._on_tip,    self._on_err)

    def _on_summary(self, data):
        if not data: return
        today = data.get("today", {})
        weekly = data.get("weekly", {})
        cal    = round(today.get("calories", 0))
        caltgt = today.get("calorie_target", 2000)
        prot   = round(today.get("protein", 0))
        prottgt = today.get("protein_target", 150)
        dur    = weekly.get("total_duration", 0)
        wkcount = weekly.get("workout_count", 0)

        self.card_cal.update(cal, "kcal",
                             f"Hedef: {caltgt} kcal",
                             (cal / caltgt * 100) if caltgt else 0)
        self.card_time.update(dur, "dk",
                              f"Bu hafta {wkcount} antrenman",
                              min(100, dur / (wkcount * 60 + 1) * 100) if wkcount else 0)
        self.card_workout.update(wkcount, "antrenman", "Son 7 gün", min(100, wkcount / 5 * 100))
        self.card_protein.update(prot, "g",
                                 f"Hedef: {prottgt}g",
                                 (prot / prottgt * 100) if prottgt else 0)
        self.streak_num.setText(str(wkcount))

    def _toggle_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
        else:
            self._popup.show_below(self._avatar_btn)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._popup.hide()

    def _on_profile(self, data):
        if not data: return
        state.profile = data
        full_name = data.get("full_name") or ""
        name = full_name.split()[0] or "Sporcu"
        self.welcome_lbl.setText(f"Tekrar hoş geldin, {name}")
        parts = full_name.split()
        initials = "".join(p[0].upper() for p in parts[:2])
        self._avatar_btn.setText(initials)
        self._popup.update_profile(full_name, data.get("goal", ""))

    def _on_meals(self, data):
        if not data or not isinstance(data, list) or not data:
            self.meal_list_lbl.setText("Bugün henüz öğün eklenmedi.")
            return
        lines = []
        for m in data[:4]:
            meal_type = MEAL_NAMES.get(m.get("meal_type", ""), "")
            name = m.get("food_name_tr") or m.get("food_name") or "Bilinmeyen"
            cal  = round(m.get("calories", 0))
            lines.append(f"{name}  —  {cal} kcal")
        self.meal_list_lbl.setText("\n".join(lines))

    def _on_workouts(self, data):
        if not data or not isinstance(data, list) or not data:
            self.wo_list_lbl.setText("Bugün antrenman yapılmadı.")
            return
        today = date.today().isoformat()
        today_wos = [w for w in data if w.get("date") == today]
        if not today_wos:
            self.wo_list_lbl.setText("Bugün antrenman yapılmadı.")
            return
        lines = []
        for w in today_wos[:3]:
            title = w.get("program_title") or "Serbest Antrenman"
            sets  = w.get("total_sets", 0)
            lines.append(f"{title}  —  {sets} set")
        self.wo_list_lbl.setText("\n".join(lines))

    def _on_perf(self, data):
        if data and isinstance(data, list):
            self.chart.plot(data)

    def _on_tip(self, data):
        tip = (data or {}).get("tip", "Tutarlı ol, yeterli protein al.")
        self.ai_tip_lbl.setText(tip)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.toast.move((self.width() - self.toast.width()) // 2,
                        self.height() - self.toast.height() - 30)

    def _on_err(self, msg: str):
        self.sub_lbl.setText("Bazı veriler yüklenemedi.")
