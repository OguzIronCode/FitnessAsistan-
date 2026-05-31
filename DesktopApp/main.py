"""PyQt PoC — Login window and minimal main window.

Run `py main.py` inside the `DesktopApp` folder after installing requirements.
"""
from __future__ import annotations

import sys
from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QMessageBox,
    QTabWidget,
)

from api import FitTrackAPI


class LoginThread(QtCore.QThread):
    success = QtCore.pyqtSignal(dict)
    error = QtCore.pyqtSignal(str)

    def __init__(self, api: FitTrackAPI, email: str, password: str):
        super().__init__()
        self.api = api
        self.email = email
        self.password = password

    def run(self) -> None:
        try:
            res = self.api.login(self.email, self.password)
            self.success.emit(res)
        except Exception as e:
            self.error.emit(str(e))


class LoginWindow(QWidget):
    def __init__(self, api: FitTrackAPI):
        super().__init__()
        self.api = api
        self.thread: LoginThread | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("FitTrack — Login")
        layout = QVBoxLayout()

        title = QLabel("FitTrack Desktop")
        title.setStyleSheet("font-weight: 700; font-size: 16px; margin-bottom: 8px;")
        layout.addWidget(title)

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        layout.addWidget(self.email)

        self.pw = QLineEdit()
        self.pw.setPlaceholderText("Password")
        self.pw.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.pw)

        self.btn = QPushButton("Login")
        self.btn.clicked.connect(self.attempt_login)
        layout.addWidget(self.btn)

        self.status = QLabel("")
        layout.addWidget(self.status)

        self.setLayout(layout)

    def attempt_login(self) -> None:
        email = self.email.text().strip()
        pw = self.pw.text().strip()
        if not email or not pw:
            QMessageBox.warning(self, "Eksik bilgi", "Lütfen e-posta ve şifre girin.")
            return
        self.btn.setEnabled(False)
        self.status.setText("Giriş yapılıyor...")
        self.thread = LoginThread(self.api, email, pw)
        self.thread.success.connect(self.on_success)
        self.thread.error.connect(self.on_error)
        self.thread.finished.connect(lambda: self.btn.setEnabled(True))
        self.thread.start()

    def on_success(self, data: dict) -> None:
        QMessageBox.information(self, "Başarılı", "Giriş başarılı.")
        self.status.setText("Giriş başarılı")
        self.main = MainWindow(self.api)
        self.main.show()
        self.close()

    def on_error(self, msg: str) -> None:
        QMessageBox.critical(self, "Giriş başarısız", msg)
        self.status.setText("")


class MainWindow(QWidget):
    def __init__(self, api: FitTrackAPI):
        super().__init__()
        self.api = api
        self._init_ui()

    def _init_ui(self) -> None:
        # Import UI widgets lazily to keep startup fast
        from ui import (
            DashboardWidget,
            ProfileWidget,
            WorkoutWidget,
            NutritionWidget,
            AIWidget,
            AnalyticsWidget,
        )

        self.setWindowTitle("FitTrack — Ana Sayfa")
        layout = QVBoxLayout()

        uid = getattr(self.api, "_user_id", None) or "(bilinmiyor)"
        self.lbl = QLabel(f"Girişli kullanıcı: {uid}")
        layout.addWidget(self.lbl)

        tabs = QTabWidget()
        tabs.addTab(DashboardWidget(self.api), "Ana Sayfa")
        tabs.addTab(ProfileWidget(self.api), "Profil")
        tabs.addTab(WorkoutWidget(self.api), "Antrenman")
        tabs.addTab(NutritionWidget(self.api), "Beslenme")
        tabs.addTab(AIWidget(self.api), "AI Asistan")
        tabs.addTab(AnalyticsWidget(self.api), "Analiz")

        layout.addWidget(tabs)

        self.btnLogout = QPushButton("Çıkış")
        self.btnLogout.clicked.connect(self.logout)
        layout.addWidget(self.btnLogout)

        self.setLayout(layout)

    def logout(self) -> None:
        self.api.clear_token()
        QMessageBox.information(self, "Çıkış", "Oturum kapatıldı.")
        self.login = LoginWindow(self.api)
        self.login.show()
        self.close()


def main() -> None:
    app = QApplication(sys.argv)
    api = FitTrackAPI()
    if api._token:
        win = MainWindow(api)
    else:
        win = LoginWindow(api)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
