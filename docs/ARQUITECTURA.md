# Arquitectura del Proyecto

## Visión general

El proyecto sigue una arquitectura modular con separación clara entre:

- **Interfaz de usuario** (Tkinter)
- **Lógica de negocio** (resaltado de sintaxis)
- **Acceso a datos** (SQL Server)

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

## Módulos

### main.py

**Responsabilidad**: Punto de entrada de la aplicación.

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

### config.py

**Responsabilidad**: Centralizar configuración visual.

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

### db/connection.py

**Responsabilidad**: Comunicación con SQL Server.

**Clase principal**: `DatabaseConnection`

```python
class DatabaseConnection:
    def __init__(server, database, table, user, password, content_column, ...)
    def connect()                    # Abre conexión pyodbc
    def close()                      # Cierra conexión
    def get_script(modelo, codigo)   # SELECT del script
    def save_script(modelo, codigo, content)  # UPDATE del script
```

**Manejo de errores**:
- `ValueError`: Credenciales faltantes
- `ConnectionError`: Fallo de conexión
- `LookupError`: Script/columna no existe

**SQL generado**:
```sql
-- get_script
SELECT [SCRIPT] FROM [G_SCRIPT] WHERE [MODELO] = ? AND [CODIGO] = ?

-- save_script
UPDATE [G_SCRIPT] SET [SCRIPT] = ? WHERE [MODELO] = ? AND [CODIGO] = ?
```

---

### editor/app.py

**Responsabilidad**: Ventana principal de la aplicación.

**Clase principal**: `EditorApp` (hereda de `tk.Tk`)

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

---

### editor/text_editor.py

**Responsabilidad**: Widget de texto con resaltado.

**Clase principal**: `TextEditor` (hereda de `tk.Text`)

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

---

### editor/line_numbers.py

**Responsabilidad**: Mostrar números de línea sincronizados.

**Clase principal**: `LineNumbers` (hereda de `tk.Canvas`)

```python
class LineNumbers(tk.Canvas):
    def __init__(master, text_widget)
    def redraw()   # Redibujar números
```

**Sincronización**: Se actualiza cuando cambia el contenido o scroll del editor.

---

### editor/syntax/vb_highlighter.py

**Responsabilidad**: Aplicar colores al código VBScript.

**Clase principal**: `VBHighlighter`

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

**Tags definidos**:
| Tag | Token Pygments | Color |
|-----|----------------|-------|
| keyword | Token.Keyword | Azul |
| string | Token.Literal.String | Naranja |
| comment | Token.Comment | Verde |
| number | Token.Literal.Number | Verde claro |
| builtin | Token.Name.Builtin | Amarillo |

---

## Flujo de datos

### Al abrir

```
CLI args → main.py → DatabaseConnection.connect()
                   → DatabaseConnection.get_script()
                   → EditorApp(contenido)
                   → TextEditor.set_content()
                   → VBHighlighter.highlight()
```

### Al guardar (Ctrl+S)

```
Usuario pulsa Ctrl+S
    → EditorApp._guardar()
    → TextEditor.get("1.0", "end-1c")
    → DatabaseConnection.save_script()
    → SQL: UPDATE G_SCRIPT SET [SCRIPT]=? WHERE ...
    → Actualizar barra de estado
```

### Al cerrar

```
Usuario cierra ventana
    → EditorApp._on_cerrar()
    → ¿Modificado? 
        → Sí: Mostrar diálogo
            → "Sí": _guardar() + destroy()
            → "No": destroy()
            → "Cancelar": return
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
