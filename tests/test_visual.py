# -*- coding: utf-8 -*-
"""Test visual de colores"""
import tkinter as tk

# Colores VS Code
COLOR_FONDO = "#1e1e1e"
COLOR_TEXTO = "#d4d4d4"
COLOR_KEYWORD = "#569cd6"
COLOR_STRING = "#ce9178"
COLOR_COMMENT = "#6a9955"
COLOR_NUMBER = "#b5cea8"

root = tk.Tk()
root.title("Test de Colores")
root.geometry("600x400")

text = tk.Text(root, bg=COLOR_FONDO, fg=COLOR_TEXTO, font=("Consolas", 14))
text.pack(fill="both", expand=True)

# Configurar tags
text.tag_configure("keyword", foreground=COLOR_KEYWORD)
text.tag_configure("string", foreground=COLOR_STRING)
text.tag_configure("comment", foreground=COLOR_COMMENT)
text.tag_configure("number", foreground=COLOR_NUMBER)

# Insertar texto de prueba
text.insert("end", "' Comentario en verde\n")
text.tag_add("comment", "1.0", "1.end")

text.insert("end", "Sub ")
text.tag_add("keyword", "2.0", "2.3")
text.insert("end", "Main()\n")

text.insert("end", "    x = ")
text.insert("end", "10")
text.tag_add("number", "3.8", "3.10")
text.insert("end", "\n")

text.insert("end", '    MsgBox ')
text.insert("end", '"Hola Mundo"')
text.tag_add("string", "4.11", "4.23")
text.insert("end", "\n")

text.insert("end", "End Sub")
text.tag_add("keyword", "5.0", "5.3")
text.tag_add("keyword", "5.4", "5.7")

print("Ventana abierta - verifica los colores")
root.mainloop()
