"""
Editor principal con soporte para resaltado de sintaxis y funcionalidades de edición.
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
            master,
            undo=True,
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO,
            font=FUENTE_EDITOR,
            insertbackground="white",
            selectbackground="#264f78",  # Selección tipo VS Code
            tabs=("1c"),
            spacing3=4,                 # Espaciado entre líneas
            wrap="none",                # Sin wrap
            **kwargs
        )

        self.highlighter = VBHighlighter(self)

        # Binds principales para refrescar resaltado/estado
        self.bind("<KeyRelease>", self._highlight_event)
        self.bind("<ButtonRelease-1>", self._highlight_event)

        # Binds extra para asegurar que se redibujan números de línea en acciones clave
        for key in ["<Return>", "<BackSpace>", "<Delete>"]:
            self.bind(key, self._trigger_line_update)

        self._highlight_event()  # Inicial

    def _trigger_line_update(self, event=None):
        """Dispara un evento personalizado para que LineNumbers se redibuje."""
        self.event_generate("<<Change>>")

    def _highlight_event(self, event=None):
        code = self.get("1.0", "end-1c")
        self.highlighter.highlight(code)

        # Disparar evento para LineNumbers / barra de estado
        self.event_generate("<<Change>>")

    def set_content(self, text):
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self._highlight_event()