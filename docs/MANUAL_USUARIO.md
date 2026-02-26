# Manual de Usuario

Editor de código VBScript con resaltado de sintaxis y conexión directa a SQL Server, construido sobre Tkinter y Pygments. Diseñado como reemplazo del editor básico integrado en la aplicación de escritorio.

---

## Lanzamiento
El editor se abre automáticamente cuando haces clic en "Editar script" desde la aplicación principal. No necesitas ejecutar ningún comando.

### Parámetros disponibles

| Parámetro | Obligatorio | Por defecto | Descripción |
|-----------|:-----------:|-------------|-------------|
| `--server` | Sí* | — | Servidor SQL Server (ej: `srv\sql2019`) |
| `--database` | Sí* | — | Nombre de la base de datos |
| `--modelo` | Sí* | — | Columna `MODELO` del script (`nvarchar(3)`) |
| `--codigo` | Sí* | — | Columna `CODIGO` del script (`nvarchar(20)`) |
| `--user` | Sí* | — | Usuario SQL Authentication |
| `--password` | Sí* | — | Contraseña SQL Authentication |
| `--table` | No | `G_SCRIPT` | Nombre de la tabla |
| `--content-column` | No | `SCRIPT` | Columna que contiene el código |
| `--driver` | No | `ODBC Driver 18 for SQL Server` | Driver ODBC instalado en el equipo |

*Obligatorio solo si se quiere conectar a BD. Sin estos parámetros el editor arranca en modo local con un script de ejemplo.

### Modo local (sin db)
Si se lanza sin parámtros de conexión, el editor abre un script de ejemplo predefinido. Los cambios se pueden editar pero el guardado es simulado (no persiste en ningún sitio). Útil para probar la instalación o depurar el resaltado de sintaxis.

## Interfaz

```
┌─────────────────────────────────────────────────────────────┐
│  Editor VBS - T01/BOBINADO                            [─][□][×] │
├─────────────────────────────────────────────────────────────┤
│  1 │ If var0="X" Then                                       │
│  2 │      r="\\DILOERP\in2$\DATOS\BOBINADO1.GIF"           │
│  3 │ End If                                                 │
│  4 │                                                        │
│  5 │ ' Este es un comentario                                │
│    │                                                        │
├─────────────────────────────────────────────────────────────┤
│  SQL (T01/BOBINADO) | Línea: 1  Col: 1 | Guardado           │
└─────────────────────────────────────────────────────────────┘
      ▲                    ▲                  ▲
      │                    │                  │
   Origen            Posición cursor     Estado
```

El título muestra `MODELO/CODIGO`cuando hay conexión activa, o `Local`en modo sin DB. La barra de estado en la parte inferior refleja el estado de la conexión, la posición del cursor y si hay cambios pendientes sin guardar.

---

### Elementos de la interfaz

| Elemento | Descripción |
|----------|-------------|
| **Título** | Muestra MODELO/CODIGO del script abierto |
| **Números de línea** | Columna izquierda con número de cada línea |
| **Área de edición** | Zona principal donde escribes el código |
| **Barra de estado** | Información sobre origen, posición y estado |

## Resaltado de sintaxis
El resaltado usa Pygments con `VBScriptLexer`. Los colores siguen la paleta de VS Code Dark+:

| Color | Token | Ejemplos |
|-------|-------|---------|
| Azul `#569cd6` | Palabras clave | `If`, `Then`, `End`, `Sub`, `Function`, `Dim` |
| Naranja `#ce9178` | Cadenas de texto | `"Hola mundo"` |
| Verde `#6a9955` | Comentarios *(itálica)* | `' Esto es un comentario` |
| Verde claro `#b5cea8` | Números | `10`, `3.14` |
| Amarillo `#dcdcaa` | Funciones y built-ins | `MsgBox`, `InputBox`, `MiFuncion` |
| Turquesa `#4ec9b0` | Clases y tipos | `CreateObject`, tipos COM |
| Azul claro `#9cdcfe` | Variables y atributos | `miVariable`, `var0` |
| Cian `#4fc1ff` | Constantes | constantes nombradas |
| Gris `#808080` | Puntuación | `(`, `)`, `,` |
| Blanco `#d4d4d4` | Texto normal y operadores | resto del código |

El resaltado se recalcula en cada pulsación de tecla sobre e contenido completo del editor.

---

## Atajos de teclado

| Atajo | Acción |
|-------|--------|
| **Ctrl + S** | Guardar en la base de datos |
| **Ctrl + Z** | Deshacer |
| **Ctrl + Y** | Rehacer |
| **Ctrl + A** | Seleccionar todo |

## Guardar cambios

### Mientras editas

1. La barra de estado muestra **"Modificado"** cuando hay cambios sin guardar
2. Pulsa **Ctrl + S** para guardar
3. La barra muestra **"Guardado en SQL Server"** brevemente

Al pulsar `Ctrl+S` el editor ejecuta un `UPDATE` sobre la tabla configurada usando la clave `MODELO` + `CODIGO`. Si la operación afecta a exactamente una fila, la barra de estado muestra `Guardado en SQL Server` durante 1,5 segundos y el flag de modificación se resetea.

Si el `UPDATE` no afecta a ninguna fila (clave no encontrada), aparece un aviso indicando qué `MODELO` y `CODIGO` se estaban buscando.


### Al cerrar con cambios pendientes

Si  se cierra la ventana con el flag de modificado activo, el editor pregunta:

```
┌──────────────────────────────────────┐
│  Cambios sin guardar                 │
│                                      │
│  Hay cambios sin guardar.            │
│                                      │
│  ¿Desea guardar antes de cerrar?     │
│                                      │
│  [Sí]    [No]    [Cancelar]          │
└──────────────────────────────────────┘
```

- **Sí**: Guarda y cierra
- **No**: Cierra sin guardar (se pierden los cambios)
- **Cancelar**: Vuelve al editor

## Indicadores de estado

| Indicador | Significado |
|-----------|-------------|
| `SQL (T01/BOBINADO)` | Conectado a BD, editando el script T01/BOBINADO |
| `Local` | Sin conexión a BD, modo de prueba |
| `Modificado` | Hay cambios sin guardar |
| `Guardado` | Sin cambios pendientes |
| `Guardado en SQL Server` | Confirmación transitoria tras guardar (1,5 s) |
| `Guardado (local)` | Guardado simulado en modo sin BD |

---

## Consejos

### Escribir código

- Los comentarios empiezan con apóstrofe: `' Comentario`
- Las cadenas de texto van entre comillas: `"texto"`
- Indenta el código para mayor legibilidad (usa Tab o espacios)

### Evitar errores

- Cierra siempre las comillas que abras
- Asegúrate de cerrar `If` con `End If`
- Guarda frecuentemente (Ctrl + S)

## Solución de problemas

**El editor abre pero no carga el script**

Verificar que los valores de `--modelo` y `--codigo` coinciden exactamente con los de la tabla (incluyendo mayúsculas y espacios). La query usa `WHERE [MODELO] = ? AND [CODIGO] = ?` con parámetros tipados.

**Error `42S22` al cargar o guardar**

La columna especificada en `--content-column` no existe en la tabla. Revisar el nombre exacto de la columna en SQL Server. El valor por defecto es `SCRIPT`.

**Error de conexión al arrancar**

El editor falla en `connect()` y termina con código de salida 1. Las causas más comunes son: driver ODBC no instalado en el equipo (por defecto busca `ODBC Driver 18 for SQL Server`), servidor inaccesible, o credenciales incorrectas. Cambiar el driver con `--driver "ODBC Driver 17 for SQL Server"` si la versión 18 no está disponible.

**Los colores no se ven correctamente**

Reiniciar el editor. Si persiste, puede ser un conflicto con la versión de Pygments instalada — verificar con `pip show pygments` que es >= 2.0.

**El guardado avisa de "0 filas actualizadas"**

El registro con esa clave compuesta no existe en la tabla. Crear el registro manualmente en BD antes de editar, o verificar que `--modelo` y `--codigo` son correctos.
