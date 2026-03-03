# -*- coding: utf-8 -*-
r"""
Punto de entrada del editor - DINÁMICO SIN HARDCODEO.

El programa detecta automáticamente la estructura de la BD y se adapta.
Configuración via: variables de entorno, archivo JSON, o parámetros CLI.

Uso desde otro sistema:
    editor.exe --config-file config.json
    
    O bien:
    
    set EDITOR_SERVER=servidor\instancia
    set EDITOR_DATABASE=MIBD
    set EDITOR_TABLE=G_SCRIPT
    set EDITOR_KEY_COLUMNS=MODELO,CODIGO
    set EDITOR_KEY_VALUES=T01,BOBINADO
    set EDITOR_CONTENT_COLUMN=SCRIPT
    set EDITOR_USER=sa
    set EDITOR_PASSWORD=clave
    editor.exe

Cero hardcodeo: Todo configurable externamente.

SIN PARÁMETROS: Si ejecutas solo 'python main.py', se abre en modo local sin BD.
"""

import argparse
import sys

from editor.logger import logger
from db.connection import (
    DatabaseConnection,
    parse_connection_string,
    resolve_table_for_context,
    CONTEXT_DOCUMENTO,
    CONTEXT_PLANTILLA,
    DEFAULT_TABLES,
)
from editor.app import EditorApp
from config_loader import ConfigLoader

# Texto de ejemplo si no hay BD
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
        description="Editor dinámico de scripts con auto-detección de estructura de BD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
MODO RÁPIDO (sin parámetros):
  python main.py
  → Se abre en modo local con script de ejemplo (sin conectar a BD)

CONFIGURACIÓN MULTI-FUENTE (prioridad: CLI > ENV > JSON):

1. Archivo de configuración JSON:
   --config-file editor_config.json

2. Variables de entorno (prefijo EDITOR_):
   EDITOR_SERVER, EDITOR_DATABASE, EDITOR_TABLE
   EDITOR_KEY_COLUMNS (formato: MODELO,CODIGO)
   EDITOR_KEY_VALUES (formato: T01,SCRIPT001)
   EDITOR_CONTENT_COLUMN, EDITOR_USER, EDITOR_PASSWORD

3. Parámetros de línea de comandos:
   --server, --database, --table
   --key-columns "MODELO,CODIGO"
   --key-values "T01,SCRIPT001"
   --content-column SCRIPT
   --user sa --password clave

Ejemplo completo:
  editor.exe --server "servidor\instancia" --database "MIBD" --table "G_SCRIPT" \
             --key-columns "MODELO,CODIGO" --key-values "T01,BOBINADO" \
             --content-column "SCRIPT" --user "sa" --password "clave"

O simplemente:
  editor.exe --config-file config.json
"""
    )

    # Archivo de configuración
    parser.add_argument("--config-file", help="Archivo JSON con toda la configuración")

    # Connection string completa (alternativa a parámetros individuales)
    parser.add_argument("--connection-string", 
                        help="Connection string completa de SQL Server")

    # Parámetros individuales de conexión
    parser.add_argument("--server", help="Servidor SQL Server")
    parser.add_argument("--database", help="Base de datos")
    parser.add_argument("--table", help="Nombre de la tabla")
    parser.add_argument("--user", help="Usuario SQL")
    parser.add_argument("--password", help="Contraseña SQL")
    parser.add_argument("--driver", help="Driver ODBC")
    parser.add_argument("--trust-cert", action="store_true",
                        help="TrustServerCertificate=Yes")

    # Estructura del registro
    parser.add_argument("--key-columns",
                        help="Columnas clave separadas por coma (ej: MODELO,CODIGO)")
    parser.add_argument("--key-values",
                        help="Valores de las claves separados por coma (ej: T01,SCRIPT001)")
    parser.add_argument("--content-column", default="SCRIPT",
                        help="Columna con el contenido del script")

    # Columnas editables (opcional - por defecto se detecta automáticamente)
    parser.add_argument("--editable-columns",
                        help="Columnas editables por el usuario (ej: GRUPO,DESCRIPCION)")

    # Contexto de trabajo: Plantilla vs Documento
    parser.add_argument("--tipo", choices=["documento", "plantilla"],
                        default="documento",
                        help="Contexto de trabajo: 'documento' o 'plantilla'. "
                             "Determina la tabla de BD automáticamente.")
    parser.add_argument("--table-documento",
                        help="Tabla específica para modo documento (default: G_SCRIPT)")
    parser.add_argument("--table-plantilla",
                        help="Tabla específica para modo plantilla (default: G_SCRIPT_PLANTILLA)")

    # Modo local sin BD
    parser.add_argument("--local", action="store_true",
                        help="Modo local sin conexión a BD (solo para pruebas)")

    args = parser.parse_args()

    # ========================================================================
    # CARGA DE CONFIGURACIÓN MULTI-FUENTE
    # ========================================================================
    config = ConfigLoader()
    
    # 1. Cargar desde archivo JSON (si se especifica)
    if args.config_file:
        config.load_from_file(args.config_file)
    
    # 2. Cargar desde variables de entorno
    config.load_from_env()
    
    # 3. Preparar args de CLI para merge
    cli_args = {}
    if args.connection_string:
        cli_args["connection_string"] = args.connection_string
    if args.server:
        cli_args["server"] = args.server
    if args.database:
        cli_args["database"] = args.database
    if args.table:
        cli_args["table"] = args.table
    if args.user:
        cli_args["user"] = args.user
    if args.password:
        cli_args["password"] = args.password
    if args.driver:
        cli_args["driver"] = args.driver
    if args.trust_cert:
        cli_args["trust_cert"] = True
    if args.content_column:
        cli_args["content_column"] = args.content_column
    if args.key_columns:
        cli_args["key_columns"] = [c.strip() for c in args.key_columns.split(",")]
    if args.key_values:
        cli_args["key_values"] = [v.strip() for v in args.key_values.split(",")]
    if args.editable_columns:
        cli_args["editable_columns"] = [c.strip() for c in args.editable_columns.split(",")]
    # Contexto de trabajo (Plantilla / Documento)
    cli_args["tipo"] = args.tipo
    if args.table_documento:
        cli_args["table_documento"] = args.table_documento
    if args.table_plantilla:
        cli_args["table_plantilla"] = args.table_plantilla
    
    # 4. Combinar todas las fuentes
    final_config = config.merge(cli_args)
    
    # ========================================================================
    # MODO LOCAL (sin BD) - Por defecto si no hay configuracion
    # ========================================================================
    # Si no hay configuracion de conexion minima, ir a modo local automaticamente
    has_connection_string = bool(final_config.get("connection_string"))
    has_minimal_config = has_connection_string or bool(
        final_config.get("server") and 
        final_config.get("database") and 
        final_config.get("key_columns") and 
        final_config.get("key_values")
    )
    
    if args.local or not has_minimal_config:
        if not has_minimal_config and not args.local:
            print("INFO: Sin configuracion detectada. Abriendo en modo local...")
            print("      (Para conectar a BD, usa --config-file o --server, --database, etc.)\n")
        logger.info("Modo local sin conexion a BD")
        
        # Datos de ejemplo para que el sidebar muestre contenido en modo local
        ejemplo_record = {
            "MODELO": "T01",
            "CODIGO": "BOBINADO",
            "TIPO": "VBS",
            "GRUPO": "PRODUCCION",
            "DESCRIPCION": "Script de ejemplo para pruebas locales",
            "SCRIPT": TEXTO_EJEMPLO,
            "TABLACAMPO0": "valor_0",
            "TABLACAMPO1": "valor_1",
            "TABLACAMPO2": "valor_2",
            "TABLACAMPO3": "valor_3",
            "TABLACAMPO4": "valor_4",
            "TABLACAMPO5": "",
            "TABLACAMPO6": "",
            "TABLACAMPO7": "",
            "TABLACAMPO8": "",
            "TABLACAMPO9": "",
        }
        ejemplo_keys = ["MODELO", "CODIGO"]
        ejemplo_editable = ["GRUPO"]
        
        # Scripts de ejemplo para el desplegable en modo local
        ejemplo_scripts = [
            {"label": "BOBINADO", "content": TEXTO_EJEMPLO, "key_values": ["T01", "BOBINADO"]},
            {"label": "FACTURA", "content": "' Script FACTURA\nSub Factura()\n    Dim total As Double\n    total = 100.50\n    MsgBox \"Total: \" & total\nEnd Sub", "key_values": ["T01", "FACTURA"]},
            {"label": "ETIQUETA", "content": "' Script ETIQUETA\nSub Etiqueta()\n    Dim codigo As String\n    codigo = var0\n    MsgBox \"Codigo: \" & codigo\nEnd Sub", "key_values": ["T01", "ETIQUETA"]},
        ]
        
        app = EditorApp(
            inicial_text=TEXTO_EJEMPLO,
            db=None,
            record=ejemplo_record,
            key_columns=ejemplo_keys,
            content_column="SCRIPT",
            editable_columns=ejemplo_editable,
            scripts_list=ejemplo_scripts,
            context_type=final_config.get("tipo", CONTEXT_DOCUMENTO)
        )
        app.mainloop()
        return
    
    # ========================================================================
    # VALIDAR CONFIGURACIÓN REQUERIDA
    # ========================================================================
    try:
        config.validate_connection_config()
        config.validate_script_config()
    except ValueError as e:
        logger.error("Configuración incompleta: %s", e)
        print(f"\nERROR: {e}\n", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    # ========================================================================
    # CONECTAR A BD Y CARGAR REGISTRO COMPLETO
    # ========================================================================
    db = None
    record = {}
    contenido = TEXTO_EJEMPLO

    # Resolver contexto de trabajo (Plantilla vs Documento)
    context_type = final_config.get("tipo", CONTEXT_DOCUMENTO)
    
    # Construir mapeo de tablas personalizado si se proporcionaron
    custom_table_map = dict(DEFAULT_TABLES)  # copiar defaults
    if final_config.get("table_documento"):
        custom_table_map[CONTEXT_DOCUMENTO] = final_config["table_documento"]
    if final_config.get("table_plantilla"):
        custom_table_map[CONTEXT_PLANTILLA] = final_config["table_plantilla"]
    
    try:
        logger.info("=== INICIANDO CONEXIÓN A BASE DE DATOS ===")
        logger.info("Contexto de trabajo: %s", context_type.upper())
        
        # ----------------------------------------------------------
        # Decidir cómo crear la conexión: connection_string o params
        # ----------------------------------------------------------
        conn_str_raw = final_config.get("connection_string")
        
        if conn_str_raw:
            # ---- Modo cadena de conexión (lo que el responsable pide) ----
            logger.info("Usando cadena de conexión proporcionada externamente")
            db = DatabaseConnection.from_connection_string(
                conn_str=conn_str_raw,
                context_type=context_type,
                table=final_config.get("table"),        # override manual si existe
                table_map=custom_table_map,
                content_column=final_config.get("content_column", "SCRIPT"),
            )
        else:
            # ---- Modo parámetros individuales (compatibilidad) ----
            resolved_table = resolve_table_for_context(
                context_type,
                table_override=final_config.get("table"),
                table_map=custom_table_map,
            )
            db = DatabaseConnection(
                server=final_config["server"],
                database=final_config["database"],
                table=resolved_table,
                user=final_config["user"],
                password=final_config["password"],
                driver=final_config.get("driver", "ODBC Driver 18 for SQL Server"),
                trust_server_certificate=final_config.get("trust_cert", True),
                content_column=final_config.get("content_column", "SCRIPT"),
                context_type=context_type,
            )
        
        logger.info("Servidor: %s", db.server)
        logger.info("Base de datos: %s", db.database)
        logger.info("Tabla (resuelta): %s", db.table)
        logger.info("Contexto: %s", db.context_type)
        
        db.connect()
        logger.info("✓ Conexión establecida correctamente")
        
        # Obtener esquema de la tabla
        schema = db.get_table_schema()
        logger.info("✓ Esquema detectado: %d columnas", len(schema))
        logger.debug("Columnas: %s", [col["name"] for col in schema])
        
        # Cargar registro completo con TODOS los campos
        key_columns = final_config["key_columns"]
        key_values = final_config["key_values"]
        
        logger.info("Cargando registro: %s", 
                    ", ".join(f"{k}={v}" for k, v in zip(key_columns, key_values)))
        
        record = db.get_record_full(key_columns, key_values)
        logger.info("✓ Registro cargado: %d campos", len(record))
        
        # Extraer contenido del script
        content_column = final_config.get("content_column", "SCRIPT")
        contenido = record.get(content_column, TEXTO_EJEMPLO)
        logger.info("✓ Script cargado: %d caracteres", len(contenido))
        
        logger.info("=== CARGA COMPLETADA EXITOSAMENTE ===")
        
    except Exception as e:
        logger.exception("Error fatal durante la carga")
        print(f"\n❌ ERROR: {e}\n", file=sys.stderr)
        sys.exit(1)
    
    # ========================================================================
    # LANZAR EDITOR CON DATOS DINÁMICOS
    # ========================================================================
    # Cargar lista de scripts dinámicamente desde BD (para el desplegable)
    scripts_list = final_config.get("scripts_list", [])
    
    if not scripts_list and db:
        try:
            scripts_list = db.get_scripts_for_model(
                key_columns=final_config["key_columns"],
                key_values=final_config["key_values"],
            )
            logger.info("Scripts disponibles en desplegable: %d", len(scripts_list))
        except Exception as e:
            logger.warning("No se pudo cargar lista de scripts: %s", e)
            scripts_list = []
    
    app = EditorApp(
        inicial_text=contenido,
        db=db,
        record=record,
        key_columns=final_config["key_columns"],
        content_column=final_config.get("content_column", "SCRIPT"),
        editable_columns=final_config.get("editable_columns", []),
        scripts_list=scripts_list,
        context_type=context_type
    )
    
    try:
        app.mainloop()
    finally:
        # Garantizar que la conexión se cierra aunque la app falle
        if db is not None:
            db.close()
            logger.info("Conexión cerrada")


if __name__ == "__main__":
    main()
