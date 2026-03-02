# Manual de Usuario — Editor de Scripts VBS

Editor de código VBScript con resaltado de sintaxis, panel lateral dinámico y conexión directa a SQL Server.  
Diseñado como reemplazo del editor básico integrado en la aplicación de escritorio (Gestión 21).

---

## 1. Lanzamiento

El editor se abre automáticamente cuando se hace clic en **"Editar script"** desde la aplicación principal. No es necesario ejecutar ningún comando manualmente.

### Parámetros disponibles

| Parámetro | Obligatorio | Por defecto | Descripción |
|-----------|:-----------:|-------------|-------------|
| `--server` | Sí* | — | Servidor SQL Server (ej: `srv\sql2019`) |
| `--database` | Sí* | — | Nombre de la base de datos |
| `--user` | Sí* | — | Usuario SQL Authentication |
| `--password` | Sí* | — | Contraseña SQL Authentication |
| `--table` | No | `G_SCRIPT` | Nombre de la tabla |
| `--key-columns` | Sí* | — | Columnas clave separadas por coma (ej: `MODELO,CODIGO`) |
| `--key-values` | Sí* | — | Valores de la clave separados por coma (ej: `T01,BOBINADO`) |
| `--content-column` | No | `SCRIPT` | Columna que contiene el código VBS |
| `--editable-columns` | No | — | Columnas editables desde el sidebar (separadas por coma) |
| `--driver` | No | autodetectado | Driver ODBC (ej: `ODBC Driver 18 for SQL Server`) |
| `--config` | No | — | Ruta a archivo JSON de configuración |

\* Obligatorio solo para conexión a BD. Sin estos parámetros el editor arranca en **modo local**.

### Modo local (sin BD)

Si se lanza sin parámetros de conexión, el editor abre un script de ejemplo predefinido y una lista de scripts de prueba. Se puede editar libremente pero el guardado es simulado (no persiste). Útil para probar la instalación o el resaltado de sintaxis.

### Configuración por archivo JSON

En lugar de pasar todos los parámetros por línea de comandos, se puede crear un archivo JSON:

```json
{
  "server": "srv\\sql2019",
  "database": "MI_BD",
  "user": "usuario",
  "password": "clave",
  "table": "G_SCRIPT",
  "key_columns": ["MODELO", "CODIGO"],
  "key_values": ["T01", "BOBINADO"],
  "content_column": "SCRIPT"
}
```

Y lanzar con: `editor.exe --config config.json`

La prioridad de configuración es: **Línea de comandos > Variables de entorno > Archivo JSON**.

---

## 2. Interfaz

```
┌──────────────────────────────────────────────────────────────────┐
│  Editor VBS - T01 / BOBINADO                         [─] [□] [×]│
├────────────┬─────────────────────────────────────────────────────┤
│            │ [ Mostrar SCRIPT ▼  T01/BOBINADO              ]    │
│  MODELO    │ ┌─ Buscar: [________________] [▼] [▲] [n/N]  ──┐  │
│  T01       │ │                                               │  │
│            │ │ 01 │ If var0="X" Then                         │  │
│  CODIGO    │ │ 02 │     r="\\DILOERP\in2$\DATOS\BOB.GIF"    │  │
│  BOBINADO  │ │ 03 │ End If                                   │  │
│            │ │ 04 │                                           │  │
│  TIPO      │ │ 05 │ ' Este es un comentario                  │  │
│  T - OT    │ │ 06 │ Dim resultado                            │  │
│            │ │ 07 │ resultado = MsgBox("Hola")               │  │
│  GRUPO     │ │    │                                           │  │
│  [_______] │ │    │                                           │  │
│            │ │    │                                           │  │
│ ────────── │ │    │                                           │  │
│ Var 0 [__] │ │    │                                           │  │
│ Var 1 [__] │ │    │                                           │  │
│ Var 2 [__] │ │    │                                           │  │
│ Var 3 [__] │ │    │                                           │  │
│ ...        │ └────┘                                           │  │
│ Var 9 [__] │                                                     │
├────────────┴─────────────────────────────────────────────────────┤
│  SQL (T01/BOBINADO)  |  Línea: 1  Col: 1  |  Guardado           │
└──────────────────────────────────────────────────────────────────┘
```

### Elementos de la interfaz

| # | Elemento | Ubicación | Descripción |
|---|----------|-----------|-------------|
| 1 | **Título de ventana** | Arriba | Muestra las claves del script activo (ej: `T01 / BOBINADO`) o `Local` |
| 2 | **Panel lateral (Sidebar)** | Izquierda | Datos del registro: campos de solo lectura, campos editables y variables |
| 3 | **Selector de scripts** | Arriba del editor | Desplegable para cambiar entre scripts del mismo modelo |
| 4 | **Barra de búsqueda** | Arriba del editor, bajo el selector | Búsqueda de texto siempre visible |
| 5 | **Números de línea** | Izquierda del editor | Numeración automática sincronizada con el scroll |
| 6 | **Área de edición** | Centro | Editor de código con resaltado de sintaxis VBScript |
| 7 | **Barra de estado** | Abajo | Origen de datos, posición del cursor, estado de guardado |

---

## 3. Panel lateral (Sidebar)

El panel lateral muestra la información del registro de la base de datos, dividido en dos secciones:

### Sección superior: Campos del registro

- **Campos de solo lectura** (fondo gris): Datos informativos como MODELO, CODIGO, TIPO, etc.
- **Campos editables** (fondo blanco): Campos que se pueden modificar directamente, como GRUPO, DESCRIPCION, etc. Los campos editables se configuran con el parámetro `--editable-columns`.

### Sección inferior: Variables (Var 0 – Var 9)

Siempre se muestran **10 filas de variables** (Var 0 a Var 9), todas editables. Corresponden a las columnas `VAR0`–`VAR9` de la tabla en la base de datos.

- Si la columna existe en BD y tiene valor, se muestra precargado.
- Si no existe o está vacía, se muestra en blanco.
- Al guardar (Ctrl+S), los valores editados se envían a la BD junto con el script.

---

## 4. Selector de scripts (desplegable)

El desplegable en la parte superior del editor permite cambiar entre diferentes scripts **sin cerrar la aplicación**.

### Funcionamiento

- Al abrir el editor conectado a BD, se cargan automáticamente todos los scripts que comparten la primera columna clave (ej: todos los scripts con `MODELO = T01`).
- Al seleccionar un script del desplegable, se recarga **todo el registro completo**: el código, los campos del sidebar y las variables.
- Si hay cambios sin guardar, se pregunta antes de cambiar:

```
┌──────────────────────────────────┐
│  Cambios sin guardar             │
│                                  │
│  ¿Guardar antes de cambiar?     │
│                                  │
│  [Sí]    [No]    [Cancelar]     │
└──────────────────────────────────┘
```

### En modo local

Se muestran scripts de ejemplo predefinidos para demostración.

---

## 5. Barra de búsqueda

### Búsqueda rápida (siempre visible)

La barra de búsqueda está siempre visible encima del área de edición.

1. Escribir el texto a buscar en el campo de búsqueda.
2. Pulsar **Enter** o el botón **▼** (Siguiente) para buscar.
3. Las coincidencias se resaltan en **amarillo**. La coincidencia activa se resalta en **naranja**.
4. Usar **▲** (Anterior) o **▼** (Siguiente) para navegar entre resultados.
5. El contador muestra la posición actual: `3/12` = resultado 3 de 12 encontrados.

**Atajo**: Pulsar **Ctrl+F** lleva el foco directamente al campo de búsqueda.

### Buscar y reemplazar (flotante)

Para buscar y reemplazar texto, pulsar **Ctrl+H**. Se abre una barra flotante en la esquina superior derecha del editor con campos de búsqueda y reemplazo.

- **Reemplazar**: Sustituye la coincidencia actual.
- **Reemplazar todo**: Sustituye todas las coincidencias de una vez.
- **F3** / **Shift+F3**: Siguiente / Anterior coincidencia.

---

## 6. Resaltado de sintaxis

El editor colorea automáticamente el código VBScript según el tipo de elemento:

| Color | Elemento | Ejemplos |
|-------|----------|----------|
| Azul (`#0909C9`) | Palabras clave | `If`, `Then`, `End`, `Sub`, `Function`, `Dim`, `Set` |
| Morado (`#9747AF`) | Cadenas de texto | `"Hola mundo"`, `"ruta\archivo"` |
| Verde (`#008000`) | Comentarios | `' Esto es un comentario` |
| Naranja (`#FF7640`) | Operadores | `=`, `+`, `-`, `&`, `<>` |
| Gris (`#696868`) | Puntuación | `(`, `)`, `,`, `.` |
| Negro (`#000000`) | Texto general | Variables, números, funciones |

El resaltado se actualiza automáticamente con cada cambio en el texto.

---

## 7. Atajos de teclado

| Atajo | Acción |
|-------|--------|
| **Ctrl + S** | Guardar script y campos editados en BD |
| **Ctrl + Z** | Deshacer último cambio |
| **Ctrl + Y** | Rehacer último cambio deshecho |
| **Ctrl + A** | Seleccionar todo el texto |
| **Ctrl + F** | Foco en la barra de búsqueda fija |
| **Ctrl + H** | Abrir buscar y reemplazar (flotante) |
| **Ctrl + G** | Ir a número de línea |
| **F3** | Buscar siguiente coincidencia |
| **Shift + F3** | Buscar coincidencia anterior |

---

## 8. Guardar cambios

### Proceso de guardado (Ctrl+S)

Al pulsar Ctrl+S se guarda **todo a la vez**:

1. El **contenido del script** (área de edición).
2. Los **campos editables** del sidebar (ej: GRUPO, DESCRIPCION).
3. Los **valores de las variables** (Var 0 a Var 9).

Todo se envía en un solo `UPDATE` a la base de datos.

### Indicadores de estado

| Indicador en la barra de estado | Significado |
|---------------------------------|-------------|
| `SQL (T01/BOBINADO)` | Conectado a BD, editando script T01/BOBINADO |
| `Local` | Sin conexión a BD, modo de prueba |
| `Modificado` | Hay cambios sin guardar |
| `Guardado` | Sin cambios pendientes |
| `Guardado en SQL Server` | Confirmación temporal tras guardar con éxito (1,5 s) |
| `Guardado (local)` | Guardado simulado en modo sin BD |

### Al cerrar con cambios pendientes

Si se cierra la ventana (botón X) con cambios sin guardar, aparece un diálogo de confirmación con tres opciones:

- **Sí**: Guarda y cierra.
- **No**: Cierra sin guardar (se pierden los cambios).
- **Cancelar**: Vuelve al editor sin cerrar.

---

## 9. Ir a línea

Pulsar **Ctrl+G** abre un diálogo donde se puede escribir un número de línea. El cursor se mueve directamente a esa línea y el editor hace scroll para mostrarla.

---

## 10. Consejos de uso

### Escritura de código VBScript

- Los comentarios empiezan con apóstrofe: `' Comentario`
- Las cadenas de texto van entre comillas dobles: `"texto"`
- Usa indentación (Tab o espacios) para mayor legibilidad.
- Cierra siempre las estructuras: `If...End If`, `Sub...End Sub`, `For...Next`.

### Buenas prácticas

- **Guardar frecuentemente** con Ctrl+S.
- **Usar el desplegable** para cambiar entre scripts en vez de cerrar y reabrir.
- Las **variables Var 0–9** se pueden usar como parámetros que la aplicación principal lee en tiempo de ejecución.
- Si necesitas buscar un texto largo, usa **Ctrl+F** para ir rápidamente a la barra de búsqueda.

---

## 11. Solución de problemas

### El editor no arranca

**Posible causa**: Falta el driver ODBC de SQL Server.  
**Solución**: Instalar "ODBC Driver 17 for SQL Server" o "ODBC Driver 18 for SQL Server" desde la web de Microsoft. El editor detecta automáticamente el driver disponible.

### Error de conexión al arrancar

**Posibles causas**:
- Servidor SQL Server inaccesible (verificar red y nombre del servidor).
- Credenciales incorrectas (verificar `--user` y `--password`).
- Driver ODBC no instalado.

**Solución**: Si el Driver 18 no funciona, probar con: `--driver "ODBC Driver 17 for SQL Server"`.

### El editor abre pero no carga el script

**Posible causa**: Los valores de las claves no coinciden con ningún registro de la tabla.  
**Solución**: Verificar que `--key-values` sea exactamente igual a los datos en BD (mayúsculas, espacios, etc.).

### Error `42S22` al cargar o guardar

**Causa**: La columna especificada en `--content-column` no existe en la tabla.  
**Solución**: Verificar el nombre exacto de la columna en SQL Server. El valor por defecto es `SCRIPT`.

### El guardado avisa "0 filas actualizadas"

**Causa**: No existe un registro con esa combinación de claves en la tabla.  
**Solución**: Crear el registro en BD antes de editar, o verificar que las claves son correctas.

### Los colores no se ven correctamente

**Solución**: Reiniciar el editor. Si persiste, verificar la versión de Pygments con `pip show pygments` (requiere >= 2.0).

### El desplegable de scripts está vacío

**Causa**: No se encontraron otros scripts con la misma primera clave.  
**Solución**: Verificar que existen registros en la tabla con el mismo valor en la primera columna clave (ej: `MODELO = T01`).

---

## 12. Registro de actividad (Logs)

El editor genera un archivo de log en:

```
%APPDATA%\EditorVBS\editor.log
```

Este archivo registra errores, conexiones y operaciones de guardado. Se rota automáticamente al alcanzar 1 MB (se conservan los 3 últimos archivos). Es útil para diagnosticar problemas: si algo no funciona, revisar este archivo para ver el detalle del error.
