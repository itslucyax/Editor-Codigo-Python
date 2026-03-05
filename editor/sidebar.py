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
            
            # Detectar variables: VAR0-VAR9 o TABLACAMPO0-TABLACAMPO9
            # Solo incluir si tiene valor (no vacio)
            if field_upper.startswith("VAR") and len(field_upper) <= 4:
                try:
                    int(field_upper[3:])
                    self.variable_fields.append((field_name, value))
                    continue
                except (ValueError, IndexError):
                    pass
            elif field_upper.startswith("TABLACAMPO") and len(field_upper) <= 11:
                try:
                    int(field_upper[10:])
                    self.variable_fields.append((field_name, value))
                    continue
                except (ValueError, IndexError):
                    pass
            
            # El resto son metadata (excluir TIPO, se muestra aparte)
            if field_upper not in ("TIPO", "DESCRIPCION"):
                self.metadata_fields.append((field_name, value))
    
    def _build_ui(self):
        """Construye la interfaz completa del sidebar dinámicamente."""
        # Mostrar claves primarias en la parte superior (destacadas)
        if self.key_columns:
            self._build_key_section()
        
        # Mostrar TIPO (significado de la primera letra de MODELO)
        self._build_tipo_section()
        
        # Sección de metadata
        if self.metadata_fields:
            self._build_metadata_section()
        
        # Separador y variables (siempre 10 filas fijas editables)
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
    
    # Mapeo de la primera letra de MODELO a su significado
    # Fallback hardcoded — si existe tabla de lookup en BD, se puede sobreescribir
    TIPO_MAP = {
        "A": "Albarán de Salida de Almacén",
        "S": "Albarán de Salida de Facturación",
        "F": "Factura",
        "O": "Carta de Oferta",
        "E": "Entrada",
        "T": "Orden de Trabajo",
        "P": "Pedido Proveedor",
        "Q": "Etiqueta",
        "R": "Recibo",
        "L": "Documento de Pago",
        "U": "Solicitud de Cliente",
        "V": "Solicitud de Proveedor",
        "X": "Presupuesto",
        "C": "Pedido Cliente",
        "H": "Vales Horarios",
        "Z": "Etiquetas Lotes"
    }
    
    def _build_tipo_section(self):
        """
        Muestra el TIPO basado en la primera letra de MODELO.
        Ej: MODELO='T01' -> 'Tipo: T - Orden de Trabajo'
        """
        modelo_value = self.record.get("MODELO", "")
        if not modelo_value:
            return
        
        letra = modelo_value[0].upper()
        descripcion = self.TIPO_MAP.get(letra, letra)
        
        container = tk.Frame(self, bg=COLOR_SIDEBAR_BG)
        container.pack(fill="x", padx=10, pady=(0, 5))
        
        tk.Label(
            container,
            text="Tipo:",
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_SIDEBAR_BG,
            fg="#000000",
            anchor="w"
        ).pack(fill="x")
        
        tk.Label(
            container,
            text=f"{letra} - {descripcion}",
            font=("Segoe UI", 9),
            bg=COLOR_SIDEBAR_BG,
            fg="#555555",
            anchor="w"
        ).pack(fill="x", pady=(2, 0))
    
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
        """Construye la sección inferior con 10 filas fijas (Var 0 a Var 9) editables."""
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
        
        # Indexar variables existentes por su número
        existing_vars = {}
        for var_name, var_value in self.variable_fields:
            upper = var_name.upper()
            if upper.startswith("TABLACAMPO"):
                try:
                    idx = int(upper[10:])
                    existing_vars[idx] = (var_name, str(var_value).strip() if var_value else "")
                except ValueError:
                    pass
            elif upper.startswith("VAR"):
                try:
                    idx = int(upper[3:])
                    existing_vars[idx] = (var_name, str(var_value).strip() if var_value else "")
                except ValueError:
                    pass
        
        # Guardar qué nombres de columna existen realmente en la BD
        # para no intentar hacer UPDATE de columnas que no existen
        self._db_variable_names = set()
        for var_name, _ in self.variable_fields:
            self._db_variable_names.add(var_name)
        
        # Siempre crear 10 filas (Var 0 a Var 9)
        for i in range(10):
            if i in existing_vars:
                var_name, var_value = existing_vars[i]
            else:
                var_name = f"VAR{i}"
                var_value = ""
            self._create_variable_row(container, var_name, var_value)
    
    def _create_variable_row(self, parent, var_name, value):
        """
        Crea una fila con etiqueta "Var X" y Entry editable para el valor.
        El usuario puede escribir el nombre del campo de BD (ej: g_cfacli.FACTURA).
        
        Args:
            parent: Widget padre
            var_name: Nombre de la variable (ej: "VAR0")
            value: Valor de la variable
        """
        row_frame = tk.Frame(parent, bg=COLOR_SIDEBAR_BG)
        row_frame.pack(fill="x", pady=2)
        
        # Etiqueta "Var 0", "Var 1", etc.
        upper = var_name.upper()
        if upper.startswith("TABLACAMPO"):
            display_name = "Var " + upper[10:]
        else:
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
        
        # Entry EDITABLE para el valor
        entry = tk.Entry(
            row_frame,
            font=("Consolas", 8),
            bg="#FFFFFF",
            fg="#000000",
            relief="solid",
            borderwidth=1,
        )
        entry.insert(0, value)
        entry.pack(side="left", fill="x", expand=True)
        
        # Guardar referencia
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
                current_state = widget.cget("state")
                if current_state == "readonly":
                    widget.config(state="normal")
                    value = widget.get()
                    widget.config(state="readonly")
                else:
                    value = widget.get()
                result[field_name] = value
        
        return result

    def get_variable_values(self) -> dict:
        """
        Obtiene los valores actuales de las 10 variables (Var 0 a Var 9).
        
        Solo devuelve las que corresponden a columnas reales de la BD,
        para evitar intentar UPDATE de columnas que no existen.
        Incluye valores vacíos para que se guarde el borrado.
        
        Returns:
            Diccionario {nombre_columna: valor} para las variables de BD
        """
        db_names = getattr(self, '_db_variable_names', set())
        variables = {}
        for field_name, widget in self.field_widgets.items():
            upper = field_name.upper()
            is_var = (
                (upper.startswith("VAR") and len(upper) <= 4) or
                (upper.startswith("TABLACAMPO") and len(upper) <= 11)
            )
            if is_var and isinstance(widget, tk.Entry):
                # Solo incluir si la columna existe realmente en la BD
                if field_name in db_names:
                    variables[field_name] = widget.get().strip()
        return variables

    def set_variable_values(self, values: list):
        """
        Establece los valores de las 10 variables desde una lista de strings.
        
        Args:
            values: Lista de 10 strings con los valores para Var 0 a Var 9
        """
        for i, value in enumerate(values[:10]):
            # Buscar el widget por diferentes nombres posibles
            for key_pattern in [f"VAR{i}", f"TABLACAMPO{i}"]:
                for field_name, widget in self.field_widgets.items():
                    if field_name.upper() == key_pattern and isinstance(widget, tk.Entry):
                        widget.delete(0, tk.END)
                        widget.insert(0, value or "")
                        break
