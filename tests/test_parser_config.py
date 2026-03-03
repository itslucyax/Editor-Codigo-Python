# -*- coding: utf-8 -*-
"""
Prueba rapida de parser + config (sin GUI, sin .exe).
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import parse_connection_string
from config_loader import ConfigLoader

t = p = f = 0

def test(name, fn):
    global t, p, f
    t += 1
    try:
        fn()
        p += 1
        print(f"  [OK]   {name}")
    except Exception as e:
        f += 1
        print(f"  [FAIL] {name} -> {e}")

print()
print("=" * 70)
print("  BLOQUE 1: Parser de cadena de conexion")
print("=" * 70)

def t1():
    r = parse_connection_string(r"Driver={SQL Server};Server=miservidor\SQLEXPRESS;Database=MiBaseDatos;UID=mi_usuario;PWD=mi_clave;")
    assert r["server"] == r"miservidor\SQLEXPRESS"
    assert r["database"] == "MiBaseDatos"
    assert r["user"] == "mi_usuario"
    assert "modelo" not in r

test("1.1 Formato ODBC estandar", t1)

def t2():
    r = parse_connection_string(r"driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D")
    assert r["database"] == "MiBaseDatos"
    assert r["modelo"] == "T01"
    assert r["tipo"] == "documento"

test("1.2 Formato extendido Gestion 21 - Documento", t2)

def t3():
    r = parse_connection_string(r"driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos A P")
    assert r["database"] == "MiBaseDatos"
    assert r["modelo"] == "A"
    assert r["tipo"] == "plantilla"

test("1.3 Formato extendido Gestion 21 - Plantilla", t3)

def t4():
    r = parse_connection_string("Driver={ODBC Driver 18 for SQL Server};Server=srv;Database=db;UID=u;PWD=p;TrustServerCertificate=Yes;")
    assert r["driver"] == "ODBC Driver 18 for SQL Server"
    assert r["trust_server_certificate"] == True

test("1.4 Driver ODBC 18 + TrustServerCertificate", t4)

def t5():
    r = parse_connection_string("Data Source=servidor;Initial Catalog=MiBD;User ID=admin;Password=secreto;")
    assert r["server"] == "servidor"
    assert r["database"] == "MiBD"
    assert r["user"] == "admin"

test("1.5 Formato ADO.NET", t5)

def t6():
    try:
        parse_connection_string("")
        assert False
    except ValueError:
        pass

test("1.6 Rechaza cadena vacia", t6)

def t7():
    try:
        parse_connection_string("esto no es valido")
        assert False
    except ValueError:
        pass

test("1.7 Rechaza cadena invalida", t7)

print()
print("=" * 70)
print("  BLOQUE 2: ConfigLoader multi-fuente")
print("=" * 70)

def t8():
    cfg = {
        "connection": {"server": r"miservidor\SQLEXPRESS", "database": "MiBaseDatos", "user": "u", "password": "p"},
        "script": {"key_columns": ["MODELO", "CODIGO"], "key_values": ["T01", "BOBINADO"]}
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(cfg, fh)
    try:
        loader = ConfigLoader()
        loader.load_from_file(path)
        m = loader.merge({})
        assert m["server"] == r"miservidor\SQLEXPRESS"
        assert m["key_columns"] == ["MODELO", "CODIGO"]
    finally:
        os.unlink(path)

test("2.1 ConfigLoader desde JSON", t8)

def t9():
    old = {}
    for k, v in {"EDITOR_SERVER": "srv", "EDITOR_DATABASE": "db", "EDITOR_USER": "u", "EDITOR_PASSWORD": "p"}.items():
        old[k] = os.environ.get(k)
        os.environ[k] = v
    try:
        loader = ConfigLoader()
        loader.load_from_env()
        m = loader.merge({})
        assert m["server"] == "srv"
        assert m["database"] == "db"
    finally:
        for k, o in old.items():
            if o is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = o

test("2.2 ConfigLoader desde variables de entorno", t9)

def t10():
    cfg = {
        "connection": {"server": "srv_json", "database": "db_json", "user": "u", "password": "p"},
        "script": {"key_columns": ["M"], "key_values": ["A"]}
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(cfg, fh)
    try:
        loader = ConfigLoader()
        loader.load_from_file(path)
        m = loader.merge({"server": "srv_cli"})
        assert m["server"] == "srv_cli", "CLI debe ganar"
        assert m["database"] == "db_json", "JSON se mantiene"
    finally:
        os.unlink(path)

test("2.3 Prioridad CLI > JSON", t10)

print()
print("=" * 70)
if f == 0:
    print(f"  RESULTADO: {p}/{t} tests OK - TODO CORRECTO")
else:
    print(f"  RESULTADO: {p}/{t} tests OK - {f} FALLARON")
print("=" * 70)
print()
sys.exit(0 if f == 0 else 1)
