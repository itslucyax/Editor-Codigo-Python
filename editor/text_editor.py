# -*- coding: utf-8 -*-
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
            master,
            undo=True,
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO,
            font=FUENTE_EDITOR,
            insertbackground="white",
            selectbackground="#264f78",  # Seleccion tipo VS Code
            wrap="none",                 # Sin wrap
            **kwargs
        )

        self.highlighter = VBHighlighter(self)

        # Debounce: id del after pendiente
        self._highlight_after_id = None

        # Eventos que cambian contenido - capturamos todos los posibles
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<Key>", self._schedule_highlight_fast)
        self.bind("<ButtonRelease-1>", self._schedule_highlight)
        self.bind("<<Paste>>", self._do_highlight_now)
        self.bind("<<Cut>>", self._do_highlight_now)
        self.bind("<<Undo>>", self._do_highlight_now)
        self.bind("<<Redo>>", self._do_highlight_now)
        self.bind("<<Modified>>", self._schedule_highlight_fast)

        # Para que numeros de linea / status se actualicen siempre
        self.bind("<KeyRelease>", lambda e: self.event_generate("<<Change>>"), add=True)
        self.bind("<MouseWheel>", lambda e: self.event_generate("<<Change>>"), add=True)

        # Primer pintado
        self._do_highlight()

    def _on_key_release(self, event=None):
        """Maneja el evento de soltar tecla - highlight rapido."""
        # Teclas que cambian contenido significativamente
        if event and event.keysym in ('BackSpace', 'Delete', 'Return', 'quotedbl', 'apostrophe'):
            self._do_highlight_now()
        else:
            self._schedule_highlight_fast()

    def _schedule_highlight_fast(self, event=None):
        """Programa el resaltado con retraso minimo (20ms)."""
        if self._highlight_after_id is not None:
            self.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.after(20, self._do_highlight)

    def _schedule_highlight(self, event=None):
        """Programa el resaltado con un pequeno retraso para evitar repintar en cada tecla."""
        if self._highlight_after_id is not None:
            self.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.after(50, self._do_highlight)

    def _do_highlight_now(self, event=None):
        """Ejecuta el resaltado inmediatamente sin espera."""
        if self._highlight_after_id is not None:
            self.after_cancel(self._highlight_after_id)
            self._highlight_after_id = None
        self._do_highlight()

    def _do_highlight(self):
        """Ejecuta el resaltado ya con el texto estable."""
        self._highlight_after_id = None
        self.highlighter.highlight()
        self.event_generate("<<Change>>")

    def set_content(self, text: str):
        # Strip newlines iniciales/finales que causan desfase en el highlighter
        text = text.strip('\n')
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self._do_highlight()  # Highlight inmediato al cargar contenido
