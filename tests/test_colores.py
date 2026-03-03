# -*- coding: utf-8 -*-
"""Script de diagnostico para verificar colores"""
import tkinter as tk
from config import *

print("=== DIAGNOSTICO DE COLORES ===")
print(f"COLOR_FONDO: {COLOR_FONDO}")
print(f"COLOR_TEXTO: {COLOR_TEXTO}")
print(f"COLOR_KEYWORD: {COLOR_KEYWORD}")
print(f"COLOR_STRING: {COLOR_STRING}")
print(f"COLOR_COMMENT: {COLOR_COMMENT}")

# Test rapido de Tkinter
root = tk.Tk()
root.withdraw()
text = tk.Text(root)
text.configure(fg=COLOR_TEXTO, bg=COLOR_FONDO)
text.tag_configure("keyword", foreground=COLOR_KEYWORD)

# Verificar que el tag se aplico
text.insert("1.0", "Sub Test")
text.tag_add("keyword", "1.0", "1.3")

# Ver la configuracion del tag
keyword_config = text.tag_cget("keyword", "foreground")
print(f"Tag keyword foreground: {keyword_config}")
print(f"Text fg: {text.cget('fg')}")

root.destroy()
print("=== FIN DIAGNOSTICO ===")
