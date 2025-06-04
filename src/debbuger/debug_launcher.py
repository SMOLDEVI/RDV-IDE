# src/debugger/debug_launcher.py

from PyQt6.QtCore import QObject, QProcess, pyqtSignal


class DebugLauncher(QObject):
    process_started = pyqtSignal()
    process_error = pyqtSignal(str)
    output_received = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.process = QProcess()

    def start_debug_server(self):
        # Команда: python -m debugpy --listen 5678 --wait-for-client your_script.py
        self.process.setProgram("python")
        self.process.setArguments([
            "-m", "debugpy",
            "--listen", "5678",
            "--wait-for-client",
            self.file_path
        ])

        self.process.setProcessChannelMode(
            QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.errorOccurred.connect(self.handle_error)

        self.process.start()
        self.output_received.emit(f"[Запуск debugpy] {self.file_path}")

    def read_output(self):
        raw_data = self.process.readAllStandardOutput()
        if not raw_data:
            return

        # Попробуйте разные кодировки:
        try:
            data = bytes(raw_data).decode('utf-8')
        except UnicodeDecodeError:
            try:
                data = bytes(raw_data).decode(
                    'cp866', errors='replace')  # Windows CMD
            except UnicodeDecodeError:
                data = bytes(raw_data).decode('latin-1', errors='replace')

        if data.strip():
            self.output_received.emit(data.strip())

    def handle_error(self, error):
        self.process_error.emit(f"Ошибка запуска debugpy: {error}")

    def is_running(self):
        return self.process.state() == QProcess.ProcessState.Running

    def stop(self):
        if self.is_running():
            self.process.terminate()
            self.process.waitForFinished(3000)
