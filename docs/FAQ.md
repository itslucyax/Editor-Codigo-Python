# Errores Comunes y Soluciones

---

## Conexión a SQL Server

### `ValueError`: "Para SQL Authentication necesitas --user y --password"

**Causa**: No se pasaron las credenciales de acceso. Si usas `--connection-string`, verifica que incluye `uid=` y `pwd=`.

**Solución**:
```powershell
# Con cadena de conexión (las credenciales van dentro)
EditorScript.exe --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D" ...

# Con parámetros individuales
EditorScript.exe --server "..." --user "usuario" --password "clave" ...
```

---

### `ConnectionError`: "Error de conexión a SQL Server"

El editor no pudo abrir la conexión pyodbc. Causas habituales:

1. **Driver ODBC no instalado** — el editor auto-detecta el mejor driver disponible (`SQL Server`, `ODBC Driver 17`, `ODBC Driver 18`). Verificar con:
   ```powershell
   Get-OdbcDriver | Select-Object Name
   ```

2. **Servidor inaccesible** — comprobar conectividad:
   ```powershell
   ping miservidor
   Test-NetConnection miservidor -Port 1433
   ```

3. **Nombre de servidor incorrecto** — si la instancia no es la predeterminada, el formato es `servidor\instancia` (ej: `miservidor\SQLEXPRESS`).

4. **Credenciales incorrectas** — verificar con SSMS usando el mismo usuario y contraseña.

---

### `ValueError`: "La cadena de conexión está vacía"

Se pasó `--connection-string` pero sin valor, o el valor quedó vacío tras el parseo.

---

### `ValueError`: "No se pudieron extraer parámetros de la cadena de conexión"

La cadena no tiene formato `clave=valor` separado por `;`. Formato correcto:
```
driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D
```

---

### `ValueError`: "Contexto 'X' no válido"

Se pasó un `--tipo` que no es `documento` ni `plantilla`. Si usas cadena de conexión con formato extendido (flag D/P), no necesitas `--tipo`.

---

## Datos

### `LookupError`: "No existe registro con MODELO='X', CODIGO='Y'"

La clave compuesta no tiene registro en la tabla. Verificar en SSMS:

```sql
SELECT * FROM G_SCRIPT WHERE MODELO = 'X' AND CODIGO = 'Y'
```

Los valores son case-sensitive según la collation de la DB. Comprobar mayúsculas y espacios.

---

### `ValueError`: Identificador SQL con caracteres no permitidos

El sanitizador rechazó un nombre de tabla o columna que contiene caracteres peligrosos (`;`, `'`, `"`, `--`). Esto protege contra SQL injection. Solo se permiten letras, números, guiones bajos, espacios, `#` y `@`.

---

### Ctrl+S no actualiza ninguna fila (aviso "0 filas actualizadas")

El `UPDATE` se ejecutó pero `rowcount` devolvió 0 — la clave no coincide exactamente. Revisar que los key_values son correctos incluyendo espacios y mayúsculas.

Si el registro no existe todavía, crearlo manualmente:

```sql
INSERT INTO G_SCRIPT (MODELO, CODIGO, SCRIPT) VALUES ('T01', 'BOBINADO', '')
```

---

### Los cambios se guardan pero se pierden

El usuario SQL no tiene permisos de `UPDATE`, o hay otro proceso con un lock activo:

```sql
GRANT UPDATE ON G_SCRIPT TO nombre_usuario;
```

---

## Visualización

### Los colores están desfasados respecto al código

Ocurría con scripts que tenían line endings CRLF (`\r\n`). `get_record_full()` los normaliza a `\n` antes de cargar el contenido, por lo que en condiciones normales no debería pasar. Si persiste, abrir el script en SSMS y verificar que no contiene caracteres de control inesperados (`CHAR(13)`, `CHAR(0)`, etc.).

---

### Los números de línea no coinciden con el texto tras hacer scroll

`LineNumbers` se redibuja ante `<<Change>>`, `<KeyRelease>`, `<MouseWheel>` y `<Configure>`. Si se desincroniza, redimensionar ligeramente la ventana fuerza un `<Configure>` que dispara el redibujado.

---

## Compilación y despliegue

### El EXE no arranca en el PC de destino

Requisitos del equipo destino:
- Windows 10 o superior
- Driver ODBC para SQL Server instalado (se auto-detecta `SQL Server`, `ODBC Driver 17` u `ODBC Driver 18`)
- Acceso de red al servidor SQL

No necesita Python instalado. Si el EXE muestra un error de DLL al arrancar, lo más probable es que falte el driver ODBC.

---

### PyInstaller falla al compilar

```powershell
# Verificar que el entorno virtual está activado y las dependencias instaladas
pip show pygments pyodbc pyinstaller

# Compilar usando el .spec existente
cd Editor-Codigo-Python
pyinstaller EditorScript.spec

# O compilar manualmente
pyinstaller --onefile --windowed --name "EditorScript" main.py
```

Si el EXE resultante no encuentra los módulos de Pygments en tiempo de ejecución, añadir:

```powershell
pyinstaller --onefile --windowed --hidden-import pygments.lexers.basic --name "EditorScript" main.py
```

---

## Formato extendido de Gestión 21

### ¿Qué es el formato extendido de cadena de conexión?

Gestión 21 envía el campo `database` con información adicional:
```
database=MiBaseDatos T01 D
```
Donde `MiBaseDatos` es la base de datos real, `T01` es el modelo, y `D` es la flag de tipo (`D`=Documento, `P`=Plantilla). El parser detecta esto automáticamente.

### La flag D/P no se reconoce

Solo se reconocen `D` (documento) y `P` (plantilla) en mayúsculas como último token del campo `database`. Si el campo tiene menos de 3 tokens separados por espacio, se trata como una base de datos normal sin formato extendido.

---

## Uso concurrente

### Dos usuarios editando el mismo script

No hay mecanismo de bloqueo. El último en pulsar Ctrl+S sobrescribe al otro sin aviso. Coordinar a nivel de proceso o añadir un sistema de reserva a nivel de aplicación si esto es un problema recurrente.

---

### ¿Se pueden abrir varias instancias del editor?

Sí, cada instancia es un proceso independiente. El riesgo de sobreescritura mencionado arriba aplica si dos instancias apuntan a la misma clave compuesta (ej: mismo `MODELO`/`CODIGO`).