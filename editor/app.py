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
    COLOR_SIDEBAR_BG,
    SEPARADOR_ANCHO,
    FUENTE_EDITOR,
)
from editor.text_editor import TextEditor
from editor.line_numbers import LineNumbers
from editor.sidebar import Sidebar
from editor.search_bar import SearchBar
from editor.script_selector import ScriptSelector
from editor.fixed_search_bar import FixedSearchBar
from editor.vbs_validator import validate_vbs, format_problemas

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
        editable_columns=None,
        scripts_list=None,
        context_type=None
    ):
        super().__init__()
        self.db = db
        self.record = record or {}
        self.key_columns = key_columns or []
        self.content_column = content_column
        self.editable_columns = editable_columns or []
        self.scripts_list = scripts_list or []
        self.context_type = context_type  # 'documento' | 'plantilla' | None
        
        # Título de ventana dinámico con contexto
        ctx_label = ""
        if self.context_type:
            ctx_label = f" [{self.context_type.capitalize()}]"
        
            if self.context_type == "plantilla":
                plantilla_key = self.key_columns[0] if self.key_columns else "PLANTILLA"
                plantilla_val = (
                    self.record.get(plantilla_key)
                    or self.record.get(plantilla_key.upper())
                    or self.record.get(plantilla_key.lower())
                    or "Sin nombre"
                )
                self.title(f"Editor VBS{ctx_label} - {plantilla_val}")
            elif self.key_columns and self.record:
                key_display = " / ".join(str(self.record.get(k, "")) for k in self.key_columns)
                self.title(f"Editor VBS{ctx_label} - {key_display}")
            else:
                self.title(f"Editor VBS{ctx_label} - Local")
        
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
        self.main_frame = tk.Frame(self, bg=COLOR_FONDO)
        self.main_frame.pack(fill="both", expand=True)

        # 1) Sidebar a la izquierda del todo - DINÁMICO
        self.sidebar = Sidebar(
            self.main_frame,
            record=self.record,
            key_columns=self.key_columns,
            content_column=self.content_column,
            editable_columns=self.editable_columns
        )
        # Ocultar sidebar en plantillas
        if self.context_type != "plantilla":
            self.sidebar.pack(side="left", fill="y")

        # 2) Separador visual entre sidebar y números de línea
        self.separator = tk.Frame(self.main_frame, width=0, bg=COLOR_SEPARADOR)
        # Ocultar separador en plantillas
        if self.context_type != "plantilla":
            self.separator.pack(side="left", fill="y", padx=0)

        # 3) Frame derecho (barras superiores + área de edición)
        right_frame = tk.Frame(self.main_frame, bg=COLOR_FONDO)
        right_frame.pack(side="left", fill="both", expand=True)

        # ============================================================
        # BARRAS SUPERIORES (siempre visibles)
        # ============================================================

        # 4a) Selector de scripts (Combobox "Mostrar SCRIPT")
        self.script_selector = ScriptSelector(
            right_frame,
            scripts_list=self.scripts_list,
            on_select_callback=self._on_script_selected,
            context_type=self.context_type
        )
        self.script_selector.pack(side="top", fill="x")

        #Posicionar el desplegable en el registro actualmente abierto
        if self.key_columns and self.record:
            first_key = self.key_columns[0] if self.key_columns else ""
            current_key = ""
            for k, v in self.record.items():
                if k.upper() == first_key.upper():
                    current_key = str(v).strip()
                    break
            for i, script in enumerate(self.scripts_list):
                kv = script.get("key_values", [])
                if kv and str(kv[0]).strip().upper() == current_key.upper():
                    self.script_selector.combo.current(i)
                    break

        # 4b) Barra de búsqueda fija (siempre visible)
        self.fixed_search = FixedSearchBar(right_frame)
        self.fixed_search.pack(side="top", fill="x")

        # ============================================================
        # ÁREA DE EDICIÓN
        # ============================================================

        # 5) Frame del editor (números de línea + editor de texto)
        editor_frame = tk.Frame(right_frame, bg=COLOR_FONDO)
        editor_frame.pack(fill="both", expand=True)

        # 6) Editor de texto con scrollbar vertical
        self.text_editor = TextEditor(editor_frame)
        self.text_editor.configure(yscrollcommand=self._editor_scrollbar.set) if hasattr(self, '_editor_scrollbar') else None

        # Conectar barra de búsqueda fija al editor de texto
        self.fixed_search.set_text_widget(self.text_editor)

        # Botón guardar en la barra de búsqueda (a la derecha de las flechas)
        self.fixed_search.add_save_button(self._guardar, self.status_var, self._update_status)

        # 7) Scrollbar del editor (se empaqueta primero para que quede a la derecha)
        self._editor_scrollbar = tk.Scrollbar(editor_frame, orient="vertical", command=self.text_editor.yview)
        self._editor_scrollbar.pack(side="right", fill="y")
        self.text_editor.configure(yscrollcommand=self._editor_scrollbar.set)

        # 8) Números de línea a la izquierda
        self.line_numbers = LineNumbers(editor_frame, self.text_editor)
        self.line_numbers.pack(side="left", fill="y")

        # 9) Editor ocupa el resto
        self.text_editor.pack(side="left", fill="both", expand=True)

        # 10) Barra de búsqueda/reemplazo flotante (Ctrl+H)
        self.search_bar = SearchBar(self.text_editor, self.text_editor)

        # Eventos para actualizar status
        self.text_editor.bind("<<Change>>",        self._update_status)
        self.text_editor.bind("<KeyRelease>",      self._update_status)
        self.text_editor.bind("<ButtonRelease-1>", self._update_status)

         # Cargar contenido inicial
        self.text_editor.set_content(inicial_text)
        self.text_editor.edit_reset()

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
        ctx = ""
        if self.context_type:
            ctx = f" | {self.context_type.capitalize()}"
        if self.db and self.key_columns and self.record:
            key_display = "/".join(str(self.record.get(k, "")) for k in self.key_columns)
            return f"SQL ({key_display}){ctx}"
        return f"Local{ctx}"

    def _update_status(self, event=None):
        """Actualiza la barra de estado con posición y estado de modificación."""
        linea, columna = self.text_editor.index("insert").split(".")
        mod = self.text_editor.edit_modified()
        estado = "Modificado" if mod else "Guardado"
        self.status_var.set(
            f"{self._get_origen_label()} | Línea: {linea}  Col: {int(columna)+1} | {estado}"
        )

    def _validar_script(self) -> bool:
        """
        Valida el script antes de guardar.
        
        Returns:
            True si se puede continuar con el guardado, False si se cancela.
        """
        contenido = self.text_editor.get("1.0", "end-1c")
        problemas = validate_vbs(contenido)
        
        if not problemas:
            return True
        
        # Separar errores y avisos
        errores = [p for p in problemas if p[0] == "error"]
        avisos = [p for p in problemas if p[0] == "aviso"]
        
        resumen = format_problemas(problemas)
        
        if errores:
            # Hay errores: preguntar si quiere guardar de todos modos
            resp = messagebox.askyesno(
                f"Validación del script — {len(errores)} error(es), {len(avisos)} aviso(s)",
                f"Se han detectado los siguientes problemas en el script:\n\n"
                f"{resumen}\n\n"
                f"¿Desea guardar de todos modos?"
            )
            return resp
        else:
            # Solo avisos: informar y continuar
            resp = messagebox.askyesno(
                f"Validación del script — {len(avisos)} aviso(s)",
                f"Se han detectado los siguientes avisos en el script:\n\n"
                f"{resumen}\n\n"
                f"¿Desea guardar de todos modos?"
            )
            return resp

    def _guardar(self, event=None):
        """Guarda el script y campos editados en BD si hay conexión."""
        # Validar script antes de guardar
        if not self._validar_script():
            self.status_var.set("Guardado cancelado. El script contiene errores.")
            self.after(3000, self._update_status)
            return "break"
        
        if self.db and self.key_columns and self.record:
            # Obtener contenido del script
            contenido = self.text_editor.get("1.0", "end-1c")
            
            # Obtener campos editados del sidebar
            campos_editados = self.sidebar.get_edited_fields()
            
            # Agregar valores de variables editadas
            variable_values = self.sidebar.get_variable_values()
            campos_editados.update(variable_values)
            
            # Agregar contenido del script a los campos actualizados
            #Nombre exacto de columna del record para evitar problemas de capitalización
            content_col_real = self.content_column
            for k in self.record.keys():
                if k.upper() == self.content_column.upper():
                    content_col_real = k
                    break
            campos_editados[content_col_real] = contenido
            
            # Obtener valores de las claves (busqueda case-sensitive en el record)
            def _get_record_val(record, key):
                if key in record:
                    return str(record[key])
                for k, v in record.items():
                    if k.upper() == key.upper():
                        return str(v)
                return ""
            key_values = [_get_record_val(self.record, k) for k in self.key_columns]
            
            try:
                ok = self.db.save_record_full(self.key_columns, key_values, campos_editados)
                if not ok:
                    key_display = ", ".join(f"{k}={v}" for k, v in zip(self.key_columns, key_values))
                    messagebox.showwarning(
                        "Guardar registro",
                        f"No se ha actualizado ningún registro.\n"
                        f"Compruebe que exista el registro con {key_display}."
                    )
                else:
                    self.text_editor.edit_modified(False)
                    self.status_var.set("✓ Los cambios han sido guardados")
                    self.after(1500, self._update_status)
                    messagebox.showinfo(
                        "Registro guardado",
                        "✓ Los cambios han sido guardados correctamente."
                    )
            except Exception as e:
                messagebox.showerror("Error al guardar el registro", str(e))
        else:
            # Sin conexión BD: guardado simulado
            self.text_editor.edit_modified(False)
            self.status_var.set("✓ Guardado (local)")
            self.after(1500, self._update_status)

        return "break"

    def _on_script_selected(self, index, script_data):
        """
        Callback cuando se selecciona un script del selector (Combobox).
        Carga el registro completo desde BD (contenido + variables + sidebar).
        Si hay cambios sin guardar, pregunta antes de cambiar.
        """
        if self.text_editor.edit_modified():
            resp = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Existen cambios sin guardar.\n¿Desea guardarlos antes de cambiar de script?"
            )
            if resp is None:
                return
            elif resp:
                self._guardar()
        
        # Si hay BD y key_values en el script, recargar registro completo
        new_key_values = script_data.get("key_values")
        if self.db and new_key_values and self.key_columns:
            try:
                # Cargar registro completo desde BD
                new_record = self.db.get_record_full(self.key_columns, new_key_values)
                self.record = new_record
                
                # Actualizar contenido del editor
                content = new_record.get(self.content_column, script_data.get("content", ""))
                self.text_editor.set_content(content)
                self.text_editor.edit_reset()
                
                # Reconstruir sidebar con los nuevos datos
                self.sidebar.destroy()
                self.sidebar = Sidebar(
                    self.main_frame,
                    record=self.record,
                    key_columns=self.key_columns,
                    content_column=self.content_column,
                    editable_columns=self.editable_columns
                )
                # Insertar antes del separador (solo si no es plantilla)
                if self.context_type != "plantilla":
                    self.sidebar.pack(side="left", fill="y", before=self.separator)
                
                # Actualizar título
                ctx_label = ""
                if self.context_type:
                    ctx_label = f" [{self.context_type.capitalize()}]"
                key_display = " / ".join(str(self.record.get(k, "")) for k in self.key_columns)
                self.title(f"Editor VBS{ctx_label} - {key_display}")
                
            except Exception as e:
                messagebox.showerror("Error al cargar el script", f"No se ha podido cargar el script:\n{e}")
                return
        else:
            # Modo local o sin key_values: solo cambiar contenido
            content = script_data.get("content", "")
            self.text_editor.set_content(content)
            self.text_editor.edit_reset()
            
        self.text_editor.edit_reset()
        self.text_editor.edit_modified(False)
        self._update_status()

    def _on_cerrar(self):
        """
        Maneja el cierre de ventana.
        Si hay cambios sin guardar, pregunta al usuario.
        """
        if self.text_editor.edit_modified():
            respuesta = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Existen cambios sin guardar.\n\n¿Desea guardarlos antes de cerrar?"
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
        """Foco a la barra de búsqueda fija (Ctrl+F)."""
        self.fixed_search.entry.focus_set()
        self.fixed_search.entry.select_range(0, "end")
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
