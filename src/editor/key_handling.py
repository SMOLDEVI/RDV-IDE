from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtCore import Qt


class KeyHandlingMixin:
    def keyPressEvent(self, event: QKeyEvent):
        if self.qcompleter and self.qcompleter.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                return
            elif event.key() == Qt.Key.Key_Tab:
                index = self.qcompleter.popup().currentIndex()
                if index.isValid():
                    selected_text = self.qcompleter.popup().model().data(index)
                    self.insert_completion(selected_text)
                else:
                    self.qcompleter.popup().hide()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.qcompleter.popup().hide()
                return
            else:
                self.qcompleter.popup().hide()

        if event.key() == Qt.Key.Key_Tab:
            self.textCursor().insertText("    ")
            return
        QPlainTextEdit.keyPressEvent(self, event)
        self.handle_completer_popup()


       