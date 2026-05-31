from datetime import date
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QWidget,
                             QComboBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer
from api import api
from theme import PRIMARY, BORDER, CARD, TEXT_DIM, TEXT_FAINT

MEAL_NAMES = {"breakfast": "Kahvaltı", "lunch": "Öğle", "dinner": "Akşam", "snack": "Ara Öğün"}

_GOAL_MAP  = {"Tüm Hedefler": None, "Yağ Yakma": "cut",
              "Kas Yapma": "bulk",  "Form Koruma": "maintain"}
_DIET_MAP  = {"Karma": "balanced",  "Yüksek Protein": "high_protein",
              "Az Karbonhidrat": "low_carb", "Vejetaryen": "vegetarian", "Vegan": "vegan"}
_MEALS_MAP = {"3 Öğün": 3, "4 Öğün": 4, "5 Öğün": 5}


class MealPlanDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Beslenme Programı Oluştur")
        self.setMinimumSize(640, 520)
        self.setModal(True)
        self._plan = None
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        title = QLabel("Beslenme Programı Oluştur")
        title.setStyleSheet("font-size: 18px; font-weight: 600; background: transparent;")
        lay.addWidget(title)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.goal_combo = QComboBox()
        self.goal_combo.addItems(list(_GOAL_MAP.keys()))
        self.goal_combo.setMinimumHeight(38)

        self.diet_combo = QComboBox()
        self.diet_combo.addItems(list(_DIET_MAP.keys()))
        self.diet_combo.setMinimumHeight(38)

        self.meals_combo = QComboBox()
        self.meals_combo.addItems(list(_MEALS_MAP.keys()))
        self.meals_combo.setMinimumHeight(38)

        for c in [self.goal_combo, self.diet_combo, self.meals_combo]:
            filter_row.addWidget(c)

        self.gen_btn = QPushButton("Oluştur")
        self.gen_btn.setObjectName("primaryBtn")
        self.gen_btn.setMinimumHeight(38)
        self.gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gen_btn.clicked.connect(self._generate)
        filter_row.addWidget(self.gen_btn)
        lay.addLayout(filter_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.plan_content = QWidget()
        self.plan_lay = QVBoxLayout(self.plan_content)
        self.plan_lay.setContentsMargins(0, 0, 0, 0)
        self.plan_lay.setSpacing(10)
        self.plan_lay.addStretch()
        self.scroll.setWidget(self.plan_content)
        lay.addWidget(self.scroll, 1)

        self.footer = QWidget()
        ft_lay = QHBoxLayout(self.footer)
        ft_lay.setContentsMargins(0, 0, 0, 0)
        close_btn = QPushButton("Kapat")
        close_btn.setObjectName("ghostBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        self.apply_btn = QPushButton("Tümünü Bugüne Ekle")
        self.apply_btn.setObjectName("primaryBtn")
        self.apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_btn.clicked.connect(self._apply_plan)
        self.apply_btn.setEnabled(False)
        ft_lay.addWidget(close_btn)
        ft_lay.addStretch()
        ft_lay.addWidget(self.apply_btn)
        lay.addWidget(self.footer)

        self._show_hint("Filtre seçip \"Oluştur\"a tıklayın.")

    def _clear_plan_area(self):
        while self.plan_lay.count() > 1:
            item = self.plan_lay.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _show_hint(self, text: str):
        self._clear_plan_area()
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 14px; padding: 40px;")
        self.plan_lay.insertWidget(0, lbl)

    def _generate(self):
        self.gen_btn.setEnabled(False)
        self.gen_btn.setText("Oluşturuluyor...")
        self.apply_btn.setEnabled(False)
        self._show_hint("Beslenme planın hazırlanıyor...")

        goal_key = self.goal_combo.currentText()
        diet_key = self.diet_combo.currentText()
        meals    = _MEALS_MAP[self.meals_combo.currentText()]

        params: dict = {"meals_per_day": meals, "diet": _DIET_MAP[diet_key]}
        goal_val = _GOAL_MAP[goal_key]
        if goal_val:
            params["goal"] = goal_val

        api.post("/ai/generate-meal-plan", {}, self._on_plan, self._on_err, params=params)

    def _on_plan(self, data):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("Oluştur")

        if not data or not data.get("meals"):
            self._show_hint("Sonuç bulunamadı. Farklı filtre deneyin.")
            return

        self._plan = data
        self._clear_plan_area()

        summary = QHBoxLayout()
        for label, val in [
            (f"{data.get('total_calories', 0)} kcal", PRIMARY),
            (f"{data.get('total_protein', 0)}g protein", "#a78bfa"),
            (f"{len(data.get('meals', []))} öğün", "#60a5fa"),
        ]:
            chip = QLabel(label)
            chip.setStyleSheet(f"""
                background: rgba(255,255,255,0.06);
                color: {val};
                border-radius: 10px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 600;
            """)
            summary.addWidget(chip)
        summary.addStretch()
        summary_w = QWidget()
        summary_w.setLayout(summary)
        self.plan_lay.insertWidget(0, summary_w)

        for i, meal in enumerate(data.get("meals", []), 1):
            self.plan_lay.insertWidget(i, self._meal_card(meal))

        self.apply_btn.setEnabled(True)

    def _meal_card(self, meal: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)

        top = QHBoxLayout()
        meal_type = meal.get("type", "")
        name_lbl = QLabel(MEAL_NAMES.get(meal_type, meal.get("name_tr") or meal_type))
        name_lbl.setStyleSheet("font-weight: 600; font-size: 14px; background: transparent;")
        time_lbl = QLabel(meal.get("time", ""))
        time_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        top.addWidget(name_lbl)
        top.addSpacing(8)
        top.addWidget(time_lbl)
        top.addStretch()
        cal_chip = QLabel(f"{meal.get('total_calories', 0)} kcal")
        cal_chip.setStyleSheet(f"""
            background: rgba(255,107,107,0.10); color: {PRIMARY};
            border-radius: 8px; padding: 3px 10px;
            font-size: 12px; font-weight: 600;
        """)
        top.addWidget(cal_chip)
        lay.addLayout(top)

        for item in meal.get("items", []):
            row = QHBoxLayout()
            n = QLabel(f"• {item.get('food', '?')}")
            n.setStyleSheet("font-size: 12px; background: transparent;")
            a = QLabel(item.get("amount", ""))
            a.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
            c = QLabel(f"{round(item.get('calories', 0))} kcal")
            c.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
            row.addWidget(n)
            row.addStretch()
            row.addWidget(a)
            row.addSpacing(12)
            row.addWidget(c)
            lay.addLayout(row)

        mp = round(meal.get("total_protein", 0), 1)
        mk = round(meal.get("total_carb", 0), 1)
        my = round(meal.get("total_fat", 0), 1)
        macro_lbl = QLabel(f"P: {mp}g  ·  K: {mk}g  ·  Y: {my}g")
        macro_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 11px; padding-top: 2px; background: transparent;")
        lay.addWidget(macro_lbl)

        return card

    def _apply_plan(self):
        if not self._plan:
            return
        today = date.today().isoformat()
        for meal in self._plan.get("meals", []):
            mtype = meal.get("type", "breakfast")
            if mtype not in ("breakfast", "lunch", "dinner", "snack"):
                mtype = "snack"
            for item in meal.get("items", []):
                payload = {
                    "date":            today,
                    "meal_type":       mtype,
                    "amount_g":        item.get("amount_g", 100),
                    "food_name":       item.get("food", ""),
                    "calories_inline": item.get("calories", 0),
                    "protein_inline":  item.get("protein", 0),
                    "carb_inline":     item.get("carb", 0),
                    "fat_inline":      item.get("fat", 0),
                    "image_url":       item.get("image_url", ""),
                }
                fid = item.get("food_id")
                if isinstance(fid, int):
                    payload["food_id"] = fid
                api.post("/meals", payload,
                         callback=lambda _: None, error_cb=lambda _: None)
        QTimer.singleShot(300, self.accept)

    def _on_err(self, msg: str):
        self.gen_btn.setEnabled(True)
        self.gen_btn.setText("Oluştur")
        self._show_hint(f"Hata: {msg}")
