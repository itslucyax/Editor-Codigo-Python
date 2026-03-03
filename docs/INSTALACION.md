# Guía de Instalación

## Requisitos previos

### Software necesario

| Software | Versión | Descarga |
|----------|---------|----------|
| Python | 3.10 o superior | https://www.python.org/downloads/ |
| Driver ODBC SQL Server | Cualquiera (`SQL Server`, `17` o `18` — se auto-detecta) | https://docs.microsoft.com/es-es/sql/connect/odbc/download-odbc-driver-for-sql-server |
| Git | Cualquiera | https://git-scm.com/downloads |

### Verificar instalación

```powershell
python --version   # Debe mostrar Python 3.10+
git --version      # Debe mostrar versión de Git

# Verificar drivers ODBC disponibles
Get-OdbcDriver | Select-Object Name
```

## Instalación para desarrollo

### 1. Clonar repositorio

```powershell
git clone https://github.com/itslucyax/Editor-Codigo-Python.git
cd Editor-Codigo-Python
```

### 2. Crear entorno virtual

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Verificar instalación

```powershell
# Modo local (sin BD)
python main.py

# Con cadena de conexión de Gestión 21
python main.py --connection-string "driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D"
```

Debe abrirse la ventana del editor.

## Compilación a EXE

### 1. Instalar PyInstaller

```powershell
pip install pyinstaller
```

### 2. Compilar

```powershell
# Usando el .spec del proyecto (recomendado)
pyinstaller EditorScript.spec

# O manualmente
pyinstaller --onefile --windowed --name "EditorScript" main.py
```

### 3. Resultado

El ejecutable se genera en:
```
dist\EditorScript.exe
```

### Opciones de compilación (modo manual)

| Opción | Descripción |
|--------|-------------|
| `--onefile` | Un solo archivo EXE (más fácil de distribuir) |
| `--windowed` | Sin ventana de consola |
| `--name "X"` | Nombre del ejecutable |
| `--icon icono.ico` | Icono personalizado (opcional) |
| `--hidden-import pygments.lexers.basic` | Necesario si Pygments no se detecta en runtime |

## Distribución

El archivo `EditorScript.exe` se puede copiar a cualquier PC Windows sin necesidad de instalar Python. Solo requiere:

- Windows 10 o superior
- Un driver ODBC para SQL Server instalado (se auto-detecta el mejor disponible)
- Acceso de red al servidor SQL Server

## Archivos de configuración opcionales

| Archivo | Uso |
|---------|-----|
| `editor_config.json` | Configuración por defecto (servidor, tabla, columnas) |
| Variables de entorno `EDITOR_*` | Configuración por entorno (dev, test, prod) |

La prioridad de configuración es: **CLI > Variables de entorno > JSON > Defaults**.

Ver `tests/editor_config.example.json` para un ejemplo de archivo de configuración.

## Solución de problemas

### Error: "ODBC Driver not found"

Instalar cualquier driver ODBC para SQL Server. El editor auto-detecta el mejor disponible:
- `ODBC Driver 18 for SQL Server` (preferido)
- `ODBC Driver 17 for SQL Server`
- `SQL Server` (incluido en Windows)

Descarga: https://docs.microsoft.com/es-es/sql/connect/odbc/download-odbc-driver-for-sql-server

### Error: "pip no reconocido"

Asegurarse de que Python está en el PATH o usar:
```powershell
py -3 -m pip install -r requirements.txt
```

### Error al compilar con PyInstaller

Verificar que el entorno virtual está activado:
```powershell
venv\Scripts\activate
pip show pyinstaller   # Debe mostrar versión instalada
```
