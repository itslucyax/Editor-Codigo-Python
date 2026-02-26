# Errores Comunes y Soluciones

---

## Conexión a SQL Server

### `ValueError`: "Para SQL Authentication necesitas --user y --password"

**Causa**: No se pasaron las credenciales de acceso.

**Solución**: Asegurarse de incluir `--user` y `--password` en el comando:
```powershell
EditorScript.exe --server "..." --user "usuario" --password "clave" ...
```

---

### ConnectionError`: "Error de conexión a SQL Server"

El editor no pudo abrir la conexión pyodbc. Causas habituales por orden de probabilidad:

1. **Driver ODBC no instalado** — por defecto busca `ODBC Driver 18 for SQL Server`. Verificar con:
   ```powershell
   Get-OdbcDriver | Select-Object Name
   ```
   Si solo tienes la versión 17, pasar `--driver "ODBC Driver 17 for SQL Server"`.

2. **Servidor inaccesible** — comprobar conectividad básica:
   ```powershell
   ping NOMBRE_SERVIDOR
   Test-NetConnection NOMBRE_SERVIDOR -Port 1433
   ```

3. **Nombre de servidor incorrecto** — si la instancia no es la predeterminada, el formato es `servidor\instancia`.

4. **Credenciales incorrectas** — verificar con SSMS usando el mismo usuario y contraseña antes de depurar el editor.
---

### `ODBC Driver not found`

El driver no está instalado en el equipo. Descargarlo desde la documentación oficial de Microsoft. Una vez instalado, si la versión es distinta a la 18, especificarla con `--driver`.

---

## Datos

### `LookupError`: "No existe script para MODELO='X' CODIGO='Y'"

La clave compuesta no tiene registro en la tabla. Verificar en SSMS:

```sql
SELECT * FROM G_SCRIPT WHERE MODELO = 'X' AND CODIGO = 'Y'
```

Los valores son case-sensitive según la collation de la DB. Comprobar mayúsculas y espacios.

---

### `LookupError`: "La columna 'X' no existe en la tabla" (error ODBC `42S22`)

El valor de `--content-column` no coincide con ninguna columna real de `G_SCRIPT`. Consultar las columnas disponibles:

```sql
SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'G_SCRIPT'
```

El valor por defecto es `SCRIPT`. Si la columna se llama diferente, pasar `--content-column "NOMBRE_REAL"`.

---
### Ctrl+S no actualiza ninguna fila (aviso "0 filas actualizadas")

El `UPDATE` se ejecutó correctamente pero `rowcount` devolvió 0 — el registro existe en BD pero la clave compuesta no coincide exactamente. Revisar que `--modelo` y `--codigo` son correctos incluyendo espacios y mayúsculas.

Si el registro no existe todavía, crearlo manualmente antes de editar:

```sql
INSERT INTO G_SCRIPT (MODELO, CODIGO, SCRIPT) VALUES ('T01', 'BOBINADO', '')
```

---

### Los cambios se guardan pero se pierden

El usuario SQL no tiene permisos de `UPDATE` sobre la tabla, o hay otro proceso con un lock activo. Verificar permisos:

```sql
GRANT UPDATE ON G_SCRIPT TO nombre_usuario;
```

Para locks activos, identificarlos con `sp_who2` o desde el Activity Monitor de SSMS.

---

## Visualización

### Los colores están desfasados respecto al código

Ocurría con scripts que tenían line endings CRLF (`\r\n`). `get_script()` los normaliza a `\n` antes de cargar el contenido, por lo que en condiciones normales no debería pasar. Si persiste, abrir el script en SSMS y verificar que no contiene caracteres de control inesperados (`CHAR(13)`, `CHAR(0)`, etc.).

---

### Los números de línea no coinciden con el texto tras hacer scroll

`LineNumbers` se redibuja ante `<<Change>>`, `<KeyRelease>`, `<MouseWheel>` y `<Configure>`. Si se desincroniza, redimensionar ligeramente la ventana fuerza un `<Configure>` que dispara el redibujado.

---

## Compilación y despliegue

### El EXE no arranca en el PC de destino

Requisitos del equipo destino:
- Windows 10 o superior
- ODBC Driver 17 o 18 for SQL Server instalado
- Acceso de red al servidor SQL

No necesita Python instalado. Si el EXE muestra un error de DLL al arrancar, lo más probable es que falte el driver ODBC.

---

### PyInstaller falla al compilar

```powershell
# Verificar que el entorno virtual está activado y las dependencias instaladas
pip show pygments pyodbc pyinstaller

# Compilar desde la raíz del proyecto
cd Editor-Codigo-Python
pyinstaller --onefile --windowed --name "EditorScript" main.py
```

Si el EXE resultante no encuentra los módulos de Pygments en tiempo de ejecución, añadir:

```powershell
pyinstaller --onefile --windowed --hidden-import pygments.lexers.basic --name "EditorScript" main.py
```

---

## Uso concurrente

### Dos usuarios editando el mismo script

No hay mecanismo de bloqueo. El último en pulsar Ctrl+S sobrescribe al otro sin aviso. Coordinar a nivel de proceso o añadir un sistema de reserva a nivel de aplicación si esto es un problema recurrente.

---

### ¿Se pueden abrir varias instancias del editor?

Sí, cada instancia es un proceso independiente. El riesgo de sobreescritura mencionado arriba aplica si dos instancias apuntan al mismo `MODELO`/`CODIGO`.