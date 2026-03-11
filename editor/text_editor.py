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
    def __init__(self, master, record=None, key_columns=None, content_column=None, editable_columns=None):
        super().__init__(master, bg=COLOR_SIDEBAR_BG, width=self.WIDTH)
        self.pack_propagate(False)  # Mantener ancho fijo

        self.record = record or {}
        self.key_columns = [c.upper() for c in (key_columns or [])]
        self.content_column = content_column.upper()
        self.editable_columns = [c.upper() for c in (editable_columns or [])]

        # Separar campos en categorías
        self._categorize_fields()

        # Referencias a widgets para obtener valores editados
        self.field_widgets = {}  # {nombre_campo: widget}

        # Scrollbar + Canvas para scroll vertical
        self._scrollbar = tk.Scrollbar(self, orient="vertical")
        self._scrollbar.pack(side="right", fill="y")

        self._canvas = tk.Canvas(
            self, bg=COLOR_SIDEBAR_BG, highlightthickness=0,
            yscrollcommand=self._scrollbar.set
        )
        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.config(command=self._canvas.yview)

        # Frame interior donde se construye el contenido
        self._inner = tk.Frame(self._canvas, bg=COLOR_SIDEBAR_BG)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw"
        )

        self._inner.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Scroll con rueda del ratón solo cuando el cursor está encima
        self._canvas.bind("<Enter>", lambda e: self._canvas.bind_all("<MouseWheel>", self._on_mousewheel))
        self._canvas.bind("<Leave>", lambda e: self._canvas.unbind_all("<MouseWheel>"))

        self._build_ui()
    def _on_canvas_configure(self, event=None):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

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
