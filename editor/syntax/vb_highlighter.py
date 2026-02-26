# -*- coding: utf-8 -*-
"""
Modulo con clase para aplicar resaltado de sintaxis VBScript/VB usando Pygments.
Estilo VS Code con diferenciacion de colores mejorada.
"""
from __future__ import annotations

from pygments import lex
from pygments.lexers.basic import VBScriptLexer
from pygments.token import Token
from config import (
    COLOR_KEYWORD,
    COLOR_STRING,
    COLOR_COMMENT,
    COLOR_NUMBER,
    COLOR_BUILTIN,
    COLOR_TEXTO,
    COLOR_FUNCTION,
    COLOR_CLASS,
    COLOR_VARIABLE,
    COLOR_CONSTANT,
    COLOR_PUNCTUATION,
    COLOR_OPERADOR,
)


def _token_to_tag(token) -> str:
    """
    Devuelve el tag Tkinter a usar para un token de Pygments.
    Mapeo completo de tokens para lograr colores estilo VS Code.
    """
    # Comentarios (verde)
    if token in Token.Comment:
        return "comment"
    
    # Palabras clave (azul)
    if token in Token.Keyword:
        return "keyword"
    
    # Cadenas de texto (naranja/salmon)
    if token in Token.Literal.String:
        return "string"
    
    # Numeros (verde claro)
    if token in Token.Literal.Number:
        return "number"
    
    # Funciones built-in (amarillo)
    if token in Token.Name.Builtin:
        return "builtin"
    
    # Nombres de funciones (amarillo)
    if token in Token.Name.Function:
        return "function"
    
    # Nombres de clases/tipos (verde turquesa)
    if token in Token.Name.Class:
        return "class"
    if token in Token.Name.Type:
        return "class"
    
    # Variables y otros nombres (azul claro)
    if token in Token.Name.Variable:
        return "variable"
    if token in Token.Name.Attribute:
        return "variable"
    
    # Constantes (azul cyan)
    if token in Token.Name.Constant:
        return "constant"
    
    # Operadores
    if token in Token.Operator:
        return "operator"
    
    # Puntuacion (gris)
    if token in Token.Punctuation:
        return "punctuation"
    
    # Otros nombres (resaltarlos como variables para mejor visual)
    if token in Token.Name:
        return "variable"
    
    return "normal"


class VBHighlighter:
    """
    Aplica resaltado de sintaxis a un tk.Text usando tags.
    Configurado con colores estilo VS Code para maxima diferenciacion visual.
    """
    
    # Lista de todos los tags usados
    TAGS = (
        "keyword", "string", "comment", "number", "builtin", 
        "function", "class", "variable", "constant", 
        "operator", "punctuation", "normal"
    )
    
    def __init__(self, text_widget):
        self.text_widget = text_widget
        # Usar VBScriptLexer para mejor compatibilidad con código VBS
        self.lexer = VBScriptLexer()
        
        # Definir los tags de colores con estilo VS Code
        self.text_widget.tag_configure("keyword", foreground=COLOR_KEYWORD)
        self.text_widget.tag_configure("string", foreground=COLOR_STRING)
        self.text_widget.tag_configure("comment", foreground=COLOR_COMMENT, font=("Consolas", 12, "italic"))
        self.text_widget.tag_configure("number", foreground=COLOR_NUMBER)
        self.text_widget.tag_configure("builtin", foreground=COLOR_BUILTIN)
        self.text_widget.tag_configure("function", foreground=COLOR_FUNCTION)
        self.text_widget.tag_configure("class", foreground=COLOR_CLASS)
        self.text_widget.tag_configure("variable", foreground=COLOR_VARIABLE)
        self.text_widget.tag_configure("constant", foreground=COLOR_CONSTANT)
        self.text_widget.tag_configure("operator", foreground=COLOR_OPERADOR)
        self.text_widget.tag_configure("punctuation", foreground=COLOR_PUNCTUATION)
        self.text_widget.tag_configure("normal", foreground=COLOR_TEXTO)

    def highlight(self, code: str = None) -> None:
        """
        Tokeniza el contenido actual del widget y aplica tags.
        Usa posiciones linea.columna para evitar problemas con offsets.
        """
        # Quitar TODOS los tags anteriores primero
        for tag in self.TAGS:
            self.text_widget.tag_remove(tag, "1.0", "end")

        # Obtener el texto directamente del widget para evitar discrepancias
        text = self.text_widget.get("1.0", "end-1c")
        
        if not text:
            return

        # Posicion actual: linea (1-based), columna (0-based)
        line = 1
        col = 0

        for token, content in lex(text, self.lexer):
            if not content:
                continue

            tag = _token_to_tag(token)
            
            # Calcular posicion inicial
            start_index = f"{line}.{col}"
            
            # Avanzar por el contenido del token
            for char in content:
                if char == '\n':
                    line += 1
                    col = 0
                else:
                    col += 1
            
            # Posicion final
            end_index = f"{line}.{col}"
            
            self.text_widget.tag_add(tag, start_index, end_index)
        
        # Asegurar que los tags de sintaxis tienen prioridad sobre normal
        for tag in self.TAGS:
            if tag != "normal":
                self.text_widget.tag_raise(tag, "normal")
