from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSlider, QLabel, QDialog, QDialogButtonBox
from PyQt6.QtCore import Qt

class SliderWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Transparency")
        self.setModal(True)
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)

        self.layout = QVBoxLayout(self)

        self.label = QLabel("Adjust Transparency", self)
        self.layout.addWidget(self.label)

        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.setRange(1, 100)
        self.slider.setValue(int(parent.windowOpacity() * 100))
        self.layout.addWidget(self.slider)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.original_opacity = parent.windowOpacity()
        self.slider.valueChanged.connect(self.preview_transparency)

    def preview_transparency(self, value):
        self.parent().setWindowOpacity(value / 100)

    def accept(self):
        # Применяем изменения только при OK
        self.parent().setWindowOpacity(self.slider.value() / 100)
        super().accept()

    def reject(self):
        # Отмена → восстановление старой прозрачности
        self.parent().setWindowOpacity(self.original_opacity)
        super().reject()