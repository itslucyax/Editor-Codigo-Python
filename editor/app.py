# -*- coding: utf-8 -*-
"""
Ventana principal del editor usando Tkinter, integra editor y numeros de linea.
Incluye confirmación al cerrar si hay cambios sin guardar.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog

from config import (
    COLOR_FONDO,
    COLOR_BARRA_ESTADO_BG,
    COLOR_BARRA_ESTADO_FG,
    COLOR_SEPARADOR,
    SEPARADOR_ANCHO,
    FUENTE_EDITOR,
)
from editor.text_editor import TextEditor
from editor.line_numbers import LineNumbers
from editor.sidebar import Sidebar
from editor.search_bar import SearchBar

class EditorApp(tk.Tk):
    """
    Ventana principal del editor de scripts - DINÁMICA.
    
    Args:
        inicial_text: Contenido inicial del editor
        db: Conexión a base de datos (DatabaseConnection o None)
        record: Diccionario completo con todos los campos del registro
        key_columns: Lista de nombres de columnas que son clave primaria
        content_column: Nombre de la columna que contiene el script
        editable_columns: Lista de nombres de columnas editables
    """
    
    def __init__(
        self, 
        inicial_text="", 
        db=None, 
        record=None,
        key_columns=None,
        content_column="SCRIPT",
        editable_columns=None
    ):
        super().__init__()
        self.db = db
        self.record = record or {}
        self.key_columns = key_columns or []
        self.content_column = content_column
        self.editable_columns = editable_columns or []
        
        # Título de ventana dinámico
        if self.key_columns and self.record:
            key_display = " / ".join(str(self.record.get(k, "")) for k in self.key_columns)
            self.title(f"Editor VBS - {key_display}")
        else:
            self.title("Editor VBS - Local")
        
        self.configure(bg=COLOR_FONDO)
        self.geometry("1100x650")
        self.minsize(700, 450)

        # Barra de estado inferior (se empaqueta primero para que quede debajo)
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self, textvariable=self.status_var, bg=COLOR_BARRA_ESTADO_BG,
            fg=COLOR_BARRA_ESTADO_FG, anchor="w", font=("Segoe UI", 10), padx=8,
        )
        self.status_bar.pack(side="bottom", fill="x")

        # Frame principal
        frame = tk.Frame(self, bg=COLOR_FONDO)
        frame.pack(fill="both", expand=True)

        # 1) Sidebar a la izquierda del todo - DINÁMICO
        self.sidebar = Sidebar(
            frame,
            record=self.record,
            key_columns=self.key_columns,
            content_column=self.content_column,
            editable_columns=self.editable_columns
        )
        self.sidebar.pack(side="left", fill="y")

        # 2) Separador visual entre sidebar y números de línea
        tk.Frame(frame, width=SEPARADOR_ANCHO, bg=COLOR_SEPARADOR).pack(side="left", fill="y", padx=5)

        # 3) Editor de texto (se crea antes que line_numbers porque este lo necesita)
        self.text_editor = TextEditor(frame)

        # 4) Números de línea en medio (entre sidebar y editor)
        self.line_numbers = LineNumbers(frame, self.text_editor)
        self.line_numbers.pack(side="left", fill="y")

        # 5) Editor a la derecha
        self.text_editor.pack(side="right", fill="both", expand=True)

        # 6) Barra de búsqueda/reemplazo (flotante sobre el editor)
        self.search_bar = SearchBar(self.text_editor, self.text_editor)

        # Eventos para actualizar status
        self.text_editor.bind("<<Change>>",        self._update_status)
        self.text_editor.bind("<KeyRelease>",      self._update_status)
        self.text_editor.bind("<ButtonRelease-1>", self._update_status)

        # Cargar contenido inicial
        self.text_editor.set_content(inicial_text)

        # Atajos de teclado
        self.bind_all("<Control-s>", self._guardar)
        self.bind_all("<Control-a>", self._seleccionar_todo)
        self.bind_all("<Control-z>", self._deshacer)
        self.bind_all("<Control-y>", self._rehacer)
        self.bind_all("<Control-f>", self._abrir_buscar)
        self.bind_all("<Control-h>", self._abrir_reemplazar)
        self.bind_all("<Control-g>", self._ir_a_linea)
        self.bind_all("<F3>", self._buscar_siguiente)
        self.bind_all("<Shift-F3>", self._buscar_anterior)
        
        # Interceptar cierre de ventana para confirmar si hay cambios
        self.protocol("WM_DELETE_WINDOW", self._on_cerrar)

    def _get_origen_label(self) -> str:
        """Devuelve etiqueta para la barra de estado."""
        if self.db and self.key_columns and self.record:
            key_display = "/".join(str(self.record.get(k, "")) for k in self.key_columns)
            return f"SQL ({key_display})"
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
        """Guarda el script y campos editados en BD si hay conexión."""
        if self.db and self.key_columns and self.record:
            # Obtener contenido del script
            contenido = self.text_editor.get("1.0", "end-1c")
            
            # Obtener campos editados del sidebar
            campos_editados = self.sidebar.get_edited_fields()
            
            # Agregar contenido del script a los campos actualizados
            campos_editados[self.content_column] = contenido
            
            # Obtener valores de las claves
            key_values = [str(self.record.get(k, "")) for k in self.key_columns]
            
            try:
                ok = self.db.save_record_full(self.key_columns, key_values, campos_editados)
                if not ok:
                    key_display = ", ".join(f"{k}={v}" for k, v in zip(self.key_columns, key_values))
                    messagebox.showwarning(
                        "Guardar", 
                        f"No se actualizó ninguna fila.\n"
                        f"Revisa que exista el registro con {key_display}"
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

    # ------------------------------------------------------------------
    # Búsqueda / Reemplazo / Ir a línea
    # ------------------------------------------------------------------

    def _abrir_buscar(self, event=None):
        """Abre la barra de búsqueda (Ctrl+F)."""
        self.search_bar.show(replace=False)
        return "break"

    def _abrir_reemplazar(self, event=None):
        """Abre la barra de búsqueda con reemplazo (Ctrl+H)."""
        self.search_bar.show(replace=True)
        return "break"

    def _buscar_siguiente(self, event=None):
        """Buscar siguiente (F3)."""
        if self.search_bar.visible:
            self.search_bar.find_next()
        return "break"

    def _buscar_anterior(self, event=None):
        """Buscar anterior (Shift+F3)."""
        if self.search_bar.visible:
            self.search_bar.find_prev()
        return "break"

    def _ir_a_linea(self, event=None):
        """Diálogo 'Ir a línea' (Ctrl+G)."""
        total = int(self.text_editor.index("end-1c").split(".")[0])
        linea = simpledialog.askinteger(
            "Ir a línea",
            f"Número de línea (1-{total}):",
            parent=self,
            minvalue=1,
            maxvalue=total,
        )
        if linea is not None:
            self.text_editor.mark_set("insert", f"{linea}.0")
            self.text_editor.see(f"{linea}.0")
            self.text_editor.focus_set()
        return "break"
