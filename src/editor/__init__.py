
from .base_editor import BaseEditor
from .auto_completer import CompleterMixin


class CodeEditor(BaseEditor, CompleterMixin):
    def __init__(self, parent=None, file_path=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setup_all()
