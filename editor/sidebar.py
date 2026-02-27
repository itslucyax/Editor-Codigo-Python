# -*- coding: utf-8 -*-
"""
Pnael lateral izquierdo del editor. Muestra metadatos del script (modelo, codigo) y botones de acciones (guardar, cargar).
y las variables de entorno Var0 - Var9 (si existen en la base de datos) para referencia del usuario.
"""
from email import header
import tkinter as tk
from turtle import left
from config import (
    COLOR_FONDO,
    COLOR_LINEAS_BG,
    COLOR_LINEAS_FG,
    COLOR_BARRA_ESTADO_BG, 
    COLOR_BARRA_ESTADO_FG,
    COLOR_VARIABLE,
    COLOR_KEYWORD,
    COLOR_TEXTO
)

#Colores especificos para el sidebar/panel lateral
_BGV            = COLOR_LINEAS_BG   # Fondo general lateral
_BG_ROW_HOVER   = "#2a2a72"       # Color de fondo al pasar el mouse sobre una fila de variable
_BORDER         = "#333338"       #Color de borde entre filas
_HEADER_FG      = "#555566"       #texto cabecera (modelo, codigo)
_LABEL_FG       = COLOR_LINEAS_FG   # Color de texto de las variables
_VALUE_FG       = COLOR_TEXTO       # Color de texto del valor de las variables
_ACCENT         = COLOR_KEYWORD     # Color de texto de las etiquetas "Var0", "Var1", etc.
_VAR_FG         = COLOR_VARIABLE    # Color de texto del nombre de la variable (ej: "Var0")
_VAR_VALUE_FG   = "#7a7a8a"       # Color de texto del valor de la variable (ej: "Valor de Var0")
_EMPTY_FG       = "#3d3d45"       # valor vacio

_FONT_UI = ("Segoe UI", 9)
_FONT_MONO = ("Courier New", 9)
_FONT_HEADER = ("Segoe UI", 10, "bold")

#Datos hardcodeados para mostrar en el sidebar (en lugar de cargar de la base de datos)
#En la version final, se cargaran dinamicamente segun el script que se abra
_PLACEHOLDER_VARS = [
    ("Var0", "Valor de Var0"),
    ("Var1", "Valor de Var1"),
    ("Var2", "Valor de Var2"),
    ("Var3", "Valor de Var3"),
    ("Var4", "Valor de Var4"),
    ("Var5", "Valor de Var5"),
    ("Var6", "Valor de Var6"),
    ("Var7", "Valor de Var7"),
    ("Var8", "Valor de Var8"),
    ("Var9", "") #vacio para probar color de valor vacio
]

class Sidebar(tk.Frame):
    """
    Panel lateral izquierdo que muestra metadatos del script y variables de entorno.
    
    Args:
        parent: Widget padre (normalmente la ventana principal)
        modelo: Valor MODELO del script (para mostrar)
        codigo: Valor CODIGO del script (para mostrar)
        variables: Lista de tuplas (nombre, valor) de variables de entorno a mostrar
    """
    WIDTH = 250 #ancho fijo del sidebar

    def __init__(self, parent, modelo="", codigo="", variables=None):
        super().__init__(parent, bg=_BGV, width=250)
        self.modelo = modelo
        self.codigo = codigo
        self.variables = variables if variables is not None else _PLACEHOLDER_VARS
        
        self._build()
    
    #----------------------------------------------------------------------------------------------------
    #CONSTRUCCION DE LA INTERFAZ DEL SIDEBAR
    #----------------------------------------------------------------------------------------------------
    def _build(self):
        self._build_meta()
        self._build_separator()
        self._build_vars()
    
    def _build_separator(self):
        """Agrega una linea separadora entre la sección de metadatos y la de variables."""
        separator = tk.Frame(self, bg=_BORDER, height=1)
        separator.pack(fill="x", pady=10)
    
    def _build_meta(self):
        """Construye la sección de metadatos (modelo, codigo)."""
        header = tk.Label(self, text="Script Metadata", bg=_BGV, fg=_HEADER_FG, font=_FONT_HEADER)
        header.pack(pady=(10, 5))

        modelo_label = tk.Label(self, text=f"Modelo: {self.modelo}", bg=_BGV, fg=_LABEL_FG, font=_FONT_UI)
        modelo_label.pack(anchor="w", padx=10)

        codigo_label = tk.Label(self, text=f"Codigo: {self.codigo}", bg=_BGV, fg=_LABEL_FG, font=_FONT_UI)
        codigo_label.pack(anchor="w", padx=10)
    
    def _build_vars(self):
        """Construye la sección de variables de entorno."""
        vars_header = tk.Label(self, text="Environment Variables", bg=_BGV, fg=_HEADER_FG, font=_FONT_HEADER)
        vars_header.pack(pady=(10, 5))

        for var_name, var_value in self.variables:
            var_frame = tk.Frame(self, bg=_BGV)
            var_frame.pack(fill="x", padx=10, pady=2)

            name_label = tk.Label(var_frame, text=var_name, bg=_BGV, fg=_VAR_FG, font=_FONT_MONO)
            name_label.pack(side="left")

            value_label = tk.Label(var_frame, text=var_value if var_value else "(empty)", bg=_BGV,
                                   fg=_VAR_VALUE_FG if var_value else _EMPTY_FG, font=_FONT_MONO)
            value_label.pack(side="right")
        
        #Ajustar scroll region cuando cambia el tamaño del inner frame
        def _on_inner_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def _on_canvas_configure(event):
            #Ajustar el ancho del inner frame al ancho del canvas
            canvas.itemconfig(inner_frame_id, width=event.width)
        
        inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        #Scroll rueda raton
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        #Filas de variables
        for i, (nombre, valor) in enumerate(self.variables):
            self._var_row(inner, i, nombre, valor)
            """
            var_frame = tk.Frame(inner, bg=_BGV)
            var_frame.pack(fill="x", padx=10, pady=2)

            name_label = tk.Label(var_frame, text=nombre, bg=_BGV, fg=_VAR_FG, font=_FONT_MONO)
            name_label.pack(side="left")

            value_label = tk.Label(var_frame, text=valor if valor else "(empty)", bg=_BGV,
                                   fg=_VAR_VALUE_FG if valor else _EMPTY_FG, font=_FONT_MONO)
            value_label.pack(side="right")
            """
        
    #----------------------------------------------------------------------------------------------------
    #CONSTRUCCION DE LA INTERFAZ DEL SIDEBAR
    #----------------------------------------------------------------------------------------------------

    def _section_header(self, parent, text):
        """Crea un header para una sección del sidebar."""
        return tk.Label(parent, text=text, bg=_BGV, fg=_HEADER_FG, font=_FONT_HEADER)
    
    #Barra de acento izquierda del nombre de la variable
    tk.Frame(header, bg=_ACCENT, width=4).pack(side="left", fill="y", padx=(0, 5))

    tk.Label(header, text=nombre, bg=_BGV, fg=_VAR_FG, font=_FONT_MONO).pack(side="left")
    tk.Label(header, text=valor if valor else "(empty)", bg=_BGV, fg=_VAR_VALUE_FG if valor else _EMPTY_FG, font=_FONT_MONO).pack(side="right")

    fg = _ACCENT if accent else _VALUE_FG
    tk.Label(
        row,
        text=value,
        bg=_BG,
        fg=fg,
        font=_FONT_MONO,
        anchor="w",
    ).pack(side=left, fill="x", expand=True)

    def _var_row(self, parent, index, nombre, valor):
        """Fila variable: indice, nombre y valor"""
        row = tk.Frame(parent, bg=_BGV)
        row.pack(fill="x", padx=10, pady=2)
    
        #Hover
        def _enter(event):
            row.configure(bg=_BG_ROW_HOVER)
        def _leave(event):
            row.configure(bg=_BGV)
        row.bind("<Enter>", _enter)
        row.bind("<Leave>", _leave)

        #Indioce (0000, 0001, etc.)
        tk.Label(
            row,
            text=f"{index:04d}",
            bg=_BGV,
            fg=_ACCENT,
            font=_FONT_MONO,
            width=4
        ).pack(side="left", padx=(0, 5))

        #Nombre de variable
        tk.Label(
            row,
            text=nombre,
            bg=_BGV,
            fg=_VAR_FG,
            font=_FONT_MONO
        ).pack(side="left")

        #Separador vetical
        tk.Frame(row, bg=_BORDER, width=1).pack(side="left", fill="y", padx=5)

        #Valor (o placeholder si esta vacio)
        es_vacio = not valor
        tk.Label(
            row,
            text=valor if valor else "(empty)",
            bg=_BGV,
            fg=_VAR_VALUE_FG if not es_vacio else _EMPTY_FG,
            font=_FONT_MONO,
            anchor="w",
            padx=6
        ).pack(side="left", fill="x", expand=True)

#----------------------------------------------------------------------------------------------------
#   API para cuando se coencte la DB
#----------------------------------------------------------------------------------------------------

def actualizar_variables(self, variables: list):
    """Reemplaza las variables mostradas:
    Args:
        variables: Lista de tuplas (nombre, valor) ej: 
        [("Var0", "Valor de Var0"), ("Var1", "Valor de Var1"), ...]
    """
    self.variables = variables
    #Reconstruir la sección de variables (en lugar de actualizar cada fila individualmente)
    # (metodo sencillo: detruir y reconstruir el frame de vars)
    for widget in self.vars_frame.winfo_children():
        widget.destroy()
    self._build_vars_section(self.vars_frame)

    def actualizar_meta(self, modelo: str, codigo: str):
        """Actualiza los metadatos mostrados (modelo, codigo)
        y reconstruye la sección de metadatos para reflejar los cambios.
        Util cuando se carga un script distinto sin cerrar la ventana.
        """
        if modelo is not None:
            self.modelo = modelo
        if codigo is not None:
            self.codigo = codigo
        if tipo is not None:
            self.tipo = tipo
        if grupo is not None:
            self.grupo = grupo
        if modelo is not None or codigo is not None:
            for widget in self.meta_frame.winfo_children():
                widget.destroy()
            self._build_meta_section(self.meta_frame)
        