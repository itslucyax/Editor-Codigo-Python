# Editor VBS Dinámico - Sistema sin Hardcodeo

## Características principales

- **Detección automática de estructura**: El editor detecta columnas de la tabla con `INFORMATION_SCHEMA`
- **Cero hardcodeo**: No hay nombres de tablas, columnas o valores fijos en el código
- **Multi-fuente de configuración**: Soporta cadena de conexión, JSON, variables de entorno y CLI
- **Formato extendido Gestión 21**: Parsea `database=MiBaseDatos T01 D` automáticamente
- **Contexto Documento / Plantilla**: Auto-detecta el tipo y resuelve la tabla correcta
- **Sidebar dinámico**: Se adapta automáticamente a cualquier estructura de BD
- **Guardado inteligente**: Solo actualiza los campos modificados
- **Sanitización SQL**: Previene inyección en nombres de tabla/columna
- **Context manager**: Conexión se cierra siempre, incluso si la app falla

## Métodos de configuración

### 1. Cadena de conexión (Recomendado — Gestión 21)

```bash
# Documentos (flag D)
python main.py --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D" --key-columns "MODELO,CODIGO" --key-values "T01,BOBINADO"

# Plantillas (flag P)
python main.py --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos_PLT A P" --key-columns "MODELO,CODIGO" --key-values "A,FACTURA"
```

El parser detecta automáticamente:
- `database=MiBaseDatos T01 D` → BD=`MiBaseDatos`, MODELO=`T01`, tipo=Documento
- `database=MiBaseDatos_PLT A P` → BD=`MiBaseDatos_PLT`, MODELO=`A`, tipo=Plantilla

No necesitas `--tipo` — se auto-detecta del flag D/P.

### 2. Archivo JSON (Para entornos con configuración fija)

```bash
python main.py --config-file editor_config.json
```

### 3. Variables de entorno (Para integración con otros sistemas)

```batch
set EDITOR_CONNECTION_STRING=driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D
set EDITOR_KEY_COLUMNS=MODELO,CODIGO
set EDITOR_KEY_VALUES=T01,BOBINADO
set EDITOR_CONTENT_COLUMN=SCRIPT

python main.py
```

### 4. Parámetros individuales (Compatibilidad)

```bash
python main.py --server "servidor\instancia" --database "MIBD" --table "G_SCRIPT" --key-columns "MODELO,CODIGO" --key-values "T01,BOBINADO" --content-column "SCRIPT" --user "sa" --password "password"
```

## Prioridad de configuración

```
Parámetros CLI > Variables de entorno > Archivo JSON
```

## Detección automática de contexto

Cuando la cadena de conexión incluye el formato extendido de Gestión 21, el editor:

1. **Extrae el MODELO** del campo database (ej: `T01`)
2. **Detecta el tipo** por el flag final (`D` = Documento, `P` = Plantilla)
3. **Resuelve la tabla** automáticamente:
   - Documento → `G_SCRIPT`
   - Plantilla → `G_SCRIPT_PLANTILLA`
4. **Configura key_columns/key_values** si no se proporcionaron explícitamente

```
Cadena: "...database=MiBaseDatos T01 D"
                     ─────────── ─── ─
                     BD real      MOD D=Documento

Resultado:
  database = MiBaseDatos
  modelo   = T01
  tipo     = documento → tabla = G_SCRIPT
```

## Integración con Gestión 21

### Desde VB6 / VB.NET (botón en la app)

```vb
' El botón del jefe llama a esto:
Sub AbrirEditor(cadenaConexion As String, modelo As String, codigo As String)
    Shell "C:\ruta\EditorScript.exe" & _
          " --connection-string """ & cadenaConexion & """" & _
          " --key-columns ""MODELO,CODIGO""" & _
          " --key-values """ & modelo & "," & codigo & """", _
          vbNormalFocus
End Sub
```

### Generación dinámica de JSON (desde Python o .NET)

```python
import json, os

config = {
    "connection": {
        "connection_string": "driver={SQL Server};server=miservidor\\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D"
    },
    "script": {
        "key_columns": ["MODELO", "CODIGO"],
        "key_values": ["T01", "BOBINADO"],
        "content_column": "SCRIPT"
    }
}

with open("temp_config.json", "w") as f:
    json.dump(config, f)

os.system("editor.exe --config-file temp_config.json")
```

## Tablas y contexto

| Contexto | Flag | Tabla por defecto | Configurable |
|----------|------|-------------------|--------------|
| Documento | `D` | `G_SCRIPT` | `--table-documento` |
| Plantilla | `P` | `G_SCRIPT_PLANTILLA` | `--table-plantilla` |

El flag se detecta automáticamente del último carácter del campo `database` en la cadena de conexión. Si se usa el modo de parámetros individuales, se puede forzar con `--tipo documento` o `--tipo plantilla`.

## Estructura del sidebar adaptativa

El sidebar se construye dinámicamente según el contenido del registro:

### Sección superior (Claves primarias)
- Muestra las claves en grande y negrita
- Ejemplo: Si key_columns = ["MODELO", "CODIGO"], se muestran destacadas

### Sección de metadata
- Todos los campos que NO son claves ni contenido
- Los campos en `editable_columns` se muestran con Entry editables
- El resto se muestra como Label readonly

### Sección de variables (si existen)
- Detecta automáticamente columnas TABLACAMPO0-TABLACAMPO9
- Se muestra como Var 0 - Var 9 en formato tabla

## Comportamiento del guardado

Al pulsar Ctrl+S:
1. Se obtiene el contenido del editor
2. Se obtienen los valores editados del sidebar
3. Se genera un `UPDATE` dinámico con solo los campos modificados
4. Los identificadores SQL se sanitizan antes de construir la query
5. Los valores se pasan como parámetros `?` (nunca concatenados)

```sql
-- Query generada automáticamente (ejemplo)
UPDATE [G_SCRIPT]
SET [SCRIPT] = ?, [GRUPO] = ?
WHERE [MODELO] = ? AND [CODIGO] = ?
```

## Seguridad

- **Sanitización SQL**: `_sanitize_identifier()` valida nombres de tabla/columna con regex `^[\w\s#@$]+$` — cualquier carácter sospechoso (`;`, `'`, `"`, `--`) se rechaza con `ValueError`
- **Parámetros tipados**: Los valores nunca se concatenan en el SQL, siempre van como `?`
- **Contraseñas ocultas**: Los logs enmascaran passwords automáticamente
- **Context manager**: `try/finally` garantiza que la conexión se cierra aunque la app falle
- **autocommit=False**: Commit explícito solo tras verificar `rowcount`

## Logging

Todos los eventos se registran en:
```
%APPDATA%\EditorVBS\editor.log
```

Con rotación automática (1MB x 3 backups).

## FAQ

**P: ¿Qué pasa si la tabla cambia de estructura?**
R: El editor se adapta automáticamente. Usa `INFORMATION_SCHEMA.COLUMNS` para detectar la estructura.

**P: ¿Puedo usar con otras bases de datos (MySQL, PostgreSQL)?**
R: Actualmente solo SQL Server via ODBC.

**P: ¿Cómo especifico qué campos son editables?**
R: Via `editable_columns` en la configuración. Si no se especifica, todos son readonly excepto el script.

**P: ¿Soporta claves compuestas de más de 2 columnas?**
R: Sí, `key_columns` y `key_values` pueden tener cualquier cantidad de elementos.

**P: ¿Es seguro contra SQL injection?**
R: Sí. Los identificadores se sanitizan con regex y los valores se pasan como parámetros tipados.

**P: ¿Qué pasa si paso una cadena de conexión SIN el formato extendido (sin D/P)?**
R: Funciona igual que antes. El parser solo activa el modo extendido si detecta 3+ tokens en el campo database con un flag D o P al final.
