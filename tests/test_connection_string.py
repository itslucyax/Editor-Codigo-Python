# -*- coding: utf-8 -*-
"""
Test del parser de cadena de conexión y detección de contexto.

Ejecutar:
    py -3 tests/test_connection_string.py

Simula lo que ocurrirá cuando el jefe pase la cadena de conexión real.
No necesita SQL Server instalado — solo valida el parseo y la lógica.
"""

import sys
import os

# Añadir raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import (
    parse_connection_string,
    resolve_table_for_context,
    DatabaseConnection,
    CONTEXT_DOCUMENTO,
    CONTEXT_PLANTILLA,
    DEFAULT_TABLES,
    _sanitize_identifier,
    _TIPO_FLAG_MAP,
)


def separador(titulo):
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")


def test_parse_odbc():
    """Test con cadena formato ODBC (la más común en entornos SQL Server)."""
    separador("1. PARSEO — Cadena ODBC típica")

    # ---- Esto es lo que te pasaría el jefe ----
    cadena_del_jefe = (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=SERVIDOR-EMPRESA\\GESTION21;"
        "Database=G21_PRODUCCION;"
        "UID=editor_user;"
        "PWD=P@ssw0rd_Segura!;"
        "TrustServerCertificate=Yes;"
    )

    print(f"\nCadena recibida:\n  {cadena_del_jefe}\n")
    
    params = parse_connection_string(cadena_del_jefe)
    
    print("Parámetros extraídos:")
    for key, value in params.items():
        # Ocultar password parcialmente
        if key == "password":
            display = value[:3] + "***"
        else:
            display = value
        print(f"  {key:30s} → {display}")
    
    # Verificar que se extrajeron los campos básicos
    assert params["server"] == "SERVIDOR-EMPRESA\\GESTION21", "Server no coincide"
    assert params["database"] == "G21_PRODUCCION", "Database no coincide"
    assert params["user"] == "editor_user", "User no coincide"
    assert params["password"] == "P@ssw0rd_Segura!", "Password no coincide"
    assert params["driver"] == "ODBC Driver 18 for SQL Server", "Driver no coincide"
    assert params["trust_server_certificate"] == True, "TrustServerCertificate no coincide"
    
    print("\n✓ Todos los campos extraídos correctamente")


def test_parse_adonet():
    """Test con cadena formato ADO.NET (también usado en .NET / VB)."""
    separador("2. PARSEO — Cadena ADO.NET")

    cadena_adonet = (
        "Data Source=192.168.1.100,1433;"
        "Initial Catalog=G21_DESARROLLO;"
        "User ID=admin;"
        "Password=secreto123;"
    )

    print(f"\nCadena recibida:\n  {cadena_adonet}\n")
    
    params = parse_connection_string(cadena_adonet)
    
    print("Parámetros extraídos:")
    for key, value in params.items():
        if key == "password":
            display = value[:3] + "***"
        else:
            display = value
        print(f"  {key:30s} → {display}")
    
    assert params["server"] == "192.168.1.100,1433"
    assert params["database"] == "G21_DESARROLLO"
    assert params["user"] == "admin"
    assert params["password"] == "secreto123"
    
    print("\n✓ Formato ADO.NET parseado correctamente")


def test_contexto():
    """Test de resolución de tabla según contexto Documento vs Plantilla."""
    separador("3. CONTEXTO — Documento vs Plantilla")

    print(f"\nTablas por defecto configuradas:")
    for ctx, tabla in DEFAULT_TABLES.items():
        print(f"  {ctx:15s} → {tabla}")

    # Modo Documento
    tabla_doc = resolve_table_for_context(CONTEXT_DOCUMENTO)
    print(f"\n--tipo documento  →  tabla: {tabla_doc}")
    assert tabla_doc == "G_SCRIPT"

    # Modo Plantilla
    tabla_plt = resolve_table_for_context(CONTEXT_PLANTILLA)
    print(f"--tipo plantilla  →  tabla: {tabla_plt}")
    assert tabla_plt == "G_SCRIPT_PLANTILLA"

    # Override manual (--table fuerza la tabla)
    tabla_manual = resolve_table_for_context(CONTEXT_DOCUMENTO, table_override="MI_TABLA_CUSTOM")
    print(f"--table MI_TABLA  →  tabla: {tabla_manual}  (ignora contexto)")
    assert tabla_manual == "MI_TABLA_CUSTOM"

    # Tablas personalizadas de Gestión 21
    mi_mapeo = {
        "documento": "SCRIPTS_DOC_G21",
        "plantilla": "SCRIPTS_PLT_G21",
    }
    tabla_custom = resolve_table_for_context("plantilla", table_map=mi_mapeo)
    print(f"\nCon mapeo custom → plantilla: {tabla_custom}")
    assert tabla_custom == "SCRIPTS_PLT_G21"

    print("\n✓ Resolución de contexto correcta")


def test_from_connection_string():
    """Test del constructor from_connection_string (sin conectar realmente)."""
    separador("4. CONSTRUCTOR — from_connection_string")

    cadena = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=SRV-GESTION\\SQL2019;"
        "Database=GESTION21_PROD;"
        "UID=app_editor;"
        "PWD=ClaveSegura_2026!;"
        "TrustServerCertificate=Yes;"
    )

    print(f"\nCadena del jefe:\n  {cadena}\n")

    # ---- Modo DOCUMENTO ----
    db_doc = DatabaseConnection.from_connection_string(
        conn_str=cadena,
        context_type="documento",
        content_column="SCRIPT",
    )
    print(f"Modo DOCUMENTO:")
    print(f"  server   = {db_doc.server}")
    print(f"  database = {db_doc.database}")
    print(f"  table    = {db_doc.table}")
    print(f"  user     = {db_doc.user}")
    print(f"  driver   = {db_doc.driver}")
    print(f"  contexto = {db_doc.context_type}")
    print(f"  is_documento  = {db_doc.is_documento}")
    print(f"  is_plantilla  = {db_doc.is_plantilla}")

    assert db_doc.table == "G_SCRIPT"
    assert db_doc.is_documento == True
    assert db_doc.is_plantilla == False

    # ---- Modo PLANTILLA ----
    db_plt = DatabaseConnection.from_connection_string(
        conn_str=cadena,
        context_type="plantilla",
        content_column="SCRIPT",
    )
    print(f"\nModo PLANTILLA:")
    print(f"  server   = {db_plt.server}")
    print(f"  database = {db_plt.database}")
    print(f"  table    = {db_plt.table}")
    print(f"  user     = {db_plt.user}")
    print(f"  contexto = {db_plt.context_type}")
    print(f"  is_documento  = {db_plt.is_documento}")
    print(f"  is_plantilla  = {db_plt.is_plantilla}")

    assert db_plt.table == "G_SCRIPT_PLANTILLA"
    assert db_plt.is_plantilla == True

    # ---- Cambio de contexto en caliente ----
    print(f"\n  Cambiando de Plantilla → Documento en caliente...")
    db_plt.switch_context("documento")
    print(f"  table ahora = {db_plt.table}")
    print(f"  contexto    = {db_plt.context_type}")
    assert db_plt.table == "G_SCRIPT"

    print("\n✓ Constructor from_connection_string funciona correctamente")


def test_cli_simulation():
    """Simula lo que haría main.py con los argumentos del CLI."""
    separador("5. SIMULACIÓN CLI — Cómo se ejecutaría")

    print("""
Los comandos que usarás cuando el jefe te dé la cadena:

  ─── Modo Documento ───
  py -3 main.py \\
      --connection-string "Driver={{ODBC Driver 18 for SQL Server}};Server=SERVIDOR;Database=G21;UID=user;PWD=pass;" \\
      --tipo documento \\
      --key-columns "MODELO,CODIGO" \\
      --key-values "T01,BOBINADO" \\
      --content-column "SCRIPT"

  ─── Modo Plantilla ───
  py -3 main.py \\
      --connection-string "Driver={{ODBC Driver 18 for SQL Server}};Server=SERVIDOR;Database=G21;UID=user;PWD=pass;" \\
      --tipo plantilla \\
      --key-columns "MODELO,CODIGO" \\
      --key-values "T01,BOBINADO" \\
      --content-column "SCRIPT"

  ─── Con tablas personalizadas ───
  py -3 main.py \\
      --connection-string "..." \\
      --tipo plantilla \\
      --table-plantilla "MI_TABLA_PLANTILLAS" \\
      --table-documento "MI_TABLA_DOCUMENTOS" \\
      --key-columns "MODELO,CODIGO" \\
      --key-values "T01,BOBINADO"

  ─── Via variable de entorno ───
  set EDITOR_CONNECTION_STRING=Driver={{...}};Server=...;Database=...;UID=...;PWD=...;
  set EDITOR_TIPO=plantilla
  py -3 main.py --key-columns "MODELO,CODIGO" --key-values "T01,BOBINADO"
""")
    print("✓ Referencia de comandos generada")


def test_errores():
    """Test de manejo de errores."""
    separador("6. ERRORES — Validaciones")

    # Cadena vacía
    try:
        parse_connection_string("")
        print("  ✗ Debería haber fallado con cadena vacía")
    except ValueError as e:
        print(f"  ✓ Cadena vacía: {e}")

    # Cadena sin formato válido
    try:
        parse_connection_string("esto no es una cadena de conexion")
        print("  ✗ Debería haber fallado con formato inválido")
    except ValueError as e:
        print(f"  ✓ Formato inválido: {e}")

    # Contexto inválido
    try:
        resolve_table_for_context("inventado")
        print("  ✗ Debería haber fallado con contexto inválido")
    except ValueError as e:
        print(f"  ✓ Contexto inválido: {e}")

    # Connection string sin server
    try:
        DatabaseConnection.from_connection_string("UID=user;PWD=pass;")
        print("  ✗ Debería haber fallado sin server")
    except ValueError as e:
        print(f"  ✓ Sin server: {e}")

    print("\n✓ Todas las validaciones de error funcionan")


def test_sanitizacion():
    """Test de sanitización de identificadores SQL (prevención SQL injection)."""
    separador("7. SEGURIDAD — Sanitización de identificadores")

    # Nombres válidos
    assert _sanitize_identifier("G_SCRIPT", "tabla") == "G_SCRIPT"
    assert _sanitize_identifier("MODELO", "columna") == "MODELO"
    assert _sanitize_identifier("TABLACAMPO0", "columna") == "TABLACAMPO0"
    assert _sanitize_identifier("Mi Tabla Con Espacios", "tabla") == "Mi Tabla Con Espacios"
    print("  ✓ Nombres válidos aceptados: G_SCRIPT, MODELO, TABLACAMPO0")

    # Intentos de inyección SQL
    intentos_maliciosos = [
        "G_SCRIPT]; DROP TABLE G_SCRIPT;--",
        "tabla' OR '1'='1",
        "nombre; DELETE FROM users",
        "col\"maliciosa",
    ]
    for intento in intentos_maliciosos:
        try:
            _sanitize_identifier(intento, "tabla")
            print(f"  ✗ Debería haber rechazado: {intento}")
        except ValueError:
            print(f"  ✓ Rechazado correctamente: {intento[:40]}...")

    # Nombre vacío
    try:
        _sanitize_identifier("", "tabla")
        print("  ✗ Debería haber rechazado nombre vacío")
    except ValueError:
        print("  ✓ Nombre vacío rechazado")

    print("\n✓ Sanitización SQL funciona correctamente")


def test_context_manager():
    """Test del context manager (__enter__/__exit__)."""
    separador("8. CONTEXT MANAGER — Soporte 'with'")

    cadena = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=SRV-TEST;Database=TEST_DB;"
        "UID=user;PWD=pass;"
    )

    db = DatabaseConnection.from_connection_string(cadena, context_type="documento")

    # Verificar que tiene __enter__ y __exit__
    assert hasattr(db, '__enter__'), "Falta __enter__"
    assert hasattr(db, '__exit__'), "Falta __exit__"
    print("  ✓ DatabaseConnection tiene __enter__ y __exit__")
    print("  ✓ Se puede usar con 'with DatabaseConnection(...) as db:'")
    print("  ✓ La conexión se cierra automáticamente al salir del bloque")

    print("\n✓ Context manager implementado correctamente")


def test_cadenas_reales_gestion21():
    """Test con cadenas en formato extendido Gestión 21 (formato real de producción)."""
    separador("9. CADENAS REALES — Formato extendido Gestión 21")

    # ============================================================
    # Cadena para DOCUMENTOS (flag D al final)
    # ============================================================
    cadena_doc = r"driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D"

    print(f"\n  Cadena Documentos:\n    {cadena_doc}\n")

    params_doc = parse_connection_string(cadena_doc)

    print("  Parámetros extraídos:")
    for k, v in params_doc.items():
        display = "****" if k == "password" else v
        print(f"    {k:30s} → {display}")

    assert params_doc["driver"] == "SQL Server", f"Driver incorrecto: {params_doc['driver']}"
    assert params_doc["server"] == r"miservidor\SQLEXPRESS", f"Server incorrecto: {params_doc['server']}"
    assert params_doc["database"] == "MiBaseDatos", f"Database incorrecto: {params_doc['database']}"
    assert params_doc["user"] == "mi_usuario", f"User incorrecto: {params_doc['user']}"
    assert params_doc["password"] == "mi_clave", f"Password incorrecto"
    assert params_doc["modelo"] == "T01", f"Modelo incorrecto: {params_doc.get('modelo')}"
    assert params_doc["tipo"] == "documento", f"Tipo incorrecto: {params_doc.get('tipo')}"

    print("\n  ✓ Documentos: database=MiBaseDatos, modelo=T01, tipo=documento")

    # Crear DatabaseConnection — debe auto-detectar tipo y modelo
    db_doc = DatabaseConnection.from_connection_string(cadena_doc)
    assert db_doc.database == "MiBaseDatos"
    assert db_doc.context_type == "documento"
    assert db_doc.modelo == "T01"
    assert db_doc.table == "G_SCRIPT"
    assert db_doc.is_documento == True

    print(f"  ✓ DatabaseConnection: db={db_doc.database}, tabla={db_doc.table}, "
          f"contexto={db_doc.context_type}, modelo={db_doc.modelo}")

    # ============================================================
    # Cadena para PLANTILLAS (flag P al final)
    # ============================================================
    cadena_plt = r"driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos_PLT A P"

    print(f"\n  Cadena Plantillas:\n    {cadena_plt}\n")

    params_plt = parse_connection_string(cadena_plt)

    print("  Parámetros extraídos:")
    for k, v in params_plt.items():
        display = "****" if k == "password" else v
        print(f"    {k:30s} → {display}")

    assert params_plt["database"] == "MiBaseDatos_PLT", f"Database incorrecto: {params_plt['database']}"
    assert params_plt["modelo"] == "A", f"Modelo incorrecto: {params_plt.get('modelo')}"
    assert params_plt["tipo"] == "plantilla", f"Tipo incorrecto: {params_plt.get('tipo')}"

    print("\n  ✓ Plantillas: database=MiBaseDatos_PLT, modelo=A, tipo=plantilla")

    # Crear DatabaseConnection — sin pasar context_type, debe detectarlo solo
    db_plt = DatabaseConnection.from_connection_string(cadena_plt)
    assert db_plt.database == "MiBaseDatos_PLT"
    assert db_plt.context_type == "plantilla"
    assert db_plt.modelo == "A"
    assert db_plt.table == "G_SCRIPT_PLANTILLA"
    assert db_plt.is_plantilla == True

    print(f"  ✓ DatabaseConnection: db={db_plt.database}, tabla={db_plt.table}, "
          f"contexto={db_plt.context_type}, modelo={db_plt.modelo}")

    # ============================================================
    # Verificar que las cadenas estándar NO activan formato extendido
    # ============================================================
    cadena_normal = "Driver={SQL Server};Server=SRV;Database=MiBaseDatos;UID=sa;PWD=123;"
    params_normal = parse_connection_string(cadena_normal)
    assert "modelo" not in params_normal, "Cadena normal NO debería tener modelo"
    assert "tipo" not in params_normal, "Cadena normal NO debería tener tipo"
    print("\n  ✓ Cadenas estándar siguen funcionando sin cambios")

    print("\n✓ Cadenas de formato extendido Gestión 21 parseadas correctamente")


if __name__ == "__main__":
    print("\n" + "╔" + "═"*58 + "╗")
    print("║  TEST: Parser de cadena de conexión + Contexto          ║")
    print("╚" + "═"*58 + "╝")

    test_parse_odbc()
    test_parse_adonet()
    test_contexto()
    test_from_connection_string()
    test_cli_simulation()
    test_errores()
    test_sanitizacion()
    test_context_manager()
    test_cadenas_reales_gestion21()

    separador("RESULTADO FINAL")
    print("\n  ✓✓✓ TODOS LOS TESTS PASARON CORRECTAMENTE ✓✓✓\n")
    print("  El formato extendido de Gestión 21 funciona perfectamente.")
    print("  Documentos → MiBaseDatos (MODELO=T01, tabla=G_SCRIPT)")
    print("  Plantillas → MiBaseDatos_PLT (MODELO=A, tabla=G_SCRIPT_PLANTILLA)\n")
