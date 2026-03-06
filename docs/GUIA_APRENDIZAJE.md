# De Aprendiz a Autora: Domina tu Código

## Guía pedagógica completa del Editor de Scripts VBS

---

# PARTE 1: FUNDAMENTOS DE PYTHON EN ESTE PROYECTO

---

## 1.1 ¿Qué es una Clase? — El plano de construcción

Imagina que trabajas en una fábrica de coches. Tienes un **plano** que dice: "un coche tiene 4 ruedas, un motor, un color, y puede arrancar, frenar y girar". Ese plano es **la Clase**. Cada coche real que sale de la fábrica siguiendo ese plano es **un objeto** (o **instancia**).

En tu proyecto, esto es exactamente lo que pasa:

```python
class Sidebar(tk.Frame):      # ← Esto es el PLANO del panel lateral
```

Este plano dice: "Un Sidebar tiene un record, unas key_columns, unos field_widgets, y sabe _build_ui(), get_edited_fields(), etc."

Cuando en `app.py` escribes:

```python
self.sidebar = Sidebar(self.main_frame, record=self.record, ...)
```

Estás diciendo: **"Fábrica, constrúyeme un Sidebar real con ESTOS datos concretos"**. Ahora `self.sidebar` es un objeto real, vivo en la pantalla, con sus datos rellenados.

### Clases de tu proyecto y su equivalente real

| Clase | Archivo | Es como... |
|-------|---------|------------|
| `EditorApp` | app.py | El plano de **la ventana completa** (con sidebar, editor, barras) |
| `Sidebar` | sidebar.py | El plano del **panel lateral** |
| `TextEditor` | text_editor.py | El plano del **área donde escribes código** |
| `LineNumbers` | line_numbers.py | El plano de la **columna de números de línea** |
| `SearchBar` | search_bar.py | El plano de la **barra de buscar/reemplazar flotante** |
| `FixedSearchBar` | fixed_search_bar.py | El plano de la **barra de búsqueda fija** |
| `ScriptSelector` | script_selector.py | El plano del **desplegable de scripts** |
| `VBHighlighter` | vb_highlighter.py | El plano del **pintor de colores de sintaxis** |
| `DatabaseConnection` | connection.py | El plano de **la conexión con SQL Server** |
| `ConfigLoader` | config_loader.py | El plano del **cargador de configuración** |

### ¿Qué significa `class Sidebar(tk.Frame)`?

Los paréntesis no son decoración. Significan **herencia**: "Sidebar ES UN tk.Frame, pero con cosas extra". Es como decir: "Un coche deportivo ES UN coche, pero además tiene turbo y alerón".

```python
class Sidebar(tk.Frame):       # Sidebar hereda todo lo que sabe hacer un Frame
class TextEditor(tk.Text):     # TextEditor hereda todo lo que sabe hacer un Text
class EditorApp(tk.Tk):        # EditorApp hereda todo lo de una ventana Tkinter
```

¿Qué ganas con esto? Que Sidebar ya sabe pintarse en pantalla, empaquetarse con `.pack()`, destruirse con `.destroy()`... sin que tú escribas ni una línea para eso. Lo heredó del padre `tk.Frame`.

---

## 1.2 `self` — "Yo mismo"

`self` es la palabra más repetida en todo el proyecto. Aparece en **cada** método de **cada** clase. Y al principio parece inútil. Pero es absolutamente fundamental.

### La explicación sencilla

Piensa en una oficina con 3 empleados. Los 3 tienen un nombre, pero **cada uno tiene SU propio nombre**. Si uno dice "mi nombre", se refiere al suyo, no al de otro.

`self` es exactamente eso: **"mi"**, **"yo"**, **"lo mío"**.

```python
class Sidebar(tk.Frame):
    def __init__(self, master, record=None, ...):
        self.record = record or {}        # MI registro de datos
        self.key_columns = key_columns    # MIS columnas clave
        self.field_widgets = {}           # MIS widgets (cajas de texto)
```

Cuando creas DOS sidebars (uno para cada script), cada uno tiene **su propio** `self.record`, **su propio** `self.field_widgets`. No se mezclan.

### ¿Qué pasa si borras `self` de una línea?

Caso real del proyecto. En `app.py` línea del constructor:

```python
# CON self (correcto):
self.db = db                # Guarda la conexión como ATRIBUTO del objeto
                            # → Cualquier método de EditorApp puede usarla después

# SIN self (roto):
db = db                     # Crea una variable LOCAL que MUERE al terminar __init__
                            # → Cuando _guardar() intente usar self.db... ¡ERROR!
```

Otro ejemplo real. En `sidebar.py`:

```python
# CON self:
self.field_widgets[field_name] = entry    # Se guarda para siempre en el objeto
                                          # → get_edited_fields() lo leerá después

# SIN self:
field_widgets[field_name] = entry         # ¡ERROR! field_widgets no existe como variable local
```

### La regla de oro

- **`self.algo`** = un dato que el objeto **guarda para siempre** y cualquier método puede leer.
- **`algo`** (sin self) = una variable temporal que **desaparece** al terminar la función.

Si necesitas usar un dato en más de un método → ponle `self.` delante.

---

## 1.3 Métodos (`def`) vs Atributos (`self.algo`)

### Atributos: Lo que el objeto **TIENE**

Son los datos, las propiedades, la información. Se definen con `self.nombre = valor`.

```python
# En EditorApp.__init__():
self.db = db                          # TIENE una conexión a BD
self.record = record or {}            # TIENE un registro de datos
self.key_columns = key_columns or []  # TIENE una lista de columnas clave
self.content_column = content_column  # TIENE el nombre de la columna del script
self.scripts_list = scripts_list      # TIENE la lista de scripts para el desplegable
```

### Métodos: Lo que el objeto **SABE HACER**

Son funciones que están dentro de la clase. Definen acciones, comportamientos.

```python
# En EditorApp:
def _guardar(self, event=None):        # SABE guardar en BD
def _update_status(self, event=None):  # SABE actualizar la barra de estado
def _on_cerrar(self):                  # SABE gestionar el cierre de ventana
def _on_script_selected(self, ...):    # SABE reaccionar cuando cambian el script
```

### La diferencia clave

| | Atributo (`self.algo`) | Método (`def algo(self)`) |
|-|------------------------|--------------------------|
| ¿Qué es? | Un **dato** | Una **acción** |
| ¿Cómo se usa? | `self.record` | `self._guardar()` |
| Equivalente | "El coche tiene color rojo" | "El coche sabe arrancar" |
| En VB sería | `Property` o variable de módulo | `Sub` / `Function` |

### ¿Por qué algunos métodos empiezan con `_`?

El guion bajo `_` es una **convención** de Python que dice: "este método es privado, es para uso interno de la clase, no lo llames desde fuera".

```python
def _guardar(self, event=None):       # _ = "Es interno de EditorApp, la barra de atajos lo llama"
def _build_ui(self):                  # _ = "Es interno de Sidebar, se llama solo al construir"
def get_edited_fields(self):          # Sin _ = "Es público, app.py puede llamarlo"
```

No es obligatorio (Python no lo bloquea), pero es una señal para cualquier programador que lea el código: "no uses esto directamente, puede cambiar".

---

# PARTE 2: ESTRUCTURA DE ARCHIVOS (MÓDULOS)

---

## 2.1 ¿Cómo sabe Python que un archivo habla con otro?

Python **no lo sabe automáticamente**. Tú tienes que decírselo explícitamente con `import`.

Piensa en los archivos como oficinas en un edificio. Cada oficina trabaja por su cuenta. Si la oficina de Contabilidad (connection.py) necesita decirle algo a la oficina de Atención al Cliente (app.py), necesita **una puerta que las conecte**. Esa puerta es el `import`.

### La estructura de carpetas de tu proyecto

```
Editor-Codigo-Python/
│
├── main.py              ← RECEPCIÓN (punto de entrada, dirige a todos)
├── config.py            ← MANUAL DE ESTILO (colores, fuentes)
├── config_loader.py     ← ADMINISTRACIÓN (lee la configuración)
│
├── editor/              ← PLANTA DE OFICINAS DE INTERFAZ
│   ├── __init__.py      ← "Esta carpeta es un paquete Python"
│   ├── app.py           ← GERENTE (ventana principal, coordina todo)
│   ├── sidebar.py       ← Panel lateral
│   ├── text_editor.py   ← Área de texto
│   ├── line_numbers.py  ← Números de línea
│   ├── search_bar.py    ← Barra flotante de búsqueda
│   ├── fixed_search_bar.py ← Barra fija de búsqueda
│   ├── script_selector.py  ← Desplegable de scripts
│   ├── logger.py        ← Sistema de registro
│   └── syntax/          ← SUB-OFICINA DE COLORES
│       ├── __init__.py
│       └── vb_highlighter.py  ← Pintador de sintaxis VBS
│
└── db/                  ← PLANTA DE DATOS
    ├── __init__.py
    └── connection.py    ← Toda la comunicación con SQL Server
```

### ¿Para qué sirve `__init__.py`?

Es un archivo que le dice a Python: "esta carpeta no es una carpeta cualquiera, es un **paquete** (módulo) de Python, puedes importar cosas de ella". Puede estar vacío, pero tiene que existir.

Sin `__init__.py` en `editor/`, la línea `from editor.app import EditorApp` daría error.

---

## 2.2 El sistema de `import` — Cómo viaja la información

### Ejemplo real del proyecto

En `main.py` tienes estas líneas:

```python
from db.connection import DatabaseConnection, parse_connection_string, ...
from editor.app import EditorApp
from config_loader import ConfigLoader
```

Esto dice:
- "De la carpeta `db`, archivo `connection.py`, tráeme la clase `DatabaseConnection` y la función `parse_connection_string`"
- "De la carpeta `editor`, archivo `app.py`, tráeme la clase `EditorApp`"
- "Del archivo `config_loader.py` (en la raíz), tráeme la clase `ConfigLoader`"

### ¿Cómo viaja la información concretamente?

Paso a paso real cuando `app.py` necesita usar `Sidebar`:

```python
# En app.py (arriba del todo):
from editor.sidebar import Sidebar   # 1) Python lee sidebar.py y "trae" la clase Sidebar

# Más abajo, en el constructor:
self.sidebar = Sidebar(              # 2) Crea un objeto Sidebar PASÁNDOLE datos
    self.main_frame,                 #    - El frame donde se va a pintar
    record=self.record,              #    - Los datos del registro
    key_columns=self.key_columns,    #    - Las columnas clave
)
```

La información viaja **como argumentos de función** (parámetros). Sidebar recibe los datos cuando lo creates, los guarda en `self.record`, `self.key_columns`, etc., y los usa para construir su interfaz.

### Flujo completo de imports en el proyecto

```
main.py
  │
  ├── import ConfigLoader        ← de config_loader.py
  ├── import DatabaseConnection  ← de db/connection.py
  └── import EditorApp           ← de editor/app.py
         │
         ├── import TextEditor   ← de editor/text_editor.py
         │      └── import VBHighlighter ← de editor/syntax/vb_highlighter.py
         ├── import LineNumbers   ← de editor/line_numbers.py
         ├── import Sidebar       ← de editor/sidebar.py
         ├── import SearchBar     ← de editor/search_bar.py
         ├── import FixedSearchBar← de editor/fixed_search_bar.py
         ├── import ScriptSelector← de editor/script_selector.py
         └── import config.*      ← de config.py (colores, fuentes)
```

### Regla importante: la información fluye en UN solo sentido

`db/connection.py` **NUNCA** importa nada de `editor/`. Y `editor/sidebar.py` **NUNCA** importa nada de `db/`. La comunicación siempre pasa por `app.py`, que es el director de orquesta. Esta regla se llama **separación de capas** y evita que todo se convierta en un lío de dependencias cruzadas.

---

# PARTE 3: LIBRERÍAS (Las herramientas)

---

Cada `import` que ves al principio de un archivo trae una herramienta que alguien ya programó por nosotros. No reinventamos la rueda.

### Librerías externas (instaladas con `pip`)

| Librería | Archivo donde se usa | ¿Qué problema resuelve? |
|----------|---------------------|------------------------|
| **pyodbc** | db/connection.py | Conectar con SQL Server desde Python. Sin esto, no podríamos hacer SELECT ni UPDATE. Es como el "cable" entre Python y la base de datos. |
| **pygments** | editor/syntax/vb_highlighter.py | Analizar código VBScript y clasificar cada palabra (keyword, string, comentario...). Sin esto, tendríamos que programar nosotras un parser de VBS desde cero. |

### Librerías estándar de Python (ya vienen instaladas)

| Librería | Archivo donde se usa | ¿Qué problema resuelve? |
|----------|---------------------|------------------------|
| **tkinter** | Todos los de editor/ | Crear ventanas, botones, campos de texto, menús... Es la librería gráfica estándar de Python. Equivalente al sistema de Forms de VB. |
| **tkinter.ttk** | script_selector.py | Versión "moderna" de algunos widgets de tkinter. El `Combobox` (desplegable) viene de aquí. |
| **argparse** | main.py | Leer parámetros de la línea de comandos (`--server`, `--database`, etc.). Sin esto, tendríamos que parsear `sys.argv` manualmente. |
| **json** | config_loader.py | Leer y escribir archivos JSON. Python no sabe leer JSON por defecto; esta librería convierte JSON a diccionarios de Python y viceversa. |
| **os** | config_loader.py | Acceder a variables de entorno (`os.environ.get(...)`) y comprobar si un archivo existe (`os.path.exists(...)`). |
| **re** | db/connection.py | Expresiones regulares. Se usa para validar nombres de tablas/columnas (que no contengan caracteres peligrosos) y para parsear la cadena de conexión. |
| **logging** | logger.py, connection.py | Sistema de registro de actividad. Escribe mensajes en un archivo log para poder depurar después. Mucho mejor que `print()` porque tiene niveles (DEBUG, INFO, WARNING, ERROR). |
| **sys** | main.py | Acceso al sistema: `sys.exit(1)` para terminar el programa con error, `sys.stderr` para escribir mensajes de error. |

### ¿Qué es `from __future__ import annotations`?

Aparece en `db/connection.py`. Es una instrucción especial que le dice a Python: "Cuando veas un tipo como `str` o `List[dict]` en la firma de una función, no lo evalúes ahora, trátalo como texto". Esto permite que una clase se referencie a sí misma en los type hints antes de estar totalmente definida. Es un detalle avanzado de tipado, no afecta al funcionamiento del programa.

---

# PARTE 4: LÓGICA PASO A PASO

---

## 4.1 El viaje de Var 0: Desde el teclado hasta SQL Server

Vamos a seguir exactamente qué pasa cuando un usuario escribe "FACTURA" en el campo Var 0 del sidebar y pulsa Ctrl+S.

### Paso 1: El usuario escribe en el Entry

En `sidebar.py`, método `_create_variable_row()`, se creó un widget `tk.Entry` para Var 0:

```python
entry = tk.Entry(row_frame, font=("Consolas", 8), bg="#FFFFFF", ...)
entry.insert(0, value)          # Valor inicial que venía de la BD
entry.pack(side="left", ...)
self.field_widgets["VAR0"] = entry   # Se guarda la REFERENCIA al widget
```

Cuando el usuario escribe "FACTURA", el texto queda **dentro del widget Entry**. Todavía no se ha movido a ningún sitio.

### Paso 2: El usuario pulsa Ctrl+S

En `app.py`, el atajo estaba registrado:

```python
self.bind_all("<Control-s>", self._guardar)
```

Tkinter detecta la combinación de teclas y llama a `self._guardar()`.

### Paso 3: `_guardar()` recoge TODOS los datos

```python
def _guardar(self, event=None):
    # 3a) Obtener el script del editor
    contenido = self.text_editor.get("1.0", "end-1c")
    
    # 3b) Obtener campos editables del sidebar (ej: GRUPO)
    campos_editados = self.sidebar.get_edited_fields()
    
    # 3c) Obtener variables (aquí está nuestro VAR0 = "FACTURA")
    variable_values = self.sidebar.get_variable_values()
    #     → Esto devuelve {"VAR0": "FACTURA"}
    
    # 3d) Juntar todo en un solo diccionario
    campos_editados.update(variable_values)
    campos_editados[self.content_column] = contenido
    #     → campos_editados = {"GRUPO": "PRODUCCION", "VAR0": "FACTURA", "SCRIPT": "If var0=..."}
```

### Paso 4: `get_variable_values()` lee el Entry

Dentro de `sidebar.py`:

```python
def get_variable_values(self):
    variables = {}
    for field_name, widget in self.field_widgets.items():
        # ¿Es una variable? (empieza por VAR o TABLACAMPO + dígito)
        if is_var and isinstance(widget, tk.Entry):
            value = widget.get().strip()    # ← .get() LEE el texto actual del Entry
            if value:                        #    En nuestro caso: "FACTURA"
                variables[field_name] = value
    return variables
    # → {"VAR0": "FACTURA"}
```

### Paso 5: Se llama a la BD

De vuelta en `_guardar()`:

```python
    key_values = [str(self.record.get(k, "")) for k in self.key_columns]
    # → ["T01", "BOBINADO"]
    
    ok = self.db.save_record_full(self.key_columns, key_values, campos_editados)
```

### Paso 6: `save_record_full()` construye el UPDATE

En `db/connection.py`:

```python
def save_record_full(self, key_columns, key_values, updated_fields):
    # updated_fields = {"GRUPO": "PRODUCCION", "VAR0": "FACTURA", "SCRIPT": "If var0=..."}
    
    # 6a) Construye el SQL dinámicamente:
    # SET [GRUPO] = ?, [VAR0] = ?, [SCRIPT] = ?
    set_parts = [f"[{col}] = ?" for col in updated_fields.keys()]
    
    # WHERE [MODELO] = ? AND [CODIGO] = ?
    where_parts = [f"[{col}] = ?" for col in key_columns]
    
    # SQL final:
    # UPDATE [G_SCRIPT] SET [GRUPO] = ?, [VAR0] = ?, [SCRIPT] = ? WHERE [MODELO] = ? AND [CODIGO] = ?
    
    # 6b) Valores en orden: primero los del SET, luego los del WHERE
    values = ["PRODUCCION", "FACTURA", "If var0=...", "T01", "BOBINADO"]
    
    # 6c) Ejecuta con parámetros (los ? se rellenan con los values)
    cur.execute(sql, *values)
    
    # 6d) Confirma la transacción
    self._cnxn.commit()
```

### Resumen del viaje completo

```
Teclado del usuario
    ↓ (el usuario escribe "FACTURA")
tk.Entry (widget del sidebar)
    ↓ (Ctrl+S → _guardar() → get_variable_values())
widget.get() → string "FACTURA"
    ↓ (se mete en el diccionario campos_editados)
dict {"VAR0": "FACTURA", "SCRIPT": "...", ...}
    ↓ (se pasa a save_record_full())
SQL: UPDATE [G_SCRIPT] SET [VAR0] = ? WHERE [MODELO] = ? AND [CODIGO] = ?
    ↓ (pyodbc ejecuta la query con parámetros)
SQL Server → Dato guardado en la tabla
    ↓ (commit)
Barra de estado: "Guardado en SQL Server" ✓
```

---

## 4.2 ¿Cómo decide entre Plantilla y Documento?

El sistema de **Contexto** es lo que hay nuevo en tu código. Funciona así:

### El concepto

Gestión 21 tiene dos tipos de scripts:
- **Documento**: Scripts asociados a un documento concreto (factura, albarán...). Tabla: `G_SCRIPT`.
- **Plantilla**: Scripts de plantilla que se copian a los documentos. Tabla: `G_SCRIPT_PLANTILLA`.

El editor necesita saber cuál de las dos tablas usar. Esa decisión se toma en `main.py`.

### Camino 1: Parámetros individuales (`--tipo`)

```python
# El usuario lanza:
# editor.exe --server srv --database MiBD --tipo plantilla --key-columns MODELO,CODIGO --key-values T01,BOB

# En main.py se lee:
context_type = final_config.get("tipo", CONTEXT_DOCUMENTO)  # → "plantilla"

# Se resuelve la tabla:
resolved_table = resolve_table_for_context("plantilla")
# → Mira en DEFAULT_TABLES: {"documento": "G_SCRIPT", "plantilla": "G_SCRIPT_PLANTILLA"}
# → Devuelve "G_SCRIPT_PLANTILLA"

# Se crea la conexión con esa tabla:
db = DatabaseConnection(server=..., table="G_SCRIPT_PLANTILLA", ...)
```

### Camino 2: Cadena de conexión extendida (formato Gestión 21)

```python
# El responsable de Gestión 21 lanza:
# editor.exe --connection-string "driver={SQL Server};server=srv;uid=user;pwd=pass;database=MiBD T01 D"
#                                                                                              ↑   ↑
#                                                                                           MODELO  D=Documento
```

El **formato extendido** mete MODELO y tipo (D/P) al final del campo `database`.

```python
# parse_connection_string() detecta los tokens extra:
tokens = "MiBD T01 D".split()  # → ["MiBD", "T01", "D"]
# len(tokens) >= 3 y último es "D" → formato extendido
result["database"] = "MiBD"          # Nombre real de la BD
result["modelo"] = "T01"             # MODELO detectado
result["tipo"] = "documento"         # D → documento, P → plantilla
```

### Decisión final en `main.py`

```python
if conn_str_raw:
    # Cadena de conexión → from_connection_string() detecta todo automáticamente
    db = DatabaseConnection.from_connection_string(conn_str_raw, ...)
    # Si la cadena tenía "D", db.context_type = "documento", db.table = "G_SCRIPT"
    # Si la cadena tenía "P", db.context_type = "plantilla", db.table = "G_SCRIPT_PLANTILLA"
else:
    # Parámetros individuales → resolve_table_for_context() decide
    resolved_table = resolve_table_for_context(context_type, ...)
    db = DatabaseConnection(table=resolved_table, ...)
```

### ¿Y si quiero que Plantilla use una tabla diferente?

Se puede personalizar:

```
editor.exe --tipo plantilla --table-plantilla "MI_TABLA_CUSTOM"
```

Esto sobreescribe el default `G_SCRIPT_PLANTILLA` con `MI_TABLA_CUSTOM`.

---

# PARTE 5: SIMULACRO DE EXAMEN

---

## "Soy tu jefe y quiero pillarte. 5 preguntas difíciles."

---

### Pregunta 1: "¿Dónde se guarda el texto del script antes de mandarlo a SQL Server?"

**Respuesta técnica**:

El texto vive dentro del widget `tk.Text` del editor (en `self.text_editor`, que es una instancia de `TextEditor` definida en `text_editor.py`). Tkinter lo almacena internamente en memoria. Cuando el usuario pulsa Ctrl+S, el método `_guardar()` de `app.py` lo extrae con:

```python
contenido = self.text_editor.get("1.0", "end-1c")
```

Donde `"1.0"` significa "línea 1, columna 0" (el inicio) y `"end-1c"` significa "el final menos 1 carácter" (porque Tkinter siempre añade un `\n` extra al final). El texto extraído se pone en un diccionario Python junto con los demás campos y se pasa a `db.save_record_full()`, que construye un `UPDATE` parametrizado y lo ejecuta con `pyodbc`.

**En ningún momento se guarda en un archivo temporal**: va directo de la memoria del widget al `UPDATE` de SQL Server.

---

### Pregunta 2: "Si mañana cambio la tabla de G_SCRIPT a G_CODIGO_VBS, ¿qué archivos hay que tocar?"

**Respuesta técnica**:

**Ningún archivo de código**. La tabla es completamente configurable desde fuera:

- Por CLI: `--table G_CODIGO_VBS`
- Por JSON: `"table": "G_CODIGO_VBS"` en el archivo de configuración
- Por variable de entorno: `EDITOR_TABLE=G_CODIGO_VBS`

El código en `connection.py` usa `self.table` que se inicializó con el valor que vino de la configuración. El `SELECT` y el `UPDATE` usan `[{self.table}]`, así que se adaptan solos. Las columnas también se detectan automáticamente con `get_table_schema()` que lee `INFORMATION_SCHEMA.COLUMNS`.

Si además la nueva tabla tiene columnas diferentes (por ejemplo `TEXTO_VBS` en vez de `SCRIPT`), basta con pasar `--content-column TEXTO_VBS`. No hay ningún nombre de tabla ni columna hardcodeado (escrito a mano) en el código.

---

### Pregunta 3: "¿Cómo protege el código contra inyección SQL? Demuéstramelo."

**Respuesta técnica**:

Con dos mecanismos de defensa:

**1. Queries parametrizadas** — En `save_record_full()` y `get_record_full()`, todos los VALORES van como `?` (placeholders):

```python
sql = "UPDATE [G_SCRIPT] SET [VAR0] = ? WHERE [MODELO] = ? AND [CODIGO] = ?"
cur.execute(sql, *values)   # Los valores se pasan como argumentos separados
```

pyodbc envía los `?` y los valores por separado al servidor. El servidor los trata como datos literales, NUNCA como código SQL. Aunque alguien escriba `'; DROP TABLE G_SCRIPT; --` en Var 0, SQL Server lo guardará como texto plano.

**2. Sanitización de identificadores** — Los nombres de tabla y columna no pueden ir como `?` (limitación de SQL). Por eso existe `_sanitize_identifier()` en `connection.py`:

```python
_VALID_SQL_IDENTIFIER = re.compile(r"^[\w\s#@$]+$", re.UNICODE)

def _sanitize_identifier(name, label="identificador"):
    if not _VALID_SQL_IDENTIFIER.match(name):
        raise ValueError(f"{label} '{name}' contiene caracteres no permitidos")
    return name
```

Antes de poner un nombre de tabla o columna en el SQL, se valida con una expresión regular que solo permite letras, números, guiones bajos y #. Si alguien intenta pasar algo como `G_SCRIPT; DROP TABLE--`, el regex lo rechaza y lanza un error. Además, todos los identificadores van entre corchetes `[...]`, que es la forma estándar de SQL Server para escapar nombres.

---

### Pregunta 4: "¿Por qué destruyes y recreas el sidebar entero al cambiar de script en vez de actualizarlo?"

**Respuesta técnica**:

El sidebar se compone de decenas de widgets creados dinámicamente (Labels, Entries, Frames) según los campos del registro. No todos los registros tienen los mismos campos visibles: uno puede tener VAR0 a VAR5, otro puede tener VAR0 a VAR9, y los valores de GRUPO, DESCRIPCION, etc., cambian.

Actualizar widget por widget requeriría:
1. Localizar cada Entry/Label existente.
2. Verificar si el campo sigue existiendo en el nuevo registro.
3. Borrar campos que ya no aplican.
4. Crear campos nuevos que no existían.
5. Reorganizar el layout.

Esto es mucho más código, más propenso a bugs, y más difícil de mantener. En cambio, `destroy()` + crear nuevo es:

```python
self.sidebar.destroy()                            # Borra TODO de golpe (1 línea)
self.sidebar = Sidebar(self.main_frame, ...)      # Crea todo de nuevo con datos nuevos (1 línea)
self.sidebar.pack(side="left", fill="y", before=self.separator)  # Lo coloca (1 línea)
```

Tres líneas, cero bugs, rendimiento imperceptible (la recreación tarda menos de 10 milisegundos). La regla en programación es: **si reconstruir es más simple y no tiene coste visible, reconstruye.**

---

### Pregunta 5: "¿Qué pasaría si el servidor SQL Server tarda 30 segundos en responder al guardar? ¿Se congela la interfaz?"

**Respuesta técnica**:

**Sí, se congelaría.** Y este es un punto que conozco y se puede mejorar.

Actualmente, `_guardar()` llama a `self.db.save_record_full()` de forma **síncrona** (bloqueante). Esto significa que Tkinter se queda esperando a que la query termine. Mientras tanto, la ventana no responde a clicks ni teclado (parece "colgada").

¿Por qué se hizo así? Porque en el escenario real de Gestión 21, la BD está en la red local y las queries tardan milisegundos. El caso de 30 segundos es excepcional.

Si fuera necesario solucionarlo, las dos opciones serían:

1. **Threading**: ejecutar `save_record_full()` en un hilo separado usando `threading.Thread`, y cuando termine, notificar al hilo principal de Tkinter con `self.after()` para actualizar la barra de estado.

2. **Timeout en la conexión**: configurar un timeout en pyodbc para que si tarda más de X segundos, cancele y muestre error:
   ```python
   self._cnxn.timeout = 10  # Timeout de 10 segundos
   ```

Esto es una **mejora futura** conocida, no un defecto de diseño.

---

# PARTE 6: CHULETA RÁPIDA DE CONCEPTOS

---

| Concepto | Definición corta (en tus palabras) |
|----------|------------------------------------|
| **Clase** | Plano/molde para crear objetos. Define qué datos tienen y qué saben hacer. |
| **Objeto/Instancia** | Un ejemplar concreto creado a partir de una clase. Ej: `self.sidebar` es un objeto Sidebar. |
| **self** | Referencia al objeto actual. "Yo mismo". Permite que cada objeto tenga sus propios datos. |
| **Atributo** | Dato guardado en un objeto con `self.nombre = valor`. Persiste mientras el objeto viva. |
| **Método** | Función dentro de una clase. Define algo que el objeto sabe hacer. Siempre recibe `self`. |
| **Herencia** | Una clase "hija" hereda todo de la "padre". `class Sidebar(tk.Frame)` = Sidebar ES un Frame. |
| **`super().__init__()`** | Llamada al constructor del padre. "Primero configura lo del Frame, luego lo mío extra". |
| **import** | Trae código de otro archivo para poder usarlo. Es la conexión entre módulos. |
| **Módulo** | Un archivo `.py`. Cada archivo de tu proyecto es un módulo. |
| **Paquete** | Una carpeta con `__init__.py`. Las carpetas `editor/` y `db/` son paquetes. |
| **Callback** | Función que se pasa como parámetro para que otro código la llame después. |
| **Debounce** | Esperar un poco antes de ejecutar algo, para evitar ejecutarlo 50 veces seguidas. |
| **Query parametrizada** | SQL que usa `?` para los valores, evitando inyección SQL. |
| **`pack()`** | Sistema de layout de Tkinter que coloca widgets apilándolos (arriba, abajo, izquierda, derecha). |
| **Widget** | Cualquier elemento visual: botón, campo de texto, etiqueta, frame... |
| **Tag (en tk.Text)** | Etiqueta que se aplica a un rango de texto para darle formato (color, negrita). |
| **`mainloop()`** | Bucle infinito de Tkinter que espera eventos del usuario. El programa "vive" ahí dentro. |
| **Context manager** | Patrón `with ... as ...:` que garantiza que algo se cierre/libere al terminar. |
| **`*args`** (asterisco) | Desempaquetar una lista como argumentos separados. `f(*[1,2,3])` = `f(1,2,3)`. |
| **f-string** | String con variables dentro: `f"Hola {nombre}"`. La `f` al principio activa la sustitución. |

---

**Úsalos de forma natural cuando hables con tu jefe. No digas "la cosa del panel". Di "el atributo `self.sidebar`, que es una instancia de la clase `Sidebar`". Eso marca la diferencia.**
