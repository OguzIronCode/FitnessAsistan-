from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class AIWidget(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        layout = QVBoxLayout()
        layout.addWidget(QLabel("AI Asistan — Chat (placeholder)"))
        self.setLayout(layout)
