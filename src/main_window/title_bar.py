import os
from PyQt6.QtCore import Qt, QPoint, QCoreApplication, pyqtSignal, QTimer, QDir, QStringListModel
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QWidget, QPushButton, QSpacerItem, QHBoxLayout,
    QSizePolicy, QLabel, QLineEdit, QCompleter, QListView
)
from src.editor.editor import CodeEditor


class TitleBar(QWidget):
    open_file_requested = pyqtSignal(str)

    def __init__(self, parent=None, menu_bar=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(30)

        self.current_directory = os.getcwd()
        self.setStyleSheet("""
            TitleBar {
                background-color: rgba(0, 0, 0, 0.8);
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QMenuBar {
                background: transparent;
                color: white;
            }
            QMenuBar::item:selected {
                background: rgba(255, 255, 255, 0.1);
            }
            QLabel {
                margin: 0px;
                padding: 0px;
            }
        """)

        self.menu_bar = menu_bar
        self.window_label = QLabel("RDV.IDE")

        # Поле поиска с автодополнением
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search...")
        self.search_field.setFixedHeight(24)
        self.search_field.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 4px 8px;
                color: white;
            }
            QLineEdit:focus {
                border: 1px solid #00b4ff;
            }
        """)

        # Модель и completer для автозаполнения
        self.completion_model = QStringListModel()
        self.completer = QCompleter()
        self.completer.setModel(self.completion_model)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(
            Qt.MatchFlag.MatchContains)  # Поиск по подстроке

        # Стилизация выпадающего списка автозавершения
        self.completer.popup().setStyleSheet("""
            QListView {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #444;
            }
            QListView::item:selected {
                background-color: #007acc;
                color: white;
            }
        """)

        self.search_field.setCompleter(self.completer)

        # Таймер для отложенного поиска
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.update_completions)

        self.search_field.textEdited.connect(self.on_text_changed)
        self.completer.activated.connect(self.on_completion_selected)

        # Кнопки управления
        self.minimize_button = QPushButton("⬇")
        self.restore_button = QPushButton("🔳")
        self.close_button = QPushButton("❌")

        self.minimize_button.clicked.connect(self.minimize_window)
        self.restore_button.clicked.connect(self.restore_window)
        self.close_button.clicked.connect(self.close_window)

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(0)

        if self.menu_bar:
            layout.addWidget(self.menu_bar)

        spacer = QSpacerItem(
            80, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout.addSpacerItem(spacer)
        layout.addWidget(self.search_field)
        layout.addSpacerItem(spacer)
        layout.addWidget(self.window_label)
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.restore_button)
        layout.addWidget(self.close_button)

        # Перетаскивание окна
        self.draggable = True
        self.is_dragging = False
        self.drag_position = QPoint()

    def mousePressEvent(self, event: QMouseEvent):
        if self.draggable and event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.window().pos()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging:
            self.window().move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.draggable and event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            event.accept()

    def close_window(self):
        QCoreApplication.quit()

    def minimize_window(self):
        self.window().showMinimized()

    def restore_window(self):
        if self.window().isFullScreen():
            self.window().showNormal()
        else:
            self.window().showFullScreen()

    def mouseDoubleClickEvent(self, event):
        self.restore_window()

    def on_text_changed(self, text):
        self.search_timer.stop()
        if text:
            self.search_timer.start(300)
        else:
            self.completion_model.setStringList([])

    def update_completions(self):
        text = self.search_field.text()
        if not text:
            self.completion_model.setStringList([])
            return

        results = []
        for root, dirs, files in os.walk(self.current_directory):
            for name in files:
                if text.lower() in name.lower():
                    results.append(name)
            if len(results) >= 20:
                break

        self.completion_model.setStringList(sorted(set(results)))

    def on_completion_selected(self, selected_name: str):
        if not selected_name:
            return

        selected_path = None
        for root, dirs, files in os.walk(self.current_directory):
            if selected_name in files:
                selected_path = os.path.join(root, selected_name)
                break

        if selected_path:
            self.open_file_requested.emit(selected_path)
            editor = self.find_editor()
            if editor:
                try:
                    with open(selected_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    editor.setPlainText(content)
                    editor.file_path = selected_path
                    editor.set_lexer_by_filename(selected_path)
                except Exception as e:
                    print(f"Error reading file {selected_path}: {e}")

        self.search_field.clear()

    def find_editor(self):
        if self.parent is not None:
            for child in self.parent.findChildren(CodeEditor):
                return child
        return None

    def set_current_directory(self, path: str):
        if os.path.isdir(path):
            self.current_directory = path
            print(f"Current directory changed to: {path}")
        else:
            print(f"Invalid directory: {path}")
