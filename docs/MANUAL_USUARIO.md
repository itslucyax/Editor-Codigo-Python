# Manual de Usuario — Editor de Scripts VBS

Editor de código VBScript con resaltado de sintaxis, panel lateral dinámico y conexión directa a SQL Server.  
Diseñado como reemplazo del editor básico integrado en la aplicación de escritorio (Gestión 21).

---

## 1. Lanzamiento

El editor se abre automáticamente cuando se hace clic en **"Editar script"** desde la aplicación principal (Gestión 21). No es necesario ejecutar ningún comando manualmente.

### Modo recomendado: Cadena de conexión

La forma más sencilla de lanzar el editor es con `--connection-string`. Gestión 21 usa un **formato extendido** donde el campo `database` incluye modelo y tipo:

```
EditorScript.exe --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D"
```

El editor auto-detecta:
- **Base de datos real**: `MiBaseDatos`
- **Modelo**: `T01`
- **Tipo**: `D` = Documento, `P` = Plantilla (determina la tabla automáticamente)

### Parámetros disponibles

| Parámetro | Obligatorio | Por defecto | Descripción |
|-----------|:-----------:|-------------|-------------|
| `--connection-string` | Sí* | — | Cadena de conexión completa (ODBC o formato Gestión 21) |
| `--tipo` | No | auto | `documento` o `plantilla` (auto-detectado si la cadena usa flag D/P) |
| `--key-columns` | No | `MODELO,CODIGO` | Columnas clave separadas por coma |
| `--key-values` | No | auto | Valores de la clave (auto-detectados desde la cadena si tiene modelo) |
| `--table` | No | según tipo | `G_SCRIPT` (documento) o `G_SCRIPT_PLANTILLA` (plantilla) |
| `--content-column` | No | `SCRIPT` | Columna que contiene el código VBS |
| `--editable-columns` | No | — | Columnas editables desde el sidebar (separadas por coma) |
| `--driver` | No | autodetectado | Driver ODBC (se detecta el mejor disponible) |
| `--config-file` | No | — | Ruta a archivo JSON de configuración |

**Parámetros individuales** (compatibilidad con versiones anteriores):

| Parámetro | Descripción |
|-----------|-------------|
| `--server` | Servidor SQL Server (ej: `miservidor\SQLEXPRESS`) |
| `--database` | Nombre de la base de datos |
| `--user` | Usuario SQL Authentication |
| `--password` | Contraseña SQL Authentication |

\* Se necesita `--connection-string` O los 4 parámetros individuales (server, database, user, password). Sin ninguno, el editor arranca en **modo local**.

### Modo local (sin BD)

Si se lanza sin parámetros de conexión, el editor abre un script de ejemplo predefinido y una lista de scripts de prueba. Se puede editar libremente pero el guardado es simulado (no persiste). Útil para probar la instalación o el resaltado de sintaxis.

### Configuración por archivo JSON

En lugar de pasar todos los parámetros por línea de comandos, se puede crear un archivo JSON:

```json
{
  "connection": {
    "server": "miservidor\\SQLEXPRESS",
    "database": "MiBaseDatos",
    "user": "mi_usuario",
    "password": "mi_clave",
    "table": "G_SCRIPT",
    "content_column": "SCRIPT"
  },
  "script": {
    "key_columns": ["MODELO", "CODIGO"],
    "key_values": ["T01", "BOBINADO"],
    "editable_columns": ["GRUPO", "DESCRIPCION"]
  }
}
```

Y lanzar con: `EditorScript.exe --config-file config.json`

La prioridad de configuración es: **Línea de comandos > Variables de entorno > Archivo JSON**.

Ver `tests/editor_config.example.json` para un ejemplo completo.

---

## 2. Interfaz

```
┌──────────────────────────────────────────────────────────────────┐
│ Editor VBS — T01 / BOBINADO                         [─] [□] [×]  │
├────────────┬─────────────────────────────────────────────────────┤
│            │  [▾ SCRIPT ▾  T01/BOBINADO                      ]   │
│  MODELO    ├─────────────────────────────────────────────────────┤
│  T01       │  Buscar: [________________] [▼] [▲]  3/12           │
│            ├─────┬───────────────────────────────────────────────┤
│  CODIGO    │  01 │ If var0="X" Then                              │
│  BOBINADO  │  02 │     r="\\server\ruta\datos\BOB.GIF"           │
│            │  03 │ End If                                        │
│  TIPO      │  04 │                                               │
│  T - OT    │  05 │ ' Este es un comentario                       │
│            │  06 │ Dim resultado                                 │
│  GRUPO     │  07 │ resultado = MsgBox("Hola")                    │
│  [_______] │     │                                               │
│            │     │                                               │
│ ────────── │     │                                               │
│ Var 0 [__] │     │                                               │
│ Var 1 [__] │     │                                               │
│ Var 2 [__] │     │                                               │
│ ...        │     │                                               │
│ Var 9 [__] │     │                                               │
├────────────┴─────┴───────────────────────────────────────────────┤
│ [Documento] T01/BOBINADO  │  Línea: 1  Col: 1  │  Guardado       │
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
| `[Documento] T01/BOBINADO` | Conectado a BD en modo documento |
| `[Plantilla] T01/BOBINADO` | Conectado a BD en modo plantilla |
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
**Solución**: Instalar cualquier driver ODBC para SQL Server. El editor auto-detecta el mejor disponible (`ODBC Driver 18` > `ODBC Driver 17` > `SQL Server`).

### Error de conexión al arrancar

**Posibles causas**:
- Servidor SQL Server inaccesible (verificar red y nombre del servidor).
- Credenciales incorrectas (verificar `uid`/`pwd` en la cadena de conexión, o `--user`/`--password`).
- Driver ODBC no instalado (el editor auto-detecta `SQL Server`, `ODBC Driver 17` u `ODBC Driver 18`).

**Solución**: Verificar conectividad de red al servidor. Comprobar que hay al menos un driver ODBC instalado.

### Error al parsear la cadena de conexión

**Causa**: La cadena no tiene el formato esperado `clave=valor;clave=valor`.
**Solución**: Verificar que la cadena sigue el formato ODBC:
```
driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D
```

### El editor abre pero no carga el script

**Posible causa**: Los valores de las claves no coinciden con ningún registro de la tabla.  
**Solución**: Si usas formato extendido, el modelo se detecta automáticamente de la cadena. Verificar que exista un registro con esa clave en la tabla correspondiente.

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
