# -*- coding: utf-8 -*-
"""
Barra de búsqueda y reemplazo integrada en el editor.

Se muestra como un panel flotante en la parte superior del editor,
al estilo VS Code.  Soporta:
  - Buscar siguiente / anterior (Enter / Shift+Enter)
  - Reemplazar una ocurrencia / todas
  - Buscar con coincidencia de mayúsculas (match case)
  - Escape para cerrar
"""

import tkinter as tk
from config import COLOR_BARRA_ESTADO_BG, COLOR_BARRA_ESTADO_FG


class SearchBar(tk.Frame):
    """Barra Buscar / Reemplazar acoplada al editor."""

    _TAG = "search_highlight"
    _TAG_CURRENT = "search_current"

    def __init__(self, parent, text_widget: tk.Text):
        super().__init__(parent, bg=COLOR_BARRA_ESTADO_BG, padx=6, pady=4)
        self.text_widget = text_widget
        self._matches: list[str] = []   # índices Tkinter de matches
        self._current_idx = -1
        self._match_case = tk.BooleanVar(value=False)

        # --- Fila 1: Buscar ---
        row1 = tk.Frame(self, bg=COLOR_BARRA_ESTADO_BG)
        row1.pack(fill="x", pady=(0, 2))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search_change())

        self.entry_search = tk.Entry(
            row1, textvariable=self.search_var,
            bg="#3c3c3c", fg="#cccccc", insertbackground="#cccccc",
            font=("Segoe UI", 10), relief="flat", width=30,
        )
        self.entry_search.pack(side="left", padx=(0, 4))
        self.entry_search.bind("<Return>", lambda e: self.find_next())
        self.entry_search.bind("<Shift-Return>", lambda e: self.find_prev())
        self.entry_search.bind("<Escape>", lambda e: self.hide())

        self.match_label = tk.Label(
            row1, text="", bg=COLOR_BARRA_ESTADO_BG,
            fg=COLOR_BARRA_ESTADO_FG, font=("Segoe UI", 9),
        )
        self.match_label.pack(side="left", padx=(0, 6))

        tk.Checkbutton(
            row1, text="Aa", variable=self._match_case,
            bg=COLOR_BARRA_ESTADO_BG, fg=COLOR_BARRA_ESTADO_FG,
            selectcolor="#3c3c3c", activebackground=COLOR_BARRA_ESTADO_BG,
            font=("Segoe UI", 9), command=self._on_search_change,
        ).pack(side="left", padx=(0, 4))

        self._btn(row1, "▲", self.find_prev)
        self._btn(row1, "▼", self.find_next)
        self._btn(row1, "✕", self.hide)

        # --- Fila 2: Reemplazar ---
        row2 = tk.Frame(self, bg=COLOR_BARRA_ESTADO_BG)
        row2.pack(fill="x")

        self.replace_var = tk.StringVar()
        self.entry_replace = tk.Entry(
            row2, textvariable=self.replace_var,
            bg="#3c3c3c", fg="#cccccc", insertbackground="#cccccc",
            font=("Segoe UI", 10), relief="flat", width=30,
        )
        self.entry_replace.pack(side="left", padx=(0, 4))
        self.entry_replace.bind("<Escape>", lambda e: self.hide())

        self._btn(row2, "Reemplazar", self.replace_one)
        self._btn(row2, "Reemplazar todo", self.replace_all)

        # Tags de resaltado de búsqueda
        self.text_widget.tag_configure(self._TAG, background="#623315", foreground="#ffffff")
        self.text_widget.tag_configure(self._TAG_CURRENT, background="#515c6a", foreground="#ffffff")

        # Oculto de inicio
        self._visible = False

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------

    @staticmethod
    def _btn(parent, text, command):
        b = tk.Button(
            parent, text=text, command=command,
            bg="#3c3c3c", fg="#cccccc", activebackground="#505050",
            activeforeground="#ffffff", relief="flat", font=("Segoe UI", 9),
            padx=6, pady=1,
        )
        b.pack(side="left", padx=(0, 2))
        return b

    # ------------------------------------------------------------------
    # Mostrar / ocultar
    # ------------------------------------------------------------------

    def show(self, replace: bool = False):
        """Muestra la barra de búsqueda (y opcionalmente reemplazar)."""
        if not self._visible:
            self.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=4)
            self.lift()
            self._visible = True
        self.entry_search.focus_set()
        # Pre-llenar con texto seleccionado si hay
        try:
            sel = self.text_widget.get("sel.first", "sel.last")
            if sel:
                self.search_var.set(sel)
                self.entry_search.select_range(0, "end")
        except tk.TclError:
            pass

    def hide(self):
        """Oculta la barra y limpia resaltado."""
        self._clear_tags()
        self.place_forget()
        self._visible = False
        self.text_widget.focus_set()

    @property
    def visible(self) -> bool:
        return self._visible

    # ------------------------------------------------------------------
    # Búsqueda
    # ------------------------------------------------------------------

    def _on_search_change(self):
        """Se llama cada vez que cambia el texto de búsqueda."""
        self._find_all()
        if self._matches:
            self._current_idx = 0
            self._highlight_current()

    def _find_all(self):
        """Encuentra todas las ocurrencias y las guarda en self._matches."""
        self._clear_tags()
        self._matches.clear()
        self._current_idx = -1

        query = self.search_var.get()
        if not query:
            self.match_label.config(text="")
            return

        nocase = not self._match_case.get()
        start = "1.0"
        while True:
            pos = self.text_widget.search(
                query, start, stopindex="end", nocase=nocase
            )
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            self.text_widget.tag_add(self._TAG, pos, end)
            self._matches.append(pos)
            start = end

        total = len(self._matches)
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

    def find_next(self):
        """Salta a la siguiente coincidencia."""
        if not self._matches:
            self._find_all()
        if not self._matches:
            return
        self._current_idx = (self._current_idx + 1) % len(self._matches)
        self._highlight_current()

    def find_prev(self):
        """Salta a la coincidencia anterior."""
        if not self._matches:
            self._find_all()
        if not self._matches:
            return
        self._current_idx = (self._current_idx - 1) % len(self._matches)
        self._highlight_current()

    # ------------------------------------------------------------------
    # Reemplazo
    # ------------------------------------------------------------------

    def replace_one(self):
        """Reemplaza la coincidencia actual y avanza a la siguiente."""
        if not self._matches or self._current_idx < 0:
            return
        pos = self._matches[self._current_idx]
        query = self.search_var.get()
        replacement = self.replace_var.get()
        end = f"{pos}+{len(query)}c"

        self.text_widget.delete(pos, end)
        self.text_widget.insert(pos, replacement)

        # Re-buscar porque las posiciones cambiaron
        self._find_all()
        if self._matches:
            self._current_idx = min(self._current_idx, len(self._matches) - 1)
            self._highlight_current()

    def replace_all(self):
        """Reemplaza todas las coincidencias."""
        query = self.search_var.get()
        replacement = self.replace_var.get()
        if not query:
            return

        # Reemplazar de abajo a arriba para mantener posiciones válidas
        self._find_all()
        for pos in reversed(self._matches):
            end = f"{pos}+{len(query)}c"
            self.text_widget.delete(pos, end)
            self.text_widget.insert(pos, replacement)

        self._find_all()

    # ------------------------------------------------------------------
    # Limpieza
    # ------------------------------------------------------------------

    def _clear_tags(self):
        self.text_widget.tag_remove(self._TAG, "1.0", "end")
        self.text_widget.tag_remove(self._TAG_CURRENT, "1.0", "end")
