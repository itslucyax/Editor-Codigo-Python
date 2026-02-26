# -*- coding: utf-8 -*-
"""
Punto de entrada del editor: analiza argumentos y lanza la interfaz.
"""

import argparse
from editor.app import EditorApp

# Texto de ejemplo (código VB) que aparece si no se pasa un script real.
TEXTO_EJEMPLO = """' Script de ejemplo - Editor VBS
' Puedes editar este codigo

Sub Main()
    Dim x As Integer
    Dim nombre As String
    
    x = 10
    nombre = "Mundo"
    
    If x > 5 Then
        MsgBox "Hola " & nombre
    Else
        MsgBox "El valor es menor"
    End If
    
    Call MiFuncion(x)
End Sub

Function MiFuncion(valor)
    Dim resultado
    resultado = valor * 2
    MiFuncion = resultado
End Function
"""

def main():
    parser = argparse.ArgumentParser(description="Editor de scripts VB/VBS")
    parser.add_argument("--server", help="Servidor SQL Server")
    parser.add_argument("--database", help="Nombre de la base de datos")
    parser.add_argument("--table", help="Tabla de scripts (default: G_Scripts)", default="G_Scripts")
    parser.add_argument("--script-id", help="ID de script a editar")
    parser.add_argument("--user", help="Usuario SQL Server")
    parser.add_argument("--password", help="Contraseña SQL Server")

    args = parser.parse_args()
    # Fase 1: Solo abrimos editor con texto de ejemplo
    app = EditorApp(inicial_text=TEXTO_EJEMPLO)
    app.mainloop()

if __name__ == "__main__":
    main()
