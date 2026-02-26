# -*- coding: utf-8 -*-
"""
Ventana principal del editor usando Tkinter, integra editor y numeros de linea.
Incluye confirmación al cerrar si hay cambios sin guardar.
"""

import tkinter as tk
from tkinter import messagebox

from config import COLOR_FONDO, COLOR_BARRA_ESTADO_BG, COLOR_BARRA_ESTADO_FG, FUENTE_EDITOR
from editor.text_editor import TextEditor
from editor.line_numbers import LineNumbers


class EditorApp(tk.Tk):
    """
    Ventana principal del editor de scripts.
    
    Args:
        inicial_text: Contenido inicial del editor
        db: Conexión a base de datos (DatabaseConnection o None)
        modelo: Valor MODELO del script (para guardar)
        codigo: Valor CODIGO del script (para guardar)
    """
    
    def __init__(self, inicial_text="", db=None, modelo=None, codigo=None):
        super().__init__()
        self.db = db
        self.modelo = modelo
        self.codigo = codigo
        
        # Título de ventana
        if modelo and codigo:
            self.title(f"Editor VBS - {modelo}/{codigo}")
        else:
            self.title("Editor VBS - Local")
        
        self.configure(bg=COLOR_FONDO)
        self.geometry("900x600")
        self.minsize(600, 400)

        # Frame principal
        frame = tk.Frame(self, bg=COLOR_FONDO)
        frame.pack(fill="both", expand=True)

        # Editor de texto
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

        # Eventos para actualizar status
        self.text_editor.bind("<<Change>>", self._update_status)
        self.text_editor.bind("<KeyRelease>", self._update_status)
        self.text_editor.bind("<ButtonRelease-1>", self._update_status)

        # Cargar contenido inicial
        self.text_editor.set_content(inicial_text)

        # Atajos de teclado
        self.bind_all("<Control-s>", self._guardar)
        self.bind_all("<Control-a>", self._seleccionar_todo)
        self.bind_all("<Control-z>", self._deshacer)
        self.bind_all("<Control-y>", self._rehacer)
        
        # Interceptar cierre de ventana para confirmar si hay cambios
        self.protocol("WM_DELETE_WINDOW", self._on_cerrar)

    def _get_origen_label(self) -> str:
        """Devuelve etiqueta para la barra de estado."""
        if self.db and self.modelo and self.codigo:
            return f"SQL ({self.modelo}/{self.codigo})"
        return "Local"

    def _update_status(self, event=None):
        """Actualiza la barra de estado con posición y estado de modificación."""
        linea, columna = self.text_editor.index("insert").split(".")
        mod = self.text_editor.edit_modified()
        estado = "Modificado" if mod else "Guardado"
        self.status_var.set(
            f"{self._get_origen_label()} | Línea: {linea}  Col: {int(columna)+1} | {estado}"
        )

    def _guardar(self, event=None):
        """Guarda el script en BD si hay conexión, si no simula guardado."""
        if self.db and self.modelo and self.codigo:
            contenido = self.text_editor.get("1.0", "end-1c")
            try:
                ok = self.db.save_script(self.modelo, self.codigo, contenido)
                if not ok:
                    messagebox.showwarning(
                        "Guardar", 
                        f"No se actualizó ninguna fila.\n"
                        f"Revisa que exista MODELO='{self.modelo}' CODIGO='{self.codigo}'"
                    )
                else:
                    self.text_editor.edit_modified(False)
                    self.status_var.set("Guardado en SQL Server")
                    self.after(1500, self._update_status)
            except Exception as e:
                messagebox.showerror("Error al guardar", str(e))
        else:
            # Sin conexión BD: guardado simulado
            self.text_editor.edit_modified(False)
            self.status_var.set("Guardado (local)")
            self.after(1500, self._update_status)

        return "break"

    def _on_cerrar(self):
        """
        Maneja el cierre de ventana.
        Si hay cambios sin guardar, pregunta al usuario.
        """
        if self.text_editor.edit_modified():
            respuesta = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Hay cambios sin guardar.\n\n¿Desea guardar antes de cerrar?"
            )
            if respuesta is None:
                # Cancelar: no cerrar
                return
            elif respuesta:
                # Sí: guardar y cerrar
                self._guardar()
        
        # Cerrar ventana
        self.destroy()

    def _seleccionar_todo(self, event=None):
        """Selecciona todo el texto (Ctrl+A)."""
        self.text_editor.tag_add("sel", "1.0", "end")
        return "break"

    def _deshacer(self, event=None):
        """Deshace última acción (Ctrl+Z)."""
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass
        return "break"

    def _rehacer(self, event=None):
        """Rehace última acción (Ctrl+Y)."""
        try:
            self.text_editor.edit_redo()
        except tk.TclError:
            pass
        return "break"
