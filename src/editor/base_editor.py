from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QRect, QTimer

from src.editor.line_number import LineNumberArea
from src.editor.syntax_hightlighter import ReliableSyntaxHighlighter
from pygments.lexers import get_lexer_for_filename


class BaseEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.highlighter = ReliableSyntaxHighlighter(self.document())
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_line_number_area)

        self.setup_editor()

        self.document().contentsChanged.connect(self.update_line_number_area)
        self.verticalScrollBar().valueChanged.connect(self.update_line_number_area_on_scroll)

    def setup_editor(self):
        font = QFont("Courier New", 20)
        metrics = self.fontMetrics()
        self.setTabStopDistance(12 * metrics.horizontalAdvance(' '))
        self.setFont(font)
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #abb2bf;
                selection-background-color: #3e4451;
                border: none;
            }
        """)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def update_line_number_area(self):
        self.line_number_area.update(0, 0, self.line_number_area.width(), self.height())

    def update_line_number_area_on_scroll(self):
        self.update_timer.start(100)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        w = self.line_number_area.width()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), w, cr.height()))
        self.setViewportMargins(w, 0, 0, 0)

    def set_lexer_by_filename(self, filename):
        try:
            lexer = get_lexer_for_filename(filename)
            self.highlighter.set_lexer(lexer)
        except Exception:
            self.highlighter.set_lexer(None)
