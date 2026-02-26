# Guía de Instalación

## Requisitos previos

### Software necesario

| Software | Versión | Descarga |
|----------|---------|----------|
| Python | 3.10 o superior | https://www.python.org/downloads/ |
| ODBC Driver | 17 o 18 | https://docs.microsoft.com/es-es/sql/connect/odbc/download-odbc-driver-for-sql-server |
| Git | Cualquiera | https://git-scm.com/downloads |

### Verificar instalación

```powershell
python --version   # Debe mostrar Python 3.10+
git --version      # Debe mostrar versión de Git
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
python main.py
```

Debe abrirse la ventana del editor con el texto de ejemplo.

## Compilación a EXE

### 1. Instalar PyInstaller

```powershell
pip install pyinstaller
```

### 2. Compilar

```powershell
pyinstaller --onefile --windowed --name "EditorScript" main.py
```

### 3. Resultado

El ejecutable se genera en:
```
dist\EditorScript.exe
```

### Opciones de compilación

| Opción | Descripción |
|--------|-------------|
| `--onefile` | Un solo archivo EXE (más fácil de distribuir) |
| `--windowed` | Sin ventana de consola |
| `--name "X"` | Nombre del ejecutable |
| `--icon icono.ico` | Icono personalizado (opcional) |

## Distribución

El archivo `EditorScript.exe` se puede copiar a cualquier PC Windows sin necesidad de instalar Python. Solo requiere:

- ODBC Driver 17 o 18 instalado
- Acceso de red al servidor SQL Server

## Solución de problemas

### Error: "ODBC Driver not found"

Instalar el driver ODBC desde:
https://docs.microsoft.com/es-es/sql/connect/odbc/download-odbc-driver-for-sql-server

### Error: "pip no reconocido"

Asegurarse de que Python está en el PATH o usar:
```powershell
py -3 -m pip install -r requirements.txt
```

### Error al compilar con PyInstaller

Verificar que el entorno virtual está activado:
```powershell
venv\Scripts\activate
```
