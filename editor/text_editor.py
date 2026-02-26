"""
Editor principal con soporte para resaltado de sintaxis y funcionalidades de edicion.
"""

import tkinter as tk
from editor.syntax.vb_highlighter import VBHighlighter
from config import COLOR_FONDO, COLOR_TEXTO, FUENTE_EDITOR

class TextEditor(tk.Text):
    """
    Widget de texto con resaltado para VBS/VB.
    """
    def __init__(self, master, **kwargs):
        super().__init__(
            master, undo=True, 
            bg=COLOR_FONDO, fg=COLOR_TEXTO, 
            font=FUENTE_EDITOR, insertbackground="white",
            selectbackground="#264f78",  # Seleccion tipo VS Code
            tabs=("1c"),
            spacing3=4,                   # Espaciado entre líneas
            wrap="none",                  # Sin wrap
            **kwargs
        )
        self.highlighter = VBHighlighter(self)
        self.bind("<KeyRelease>", self._highlight_event)
        self.bind("<ButtonRelease-1>", self._highlight_event)
        self._highlight_event()  # Inicial

    def _highlight_event(self, event=None):
        code = self.get("1.0", "end-1c")
        self.highlighter.highlight(code)
        # Disparar evento para LineNumbers, si existe
        self.event_generate("<<Change>>")

    def set_content(self, text):
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self._highlight_event()
