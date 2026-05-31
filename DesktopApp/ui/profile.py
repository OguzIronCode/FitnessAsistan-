from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout


class ProfileWidget(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Profil Oluşturma / Düzenleme — (placeholder)"))
        self.setLayout(layout)
