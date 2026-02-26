# Preguntas Frecuentes (FAQ)

## Errores de conexión

### "Para SQL Authentication necesitas --user y --password"

**Causa**: No se pasaron las credenciales de acceso.

**Solución**: Asegurarse de incluir `--user` y `--password` en el comando:
```powershell
EditorScript.exe --server "..." --user "usuario" --password "clave" ...
```

---

### "Error de conexión a SQL Server"

**Causas posibles**:
1. Servidor no accesible (red/firewall)
2. Nombre de servidor incorrecto
3. SQL Server no está ejecutándose
4. Puerto bloqueado

**Soluciones**:
1. Verificar conexión de red: `ping servidor`
2. Verificar nombre con `\instancia` si aplica
3. Comprobar que SQL Server está activo en el servidor
4. Verificar que el firewall permite el puerto 1433

---

### "Login failed for user"

**Causa**: Usuario o contraseña incorrectos.

**Solución**: Verificar credenciales en SSMS u otra herramienta.

---

### "ODBC Driver not found"

**Causa**: El driver ODBC no está instalado.

**Solución**: Descargar e instalar desde:
https://docs.microsoft.com/es-es/sql/connect/odbc/download-odbc-driver-for-sql-server

Si tienes Driver 17 en vez de 18, usar:
```powershell
--driver "ODBC Driver 17 for SQL Server"
```

---

## Errores de datos

### "No existe script para MODELO='X' CODIGO='Y'"

**Causa**: No hay registro en la tabla con esa combinación.

**Solución**: Verificar en SSMS que existe:
```sql
SELECT * FROM G_SCRIPT WHERE MODELO = 'X' AND CODIGO = 'Y'
```

---

### "La columna 'SCRIPTS' no existe en la tabla"

**Causa**: El nombre de la columna del contenido es diferente.

**Solución**: 
1. Ver columnas reales en SSMS:
   ```sql
   SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
   WHERE TABLE_NAME = 'G_SCRIPT'
   ```
2. Usar el nombre correcto:
   ```powershell
   --content-column "NOMBRE_REAL"
   ```

---

### Los cambios no se guardan

**Causas posibles**:
1. Error silencioso de permisos
2. Otro proceso bloqueando la fila

**Soluciones**:
1. Verificar permisos del usuario SQL:
   ```sql
   -- El usuario debe tener UPDATE en la tabla
   GRANT UPDATE ON G_SCRIPT TO usuario;
   ```
2. Cerrar otras conexiones al mismo registro

---

## Problemas de visualización

### Los colores no se ven bien / están desfasados

**Causa histórica**: Caracteres CRLF (`\r\n`) de Windows desalineaban el resaltado.

**Solución aplicada**: El código normaliza automáticamente a `\n`. Si persiste:
1. Cerrar y abrir de nuevo
2. Verificar que el script no tiene caracteres extraños

---

### Los números de línea no coinciden

**Causa**: El scroll del editor y los números están desincronizados.

**Solución**: Redimensionar la ventana o hacer scroll para forzar redibujado.

---

### La ventana se ve muy pequeña/grande

**Solución**: La ventana es redimensionable. Arrastrar los bordes para ajustar. Mínimo: 600x400 píxeles.

---

## Problemas de funcionamiento

### Ctrl+S no hace nada

**Causas posibles**:
1. No hay conexión a BD (modo Local)
2. Error de conexión no mostrado

**Verificar**: La barra de estado debe mostrar `SQL (MODELO/CODIGO)`. Si muestra `Local`, no hay conexión.

---

### El editor se congela al abrir

**Causa**: Script muy grande o conexión lenta.

**Solución**: Esperar. Para scripts muy grandes (>10000 líneas), el resaltado inicial tarda más.

---

### No puedo deshacer (Ctrl+Z)

**Causa**: El historial de deshacer está vacío (no hay acciones previas).

**Nota**: El historial se pierde al cerrar el editor.

---

## Compilación

### Error al compilar con PyInstaller

**Verificar**:
1. Entorno virtual activado: `venv\Scripts\activate`
2. PyInstaller instalado: `pip install pyinstaller`
3. Estar en la carpeta correcta: `cd Editor-Codigo-Python`

---

### El EXE no funciona en otro PC

**Requisitos del PC destino**:
- Windows 10/11
- ODBC Driver 17 o 18 instalado
- Acceso de red al SQL Server

No necesita Python instalado.

---

### El EXE es muy grande (>10 MB)

**Causa**: PyInstaller incluye todas las dependencias.

**Solución** (opcional): Usar `--exclude-module` para excluir módulos no usados:
```powershell
pyinstaller --onefile --windowed --exclude-module numpy --name "EditorScript" main.py
```

---

## Integración

### ¿Cómo sabe la app qué script abrir?

La aplicación de escritorio conoce el MODELO y CODIGO del elemento donde el usuario hizo clic, y los pasa como parámetros al ejecutar el editor.

---

### ¿Se puede abrir varios editores a la vez?

Sí, cada instancia es independiente. Pero evitar editar el mismo script desde dos editores simultáneamente.

---

### ¿Qué pasa si dos usuarios editan el mismo script?

El último en guardar sobrescribe los cambios del otro. No hay bloqueo ni merge automático.

**Recomendación**: Coordinar para evitar ediciones simultáneas del mismo script.

---

## Contacto

Para problemas no listados aquí, contactar al administrador de sistemas o al equipo de desarrollo.
