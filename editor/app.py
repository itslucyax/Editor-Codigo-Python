# -*- coding: utf-8 -*-
"""
Ventana principal del editor usando Tkinter, integra editor y numeros de linea.
"""

import tkinter as tk
from config import COLOR_FONDO, COLOR_BARRA_ESTADO_BG, COLOR_BARRA_ESTADO_FG, FUENTE_EDITOR
from editor.text_editor import TextEditor
from editor.line_numbers import LineNumbers

class EditorApp(tk.Tk):
    def __init__(self, inicial_text=""):
        super().__init__()
        self.title("Script Editor VB/VBS - Fase 1")
        self.configure(bg=COLOR_FONDO)
        self.geometry("900x600")
        self.minsize(600, 400)

        # Añadir frame principal
        frame = tk.Frame(self, bg=COLOR_FONDO)
        frame.pack(fill="both", expand=True)

        # Editor
        self.text_editor = TextEditor(frame)
        self.text_editor.pack(side="right", fill="both", expand=True)

        # Números de línea
        self.line_numbers = LineNumbers(frame, self.text_editor)
        self.line_numbers.pack(side="left", fill="y")

        # Barra de estado inferior
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self, textvariable=self.status_var, bg=COLOR_BARRA_ESTADO_BG,
            fg=COLOR_BARRA_ESTADO_FG, anchor="w", font=("Segoe UI", 10)
        )
        self.status_bar.pack(side="bottom", fill="x")

        self.text_editor.bind("<<Change>>", self._update_status)
        self.text_editor.bind("<KeyRelease>", self._update_status)
        self.text_editor.bind("<ButtonRelease-1>", self._update_status)

        self.text_editor.set_content(inicial_text)

        # Atajos de teclado
        self.bind_all("<Control-s>", self._guardar)
        self.bind_all("<Control-a>", self._seleccionar_todo)
        self.bind_all("<Control-z>", self._deshacer)
        self.bind_all("<Control-y>", self._rehacer)

    def _update_status(self, event=None):
        linea, columna = self.text_editor.index("insert").split(".")
        modificado = "*" if self.text_editor.edit_modified() else ""
        self.status_var.set(f"Linea: {linea}  Col: {int(columna)+1}  |  VBScript {modificado}")

    def _guardar(self, event=None):
        # Solo muestra mensaje ficticio
        self.status_var.set("Guardado (simulado)")
        self.after(1200, self._update_status)

    def _seleccionar_todo(self, event=None):
        self.text_editor.tag_add("sel", "1.0", "end")
        return "break"

    def _deshacer(self, event=None):
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def _rehacer(self, event=None):
        try:
            self.text_editor.edit_redo()
        except tk.TclError:
            pass
        return "break"
