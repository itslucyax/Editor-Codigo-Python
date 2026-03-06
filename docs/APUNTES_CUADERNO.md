# Apuntes de Proyecto — Editor VBS para Gestión 21


## Página 1 · Arquitectura general

El editor tiene 3 capas. Cada capa solo habla con la de al lado, nunca se saltan:

| Capa | Carpeta | Responsabilidad |
|------|---------|-----------------|
| **Interfaz** | `editor/` | Todo lo visual: ventana, panel, botones |
| **Configuración** | `config.py`, `config_loader.py` | Colores, fuentes, parámetros |
| **Datos** | `db/` | Toda la comunicación con SQL Server |

El que las conecta es **app.py** → es el "director de orquesta".

**Regla importante**: `db/connection.py` nunca importa nada de `editor/`.
La base de datos no sabe que existe una interfaz. Si mañana cambias
la interfaz por una web, la capa de datos sigue igual.


## Página 2 · Para qué sirve cada archivo

**Raíz del proyecto:**

| Archivo | Hace |
|---------|------|
| `main.py` | Arranca todo. Lee argumentos, carga config, conecta BD, lanza ventana |
| `config.py` | Colores y fuente del editor. Si quiero cambiar un color, solo toco aquí |
| `config_loader.py` | Lee configuración de 3 sitios: JSON, variables de entorno, CLI |

**Carpeta editor/ (interfaz):**

| Archivo | Hace |
|---------|------|
| `app.py` | Ventana principal. Monta todo, gestiona atajos (Ctrl+S), coordina guardado |
| `sidebar.py` | Panel izquierdo con datos del registro y 10 variables editables |
| `text_editor.py` | Área donde se escribe el código, con resaltado automático |
| `line_numbers.py` | Columna de números de línea, sincronizada con el scroll |
| `fixed_search_bar.py` | Barra de búsqueda fija arriba del editor (siempre visible) |
| `search_bar.py` | Barra flotante de buscar/reemplazar (Ctrl+H) |
| `script_selector.py` | Desplegable para cambiar entre scripts sin cerrar el editor |
| `syntax/vb_highlighter.py` | Colorea el código VBS usando la librería Pygments |
| `logger.py` | Escribe logs en `%APPDATA%/EditorVBS/editor.log` |

**Carpeta db/ (datos):**

| Archivo | Hace |
|---------|------|
| `connection.py` | Todo el SQL: conectar, SELECT, UPDATE, detectar esquema, listar scripts |


## Página 3 · Conceptos de Python que uso en el proyecto

**Clase** = un plano para crear objetos.
Se define con `class`. Ejemplo: `class Sidebar(tk.Frame)` quiere decir
"Sidebar ES un Frame de Tkinter, pero con cosas extra que yo le añado".

**Objeto** = un ejemplar real creado a partir del plano.
`self.sidebar = Sidebar(...)` fabrica un sidebar concreto con datos reales.

**self** = "yo mismo". Cada método de una clase lo recibe como primer parámetro.
Sirve para que el objeto acceda a sus propios datos.

- `self.record = datos` → guarda el dato en el objeto. Cualquier método lo puede usar después.
- `record = datos` → variable local. Se pierde al acabar la función.

**Método** = función dentro de una clase. Lo que el objeto *sabe hacer*.
Ejemplo: `def _guardar(self)` → el editor sabe guardar.

**Atributo** = dato dentro del objeto. Lo que el objeto *tiene*.
Ejemplo: `self.db` → el editor tiene una conexión a BD.

**import** = traer código de otro archivo.
`from editor.sidebar import Sidebar` → "del archivo sidebar.py, tráeme la clase Sidebar".

**callback** = pasar una función como parámetro para que otro la llame después.
`ScriptSelector(on_select_callback=self._on_script_selected)` →
"cuando el usuario elija un script del desplegable, llama a _on_script_selected".

**`_` al principio** = convención de "es privado, uso interno". Python no lo bloquea,
pero es una señal: no lo llames desde fuera.


## Página 4 · Flujo de guardar (Ctrl+S)

Cuando el usuario escribe algo en Var 0 y pulsa guardar:

```
 1. Tkinter detecta Ctrl+S
 2. Llama a _guardar() en app.py
 3. Lee el script:  text_editor.get("1.0", "end-1c")
 4. Lee campos editables:  sidebar.get_edited_fields()
 5. Lee variables Var 0-9:  sidebar.get_variable_values()
 6. Junta todo en un diccionario:
      {"SCRIPT": "...", "GRUPO": "...", "VAR0": "FACTURA"}
 7. Pasa el dict a db.save_record_full()
 8. connection.py construye el SQL:
      UPDATE [G_SCRIPT] SET [SCRIPT]=?, [VAR0]=? WHERE [MODELO]=? AND [CODIGO]=?
 9. Ejecuta con parámetros (los ? se rellenan con los valores)
10. Hace commit() para confirmar
11. Barra de estado muestra "Guardado en SQL Server"
```

**Clave de seguridad**: los valores van como `?`, nunca concatenados.
Así es imposible inyectar SQL aunque alguien escriba código malicioso en Var 0.


## Página 5 · Flujo de cambiar de script (desplegable)

```
 1. El usuario selecciona otro script del Combobox
 2. Llama a _on_script_selected() en app.py
 3. ¿Hay cambios sin guardar? → Pregunta: Sí / No / Cancelar
 4. Carga el registro completo desde BD: db.get_record_full()
 5. Actualiza el editor: text_editor.set_content(nuevo_script)
 6. Destruye el sidebar viejo: sidebar.destroy()
 7. Crea uno nuevo con los datos del nuevo registro
 8. Actualiza el título de la ventana
```

**¿Por qué destruir y recrear?** Porque reconstruirlo entero son 3 líneas de código
y tarda menos de 10ms. Actualizar widget por widget serían decenas de líneas y más errores.


## Página 6 · Plantilla vs Documento

El editor soporta dos contextos de trabajo con tablas distintas:

| Contexto | Flag | Tabla por defecto |
|----------|------|-------------------|
| Documento | D | `G_SCRIPT` |
| Plantilla | P | `G_SCRIPT_PLANTILLA` |

Se puede elegir de dos formas:

- Con parámetro: `--tipo plantilla`
- Automático desde la cadena de conexión de Gestión 21:
  `"database=MiBD T01 D"` → detecta MODELO=T01 y tipo=Documento

No hay que tocar código para cambiar entre uno y otro.


## Página 7 · Librerías que usamos

| Librería | Para qué la usamos |
|----------|--------------------|
| **tkinter** | Crear ventanas, botones, campos de texto (como Forms en VB) |
| **ttk** | Widgets más modernos, como el Combobox del desplegable |
| **pyodbc** | Conectar con SQL Server y ejecutar queries |
| **pygments** | Analizar código VBS y clasificar cada palabra para colorearla |
| **argparse** | Leer parámetros de la línea de comandos (--server, --database...) |
| **json** | Leer archivos de configuración JSON |
| **os** | Acceder a variables de entorno y comprobar rutas |
| **re** | Expresiones regulares (validar que nombres de tabla sean seguros) |
| **logging** | Escribir logs con niveles: DEBUG, INFO, WARNING, ERROR |


## Página 8 · Atajos de teclado

| Atajo | Acción |
|-------|--------|
| Ctrl+S | Guardar en BD |
| Ctrl+Z | Deshacer |
| Ctrl+Y | Rehacer |
| Ctrl+A | Seleccionar todo |
| Ctrl+F | Foco en la barra de búsqueda |
| Ctrl+H | Abrir buscar y reemplazar |
| Ctrl+G | Ir a línea |
| F3 | Siguiente coincidencia |
| Shift+F3 | Anterior coincidencia |


## Página 9 · Si mi jefe me pregunta...

**"¿Dónde está el texto antes de guardarse?"**
En la memoria del widget tk.Text. Se saca con `.get("1.0", "end-1c")`.
Va directo al UPDATE de SQL, no se guarda en ningún archivo temporal.

**"¿Si cambio la tabla de G_SCRIPT a otra, qué código toco?"**
Ninguno. Se configura desde fuera con `--table` o en el JSON.
Las columnas se detectan solas con `INFORMATION_SCHEMA.COLUMNS`.

**"¿Cómo proteges contra SQL injection?"**
Los valores van como `?` (parametrizados), nunca concatenados.
Los nombres de tabla y columna se validan con regex antes de usarlos.

**"¿Por qué destruyes el sidebar en vez de actualizarlo?"**
Porque recrearlo son 3 líneas, tarda <10ms y cero bugs.
Actualizar uno a uno serían muchas líneas y más propenso a fallos.

**"¿Se congela si el servidor tarda mucho?"**
Sí, porque la llamada es síncrona. En red local va en milisegundos.
Si fuera necesario, se puede añadir un hilo (threading) o un timeout.


## Página 10 · Chuleta rápida para no olvidar

| Escribo... | Significa... |
|------------|-------------|
| `self.algo` | Dato que perdura en el objeto (lo pueden leer otros métodos) |
| `contenido = self.text_editor.get("1.0", "end-1c")` | Variable local dentro de una función o método; solo existe mientras se ejecuta esa función, luego se borra. Ejemplo real: en `_guardar()` de app.py, la variable `contenido` guarda el texto del editor solo mientras dura la función |
| `def _metodo()` | Método privado (convención: no llamar desde fuera) |
| `def metodo()` | Método público (otros archivos pueden usarlo) |
| `"1.0"` | Línea 1, columna 0 — así cuenta posiciones Tkinter |
| `"end-1c"` | Final del texto menos 1 carácter (quita el \\n extra de Tkinter) |
| `return "break"` | En un atajo de teclado: que Tkinter no procese más el evento |
| `pack_propagate(False)` | El frame mantiene su tamaño fijo, no se encoge |
| `edit_modified()` | Flag de Tkinter: True si el usuario cambió algo |
| `autocommit=False` | Los cambios SQL no se guardan hasta hacer commit() |
| `super().__init__()` | "Primero ejecuta el constructor del padre, luego lo mío" |
| `widget.get()` | Lee el contenido actual de un Entry o Text |
