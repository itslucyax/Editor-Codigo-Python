# -*- coding: utf-8 -*-
"""
Panel lateral izquierdo del editor - DINÁMICO.
Muestra todos los campos del registro automáticamente según el esquema de la BD.
NO hay hardcodeo de nombres de campos.
"""
import tkinter as tk
from config import (
    COLOR_FONDO,
    COLOR_SIDEBAR_BG,
    COLOR_SIDEBAR_FG,
    COLOR_TEXTO
)


class Sidebar(tk.Frame):
    """
    Panel lateral DINÁMICO que se adapta automáticamente a cualquier estructura de BD.
    
    Construcción adaptativa:
    1. Detecta qué campos tiene el registro
    2. Separa campos de metadata vs variables (VAR0-VAR9)
    3. Los de metadata se muestran en sección superior (algunos editables, algunos readonly)
    4. Los de variables se muestran en sección inferior con Entry readonly
    
    Args:
        master: Widget padre
        record: Diccionario completo con TODOS los campos del registro de BD
        key_columns: Lista de nombres de columnas que son clave primaria (readonly)
        content_column: Nombre de la columna que contiene el script (no se muestra)
        editable_columns: Lista de nombres de columnas editables por el usuario
    """
    WIDTH = 210  # Ancho fijo del sidebar en píxeles

    def __init__(
        self, 
        master, 
        record: dict = None,
        key_columns: list = None,
        content_column: str = "SCRIPT",
        editable_columns: list = None
    ):
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
        
        self._build_ui()
    
    def _categorize_fields(self):
        """
        Categoriza los campos del registro en:
        - metadata_fields: Campos de información general (no VAR*)
        - variable_fields: Campos tipo VAR0-VAR9
        """
        self.metadata_fields = []
        self.variable_fields = []
        
        for field_name, value in self.record.items():
            field_upper = field_name.upper()
            
            # Excluir claves primarias y columna de contenido de la visualización
            if field_upper in self.key_columns or field_upper == self.content_column:
                continue
            
            # Detectar variables (VAR0, VAR1, etc.)
            if field_upper.startswith("VAR") and len(field_upper) <= 4:
                try:
                    # Verificar que después de VAR venga un número
                    int(field_upper[3:])
                    self.variable_fields.append((field_name, value))
                    continue
                except (ValueError, IndexError):
                    pass
            
            # El resto son metadata
            self.metadata_fields.append((field_name, value))
    
    def _build_ui(self):
        """Construye la interfaz completa del sidebar dinámicamente."""
        # Mostrar claves primarias en la parte superior (destacadas)
        if self.key_columns:
            self._build_key_section()
        
        # Sección de metadata
        if self.metadata_fields:
            self._build_metadata_section()
        
        # Separador
        if self.variable_fields:
            tk.Frame(self, bg="#999", height=1).pack(fill="x", pady=10, padx=5)
            self._build_variables_section()
    
    def _build_key_section(self):
        """
        Construye la sección superior con las claves primarias (MODELO, CODIGO, etc).
        Estilo destacado: texto grande y negrita.
        """
        container = tk.Frame(self, bg=COLOR_SIDEBAR_BG)
        container.pack(fill="x", padx=10, pady=(10, 5))
        
        for key_col in self.key_columns:
            value = self.record.get(key_col, "")
            
            # Mostrar en grande y negrita
            label = tk.Label(
                container,
                text=value,
                font=("Segoe UI", 14, "bold"),
                bg=COLOR_SIDEBAR_BG,
                fg="#000000",
                anchor="w"
            )
            label.pack(fill="x", pady=(0, 2))
    
    def _build_metadata_section(self):
        """
        Construye la sección de campos de metadata.
        Campos editables tienen Entry, campos readonly tienen Label.
        """
        container = tk.Frame(self, bg=COLOR_SIDEBAR_BG)
        container.pack(fill="x", padx=10, pady=(5, 10))
        
        for field_name, value in self.metadata_fields:
            field_upper = field_name.upper()
            is_editable = field_upper in self.editable_columns
            
            # Frame para cada campo
            field_frame = tk.Frame(container, bg=COLOR_SIDEBAR_BG)
            field_frame.pack(fill="x", pady=3)
            
            # Etiqueta del campo
            tk.Label(
                field_frame,
                text=f"{field_name}:",
                font=("Segoe UI", 9, "bold"),
                bg=COLOR_SIDEBAR_BG,
                fg="#000000",
                anchor="w"
            ).pack(fill="x")
            
            # Valor (editable o readonly)
            if is_editable:
                # Entry editable
                entry = tk.Entry(
                    field_frame,
                    font=("Segoe UI", 9),
                    bg="#FFFFFF",
                    fg="#000000",
                    relief="solid",
                    borderwidth=1
                )
                entry.insert(0, value)
                entry.pack(fill="x", pady=(2, 0))
                self.field_widgets[field_name] = entry
            else:
                # Label readonly
                label = tk.Label(
                    field_frame,
                    text=value,
                    font=("Segoe UI", 9),
                    bg=COLOR_SIDEBAR_BG,
                    fg="#555555",
                    anchor="w",
                    wraplength=180  # Wrap text si es muy largo
                )
                label.pack(fill="x", pady=(2, 0))
    
    def _build_variables_section(self):
        """Construye la sección inferior con las variables (VAR0-VAR9)."""
        container = tk.Frame(self, bg=COLOR_SIDEBAR_BG)
        container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Cabecera de sección
        tk.Label(
            container,
            text="Variables del Script",
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_SIDEBAR_BG,
            fg="#000000",
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        # Ordenar variables por número (VAR0, VAR1, ..., VAR9)
        sorted_vars = sorted(self.variable_fields, key=lambda x: x[0])
        
        # Crear filas para cada variable
        for var_name, var_value in sorted_vars:
            self._create_variable_row(container, var_name, var_value)
    
    def _create_variable_row(self, parent, var_name, value):
        """
        Crea una fila con etiqueta "VAR X" y Entry readonly para el valor.
        
        Args:
            parent: Widget padre
            var_name: Nombre de la variable (ej: "VAR0")
            value: Valor de la variable
        """
        row_frame = tk.Frame(parent, bg=COLOR_SIDEBAR_BG)
        row_frame.pack(fill="x", pady=2)
        
        # Etiqueta "Var 0", "Var 1", etc.
        display_name = var_name.replace("VAR", "Var ")
        tk.Label(
            row_frame,
            text=display_name,
            font=("Consolas", 8),
            bg=COLOR_SIDEBAR_BG,
            fg="#333333",
            width=6,
            anchor="w"
        ).pack(side="left", padx=(0, 5))
        
        # Entry readonly para el valor
        entry = tk.Entry(
            row_frame,
            font=("Consolas", 8),
            bg="#E8E8E8",  # Fondo más oscuro que el editor
            fg="#000000",
            relief="solid",
            borderwidth=1,
            state="readonly"
        )
        
        # Configurar el valor (necesitamos cambiar temporalmente el estado)
        entry.config(state="normal")
        entry.insert(0, value)
        entry.config(state="readonly")
        
        entry.pack(side="left", fill="x", expand=True)
        
        # Guardar referencia (por si acaso necesitamos actualizar después)
        self.field_widgets[var_name] = entry
    
    def get_edited_fields(self) -> dict:
        """
        Obtiene los valores actuales de todos los campos editables.
        
        Returns:
            Diccionario {nombre_campo: valor_actual} solo para campos editables
        """
        edited = {}
        for field_name, widget in self.field_widgets.items():
            if field_name.upper() in self.editable_columns:
                if isinstance(widget, tk.Entry):
                    edited[field_name] = widget.get()
        return edited
    
    def get_all_fields(self) -> dict:
        """
        Obtiene los valores actuales de TODOS los campos (editables y readonly).
        
        Returns:
            Diccionario completo con todos los valores actuales
        """
        result = self.record.copy()
        
        # Actualizar con valores editados
        for field_name, widget in self.field_widgets.items():
            if isinstance(widget, tk.Entry):
                # Obtener valor actual (temporalmente cambiar estado si es readonly)
                current_state = widget.cget("state")
                if current_state == "readonly":
                    widget.config(state="normal")
                    value = widget.get()
                    widget.config(state="readonly")
                else:
                    value = widget.get()
                result[field_name] = value
        
        return result
