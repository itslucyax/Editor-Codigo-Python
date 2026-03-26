"""
Conexión dinamia a SQL Server para leer/guardar scripts.

Soporta:
- Conexión por parámetros individuales (server, database, user, password)
- Conexión por cadena de conexión completa (connection string)
- Detección automática de contexto: Plantilla vs. Documento
- Auto-detección de driver ODBC
"""

from __future__ import annotations

import logging
import re
from typing import Optional, List, Tuple, Dict

import pyodbc

logger = logging.getLogger("EditorVBS.db")

# Patrón para validar identificadores SQL Server (nombres de tabla/columna)
# Solo permite letras, números, guiones bajos, espacios y # (tablas temporales)
_VALID_SQL_IDENTIFIER = re.compile(r"^[\w\s#@$]+$", re.UNICODE)


def _sanitize_identifier(name: str, label: str = "identificador") -> str:
    """Valida que un nombre de tabla o columna sea seguro para usar en SQL.

    Solo permite caracteres alfanuméricos, guiones bajos, espacios, # y @.
    Rechaza cualquier cosa que pueda ser inyección SQL.

    Args:
        name: Nombre a validar (ej: 'G_SCRIPT', 'MODELO').
        label: Etiqueta para el mensaje de error (ej: 'tabla', 'columna').

    Returns:
        El mismo nombre si es válido.

    Raises:
        ValueError: Si el nombre contiene caracteres no permitidos.
    """
    if not name or not name.strip():
        raise ValueError(f"El {label} no puede estar vacío")
    if not _VALID_SQL_IDENTIFIER.match(name):
        raise ValueError(
            f"{label} '{name}' contiene caracteres no permitidos. "
            f"Solo se aceptan letras, números y guiones bajos."
        )
    return name

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


# ======================================================================
# Contextos de trabajo
# ======================================================================
CONTEXT_DOCUMENTO = "documento"
CONTEXT_PLANTILLA = "plantilla"

# Tablas por defecto según contexto (configurables)
DEFAULT_TABLES = {
    CONTEXT_DOCUMENTO: "G_SCRIPT",
    CONTEXT_PLANTILLA: "E_PROGRA",
}

# Mapeo de flags de tipo en la cadena de conexión extendida
# Gestión 21 usa: "database=MiBaseDatos T01 D" donde D=Documento, P=Plantilla
_TIPO_FLAG_MAP = {
    "D": CONTEXT_DOCUMENTO,
    "P": CONTEXT_PLANTILLA,
}


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


# ======================================================================
# Parser de cadena de conexión
# ======================================================================

# Mapeo de claves comunes en connection strings → nombres internos
_CONN_STR_KEY_MAP = {
    # Formato ODBC
    "DRIVER":                    "driver",
    "SERVER":                    "server",
    "DATABASE":                  "database",
    "UID":                       "user",
    "PWD":                       "password",
    "TRUSTSERVERCERTIFICATE":    "trust_server_certificate",
    # Formato ADO.NET
    "DATA SOURCE":               "server",
    "INITIAL CATALOG":           "database",
    "USER ID":                   "user",
    "PASSWORD":                  "password",
    # Variantes comunes
    "ADDR":                      "server",
    "ADDRESS":                   "server",
    "DB":                        "database",
    "USER":                      "user",
    "TRUSTED_CONNECTION":        "trusted_connection",
}


def parse_connection_string(conn_str: str) -> Dict[str, str]:
    """Parsea una cadena de conexión SQL Server y extrae sus componentes.

    Soporta formatos ODBC y ADO.NET, **incluyendo el formato extendido
    de Gestión 21** donde el valor de ``database`` incluye MODELO y tipo
    separados por espacios:

        Formato estándar:
            "Driver={SQL Server};Server=srv;Database=db;UID=u;PWD=p;"

        Formato extendido Gestión 21:
            "driver={SQL Server};server=miservidor\\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D"
            → database="MiBaseDatos", modelo="T01", tipo="documento" (D=Documento, P=Plantilla)

    Args:
        conn_str: Cadena de conexión completa.

    Returns:
        Diccionario con claves normalizadas::

            {
                "driver":   "SQL Server",
                "server":   "miservidor\\SQLEXPRESS",
                "database": "MiBaseDatos",
                "user":     "mi_usuario",
                "password": "mi_clave",
                # Solo presentes si la cadena usa formato extendido:
                "modelo":   "T01",
                "tipo":     "documento",    # (o "plantilla")
            }

    Raises:
        ValueError: Si la cadena está vacía o no tiene formato válido.
    """
    if not conn_str or not conn_str.strip():
        raise ValueError("La cadena de conexión está vacía")

    result: Dict[str, str] = {}

    # Separar por ';' respetando valores entre llaves {}
    # Ejemplo: Driver={ODBC Driver 18 for SQL Server};Server=srv
    parts = re.split(r";(?![^{}]*})", conn_str)

    for part in parts:
        part = part.strip()
        if not part or "=" not in part:
            continue

        # Separar en clave=valor (solo en el primer '=')
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Quitar llaves del valor si las tiene (ej: {ODBC Driver 18...})
        if value.startswith("{") and value.endswith("}"):
            value = value[1:-1]

        # Normalizar clave
        key_upper = key.upper()
        internal_key = _CONN_STR_KEY_MAP.get(key_upper, key.lower().replace(" ", "_"))

        result[internal_key] = value

    if not result:
        raise ValueError(
            f"No se pudieron extraer parámetros de la cadena de conexión.\n"
            f"Formato esperado: 'Server=srv;Database=db;UID=user;PWD=pass;'"
        )

    # ------------------------------------------------------------------
    # Detectar formato extendido de Gestión 21
    # El último token es SIEMPRE el flag: D=Documento, P=Plantilla.
    #
    # Formato DOCUMENTO (flag=D, mínimo 4 tokens):
    #   "datosABEL T01 BOBINADO D"         → db=datosABEL, modelo=T01, codigo=BOBINADO
    #   Los 3 últimos tokens son: MODELO CODIGO D
    #   Todo lo anterior es el nombre de la BD.
    #
    # Formato PLANTILLA (flag=P, mínimo 3 tokens, puede tener más):
    #   "dato01ABEL A P"                   → db=dato01ABEL, modelo=A
    #   "datosABEL O01 APLICACION P"       → db=datosABEL, modelo=O01  (APLICACION se ignora)
    #   Siempre: primer token=BD, segundo token=MODELO, resto hasta P se ignora.
    # ------------------------------------------------------------------
    db_raw = result.get("database", "")
    tokens = db_raw.split()
    if len(tokens) >= 3:
        flag = tokens[-1].upper()
        if flag in _TIPO_FLAG_MAP:
            if flag == "P":
                # Plantilla: primer token=BD, segundo token=MODELO, resto ignorado
                result["database"] = tokens[0]
                result["modelo"]   = tokens[1]
                result["codigo"]   = None
                result["tipo"]     = CONTEXT_PLANTILLA
                ignored = tokens[2:-1]
                logger.info(
                    "Formato plantilla detectado: db=%s, plantilla=%s%s",
                    result["database"], result["modelo"],
                    f" (tokens ignorados: {ignored})" if ignored else "",
                )
            else:
                # Documento (flag=D): los 3 últimos son MODELO CODIGO D
                result["database"] = " ".join(tokens[:-3])
                result["modelo"]   = tokens[-3]
                result["codigo"]   = tokens[-2]
                result["tipo"]     = CONTEXT_DOCUMENTO
                logger.info(
                    "Formato documento detectado: db=%s, modelo=%s, codigo=%s",
                    result["database"], result["modelo"], result["codigo"],
                )

    # Normalizar trust_server_certificate a booleano-string
    if "trust_server_certificate" in result:
        val = result["trust_server_certificate"].lower()
        result["trust_server_certificate"] = val in ("yes", "true", "1")
    else:
        result["trust_server_certificate"] = True  # default seguro

    logger.info(
        "Connection string parseada: server=%s, database=%s, user=%s",
        result.get("server", "N/A"),
        result.get("database", "N/A"),
        result.get("user", "N/A"),
    )
    return result


def resolve_table_for_context(
    context_type: str,
    table_override: Optional[str] = None,
    table_map: Optional[Dict[str, str]] = None,
) -> str:
    """Determina la tabla correcta según el contexto de trabajo.

    Args:
        context_type: 'documento' o 'plantilla'.
        table_override: Si se proporciona, se usa directamente (ignora contexto).
        table_map: Mapeo personalizado {contexto: tabla}. Si no se da, usa DEFAULT_TABLES.

    Returns:
        Nombre de la tabla a usar.

    Raises:
        ValueError: Si el contexto no es válido.
    """
    if table_override:
        logger.info("Tabla forzada por parámetro: %s", table_override)
        return table_override

    ctx = context_type.lower().strip()
    mapping = table_map or DEFAULT_TABLES

    if ctx not in mapping:
        valid = ", ".join(mapping.keys())
        raise ValueError(
            f"Contexto '{context_type}' no válido. Valores permitidos: {valid}"
        )

    table = mapping[ctx]
    logger.info("Tabla resuelta por contexto '%s': %s", ctx, table)
    return table


class DatabaseConnection:
    """
    Conecta con SQL Server usando pyodbc y permite leer/guardar scripts.

    Soporta dos modos de construcción:
    1. Parámetros individuales: DatabaseConnection(server=..., database=..., ...)
    2. Cadena de conexión:      DatabaseConnection.from_connection_string(conn_str, ...)

    El contexto de trabajo (Plantilla/Documento) determina la tabla automáticamente.
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
        context_type: Optional[str] = None,
        modelo: Optional[str] = None,
        codigo: Optional[str] = None,
    ):
        self.server = server
        self.database = database
        self.table = table
        self.user = user
        self.password = password
        self.driver = driver
        self.trust_server_certificate = trust_server_certificate
        self.content_column = content_column
        self.context_type = context_type  # 'documento' | 'plantilla' | None
        self.modelo = modelo              # MODELO extraído de la cadena (o None)
        self.codigo = codigo              # CODIGO extraído de la cadena (o None)

        self._cnxn: Optional[pyodbc.Connection] = None

    # ------------------------------------------------------------------
    # Context manager: permite usar 'with DatabaseConnection(...) as db:'
    # ------------------------------------------------------------------

    def __enter__(self) -> "DatabaseConnection":
        """Abre la conexión al entrar en el bloque 'with'."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Cierra la conexión al salir del bloque 'with', haya error o no."""
        self.close()
        return False  # No suprimimos excepciones, se propagan normalmente

    # ------------------------------------------------------------------
    # Constructor alternativo: desde cadena de conexión
    # ------------------------------------------------------------------

    @classmethod
    def from_connection_string(
        cls,
        conn_str: str,
        context_type: str = CONTEXT_DOCUMENTO,
        table: Optional[str] = None,
        table_map: Optional[Dict[str, str]] = None,
        content_column: str = "SCRIPT",
    ) -> "DatabaseConnection":
        """Crea una instancia a partir de una cadena de conexión completa.

        Parsea la cadena, extrae cada componente y resuelve la tabla
        según el contexto de trabajo.

        Si la cadena usa el **formato extendido de Gestión 21**
        (``database=MiBaseDatos T01 D``), el tipo y el MODELO se detectan
        automáticamente y tienen prioridad sobre el parámetro *context_type*.

        Args:
            conn_str: Cadena de conexión SQL Server.
                Estándar: ``"Driver={SQL Server};Server=srv;Database=db;UID=user;PWD=pass;"´´
                Extendida: ``"driver={SQL Server};server=miservidor\\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D"``
            context_type: 'documento' o 'plantilla'. Se usa solo si la cadena
                          **no** incluye el flag de tipo (D/P).
            table: Si se proporciona, sobrescribe la tabla resuelta por contexto.
            table_map: Mapeo personalizado {contexto: tabla}.
            content_column: Columna que contiene el script.

        Returns:
            Instancia de DatabaseConnection lista para llamar a connect().

        Raises:
            ValueError: Si la cadena no es válida o faltan datos mínimos.
        """
        params = parse_connection_string(conn_str)

        # Si el parser detectó formato extendido, usar tipo/modelo de la cadena
        effective_context = params.pop("tipo", None) or context_type
        modelo = params.pop("modelo", None)
        codigo = params.pop("codigo", None)

        # Resolución de la tabla por contexto
        resolved_table = resolve_table_for_context(
            effective_context, table_override=table, table_map=table_map
        )

        # Extraer driver, o auto-detectar
        driver = params.get("driver", None)
        if not driver:
            driver = detect_odbc_driver()

        # Validar datos mínimos
        server = params.get("server")
        database = params.get("database")
        user = params.get("user")
        password = params.get("password")

        if not server or not database:
            raise ValueError(
                "La cadena de conexión debe contener al menos Server y Database.\n"
                f"Datos extraídos: {params}"
            )

        trust = params.get("trust_server_certificate", True)

        logger.info(
            "DatabaseConnection creada desde connection string: "
            "server=%s, db=%s, tabla=%s (contexto=%s, modelo=%s)",
            server, database, resolved_table, effective_context,
            modelo or "N/A",
        )

        return cls(
            server=server,
            database=database,
            table=resolved_table,
            user=user,
            password=password,
            driver=driver,
            trust_server_certificate=trust,
            content_column=content_column,
            context_type=effective_context,
            modelo=modelo,
            codigo=codigo,
        )

    # ------------------------------------------------------------------
    # Utilidades de contexto
    # ------------------------------------------------------------------

    @property
    def is_plantilla(self) -> bool:
        """True si el contexto actual es Plantilla."""
        return self.context_type == CONTEXT_PLANTILLA

    @property
    def is_documento(self) -> bool:
        """True si el contexto actual es Documento."""
        return self.context_type == CONTEXT_DOCUMENTO

    def switch_context(self, new_context: str, table_map: Optional[Dict[str, str]] = None) -> None:
        """Cambia el contexto de trabajo y actualiza la tabla.

        Args:
            new_context: 'documento' o 'plantilla'.
            table_map: Mapeo personalizado. Si no se da, usa DEFAULT_TABLES.
        """
        old = self.context_type
        self.context_type = new_context.lower().strip()
        self.table = resolve_table_for_context(self.context_type, table_map=table_map)
        logger.info("Contexto cambiado: %s → %s (tabla: %s)", old, self.context_type, self.table)

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

    def search_text_in_document(self, query_text: str, key_columns: list, key_values:list) -> list[dict]:
        """
        Busca una cadena de texto en todos los scripts que pertenecen al mismo documento
        """
        if not query_text:
            return []
        
        safe_table = self._safe_table()
        content_col = self._self_column(self.content_column or "SCRIPT")
        
        #En G21 para buscar en el mismo documento, filtramos por la primera
        #columna de la clave
        doc_column = self._safe_column(key_columns[0])
        doc_value = key_values[0]
        
        sql = f"SELECT * FROM [{safe_table}] WHERE [{doc_column}] = ? AND [{content_col}] LIKE ?"
        
        cur = self._cursor()
        #Ell % es para que busque contiene no es igual a
        rows = cur.execute(sql, doc_value, f"%{query_text}%").fetchall()
        
        colunms = [column[0] for column in cur.description]
        return [dict(zip(colunms, row)) for row in rows]

    def _cursor(self) -> pyodbc.Cursor:
        if self._cnxn is None:
            raise RuntimeError("No hay conexión abierta. Llama a connect() primero.")
        return self._cnxn.cursor()

    # ------------------------------------------------------------------
    # Sanitización de identificadores SQL
    # ------------------------------------------------------------------

    def _safe_table(self) -> str:
        """Devuelve el nombre de tabla validado para uso en SQL."""
        return _sanitize_identifier(self.table, "tabla")

    def _safe_column(self, col: str) -> str:
        """Devuelve un nombre de columna validado para uso en SQL."""
        return _sanitize_identifier(col, "columna")

    def save_record_full(
        self, 
        key_columns: List[str],
        key_values: List[str],
        updated_fields: dict
    ) -> bool:
        """
        Guarda cambios en un registro de forma dinamia.
        
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
        
        # Sanitizar todos los nombres de columna antes de construir el SQL
        safe_table = self._safe_table()
        
        # Construir SET clause (con columnas validadas)
        set_parts = [f"[{self._safe_column(col)}] = ?" for col in updated_fields.keys()]
        set_clause = ", ".join(set_parts)
        
        # Construir WHERE clause (con columnas validadas)
        where_parts = [f"[{self._safe_column(col)}] = ?" for col in key_columns]
        where_clause = " AND ".join(where_parts)
        
        sql = f"UPDATE [{safe_table}] SET {set_clause} WHERE {where_clause}"
        
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
        return updated >= 1

    # ------------------------------------------------------------------
    # Listado dinámico de scripts (para el desplegable)
    # ------------------------------------------------------------------

    def get_scripts_for_model(
        self,
        key_columns: List[str],
        key_values: List[str],
        group_by_column: str = None,
    ) -> List[dict]:
        """
        Obtiene todos los scripts que comparten parte de la clave primaria.
        
        Para el desplegable del editor: dado un MODELO, devuelve todos los
        CODIGOS disponibles con su contenido.
        
        Si key_columns=["MODELO","CODIGO"] y key_values=["T01","BOBINADO"],
        busca todos los registros que coincidan con la PRIMERA clave (MODELO=T01),
        devolviendo cada uno con su CODIGO y SCRIPT.
        
        Args:
            key_columns: Lista completa de columnas clave (ej: ["MODELO", "CODIGO"])
            key_values: Lista completa de valores (ej: ["T01", "BOBINADO"])
            group_by_column: Columna por la que agrupar (default: primera de key_columns)
            
        Returns:
            Lista de dicts: [{"label": "BOBINADO", "key_values": ["T01","BOBINADO"], 
                              "content": "Sub Main()..."}]
        """
        if not key_columns or len(key_columns) < 2:
            logger.info("get_scripts_for_model: clave simple, no hay lista de scripts")
            return []
        
        cur = self._cursor()
        
        # Filtrar por la primera columna clave (ej: MODELO)
        filter_col = key_columns[0]
        filter_val = key_values[0]
        
        # La segunda columna clave es la que varía (ej: CODIGO)
        label_col = key_columns[1] if len(key_columns) > 1 else key_columns[0]
        
        # Columnas a traer: todas las claves + contenido
        select_cols = list(key_columns) + [self.content_column]
        # Eliminar duplicados manteniendo orden
        select_cols = list(dict.fromkeys(select_cols))
        
        # Sanitizar todos los identificadores
        safe_table = self._safe_table()
        cols_sql = ", ".join(f"[{self._safe_column(c)}]" for c in select_cols)
        safe_filter = self._safe_column(filter_col)
        safe_label = self._safe_column(label_col)
        sql = f"SELECT {cols_sql} FROM [{safe_table}] WHERE [{safe_filter}] = ? ORDER BY [{safe_label}]"
        
        logger.debug("get_scripts_for_model SQL: %s (val=%s)", sql, filter_val)
        
        try:
            rows = cur.execute(sql, filter_val).fetchall()
        except Exception as e:
            logger.warning("Error al obtener lista de scripts: %s", e)
            return []
        
        scripts = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(select_cols):
                val = row[i]
                row_dict[col] = "" if val is None else str(val).strip()
            
            # Construir label legible (valor de la segunda clave)
            label = row_dict.get(label_col, "")
            content = row_dict.get(self.content_column, "")
            row_key_values = [row_dict.get(k, "") for k in key_columns]
            
            scripts.append({
                "label": label,
                "content": content,
                "key_values": row_key_values,
            })
        
        logger.info("get_scripts_for_model: %d scripts encontrados para %s=%s",
                    len(scripts), filter_col, filter_val)
        return scripts

    # ------------------------------------------------------------------
    # Listado de plantillas (para el desplegable en modo plantilla)
    # ------------------------------------------------------------------

    def get_all_plantillas(
        self,
        tabla_listado: str = "E_PLANTI",
        col_clave: str = "PLANTILLA",
        col_descri: str = "DESCRI",
        tabla_contenido: str = "E_PROGRA",
        col_contenido: str = "TEXTO",
    ) -> List[dict]:
        """
        Obtiene todas las plantillas disponibles para el desplegable.

        Consulta E_PLANTI (listado) y une con E_PROGRA (contenido) para
        devolver el label 'PLANTILLA - DESCRI' y el texto de cada plantilla.

        Args:
            tabla_listado:   Tabla con el catálogo de plantillas (E_PLANTI).
            col_clave:       Columna clave en ambas tablas (PLANTILLA).
            col_descri:      Columna descripción en la tabla listado (DESCRI).
            tabla_contenido: Tabla con el texto de la plantilla (E_PROGRA).
            col_contenido:   Columna con el texto (TEXTO).

        Returns:
            Lista de dicts:
            [{"label": "A - Copia estándar", "key_values": ["A"], "content": "..."}]
        """
        cur = self._cursor()

        safe_tl  = _sanitize_identifier(tabla_listado,   "tabla_listado")
        safe_tc  = _sanitize_identifier(tabla_contenido, "tabla_contenido")
        safe_ck  = _sanitize_identifier(col_clave,       "col_clave")
        safe_cd  = _sanitize_identifier(col_descri,      "col_descri")
        safe_cnt = _sanitize_identifier(col_contenido,   "col_contenido")

        sql = f"""
            SELECT [{safe_ck}], MAX([{safe_cd}]) AS [{safe_cd}]
            FROM [{safe_tl}]
            WHERE [{safe_cd}] IS NOT NULL AND [{safe_cd}] <> ''
            GROUP BY [{safe_ck}]
            ORDER BY [{safe_ck}]
        """
        logger.debug("get_all_plantillas SQL: %s", sql.strip())

        try:
            rows = cur.execute(sql).fetchall()
        except Exception as e:
            logger.warning("Error al obtener lista de plantillas: %s", e)
            return []

        plantillas = []
        for row in rows:
            clave   = "" if row[0] is None else str(row[0]).strip()
            descri  = "" if row[1] is None else str(row[1]).strip()

            #Si no tiene descri, esta sin usar -> no mostrar en el desplegable --> solucionado en connection.py cambiando de Left Join a INNER JOIN (mas limpio)
            #if not descri or not descri.strip():
                #continue
            
            label = f"{clave} - {descri}"

            plantillas.append({
                "label":      label,
                "key_values": [clave],
                "content":    "", #Se carga al seleccionar
            })

        logger.info("get_all_plantillas: %d plantillas encontradas", len(plantillas))
        return plantillas


    # ------------------------------------------------------------------

    def get_variables(self, modelo: str, codigo: str,
                      var_columns: Optional[List[str]] = None) -> Tuple[List[str], str]:
        """Lee las columnas TABLACAMPO0-9 y GRUPO de la fila del script.

        Args:
            modelo: Valor de la columna MODELO.
            codigo: Valor de la columna CODIGO.
            var_columns: Lista de nombres de columna a leer.
                         Por defecto ["TABLACAMPO0", ..., "TABLACAMPO9"].

        Returns:
            Tupla (lista de 10 strings con valores de las variables,
            string con el valor de GRUPO). Valores None se convierten a "".

        Raises:
            LookupError: Si no existe la fila.
        """
        if var_columns is None:
            var_columns = [f"TABLACAMPO{i}" for i in range(10)]

        # Añadir GRUPO a la consulta
        all_columns = var_columns + ["GRUPO"]

        # Filtrar columnas que realmente existen en la tabla
        existing = self._existing_columns(all_columns)
        if not existing:
            logger.warning("Ninguna de las columnas %s existe en %s",
                           all_columns, self.table)
            return (["" for _ in var_columns], "")

        safe_table = self._safe_table()
        cols_sql = ", ".join(f"[{self._safe_column(c)}]" for c in existing)
        sql = f"""
        SELECT {cols_sql}
        FROM [{safe_table}]
        WHERE [MODELO] = ? AND [CODIGO] = ?
        """
        cur = self._cursor()
        row = cur.execute(sql, modelo, codigo).fetchone()

        if not row:
            raise LookupError(
                f"No existe registro para MODELO='{modelo}' CODIGO='{codigo}'"
            )

        # Extraer valores en un dict temporal
        values = {}
        for i, col_name in enumerate(existing):
            val = "" if row[i] is None else str(row[i]).strip()
            values[col_name] = val

        # Construir lista de 10 variables en orden
        variables = [values.get(c, "") for c in var_columns]
        grupo = values.get("GRUPO", "")

        logger.debug("get_variables: vars=%s, grupo=%s", variables, grupo)
        return (variables, grupo)

    def _existing_columns(self, candidates: List[str]) -> List[str]:
        """Devuelve solo los nombres de columna que existen en la tabla."""
        cur = self._cursor()
        sql = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        """
        rows = cur.execute(sql, self._safe_table()).fetchall()
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
        rows = cur.execute(sql, self._safe_table()).fetchall()
        
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
        Carga un registro completo con TODAS sus columnas de forma dinamica.
        
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
        
        #Obtener todas las columnas de la tabla
        schema = self.get_table_schema()
        all_columns = [col["name"] for col in schema]
        
        #Construir SELECT dinamicamente
        safe_table = self._safe_table()
        cols_sql = ", ".join(f"[{self._safe_column(col)}]" for col in all_columns)
        
        #Construir WHERE dinamicamente
        where_parts = [f"[{self._safe_column(col)}] = ?" for col in key_columns]
        where_sql = " AND ".join(where_parts)
        
        sql = f"SELECT {cols_sql} FROM [{safe_table}] WHERE {where_sql}"
        
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