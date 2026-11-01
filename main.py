import sys
from pathlib import Path

from cores import db
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QIcon, QColor, QDrag, QPixmap, QPainter
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QMimeData

db.init_db()

if getattr(sys, "frozen", False):
    base_dir = Path(sys._MEIPASS)
else:
    base_dir = Path(__file__).resolve().parent

file_ico = base_dir / "ui" / "images" / "icon.ico"

bg_main = "#0B1220"
bg_panel = "#101A2E"
bg_column = "#16233D"
bg_card = "#1E2E4D"
bg_card_hover = "#263A5E"
bg_input = "#1A2842"
accent = "#4FA8FF"
accent_light = "#9CCBFF"
text_main = "#E6EFFA"
text_dim = "#8FA3BF"
danger = "#FF6B8A"

font_name = "SansSerif"


def app_style():
    return f"""
        * {{
            font-family: '{font_name}';
            font-size: 12px;
            font-weight: bold;
            color: {text_main};
        }}
        QToolTip {{
            background-color: {bg_panel};
            color: {text_main};
            border: none;
            border-radius: 4px;
            padding: 4px 6px;
            font-family: '{font_name}';
            font-size: 11px;
            font-weight: bold;
        }}
    """


class GlowButton(QPushButton):
    def __init__(self, text, parent=None, color=accent):
        super().__init__(text, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._color = color
        self._glow = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"glow")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._apply_style()

    def _apply_style(self):
        alpha = int(30 + self._glow * 90)
        border_alpha = int(110 + self._glow * 145)
        c = QColor(self._color)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({c.red()}, {c.green()}, {c.blue()}, {alpha});
                border: 1px solid rgba({c.red()}, {c.green()}, {c.blue()}, {border_alpha});
                border-radius: 6px;
                color: {text_main};
                font-family: '{font_name}';
                font-size: 11px;
                font-weight: bold;
                padding: 4px 12px;
            }}
        """)

    def get_glow(self):
        return self._glow

    def set_glow(self, value):
        self._glow = value
        self._apply_style()

    glow = pyqtProperty(float, get_glow, set_glow)

    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)


class IconButton(QPushButton):
    def __init__(self, text, parent=None, color=text_dim, hover_color=accent_light):
        super().__init__(text, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color = QColor(color)
        self._hover = QColor(hover_color)
        self._glow = 0.0
        self._anim = QPropertyAnimation(self, b"glow")
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._apply_style()

    def _apply_style(self):
        r = int(self._color.red() + (self._hover.red() - self._color.red()) * self._glow)
        g = int(self._color.green() + (self._hover.green() - self._color.green()) * self._glow)
        b = int(self._color.blue() + (self._hover.blue() - self._color.blue()) * self._glow)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: rgb({r}, {g}, {b});
                font-family: '{font_name}';
                font-size: 14px;
                font-weight: bold;
                padding: 0px;
            }}
        """)

    def get_glow(self):
        return self._glow

    def set_glow(self, value):
        self._glow = value
        self._apply_style()

    glow = pyqtProperty(float, get_glow, set_glow)

    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._glow)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)


class CloseIconButton(IconButton):
    def __init__(self, text="×", parent=None):
        super().__init__(text, parent, color=text_dim, hover_color=danger)


class TagChip(QLabel):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        c = QColor(color)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: rgba({c.red()}, {c.green()}, {c.blue()}, 60);
                border: none;
                border-radius: 3px;
                color: {text_main};
                font-family: '{font_name}';
                font-size: 10px;
                font-weight: bold;
                padding: 1px 5px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(16)


class DraggableCard(QFrame):
    def __init__(self, card_id, text, tags, col_id, parent=None):
        super().__init__(parent)
        self.card_id = card_id
        self.col_id = col_id
        self.text = text
        self.tags = tags
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_card};
                border: none;
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: {bg_card_hover};
            }}
        """)
        self._drag_start = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 6, 6)
        lay.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(3)

        if tags:
            for t in tags:
                top_row.addWidget(TagChip(t["name"], t["color"]))
        top_row.addStretch()

        self.tags_btn = IconButton("т", self, color=text_dim, hover_color=accent_light)
        self.tags_btn.setFixedSize(16, 16)
        self.tags_btn.setToolTip("Изменить")
        top_row.addWidget(self.tags_btn)

        self.del_btn = CloseIconButton("×", self)
        self.del_btn.setFixedSize(16, 16)
        self.del_btn.setToolTip("Удалить карточку")
        top_row.addWidget(self.del_btn)

        lay.addLayout(top_row)

        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            color: {text_main};
            font-family: '{font_name}';
            font-size: 12px;
            font-weight: bold;
        """)
        lay.addWidget(self.label)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_start is None:
            return
        if (event.position().toPoint() - self._drag_start).manhattanLength() < 20:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"card:{self.card_id}:{self.col_id}")
        drag.setMimeData(mime)

        pix = QPixmap(self.size())
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setOpacity(0.85)
        self.render(painter)
        painter.end()
        drag.setPixmap(pix)
        drag.setHotSpot(event.position().toPoint())

        drag.exec(Qt.DropAction.MoveAction)
        self._drag_start = None


class CardContainer(QWidget):
    def __init__(self, col_id, parent=None):
        super().__init__(parent)
        self.col_id = col_id
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        self.layout.addStretch()

    def _accepts(self, event):
        if not event.mimeData().hasText():
            return False
        text = event.mimeData().text()
        if not text.startswith("card:"):
            return False
        _, _, src_col = text.split(":")
        return int(src_col) == self.col_id

    def dragEnterEvent(self, event):
        if self._accepts(event):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if self._accepts(event):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not self._accepts(event):
            return
        _, card_id, _ = event.mimeData().text().split(":")
        card_id = int(card_id)

        card = self._find_card(card_id)
        if card is None:
            return

        pos = event.position().toPoint()
        target_index = self._index_at(pos, card)

        self.layout.removeWidget(card)
        self.layout.insertWidget(target_index, card)
        self._save_order()
        event.acceptProposedAction()

    def _index_at(self, pos, moving_card):
        idx = 0
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if w is None or w is moving_card or not isinstance(w, DraggableCard):
                continue
            if pos.y() < w.geometry().center().y():
                return idx
            idx += 1
        return idx

    def _find_card(self, card_id):
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, DraggableCard) and w.card_id == card_id:
                return w
        return None

    def _save_order(self):
        order = 0
        for i in range(self.layout.count()):
            w = self.layout.itemAt(i).widget()
            if isinstance(w, DraggableCard):
                db.update_card(w.card_id, position=order)
                order += 1


class ColumnWidget(QFrame):
    def __init__(self, col_id, title, parent=None):
        super().__init__(parent)
        self.col_id = col_id
        self.title = title
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFixedWidth(260)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_column};
                border: none;
                border-radius: 8px;
            }}
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(4)

        self.header = QLabel(title)
        self.header.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            color: {text_main};
            font-family: '{font_name}';
            font-size: 13px;
            font-weight: bold;
        """)
        header.addWidget(self.header)
        header.addStretch()

        self.add_btn = IconButton("+", self, color=accent_light, hover_color=accent)
        self.add_btn.setFixedSize(20, 20)
        self.add_btn.setToolTip("Добавить карточку")
        header.addWidget(self.add_btn)

        self.del_col_btn = CloseIconButton("×", self)
        self.del_col_btn.setFixedSize(20, 20)
        self.del_col_btn.setToolTip("Удалить колонку")
        header.addWidget(self.del_col_btn)

        outer.addLayout(header)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setWidgetResizable(True)
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.cards_scroll.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(79, 168, 255, 120);
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {accent};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
                background: transparent;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
        """)

        self.cards_container = CardContainer(col_id)
        self.cards_scroll.setWidget(self.cards_container)
        outer.addWidget(self.cards_scroll, stretch=1)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Task Nest")
        self.setWindowIcon(QIcon(str(file_ico)))
        self.setFixedSize(1000, 560)
        self.setStyleSheet(f"background-color: {bg_main};")

        self.rendered_columns = {}
        self._pending_card_col_id = None
        self._pending_card_tags = set()
        self._edit_card_id = None
        self._pending_delete_col_id = None

        self._build_ui()
        self._build_create_column_dialog()
        self._build_delete_column_dialog()
        self._build_card_dialog()
        self._build_tags_dialog()

        self.sync_columns()

        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.sync_columns)
        self.timer.start()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        top = QFrame(self)
        top.setFrameShape(QFrame.Shape.NoFrame)
        top.setStyleSheet("background-color: transparent; border: none;")
        top.setFixedHeight(44)

        panel = QHBoxLayout(top)
        panel.setContentsMargins(0, 6, 0, 6)
        panel.setSpacing(8)

        title = QLabel("Task Nest", top)
        title.setStyleSheet(f"""
            background-color: transparent;
            border: none;
            color: {text_main};
            font-family: '{font_name}';
            font-size: 16px;
            font-weight: bold;
        """)
        panel.addWidget(title)
        panel.addStretch()

        self.tags_btn = GlowButton("Теги", top)
        self.tags_btn.setFixedSize(80, 28)
        self.tags_btn.clicked.connect(self.open_tags)
        panel.addWidget(self.tags_btn)

        self.create_column_btn = GlowButton("Колонка", top)
        self.create_column_btn.setFixedSize(120, 28)
        self.create_column_btn.clicked.connect(self.open_create_column)
        panel.addWidget(self.create_column_btn)

        main_layout.addWidget(top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:horizontal {{
                background: transparent;
                height: 8px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(79, 168, 255, 120);
                border-radius: 4px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {accent};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
                background: transparent;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: transparent;
            }}
        """)

        self.content = QWidget()
        self.content.setStyleSheet("background-color: transparent;")
        self.content_layout = QHBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.content_layout.addStretch()

        self.scroll.setWidget(self.content)
        main_layout.addWidget(self.scroll, stretch=1)

    def _make_popup(self, w, h):
        frame = QFrame(self)
        frame.setFrameShape(QFrame.Shape.NoFrame)
        frame.setFixedSize(w, h)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_panel};
                border: none;
                border-radius: 8px;
            }}
        """)
        frame.hide()
        return frame

    def _popup_title(self, frame, text, width):
        lbl = QLabel(text, frame)
        lbl.setFixedSize(width, 24)
        lbl.move(16, 12)
        lbl.setStyleSheet(f"""
            background: transparent;
            border: none;
            color: {text_main};
            font-family: '{font_name}';
            font-size: 13px;
            font-weight: bold;
        """)
        return lbl

    def _popup_close(self, frame, x):
        btn = CloseIconButton("×", frame)
        btn.setFixedSize(18, 18)
        btn.move(x, 15)
        return btn

    def _style_input(self, line_edit):
        line_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg_input};
                border: none;
                border-radius: 4px;
                color: {text_main};
                font-family: '{font_name}';
                font-size: 12px;
                font-weight: bold;
                padding-left: 8px;
            }}
            QLineEdit:focus {{
                background-color: {bg_column};
            }}
        """)

    def _hide_all_popups(self):
        self.column_frame.hide()
        self.delete_column_frame.hide()
        self.card_frame.hide()
        self.tags_frame.hide()

    def _center_popup(self, frame):
        frame.move(
            (self.width() - frame.width()) // 2,
            (self.height() - frame.height()) // 2
        )

    def _build_create_column_dialog(self):
        self.column_frame = self._make_popup(240, 130)
        self._popup_title(self.column_frame, "Новая колонка", 180)
        self.column_frame_close = self._popup_close(self.column_frame, 212)
        self.column_frame_close.clicked.connect(self.close_create_column)

        self.column_frame_name = QLineEdit(self.column_frame)
        self._style_input(self.column_frame_name)
        self.column_frame_name.setPlaceholderText("Название")
        self.column_frame_name.setFixedSize(200, 32)
        self.column_frame_name.move(20, 44)
        self.column_frame_name.returnPressed.connect(self._create_column_from_input)

        self.column_frame_end = GlowButton("Создать", self.column_frame)
        self.column_frame_end.setFixedSize(200, 28)
        self.column_frame_end.move(20, 88)
        self.column_frame_end.clicked.connect(self._create_column_from_input)

    def open_create_column(self):
        self._hide_all_popups()
        self._center_popup(self.column_frame)
        self.column_frame.show()
        self.column_frame.raise_()
        self.column_frame_name.clear()
        self.column_frame_name.setFocus()

    def close_create_column(self):
        self.column_frame.hide()
        self.column_frame_name.clear()

    def _create_column_from_input(self):
        name = self.column_frame_name.text().strip()
        if not name:
            return
        col_id = db.create_column(name)
        self.close_create_column()
        self.add_column(name, col_id)

    def _build_delete_column_dialog(self):
        self.delete_column_frame = self._make_popup(260, 130)
        self._popup_title(self.delete_column_frame, "Удалить колонку?", 200)
        self.delete_column_frame_close = self._popup_close(self.delete_column_frame, 232)
        self.delete_column_frame_close.clicked.connect(self.close_delete_column)

        self.delete_column_label = QLabel("", self.delete_column_frame)
        self.delete_column_label.setFixedSize(220, 32)
        self.delete_column_label.move(20, 44)
        self.delete_column_label.setStyleSheet(f"""
            background: transparent;
            border: none;
            color: {text_dim};
            font-family: '{font_name}';
            font-size: 11px;
            font-weight: bold;
        """)

        self.delete_column_yes = GlowButton("Удалить", self.delete_column_frame, color=danger)
        self.delete_column_yes.setFixedSize(100, 28)
        self.delete_column_yes.move(20, 88)
        self.delete_column_yes.clicked.connect(self._confirm_delete_column)

        self.delete_column_no = GlowButton("Отмена", self.delete_column_frame)
        self.delete_column_no.setFixedSize(100, 28)
        self.delete_column_no.move(140, 88)
        self.delete_column_no.clicked.connect(self.close_delete_column)

    def open_delete_column(self, col_id):
        self._hide_all_popups()
        self._pending_delete_col_id = col_id
        col = self.rendered_columns.get(col_id)
        title = col.title if col else ""
        self.delete_column_label.setText(f"«{title}» и все её карточки будут удалены")
        self._center_popup(self.delete_column_frame)
        self.delete_column_frame.show()
        self.delete_column_frame.raise_()

    def close_delete_column(self):
        self.delete_column_frame.hide()
        self._pending_delete_col_id = None

    def _confirm_delete_column(self):
        col_id = self._pending_delete_col_id
        if col_id is None:
            return
        db.delete_column(col_id)
        widget = self.rendered_columns.pop(col_id, None)
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        self.close_delete_column()

    def _build_card_dialog(self):
        self.card_frame = self._make_popup(300, 260)
        self._popup_title(self.card_frame, "Карточка", 220)
        self.card_frame_close = self._popup_close(self.card_frame, 272)
        self.card_frame_close.clicked.connect(self.close_card_dialog)

        self.card_frame_text = QLineEdit(self.card_frame)
        self._style_input(self.card_frame_text)
        self.card_frame_text.setPlaceholderText("Текст карточки")
        self.card_frame_text.setFixedSize(260, 32)
        self.card_frame_text.move(20, 44)
        self.card_frame_text.returnPressed.connect(self._save_card_from_input)

        self.card_tags_container = QWidget(self.card_frame)
        self.card_tags_container.setStyleSheet("background: transparent;")
        self.card_tags_container.setGeometry(20, 86, 260, 120)
        self.card_tags_layout = QVBoxLayout(self.card_tags_container)
        self.card_tags_layout.setContentsMargins(0, 0, 0, 0)
        self.card_tags_layout.setSpacing(4)

        self.card_frame_end = GlowButton("Сохранить", self.card_frame)
        self.card_frame_end.setFixedSize(260, 28)
        self.card_frame_end.move(20, 216)
        self.card_frame_end.clicked.connect(self._save_card_from_input)

    def open_create_card(self, col_id, card_id=None):
        self._hide_all_popups()
        self._pending_card_col_id = col_id
        self._edit_card_id = card_id

        if card_id is None:
            self._pending_card_tags = set()
            self.card_frame_text.clear()
        else:
            self._pending_card_tags = {t["id"] for t in db.get_card_tags(card_id)}
            self.card_frame_text.setText(self._card_text_by_id(card_id))

        self._fill_card_tag_checkboxes()
        self._center_popup(self.card_frame)
        self.card_frame.show()
        self.card_frame.raise_()
        self.card_frame_text.setFocus()

    def _card_text_by_id(self, card_id):
        for col in self.rendered_columns.values():
            layout = col.cards_container.layout
            for i in range(layout.count()):
                w = layout.itemAt(i).widget()
                if isinstance(w, DraggableCard) and w.card_id == card_id:
                    return w.text
        return ""

    def _fill_card_tag_checkboxes(self):
        while self.card_tags_layout.count():
            item = self.card_tags_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        tags = db.get_tags()
        if not tags:
            lbl = QLabel("Тегов нет", self.card_tags_container)
            lbl.setStyleSheet(f"""
                background: transparent;
                color: {text_dim};
                font-family: '{font_name}';
                font-size: 11px;
                font-weight: bold;
            """)
            self.card_tags_layout.addWidget(lbl)
            return

        for t in tags:
            cb = QCheckBox(t["name"], self.card_tags_container)
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {text_main};
                    font-family: '{font_name}';
                    font-size: 11px;
                    font-weight: bold;
                    spacing: 6px;
                }}
                QCheckBox::indicator {{
                    width: 12px; height: 12px;
                    border-radius: 3px;
                    border: none;
                    background: {bg_input};
                }}
                QCheckBox::indicator:checked {{
                    background: {t['color']};
                }}
            """)
            if t["id"] in self._pending_card_tags:
                cb.setChecked(True)
            cb.toggled.connect(
                lambda checked, tag_id=t["id"]: self._toggle_pending_tag(tag_id, checked)
            )
            self.card_tags_layout.addWidget(cb)

    def _toggle_pending_tag(self, tag_id, checked):
        if checked:
            self._pending_card_tags.add(tag_id)
        else:
            self._pending_card_tags.discard(tag_id)

    def close_card_dialog(self):
        self.card_frame.hide()
        self.card_frame_text.clear()
        self._pending_card_col_id = None
        self._pending_card_tags = set()
        self._edit_card_id = None

    def _save_card_from_input(self):
        text = self.card_frame_text.text().strip()
        if not text or self._pending_card_col_id is None:
            return

        col_id = self._pending_card_col_id

        if self._edit_card_id is None:
            card_id = db.create_card(col_id, text)
            for tag_id in self._pending_card_tags:
                db.add_tag_to_card(card_id, tag_id)
            self.close_card_dialog()
            self.sync_cards(col_id)
        else:
            card_id = self._edit_card_id
            db.update_card(card_id, title=text)
            existing = {t["id"] for t in db.get_card_tags(card_id)}
            for tag_id in self._pending_card_tags - existing:
                db.add_tag_to_card(card_id, tag_id)
            with db.get_conn() as conn:
                for tag_id in existing - self._pending_card_tags:
                    conn.execute(
                        "DELETE FROM card_tags WHERE card_id = ? AND tag_id = ?",
                        (card_id, tag_id)
                    )
            self.close_card_dialog()
            self.reload_column(col_id)

    def _build_tags_dialog(self):
        self.tags_frame = self._make_popup(340, 380)
        self._popup_title(self.tags_frame, "Теги", 240)
        close_btn = self._popup_close(self.tags_frame, 312)
        close_btn.clicked.connect(self.close_tags)

        self.tag_name_input = QLineEdit(self.tags_frame)
        self._style_input(self.tag_name_input)
        self.tag_name_input.setPlaceholderText("Название")
        self.tag_name_input.setFixedSize(160, 30)
        self.tag_name_input.move(16, 44)

        self.tag_color_btn = QPushButton(self.tags_frame)
        self.tag_color_btn.setFixedSize(30, 30)
        self.tag_color_btn.move(184, 44)
        self.tag_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tag_color = accent
        self._update_tag_color_btn()
        self.tag_color_btn.clicked.connect(self._pick_tag_color)

        add_btn = GlowButton("Добавить", self.tags_frame)
        add_btn.setFixedSize(90, 30)
        add_btn.move(222, 44)
        add_btn.clicked.connect(self._add_tag)

        self.tags_list = QWidget(self.tags_frame)
        self.tags_list.setStyleSheet("background: transparent;")
        self.tags_list.setGeometry(16, 88, 308, 276)
        self.tags_list_layout = QVBoxLayout(self.tags_list)
        self.tags_list_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_list_layout.setSpacing(4)
        self.tags_list_layout.addStretch()

    def _update_tag_color_btn(self):
        c = QColor(self._tag_color)
        self.tag_color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({c.red()}, {c.green()}, {c.blue()});
                border: none;
                border-radius: 4px;
            }}
        """)

    def _pick_tag_color(self):
        color = QColorDialog.getColor(QColor(self._tag_color), self, "Цвет тега")
        if color.isValid():
            self._tag_color = color.name()
            self._update_tag_color_btn()

    def _add_tag(self):
        name = self.tag_name_input.text().strip()
        if not name:
            return
        db.create_tag(name, self._tag_color)
        self.tag_name_input.clear()
        self._refresh_tags_list()

    def _refresh_tags_list(self):
        while self.tags_list_layout.count() > 1:
            item = self.tags_list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        for t in db.get_tags():
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(6)

            chip = TagChip(t["name"], t["color"])
            rl.addWidget(chip)
            rl.addStretch()

            del_btn = CloseIconButton("×", row)
            del_btn.setFixedSize(18, 18)
            del_btn.clicked.connect(
                lambda checked, tid=t["id"]: self._delete_tag(tid)
            )
            rl.addWidget(del_btn)

            self.tags_list_layout.insertWidget(self.tags_list_layout.count() - 1, row)

    def _delete_tag(self, tag_id):
        db.delete_tag(tag_id)
        self._refresh_tags_list()

    def open_tags(self):
        self._hide_all_popups()
        self._refresh_tags_list()
        self._center_popup(self.tags_frame)
        self.tags_frame.show()
        self.tags_frame.raise_()
        self.tag_name_input.setFocus()

    def close_tags(self):
        self.tags_frame.hide()

    def sync_columns(self):
        db_columns = db.get_all_columns()
        db_ids = {c["id"] for c in db_columns}
        ui_ids = set(self.rendered_columns.keys())

        for col in db_columns:
            if col["id"] not in ui_ids:
                self.add_column(col["title"], col["id"])
            else:
                self.sync_cards(col["id"])

        for col_id in ui_ids - db_ids:
            widget = self.rendered_columns.pop(col_id)
            widget.setParent(None)
            widget.deleteLater()

    def sync_cards(self, col_id):
        column = self.rendered_columns.get(col_id)
        if column is None:
            return
        layout = column.cards_container.layout

        ui_cards = {}
        for i in range(layout.count()):
            w = layout.itemAt(i).widget()
            if isinstance(w, DraggableCard) and w.card_id is not None:
                ui_cards[w.card_id] = w

        db_cards = db.get_cards_column(col_id)
        db_card_ids = {c["id"] for c in db_cards}
        tags_map = db.get_all_card_tags()

        for c in db_cards:
            if c["id"] not in ui_cards:
                tags = tags_map.get(c["id"], [])
                card = DraggableCard(c["id"], c["title"], tags, col_id, column.cards_container)
                self._wire_card(card)
                layout.insertWidget(layout.count() - 1, card)

        for cid in set(ui_cards) - db_card_ids:
            w = ui_cards[cid]
            w.setParent(None)
            w.deleteLater()

    def _wire_card(self, card):
        card.del_btn.clicked.connect(
            lambda checked, cid=card.card_id: self.on_delete_card(cid)
        )
        card.tags_btn.clicked.connect(
            lambda checked, cid=card.card_id, col=card.col_id: self.open_create_card(col, cid)
        )

    def reload_column(self, col_id):
        column = self.rendered_columns.get(col_id)
        if column is None:
            return
        layout = column.cards_container.layout
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        layout.addStretch()
        self.sync_cards(col_id)

    def add_column(self, title, col_id):
        column = ColumnWidget(col_id, title)

        column.add_btn.clicked.connect(
            lambda checked, cid=col_id: self.open_create_card(cid)
        )
        column.del_col_btn.clicked.connect(
            lambda checked, cid=col_id: self.open_delete_column(cid)
        )

        tags_map = db.get_all_card_tags()
        for card in db.get_cards_column(col_id):
            tags = tags_map.get(card["id"], [])
            card_widget = DraggableCard(card["id"], card["title"], tags, col_id, column.cards_container)
            self._wire_card(card_widget)
            column.cards_container.layout.insertWidget(
                column.cards_container.layout.count() - 1, card_widget
            )

        self.rendered_columns[col_id] = column
        self.content_layout.insertWidget(self.content_layout.count() - 1, column)

    def on_delete_card(self, card_id):
        db.delete_card(card_id)
        for col_id in list(self.rendered_columns.keys()):
            self.sync_cards(col_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(app_style())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())