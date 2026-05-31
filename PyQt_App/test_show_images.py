"""
Küçük PyQt testi: assets/exercises içinden bazı egzersiz görsellerini gösterir.
Çalıştırmak için: `py -3 PyQt_App/test_show_images.py`
"""
import sys
import re
from pathlib import Path

# Ensure local PyQt_App package imports resolve
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QScrollArea
    from PyQt6.QtGui import QPixmap
    from PyQt6.QtCore import Qt
except Exception as e:
    print("PyQt6 import error:", e)
    sys.exit(1)

from exercise_images import find_image, all_images


def make_image_widget(name: str, path: str):
    w = QWidget()
    lay = QVBoxLayout(w)
    title = QLabel(name)
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(title)

    img_lbl = QLabel()
    img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if path:
        pix = QPixmap(path)
        if not pix.isNull():
            pix = pix.scaledToWidth(480, Qt.TransformationMode.SmoothTransformation)
            img_lbl.setPixmap(pix)
        else:
            img_lbl.setText("(görsel yüklenemedi)")
    else:
        img_lbl.setText("(görsel bulunamadı)")
    lay.addWidget(img_lbl)
    return w


def main():
    app = QApplication(sys.argv)
    win = QWidget()
    win.setWindowTitle("Egzersiz Görselleri - Hızlı Test")
    main_lay = QVBoxLayout(win)

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    content = QWidget()
    content_lay = QVBoxLayout(content)
    content_lay.setSpacing(12)

    imgs = all_images()
    if not imgs:
        content_lay.addWidget(QLabel("assets/exercises dizini boş veya bulunamadı."))
    else:
        # İlk 12 görseli göster
        for k, p in list(imgs.items())[:12]:
            # derive display name from filename stem (remove _altN)
            stem = Path(p).stem
            disp = re.sub(r"_alt\d+$", "", stem)
            widget = make_image_widget(disp, p)
            content_lay.addWidget(widget)

    content.setLayout(content_lay)
    scroll.setWidget(content)
    main_lay.addWidget(scroll)

    win.resize(760, 900)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
