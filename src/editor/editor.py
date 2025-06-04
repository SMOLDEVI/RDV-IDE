from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit
from PyQt6.QtCore import QTimer, QRect
from PyQt6.QtGui import QTextCursor, QFont, QColor,QTextFormat,QTextCharFormat
from pygments.lexers import get_lexer_for_filename
from src.editor.syntax_hightlighter import ReliableSyntaxHighlighter
from src.editor.line_number import LineNumberArea
from src.editor.auto_completer import CompleterMixin
from src.editor.key_handling import KeyHandlingMixin
import autopep8

class OutputProxy:
    def __init__(self, text_edit):
        self.text_edit = text_edit

    def write(self, text):
        if self.text_edit:
            self.text_edit.append(text.rstrip())

    def flush(self):
        pass

class CodeEditor(QPlainTextEdit, CompleterMixin, KeyHandlingMixin):
    def __init__(self, parent=None, file_path=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.breakpoints = set()
        self.setup_editor()
        self.setup_completer()
        self.highlighter = ReliableSyntaxHighlighter(self.document())
        self.file_path = file_path
        self.setup_line_number_area()
        self.document().contentsChanged.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.verticalScrollBar().valueChanged.connect(self.on_scroll)

        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_line_number_area)

        if file_path:
            self.set_lexer_by_filename(file_path)

    def setup_editor(self):
        font = QFont("Courier New", 12)
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

    def eventFilter(self, obj, event):
        if hasattr(self, 'qcompleter') and self.qcompleter is not None:
            if obj == self.qcompleter.popup() and self.qcompleter.popup() is not None:
                if event.type() == event.Type.Show:
                    cursor_rect = self.cursorRect()
                    pt = self.mapToGlobal(cursor_rect.bottomRight())
                    self.qcompleter.popup().move(pt.x(), pt.y())
                    return True

            # Пример: активация автодополнения
            if obj == self and event.type() == event.Type.KeyPress:
                if len(event.text()) > 0 and event.text().isalnum():
                    self.handle_completer_popup()

        return super().eventFilter(obj, event)

    def update_line_number_area(self):
        self.line_number_area.update(0, 0, self.line_number_area.width(), self.height())

    def on_scroll(self):
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
        except:
            self.highlighter.set_lexer(None)

    def format_code(self):
        original_text = self.toPlainText()
        try:
            formatted = autopep8.fix_code(original_text)
            if formatted.strip() != original_text.strip():
                cursor = self.textCursor()
                cursor.select(QTextCursor.SelectionType.Document)
                cursor.removeSelectedText()
                cursor.insertText(formatted)
        except Exception as e:
            print("Ошибка форматирования:", e)

    def highlight_current_line(self):
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            # Тонкая полоска вместо фона всей строки
            line_format = QTextCharFormat()
            line_format.setBackground(QColor("#3e4451"))  # Цвет полоски
            line_format.setProperty(QTextFormat.Property.FullWidthSelection, True)

            selection.format = line_format
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)
    
    def toggle_breakpoint(self, line_number):
        if line_number in self.breakpoints:
            self.breakpoints.remove(line_number)
        else:
            self.breakpoints.add(line_number)
        self.update_breakpoints()

    def update_breakpoints(self):
        extra_selections = []

        for block_number in self.breakpoints:
            block = self.document().findBlockByLineNumber(block_number)
            if not block.isValid():
                continue  # пропускаем невалидные блоки
            cursor = QTextCursor(block)
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#e06c75"))
            fmt.setProperty(QTextFormat.Property.FullWidthSelection, True)

            selection = QTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            selection.format = fmt
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

        self.setExtraSelections(extra_selections)
    def setup_line_number_area(self):
        self.line_number_area = LineNumberArea(self)
        self.line_number_area.line_clicked.connect(self.toggle_breakpoint)
    
    def highlight_debug_line(self, line_number):
        extra_selections = []

        # Текущая исполняемая строка
        selection = QTextEdit.ExtraSelection()
        line_format = QTextCharFormat()
        line_format.setBackground(QColor("#4f5b67"))  # Цвет текущей строки
        line_format.setProperty(QTextFormat.Property.FullWidthSelection, True)

        cursor = QTextCursor(self.document().findBlockByLineNumber(line_number))
        selection.format = line_format
        selection.cursor = cursor
        selection.cursor.select(QTextCursor.SelectionType.LineUnderCursor)

        extra_selections.append(selection)

        # Существующие точки останова
        for block_number in self.breakpoints:
            cursor = QTextCursor(self.document().findBlockByLineNumber(block_number))
            fmt = QTextCharFormat()
            fmt.setBackground(QColor("#e06c75"))  # Красный цвет для брейкпоинта
            fmt.setProperty(QTextFormat.Property.FullWidthSelection, True)

            selection = QTextEdit.ExtraSelection()
            selection.format = fmt
            selection.cursor = cursor
            selection.cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)