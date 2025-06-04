# auto_completer.py
import jedi
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QCompleter
from PyQt6.QtCore import QTimer, Qt, QRect, QStringListModel, QObject
from PyQt6.QtGui import QTextCursor


class CompleterMixin(QObject):
    def setup_completer(self):
        self.completion_model = QStringListModel()
        self.qcompleter = QCompleter(self.completion_model, self)
        self.qcompleter.setCompletionMode(
            QCompleter.CompletionMode.PopupCompletion)
        self.qcompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.qcompleter.setFilterMode(Qt.MatchFlag.MatchContains)
        self.qcompleter.setWrapAround(True)
        self.qcompleter.setWidget(self)
        self.qcompleter.popup().installEventFilter(self)
        self.qcompleter.popup().setStyleSheet("""
            QListView {
                background-color: #2e323a;
                color: #abb2bf;
                font-family: Courier New;
                font-size: 12pt;
                border: 1px solid #3b4048;
                outline: 0px;
                border-radius: 20px;
            }
            QListView::item:selected {
                background-color: #3e4451;
            }
        """)
        self.qcompleter.popup().setMinimumWidth(300)
        self.qcompleter.activated.connect(self.insert_completion)

        self.completion_timer = QTimer(self)
        self.completion_timer.setSingleShot(True)
        self.completion_timer.timeout.connect(self.request_completion)

    def eventFilter(self, obj, event):
        if hasattr(self, 'qcompleter') and self.qcompleter is not None:
            if obj == self.qcompleter.popup():
                if event.type() == event.Type.Show:
                    cursor_rect = self.cursorRect()
                    pt = self.mapToGlobal(cursor_rect.bottomRight())
                    self.qcompleter.popup().move(pt.x(), pt.y())
                    return True
        return super().eventFilter(obj, event)

    def request_completion(self):
        cursor = self.textCursor()
        current_block_text = cursor.block().text()
        column = cursor.positionInBlock()

        word = ''
        for i in range(column - 1, -1, -1):
            if not current_block_text[i].isalnum() and current_block_text[i] != '_':
                break
            word = current_block_text[i] + word

        if len(word) < 1:
            self.qcompleter.popup().hide()
            return

        source_code = self.toPlainText()
        line = cursor.blockNumber() + 1
        column = cursor.positionInBlock()

        self.auto_completer = AutoCompleter(self, source_code, line, column)
        self.auto_completer.suggestions_ready.connect(
            self.show_suggestions, Qt.ConnectionType.QueuedConnection)
        self.auto_completer.start()

    def show_suggestions(self, suggestions):
        if not suggestions:
            self.qcompleter.popup().hide()
            return

        self.completion_model.setStringList(suggestions)
        cursor_rect = self.cursorRect()
        self.qcompleter.complete(
            QRect(cursor_rect.topLeft(), cursor_rect.size()))

    def insert_completion(self, text):
        if not text:
            return

        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.removeSelectedText()
        cursor.insertText(text)
        self.qcompleter.popup().hide()

    def handle_completer_popup(self):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Left, n=1)
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        selected_text = cursor.selectedText()

        if len(selected_text) >= 1:
            self.completion_timer.start(300)

    def eventFilter(self, obj, event):
        if hasattr(self, 'qcompleter') and self.qcompleter is not None:
            if obj == self.qcompleter.popup():
                if event.type() == event.Type.Show:
                    cursor_rect = self.cursorRect()
                    pt = self.mapToGlobal(cursor_rect.bottomRight())
                    self.qcompleter.popup().move(pt.x(), pt.y())
                    return True
        return super().eventFilter(obj, event)


class AutoCompleter(QThread):
    suggestions_ready = pyqtSignal(list)

    def __init__(self, code_editor, source, line, column):
        super().__init__()
        self.code_editor = code_editor
        self.source = source
        self.line = line
        self.column = column

    def run(self):
        try:
            if self.code_editor.file_path:
                script = jedi.Script(
                    self.source, path=self.code_editor.file_path)
            else:
                script = jedi.Script(self.source)
            completions = script.complete(self.line, self.column)
            suggestions = [c.name for c in completions]
            self.suggestions_ready.emit(suggestions)
        except Exception as e:
            print("Ошибка автодополнения:", e)
            self.suggestions_ready.emit([])
