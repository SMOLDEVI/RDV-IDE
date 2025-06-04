from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from src.recent.recent_projects import load_recent_projects


class StartScreen(QWidget):
    def __init__(self, new_project_callback, open_project_callback, just_start_callback):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint) 
        self.resize(700, 500)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #dcdce5;
                font-family: 'Courier New';
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #3a3a4f;
                border: 1px solid #4a4a5e;
                padding: 10px;
                border-radius: 6px;
                min-width: 180px;
            }
            QPushButton:hover {
                background-color: #4a4a5e;
            }
            QPushButton:pressed {
                background-color: #5a5a6e;
            }
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #2a2a3a;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a5e;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        title = QLabel("Welcome to RDV.IDE")
        title.setFont(QFont("Courier New", 24))
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Кнопки действий
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        new_btn = QPushButton("📄 New Project")
        new_btn.clicked.connect(new_project_callback)
        button_layout.addWidget(new_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        open_btn = QPushButton("📁 Open Project")
        open_btn.clicked.connect(open_project_callback)
        button_layout.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        start_btn = QPushButton("🚀 Start Without Project")
        start_btn.clicked.connect(just_start_callback)
        button_layout.addWidget(start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(button_layout)

        # Recent Projects Header
        recent_title = QLabel("Recent Projects")
        recent_title.setFont(QFont("Courier New", 16))
        layout.addWidget(recent_title, alignment=Qt.AlignmentFlag.AlignLeft)

        # Frame for Scroll Area (for better styling)
        scroll_frame = QFrame()
        scroll_frame.setStyleSheet("""
            QFrame {
                background-color: #29293a;
                border-radius: 6px;
                padding: 5px;
            }
        """)
        scroll_frame_layout = QVBoxLayout(scroll_frame)
        scroll_frame_layout.setContentsMargins(5, 5, 5, 5)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_layout.setSpacing(5)

        recent_projects = load_recent_projects()
        if recent_projects:
            for path in recent_projects:
                btn = QPushButton(path)
                btn.setStyleSheet("""
                    text-align: left;
                    padding-left: 10px;
                    height: 30px;
                    border: 1px solid #3a3a4f;
                    border-radius: 4px;
                """)
                btn.clicked.connect(lambda _, p=path: open_project_callback(p))
                scroll_layout.addWidget(btn)
        else:
            no_proj_label = QLabel("No recent projects found.")
            no_proj_label.setStyleSheet("color: #888;")
            scroll_layout.addWidget(no_proj_label)

        scroll_area.setWidget(scroll_content)
        scroll_frame_layout.addWidget(scroll_area)

        layout.addWidget(scroll_frame)

        self.setLayout(layout)