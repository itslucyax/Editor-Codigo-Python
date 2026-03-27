# -*- coding: utf-8 -*-
from __future__ import annotations
import logging
import re
from typing import Optional, List, Tuple, Dict
import pyodbc

logger = logging.getLogger("EditorVBS.db")

# --- FUNCIONES AUXILIARES ---
_VALID_SQL_IDENTIFIER = re.compile(r"^[\w\s#@$]+$", re.UNICODE)

def _sanitize_identifier(name: str, label: str = "identificador") -> str:
    if not name or not name.strip(): raise ValueError(f"El {label} no puede estar vacío")
    if not _VALID_SQL_IDENTIFIER.match(name): raise ValueError(f"{label} '{name}' no válido.")
    return name

_PREFERRED_DRIVERS = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
CONTEXT_DOCUMENTO, CONTEXT_PLANTILLA = "documento", "plantilla"
DEFAULT_TABLES = {CONTEXT_DOCUMENTO: "G_SCRIPT", CONTEXT_PLANTILLA: "E_PROGRA"}
_TIPO_FLAG_MAP = {"D": CONTEXT_DOCUMENTO, "P": CONTEXT_PLANTILLA}

def detect_odbc_driver() -> str:
    installed = pyodbc.drivers()
    for drv in _PREFERRED_DRIVERS:
        if drv in installed: return drv
    return "SQL Server"

def resolve_table_for_context(context_type: str, table_override: Optional[str] = None, table_map: Optional[Dict[str, str]] = None) -> str:
    if table_override: return table_override
    ctx = context_type.lower().strip()
    mapping = table_map or DEFAULT_TABLES
    return mapping.get(ctx, "G_SCRIPT")

def parse_connection_string(conn_str: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    parts = re.split(r";(?![^{}]*})", conn_str)
    for part in parts:
        if "=" not in part: continue
        key, value = part.split("=", 1)
        key, value = key.strip().upper(), value.strip()
        if value.startswith("{") and value.endswith("}"): value = value[1:-1]
        result[key.lower().replace(" ", "_")] = value
    
    db_raw = result.get("database", "")
    tokens = db_raw.split()
    if len(tokens) >= 3 and tokens[-1].upper() in _TIPO_FLAG_MAP:
        flag = tokens[-1].upper()
        if flag == "P":
            result["database"], result["modelo"], result["tipo"] = tokens[0], tokens[1], CONTEXT_PLANTILLA
        else:
            result["database"], result["modelo"], result["codigo"], result["tipo"] = " ".join(tokens[:-3]), tokens[-3], tokens[-2], CONTEXT_DOCUMENTO
    return result

# --- CLASE PRINCIPAL ---
class DatabaseConnection:
    def __init__(self, server, database, table="G_SCRIPT", user=None, password=None, driver=None, 
                 trust_server_certificate=True, content_column="SCRIPT", context_type=None, modelo=None, codigo=None):
        self.server, self.database, self.table = server, database, table
        self.user, self.password, self.driver = user, password, driver or "SQL Server"
        self.trust_server_certificate, self.content_column = trust_server_certificate, content_column
        self.context_type, self.modelo, self.codigo = context_type, modelo, codigo
        self._cnxn = None

    @classmethod
    def from_connection_string(cls, conn_str, context_type=CONTEXT_DOCUMENTO, **kwargs):
        p = parse_connection_string(conn_str)
        t = resolve_table_for_context(p.get("tipo", context_type), table_override=kwargs.get("table"))
        return cls(server=p.get("server") or p.get("data_source"), database=p.get("database"),
                   table=t, user=p.get("uid") or p.get("user_id"), password=p.get("pwd") or p.get("password"),
                   driver=p.get("driver", detect_odbc_driver()), context_type=p.get("tipo", context_type),
                   modelo=p.get("modelo"), codigo=p.get("codigo"))

    def connect(self):
        c = [f"DRIVER={{{self.driver}}}", f"SERVER={self.server}", f"DATABASE={self.database}", f"UID={self.user}", f"PWD={self.password}"]
        if self.trust_server_certificate: c.append("TrustServerCertificate=yes")
        self._cnxn = pyodbc.connect(";".join(c) + ";", autocommit=True)

    def close(self):
        if self._cnxn: self._cnxn.close()

    def _cursor(self):
        if not self._cnxn: self.connect()
        return self._cnxn.cursor()

    def get_table_schema(self) -> List[Dict[str, str]]:
        """Devuelve lista de dicts con 'name' como espera main.py"""
        cur = self._cursor()
        cur.execute(f"SELECT TOP 0 * FROM [{self.table}]")
        return [{"name": col[0]} for col in cur.description]

    def get_record_full(self, key_columns, key_values):
        """Versión fija: usa un solo cursor para evitar el error de NoneType"""
        where = " AND ".join([f"[{c}] = ?" for c in key_columns])
        cur = self._cursor()
        row = cur.execute(f"SELECT * FROM [{self.table}] WHERE {where}", key_values).fetchone()
        if row and cur.description:
            cols = [col[0] for col in cur.description]
            return dict(zip(cols, row))
        return None

    def get_scripts_for_model(self, key_columns, key_values, group_by_column=None):
        """Para el caso 'D' (G_SCRIPT)"""
        try:
            cur = self._cursor()
            # Si tenemos modelo y código en la cadena de conexión, intentamos traer ese grupo
            filter_val = key_values[0] if key_values else ""
            sql = f"SELECT * FROM [{self.table}] WHERE [{key_columns[0]}] = ?"
            rows = cur.execute(sql, filter_val).fetchall()
            cols = [c[0].upper() for c in cur.description]
            res = []
            for r in rows:
                d = dict(zip(cols, r))
                res.append({
                    "label": str(d.get("CODIGO", d.get(key_columns[-1].upper(), ""))).strip(),
                    "content": d.get("SCRIPT", d.get("PROGRA", "")),
                    "key_values": [str(d.get(k.upper(), "")) for k in key_columns]
                })
            return res
        except Exception as e:
            logger.error(f"Error en scripts: {e}")
            return []

    def get_all_plantillas(self):
        """
        Relaciona E_PLANTI (nombres) con E_PROGRA (scripts)
        Evita duplicados agrupando por la letra de la plantilla.
        """
        try:
            cur = self._cursor()
            # Hacemos un JOIN: 
            # E_PLANTI (PLANTILLA, DESCRI) -> E_PROGRA (PLANTILLA, TEXTO)
            sql = """
                SELECT 
                    P.PLANTILLA, 
                    MAX(P.DESCRI) as NOMBRE, 
                    MAX(G.TEXTO) as SCRIPT
                FROM E_PLANTI P
                LEFT JOIN E_PROGRA G ON P.PLANTILLA = G.PLANTILLA
                GROUP BY P.PLANTILLA
                ORDER BY P.PLANTILLA
            """
            cur.execute(sql)
            rows = cur.fetchall()
            res = []
            for r in rows:
                letra = str(r[0] or "").strip()
                nombre = str(r[1] or "").strip()
                contenido = r[2] or ""
                # El label será: "A - NOMBRE DE LA PLANTILLA"
                full_label = f"{letra} - {nombre}" if nombre else letra
                res.append({
                    "label": full_label,
                    "content": contenido,
                    "key_values": [letra] # La clave para buscar es la letra
                })
            logger.info(f"Cargadas {len(res)} plantillas únicas con JOIN.")
            return res
        except Exception as e:
            logger.error(f"Error en JOIN de plantillas: {e}")
            return []

    def get_scripts_for_search(self):
        try:
            return self._cursor().execute(f"SELECT CODIGO, SCRIPT FROM [{self.table}] WHERE MODELO = ?", [self.modelo]).fetchall()
        except: return []

    def get_acum_fields(self):
        try:
            return self._cursor().execute("SELECT ACUM, DESCRI FROM E_ACUM ORDER BY ACUM").fetchall()
        except: return []

    def __enter__(self): self.connect(); return self
    def __exit__(self, *args): self.close()