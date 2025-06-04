# themes.py

DARK_THEME = """
/* --- Твой текущий стиль --- */
/* --- Базовый фон --- */
QDialog, QWidget, QMainWindow {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 0.5px solid rgba(255, 255, 255, 0.01);
    border-radius: 1px;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12pt;
}

QDialog {
    background-color: #2d2d2d;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 5px;
}

/* --- Слайдер --- */
QSlider {
    background: #2d2d2d;
    border-radius: 5px;
    height: 10px;
}

QSlider::handle {
    background: #00b4ff;
    border-radius: 5px;
    width: 15px;
    height: 15px;
}

QSlider::handle:hover {
    background: #007acc;
}

QSlider::add-page {
    background: #404040;
    border-radius: 5px;
}

QSlider::sub-page {
    background: #1e1e1e;
    border-radius: 5px;
}

/* --- Кнопки в диалогах --- */
QDialogButtonBox {
    background-color: #2d2d2d;
    color: #cccccc;
    border-radius: 5px;
    padding: 5px;
}

QDialogButtonBox::button {
    background: #3a3a3a;
    color: #cccccc;
    border-radius: 5px;
    padding: 6px 12px;
    border: 1px solid #3c3c3c;
}

QDialogButtonBox::button:hover {
    background-color: #007acc;
    color: white;
}

/* --- Метки в окне со слайдером --- */
QLabel {
    color: #cccccc;
    font-size: 14px;
    padding: 10px;
}

/* --- Меню и контекстное меню --- */
QMenu {
    background-color: #2d2d2d;
    color: #cccccc;
    border: 1px solid #3c3c3c;
}

QMenu::item:selected {
    background-color: #007acc;
    color: #ffffff;
}

/* --- Панель вкладок --- */
QTabWidget::pane {
    border: none;
    background-color: #1e1e1e;
}

/* --- Вкладки --- */
QTabBar::tab {
    background: #2d2d2d;
    color: #cccccc;
    padding: 6px 14px;
    margin: 0px;
    border: none;
    font-weight: normal;
}

QTabBar::tab:selected {
    background: #1e1e1e;
    color: white;
    border-top: 2px solid #00b4ff;
}

QTabBar::tab:hover {
    background: #404040;
    color: #ffffff;
}

/* --- Скроллбары --- */
QScrollBar:vertical, QScrollBar:horizontal {
    background: #1e1e1e;
    width: 8px;
    height: 8px;
    margin: 2px;
    border: none;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #5a5a5a;
    min-height: 20px;
    border-radius: 7px;
}

QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
    border: none;
}

/* --- Выделение текста --- */
QPlainTextEdit::selection {
    background-color: #264f78;
    color: #ffffff;
}

"""

LIGHT_THEME = """
QDialog, QWidget, QMainWindow {
    background-color: #f0f0f0;
    color: #333333;
    border: none;
    font-family: Consolas, "Courier New", monospace;
    font-size: 12pt;
}

QMainWindow {
    background-color: qlineargradient(
        spread:pad,
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #ffffff,
        stop:1 #e0e0e0
    );
}

QDialog {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 10px;
}

QSlider {
    background: #dddddd;
    border-radius: 5px;
    height: 10px;
}

QSlider::handle {
    background: #007acc;
    border-radius: 5px;
    width: 15px;
    height: 15px;
}

QSlider::handle:hover {
    background: #005fa3;
}

QSlider::add-page {
    background: #bbbbbb;
    border-radius: 5px;
}

QSlider::sub-page {
    background: #eeeeee;
    border-radius: 5px;
}

QDialogButtonBox {
    background-color: #efefef;
    color: #333333;
    border-radius: 5px;
    padding: 5px;
}

QDialogButtonBox::button {
    background: #dddddd;
    color: #333333;
    border-radius: 5px;
    padding: 6px 12px;
    border: 1px solid #cccccc;
}

QDialogButtonBox::button:hover {
    background-color: #007acc;
    color: white;
}

QLabel {
    color: #333333;
    font-size: 14px;
    padding: 10px;
}

QMenu {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
}

QMenu::item:selected {
    background-color: #007acc;
    color: #ffffff;
}

QTabWidget::pane {
    border: none;
    background-color: #f9f9f9;
}

QTabBar::tab {
    background: #e0e0e0;
    color: #333333;
    padding: 6px 14px;
    margin: 0px;
    border: none;
    font-weight: normal;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: black;
    border-top: 2px solid #007acc;
}

QTabBar::tab:hover {
    background: #cccccc;
    color: #000000;
}

QScrollBar:vertical, QScrollBar:horizontal {
    background: #dddddd;
    width: 8px;
    height: 8px;
    margin: 2px;
    border: none;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #aaaaaa;
    min-height: 20px;
    border-radius: 7px;
}

QScrollBar::add-line, QScrollBar::sub-line {
    background: none;
    border: none;
}

QPlainTextEdit::selection {
    background-color: #b3d7ff;
    color: #000000;
}
"""