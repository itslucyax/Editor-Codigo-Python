import tkinter as tk
from pygments.lexers import VbNetLexer

root = tk.Tk()
root.title("Test - Editor de Código")
root.geometry("600x400")
root.configure(bg="#1e1e1e")

text = tk.Text(root, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 12),
               insertbackground="white")
text.pack(fill="both", expand=True, padx=10, pady=10)

text.insert("1.0", """' Script de ejemplo
Sub Main()
    Dim x As Integer
    x = 10
    If x > 5 Then
        MsgBox "Mayor que 5"
    End If
End Sub""")

lexer = VbNetLexer()
print(f"Pygments lexer cargado: {lexer.name}")

root.mainloop()
