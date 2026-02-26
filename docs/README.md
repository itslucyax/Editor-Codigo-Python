# Editor de Scripts VBS

<p align="center">
  <img src="docs/images/editor.png" alt="Editor de Scripts VBS" width="800"/>
</p>

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6)
![Database](https://img.shields.io/badge/SQL%20Server-ODBC-red)
![Status](https://img.shields.io/badge/Status-Production-green)

Editor de scripts VBScript con resaltado de sintaxis estilo VS Code y conexión a SQL Server.

## Descripción

Este proyecto es un editor de scripts diseñado para reemplazar el editor básico de una aplicación de escritorio empresarial ("Diseñador de documentos"). Permite editar scripts VBScript almacenados en SQL Server con:

- Resaltado de sintaxis con colores tipo VS Code
- Tema oscuro
- Números de línea
- Guardado directo en base de datos (Ctrl+S)
- Confirmación al cerrar si hay cambios sin guardar

## Requisitos

- **Python 3.10+** (solo para desarrollo/compilación)
- **SQL Server** con acceso mediante SQL Authentication
- **ODBC Driver 17 o 18** para SQL Server
- **Windows 10/11**

## Estructura del proyecto

```
Editor-Codigo-Python/
├── main.py                 # Punto de entrada, parseo de argumentos CLI
├── config.py               # Colores, fuentes y configuración visual
├── requirements.txt        # Dependencias Python
├── db/
│   ├── __init__.py
│   └── connection.py       # Conexión SQL Server, get/save script
├── editor/
│   ├── __init__.py
│   ├── app.py              # Ventana principal Tkinter
│   ├── text_editor.py      # Widget de texto con resaltado
│   ├── line_numbers.py     # Widget de números de línea
│   └── syntax/
│       ├── __init__.py
│       └── vb_highlighter.py  # Resaltado con Pygments
└── docs/
    ├── README.md           # (este archivo)
    ├── INSTALACION.md
    ├── INTEGRACION.md
    ├── MANUAL_USUARIO.md
    ├── ARQUITECTURA.md
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

Ver [INSTALACION.md](INSTALACION.md) para instrucciones detalladas.

## Uso

```powershell
python main.py --server "servidor\instancia" --database "MIBD" --modelo "ABC" --codigo "FACTURA" --content-column "SCRIPT" --user "usuario" --password "clave"
```

Ver [INTEGRACION.md](INTEGRACION.md) para integrar con la app de escritorio.

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [INSTALACION.md](INSTALACION.md) | Instalación y compilación a EXE |
| [INTEGRACION.md](INTEGRACION.md) | Guía para el informático |
| [MANUAL_USUARIO.md](MANUAL_USUARIO.md) | Manual para el usuario final |
| [ARQUITECTURA.md](ARQUITECTURA.md) | Estructura del código |
| [FAQ.md](FAQ.md) | Preguntas frecuentes |

## Licencia

Proyecto interno para uso empresarial.

## Autoras

- [Lucía Martín Eslava]
- [Naiara Antolín Pérez]
