from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor
from PyQt6.QtCore import QSize 
from pygments.token import Token, Name, Keyword, String, Number, Operator, Punctuation, Comment, Literal, Generic


class ReliableSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.lexer = None
        self.styles = {
            Token.Keyword: self.create_format('#569CD6', bold=True),         # Голубые ключевые слова
            Token.Keyword.Namespace: self.create_format('#4EC9B0'),           # Например, 'import'
            Token.Name: self.create_format('#9CDCFE'),                        # Переменные
            Token.Name.Function: self.create_format('#DCDCAA'),               # Функции
            Token.Name.Class: self.create_format('#4EC9B0', bold=True),       # Классы
            Token.Name.Decorator: self.create_format('#C586C0'),              # Декораторы
            Token.String: self.create_format('#CE9178'),                      # Строки
            Token.String.Doc: self.create_format('#608B4E'),                  # Docstrings / многострочные строки
            Token.Number: self.create_format('#B5CEA8'),                      # Числа
            Token.Operator: self.create_format('#D4D4D4'),                    # Операторы (+, -, = и т.п.)
            Token.Punctuation: self.create_format('#D4D4D4'),                 # Знаки препинания
            Token.Comment: self.create_format('#6A9955', italic=True),        # Комментарии
            Token.Comment.Preproc: self.create_format('#C586C0'),             # Препроцессоры (#include, #define)
            Token.Literal: self.create_format('#D4D4D4'),
            Token.Literal.Date: self.create_format('#CE9178'),
            Token.Generic.Heading: self.create_format('#569CD6', bold=True),
            Token.Generic.Subheading: self.create_format('#569CD6', bold=True),
            Token.Generic.Deleted: self.create_format('#CE9178'),
            Token.Generic.Inserted: self.create_format('#569CD6'),
            Token.Generic.Error: self.create_format('#F44747'),
            Token.Generic.Emph: self.create_format(italic=True),
            Token.Generic.Strong: self.create_format(bold=True),
            Token.Generic.Traceback: self.create_format('#DCDCAA'),
            Token.Generic.Output: self.create_format('#608B4E'),
        }

        self.default_format = self.create_format('#D4D4D4') 

    def create_format(self, color=None, bold=False, italic=False):
        fmt = QTextCharFormat()
        if color:
            fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        return fmt

    def highlightBlock(self, text):
        if not self.lexer:
            return
            
        try:
            tokens = list(self.lexer.get_tokens(text))
        except Exception as e:
            print("Lexer error:", str(e))
            return
            
        pos = 0
        for token_type, value in tokens:
            length = len(value)
            if not length:
                continue
                
            # Найдём совпадение стиля
            fmt = self.default_format
            current_type = token_type
            while current_type not in self.styles and current_type.parent:
                current_type = current_type.parent

            if current_type in self.styles:
                fmt = self.styles[current_type]
            
            self.setFormat(pos, length, fmt)
            pos += length

    def set_lexer(self, lexer):
        self.lexer = lexer
        self.rehighlight()  # Обновляем подсветку при смене лексера