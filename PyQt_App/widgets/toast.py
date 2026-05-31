from PyQt6.QtWidgets import QLabel, QWidget
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor
from theme import PRIMARY, ERROR, SUCCESS


class Toast(QLabel):
    """Ekranın altında kısa süre görünen bildirim etiketi."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._hide_toast)

    def show_toast(self, message: str, kind: str = "error", duration: int = 3000):
        colors = {
            "error":   (ERROR,   "rgba(40,10,10,220)"),
            "success": (SUCCESS, "rgba(10,40,20,220)"),
            "info":    (PRIMARY, "rgba(30,20,30,220)"),
        }
        fg, bg = colors.get(kind, colors["info"])
        self.setStyleSheet(f"""
            QLabel {{
                background: {bg};
                color: {fg};
                border: 1px solid {fg};
                border-radius: 20px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 500;
            }}
        """)
        self.setText(message)
        self.adjustSize()

        # Ekranın altında ortala
        pw = self.parent().width()
        ph = self.parent().height()
        w  = min(self.sizeHint().width() + 40, pw - 60)
        self.setFixedWidth(w)
        self.adjustSize()
        self.move((pw - self.width()) // 2, ph - self.height() - 30)
        self.raise_()
        self.show()

        self._timer.stop()
        self._timer.start(duration)

    def _hide_toast(self):
        self.hide()
