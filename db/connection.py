"""
Conexión a SQL Server para leer/guardar scripts en la tabla G_SCRIPT.

Autenticación: SQL Authentication (usuario/contraseña)
Clave compuesta: MODELO (nvarchar(3)) + CODIGO (nvarchar(20))
Columna de contenido: configurable via --content-column
"""

from __future__ import annotations

from typing import Optional

import pyodbc


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
        Lanza ValueError si faltan credenciales.
        Lanza pyodbc.Error si falla la conexión.
        """
        if not self.user or not self.password:
            raise ValueError("Para SQL Authentication necesitas --user y --password")

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
        
        try:
            self._cnxn = pyodbc.connect(conn_str, autocommit=False)
        except pyodbc.Error as e:
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
        return updated == 1