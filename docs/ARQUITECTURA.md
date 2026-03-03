# Arquitectura del Proyecto

## Visión general

Aplicación de escritorio Python con tres capas bien delimitadas: interfaz gráfica (Tkinter), resaltado de sintaxis (Pygments) y acceso a datos (pyodbc → SQL Server). La comunicación entre capas siempre va de arriba hacia abajo; `db/` no sabe nada de la UI y `syntax/` no sabe nada de la DB.

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                    (Punto de entrada)                            │
│              Parsea argumentos CLI + config multi-fuente         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
 ┌──────────────┐    ┌──────────┐    ┌──────────────┐
 │     db/      │    │ editor/  │    │ config.py    │
 │ connection   │◄───│   app    │───►│config_loader │
 │ (parse_conn  │    └────┬─────┘    └──────────────┘
 │  _string)    │         │
 └──────────────┘    ┌────┼────────────────┐
                     ▼    ▼         ▼      ▼
              ┌────────┐┌──────┐┌───────┐┌──────────┐
              │ text_  ││line_ ││search_││ sidebar  │
              │ editor ││number││ bar   ││ + script │
              └────────┘└──────┘└───────┘│ selector │
                     │                   └──────────┘
                     ▼
              ┌──────────┐
              │  syntax/ │
              │ highlight│
              └──────────┘
```
---

## Módulos

### main.py - Bootstrap

Punto de entrada. Usa `argparse` para recibir parámetros CLI, `ConfigLoader` para combinar configuración de múltiples fuentes (CLI > ENV > JSON), y lanza la conexión y el editor.

Soporta dos modos de conexión:
1. **Cadena de conexión** (`--connection-string`): El parser extrae automáticamente server, database, user, password, y en formato extendido Gestión 21 también MODELO y tipo (D/P).
2. **Parámetros individuales** (`--server`, `--database`, etc.): Compatibilidad con versiones anteriores.

Si no hay configuración de BD, arranca en **modo local** con un script de ejemplo.

```python
# Flujo principal
1. Parsear argumentos CLI (argparse)
2. Cargar configuración multi-fuente (ConfigLoader: JSON → ENV → CLI)
3. Crear conexión a BD:
   a) Desde connection string → parse_connection_string() → from_connection_string()
   b) Desde parámetros individuales → DatabaseConnection(server=..., ...)
4. Detectar contexto (Documento/Plantilla) y resolver tabla
5. Conectar y cargar registro completo (get_record_full)
6. Crear ventana del editor (EditorApp)
7. Ejecutar loop principal (mainloop)
8. Cerrar conexión al salir (try/finally)
```

**Argumentos principales**:
- `--connection-string`: Cadena de conexión completa (formato ODBC, ADO.NET o Gestión 21)
- `--tipo`: `documento` o `plantilla` (auto-detectado si la cadena usa formato extendido)
- `--key-columns`, `--key-values`: Claves del registro
- `--config-file`: Archivo JSON con toda la configuración
- `--server`, `--database`, `--user`, `--password`: Parámetros individuales (compatibilidad)

---

### config.py - Constantes visuales

Único punto de configuración para colores y fuente. Todas las constantes son strings o tuplas importadas directamente por los módulos que las necesitan. Cambiar un color aquí afecta a todos los componentes sin tocar nada más.

```python
# Colores del tema oscuro
COLOR_FONDO        = "#1e1e1e"   # Fondo del editor
COLOR_TEXTO        = "#d4d4d4"   # Texto normal
COLOR_KEYWORD      = "#569cd6"   # Palabras clave
COLOR_STRING       = "#ce9178"   # Cadenas
COLOR_COMMENT      = "#6a9955"   # Comentarios
# ... etc

# Fuente
FUENTE_EDITOR      = ("Consolas", 12)
```

---

### config_loader.py - Configuración multi-fuente

Carga y combina configuración de tres fuentes con prioridad: **CLI > ENV > JSON**.

```python
class ConfigLoader:
    def load_from_file(path)     # Carga desde JSON
    def load_from_env()          # Carga desde variables EDITOR_*
    def merge(cli_args)          # Combina todo, CLI tiene prioridad
    def validate_connection_config()  # Valida datos mínimos
    def validate_script_config()      # Valida key_columns/key_values
```

Variables de entorno soportadas: `EDITOR_SERVER`, `EDITOR_DATABASE`, `EDITOR_CONNECTION_STRING`, `EDITOR_TIPO`, etc.

---

### db/connection.py - Acceso a datos

**Módulo central de conexión a SQL Server.** Incluye:

#### Funciones de módulo

- `parse_connection_string(conn_str)`: Parsea cadenas ODBC, ADO.NET y **formato extendido Gestión 21** (donde `database=MiBaseDatos T01 D` se descompone en database, MODELO y tipo D/P).
- `resolve_table_for_context(context_type)`: Mapea `"documento"` → `G_SCRIPT`, `"plantilla"` → `G_SCRIPT_PLANTILLA`.
- `detect_odbc_driver()`: Auto-detecta el mejor driver ODBC instalado.
- `_sanitize_identifier(name)`: Previene inyección SQL en nombres de tabla/columna.

#### Clase `DatabaseConnection`

```python
class DatabaseConnection:
    # Constructores
    def __init__(server, database, table, user, password, driver, context_type, modelo, ...)
    @classmethod
    def from_connection_string(conn_str, context_type, ...)  # Parsea y crea

    # Context manager
    def __enter__()  →  connect() + return self
    def __exit__()   →  close()

    # Conexión
    def connect()    # Abre conexión pyodbc (auto-detecta driver)
    def close()      # Cierra conexión

    # Lectura dinámica
    def get_table_schema()                    # INFORMATION_SCHEMA → lista de columnas
    def get_record_full(key_columns, key_values)  # SELECT * dinámico
    def get_scripts_for_model(...)            # Lista de scripts para el desplegable

    # Escritura dinámica
    def save_record_full(key_columns, key_values, updated_fields)  # UPDATE dinámico

    # Variables Var0-Var9
    def get_variables(modelo, codigo)         # Lee TABLACAMPO0-9 + GRUPO

    # Contexto
    def switch_context(new_context)           # Cambio Documento ↔ Plantilla en caliente
    @property is_documento / is_plantilla
```

**Seguridad:**
- Todos los identificadores SQL (tabla, columna) pasan por `_sanitize_identifier()` que rechaza caracteres peligrosos
- Los valores se pasan siempre como parámetros `?` (nunca concatenados)
- `autocommit=False`, commit explícito tras verificar `rowcount`

**Formato extendido Gestión 21:**

```
"database=MiBaseDatos T01 D"
         ───────────  ─── ─
         BD real      MOD TIP
```

El parser detecta que el último token es `D` o `P` y extrae automáticamente:
- `database` → `"MiBaseDatos"` (nombre real de la BD)
- `modelo` → `"T01"` (código del modelo)
- `tipo` → `"documento"` (D) o `"plantilla"` (P)

| Situación | Excepción |
|-----------|-----------|
| Faltan `--user` o `--password` | `ValueError` |
| No se puede conectar al servidor | `ConnectionError` (wrappea `pyodbc.Error`) |
| Registro no encontrado en BD | `LookupError` |
| Columna no existe | `LookupError` (error ODBC `42S22`) |
| Cadena de conexión vacía o inválida | `ValueError` |
| Contexto no válido | `ValueError` |
| Identificador SQL peligroso | `ValueError` (sanitización) |

**SQL generado** (identificadores sanitizados, valores como parámetros `?`):

```sql
-- Lectura dinámica
SELECT [MODELO], [CODIGO], [SCRIPT], ... FROM [G_SCRIPT] WHERE [MODELO] = ? AND [CODIGO] = ?

-- Escritura dinámica (solo campos modificados)
UPDATE [G_SCRIPT] SET [SCRIPT] = ?, [GRUPO] = ? WHERE [MODELO] = ? AND [CODIGO] = ?
```

---

### editor/app.py - Ventana principal

**Clase principal**: `EditorApp` (`tk.Tk`)

Monta la ventana, conecta los componentes y gestiona los eventos de alto nivel. Recibe `context_type` para mostrar "Documento" o "Plantilla" en el título.

Estructura de la ventana:
- `Sidebar` (izquierda): Campos del registro (readonly / editables) + variables Var0-9
- `ScriptSelector` (arriba): Desplegable para cambiar de script
- `SearchBar` / `FixedSearchBar` (arriba del editor): Buscar y reemplazar
- `TextEditor` + `LineNumbers` (centro): Área de edición con resaltado
- `Label` barra de estado (fondo): Contexto, cursor, estado

```python
class EditorApp(tk.Tk):
    def __init__(inicial_text, db, record, key_columns, content_column,
                 editable_columns, scripts_list, context_type)

    # Métodos principales
    def _guardar()       # Ctrl+S → save_record_full()
    def _on_cerrar()     # Confirmar antes de cerrar
    def _update_status() # Actualizar barra de estado

    # Atajos de teclado
    def _seleccionar_todo()  # Ctrl+A
    def _deshacer()          # Ctrl+Z
    def _rehacer()           # Ctrl+Y
```

**Componentes que contiene**:
- `Sidebar`: Panel lateral dinámico con campos del registro
- `ScriptSelector`: Desplegable de scripts (cambia sin cerrar ventana)
- `TextEditor`: Área de edición
- `LineNumbers`: Números de línea
- `SearchBar`: Buscar y reemplazar (Ctrl+F / Ctrl+H)
- `Label`: Barra de estado

Atajos registrados con `bind_all`:

| Atajo | Método |
|-------|--------|
| `Ctrl+S` | `_guardar()` — guarda script + campos editables |
| `Ctrl+Z` | `_deshacer()` → `edit_undo()` |
| `Ctrl+Y` | `_rehacer()` → `edit_redo()` |
| `Ctrl+A` | `_seleccionar_todo()` |
| `Ctrl+F` | Abrir barra de búsqueda |
| `Ctrl+H` | Abrir buscar y reemplazar |
| `Ctrl+G` | Ir a línea |
| `F3` / `Shift+F3` | Siguiente / anterior coincidencia |

El cierre se intercepta con `protocol("WM_DELETE_WINDOW", _on_cerrar)`. Si hay cambios sin guardar, muestra diálogo `askyesnocancel`.

La barra de estado muestra: contexto (Documento/Plantilla), posición del cursor y estado de modificación.

---

### editor/text_editor.py - Área de edición

**Clase principal**: `TextEditor` (hereda de `tk.Text`)

Extiende `tk.Text` con resaltado de sintaxis y un sistema de debounce para no recalcular los tags en cada pulsación.

Configuración del widget:
- `undo=True` — historial nativo de Tkinter
- `wrap="none"` — scroll horizontal en lugar de wrap
- `selectbackground="#264f78"` — selección estilo VS Code

```python
class TextEditor(tk.Text):
    def __init__(master)
    
    # Resaltado
    highlighter = VBHighlighter(self)
    
    # Debounce para no resaltar en cada tecla
    def _schedule_highlight()   # Programa resaltado con delay
    def _do_highlight()         # Ejecuta resaltado
    
    # Contenido
    def set_content(text)       # Cargar texto inicial
```

**Eventos que escucha**:
- `<KeyRelease>`: Resaltar tras escribir
- `<<Paste>>`, `<<Cut>>`: Resaltar tras pegar/cortar
- `<<Undo>>`, `<<Redo>>`: Resaltar tras deshacer/rehacer


El resaltado es costoso (tokeniza todo el texto con Pygments). Para no bloquearse en cada tecla hay tres niveles de respuesta:

| Evento | Comportamiento |
|--------|----------------|
| `BackSpace`, `Delete`, `Return`, `"`, `'` | Resaltado inmediato (`_do_highlight_now`) |
| Resto de teclas, `<<Modified>>` | Resaltado diferido 20 ms (`_schedule_highlight_fast`) |
| `<ButtonRelease-1>` | Resaltado diferido 50 ms (`_schedule_highlight`) |
| `<<Paste>>`, `<<Cut>>`, `<<Undo>>`, `<<Redo>>` | Resaltado inmediato |

Cada llamada a `_schedule_highlight*` cancela el `after` pendiente antes de programar uno nuevo, garantizando que solo haya un resaltado en cola a la vez.

Tras cada resaltado se emite `<<Change>>` para que `LineNumbers` y la barra de estado se actualicen.

---

### editor/line_numbers.py - Números de línea

**Clase principal**: `LineNumbers` (hereda de `tk.Canvas`)

Canvas de 40 px de ancho. `redraw()` recorre las líneas visibles usando `dlineinfo()` — que devuelve la posición Y real en pantalla — y dibuja el número con `create_text`. Esto hace que funcione correctamente con scroll sin necesidad de cálculos manuales de offset.

Se suscribe a `<<Change>>`, `<Configure>`, `<KeyRelease>`, `<MouseWheel>`, `<ButtonRelease-1>`, `<Return>`, `<BackSpace>` y `<Delete>` del `TextEditor` para mantenerse sincronizado.

```python
class LineNumbers(tk.Canvas):
    def __init__(master, text_widget)
    def redraw()   # Redibujar números
```

**Sincronización**: Se actualiza cuando cambia el contenido o scroll del editor.

---

### editor/syntax/vb_highlighter.py - Resaltado

**Clase principal**: `VBHighlighter`

Usa `VBScriptLexer` de Pygments para tokenizar y mapea cada tipo de token a un tag de Tkinter. Los tags se configuran en `__init__` con los colores de `config.py`; en cada llamada a `highlight()` se limpian todos los tags y se vuelven a aplicar.

```python
class VBHighlighter:
    def __init__(text_widget)
    
    lexer = VBScriptLexer()   # Pygments
    
    def highlight()   # Tokeniza y aplica tags
```

**Flujo del resaltado**:
```
1. Obtener texto del widget
2. Tokenizar con Pygments (VBScriptLexer)
3. Para cada token:
   - Calcular posición línea.columna
   - Mapear token → tag (keyword, string, comment...)
   - Aplicar tag al rango de texto
```

**Mapeo de tokens:**

| Tag Tkinter | Token Pygments | Notas |
|-------------|----------------|-------|
| `keyword` | `Token.Keyword` | `If`, `Sub`, `Function`, etc. |
| `string` | `Token.Literal.String` | |
| `comment` | `Token.Comment` | Fuente itálica |
| `number` | `Token.Literal.Number` | |
| `builtin` | `Token.Name.Builtin` | `MsgBox`, `InputBox`, etc. |
| `function` | `Token.Name.Function` | Nombres de funciones definidas |
| `class` | `Token.Name.Class`, `Token.Name.Type` | |
| `variable` | `Token.Name.Variable`, `Token.Name.Attribute`, `Token.Name` (fallback) | |
| `constant` | `Token.Name.Constant` | |
| `operator` | `Token.Operator` | |

El cálculo de posiciones se hace en coordenadas `línea.columna` en lugar de offsets absolutos. El motivo es que los offsets fallan con caracteres multibyte y con saltos de línea CRLF — calcular `línea.columna` iterando carácter a carácter es más lento pero correcto.

---

## Flujos principales

### Apertura (modo cadena de conexión)

```
Gestión 21 ejecuta: editor.exe --connection-string "driver=...;database=MiBaseDatos T01 D" --key-columns "MODELO,CODIGO" --key-values "T01,BOBINADO"
    │
    ▼
main.py → argparse recibe --connection-string
    │
    ▼
ConfigLoader → merge(CLI > ENV > JSON)
    │
    ▼
parse_connection_string("...database=MiBaseDatos T01 D")
    → database="MiBaseDatos", modelo="T01", tipo="documento"
    │
    ▼
DatabaseConnection.from_connection_string()
    → tabla resuelta: G_SCRIPT (porque tipo=documento)
    │
    ▼
db.connect() → pyodbc.connect(...)     # Conexión real a SQL Server
    │
    ▼
db.get_record_full(["MODELO","CODIGO"], ["T01","BOBINADO"])
    → SELECT * FROM G_SCRIPT WHERE MODELO='T01' AND CODIGO='BOBINADO'
    │
    ▼
EditorApp(text=record["SCRIPT"], context_type="documento")
    → Sidebar muestra campos del registro
    → ScriptSelector carga lista de scripts del mismo MODELO
    → TextEditor muestra el script con resaltado
    → Barra de estado: [Documento] T01/BOBINADO
```

### Guardado (Ctrl+S)

```
Usuario pulsa Ctrl+S
    → EditorApp._guardar()
    → Recoger: texto del editor + campos editables del sidebar
    → db.save_record_full(key_columns, key_values, campos_modificados)
    → SQL: UPDATE [G_SCRIPT] SET [SCRIPT]=?, [GRUPO]=? WHERE [MODELO]=? AND [CODIGO]=?
    → Verificar rowcount == 1
    → Actualizar barra de estado: "Guardado ✓"
```

### Cierre con cambios pendientes

```
Usuario cierra ventana
    → EditorApp._on_cerrar()
    → ¿Modificado?
        → Sí: Mostrar diálogo
            → "Sí": _guardar() + destroy()
            → "No": destroy()
            → "Cancelar": return (no cierra)
        → No: destroy()
    → finally: db.close()  (siempre se cierra la conexión)
```

---

## Dependencias externas

| Librería | Uso |
|----------|-----|
| `tkinter` | Interfaz gráfica (incluido en Python) |
| `pyodbc` | Conexión a SQL Server |
| `pygments` | Tokenización de código para resaltado |

---

## Decisiones de diseño

### ¿Por qué Tkinter?

- Incluido en Python (sin dependencias adicionales)
- Ligero y rápido
- Suficiente para un editor de texto simple
- Fácil de compilar a EXE

### ¿Por qué Pygments?

- Soporta VBScript nativamente
- Tokenización robusta y probada
- Fácil de mapear tokens a colores

### ¿Por qué posiciones línea.columna?

Inicialmente usamos offsets (`1.0+Nc`), pero fallaba con caracteres especiales y CRLF. Calcular posición `línea.columna` manualmente es más robusto.

## Dependencias

| Librería | Versión mínima | Uso |
|----------|----------------|-----|
| `tkinter` | Python stdlib | GUI completa |
| `pygments` | ≥ 2.0 | Tokenización VBScript |
| `pyodbc` | ≥ 4.0 | Conexión SQL Server |

Driver ODBC requerido en el sistema: `ODBC Driver 17` o `18 for SQL Server` (configurable con `--driver`).