"""
Modulo con clase para aplicar resaltado de sintaxis VBScript/VB usando Pygments.
"""

from pygments.lexers import VbNetLexer
from pygments.token import Token
from config import (
    COLOR_KEYWORD, COLOR_STRING, COLOR_COMMENT,
    COLOR_NUMBER, COLOR_BUILTIN, COLOR_TEXTO
)

# Diccionario de mapeo: tipo de token a nombre de tag y color
TOKEN_TAGS = {
    Token.Keyword: ("keyword", COLOR_KEYWORD),
    Token.Literal.String: ("string", COLOR_STRING),
    Token.Comment: ("comment", COLOR_COMMENT),
    Token.Literal.Number: ("number", COLOR_NUMBER),
    Token.Name.Builtin: ("builtin", COLOR_BUILTIN),
}

class VBHighlighter:
    """
    Clase de utilidad para aplicar colores en un Text widget según el token de Pygments
    """
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.lexer = VbNetLexer()
        # Definir los tags de colores
        for tag, color in [("keyword", COLOR_KEYWORD), 
                           ("string", COLOR_STRING), 
                           ("comment", COLOR_COMMENT), 
                           ("number", COLOR_NUMBER),
                           ("builtin", COLOR_BUILTIN)]:
            self.text_widget.tag_configure(tag, foreground=color)
        self.text_widget.tag_configure("normal", foreground=COLOR_TEXTO)

    def highlight(self, code: str):
        """Aplica resaltado al codigo en el Text widget."""
        # Borrar colores antiguos
        for tag in TOKEN_TAGS.values():
            self.text_widget.tag_remove(tag[0], "1.0", "end")
        self.text_widget.tag_remove("normal", "1.0", "end")

        from pygments import lex
        for token, content in lex(code, self.lexer):
            tag, _ = TOKEN_TAGS.get(token, ("normal", COLOR_TEXTO))
            if content:
                start = self.text_widget.search(content, "1.0", stopindex="end")
                while start:
                    end = f"{start}+{len(content)}c"
                    self.text_widget.tag_add(tag, start, end)
                    # Buscar la siguiente aparición después de end
                    new_start = self.text_widget.search(content, end, stopindex="end")
                    if not new_start:
                        break
                    start = new_start
