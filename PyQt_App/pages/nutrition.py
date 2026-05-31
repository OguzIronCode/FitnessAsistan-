from datetime import date
import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QFrame, QPushButton, QLineEdit,
                             QDialog, QComboBox, QSpinBox, QProgressBar,
                             QSizePolicy, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from api import api
from state import state
from theme import (BG, CARD, CARD2, BORDER, PRIMARY, TEXT, TEXT_DIM, TEXT_FAINT, ERROR)
from widgets.toast import Toast
from food_images import find_food_image


class _ImageLoader(QThread):
    """Arka planda görsel URL'yi indir, bytes olarak emit et."""
    loaded = pyqtSignal(bytes)

    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        try:
            r = requests.get(self._url, timeout=8)
            if r.ok and r.content:
                self.loaded.emit(r.content)
        except Exception:
            pass

MEAL_ICONS = {"breakfast": "", "lunch": "", "dinner": "", "snack": ""}
MEAL_NAMES = {"breakfast": "Kahvaltı", "lunch": "Öğle Yemeği",
              "dinner": "Akşam Yemeği", "snack": "Ara Öğün"}


# ── Besin Arama Diyaloğu ──────────────────────────────────────────────────────
class FoodSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Besin Ekle")
        self.setFixedSize(560, 600)
        self.selected_food = None
        self._img_loaders: list[_ImageLoader] = []
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        lay.addWidget(QLabel("Öğün Türü & Besin Ara"))

        top_row = QHBoxLayout()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Kahvaltı", "Öğle Yemeği", "Akşam Yemeği", "Ara Öğün"])
        self.type_combo.setMinimumHeight(40)
        self.type_combo.setFixedWidth(150)
        top_row.addWidget(self.type_combo)

        self.search_inp = QLineEdit()
        self.search_inp.setPlaceholderText("Örn: Tavuk, Yulaf...")
        self.search_inp.setMinimumHeight(40)
        top_row.addWidget(self.search_inp, 1)
        lay.addLayout(top_row)

        self.result_scroll = QScrollArea()
        self.result_scroll.setWidgetResizable(True)
        self.result_content = QWidget()
        self.result_lay = QVBoxLayout(self.result_content)
        self.result_lay.setContentsMargins(0, 0, 0, 0)
        self.result_lay.setSpacing(4)
        self.result_lay.addStretch()
        self.result_scroll.setWidget(self.result_content)
        lay.addWidget(self.result_scroll, 1)

        self.status_lbl = QLabel("Aramak için yazmaya başlayın.")
        self.status_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 12px; background: transparent;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._do_search)
        self.search_inp.textChanged.connect(lambda _: self._search_timer.start(400))

    def _do_search(self):
        q = self.search_inp.text().strip()
        if len(q) < 2:
            return
        self._clear_results()
        self.status_lbl.setText("Aranıyor...")
        api.get(f"/food/search?q={q}&limit=20", self._on_results, self._on_err)

    def _clear_results(self):
        # Çalışan image loader'ları durdur
        for ldr in self._img_loaders:
            ldr.quit()
            ldr.wait()
        self._img_loaders.clear()
        while self.result_lay.count() > 1:
            item = self.result_lay.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _on_results(self, data):
        self._clear_results()
        if not data or not isinstance(data, list) or not data:
            self.status_lbl.setText("Sonuç bulunamadı.")
            return
        self.status_lbl.setText(f"{len(data)} sonuç bulundu.")
        for food in data:
            self.result_lay.insertWidget(self.result_lay.count() - 1,
                                         self._food_row(food))

    def _food_row(self, food: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.02);
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background: rgba(255,255,255,0.05);
                border-color: {PRIMARY};
            }}
            QLabel {{ background: transparent; border: none; border-radius: 0; }}
        """)
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(10, 8, 12, 8)
        row_lay.setSpacing(10)

        # ── Ürün görseli ─────────────────────────────────────────────────
        food_name_for_img = food.get("name_tr") or food.get("name") or ""
        img_frame = QFrame()
        img_frame.setFixedSize(56, 56)
        img_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.04);
                border-radius: 8px;
            }}
        """)
        _fl = QVBoxLayout(img_frame)
        _fl.setContentsMargins(0, 0, 0, 0)
        img_lbl = QLabel("")
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        _fl.addWidget(img_lbl)

        local_path = find_food_image(food_name_for_img)
        if local_path:
            px = QPixmap(local_path)
            if not px.isNull():
                px = px.scaled(56, 56,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
                img_lbl.setPixmap(px)
                img_lbl.setText("")
                img_lbl.setStyleSheet("background: transparent;")
        else:
            image_url = food.get("image_url") or ""
            if image_url:
                loader = _ImageLoader(image_url)
                def _set_pixmap(data: bytes, lbl=img_lbl):
                    px = QPixmap()
                    px.loadFromData(data)
                    if not px.isNull():
                        px = px.scaled(56, 56,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                        lbl.setPixmap(px)
                        lbl.setText("")
                        lbl.setStyleSheet("background: transparent;")
                loader.loaded.connect(_set_pixmap)
                loader.start()
                self._img_loaders.append(loader)

        row_lay.addWidget(img_frame)

        # ── İsim + makrolar ───────────────────────────────────────────────
        name_col = QVBoxLayout()
        name = food.get("name_tr") or food.get("name") or "?"
        n_lbl = QLabel(name)
        n_lbl.setStyleSheet("font-weight: 500; font-size: 13px; background: transparent;")
        n_lbl.setWordWrap(True)
        srv = food.get("serving_size") or "100g"
        p   = food.get("protein", 0) or 0
        c   = food.get("carbohydrate", 0) or 0
        f_  = food.get("fat", 0) or 0
        s_lbl = QLabel(f"{srv}  ·  P:{round(p,1)}g  K:{round(c,1)}g  Y:{round(f_,1)}g")
        s_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        name_col.addWidget(n_lbl)
        name_col.addWidget(s_lbl)
        row_lay.addLayout(name_col, 1)

        # ── Kalori ────────────────────────────────────────────────────────
        cal = round(food.get("calories") or 0)
        cal_col = QVBoxLayout()
        cal_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_lbl = QLabel(f"{cal}")
        c_lbl.setStyleSheet(f"color: {PRIMARY}; font-weight: 700; font-size: 16px; background: transparent;")
        c_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_lbl = QLabel("kcal")
        unit_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 10px; background: transparent;")
        unit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cal_col.addWidget(c_lbl)
        cal_col.addWidget(unit_lbl)
        row_lay.addLayout(cal_col)

        row.mousePressEvent = lambda _ev, f=food: self._select_food(f)
        return row

    def _select_food(self, food: dict):
        self.selected_food = food
        self.accept()

    def _on_err(self, msg: str):
        self.status_lbl.setText(f"Hata: {msg}")

    def get_meal_type(self):
        mapping = {"Kahvaltı": "breakfast", "Öğle Yemeği": "lunch",
                   "Akşam Yemeği": "dinner", "Ara Öğün": "snack"}
        return mapping.get(self.type_combo.currentText(), "breakfast")


# ── Miktar Diyaloğu ───────────────────────────────────────────────────────────
class AmountDialog(QDialog):
    def __init__(self, food: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Porsiyon Belirle")
        self.setFixedSize(340, 220)
        self._build_ui(food)

    def _build_ui(self, food):
        lay = QVBoxLayout(self); lay.setContentsMargins(24, 20, 24, 20); lay.setSpacing(12)
        name = food.get("name_tr") or food.get("name") or "?"
        lay.addWidget(QLabel(f"<b>{name}</b>"))
        srv = QLabel(f"Porsiyon: {food.get('serving_size','100g')}")
        srv.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent;")
        lay.addWidget(srv)
        lay.addWidget(QLabel("MİKTAR (gram/ml)"))
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(1, 2000); self.amount_spin.setValue(100)
        self.amount_spin.setMinimumHeight(44); self.amount_spin.setSuffix(" g")
        lay.addWidget(self.amount_spin)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                QDialogButtonBox.StandardButton.Cancel)
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Ekle")
        btns.button(QDialogButtonBox.StandardButton.Ok).setObjectName("primaryBtn")
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_amount(self): return self.amount_spin.value()


# ── Ana Sayfa ─────────────────────────────────────────────────────────────────
class NutritionPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._targets = {"calories": 2000, "protein": 150, "carb": 200, "fat": 65}
        self._card_loaders: list[_ImageLoader] = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Başlık ────────────────────────────────────────────────────────
        hdr = QFrame(); hdr.setObjectName("header"); hdr.setFixedHeight(64)
        hdr_lay = QHBoxLayout(hdr); hdr_lay.setContentsMargins(20, 0, 20, 0)

        left_info = QVBoxLayout()
        self.date_lbl = QLabel(date.today().strftime("%d %B %Y"))
        self.date_lbl.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        self.remain_lbl = QLabel("Kalan: — kcal")
        self.remain_lbl.setStyleSheet(f"color: {PRIMARY}; font-size: 12px; background: transparent;")
        left_info.addWidget(self.date_lbl)
        left_info.addWidget(self.remain_lbl)
        hdr_lay.addLayout(left_info)
        hdr_lay.addStretch()

        clear_btn = QPushButton("Günü Temizle")
        clear_btn.setObjectName("dangerBtn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_day)
        hdr_lay.addWidget(clear_btn)

        ai_btn = QPushButton("Beslenme Programı Oluştur")
        ai_btn.setObjectName("ghostBtn")
        ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ai_btn.clicked.connect(self._open_meal_plan)
        hdr_lay.addWidget(ai_btn)

        add_btn = QPushButton("Öğün Ekle")
        add_btn.setObjectName("primaryBtn")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_meal)
        hdr_lay.addWidget(add_btn)
        root.addWidget(hdr)

        # ── Öğün listesi ──────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        root.addWidget(self.scroll, 1)

        self.content = QWidget()
        self.meal_lay = QVBoxLayout(self.content)
        self.meal_lay.setContentsMargins(20, 16, 20, 100)
        self.meal_lay.setSpacing(10)
        self.meal_lay.addStretch()
        self.scroll.setWidget(self.content)

        # ── Alt makro özeti ────────────────────────────────────────────────
        footer = QFrame()
        footer.setStyleSheet(f"""
            QFrame {{
                background: rgba(30,30,46,220);
                border: none;
                border-top: 1px solid {BORDER};
            }}
        """)
        footer.setFixedHeight(110)
        ft_lay = QVBoxLayout(footer); ft_lay.setContentsMargins(20, 12, 20, 12); ft_lay.setSpacing(8)

        sum_row = QHBoxLayout()
        sum_row.addWidget(QLabel("Günlük Makro Özeti"))
        sum_row.addStretch()
        self.cal_summary = QLabel("0 / 2000 kcal")
        self.cal_summary.setStyleSheet(f"font-weight: 600; color: {PRIMARY}; background: transparent;")
        sum_row.addWidget(self.cal_summary)
        ft_lay.addLayout(sum_row)

        for key, label, bar_id in [("protein","Protein","proteinBar"),
                                    ("carb","Karbonhidrat","carbBar"),
                                    ("fat","Yağ","fatBar")]:
            row = QHBoxLayout(); row.setSpacing(8)
            row.addWidget(self._small_lbl(label, 60))
            bar = QProgressBar(); bar.setObjectName(bar_id)
            bar.setRange(0, 100); bar.setValue(0); bar.setTextVisible(False)
            bar.setFixedHeight(6)
            setattr(self, f"bar_{key}", bar)
            row.addWidget(bar, 1)
            val_lbl = QLabel("0g"); val_lbl.setFixedWidth(40)
            val_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
            setattr(self, f"val_{key}", val_lbl)
            row.addWidget(val_lbl)
            ft_lay.addLayout(row)
        root.addWidget(footer)

        self.toast = Toast(self)

        # Veri yükle
        self._load()
        api.get("/user/profile", self._on_profile, lambda _: None)

    def _small_lbl(self, text, width=60):
        l = QLabel(text); l.setFixedWidth(width)
        l.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        return l

    def _load(self):
        today = date.today().isoformat()
        api.get(f"/meals?date={today}",     self._on_meals,   self._on_err)
        api.get(f"/meals/summary?date={today}", self._on_summary, self._on_err)

    def _on_profile(self, data):
        if not data: return
        self._targets = {
            "calories": data.get("calorie_target", 2000),
            "protein":  data.get("protein_target", 150),
            "carb":     data.get("carb_target", 200),
            "fat":      data.get("fat_target", 65),
        }

    def _on_meals(self, data):
        for ldr in self._card_loaders:
            ldr.quit()
            ldr.wait()
        self._card_loaders.clear()

        while self.meal_lay.count() > 1:
            item = self.meal_lay.takeAt(0)
            if item and item.widget(): item.widget().deleteLater()

        if not data or not isinstance(data, list) or not data:
            empty = QLabel("Bugün henüz öğün eklenmedi.\nYukarıdaki 'Öğün Ekle' butonuna tıklayın.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 14px; line-height: 2;")
            self.meal_lay.insertWidget(0, empty)
            return

        for i, meal in enumerate(data):
            self.meal_lay.insertWidget(i, self._meal_card(meal))

    def _meal_card(self, meal: dict) -> QFrame:
        card = QFrame(); card.setObjectName("card")
        lay = QHBoxLayout(card); lay.setContentsMargins(12, 12, 16, 12)
        lay.setSpacing(10)

        # ── Ürün görseli veya öğün ikonu ─────────────────────────────────
        meal_food_name = meal.get("food_name_tr") or meal.get("food_name") or ""
        img_frame = QFrame()
        img_frame.setFixedSize(52, 52)
        img_frame.setStyleSheet("QFrame { background: rgba(255,107,107,0.08); border-radius: 12px; }")
        _ml = QVBoxLayout(img_frame)
        _ml.setContentsMargins(0, 0, 0, 0)
        img_lbl = QLabel(MEAL_ICONS.get(meal.get("meal_type", ""), ""))
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        _ml.addWidget(img_lbl)

        local_path = find_food_image(meal_food_name)
        if local_path:
            px = QPixmap(local_path)
            if not px.isNull():
                px = px.scaled(52, 52,
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
                img_lbl.setPixmap(px)
                img_lbl.setText("")
                img_lbl.setStyleSheet("background: transparent;")
        else:
            image_url = meal.get("image_url") or ""
            if image_url:
                ldr = _ImageLoader(image_url)
                def _set(data: bytes, lbl=img_lbl):
                    px = QPixmap()
                    px.loadFromData(data)
                    if not px.isNull():
                        px = px.scaled(52, 52,
                                       Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                        lbl.setPixmap(px)
                        lbl.setText("")
                        lbl.setStyleSheet("background: transparent;")
                ldr.loaded.connect(_set)
                ldr.start()
                self._card_loaders.append(ldr)

        lay.addWidget(img_frame)

        info = QVBoxLayout()
        meal_type_tr = MEAL_NAMES.get(meal.get("meal_type"), meal.get("meal_type", ""))
        type_lbl = QLabel(meal_type_tr.upper())
        type_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        name_lbl = QLabel(meal.get("food_name_tr") or meal.get("food_name") or "?")
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 500; background: transparent;")
        srv_lbl  = QLabel(f"{meal.get('amount_g',0)}g porsiyon")
        srv_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        info.addWidget(type_lbl); info.addWidget(name_lbl); info.addWidget(srv_lbl)
        lay.addLayout(info, 1)

        macro_col = QVBoxLayout(); macro_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        cal_lbl = QLabel(f"{round(meal.get('calories',0))} kcal")
        cal_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; background: transparent;")
        p, c, f_ = round(meal.get("protein",0),1), round(meal.get("carb",0),1), round(meal.get("fat",0),1)
        macro_lbl = QLabel(f"P:{p}g  K:{c}g  Y:{f_}g")
        macro_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        macro_col.addWidget(cal_lbl); macro_col.addWidget(macro_lbl)
        lay.addLayout(macro_col)

        del_btn = QPushButton("Sil")
        del_btn.setObjectName("iconBtn")
        del_btn.setFixedSize(40, 36)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda _, mid=meal.get("id"): self._delete_meal(mid))
        lay.addWidget(del_btn)
        return card

    def _on_summary(self, data):
        if not data: return
        t = self._targets
        cal  = round(data.get("calories", 0))
        prot = round(data.get("protein",  0), 1)
        carb = round(data.get("carb",     0), 1)
        fat_ = round(data.get("fat",      0), 1)

        remain = max(0, t["calories"] - cal)
        self.cal_summary.setText(f"{cal} / {t['calories']} kcal")
        self.remain_lbl.setText(f"Kalan: {remain} kcal")

        for key, val in [("protein", prot), ("carb", carb), ("fat", fat_)]:
            tgt = t.get(key, 1)
            getattr(self, f"bar_{key}").setValue(int(min(100, val / tgt * 100)))
            getattr(self, f"val_{key}").setText(f"{val}g")

    def _add_meal(self):
        dlg = FoodSearchDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted or not dlg.selected_food:
            return
        food = dlg.selected_food
        meal_type = dlg.get_meal_type()

        amt_dlg = AmountDialog(food, self)
        if amt_dlg.exec() != QDialog.DialogCode.Accepted:
            return

        today = date.today().isoformat()
        payload = {
            "date":      today,
            "meal_type": meal_type,
            "amount_g":  amt_dlg.get_amount(),
            # Beslenme verisi inline — food_id FK kısıtı bypass
            "food_name":       food.get("name_tr") or food.get("name", ""),
            "calories_inline": food.get("calories"),
            "protein_inline":  food.get("protein"),
            "carb_inline":     food.get("carbohydrate"),
            "fat_inline":      food.get("fat"),
            "image_url":       food.get("image_url") or "",
        }
        api.post("/meals", payload,
                 callback=lambda _: (self.toast.show_toast("Öğün eklendi!", "success"), self._load()),
                 error_cb=self._on_err)

    def _delete_meal(self, meal_id: str):
        api.delete(f"/meals/{meal_id}",
                   callback=lambda _: (self.toast.show_toast("Silindi", "success"), self._load()),
                   error_cb=self._on_err)

    def _clear_day(self):
        today = date.today().isoformat()
        api.get(f"/meals?date={today}",
                callback=self._do_clear, error_cb=self._on_err)

    def _do_clear(self, meals):
        if not meals: return
        for m in meals:
            api.delete(f"/meals/{m['id']}")
        QTimer.singleShot(500, self._load)
        self.toast.show_toast(f"{len(meals)} öğün silindi", "success")

    def _open_meal_plan(self):
        from pages.meal_plan_dialog import MealPlanDialog
        dlg = MealPlanDialog(self)
        dlg.exec()
        self._load()

    def _on_profile_reload(self):
        """Settings'ten profil güncellenince hedefleri tazele."""
        api.get("/user/profile", self._on_profile, lambda _: None)

    def _on_err(self, msg: str):
        self.toast.show_toast(msg, "error")

    def showEvent(self, event):
        super().showEvent(event)
        self._load()
