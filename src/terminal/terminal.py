import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPlainTextEdit, QPushButton,
    QTextBrowser, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, QProcess, QEvent, QTextStream
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor
from src.editor.editor import CodeEditor


class WindowsTerminal(QWidget):
    def __init__(self, parent=None, tab_view=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.tab_view = tab_view
        self.process = None
        self.command_history = []
        self.history_index = -1
        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Текстовое поле для эмуляции терминала
        self.terminal_output = QTextBrowser()
        self.terminal_output.setFont(QFont("Consolas", 12))
        self.terminal_output.setStyleSheet("""
            background-color: #1e1e1e;
            color: #dcdcdc;
            border-top: 1px solid #333;
            padding: 8px;
        """)
        self.terminal_output.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Поле ввода команд
        self.command_input = QPlainTextEdit()
        self.command_input.setFont(QFont("Consolas", 12))
        self.command_input.setStyleSheet("""
            background-color: #2d2d2d;
            color: white;
            border: none;
            padding: 4px;
        """)
        self.command_input.setMaximumHeight(40)
        # Добавляем фильтр для событий клавиш
        self.command_input.installEventFilter(self)

        # Кнопки управления
        self.button_layout = QHBoxLayout()
        self.compile_button = QPushButton("▷ Запустить")
        self.clear_button = QPushButton("CLS")
        self.restart_button = QPushButton("⟳")

        self.compile_button.clicked.connect(self.compile_code)
        self.clear_button.clicked.connect(self.clear_terminal)
        self.restart_button.clicked.connect(self.restart_shell)

        self.compile_button.setStyleSheet(self.get_button_style("#28a745"))
        self.clear_button.setStyleSheet(self.get_button_style("#dc3545"))
        self.restart_button.setStyleSheet(self.get_button_style("#ffc107"))

        self.button_layout.addWidget(self.compile_button)
        self.button_layout.addWidget(self.restart_button)
        self.button_layout.addWidget(self.clear_button)

        # Добавляем элементы в layout
        self.layout.addWidget(self.terminal_output)
        self.layout.addWidget(self.command_input)
        self.layout.addLayout(self.button_layout)
        self.setLayout(self.layout)

        # Запускаем командный процессор Windows
        self.start_command_process()

    def get_button_style(self, color):
        return f"""
        QPushButton {{
            background-color: {color};
            color: black;
            font-weight: bold;
            font-size: 12px;
            padding: 5px 10px;
            border-radius: 4px;
        }}
        QPushButton:hover {{
            opacity: 0.9;
        }}
        QPushButton:pressed {{
            opacity: 0.8;
        }}
        """

    def eventFilter(self, obj, event):
        if obj == self.command_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return:
                cursor = self.command_input.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.select(QTextCursor.SelectionType.LineUnderCursor)
                command = cursor.selectedText().strip()

                if command:
                    self.append_output(f"{self.get_prompt()} {command}\n")

                    # Кодируем команду в cp866 перед отправкой в cmd.exe
                    encoded_command = f"{command}\r\n".encode('cp866')
                    self.process.write(encoded_command)

                    self.command_history.append(command)
                    self.history_index = len(self.command_history)
                self.command_input.clear()
                return True

            elif event.key() == Qt.Key.Key_Up:
                if self.command_history:
                    self.history_index = max(0, self.history_index - 1)
                    self.command_input.setPlainText(
                        self.command_history[self.history_index])
                    cursor = self.command_input.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.command_input.setTextCursor(cursor)
                return True

            elif event.key() == Qt.Key.Key_Down:
                if self.command_history:
                    self.history_index = min(
                        len(self.command_history) - 1, self.history_index + 1)
                    self.command_input.setPlainText(
                        self.command_history[self.history_index])
                    cursor = self.command_input.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    self.command_input.setTextCursor(cursor)
                return True

        return super().eventFilter(obj, event)

    def get_prompt(self):
        return "$"

    def compile_code(self):
        current_index = self.tab_view.currentIndex()
        if current_index == -1:
            return

        editor = self.tab_view.widget(current_index)
        if not isinstance(editor, CodeEditor):
            return

        file_path = self.parent_widget.tab_files.get(current_index)
        if not file_path:
            QMessageBox.warning(self, "Ошибка", "Файл не сохранён!")
            return

        code = editor.toPlainText()
        if file_path.endswith(".py"):
            self.execute_command(f"python {file_path}")
        elif file_path.endswith(".cpp"):
            base_name = os.path.splitext(file_path)[0]
            self.execute_command(f"g++ {file_path} -o {base_name}.exe")
            self.execute_command(f"clang {file_path} -o {base_name}.exe")
            self.execute_command(f".\\{base_name}.exe")
        elif file_path.endswith(".java"):
            self.execute_command(f"javac {file_path}")
            class_name = os.path.splitext(os.path.basename(file_path))[0]
            self.execute_command(f"java {class_name}")
        else:
            QMessageBox.warning(
                self, "Ошибка", "Неизвестный тип файла для запуска.")

    def execute_command(self, command):
        self.append_output(f"{self.get_prompt()} {command}\n")

        encoded_command = f"{command}\r\n".encode('cp866')
        self.process.write(encoded_command)

    def start_command_process(self):
        self.process = QProcess()
        self.process.setProgram("cmd")
        self.process.setArguments(["/K"])
        self.process.setProcessChannelMode(
            QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.start()
        self.process.waitForStarted()

    def read_output(self):
        data = self.process.readAllStandardOutput()
        if data:
            # Используем cp866 для корректного отображения русских букв
            text = bytes(data).decode('cp866')
            self.append_output(text)

    def append_output(self, text):
        cursor = self.terminal_output.textCursor()
        format = QTextCharFormat()
        format.setForeground(QColor("white"))  # Зеленый цвет
        cursor.setCharFormat(format)
        cursor.insertText(text)
        self.terminal_output.setTextCursor(cursor)
        self.terminal_output.ensureCursorVisible()

    def clear_terminal(self):
        self.terminal_output.clear()

    def restart_shell(self):
        if self.process:
            self.process.kill()
            self.process.waitForFinished()
        self.start_command_process()
        self.append_output("[Терминал перезапущен]\n")

    def toggle_visibility(self):
        self.setVisible(not self.isVisible())

    def showEvent(self, event):
        super().showEvent(event)
        self.command_input.setFocus()
    
    def __del__(self):
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished(3000)