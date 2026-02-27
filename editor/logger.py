# -*- coding: utf-8 -*-
"""
Sistema de logging centralizado para el editor.

Escribe logs en %APPDATA%/EditorVBS/editor.log con rotación automática.
Máximo 3 ficheros de 1 MB cada uno para no llenar disco.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Directorio de logs: %APPDATA%/EditorVBS/
_LOG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "EditorVBS")
_LOG_FILE = os.path.join(_LOG_DIR, "editor.log")

# Crear directorio si no existe
os.makedirs(_LOG_DIR, exist_ok=True)

# Logger principal
logger = logging.getLogger("EditorVBS")
logger.setLevel(logging.DEBUG)

# Handler: fichero con rotación (1 MB max, 3 backups)
_file_handler = RotatingFileHandler(
    _LOG_FILE,
    maxBytes=1_048_576,    # 1 MB
    backupCount=3,
    encoding="utf-8",
)
_file_handler.setLevel(logging.DEBUG)
_file_handler.setFormatter(logging.Formatter(
    "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger.addHandler(_file_handler)

# Handler: consola (solo WARNING+ para no ensuciar stdout)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.WARNING)
_console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(_console_handler)
