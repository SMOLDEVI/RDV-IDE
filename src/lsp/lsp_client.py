import asyncio
import json
import os

class LSPClient:
    def __init__(self, server_command):
        self.server_command = server_command  # например ['pylsp', '--stdio']
        self.process = None
        self.is_running = False
        self.request_id = 0

    async def start(self):
        try:
            self.process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.is_running = True
            print("[LSP]: Сервер успешно запущен.")
        except FileNotFoundError as e:
            print(f"[Ошибка запуска сервера LSP]: {e}")
            self.process = None
            self.is_running = False

    async def stop(self):
        if self.process:
            self.process.terminate()
            await self.process.wait()
            self.process = None
            self.is_running = False
            print("[LSP]: Сервер остановлен.")

    async def send(self, payload):
        if not self.is_running:
            print("[LSP]: Невозможно отправить данные — сервер не запущен.")
            return
        
        data = json.dumps(payload)
        content_length = len(data.encode('utf-8'))
        header = f"Content-Length: {content_length}\r\n\r\n"
        
        try:
            self.process.stdin.write(header.encode('utf-8') + data.encode('utf-8'))
            await self.process.stdin.drain()
        except Exception as e:
            print(f"[Ошибка отправки данных LSP]: {e}")
            await self.stop()

    async def request_completion(self, text, line, column, file_path):
        if not self.is_running:
            print("[LSP]: Автодополнение недоступно — сервер не запущен.")
            return None
        
        self.request_id += 1
        uri = f"file:///{file_path.replace('\\', '/')}"  # Используем путь к файлу
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "textDocument/completion",
            "params": {
                "textDocument": {"uri": uri},
                "position": {"line": line, "character": column},
                "context": {"triggerKind": 1}
            }
        }
        
        await self.send(request)
        
        try:
            response = await self.read_response()
            return response
        except Exception as e:
            print(f"[Ошибка получения ответа LSP]: {e}")
            return None

    async def read_response(self):
        if not self.is_running:
            return None

        try:
            # Чтение заголовка
            header = b""
            while not header.endswith(b"\r\n\r\n"):
                chunk = await self.process.stdout.read(1)
                if not chunk:
                    raise ConnectionError("Потеря связи с сервером LSP.")
                header += chunk

            header_text = header.decode('utf-8')
            headers = dict(
                line.split(": ", 1)
                for line in header_text.split("\r\n")
                if ": " in line
            )

            content_length = int(headers.get("Content-Length", 0))
            body = await self.process.stdout.readexactly(content_length)

            return json.loads(body.decode('utf-8'))
        except Exception as e:
            print(f"[Ошибка чтения ответа LSP]: {e}")
            await self.stop()
            return None
