# -*- coding: utf-8 -*-
"""
Editor principal con soporte para resaltado de sintaxis y funcionalidades de edicion.
"""

import tkinter as tk
from editor.syntax.vb_highlighter import VBHighlighter
from config import COLOR_FONDO, COLOR_TEXTO, COLOR_CURSOR, COLOR_SELECCION, FUENTE_EDITOR


class TextEditor(tk.Text):
    """
    Widget de texto con resaltado para VBS/VB.
    """
    def __init__(self, master, **kwargs):
        self._user_modified = False
        super().__init__(
            master,
            undo=True,
            bg=COLOR_FONDO,
            fg=COLOR_TEXTO,
            font=FUENTE_EDITOR,
            insertbackground=COLOR_CURSOR,
            selectbackground=COLOR_SELECCION,
            wrap="none",
            **kwargs
        )

        self.configure(blockcursor=False, insertontime=600, insertofftime=300)
        self.highlighter = VBHighlighter(self)
        self._highlight_after_id = None

        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<Key>", self._schedule_highlight_fast)
        self.bind("<Key>", self._on_user_key, add=True)
        self.bind("<ButtonRelease-1>", self._schedule_highlight)
        self.bind("<<Paste>>", self._do_highlight_now)
        self.bind("<<Cut>>", self._do_highlight_now)
        self.bind("<<Undo>>", self._do_highlight_now)
        self.bind("<<Redo>>", self._do_highlight_now)
        self.bind("<<Modified>>", self._schedule_highlight_fast)

        self.bind("<KeyRelease>", lambda e: self.event_generate("<<Change>>"), add=True)
        self.bind("<MouseWheel>", lambda e: self.event_generate("<<Change>>"), add=True)

        self._do_highlight()

    def _on_user_key(self, event=None):
        if event and event.keysym not in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"):
            self._user_modified = True

    def _on_key_release(self, event=None):
        """Maneja el evento de soltar tecla - highlight rapido."""
        # Teclas que cambian contenido significativamente
        if event and event.keysym in ('BackSpace', 'Delete', 'Return', 'quotedbl', 'apostrophe'):
            self._do_highlight_now()
        else:
            self._schedule_highlight_fast()

    def _schedule_highlight_fast(self, event=None):
        if self._highlight_after_id is not None:
            self.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.after(1500, self._do_highlight)

    def _schedule_highlight(self, event=None):
        if self._highlight_after_id is not None:
            self.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.after(1500, self._do_highlight)

    def _do_highlight_now(self, event=None):
        """Ejecuta el resaltado inmediatamente sin espera."""
        if self._highlight_after_id is not None:
            self.after_cancel(self._highlight_after_id)
            self._highlight_after_id = None
        self._do_highlight()
        self.after(50, self._do_highlight)

    def _do_highlight(self):
        """Ejecuta el resaltado ya con el texto estable."""
        self._highlight_after_id = None
        self.highlighter.highlight()
        self.event_generate("<<Change>>")
        if not self._user_modified:
            self.edit_modified(False)

    def set_content(self, text: str):
        # Strip newlines iniciales/finales que causan desfase en el highlighter
        text = text.strip('\n')
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self._do_highlight()
        self._user_modified = False
