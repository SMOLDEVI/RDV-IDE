# src/debugger/dap_client.py

import json
import socket
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class DapClient(QObject):
    message_received = pyqtSignal(dict)
    connected = pyqtSignal()
    output_received = pyqtSignal(str)

    def __init__(self, host="localhost", port=5678):
        super().__init__()
        self.sock = None
        self.host = host
        self.port = port
        self.buffer = ""
        self.seq = 1

    def connect_to_debugger(self):
        try:
            print("[DEBUG] Попытка подключения к debugpy")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.sock.setblocking(False)
            print("[DEBUG] Сигнал connected отправлен")
            self.connected.emit()
            QTimer.singleShot(100, self.poll_socket)
        except Exception as e:
            self.output_received.emit(
                f"[Ошибка] Не удалось подключиться к отладчику: {e}")

    def poll_socket(self):
        if not self.sock:
            return
        try:
            data = self.sock.recv(4096).decode("utf-8")
            if data:
                self.buffer += data
                self.process_buffer()
        except BlockingIOError:
            pass
        QTimer.singleShot(100, self.poll_socket)

    def process_buffer(self):
        while "\r\n\r\n" in self.buffer:
            header_end = self.buffer.find("\r\n\r\n")
            header = self.buffer[:header_end]
            content_length = 0
            for line in header.split("\r\n"):
                if line.startswith("Content-Length:"):
                    content_length = int(line.split(":")[1].strip())
            body_start = header_end + 4
            body_end = body_start + content_length
            if len(self.buffer) >= body_end:
                body = self.buffer[body_start:body_end]
                self.buffer = self.buffer[body_end:]
                try:
                    msg = json.loads(body)
                    self.message_received.emit(msg)
                except json.JSONDecodeError as e:
                    self.output_received.emit(f"[JSON ошибка] {str(e)}")

    def send_request(self, command, arguments=None):
        payload = json.dumps({
            "type": "request",
            "seq": self.seq,
            "command": command,
            "arguments": arguments or {}
        })
        self.seq += 1
        header = f"Content-Length: {len(payload)}\r\n\r\n"
        self.sock.sendall((header + payload).encode("utf-8"))

    def initialize(self):
        self.send_request("initialize", {
            "clientID": "RDV.IDE",
            "adapterID": "debugpy",
            "pathFormat": "path",
            "linesStartAt1": True,
            "columnsStartAt1": True,
            "supportsVariableType": True,
            "supportsVariablePaging": True,
            "supportsRunInTerminalRequest": True
        })

    def attach(self):
        self.send_request("attach", {
            "name": "Attach to debugpy",
            "type": "python",
            "request": "attach",
            "connect": {
                "host": self.host,
                "port": self.port
            },
            "justMyCode": True
        })

    def set_breakpoints(self, file_path, lines):
        self.send_request("setBreakpoints", {
            "source": {"path": file_path},
            "breakpoints": [{"line": line + 1} for line in lines]
        })

    def continue_execution(self, thread_id):
        self.send_request("continue", {"threadId": thread_id})

    def next_step(self, thread_id):
        self.send_request("next", {"threadId": thread_id})

    def step_in(self, thread_id):
        self.send_request("stepIn", {"threadId": thread_id})

    def step_out(self, thread_id):
        self.send_request("stepOut", {"threadId": thread_id})
