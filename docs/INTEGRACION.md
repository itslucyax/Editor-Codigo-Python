# Guía de Integración

Esta guía explica cómo integrar el editor de scripts con Gestión 21 u otra aplicación de escritorio.

## Resumen

El editor se lanza mediante línea de comandos. La aplicación de escritorio ejecuta el EXE pasándole una **cadena de conexión** que contiene toda la información necesaria (servidor, base de datos, MODELO y tipo).

El editor actúa como un "editor especializado conectado a la base de datos", funcionando como una extensión externa de la aplicación principal.

## Modo recomendado: Cadena de conexión (Gestión 21)

### Formato de la cadena

Gestión 21 usa un formato especial donde el campo `database` incluye el MODELO y el tipo separados por espacios:

```
driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D
                                                                       ───────────  ─── ─
                                                                       BD real      MOD TIPO
```

| Token | Significado | Ejemplo |
|-------|-------------|---------||
| BD real | Nombre de la base de datos | `MiBaseDatos` |
| MOD | Código del modelo | `T01` |
| TIPO | `D` = Documento, `P` = Plantilla | `D` |

El editor parsea esto automáticamente y detecta:
- A qué base de datos conectarse
- Qué MODELO cargar
- Si es Documento (tabla `G_SCRIPT`) o Plantilla (tabla `G_SCRIPT_PLANTILLA`)

### Comandos

```powershell
# Documentos (flag D)
EditorScript.exe --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D" --key-columns "MODELO,CODIGO" --key-values "T01,BOBINADO"

# Plantillas (flag P)
EditorScript.exe --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos_PLT A P" --key-columns "MODELO,CODIGO" --key-values "A,FACTURA"
```

> **Nota**: Si no se pasan `--key-values`, el editor carga automáticamente el primer script disponible para el MODELO detectado.

### Ejemplo VB para el botón de Gestión 21

```vb
' Al hacer clic en el botón "Editar Script"
Sub AbrirEditor(cadenaConexion As String, modelo As String, codigo As String)
    Dim comando As String
    comando = "C:\Ruta\EditorScript.exe" & _
              " --connection-string """ & cadenaConexion & """" & _
              " --key-columns ""MODELO,CODIGO""" & _
              " --key-values """ & modelo & "," & codigo & """"

    Shell comando, vbNormalFocus
End Sub

' Uso:
' AbrirEditor "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D", "T01", "BOBINADO"
```

## Parámetros CLI completos

### Principales

| Parámetro | Obligatorio | Descripción | Ejemplo |
|-----------|-------------|-------------|---------|
| `--connection-string` | Sí* | Cadena de conexión completa | `"driver={SQL Server};server=...;database=MiBaseDatos T01 D"` |
| `--key-columns` | Sí | Columnas clave separadas por coma | `"MODELO,CODIGO"` |
| `--key-values` | No** | Valores de las claves | `"T01,BOBINADO"` |
| `--content-column` | No | Columna del script (default: SCRIPT) | `"SCRIPT"` |

\* Alternativa: usar `--server`, `--database`, `--user`, `--password` por separado.

\** Si no se da, se auto-detecta el MODELO de la cadena y se carga el primer script.

### Opcionales

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| `--tipo` | Forzar tipo (se auto-detecta de la cadena) | `documento` / `plantilla` |
| `--table` | Forzar tabla (ignora auto-detección) | `"MI_TABLA"` |
| `--table-documento` | Tabla custom para documentos | `"SCRIPTS_DOC"` |
| `--table-plantilla` | Tabla custom para plantillas | `"SCRIPTS_PLT"` |
| `--config-file` | Archivo JSON con toda la config | `"config.json"` |
| `--editable-columns` | Columnas editables en sidebar | `"GRUPO,DESCRIPCION"` |
| `--local` | Modo local sin BD (pruebas) | — |

### Parámetros individuales (compatibilidad)

| Parámetro | Descripción |
|-----------|-------------|
| `--server` | Servidor SQL Server |
| `--database` | Base de datos |
| `--user` | Usuario SQL Auth |
| `--password` | Contraseña |
| `--driver` | Driver ODBC (auto-detectado) |

## Flujo de integración

```
┌─────────────────────────────────────────────────────────────┐
│  1. Usuario hace clic en un elemento dentro de Gestión 21   │
│  2. Hace clic en el botón "Editar script"                   │
│  3. Gestión 21 construye la cadena de conexión con D o P    │
│  4. Gestión 21 ejecuta:                                     │
│                                                             │
│     EditorScript.exe --connection-string "driver=...;       │
│       database=MiBaseDatos T01 D"                           │
│       --key-columns "MODELO,CODIGO"                         │
│       --key-values "T01,BOBINADO"                           │
│                                                             │
│  5. El editor parsea la cadena automáticamente:             │
│     → database = MiBaseDatos                                  │
│     → MODELO = T01                                          │
│     → tipo = Documento → tabla = G_SCRIPT                   │
│                                                             │
│  6. Se conecta a SQL Server y carga el registro             │
│  7. Se abre el editor con el script y los campos            │
│  8. Usuario edita y guarda (Ctrl+S)                         │
│  9. Usuario cierra el editor                                │
│  10. Los cambios ya están en la BD                          │
└─────────────────────────────────────────────────────────────┘
```

## Base de datos

### Tablas usadas

| Contexto | Tabla por defecto | Configurable con |
|----------|-------------------|------------------|
| Documento (D) | `G_SCRIPT` | `--table-documento` |
| Plantilla (P) | `G_SCRIPT_PLANTILLA` | `--table-plantilla` |

### Estructura esperada

```sql
CREATE TABLE G_SCRIPT (
    MODELO nvarchar(3) NOT NULL,
    CODIGO nvarchar(20) NOT NULL,
    SCRIPT ntext,                  -- contenido del script VBS
    GRUPO nvarchar(50),            -- grupo/categoría
    TABLACAMPO0 nvarchar(100),     -- variables Var0-Var9
    TABLACAMPO1 nvarchar(100),
    -- ... TABLACAMPO2 a TABLACAMPO9
    PRIMARY KEY (MODELO, CODIGO)
)
```

### Operaciones SQL que realiza el editor

```sql
-- Al abrir: carga registro completo
SELECT * FROM [G_SCRIPT] WHERE [MODELO] = ? AND [CODIGO] = ?

-- Al guardar (Ctrl+S): solo campos modificados
UPDATE [G_SCRIPT] SET [SCRIPT] = ?, [GRUPO] = ? WHERE [MODELO] = ? AND [CODIGO] = ?

-- Para el desplegable: lista scripts del mismo MODELO
SELECT [MODELO], [CODIGO], [SCRIPT] FROM [G_SCRIPT] WHERE [MODELO] = ? ORDER BY [CODIGO]
```

> **Seguridad**: Todos los nombres de tabla/columna pasan por sanitización. Los valores se pasan siempre como parámetros `?` (nunca concatenados en el SQL).

## Seguridad

### Credenciales

Las credenciales van dentro de la cadena de conexión (`uid=usuario;pwd=clave`). Recomendaciones:

1. Usar un usuario SQL con permisos mínimos (solo SELECT/UPDATE en las tablas del editor)
2. La contraseña no se muestra en logs (se enmascara automáticamente)
3. Para mayor seguridad, evaluar Windows Authentication en futuras versiones

### Permisos recomendados

```sql
CREATE LOGIN editor_script WITH PASSWORD = 'contraseña_segura';
USE MiBaseDatos;
CREATE USER editor_script FOR LOGIN editor_script;
GRANT SELECT, UPDATE ON dbo.G_SCRIPT TO editor_script;
GRANT SELECT, UPDATE ON dbo.G_SCRIPT_PLANTILLA TO editor_script;
```

## Pruebas

### Comando de prueba con cadenas reales

```powershell
# Prueba Documentos
.\EditorScript.exe --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D" --key-columns "MODELO,CODIGO" --key-values "T01,BOBINADO"

# Prueba Plantillas
.\EditorScript.exe --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos_PLT A P" --key-columns "MODELO,CODIGO" --key-values "A,FACTURA"

# Modo local (sin BD)
.\EditorScript.exe
```

### Verificar funcionamiento

1. Se abre el editor con el script cargado
2. El título muestra `[Documento]` o `[Plantilla]`
3. El sidebar muestra los campos del registro
4. Ctrl+S guarda en BD (barra de estado confirma)
5. Al cerrar con cambios, pregunta si guardar
