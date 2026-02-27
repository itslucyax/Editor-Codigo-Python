"""
Conexión a SQL Server para leer/guardar scripts en la tabla G_SCRIPT.

Autenticación: SQL Authentication (usuario/contraseña)
Clave compuesta: MODELO (nvarchar(3)) + CODIGO (nvarchar(20))
Columna de contenido: configurable via --content-column
"""

from __future__ import annotations

import logging
from typing import Optional, List, Tuple

import pyodbc

logger = logging.getLogger("EditorVBS.db")

# Drivers ODBC preferidos, de más reciente a más antiguo
_PREFERRED_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13.1 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "ODBC Driver 11 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server Native Client 10.0",
    "SQL Server",
]


def detect_odbc_driver() -> str:
    """Detecta el mejor driver ODBC instalado en la máquina.

    Recorre `_PREFERRED_DRIVERS` y devuelve el primero que esté
    disponible según `pyodbc.drivers()`.  Si no encuentra ninguno
    lanza RuntimeError con un mensaje descriptivo.
    """
    installed = pyodbc.drivers()
    logger.debug("Drivers ODBC instalados: %s", installed)
    for drv in _PREFERRED_DRIVERS:
        if drv in installed:
            logger.info("Driver ODBC seleccionado: %s", drv)
            return drv
    raise RuntimeError(
        "No se encontró ningún driver ODBC compatible con SQL Server.\n"
        f"Drivers instalados: {installed}\n"
        "Instala 'ODBC Driver 18 for SQL Server' desde:\n"
        "https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server"
    )


class DatabaseConnection:
    """
    Conecta con SQL Server usando pyodbc y permite leer/guardar scripts.
    """

    def __init__(
        self,
        server: str,
        database: str,
        table: str = "G_SCRIPT",
        user: Optional[str] = None,
        password: Optional[str] = None,
        driver: str = "ODBC Driver 18 for SQL Server",
        trust_server_certificate: bool = True,
        content_column: str = "SCRIPT",
    ):
        self.server = server
        self.database = database
        self.table = table
        self.user = user
        self.password = password
        self.driver = driver
        self.trust_server_certificate = trust_server_certificate
        self.content_column = content_column

        self._cnxn: Optional[pyodbc.Connection] = None

    def connect(self) -> None:
        """
        Abre la conexión usando SQL Authentication.
        Si el driver indicado no está disponible, intenta auto-detectar uno.
        Lanza ValueError si faltan credenciales.
        Lanza RuntimeError si no hay driver ODBC.
        """
        if not self.user or not self.password:
            raise ValueError("Para SQL Authentication necesitas --user y --password")

        # Auto-detectar driver si el indicado no está instalado
        if self.driver not in pyodbc.drivers():
            logger.warning("Driver '%s' no encontrado, auto-detectando...", self.driver)
            self.driver = detect_odbc_driver()

        parts = [
            f"DRIVER={{{self.driver}}}",
            f"SERVER={self.server}",
            f"DATABASE={self.database}",
            f"UID={self.user}",
            f"PWD={self.password}",
        ]
        if self.trust_server_certificate:
            parts.append("TrustServerCertificate=yes")

        conn_str = ";".join(parts) + ";"
        logger.debug("Cadena de conexión: %s", conn_str.replace(self.password, "****"))

        try:
            self._cnxn = pyodbc.connect(conn_str, autocommit=False)
            logger.info("Conexión abierta a %s/%s", self.server, self.database)
        except pyodbc.Error as e:
            logger.error("Fallo de conexión: %s", e)
            raise ConnectionError(f"Error de conexión a SQL Server: {e}") from e

    def close(self) -> None:
        """Cierra la conexión si existe."""
        if self._cnxn is not None:
            self._cnxn.close()
            self._cnxn = None

    def _cursor(self) -> pyodbc.Cursor:
        if self._cnxn is None:
            raise RuntimeError("No hay conexión abierta. Llama a connect() primero.")
        return self._cnxn.cursor()

    def get_script(self, modelo: str, codigo: str) -> str:
        """
        Lee el script desde la base de datos.
        
        Args:
            modelo: Valor de la columna MODELO
            codigo: Valor de la columna CODIGO
            
        Returns:
            Contenido del script como string (line endings normalizados a \n)
            
        Raises:
            LookupError: Si no existe el script
            pyodbc.ProgrammingError: Si la columna no existe (error 42S22)
        """
        cur = self._cursor()

        sql = f"""
        SELECT [{self.content_column}]
        FROM [{self.table}]
        WHERE [MODELO] = ? AND [CODIGO] = ?
        """

        try:
            row = cur.execute(sql, modelo, codigo).fetchone()
        except pyodbc.ProgrammingError as e:
            # Error 42S22 = columna no existe
            if "42S22" in str(e):
                raise LookupError(
                    f"La columna '{self.content_column}' no existe en la tabla '{self.table}'. "
                    f"Usa --content-column para especificar el nombre correcto."
                ) from e
            raise

        if not row:
            raise LookupError(f"No existe script para MODELO='{modelo}' CODIGO='{codigo}'")

        # Convertir a str y normalizar line endings para Tkinter
        content = "" if row[0] is None else str(row[0])
        return content.replace("\r\n", "\n").replace("\r", "\n")

    def save_script(self, modelo: str, codigo: str, content: str) -> bool:
        """
        Guarda el script en la base de datos.
        
        Args:
            modelo: Valor de la columna MODELO
            codigo: Valor de la columna CODIGO  
            content: Nuevo contenido del script
            
        Returns:
            True si se actualizó exactamente 1 fila
            
        Raises:
            pyodbc.ProgrammingError: Si la columna no existe
        """
        cur = self._cursor()

        sql = f"""
        UPDATE [{self.table}]
        SET [{self.content_column}] = ?
        WHERE [MODELO] = ? AND [CODIGO] = ?
        """

        try:
            cur.execute(sql, content, modelo, codigo)
        except pyodbc.ProgrammingError as e:
            if "42S22" in str(e):
                raise LookupError(
                    f"La columna '{self.content_column}' no existe. "
                    f"Verifica --content-column."
                ) from e
            raise

        updated = cur.rowcount
        self._cnxn.commit()
        logger.info("save_script: %d filas actualizadas (MODELO=%s, CODIGO=%s)",
                    updated, modelo, codigo)
        return updated == 1

    def save_record_full(
        self, 
        key_columns: List[str],
        key_values: List[str],
        updated_fields: dict
    ) -> bool:
        """
        Guarda cambios en un registro de forma dinámica.
        
        Args:
            key_columns: Lista de columnas que forman la clave primaria
            key_values: Lista de valores correspondientes a las claves
            updated_fields: Diccionario {columna: nuevo_valor} con los campos a actualizar
            
        Returns:
            True si se actualizó exactamente 1 fila
            
        Raises:
            ValueError: Si las longitudes no coinciden
            pyodbc.ProgrammingError: Si alguna columna no existe
        """
        if len(key_columns) != len(key_values):
            raise ValueError(
                f"key_columns tiene {len(key_columns)} elementos pero "
                f"key_values tiene {len(key_values)} elementos"
            )
        
        if not updated_fields:
            logger.warning("save_record_full: No hay campos para actualizar")
            return True
        
        cur = self._cursor()
        
        # Construir SET clause
        set_parts = [f"[{col}] = ?" for col in updated_fields.keys()]
        set_clause = ", ".join(set_parts)
        
        # Construir WHERE clause
        where_parts = [f"[{col}] = ?" for col in key_columns]
        where_clause = " AND ".join(where_parts)
        
        sql = f"UPDATE [{self.table}] SET {set_clause} WHERE {where_clause}"
        
        # Preparar valores para la query
        values = list(updated_fields.values()) + key_values
        
        logger.debug("save_record_full SQL: %s", sql)
        logger.debug("save_record_full valores: %s", 
                     {**updated_fields, **dict(zip(key_columns, key_values))})
        
        try:
            cur.execute(sql, *values)
        except pyodbc.ProgrammingError as e:
            if "42S22" in str(e):
                raise LookupError(
                    f"Una o más columnas no existen en la tabla '{self.table}'. "
                    f"Verifica los nombres de las columnas."
                ) from e
            raise
        
        updated = cur.rowcount
        self._cnxn.commit()
        logger.info("save_record_full: %d filas actualizadas", updated)
        return updated == 1

        return updated == 1

    # ------------------------------------------------------------------
    # Variables de entorno Var0-Var9
    # ------------------------------------------------------------------

    def get_variables(self, modelo: str, codigo: str,
                      var_columns: Optional[List[str]] = None) -> List[Tuple[str, str]]:
        """Lee las columnas Var0…Var9 de la fila del script.

        Args:
            modelo: Valor de la columna MODELO.
            codigo: Valor de la columna CODIGO.
            var_columns: Lista de nombres de columna a leer.
                         Por defecto ["VAR0", ..., "VAR9"].

        Returns:
            Lista de tuplas (nombre_columna, valor_str).  Si la columna
            no existe en la tabla se omite silenciosamente.
        """
        if var_columns is None:
            var_columns = [f"VAR{i}" for i in range(10)]

        # Filtrar columnas que realmente existen en la tabla
        existing = self._existing_columns(var_columns)
        if not existing:
            logger.warning("Ninguna de las columnas %s existe en %s",
                           var_columns, self.table)
            return [(c, "") for c in var_columns]

        cols_sql = ", ".join(f"[{c}]" for c in existing)
        sql = f"""
        SELECT {cols_sql}
        FROM [{self.table}]
        WHERE [MODELO] = ? AND [CODIGO] = ?
        """
        cur = self._cursor()
        row = cur.execute(sql, modelo, codigo).fetchone()

        result: List[Tuple[str, str]] = []
        for i, col_name in enumerate(existing):
            val = "" if row is None or row[i] is None else str(row[i]).strip()
            result.append((col_name, val))

        logger.debug("get_variables: %s", result)
        return result

    def _existing_columns(self, candidates: List[str]) -> List[str]:
        """Devuelve solo los nombres de columna que existen en la tabla."""
        cur = self._cursor()
        sql = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        """
        rows = cur.execute(sql, self.table).fetchall()
        table_cols = {r[0].upper() for r in rows}
        return [c for c in candidates if c.upper() in table_cols]

    # ------------------------------------------------------------------
    # Detección automática de esquema
    # ------------------------------------------------------------------

    def get_table_schema(self) -> List[dict]:
        """
        Obtiene el esquema completo de la tabla actual.
        
        Returns:
            Lista de diccionarios con información de cada columna:
            [
                {
                    "name": "MODELO",
                    "type": "nvarchar",
                    "max_length": 3,
                    "is_nullable": False,
                    "ordinal": 1
                },
                ...
            ]
        """
        cur = self._cursor()
        sql = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        rows = cur.execute(sql, self.table).fetchall()
        
        schema = []
        for row in rows:
            schema.append({
                "name": row[0],
                "type": row[1],
                "max_length": row[2] if row[2] else None,
                "is_nullable": row[3] == "YES",
                "ordinal": row[4]
            })
        
        logger.debug("Esquema de tabla %s: %d columnas", self.table, len(schema))
        return schema

    def get_record_full(self, key_columns: List[str], key_values: List[str]) -> dict:
        """
        Carga un registro completo con TODAS sus columnas de forma dinámica.
        
        Args:
            key_columns: Lista de nombres de columnas que forman la clave (ej: ["MODELO", "CODIGO"])
            key_values: Lista de valores correspondientes (ej: ["T01", "SCRIPT001"])
            
        Returns:
            Diccionario con {nombre_columna: valor} para todas las columnas del registro
            
        Raises:
            ValueError: Si key_columns y key_values tienen diferente longitud
            LookupError: Si no se encuentra el registro
        """
        if len(key_columns) != len(key_values):
            raise ValueError(
                f"key_columns tiene {len(key_columns)} elementos pero "
                f"key_values tiene {len(key_values)} elementos"
            )
        
        # Obtener todas las columnas de la tabla
        schema = self.get_table_schema()
        all_columns = [col["name"] for col in schema]
        
        # Construir SELECT dinámicamente
        cols_sql = ", ".join(f"[{col}]" for col in all_columns)
        
        # Construir WHERE dinámicamente
        where_parts = [f"[{col}] = ?" for col in key_columns]
        where_sql = " AND ".join(where_parts)
        
        sql = f"SELECT {cols_sql} FROM [{self.table}] WHERE {where_sql}"
        
        cur = self._cursor()
        row = cur.execute(sql, *key_values).fetchone()
        
        if not row:
            keys_display = ", ".join(f"{k}='{v}'" for k, v in zip(key_columns, key_values))
            raise LookupError(f"No existe registro con {keys_display} en tabla {self.table}")
        
        # Convertir a diccionario
        record = {}
        for i, col_name in enumerate(all_columns):
            value = row[i]
            # Normalizar valores None y espacios
            if value is None:
                record[col_name] = ""
            elif isinstance(value, str):
                record[col_name] = value.strip()
            else:
                record[col_name] = str(value)
        
        logger.info("Registro cargado: %d columnas", len(record))
        logger.debug("Columnas: %s", list(record.keys()))
        return record
