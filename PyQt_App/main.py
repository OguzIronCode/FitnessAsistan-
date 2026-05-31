import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStackedWidget,
                             QWidget, QHBoxLayout, QVBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

from pathlib import Path
from theme import STYLESHEET, BG_DEEP
from state import state

_LOGO_PATH = str(Path(__file__).parent.parent / "FitnessAsistani_Logo.png")
from widgets.sidebar import SidebarWidget
from pages.login import LoginPage
from pages.profile import ProfilePage
from pages.home import HomePage
from pages.nutrition import NutritionPage
from pages.workout import WorkoutPage
from pages.ai_chat import AIChatPage
from pages.analytics import AnalyticsPage
from pages.settings import SettingsPage


# ─── Ana İçerik Alanı (sidebar + sayfalar) ───────────────────────────────────
class MainApp(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sayfalar
        self.pages = QStackedWidget()
        self.home      = HomePage()
        self.nutrition = NutritionPage()
        self.workout   = WorkoutPage()
        self.ai_chat   = AIChatPage()
        self.analytics = AnalyticsPage()
        self.settings  = SettingsPage()

        # Sıra sidebar.py'daki NAV_ITEMS ile birebir eşleşmeli:
        # 0=home, 1=workout, 2=nutrition, 3=ai_chat, 4=analytics, 5=settings
        for page in [self.home, self.workout, self.nutrition,
                     self.ai_chat, self.analytics, self.settings]:
            self.pages.addWidget(page)

        # Kenar çubuğu
        self.sidebar = SidebarWidget()
        self.sidebar.nav_changed.connect(self._on_nav)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages, 1)

        # Sayfalararası sinyaller ──────────────────────────────────────────────
        # Workout sayfasındaki "program seç" sidebar butonunu workout'a yönlendir
        self.sidebar.new_workout_btn_clicked = lambda: self._on_nav(1)

        # Workout bitince home + analytics yenile
        self.workout.workout_finished.connect(self._on_workout_finished)

        # Beslenme eklendikten sonra home'u haber et (showEvent zaten handle ediyor)
        # Ana sayfa "Bugünkü Antrenmanı Aç" → workout sayfasına git
        self.home.goto_workout.connect(lambda: self.show_page(1))

        # Ana sayfa profil popup → ayarlar / çıkış
        self.home.goto_settings.connect(lambda: self.show_page(5))
        self.home.logout_requested.connect(self._request_logout)  # noqa: forward-ref resolved via setup_logout

        # Settings kaydedince tüm sayfaların hedeflerini tazele
        self.settings.profile_saved.connect(self._on_profile_saved)

    def _on_nav(self, index: int):
        self.pages.setCurrentIndex(index)
        page = self.pages.currentWidget()
        if hasattr(page, "load_data"):
            page.load_data()

    def show_page(self, index: int):
        self._on_nav(index)
        self.sidebar.set_active(index)

    def setup_logout(self, callback):
        self.sidebar.logout_btn.clicked.connect(callback)
        self._logout_callback = callback

    def _request_logout(self):
        if hasattr(self, "_logout_callback"):
            self._logout_callback()

    def _on_workout_finished(self):
        """Antrenman bitince home ve analytics verilerini tazele."""
        self.home.load_data()
        self.analytics._load_all()

    def _on_profile_saved(self):
        """Profil güncellendikten sonra tüm sayfalardaki hedefleri tazele."""
        self.home.load_data()
        self.nutrition._load()
        self.nutrition._on_profile_reload()
        self.analytics._load_all()


# ─── Ana Pencere ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FitnessAsistanı")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 820)
        icon = QIcon(_LOGO_PATH)
        if not icon.isNull():
            self.setWindowIcon(icon)

        # Kök StackedWidget
        self.root = QStackedWidget()
        self.setCentralWidget(self.root)

        # Sayfalar
        self.login_page   = LoginPage()
        self.profile_page = ProfilePage()
        self.main_app     = MainApp()

        self.root.addWidget(self.login_page)   # 0
        self.root.addWidget(self.profile_page) # 1
        self.root.addWidget(self.main_app)     # 2

        # Sinyaller
        self.login_page.login_success.connect(self._on_login_success)
        self.login_page.goto_register.connect(lambda: self.root.setCurrentIndex(1))
        self.profile_page.register_success.connect(self._on_login_success)
        self.profile_page.goto_login.connect(lambda: self.root.setCurrentIndex(0))
        self.main_app.setup_logout(self._on_logout)

        # Başlangıç: giriş sayfası
        self.root.setCurrentIndex(0)

    def _on_login_success(self):
        # Profil var mı? Varsa ana sayfa, yoksa profil oluşturma sayfasına
        from api import api
        def _has_profile(data):
            if data:
                self.root.setCurrentIndex(2)
                self.main_app.show_page(0)
                self.main_app.home.load_data()
            else:
                self._goto_profile_create()
        def _no_profile(_):
            self._goto_profile_create()
        api.get("/user/profile", _has_profile, _no_profile)

    def _goto_profile_create(self):
        """Profil eksik → kayıt sayfasını 'sadece profil doldur' modunda aç."""
        self.profile_page.set_complete_mode(True)
        self.root.setCurrentIndex(1)

    def _on_logout(self):
        state.token   = None
        state.user_id = None
        state.profile = None
        self.profile_page.set_complete_mode(False)
        self.root.setCurrentIndex(0)
        self.login_page.email_input.clear()
        self.login_page.pw_input.clear()


# ─── Giriş Noktası ───────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
