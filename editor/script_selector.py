# -*- coding: utf-8 -*-
"""
Selector de scripts con Combobox para cambio rápido entre scripts.

Permite al usuario seleccionar entre varios scripts disponibles.
Al cambiar la selección, el contenido del editor se actualiza automáticamente.
"""

import tkinter as tk
from tkinter import ttk
from config import COLOR_FONDO, COLOR_BARRA_ESTADO_BG, COLOR_BARRA_ESTADO_FG


class ScriptSelector(tk.Frame):
    """
    Combobox "Mostrar SCRIPT" para carga rápida de scripts.
    
    Se coloca en la parte superior del área del editor.
    Al seleccionar una opción, carga el script correspondiente.
    
    Args:
        master: Widget padre
        scripts_list: Lista de diccionarios con claves "label" y "content".
                      Ej: [{"label": "Script 1", "content": "Sub Main()..."}]
                      También acepta lista simple de strings (se auto-etiquetan).
        on_select_callback: Función que se llama al seleccionar un script.
                           Recibe (index: int, script_data: dict).
    """

    def __init__(self, master, scripts_list=None, on_select_callback=None, context_type=None):
        super().__init__(master, bg=COLOR_BARRA_ESTADO_BG, padx=8, pady=4)
        self.scripts = self._normalize_scripts(scripts_list or [])
        self.on_select = on_select_callback
        self.context_type = context_type  # 'documento' | 'plantilla' | None
        self._build_ui()

    @staticmethod
    def _normalize_scripts(scripts_list):
        """
        Normaliza la lista de scripts a formato [{label, content}].
        Acepta:
          - Lista de dicts: [{"label": "...", "content": "..."}]
          - Lista de strings: ["script1", "script2"] → auto-etiquetados
          - Lista de tuplas: [("label", "content"), ...]
        """
        normalized = []
        for i, item in enumerate(scripts_list):
            if isinstance(item, dict):
                normalized.append({
                    "label": item.get("label", f"Script {i}"),
                    "content": item.get("content", "")
                })
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                normalized.append({
                    "label": str(item[0]),
                    "content": str(item[1])
                })
            elif isinstance(item, str):
                normalized.append({
                    "label": f"Script {i}",
                    "content": item
                })
        return normalized

    def _build_ui(self):
        """Construye la interfaz del selector."""
        # Label dinámico según contexto
        label_text = "Mostrar Plantilla:" if self.context_type == "plantilla" else "Mostrar SCRIPT:"
        tk.Label(
            self,
            text=label_text,
            bg=COLOR_BARRA_ESTADO_BG,
            fg=COLOR_BARRA_ESTADO_FG,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 8))

        # Estilo para el Combobox
        style = ttk.Style()
        style.configure(
            "Script.TCombobox",
            fieldbackground="#3c3c3c",
            background="#3c3c3c",
            foreground="#cccccc",
        )

        # Combobox
        labels = [s["label"] for s in self.scripts]
        self.combo_var = tk.StringVar()
        self.combo = ttk.Combobox(
            self,
            textvariable=self.combo_var,
            values=labels,
            state="readonly",
            font=("Segoe UI", 9),
            width=40,
            style="Script.TCombobox",
        )
        self.combo.pack(side="left", padx=(0, 8))
        self.combo.bind("<<ComboboxSelected>>", self._on_select)

        # Seleccionar el primero por defecto
        if self.scripts:
            self.combo.current(0)

        # Indicador de total
        unit = "plantillas" if self.context_type == "plantilla" else "scripts"
        self.count_label = tk.Label(
            self,
            text=f"{len(self.scripts)} {unit}",
            bg=COLOR_BARRA_ESTADO_BG,
            fg="#888888",
            font=("Segoe UI", 8),
        )
        self.count_label.pack(side="left")

    def _on_select(self, event=None):
        """Callback interno cuando el usuario selecciona un script."""
        idx = self.combo.current()
        if 0 <= idx < len(self.scripts) and self.on_select:
            self.on_select(idx, self.scripts[idx])

    def set_scripts(self, scripts_list):
        """
        Actualiza la lista de scripts del selector.
        
        Args:
            scripts_list: Nueva lista de scripts (mismos formatos que el constructor)
        """
        self.scripts = self._normalize_scripts(scripts_list)
        labels = [s["label"] for s in self.scripts]
        self.combo["values"] = labels
        self.count_label.config(text=f"{len(self.scripts)} scripts")
        if self.scripts:
            self.combo.current(0)

    def get_current_index(self) -> int:
        """Devuelve el índice del script seleccionado actualmente."""
        return self.combo.current()

    def get_current_script(self) -> dict:
        """Devuelve el diccionario del script seleccionado actualmente."""
        idx = self.combo.current()
        if 0 <= idx < len(self.scripts):
            return self.scripts[idx]
        return {"label": "", "content": ""}