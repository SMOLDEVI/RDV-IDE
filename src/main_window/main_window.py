import asyncio
import os
import sys
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from pathlib import Path
from src.customization.themes import DARK_THEME, LIGHT_THEME
from src.editor.editor import CodeEditor
from src.file_manager.file_manager import FileExplorer
from src.terminal.terminal import WindowsTerminal
from src.main_window.title_bar import TitleBar
from src.customization.slider_menu import SliderWindow
from src.debbuger.debugger_widget import DebuggerWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_theme = "dark"
        self.tab_files = {}
        self.max_recent_projects = 5
        self.recent_projects_path = "src/recent/recent_projects.json"
        self.recent_projects = []
        self.is_modified = False
        self.original_text = ""
        self.recent_projects_menu = None
        self.debugger_panel = DebuggerWidget()
        self.debugger_panel.hide()
        self.dap_client = None  
        self.debug_launcher = None

        self.load_recent_projects()
        self.init_ui()

    def init_ui(self):
        self.setWindowIcon(QIcon("src/ico.png"))
        self.resize(1000, 700)
        self.setup_font_and_style()
        self.setup_menu()
        self.setup_main_layout()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.title_bar = TitleBar(self, self.menuBar())
        self.title_bar.open_file_requested.connect(self.open_file_in_tab)

        central_widget = QWidget()
        central_layout = QVBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        central_layout.addWidget(self.title_bar)

        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.addWidget(self.centralWidget())
        central_layout.addWidget(main_splitter)
        central_widget.setLayout(central_layout)
        main_splitter.addWidget(self.debugger_panel)
        self.setCentralWidget(central_widget)
        self.setMouseTracking(True)
        self.is_dragging = False
        self.drag_position = QPoint()
        self.show()

    def setup_font_and_style(self):
        self.window_font = QFont("Courier New", 14)
        self.setFont(self.window_font)
        try:
            self.setStyleSheet(DARK_THEME)
        except FileNotFoundError:
            pass

    def setup_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("📁File")
        view_menu = menu_bar.addMenu("🌝View")
        options_menu = menu_bar.addMenu("⚙ Options")

        edit_menu = menu_bar.addMenu("🛠Edit")

        debug_menu = menu_bar.addMenu("🐞Debug")
        start_debug_action = QAction("Toggle Debug", self)
        start_debug_action.setShortcut("F5")
        start_debug_action.triggered.connect(self.start_debugging)
        debug_menu.addAction(start_debug_action)

        format_action = QAction("Format", self)
        format_action.setShortcut("Ctrl+Alt+F")
        format_action.triggered.connect(self.format_current_file)
        edit_menu.addAction(format_action)

        toggle_theme_action = QAction("Toggle Theme", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        options_menu.addAction(toggle_theme_action)

        change_transparency_action = QAction("Set Transparency", self)
        change_transparency_action.triggered.connect(
            self.show_transparency_window)
        options_menu.addAction(change_transparency_action)

        actions_view_menu = [
            ("Toggle Sidebar", "Ctrl+E", self.toggle_sidebar),
            ("Toggle Terminal", "F4", self.toggle_terminal)
        ]

        actions_options_menu = [
            ("Toggle Transparency", "Ctrl+T", self.toggle_transparency)
        ]

        actions = [
            ("New", "Ctrl+N", self.new_file),
            ("Open", "Ctrl+O", self.open_file),
            ("Save", "Ctrl+S", self.save_file),
            ("Save As", "Ctrl+Shift+S", self.save_file_as_current),
            ("Exit", "Ctrl+Q", self.exit_app)
        ]

        for text, shortcut, handler in actions_options_menu:
            action = QAction(text, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(handler)
            options_menu.addAction(action)

        for text, shortcut, handler in actions_view_menu:
            act = QAction(text, self)
            act.setShortcut(QKeySequence(shortcut))
            act.triggered.connect(handler)
            view_menu.addAction(act)

        for text, shortcut, handler in actions:
            action = QAction(text, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(handler)
            file_menu.addAction(action)

        # Добавляем пункт Recent Projects
        self.recent_projects_menu = file_menu.addMenu("Recent Projects")
        self.update_recent_projects_menu()

    def setup_main_layout(self):
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        central_widget = QWidget()
        central_layout = QHBoxLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)

        self.setup_sidebar(central_layout)

        self.tab_view = QTabWidget()
        self.tab_view.setTabsClosable(True)
        self.tab_view.tabCloseRequested.connect(self.close_tab)
        central_layout.addWidget(self.tab_view)

        central_widget.setLayout(central_layout)

        self.terminal = WindowsTerminal(parent=self, tab_view=self.tab_view)
        self.terminal.setMinimumHeight(250)

        main_splitter.addWidget(central_widget)
        main_splitter.addWidget(self.terminal)
        main_splitter.setSizes([700, 200])

        self.setCentralWidget(main_splitter)

    def setup_sidebar(self, layout):
        self.file_explorer = FileExplorer(
            file_open_callback=self.load_file_to_editor)
        layout.addWidget(self.file_explorer)

    def toggle_sidebar(self):
        self.file_explorer.setVisible(not self.file_explorer.isVisible())

    def show_transparency_window(self):
        slider_window = SliderWindow(self)
        slider_window.exec()

    def toggle_terminal(self):
        self.terminal.setVisible(not self.terminal.isVisible())

    def new_file(self):
        editor = CodeEditor(file_path=None)
        editor.original_text = ""
        editor.document().contentsChanged.connect(
            lambda ed=editor: self.update_tab_title(ed))
        index = self.tab_view.addTab(editor, "New File")
        self.tab_view.setCurrentIndex(index)
        self.tab_files[index] = None
        self.setWindowTitle("RDV.IDE - New File")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*.*)")
        if file_path:
            project_dir = os.path.dirname(file_path)
            self.add_recent_project(project_dir)
            self.load_file_to_editor(file_path)

    def open_file_from_tree(self, index):
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.load_file_to_editor(file_path)

    def load_file_to_editor(self, file_path):
        for index, path in self.tab_files.items():
            if path == file_path:
                self.tab_view.setCurrentIndex(index)
                return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            editor = CodeEditor(file_path=file_path)
            editor.document().contentsChanged.connect(
                lambda editor=editor: self.update_tab_title(editor))
            editor.original_text = content
            editor.setPlainText(content)
            editor.set_lexer_by_filename(file_path)
            index = self.tab_view.addTab(editor, Path(file_path).name)
            self.tab_view.setCurrentIndex(index)
            self.tab_files[index] = file_path
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot open file: {str(e)}")

    def save_file(self):
        current_index = self.tab_view.currentIndex()
        if current_index == -1:
            return
        editor = self.tab_view.widget(current_index)
        if not isinstance(editor, CodeEditor):
            return
        if self.tab_files.get(current_index) is None:
            self.save_file_as(current_index)
        else:
            self.save_to_file(
                self.tab_files[current_index], editor.toPlainText())

    def save_file_as_current(self):
        current_index = self.tab_view.currentIndex()
        if current_index != -1:
            self.save_file_as(current_index)

    def save_file_as(self, tab_index):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "All Files (*.*)")
        if file_path:
            editor = self.tab_view.widget(tab_index)
            self.save_to_file(file_path, editor.toPlainText())
            self.tab_files[tab_index] = file_path
            self.tab_view.setTabText(tab_index, Path(file_path).name)

    def save_to_file(self, file_path, content):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            current_index = self.tab_view.currentIndex()
            editor = self.tab_view.widget(current_index)
            if isinstance(editor, CodeEditor):
                editor.original_text = content  # сохраняем текущее состояние как "неизменное"
                self.update_tab_title(editor)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot save file: {str(e)}")

    def close_tab(self, index):
        widget = self.tab_view.widget(index)
        if widget:
            widget.deleteLater()
        if index in self.tab_files:
            del self.tab_files[index]
        self.tab_view.removeTab(index)
        if self.tab_view.count() == 0:
            self.setWindowTitle("RDV.IDE")

    def exit_app(self):
        QCoreApplication.quit()
        loop = asyncio.get_event_loop()
        loop.stop()

    def toggle_transparency(self):
        current_opacity = self.windowOpacity()
        new_opacity = 0.95 if current_opacity == 1.0 else 1.0
        self.setWindowOpacity(new_opacity)

    def load_recent_projects(self):
        if os.path.exists(self.recent_projects_path):
            try:
                with open(self.recent_projects_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.recent_projects = data.get("recent_projects", [])
            except Exception as e:
                print("Ошибка загрузки истории:", e)
                self.recent_projects = []

    def save_recent_projects(self):
        try:
            with open(self.recent_projects_path, 'w', encoding='utf-8') as f:
                json.dump(
                    {"recent_projects": self.recent_projects}, f, indent=2)
        except Exception as e:
            print("Ошибка сохранения истории:", e)

    def add_recent_project(self, path):
        if path in self.recent_projects:
            self.recent_projects.remove(path)
        self.recent_projects.insert(0, path)
        if len(self.recent_projects) > self.max_recent_projects:
            self.recent_projects.pop()
        self.save_recent_projects()
        self.update_recent_projects_menu()

    def clear_recent_projects(self):
        self.recent_projects.clear()
        self.save_recent_projects()
        self.update_recent_projects_menu()

    def update_recent_projects_menu(self):
        self.recent_projects_menu.clear()
        if not self.recent_projects:
            no_action = QAction("No recent projects", self)
            no_action.setEnabled(False)
            self.recent_projects_menu.addAction(no_action)
        else:
            for path in self.recent_projects:
                action = QAction(path, self)
                action.triggered.connect(
                    lambda checked, p=path: self.open_recent_project(p))
                self.recent_projects_menu.addAction(action)
            self.recent_projects_menu.addSeparator()
            clear_action = QAction("Clear History", self)
            clear_action.triggered.connect(self.clear_recent_projects)
            self.recent_projects_menu.addAction(clear_action)

    def open_recent_project(self, project_path):
        if os.path.isdir(project_path):
            self.file_explorer.setRootPath(project_path)
            self.setWindowTitle(f"RDV.IDE - {project_path}")
            self.add_recent_project(project_path)
        else:
            QMessageBox.warning(
                self, "Error", f"The project folder does not exist:\n{project_path}")
            self.remove_recent_project(project_path)

    def remove_recent_project(self, path):
        if path in self.recent_projects:
            self.recent_projects.remove(path)
            self.save_recent_projects()
            self.update_recent_projects_menu()

    def toggle_theme(self):
        if self.current_theme == "dark":
            self.setStyleSheet(LIGHT_THEME)
            self.current_theme = "light"
        else:
            self.setStyleSheet(DARK_THEME)
            self.current_theme = "dark"

    def format_current_file(self):
        current_index = self.tab_view.currentIndex()
        if current_index == -1:
            return

        editor = self.tab_view.widget(current_index)
        if isinstance(editor, CodeEditor):
            editor.format_code()

    def update_tab_title(self, editor):
        index = self.tab_view.indexOf(editor)
        if index == -1:
            return

        file_name = os.path.basename(
            editor.file_path) if editor.file_path else "New File"
        current_text = editor.toPlainText()
        is_modified = current_text != editor.original_text

        if is_modified:
            self.tab_view.setTabText(index, f"{file_name}*")
        else:
            self.tab_view.setTabText(index, file_name)

        editor.is_modified = is_modified

    def open_file_in_tab(self, file_path: str):
        
        for i in range(self.tab_view.count()):
            editor = self.tab_view.widget(i)
            if hasattr(editor, "file_path") and editor.file_path == file_path:
                self.tab_view.setCurrentIndex(i)
                return

        editor = CodeEditor(file_path=file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        editor.setPlainText(content)
        editor.set_lexer_by_filename(file_path)

        filename = os.path.basename(file_path)
        self.tab_view.addTab(editor, filename)
        self.tab_view.setCurrentWidget(editor)
    
    def start_debugging(self):
        if self.dap_client or (self.debug_launcher and self.debug_launcher.is_running()):
            self.debug_output.append("[Предупреждение] Отладка уже запущена.")
            return
        current_index = self.tab_view.currentIndex()
        if current_index == -1:
            return
        current_index = self.tab_view.currentIndex()
        editor = self.tab_view.widget(current_index)

        if not isinstance(editor, CodeEditor) or not editor.file_path:
            QMessageBox.warning(self, "Ошибка", "Файл не сохранён или не является Python-файлом.")
            return

        if self.debugger_panel.isVisible():
            self.debugger_panel.hide()
        else:
            self.debugger_panel.set_current_editor(editor)
            self.debugger_panel.show()
            self.debugger_panel.start_debugging()  # <<< Запуск отладки