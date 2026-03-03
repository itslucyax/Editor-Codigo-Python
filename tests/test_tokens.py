# -*- coding: utf-8 -*-
"""Test de Pygments tokenization"""
from pygments import lex
from pygments.lexers import VbNetLexer
from pygments.token import Token

lexer = VbNetLexer()
code = """' Comentario
Sub Main()
    Dim x As Integer
    x = 10
    MsgBox "Hola"
End Sub
"""

print("=== TOKENS DE PYGMENTS ===")
for token, content in lex(code, lexer):
    if content.strip():  # Solo mostrar tokens con contenido visible
        print(f"{str(token):40} -> '{content}'")
