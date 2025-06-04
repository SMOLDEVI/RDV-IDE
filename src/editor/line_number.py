from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal

class LineNumberArea(QWidget):
    line_clicked = pyqtSignal(int)

    def  __init__(self, editor, background="#1e1e1e", color="#abb2bf", current_color="#ffffff"):
        super().__init__(editor)
        self.editor = editor
        self.background = QColor(background)
        self.color = QColor(color)
        self.current_color = QColor(current_color)
        self.editor.blockCountChanged.connect(self.update_width)
        self.editor.cursorPositionChanged.connect(self.update)
        self.editor.verticalScrollBar().valueChanged.connect(self.update)
        self.update_width()

    def width(self):
        block_count = max(1, self.editor.document().blockCount())
        max_line_number = len(str(block_count))
        widest_text = '9' * max_line_number
        width = self.editor.fontMetrics().horizontalAdvance(widest_text) + 15
        return width

    def update_width(self):
        self.setFixedWidth(self.width())
        self.editor.setViewportMargins(self.width(), 0, 0, 0)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.fillRect(event.rect(), self.background)
        rect = event.rect()
        cursor = self.editor.textCursor()
        current_block = cursor.block() if cursor is not None else None

        block = self.editor.firstVisibleBlock()
        top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
        bottom = top + self.editor.blockBoundingRect(block).height()
        block_number = block.blockNumber()

        while block.isValid() and top <= rect.bottom():
            if block.isVisible() and bottom >= rect.top():
                number = str(block_number + 1)
                painter.setPen(self.current_color if block == current_block else self.color)
                painter.drawText(
                    0, int(top), self.width() - 5,
                    self.editor.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )
            block = block.next()
            top = bottom
            bottom = top + self.editor.blockBoundingRect(block).height()
            block_number += 1

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            y = event.position().y()
            block = self.editor.firstVisibleBlock()
            top = self.editor.blockBoundingGeometry(block).translated(self.editor.contentOffset()).top()
            bottom = top + self.editor.blockBoundingRect(block).height()
            while block.isValid():
                if top <= y <= bottom:
                    self.line_clicked.emit(block.blockNumber())
                    break
                block = block.next()
                top = bottom
                bottom = top + self.editor.blockBoundingRect(block).height()