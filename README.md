# Editor de Scripts VBS

Editor de scripts VBScript con resaltado de sintaxis estilo VS Code y conexión dinámica a SQL Server.

## Descripción

Este proyecto es un editor de scripts diseñado para reemplazar el editor básico de una aplicación de escritorio empresarial (Gestión 21 — "Diseñador de documentos"). Permite editar scripts VBScript almacenados en SQL Server con:

- Resaltado de sintaxis con colores tipo VS Code
- Tema oscuro
- Números de línea
- Guardado directo en base de datos (Ctrl+S)
- Confirmación al cerrar si hay cambios sin guardar
- **Conexión dinámica por cadena de conexión** (sin hardcodeo)
- **Detección automática de contexto** (Documento / Plantilla)
- **Formato extendido Gestión 21** (`database=MiBaseDatos T01 D`)
- Barra de búsqueda y reemplazo (Ctrl+F / Ctrl+H)
- Sidebar dinámico con campos del registro
- Selector de scripts (desplegable)

## Requisitos

- **Python 3.10+** (solo para desarrollo/compilación)
- **SQL Server** con acceso mediante SQL Authentication
- **ODBC Driver 17 o 18** para SQL Server (auto-detectado)
- **Windows 10/11**

## Estructura del proyecto

```
Editor-Codigo-Python/
├── main.py                 # Punto de entrada, parseo de argumentos CLI
├── config.py               # Colores, fuentes y configuración visual
├── config_loader.py        # Cargador multi-fuente (CLI > ENV > JSON)
├── requirements.txt        # Dependencias Python
├── EditorScript.spec       # Configuración PyInstaller
├── db/
│   ├── __init__.py
│   └── connection.py       # Conexión dinámica SQL Server + parser cadena
├── editor/
│   ├── __init__.py
│   ├── app.py              # Ventana principal Tkinter
│   ├── text_editor.py      # Widget de texto con resaltado
│   ├── line_numbers.py     # Widget de números de línea
│   ├── sidebar.py          # Panel lateral con campos del registro
│   ├── script_selector.py  # Desplegable de scripts
│   ├── search_bar.py       # Buscar y reemplazar
│   ├── fixed_search_bar.py # Barra de búsqueda fija
│   ├── logger.py           # Configuración de logging
│   └── syntax/
│       ├── __init__.py
│       └── vb_highlighter.py  # Resaltado con Pygments
├── tests/
│   └── test_connection_string.py  # Tests del parser y contexto
└── docs/
    ├── README.md
    ├── INSTALACION.md
    ├── INTEGRACION.md
    ├── INTEGRACION_VB.md
    ├── MANUAL_USUARIO.md
    ├── ARQUITECTURA.md
    ├── SISTEMA_DINAMICO.md
    └── FAQ.md
```

## Instalación rápida

```bash
# Clonar repositorio
git clone https://github.com/itslucyax/Editor-Codigo-Python.git
cd Editor-Codigo-Python

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

Ver [docs/INSTALACION.md](docs/INSTALACION.md) para instrucciones detalladas.

## Uso

### Modo cadena de conexión (recomendado — Gestión 21)

```powershell
# Documentos
python main.py --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D" --key-columns "MODELO,CODIGO" --key-values "T01,BOBINADO"

# Plantillas
python main.py --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos_PLT A P" --key-columns "MODELO,CODIGO" --key-values "A,FACTURA"
```

El parser detecta automáticamente el MODELO y el tipo (D=Documento, P=Plantilla) del campo `database`.

### Modo parámetros individuales (compatible)

```powershell
python main.py --server "servidor\instancia" --database "MIBD" --table "G_SCRIPT" --key-columns "MODELO,CODIGO" --key-values "T01,FACTURA" --content-column "SCRIPT" --user "sa" --password "clave"
```

### Modo local (sin BD)

```powershell
python main.py
```

Se abre con un script de ejemplo para probar el editor sin necesidad de conexión.

Ver [docs/INTEGRACION.md](docs/INTEGRACION.md) para integrar con la app de escritorio.

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [INSTALACION.md](docs/INSTALACION.md) | Instalación y compilación a EXE |
| [INTEGRACION.md](docs/INTEGRACION.md) | Guía de integración (cadena de conexión) |
| [INTEGRACION_VB.md](docs/INTEGRACION_VB.md) | Integración específica con VB.NET/VB6 |
| [MANUAL_USUARIO.md](docs/MANUAL_USUARIO.md) | Manual para el usuario final |
| [ARQUITECTURA.md](docs/ARQUITECTURA.md) | Estructura técnica del código |
| [SISTEMA_DINAMICO.md](docs/SISTEMA_DINAMICO.md) | Sistema dinámico sin hardcodeo |
| [FAQ.md](docs/FAQ.md) | Preguntas frecuentes y errores |

## Licencia

Proyecto interno para uso empresarial.

## Autoras

- Lucia Martin Eslava - itslucyax
- Naiara Antolin Perez - Naiara-sys
