from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class AnalyticsWidget(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Analizler — Analytics (placeholder)"))
        self.setLayout(layout)
