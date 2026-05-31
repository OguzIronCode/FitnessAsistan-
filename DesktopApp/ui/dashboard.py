from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class DashboardWidget(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Ana Sayfa — Dashboard (placeholder)"))
        self.setLayout(layout)
