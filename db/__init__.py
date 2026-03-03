# -*- coding: utf-8 -*-
# Archivo de inicializacion del modulo db

from db.connection import (
    DatabaseConnection,
    parse_connection_string,
    resolve_table_for_context,
    detect_odbc_driver,
    CONTEXT_DOCUMENTO,
    CONTEXT_PLANTILLA,
    DEFAULT_TABLES,
)

__all__ = [
    "DatabaseConnection",
    "parse_connection_string",
    "resolve_table_for_context",
    "detect_odbc_driver",
    "CONTEXT_DOCUMENTO",
    "CONTEXT_PLANTILLA",
    "DEFAULT_TABLES",
]
