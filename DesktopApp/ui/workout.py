from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class WorkoutWidget(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Antrenmanlar — Workout (placeholder)"))
        self.setLayout(layout)
