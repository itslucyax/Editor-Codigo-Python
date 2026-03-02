# -*- coding: utf-8 -*-
"""
Barra de búsqueda fija en la parte superior del editor.

Estilo clásico de aplicación de escritorio: siempre visible,
con campo de texto y botón "Buscar" al lado.
Resalta las coincidencias y permite navegar entre ellas.
"""

import tkinter as tk
from config import (
    COLOR_SIDEBAR_BG,
    COLOR_BARRA_ESTADO_BG,
    COLOR_BARRA_ESTADO_FG,
)


class FixedSearchBar(tk.Frame):
    """
    Barra de búsqueda fija (siempre visible) en la parte superior.
    
    Contiene un campo de texto y un botón "Buscar".
    Resalta todas las coincidencias y salta a cada una.
    """

    _TAG = "search_highlight"
    _TAG_CURRENT = "search_current"

    def __init__(self, parent, text_widget: tk.Text = None):
        super().__init__(parent, bg=COLOR_SIDEBAR_BG, padx=6, pady=4)
        self.text_widget = text_widget
        self._matches: list[str] = []
        self._current_idx = -1

        # --- Layout ---
        tk.Label(
            self,
            text="Buscar:",
            bg=COLOR_SIDEBAR_BG,
            fg="#000000",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 4))

        self.search_var = tk.StringVar()
        self.entry = tk.Entry(
            self,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#000000",
            insertbackground="#000000",
            relief="solid",
            borderwidth=1,
            width=25,
        )
        self.entry.pack(side="left", padx=(0, 4))
        self.entry.bind("<Return>", lambda e: self.find_next())
        self.entry.bind("<Shift-Return>", lambda e: self.find_prev())

        # Botón Buscar
        self._make_btn("Buscar", self.find_next)
        self._make_btn("▲", self.find_prev)
        self._make_btn("▼", self.find_next)

        # Contador de resultados
        self.match_label = tk.Label(
            self,
            text="",
            bg=COLOR_SIDEBAR_BG,
            fg="#555555",
            font=("Segoe UI", 8),
        )
        self.match_label.pack(side="left", padx=(6, 0))

    def _make_btn(self, text, command):
        """Crea un botón con estilo consistente."""
        btn = tk.Button(
            self,
            text=text,
            command=command,
            bg="#E0E0E0",
            fg="#000000",
            activebackground="#C0C0C0",
            activeforeground="#000000",
            relief="raised",
            font=("Segoe UI", 8),
            padx=6,
            pady=1,
        )
        btn.pack(side="left", padx=(0, 2))
        return btn

    def set_text_widget(self, text_widget: tk.Text):
        """Conecta el widget de texto al buscador (si no se pasó en el constructor)."""
        self.text_widget = text_widget
        # Configurar tags de resaltado
        self.text_widget.tag_configure(self._TAG, background="#FFFF00", foreground="#000000")
        self.text_widget.tag_configure(self._TAG_CURRENT, background="#FF8C00", foreground="#FFFFFF")

    def find_next(self):
        """Busca la siguiente coincidencia."""
        if not self.text_widget:
            return
        query = self.search_var.get()
        if not query:
            self._clear()
            return

        # Re-buscar si cambió el texto
        if not self._matches or self._last_query != query:
            self._find_all()

        if not self._matches:
            return

        self._current_idx = (self._current_idx + 1) % len(self._matches)
        self._highlight_current()

    def find_prev(self):
        """Busca la coincidencia anterior."""
        if not self.text_widget:
            return
        query = self.search_var.get()
        if not query:
            self._clear()
            return

        if not self._matches or self._last_query != query:
            self._find_all()

        if not self._matches:
            return

        self._current_idx = (self._current_idx - 1) % len(self._matches)
        self._highlight_current()

    def _find_all(self):
        """Encuentra todas las coincidencias."""
        self._clear_tags()
        self._matches.clear()
        self._current_idx = -1

        query = self.search_var.get()
        self._last_query = query
        if not query:
            self.match_label.config(text="")
            return

        start = "1.0"
        while True:
            pos = self.text_widget.search(query, start, stopindex="end", nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.text_widget.tag_add(self._TAG, pos, end)
            self._matches.append(pos)
            start = end

        total = len(self._matches)
        if total == 0:
            self.match_label.config(text="Sin resultados")
        else:
            self.match_label.config(text=f"{total} resultado{'s' if total != 1 else ''}")

    def _highlight_current(self):
        """Resalta la coincidencia actual de forma diferenciada."""
        self.text_widget.tag_remove(self._TAG_CURRENT, "1.0", "end")
        if not self._matches:
            return
        pos = self._matches[self._current_idx]
        query = self.search_var.get()
        end = f"{pos}+{len(query)}c"
        self.text_widget.tag_add(self._TAG_CURRENT, pos, end)
        self.text_widget.see(pos)
        self.match_label.config(
            text=f"{self._current_idx + 1}/{len(self._matches)}"
        )

    def _clear(self):
        """Limpia resultados y etiquetas."""
        self._clear_tags()
        self._matches.clear()
        self._current_idx = -1
        self._last_query = ""
        self.match_label.config(text="")

    def _clear_tags(self):
        """Elimina tags de resaltado del texto."""
        if self.text_widget:
            self.text_widget.tag_remove(self._TAG, "1.0", "end")
            self.text_widget.tag_remove(self._TAG_CURRENT, "1.0", "end")

    _last_query = ""
