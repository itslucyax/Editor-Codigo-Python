# Editor VBS Dinámico - Sistema sin Hardcodeo

## Características principales

✅ **Detección automática de estructura**: El editor detecta automáticamente todas las columnas de la tabla
✅ **Cero hardcodeo**: No hay nombres de tablas, columnas o valores fijos en el código
✅ **Multi-fuente de configuración**: Soporta JSON, variables de entorno y parámetros CLI
✅ **Sidebar dinámico**: Se adapta automáticamente a cualquier estructura de BD
✅ **Guardado inteligente**: Solo actualiza los campos modificados

## Métodos de configuración

### 1. Archivo JSON (Recomendado para producción)

```bash
python main.py --config-file editor_config.json
```

Ver `editor_config.example.json` para el formato completo.

### 2. Variables de entorno (Ideal para integración con otros sistemas)

```batch
set EDITOR_SERVER=servidor\instancia
set EDITOR_DATABASE=MIBD
set EDITOR_TABLE=G_SCRIPT
set EDITOR_KEY_COLUMNS=MODELO,CODIGO
set EDITOR_KEY_VALUES=T01,BOBINADO
set EDITOR_CONTENT_COLUMN=SCRIPT
set EDITOR_USER=sa
set EDITOR_PASSWORD=password
set EDITOR_EDITABLE_COLUMNS=GRUPO,DESCRIPCION

python main.py
```

### 3. Parámetros de línea de comandos (Máxima flexibilidad)

```bash
python main.py \
  --server "servidor\instancia" \
  --database "MIBD" \
  --table "G_SCRIPT" \
  --key-columns "MODELO,CODIGO" \
  --key-values "T01,BOBINADO" \
  --content-column "SCRIPT" \
  --user "sa" \
  --password "password" \
  --editable-columns "GRUPO,DESCRIPCION"
```

## Prioridad de configuración

Cuando hay múltiples fuentes, se aplica esta prioridad:

```
Parámetros CLI > Variables de entorno > Archivo JSON
```

## Integración con otros sistemas

### Ejemplo: Llamada desde C# / VB.NET

```vb
' Preparar variables de entorno
Environment.SetEnvironmentVariable("EDITOR_SERVER", "miservidor\sql2019")
Environment.SetEnvironmentVariable("EDITOR_DATABASE", "PRODUCCION")
Environment.SetEnvironmentVariable("EDITOR_TABLE", "SCRIPTS_PRODUCCION")
Environment.SetEnvironmentVariable("EDITOR_KEY_COLUMNS", "ID_SCRIPT")
Environment.SetEnvironmentVariable("EDITOR_KEY_VALUES", "12345")
Environment.SetEnvironmentVariable("EDITOR_CONTENT_COLUMN", "CODIGO_VBS")
Environment.SetEnvironmentVariable("EDITOR_USER", ConfigurationManager.AppSettings("DBUser"))
Environment.SetEnvironmentVariable("EDITOR_PASSWORD", ConfigurationManager.AppSettings("DBPass"))

' Lanzar el editor
Process.Start("C:\ruta\editor.exe")
```

### Ejemplo: Generación dinámica de archivo JSON

```python
import json

# Generar configuración en tiempo de ejecución
config = {
    "connection": {
        "server": obtener_servidor_activo(),
        "database": obtener_bd_produccion(),
        "table": "SCRIPTS_CLIENTE",
        "user": obtener_usuario(),
        "password": obtener_password_seguro(),
        "content_column": "SCRIPT_DATA"
    },
    "script": {
        "key_columns": ["CLIENTE_ID", "SCRIPT_VERSION"],
        "key_values": [cliente_id, version_actual],
        "editable_columns": ["NOTAS", "CATEGORIA"]
    }
}

# Guardar config temporal
with open("temp_config.json", "w") as f:
    json.dump(config, f)

# Lanzar editor
os.system("editor.exe --config-file temp_config.json")
```

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
- Detecta automáticamente columnas VAR0-VAR9 (o similar)
- Se muestra en Entry readonly en formato tabla

## Comportamiento del guardado

Al pulsar Ctrl+S:
1. Se obtiene el contenido del editor
2. Se obtienen los valores editados del sidebar
3. Se actualiza el registro con `UPDATE` dinámico
4. Solo se actualizan las columnas modificadas

```sql
-- Ejemplo de query generada automáticamente
UPDATE [G_SCRIPT]
SET [SCRIPT] = '...contenido...', [GRUPO] = 'nuevo_valor'
WHERE [MODELO] = 'T01' AND [CODIGO] = 'BOBINADO'
```

## Ventajas para tu jefe

✅ **Sin mantenimiento**: Funciona con cualquier tabla sin cambiar código
✅ **Seguro**: Las contraseñas nunca están en el código
✅ **Flexible**: Cada cliente puede tener su propia configuración
✅ **Auditable**: Todos los cambios quedan en logs
✅ **Escalable**: Fácil agregar nuevas tablas o columnas

## Logging

Todos los eventos se registran en:
```
%APPDATA%\EditorVBS\editor.log
```

Con rotación automática (1MB × 3 backups).

## Ejemplo de uso completo

```bash
# 1. Crear archivo de configuración para cada entorno
echo {
  "connection": {
    "server": "prod-server\\sql2019",
    "database": "PRODUCCION",
    "table": "SCRIPTS_CLIENTES",
    "user": "app_user",
    "password": "secure_password",
    "content_column": "CODIGO_SCRIPT"
  },
  "script": {
    "key_columns": ["ID_CLIENTE", "VERSION"],
    "key_values": ["C001", "1.0"],
    "editable_columns": ["OBSERVACIONES", "CATEGORIA"]
  }
} > prod_config.json

# 2. Lanzar editor
python main.py --config-file prod_config.json

# 3. El usuario edita y guarda (Ctrl+S)

# 4. Los cambios se guardan automáticamente en la BD
```

## FAQ

**P: ¿Qué pasa si la tabla cambia de estructura?**  
R: El editor se adapta automáticamente. No requiere cambios en el código.

**P: ¿Puedo usar con otras bases de datos (MySQL, PostgreSQL)?**  
R: Actualmente solo SQL Server via ODBC. Pero la arquitectura permite añadir otros drivers fácilmente.

**P: ¿Cómo especifico qué campos son editables?**  
R: Via `editable_columns` en la configuración. Si no se especifica, todos son readonly excepto el script.

**P: ¿Soporta claves compuestas de más de 2 columnas?**  
R: Sí, `key_columns` y `key_values` pueden tener cualquier cantidad de elementos.

**P: ¿Cómo lo llamo desde mi aplicación principal?**  
R: Genera el JSON de configuración dinámicamente y lanza el proceso con `--config-file`.
