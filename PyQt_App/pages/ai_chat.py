from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QFrame, QPushButton, QTextEdit,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor

from api import api
from state import state
from theme import (BG, CARD, CARD2, BORDER, PRIMARY, AI_CLR,
                   TEXT, TEXT_DIM, TEXT_FAINT)
from widgets.toast import Toast

QUICK_PROMPTS = [
    "Bugünkü kalori durumum nasıl?",
    "Antrenman önerileri verir misin?",
    "Protein alımımı artırmalı mıyım?",
    "Bu haftaki performansım nasıl?",
]


def _bubble(text: str, is_user: bool) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {'rgba(255,107,107,0.12)' if is_user else CARD2};
            border: 1px solid {'rgba(255,107,107,0.3)' if is_user else BORDER};
            border-radius: 14px;
        }}
        QLabel {{ background: transparent; border: none; border-radius: 0; }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(14, 10, 14, 10)
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    lbl.setStyleSheet(f"color: {TEXT}; font-size: 13px; background: transparent; line-height: 1.5;")
    lay.addWidget(lbl)
    return frame


class AIChatPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: list[dict] = []
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        left_panel = QFrame()
        left_panel.setObjectName("card")
        left_panel.setFixedWidth(300)
        left_panel.setStyleSheet(f"""
            QFrame {{
                background: rgba(20,20,30,0.4);
                border: none;
                border-right: 1px solid {BORDER};
                border-radius: 0;
            }}
        """)
        lp_lay = QVBoxLayout(left_panel)
        lp_lay.setContentsMargins(16, 20, 16, 16)
        lp_lay.setSpacing(16)

        ai_title = QLabel("AI Antrenör")
        ai_title.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        lp_lay.addWidget(ai_title)

        self.stat_cal  = self._mini_stat("Kalori", "—")
        self.stat_prot = self._mini_stat("Protein", "—")
        self.stat_wo   = self._mini_stat("Antrenman", "—")
        for s in [self.stat_cal, self.stat_prot, self.stat_wo]:
            lp_lay.addWidget(s)

        div = QFrame(); div.setObjectName("divider"); lp_lay.addWidget(div)

        qp_lbl = QLabel("HIZLI SORULAR")
        qp_lbl.setStyleSheet(f"color: {TEXT_FAINT}; font-size: 11px; font-weight: 600; letter-spacing: 1px; background: transparent;")
        lp_lay.addWidget(qp_lbl)

        for text in QUICK_PROMPTS:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,107,107,0.06);
                    border: 1px solid rgba(255,107,107,0.2);
                    border-radius: 10px;
                    color: {TEXT};
                    padding: 10px 12px;
                    text-align: left;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: rgba(255,107,107,0.14);
                    border-color: rgba(255,107,107,0.35);
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, t=text: self._send_message(t))
            lp_lay.addWidget(btn)

        lp_lay.addStretch()
        root.addWidget(left_panel)

        right_panel = QWidget()
        rp_lay = QVBoxLayout(right_panel)
        rp_lay.setContentsMargins(0, 0, 0, 0)
        rp_lay.setSpacing(0)

        chat_header = QFrame()
        chat_header.setFixedHeight(64)
        chat_header.setObjectName("header")
        ch_lay = QHBoxLayout(chat_header)
        ch_lay.setContentsMargins(20, 0, 20, 0)

        ai_avatar = QLabel("AI")
        ai_avatar.setFixedSize(40, 40)
        ai_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_avatar.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {AI_CLR}, stop:1 {PRIMARY});
            border-radius: 20px; font-size: 13px; font-weight: 600; color: white;
        """)
        ch_lay.addWidget(ai_avatar)
        ch_lay.addSpacing(12)

        info_col = QVBoxLayout()
        ai_name = QLabel("FitnessAsistanı")
        ai_name.setStyleSheet("font-weight: 600; font-size: 14px; background: transparent;")
        ai_online = QLabel("● Çevrimiçi")
        ai_online.setStyleSheet(f"color: {state.profile and '#4ade80' or TEXT_FAINT}; font-size: 11px; background: transparent;")
        info_col.addWidget(ai_name); info_col.addWidget(ai_online)
        ch_lay.addLayout(info_col)
        ch_lay.addStretch()

        clear_btn = QPushButton("Temizle")
        clear_btn.setObjectName("ghostBtn")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_chat)
        ch_lay.addWidget(clear_btn)
        rp_lay.addWidget(chat_header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rp_lay.addWidget(self.scroll, 1)

        self.msg_container = QWidget()
        self.msg_container.setStyleSheet(f"background: {BG};")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(20, 16, 20, 16)
        self.msg_layout.setSpacing(12)
        self.msg_layout.addStretch()
        self.scroll.setWidget(self.msg_container)

        self._add_ai_bubble("Merhaba! Ben FitnessAsistanı yapay zeka asistanıyım. Antrenman, beslenme veya hedefleriniz hakkında soru sorabilirsiniz.")

        input_frame = QFrame()
        input_frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(30,30,46,220);
                border-top: 1px solid {BORDER};
            }}
        """)
        inp_lay = QHBoxLayout(input_frame)
        inp_lay.setContentsMargins(16, 12, 16, 12)
        inp_lay.setSpacing(10)

        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Mesajınızı yazın... (Enter = Gönder, Shift+Enter = Yeni satır)")
        self.msg_input.setMaximumHeight(80)
        self.msg_input.setMinimumHeight(44)
        inp_lay.addWidget(self.msg_input, 1)

        self.send_btn = QPushButton("Gönder")
        self.send_btn.setObjectName("primaryBtn")
        self.send_btn.setFixedSize(100, 44)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.clicked.connect(self._on_send)
        inp_lay.addWidget(self.send_btn)
        rp_lay.addWidget(input_frame)

        root.addWidget(right_panel, 1)
        self.toast = Toast(self)

        self._load_stats()

    def _mini_stat(self, label: str, value: str) -> QFrame:
        f = QFrame()
        f.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.025);
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            QLabel {{ background: transparent; border: none; border-radius: 0; }}
        """)
        l = QHBoxLayout(f); l.setContentsMargins(10, 8, 10, 8)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 12px; background: transparent; border: none;")
        val = QLabel(value)
        val.setObjectName(f"stat_{label}")
        val.setStyleSheet(f"color: {TEXT}; font-weight: 600; font-size: 14px; background: transparent; border: none;")
        l.addWidget(lbl); l.addStretch(); l.addWidget(val)
        return f

    def _set_stat(self, label: str, value: str):
        w = self.findChild(QLabel, f"stat_{label}")
        if w: w.setText(value)

    def _load_stats(self):
        from datetime import date
        today = date.today().isoformat()
        api.get("/analytics/summary", self._on_stats, lambda _: None)

    def _on_stats(self, data):
        if not data: return
        t = data.get("today", {})
        w = data.get("weekly", {})
        self._set_stat("Kalori",    f"{round(t.get('calories', 0))} kcal")
        self._set_stat("Protein",   f"{round(t.get('protein', 0))}g")
        self._set_stat("Antrenman", f"{w.get('workout_count', 0)} antrenman")

    def _add_ai_bubble(self, text: str):
        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        avatar = QLabel("AI")
        avatar.setFixedSize(30, 30)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: {AI_CLR}; border-radius: 15px; font-size: 11px;
            font-weight: 600; color: white;
        """)
        row.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(_bubble(text, False), 1)
        row.addStretch()

        container = QWidget()
        container.setLayout(row)
        self.msg_layout.insertWidget(self.msg_layout.count() - 1, container)
        self._scroll_bottom()

    def _add_user_bubble(self, text: str):
        row = QHBoxLayout(); row.setContentsMargins(0, 0, 0, 0)
        row.addStretch()
        row.addWidget(_bubble(text, True), 0)

        container = QWidget()
        container.setLayout(row)
        self.msg_layout.insertWidget(self.msg_layout.count() - 1, container)
        self._scroll_bottom()

    def _scroll_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))

    def _on_send(self):
        text = self.msg_input.toPlainText().strip()
        if text:
            self._send_message(text)

    def _send_message(self, text: str):
        self.msg_input.clear()
        self._add_user_bubble(text)
        self.send_btn.setText("...")
        self.send_btn.setEnabled(False)

        self._history.append({"role": "user", "content": text})
        api.post("/ai/chat",
                 {"message": text, "history": self._history[-10:]},
                 callback=self._on_reply, error_cb=self._on_err)

    def _on_reply(self, data):
        self.send_btn.setText("Gönder")
        self.send_btn.setEnabled(True)
        if not data: return
        reply = data.get("reply", "Bir yanıt üretilemedi.")
        self._history.append({"role": "assistant", "content": reply})
        self._add_ai_bubble(reply)

    def _on_err(self, msg: str):
        self.send_btn.setText("Gönder")
        self.send_btn.setEnabled(True)
        self._add_ai_bubble(f"Hata: {msg}")

    def _clear_chat(self):
        self._history.clear()
        while self.msg_layout.count() > 1:
            item = self.msg_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._add_ai_bubble("Sohbet temizlendi. Nasıl yardımcı olabilirim?")

    def load_data(self):
        self._load_stats()

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt as _Qt
        if (event.key() == _Qt.Key.Key_Return
                and not event.modifiers() & _Qt.KeyboardModifier.ShiftModifier
                and self.msg_input.hasFocus()):
            self._on_send()
        else:
            super().keyPressEvent(event)
