# Guía de Integración

Esta guía explica cómo integrar el editor de scripts con la aplicación de escritorio existente.

## Resumen

El editor se lanza mediante línea de comandos. La aplicación de escritorio debe ejecutar el EXE pasando los parámetros del script a editar.

El editor actua, por tanto, como un "editor especializado conectado a la base de datos", funcionando como una extensión externa de la aplicación principal.

## Parámetros CLI

| Parámetro | Obligatorio | Descripción | Ejemplo |

| `--server` | Sí | Servidor SQL Server | `"servidor\instancia"` |
| `--database` | Sí | Base de datos | `"MIBD"` |
| `--modelo` | Sí | Valor columna MODELO | `"T01"` |
| `--codigo` | Sí | Valor columna CODIGO | `"FACTURA"` |
| `--content-column` | Sí | Columna con el script | `"SCRIPT"` |
| `--user` | Sí | Usuario SQL Auth | `"usuario"` |
| `--password` | Sí | Contraseña | `"clave"` |
| `--table` | No | Tabla (default: G_SCRIPT) | `"G_SCRIPT"` |
| `--driver` | No | Driver ODBC (default: 18) | `"ODBC Driver 17 for SQL Server"` |

## Comando completo

```powershell
EditorScript.exe --server "servidor\instancia" --database "MIBD" --modelo "ABC" --codigo "FACTURA" --content-column "SCRIPT" --user "usuario" --password "clave"
```

## Integración con la app de escritorio

### Flujo esperado

```
┌─────────────────────────────────────────────────────────────┐
│  1. Usuario hace clic derecho en un elemento                │
│  2. Selecciona "Editar script"                              │
│  3. La app obtiene MODELO y CODIGO del elemento             │
│  4. La app ejecuta:                                         │
│                                                             │
│     EditorScript.exe --server "..." --modelo "ABC" ...      │
│                                                             │
│  5. Se abre el editor con el script cargado                 │
│  6. Usuario edita y guarda (Ctrl+S)                         │
│  7. Usuario cierra el editor                                │
│  8. Los cambios ya están en la BD                           │
└─────────────────────────────────────────────────────────────┘
```

### Ejemplo en código (pseudocódigo)

```vb
' Al hacer clic en "Editar script"
Sub AbrirEditor(modelo As String, codigo As String)
    Dim comando As String
    comando = "C:\Ruta\EditorScript.exe" & _
              " --server ""servidor\instancia""" & _
              " --database ""MIBD""" & _
              " --modelo """ & modelo & """" & _
              " --codigo """ & codigo & """" & _
              " --content-column ""SCRIPT""" & _
              " --user ""usuario""" & _
              " --password ""clave"""
    
    Shell comando, vbNormalFocus
End Sub
```

### Parámetros fijos vs dinámicos

| Tipo | Parámetros | Configuración |
|------|------------|---------------|
| **Fijos** | server, database, content-column, user, password | Configurar una vez en la app |
| **Dinámicos** | modelo, codigo | Dependen del elemento seleccionado |

## Base de datos

### Estructura esperada

```sql
-- Tabla: G_SCRIPT (o la que especifiques con --table)
-- Clave primaria compuesta: MODELO + CODIGO

CREATE TABLE G_SCRIPT (
    MODELO nvarchar(3) NOT NULL,
    CODIGO nvarchar(20) NOT NULL,
    SCRIPT ntext,  -- o nvarchar(max)
    -- ... otras columnas
    PRIMARY KEY (MODELO, CODIGO)
)
```

### Operaciones que realiza el editor

```sql
-- Al abrir (get_script)
SELECT [SCRIPT] FROM [G_SCRIPT] 
WHERE [MODELO] = 'ABC' AND [CODIGO] = 'FACTURA'

-- Al guardar (save_script)
UPDATE [G_SCRIPT] SET [SCRIPT] = '...' 
WHERE [MODELO] = 'ABC' AND [CODIGO] = 'FACTURA'
```

## Seguridad

### Credenciales

Las credenciales se pasan por línea de comandos. Considerar:

1. Usar un usuario SQL con permisos mínimos (solo SELECT/UPDATE en G_SCRIPT)
2. No mostrar el comando completo en logs
3. Para mayor seguridad, evaluar integrar Windows Authentication en futuras versiones

### Permisos recomendados

```sql
-- Crear usuario específico para el editor
CREATE LOGIN editor_script WITH PASSWORD = 'contraseña_segura';
USE MIBD;
CREATE USER editor_script FOR LOGIN editor_script;
GRANT SELECT, UPDATE ON dbo.G_SCRIPT TO editor_script;
```

## Pruebas

### Comando de prueba

```powershell
.\EditorScript.exe --server "gg\sql2019" --database "DATOSDILO" --modelo "T01" --codigo "BOBINADO" --content-column "SCRIPT" --user "sa" --password "sa"
```

### Verificar funcionamiento

1.  Se abre el editor con el script
2.  Los colores se muestran correctamente
3.  Ctrl+S guarda en BD
4.  Al cerrar con cambios, pregunta si guardar
