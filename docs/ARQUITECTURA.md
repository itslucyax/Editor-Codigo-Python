# Arquitectura del Proyecto

## Visión general

Aplicación de escritorio Python con tres capas bien delimitadas: interfaz gráfica (Tkinter), resaltado de sintaxis (Pygments) y acceso a datos (pyodbc → SQL Server). La comunicación entre capas siempre va de arriba hacia abajo; `db/`no sabe nada de la UI y `syntax/` no sabe nada de la DB.

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│                    (Punto de entrada)                            │
│                   Parsea argumentos CLI                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
     ┌──────────┐    ┌──────────┐    ┌──────────┐
     │   db/    │    │ editor/  │    │ config   │
     │connection│◄───│   app    │───►│  .py     │
     └──────────┘    └────┬─────┘    └──────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  text_   │ │  line_   │ │  syntax/ │
        │  editor  │ │ numbers  │ │ highlight│
        └──────────┘ └──────────┘ └──────────┘
```
---

## Módulos

### main.py - Bootstrap

Punto de entrada. Parsea argumentos con `argparse`, instancia `DatabaseConnection`, carga el script con `get_script()`, lanza `EditorApp` y cierrra la conexión al salir del script `mainloop`. Si faltan parámetros de DB, arranca en modo local con un script de ejemplo hardcodeado.

Si `connect()` o `get_script()` lanzan excepción, termina con `sys.exit(1)` y el error va a stderr.

---

```python
# Flujo principal
1. Parsear argumentos CLI (argparse)
2. Crear conexión a BD (DatabaseConnection)
3. Cargar script desde BD (get_script)
4. Crear ventana del editor (EditorApp)
5. Ejecutar loop principal (mainloop)
6. Cerrar conexión al salir
```

**Argumentos que procesa**:
- `--server`, `--database`, `--modelo`, `--codigo`
- `--content-column`, `--user`, `--password`
- `--table`, `--driver`

---

### config.py - Constantes visuales

Único punto de configuración para colores y fuente. Todaslas constantes son strings o tuplas importadas directamente por los módulos que las necesitan. Cambiar un color aquí afecta a todos los componentes sin tocar nada más.

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

**Ventaja**: Cambiar colores en un solo lugar afecta a todo el editor.

---

### db/connection.py - Acceso a datos

**Clase principal**: `DatabaseConnection`

Encapsula la conexión pyodbc y las dos únicas operaciones que necesita el editor: leer y escribir un script. La tabla y la columna de contenido son configurables en tiempo de ejecución vía argumentos CLI.

Usa SQL Authentication (`UID`/`PWD`). No soporta Windows Authentication. La conexión se abre con `autocommit=False`; el commit se hace explícitamente en `save_script()` tras comprobar `rowcount`.

```python
class DatabaseConnection:
    def __init__(server, database, table, user, password, content_column, ...)
    def connect()                    # Abre conexión pyodbc
    def close()                      # Cierra conexión
    def get_script(modelo, codigo)   # SELECT del script
    def save_script(modelo, codigo, content)  # UPDATE del script
```

**Errores que puede lanzar:**

| Situación | Excepción |
|-----------|-----------|
| Faltan `--user` o `--password` | `ValueError` |
| No se puede conectar al servidor | `ConnectionError` (wrappea `pyodbc.Error`) |
| Script no encontrado en BD | `LookupError` |
| Columna `--content-column` no existe | `LookupError` (error ODBC `42S22`) |

**SQL generado** (parámetros tipados, sin concatenación de strings):

```sql
SELECT [SCRIPT] FROM [G_SCRIPT] WHERE [MODELO] = ? AND [CODIGO] = ?
UPDATE [G_SCRIPT] SET [SCRIPT] = ? WHERE [MODELO] = ? AND [CODIGO] = ?
```

---

### editor/app.py - Ventana principal

**Clase principal**: `EditorApp` (`tk.Tk`)

Monta la ventana, conecta los componentes y gestiona los eventos de alto nivel. No hace queries ni tokeniza; delega en `DatabaseConnection` y `TextEditor`.

Estructura de la ventana:
- `Frame` principal con `TextEditor` (derecha) y `LineNumbers` (izquierda)  layout `pack`
- `Label` de barra de estado anclado al fondo (`side="bottom"`)

```python
class EditorApp(tk.Tk):
    def __init__(inicial_text, db, modelo, codigo)
    
    # Métodos principales
    def _guardar()       # Ctrl+S → save_script()
    def _on_cerrar()     # Confirmar antes de cerrar
    def _update_status() # Actualizar barra de estado
    
    # Atajos de teclado
    def _seleccionar_todo()  # Ctrl+A
    def _deshacer()          # Ctrl+Z
    def _rehacer()           # Ctrl+Y
```

**Componentes que contiene**:
- `TextEditor`: Área de edición
- `LineNumbers`: Números de línea
- `Label`: Barra de estado

Atajos registrados con `bind_all` para que funciones independientemente del foco:

| Atajo | Método |
|-------|--------|
| `Ctrl+S` | `_guardar()` |
| `Ctrl+Z` | `_deshacer()` → `edit_undo()` |
| `Ctrl+Y` | `_rehacer()` → `edit_redo()` |
| `Ctrl+A` | `_seleccionar_todo()` |

El cierre se intercepta con `protocol("WM_DELETE_WINDOW", _on_cerrar)`. Si `edit_modified()` devuelve `True`, muestra diálogo `askyesnocancel` antes de destruir la ventana.

La barra de estado se actualiza en `_update_status()`, enlazada a `<<Change>>`, `<KeyRelease>` y `<ButtonRelease-1>`. Muestra origen (`SQL (MODELO/CODIGO)` o `Local`), posición del cursor (`línea.col`) y estado de modificación.

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

### Apertura

```
CLI args → main.py → DatabaseConnection.connect()    # pyodbc abre conexión
                   → DatabaseConnection.get_script() # SELECT, normaliza CRLF→LF
                   → EditorApp(contenido)
                   → TextEditor.set_content()  # strip \n + insert
                   → VBHighlighter.highlight() # primer pintado
                   → LineNumbers.redraw()      # primer dibujado
```

### Guardado (Ctrl+S)

```
Usuario pulsa Ctrl+S
    → EditorApp._guardar()
    → TextEditor.get("1.0", "end-1c")
    → DatabaseConnection.save_script()
    → SQL: UPDATE G_SCRIPT SET [SCRIPT]=? WHERE ...
    → Actualizar barra de estado
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