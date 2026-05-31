from datetime import date, timedelta
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QFrame, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QSpinBox,
                             QDoubleSpinBox, QSizePolicy, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from api import api
from theme import (BG, CARD, BORDER, PRIMARY, AI_CLR,
                   TEXT, TEXT_DIM, TEXT_FAINT, SUCCESS, WARN)
from widgets.toast import Toast

DAYS_TR = ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"]


def _make_chart(facecolor=CARD):
    fig = Figure(figsize=(6, 2.5), facecolor=facecolor)
    ax  = fig.add_subplot(111, facecolor=facecolor)
    ax.tick_params(colors=TEXT_FAINT, labelsize=9)
    for sp in ax.spines.values():
        sp.set_color(BORDER)
    fig.tight_layout(pad=1.5)
    return fig, ax


class PerformanceChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, self.ax = _make_chart()
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(210)

    def plot(self, data: list):
        self.ax.clear()
        self.ax.set_facecolor(CARD)
        self.ax.tick_params(colors=TEXT_FAINT, labelsize=9)
        for sp in self.ax.spines.values():
            sp.set_color(BORDER)
        if not data:
            self.ax.text(0.5,0.5,"Veri yok",color=TEXT_FAINT,ha="center",
                         va="center",transform=self.ax.transAxes); self.draw(); return
        xs    = range(len(data))
        cal   = [d.get("calories",0) for d in data]
        dur   = [d.get("workout_minutes",0) for d in data]
        lbls  = [d.get("date","")[-5:] for d in data]
        ax2   = self.ax.twinx()
        self.ax.fill_between(xs, cal, alpha=0.2, color=PRIMARY)
        self.ax.plot(xs, cal, color=PRIMARY, linewidth=2, marker="o", markersize=4)
        ax2.bar(xs, dur, alpha=0.35, color="#60a5fa", width=0.4)
        ax2.tick_params(colors=TEXT_FAINT, labelsize=8)
        for sp in ax2.spines.values(): sp.set_color(BORDER)
        self.ax.set_xticks(list(xs)); self.ax.set_xticklabels(lbls, fontsize=9)
        self.ax.yaxis.grid(True, color=BORDER, linestyle="--", alpha=0.4)
        self.ax.set_ylim(bottom=0)
        self.fig.tight_layout(pad=1)
        self.draw()


class MacroDonut(FigureCanvas):
    def __init__(self, parent=None):
        self.fig, self.ax = _make_chart(BG)
        self.fig.set_size_inches(3, 2.5)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(240, 200)
        self._draw_empty()

    def _draw_empty(self):
        self.ax.clear(); self.ax.set_facecolor(BG)
        self.ax.pie([1], colors=[BORDER], startangle=90,
                    wedgeprops=dict(width=0.5)); self.draw()

    def update_macros(self, prot, carb, fat):
        total = prot + carb + fat or 1
        self.ax.clear(); self.ax.set_facecolor(BG)
        self.ax.pie(
            [prot, carb, fat],
            colors=["#a78bfa", "#60a5fa", WARN],
            labels=["Protein","Karbonhidrat","Yağ"],
            autopct="%1.0f%%",
            startangle=90,
            textprops={"color": TEXT_FAINT, "fontsize": 8},
            wedgeprops=dict(width=0.5),
        )
        self.fig.tight_layout(pad=0.5)
        self.draw()


class AnalyticsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._days = 7
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        outer = QVBoxLayout(self); outer.setContentsMargins(0,0,0,0)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout(content); lay.setContentsMargins(24,20,24,28); lay.setSpacing(20)

        top = QHBoxLayout()
        title = QLabel("Performans Analizi")
        title.setStyleSheet("font-size: 22px; font-weight: 600; background: transparent;")
        top.addWidget(title); top.addStretch()

        period_frame = QFrame(); period_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(15,15,25,0.5);
                border: 1px solid {BORDER};
                border-radius: 999px;
            }}
        """)
        pf_lay = QHBoxLayout(period_frame); pf_lay.setContentsMargins(4,4,4,4); pf_lay.setSpacing(2)
        self._period_btns = []
        for label, days in [("7G",7),("14G",14),("30G",30)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedSize(52, 30)
            btn.clicked.connect(lambda _, d=days: self._set_period(d))
            self._period_btns.append((btn, days))
            pf_lay.addWidget(btn)
        self._period_btns[0][0].setChecked(True)
        self._update_period_styles()
        top.addWidget(period_frame)
        lay.addLayout(top)

        summary_grid = QGridLayout(); summary_grid.setSpacing(12)
        self.sum_cal      = self._summary_card("Toplam Kalori",    PRIMARY)
        self.sum_workouts = self._summary_card("Antrenman Sayısı", SUCCESS)
        self.sum_duration = self._summary_card("Toplam Süre",      "#60a5fa")
        self.sum_streak   = self._summary_card("Aktif Gün",        "#fb923c")
        for i, c in enumerate([self.sum_cal, self.sum_workouts, self.sum_duration, self.sum_streak]):
            summary_grid.addWidget(c, 0, i)
        lay.addLayout(summary_grid)

        perf_card = QFrame(); perf_card.setObjectName("card")
        pc_lay = QVBoxLayout(perf_card); pc_lay.setContentsMargins(16,14,16,12)
        pc_hdr = QHBoxLayout()
        pc_hdr.addWidget(self._lbl("Haftalık Performans","15px"))
        pc_hdr.addStretch()
        legend = QHBoxLayout()
        for dot_col, lbl_txt in [(PRIMARY,"Kalori"),("#60a5fa","Antrenman dk")]:
            dot = QLabel("●"); dot.setStyleSheet(f"color: {dot_col}; font-size: 14px; background: transparent;")
            l   = QLabel(lbl_txt); l.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
            legend.addWidget(dot); legend.addWidget(l); legend.addSpacing(8)
        pc_hdr.addLayout(legend)
        pc_lay.addLayout(pc_hdr)
        self.perf_chart = PerformanceChart()
        pc_lay.addWidget(self.perf_chart)
        lay.addWidget(perf_card)

        bot_row = QHBoxLayout(); bot_row.setSpacing(14)

        macro_card = QFrame(); macro_card.setObjectName("card")
        mc_lay = QVBoxLayout(macro_card); mc_lay.setContentsMargins(16,14,16,14)
        mc_lay.addWidget(self._lbl("Makro Dağılımı","14px"))
        self.donut = MacroDonut()
        mc_lay.addWidget(self.donut, 0, Qt.AlignmentFlag.AlignCenter)
        self.macro_detail_lbl = QLabel("—")
        self.macro_detail_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        self.macro_detail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mc_lay.addWidget(self.macro_detail_lbl)
        bot_row.addWidget(macro_card)

        pr_card = QFrame(); pr_card.setObjectName("card")
        pr_lay = QVBoxLayout(pr_card); pr_lay.setContentsMargins(16,14,16,14)
        pr_lay.addWidget(self._lbl("Kişisel Rekörlar","14px"))
        self.pr_table = QTableWidget(0, 3)
        self.pr_table.setHorizontalHeaderLabels(["Egzersiz","Ağırlık","Tarih"])
        self.pr_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.pr_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.pr_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.pr_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.pr_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        pr_lay.addWidget(self.pr_table, 1)
        bot_row.addWidget(pr_card, 1)
        lay.addLayout(bot_row)

        bm_card = QFrame(); bm_card.setObjectName("card")
        bm_lay = QVBoxLayout(bm_card); bm_lay.setContentsMargins(20,16,20,16); bm_lay.setSpacing(14)
        bm_lay.addWidget(self._lbl("Vücut Metriği Ekle","14px"))

        bm_form = QHBoxLayout(); bm_form.setSpacing(12)
        self.bm_weight = QDoubleSpinBox(); self.bm_weight.setRange(30,300)
        self.bm_weight.setValue(75); self.bm_weight.setSuffix(" kg"); self.bm_weight.setMinimumHeight(42)
        self.bm_fat    = QDoubleSpinBox(); self.bm_fat.setRange(0,60)
        self.bm_fat.setValue(0); self.bm_fat.setSuffix(" %"); self.bm_fat.setMinimumHeight(42)
        self.bm_waist  = QDoubleSpinBox(); self.bm_waist.setRange(0,200)
        self.bm_waist.setValue(0); self.bm_waist.setSuffix(" cm"); self.bm_waist.setMinimumHeight(42)
        for label, widget in [("Kilo","bm_weight"),("Yağ %","bm_fat"),("Bel (cm)","bm_waist")]:
            col = QVBoxLayout()
            col.addWidget(self._small_lbl(label.upper()))
            col.addWidget(getattr(self, widget))
            bm_form.addLayout(col)

        bm_save = QPushButton("Kaydet"); bm_save.setObjectName("primaryBtn")
        bm_save.setMinimumHeight(42); bm_save.setMinimumWidth(100)
        bm_save.setCursor(Qt.CursorShape.PointingHandCursor)
        bm_save.clicked.connect(self._save_body_metric)
        bm_form.addWidget(bm_save)
        bm_lay.addLayout(bm_form)
        lay.addWidget(bm_card)

        self.toast = Toast(self)
        self._load_all()

    def _lbl(self, text, size="13px"):
        l = QLabel(text); l.setStyleSheet(f"font-size: {size}; font-weight: 600; background: transparent;"); return l

    def _small_lbl(self, text):
        l = QLabel(text); l.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent;"); return l

    def _summary_card(self, label: str, color: str) -> QFrame:
        card = QFrame(); card.setObjectName("card"); card.setMinimumHeight(90)
        lay = QVBoxLayout(card); lay.setContentsMargins(16,14,16,14); lay.setSpacing(4)
        top = QHBoxLayout()
        t = QLabel(label.upper()); t.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        top.addWidget(t); top.addStretch()
        val = QLabel("—"); val.setObjectName(f"sum_{label.replace(' ','_')}")
        val.setStyleSheet(f"font-size: 24px; font-weight: 600; color: {color}; background: transparent;")
        lay.addLayout(top); lay.addWidget(val)
        return card

    def _set_val(self, card: QFrame, value: str):
        for l in card.findChildren(QLabel):
            if l.objectName().startswith("sum_"):
                l.setText(value); break

    def _set_period(self, days: int):
        self._days = days
        self._update_period_styles()
        self._load_all()

    def _update_period_styles(self):
        for btn, d in self._period_btns:
            if d == self._days:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {PRIMARY}; color: white;
                        border: none; border-radius: 999px; font-weight: 600;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; color: {TEXT_DIM};
                        border: none; border-radius: 999px;
                    }}
                    QPushButton:hover {{ color: {TEXT}; }}
                """)

    def _load_all(self):
        api.get(f"/analytics/weekly-performance?days={self._days}", self._on_perf, self._on_err)
        api.get("/analytics/personal-records", self._on_prs, self._on_err)
        api.get("/analytics/summary", self._on_summary, self._on_err)

    def _on_perf(self, data):
        if not data or not isinstance(data, list): return
        self.perf_chart.plot(data)
        total_cal = sum(d.get("calories",0) for d in data)
        total_dur = sum(d.get("workout_minutes",0) for d in data)
        active    = sum(1 for d in data if d.get("calories",0) > 0 or d.get("workout_minutes",0) > 0)
        self._set_val(self.sum_cal,      f"{round(total_cal):,} kcal")
        self._set_val(self.sum_duration, f"{total_dur} dk")
        self._set_val(self.sum_streak,   f"{active} gün")

    def _on_prs(self, data):
        if not data or not isinstance(data, list): return
        self.pr_table.setRowCount(len(data))
        for i, pr in enumerate(data):
            self.pr_table.setItem(i, 0, QTableWidgetItem(pr.get("exercise","?")))
            self.pr_table.setItem(i, 1, QTableWidgetItem(f"{pr.get('weight_kg',0)} kg  ×{pr.get('reps',0)}"))
            self.pr_table.setItem(i, 2, QTableWidgetItem(pr.get("date","?")))

    def _on_summary(self, data):
        if not data: return
        w = data.get("weekly",{})
        self._set_val(self.sum_workouts, str(w.get("workout_count",0)))
        t = data.get("today",{})
        prot = t.get("protein", 0)
        carb = t.get("carb",    0)
        fat  = t.get("fat",     0)
        if prot + carb + fat > 0:
            self.donut.update_macros(prot, max(0, carb), max(0, fat))
            self.macro_detail_lbl.setText(f"P:{round(prot)}g  K:{round(carb)}g  Y:{round(fat)}g")

    def _save_body_metric(self):
        payload = {
            "date":         date.today().isoformat(),
            "weight_kg":    self.bm_weight.value(),
            "body_fat_pct": self.bm_fat.value()  or None,
            "waist_cm":     self.bm_waist.value() or None,
        }
        api.post("/workouts/body-metrics", payload,
                 callback=lambda _: self.toast.show_toast("Metrik kaydedildi!", "success"),
                 error_cb=self._on_err)

    def _on_err(self, msg: str):
        self.toast.show_toast(msg, "error")

    def showEvent(self, event):
        super().showEvent(event)
        self._load_all()
