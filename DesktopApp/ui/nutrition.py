from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class NutritionWidget(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Beslenme — Nutrition (placeholder)"))
        self.setLayout(layout)
