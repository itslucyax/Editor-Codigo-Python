# -*- coding: utf-8 -*-
"""
Widget para mostrar numeros de linea sincronizados con el Text principal.
"""

import tkinter as tk
from config import COLOR_LINEAS_BG, COLOR_LINEAS_FG, FUENTE_EDITOR


class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(
            master,
            width=50,
            bg=COLOR_LINEAS_BG,
            highlightthickness=0,
            **kwargs
        )

        self.text_widget = text_widget
        # Usar fuente monoespaciada para los números
        try:
            import tkinter.font as tkfont
            self.font = tkfont.Font(family="Consolas", size=12)
        except Exception:
            self.font = FUENTE_EDITOR
        self.fg = COLOR_LINEAS_FG

        # Eventos que pueden cambiar el número de líneas o el scroll
        self.text_widget.bind("<<Change>>", self.redraw)
        self.text_widget.bind("<Configure>", self.redraw)
        self.text_widget.bind("<KeyRelease>", self.redraw)
        self.text_widget.bind("<MouseWheel>", self.redraw)
        self.text_widget.bind("<ButtonRelease-1>", self.redraw)
        self.text_widget.bind("<Return>", self.redraw)
        self.text_widget.bind("<BackSpace>", self.redraw)
        self.text_widget.bind("<Delete>", self.redraw)
        
        # Forzar redibujado inicial después de que el widget esté visible
        self.after(100, self.redraw)

    def redraw(self, event=None):
        """Redibuja los números de línea con padding de ceros."""
        self.delete("all")

        # Intentar obtener información del widget
        try:
            # Obtener el número total de líneas para calcular el padding
            total_lines = int(self.text_widget.index('end-1c').split('.')[0])
            num_digits = len(str(total_lines))
            # Ancho fijo para la barra azul (puedes ajustar este valor)
            barra_width = 50 + (num_digits-2)*12
            if self.winfo_width() != barra_width:
                self.configure(width=barra_width)
            # Obtener la primera línea visible
            i = self.text_widget.index("@0,0")
            while True:
                dline = self.text_widget.dlineinfo(i)
                if dline is None:
                    break
                y = dline[1]
                height = dline[3] if len(dline) > 3 else 14
                linenum = int(str(i).split(".")[0])
                # Formatear con padding de ceros
                linenum_str = str(linenum).zfill(num_digits)
                # Centrar verticalmente usando la altura de la línea
                y_pos = int(y + (height / 2) + 1)  # ligero ajuste hacia abajo
                # Dibujar alineado a la derecha, ocupando todo el ancho
                self.create_text(
                    barra_width - 5,
                    y_pos,
                    anchor="e",
                    text=linenum_str,
                    font=self.font,
                    fill=self.fg,
                )
                i = self.text_widget.index(f"{i}+1line")
        except (tk.TclError, ValueError):
            # Si hay algún error, simplemente intentarlo de nuevo después
            self.after(50, self.redraw)