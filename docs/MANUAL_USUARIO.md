# Manual de Usuario

## Introducción

El Editor de Scripts VBS es una herramienta para editar código VBScript con resaltado de sintaxis y colores, similar a Visual Studio Code.

## Abrir el editor

El editor se abre automáticamente cuando haces clic en "Editar script" desde la aplicación principal. No necesitas ejecutar ningún comando.

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

### Elementos de la interfaz

| Elemento | Descripción |
|----------|-------------|
| **Título** | Muestra MODELO/CODIGO del script abierto |
| **Números de línea** | Columna izquierda con número de cada línea |
| **Área de edición** | Zona principal donde escribes el código |
| **Barra de estado** | Información sobre origen, posición y estado |

## Colores del código

| Color | Significado | Ejemplo |
|-------|-------------|---------|
| 🔵 **Azul** | Palabras clave | `If`, `Then`, `End`, `Sub`, `Function` |
| 🟠 **Naranja** | Textos entre comillas | `"Hola mundo"` |
| 🟢 **Verde** | Comentarios | `' Esto es un comentario` |
| 🟢 **Verde claro** | Números | `10`, `3.14` |
| 🟡 **Amarillo** | Funciones | `MsgBox`, `InputBox` |
| ⬜ **Blanco/Gris** | Variables y texto normal | `miVariable` |

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

### Al cerrar

Si cierras el editor con cambios sin guardar:

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
| `SQL (T01/FACTURA)` | Conectado a BD, editando script T01/FACTURA |
| `Local` | Sin conexión a BD (modo de prueba) |
| `Modificado` | Hay cambios sin guardar |
| `Guardado` | Todo guardado en BD |

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

### No se ven los colores correctamente

Reinicia el editor. Si persiste, contacta al administrador.

### Error al guardar

- Verifica que tienes conexión de red
- Puede que otro usuario esté modificando el mismo script
- Contacta al administrador si el error persiste

### El editor no abre

- Verifica que la aplicación principal está funcionando
- Contacta al administrador de sistemas
