# -*- coding: utf-8 -*-
"""
Punto de entrada del editor: analiza argumentos y lanza la interfaz.

Uso desde la app de escritorio:
    editor.exe --server "SERVIDOR" --database "BD" --modelo "T01" --codigo "BOBINADO" \
               --content-column "SCRIPT" --user "usuario" --password "clave"

El trabajador solo pulsa un botón en la app; el informático configura el lanzamiento.
"""

import argparse
import sys

from db.connection import DatabaseConnection
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
    parser = argparse.ArgumentParser(
        description="Editor de scripts VB/VBS con conexión a SQL Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplo de uso:
  py -3 main.py --server "miservidor\\sql2019" --database "MIBD" \\
                --modelo "T01" --codigo "BOBINADO" \\
                --content-column "SCRIPT" --user "sa" --password "clave"
"""
    )

    # Conexión SQL Server
    parser.add_argument("--server", help="Servidor SQL Server (ej: servidor\\instancia)")
    parser.add_argument("--database", help="Nombre de la base de datos")
    parser.add_argument("--table", default="G_SCRIPT",
                        help="Nombre de la tabla (default: G_SCRIPT)")

    # Clave compuesta del script (argumentos separados)
    parser.add_argument("--modelo", help="Valor de la columna MODELO (nvarchar(3))")
    parser.add_argument("--codigo", help="Valor de la columna CODIGO (nvarchar(20))")

    # Columna del contenido (configurable)
    parser.add_argument("--content-column", default="SCRIPT",
                        help="Nombre de la columna con el contenido del script (default: SCRIPT)")

    # Autenticación SQL
    parser.add_argument("--user", help="Usuario SQL Server (SQL Authentication)")
    parser.add_argument("--password", help="Contraseña SQL Server")

    # Driver ODBC opcional
    parser.add_argument("--driver", default="ODBC Driver 18 for SQL Server",
                        help="Driver ODBC (default: ODBC Driver 18 for SQL Server)")

    args = parser.parse_args()

    db = None
    contenido = TEXTO_EJEMPLO
    modelo = args.modelo
    codigo = args.codigo

    # Si se pasan los parámetros de BD, intentamos conectar y cargar
    if args.server and args.database and modelo and codigo:
        try:
            db = DatabaseConnection(
                server=args.server,
                database=args.database,
                table=args.table,
                user=args.user,
                password=args.password,
                driver=args.driver,
                content_column=args.content_column,
            )
            db.connect()
            contenido = db.get_script(modelo, codigo)
        except Exception as e:
            print(f"Error al conectar o cargar script: {e}", file=sys.stderr)
            sys.exit(1)

    app = EditorApp(
        inicial_text=contenido,
        db=db,
        modelo=modelo,
        codigo=codigo,
    )
    app.mainloop()

    if db is not None:
        db.close()


if __name__ == "__main__":
    main()
