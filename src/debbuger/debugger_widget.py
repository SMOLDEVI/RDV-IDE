# src/debugger/debugger_widget.py

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
)
from PyQt6.QtCore import pyqtSlot, QTimer

import sys
import subprocess

from .dap_client import DapClient
from .debug_launcher import DebugLauncher
import json  # для логирования сообщений


class DebuggerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_editor = None
        self.dap_client = None
        self.debug_launcher = None
        self.current_thread_id = None
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.btn_continue = QPushButton("▶▶ Continue")
        self.btn_step_over = QPushButton("⏭ Over")
        self.btn_step_in = QPushButton("⏭ In")
        self.btn_step_out = QPushButton("⏭ Out")
        self.btn_stop = QPushButton("◼ Stop")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_continue)
        button_layout.addWidget(self.btn_step_over)
        button_layout.addWidget(self.btn_step_in)
        button_layout.addWidget(self.btn_step_out)
        button_layout.addWidget(self.btn_stop)
        layout.addLayout(button_layout)

        self.debug_output = QTextEdit()
        self.debug_output.setReadOnly(True)
        layout.addWidget(QLabel("Output"))
        layout.addWidget(self.debug_output)

        self.variables_tree = QTreeWidget()
        self.variables_tree.setHeaderLabels(["Name", "Value", "Type"])
        self.variables_tree.setStyleSheet("""
                QTreeWidget {
                    background-color: #2b2b2b;  /* тёмный фон */
                    color: #f0f0f0;             /* светлый текст */
                    font-family: Consolas, monospace;
                    font-size: 12px;
                }
                QTreeWidget::item {
                    height: 20px;
                }
                QHeaderView::section {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    padding: 4px;
                    font-weight: bold;
                    border: 1px solid #555555;
                }
                QTreeWidget::item:selected {
                    background-color: #555555;
                    color: #ffffff;
                }
            """)

        layout.addWidget(QLabel("Variables"))
        layout.addWidget(self.variables_tree)

        self.setLayout(layout)
        self.set_buttons_enabled(False)

    def setup_connections(self):
        self.btn_continue.clicked.connect(self.on_continue_clicked)
        self.btn_step_over.clicked.connect(self.on_step_over_clicked)
        self.btn_step_in.clicked.connect(self.on_step_in_clicked)
        self.btn_step_out.clicked.connect(self.on_step_out_clicked)
        self.btn_stop.clicked.connect(self.stop_debugging)

    def set_current_editor(self, editor):
        self.current_editor = editor

    def set_buttons_enabled(self, enabled):
        self.btn_continue.setEnabled(enabled)
        self.btn_step_over.setEnabled(enabled)
        self.btn_step_in.setEnabled(enabled)
        self.btn_step_out.setEnabled(enabled)
        self.btn_stop.setEnabled(enabled)

    def start_debugging(self):
        print("[DEBUG] Метод start_debugging вызван")
        if not self.current_editor or not self.current_editor.file_path:
            self.debug_output.append("[Ошибка] Нет открытого файла для отладки.")
            return

        file_path = self.current_editor.file_path
        print(f"[DEBUG] Попытка запуска отладки файла: {file_path}")
        self.debug_output.clear()
        self.variables_tree.clear()

        self.debug_launcher = DebugLauncher(file_path)
        self.debug_launcher.output_received.connect(self.debug_output.append)
        self.debug_launcher.process_error.connect(self.debug_output.append)
        self.debug_launcher.start_debug_server()

        self.debug_output.append(f"[DEBUG] Запущен debugpy для файла: {file_path}")
        QTimer.singleShot(1000, self.connect_to_dap_server)

    def connect_to_dap_server(self):
        print("[DEBUG] connect_to_dap_server() вызван")
        self.dap_client = DapClient()
        print("[DEBUG] DapClient создан")

        def on_connected():
            print("[DEBUG] Успешное подключение к DAP-серверу")
            self.debug_output.append("[DEBUG] Успешное подключение к DAP-серверу")
            self.set_buttons_enabled(True)
            self.dap_client.initialize()

        self.dap_client.connected.connect(on_connected)
        self.dap_client.message_received.connect(self.handle_dap_message)
        self.dap_client.output_received.connect(self.debug_output.append)
        self.dap_client.connect_to_debugger()

    def handle_dap_message(self, msg):
        print("<< DAP Message:", json.dumps(msg, indent=2))

        if msg.get("type") == "event":
            event_type = msg.get("event")

            if event_type == "initialized":
                print("[DEBUG] Получено событие initialized")
                self.debug_output.append("[DEBUG] DAP-сервер инициализирован")

                breakpoints = [
                    line for line in self.current_editor.breakpoints if line >= 0
                ]
                self.dap_client.set_breakpoints(
                    self.current_editor.file_path, breakpoints
                )
                self.dap_client.send_request("configurationDone")

            elif event_type == "stopped":
                reason = msg["body"].get("reason", "")
                self.current_thread_id = msg["body"].get("threadId", 1)
                line_number = msg["body"].get("line", 1) - 1
                self.debug_output.append(f"[Остановка] Причина: {reason}")
                self.current_editor.highlight_debug_line(line_number)

                self.dap_client.send_request(
                    "stackTrace", {"threadId": self.current_thread_id}
                )

            elif event_type == "output":
                output = msg["body"].get("output", "").strip()
                if output:
                    self.debug_output.append(f"[Вывод] {output}")

        elif msg.get("type") == "response":
            command = msg.get("command")
            if command == "initialize":
                print("[DEBUG] Команда initialize завершена — отправляем launch")
                self.dap_client.attach()

            if command == "stackTrace":
                stack_frames = msg["body"].get("stackFrames", [])
                if stack_frames:
                    frame_id = stack_frames[0]["id"]
                    self.dap_client.send_request("scopes", {"frameId": frame_id})

            elif command == "scopes":
                scopes = msg["body"].get("scopes", [])
                if scopes:
                    scope_ref = scopes[0]["variablesReference"]
                    self.dap_client.send_request(
                        "variables", {"variablesReference": scope_ref}
                    )

            elif command == "variables":
                variables = msg["body"].get("variables", [])
                self.update_variables_tree(variables)

    def update_variables_tree(self, variables):
        self.variables_tree.clear()
        for var in variables:
            name = var.get("name", "")
            value = var.get("value", "")
            var_type = var.get("type", "unknown")
            item = QTreeWidgetItem([name, value, var_type])
            self.variables_tree.addTopLevelItem(item)

    def on_continue_clicked(self):
        print("[DEBUG] Кнопка 'Continue' нажата")
        self.debug_output.append("[DEBUG] Продолжение выполнения...")
        self.continue_execution()

    def continue_execution(self):
        if self.dap_client and self.current_thread_id:
            print("[DEBUG] Выполняется команда: continue")
            self.dap_client.send_request(
                "continue", {"threadId": self.current_thread_id}
            )
        else:
            print("[DEBUG] DAP клиент не инициализирован — продолжение невозможно")
            self.debug_output.append("[Ошибка] Нет активного соединения с отладчиком.")

    def on_step_over_clicked(self):
        print("[DEBUG] Кнопка 'Step Over' нажата")
        self.debug_output.append("[DEBUG] Шаг выполнения: Next (Step Over)")
        self.step_over()

    def step_over(self):
        if self.dap_client and self.current_thread_id:
            print("[DEBUG] Выполняется команда: next")
            self.dap_client.send_request("next", {"threadId": self.current_thread_id})
        else:
            print("[DEBUG] DAP клиент не инициализирован — шаг недоступен")

    def on_step_in_clicked(self):
        print("[DEBUG] Кнопка 'Step In' нажата")
        self.debug_output.append("[DEBUG] Шаг выполнения: Step In")
        self.step_in()

    def step_in(self):
        if self.dap_client and self.current_thread_id:
            print("[DEBUG] Выполняется команда: stepIn")
            self.dap_client.send_request("stepIn", {"threadId": self.current_thread_id})
        else:
            print("[DEBUG] DAP клиент не инициализирован — шаг недоступен")

    def on_step_out_clicked(self):
        print("[DEBUG] Кнопка 'Step Out' нажата")
        self.debug_output.append("[DEBUG] Шаг выполнения: Step Out")
        self.step_out()

    def step_out(self):
        if self.dap_client and self.current_thread_id:
            print("[DEBUG] Выполняется команда: stepOut")
            self.dap_client.send_request(
                "stepOut", {"threadId": self.current_thread_id}
            )
        else:
            print("[DEBUG] DAP клиент не инициализирован — шаг недоступен")

    def stop_debugging(self):
        print("[DEBUG] Кнопка 'Stop' нажата")
        self.debug_output.append("[DEBUG] Остановка отладки...")

        if self.debug_launcher:
            print("[DEBUG] Останавливается debug_launcher")
            self.debug_launcher.stop()

        if self.dap_client:
            print("[DEBUG] Отправка команды disconnect")
            self.dap_client.send_request("disconnect")
            self.dap_client = None

        self.variables_tree.clear()
        self.set_buttons_enabled(False)
