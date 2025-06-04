from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QTreeView, QMenu, QInputDialog, QMessageBox,
    QPushButton, QFileDialog, QApplication
)
from PyQt6.QtGui import QFileSystemModel, QCursor, QDrag, QIcon,QDesktopServices
from PyQt6.QtCore import QDir, Qt, QMimeData, QModelIndex, QUrl,pyqtSignal
import os
import shutil
from src.main_window.title_bar import TitleBar

class FileExplorer(QFrame):
    file_tree_changed = pyqtSignal()

    def __init__(self, file_open_callback, parent=None, title_bar = None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.file_open_callback = file_open_callback
        self.title_bar = title_bar

        self.root_path = os.getcwd()
        self.model = QFileSystemModel()
        self.setup_model()
        self.tree = QTreeView()
        self.setup_tree()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Кнопка открытия папки
        self.open_folder_button = QPushButton("📁 Open Project")
        self.open_folder_button.clicked.connect(self.open_folder)
        self.open_folder_button.setStyleSheet("""
            QPushButton { border: none; padding: 5px; }
            QPushButton:hover { background: #3a3a3a; }
        """)

        layout.addWidget(self.open_folder_button)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def setRootPath(self, path):
        if os.path.isdir(path):
            self.model.setRootPath(path)
            self.tree.setModel(self.model)
            self.tree.setRootIndex(self.model.index(path))

    def setup_model(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(self.root_path)
        self.model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files)
        self.model.setNameFilterDisables(False)

    def setup_tree(self):
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(self.root_path))
        self.tree.setHeaderHidden(True)
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)
        self.tree.doubleClicked.connect(lambda index: self.file_open_callback(self.model.filePath(index)))
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDropIndicatorShown(True)
        self.tree.setDefaultDropAction(Qt.DropAction.MoveAction)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory", self.root_path)
        if folder:
            self.set_root_folder(folder)

    def set_root_folder(self, folder_path):
        self.root_path = folder_path
        self.setup_model()                     
        self.tree.setModel(self.model)         
        self.tree.setRootIndex(self.model.index(self.root_path)) 

        if self.title_bar:
            self.title_bar.set_current_directory(folder_path) 

    def refresh_view(self):
        current_index = self.tree.rootIndex()
        self.tree.setRootIndex(QModelIndex())
        self.tree.setRootIndex(current_index)
        self.file_tree_changed.emit()

    def open_context_menu(self, position):
        index = self.tree.indexAt(position)
        if not index.isValid():
            file_path = self.root_path
        else:
            file_path = self.model.filePath(index)

        is_dir = os.path.isdir(file_path)

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #282c34;
                color: #abb2bf;
                selection-background-color: #3e4451;
                border: none;
            }
        """)
        new_folder_action = menu.addAction("📁 New Folder")
        new_file_action = menu.addAction("📄 New File")
        rename_action = menu.addAction("✏️ Rename")
        delete_action = menu.addAction("❌ Delete")
        copy_path_action = menu.addAction("📋 Copy Path")
        open_in_os_action = menu.addAction("📂 Open in Explorer")

        action = menu.exec(QCursor.pos())

        if action == new_folder_action:
            self.create_new_item(file_path, is_dir, folder=True)
        elif action == new_file_action:
            self.create_new_item(file_path, is_dir, folder=False)
        elif action == rename_action:
            self.rename_item(file_path)
        elif action == delete_action:
            self.delete_item(file_path)
        elif action == copy_path_action:
            clipboard = QApplication.clipboard()
            clipboard.setText(file_path)
        elif action == open_in_os_action:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def create_new_item(self, base_path, is_dir, folder=False):
        name, ok = QInputDialog.getText(self, "Create", "Enter name:")
        if not ok or not name:
            return

        target_dir = base_path if is_dir else os.path.dirname(base_path)
        full_path = os.path.join(target_dir, name)

        if os.path.exists(full_path):
            QMessageBox.warning(self, "Error", f"'{name}' already exists.")
            return

        try:
            if folder:
                os.makedirs(full_path)
            else:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write("")
            self.refresh_view()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def rename_item(self, old_path):
        name, ok = QInputDialog.getText(self, "Rename", "Enter new name:")
        if not ok or not name:
            return

        new_path = os.path.join(os.path.dirname(old_path), name)
        if os.path.exists(new_path):
            QMessageBox.warning(self, "Error", f"'{name}' already exists.")
            return

        try:
            os.rename(old_path, new_path)
            self.refresh_view()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def delete_item(self, path):
        if path == self.root_path:
            QMessageBox.warning(self, "Error", "You cannot delete the root folder.")
            return

        confirm = QMessageBox.question(
            self, "Delete", f"Are you sure you want to delete '{os.path.basename(path)}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                elif os.path.isfile(path):
                    os.remove(path)
                self.refresh_view()
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def startDrag(self, drop_actions):
        indexes = self.tree.selectedIndexes()
        if not indexes:
            return

        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(self.model.filePath(index)) for index in indexes if index.column() == 0]
        mime_data.setUrls(urls)

        drag = QDrag(self.tree)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)

    def dropEvent(self, event):
        source_path = event.mimeData().urls()[0].toLocalFile()
        dest_index = self.tree.indexAt(event.position().toPoint())
        if not dest_index.isValid():
            dest_dir = self.root_path
        else:
            dest_dir = self.model.filePath(dest_index)
            if os.path.isfile(dest_dir):
                dest_dir = os.path.dirname(dest_dir)

        if not os.path.exists(source_path):
            event.ignore()
            return

        try:
            if os.path.isdir(source_path):
                shutil.move(source_path, dest_dir)
            else:
                shutil.copy2(source_path, dest_dir)
            self.refresh_view()
            event.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
            event.ignore()