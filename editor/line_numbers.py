"""
Widget para mostrar numeros de linea sincronizados con el Text principal.
"""

import tkinter as tk
from config import COLOR_LINEAS_BG, COLOR_LINEAS_FG, FUENTE_EDITOR

class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, width=40, bg=COLOR_LINEAS_BG,
                         highlightthickness=0, **kwargs)
        self.text_widget = text_widget
        self.font = FUENTE_EDITOR
        self.fg = COLOR_LINEAS_FG
        self.text_widget.bind("<<Change>>", self.redraw)
        self.text_widget.bind("<Configure>", self.redraw)
        self.text_widget.bind("<KeyRelease>", self.redraw)
        self.text_widget.bind("<MouseWheel>", self.redraw)
        self.text_widget.bind("<ButtonRelease-1>", self.redraw)
	self.text_widget.bind("<<Modified>>", self.redraw)
	self.text_widget.bind("<Return>", self.redraw)
	self.text_widget.bind("<BackSpace>", self.redraw)
	self.text_widget.bind("<Delete>", self.redraw)

    def redraw(self, event=None):
        """Redibuja los números de linea."""
        self.delete("all")
        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(
                30, y+2,
                anchor="ne",
                text=linenum,
                font=self.font,
                fill=self.fg
            )
            i = self.text_widget.index(f"{i}+1line")
