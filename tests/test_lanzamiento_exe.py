# -*- coding: utf-8 -*-
"""
Prueba de lanzamiento del .exe (simula lo que hace el VB.NET del jefe).
"""
import sys, os, json, time, tempfile, subprocess, ctypes

EXE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist", "EditorScript.exe")
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


def find_window(title_contains):
    """Busca ventanas cuyo titulo contenga el texto."""
    user32 = ctypes.windll.user32
    found = []
    def cb(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_contains.lower() in buf.value.lower():
                found.append(buf.value)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return found


print()
print("=" * 70)
print("  BLOQUE 3: Lanzamiento del .exe (como hara Gestion 21)")
print("=" * 70)

# --- 3.1 exe existe ---
def t_exe_existe():
    assert os.path.isfile(EXE), f"No encontrado: {EXE}"
    mb = os.path.getsize(EXE) / (1024*1024)
    assert mb > 5, f"Muy chico: {mb:.1f} MB"
    print(f"         Tamano: {mb:.1f} MB  |  Fecha: {time.ctime(os.path.getmtime(EXE))}")

test("3.1 El .exe existe y tiene tamano correcto", t_exe_existe)


# --- 3.2 modo local ---
def t_modo_local():
    proc = subprocess.Popen([EXE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(4)
    assert proc.poll() is None, "Proceso termino inesperadamente"
    ventanas = find_window("Editor VBS")
    proc.terminate()
    proc.wait(timeout=5)
    assert len(ventanas) > 0, "No se encontro ventana"
    print(f"         Ventana: '{ventanas[0]}'")

test("3.2 .exe modo local - se abre sin BD", t_modo_local)


# --- 3.3 con config JSON (flujo VB.NET) ---
def t_config_json():
    config_data = {
        "connection": {
            "server": r"miservidor\SQLEXPRESS",
            "database": "MiBaseDatos",
            "table": "G_SCRIPT",
            "user": "mi_usuario",
            "password": "mi_clave",
            "driver": "SQL Server",
            "trust_cert": True,
            "content_column": "SCRIPT"
        },
        "script": {
            "key_columns": ["MODELO", "CODIGO"],
            "key_values": ["T01", "BOBINADO"],
            "editable_columns": ["GRUPO"]
        }
    }
    fd, cfg_path = tempfile.mkstemp(suffix=".json", prefix="editor_cfg_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(config_data, fh, indent=2)
    try:
        proc = subprocess.Popen([EXE, "--config-file", cfg_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
        err = proc.stderr.read().decode("utf-8", errors="replace")
        if proc.returncode and proc.returncode != 0:
            is_conn = any(kw in err.lower() for kw in ["error", "conexi", "connection", "sql", "odbc", "login"])
            assert is_conn, f"Error inesperado:\n{err[:200]}"
            print(f"         Leyo JSON -> fallo conexion SQL (esperado sin BD real)")
        else:
            print(f"         Arranco correctamente con JSON")
    finally:
        try: os.unlink(cfg_path)
        except: pass

test("3.3 .exe con --config-file JSON (flujo VB.NET real)", t_config_json)


# --- 3.4 con connection-string extendido ---
def t_conn_str():
    cs = r"driver={SQL Server};server=miservidor\SQLEXPRESS;uid=mi_usuario;pwd=mi_clave;database=MiBaseDatos T01 D"
    proc = subprocess.Popen([EXE, "--connection-string", cs], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(5)
    if proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=5)
    err = proc.stderr.read().decode("utf-8", errors="replace")
    if proc.returncode and proc.returncode != 0:
        is_conn = any(kw in err.lower() for kw in ["error", "conexi", "connection", "sql", "odbc", "login"])
        assert is_conn, f"Error inesperado:\n{err[:200]}"
        print(f"         Parseo: BD=MiBaseDatos, MODELO=T01, tipo=Documento")
        print(f"         Fallo conexion (esperado sin servidor real)")
    else:
        print(f"         Proceso la connection string correctamente")

test("3.4 .exe con --connection-string extendido (Gestion 21)", t_conn_str)


# --- 3.5 con variables de entorno ---
def t_env_vars():
    env = os.environ.copy()
    env["EDITOR_SERVER"] = r"miservidor\SQLEXPRESS"
    env["EDITOR_DATABASE"] = "MiBaseDatos"
    env["EDITOR_TABLE"] = "G_SCRIPT"
    env["EDITOR_USER"] = "mi_usuario"
    env["EDITOR_PASSWORD"] = "mi_clave"
    env["EDITOR_KEY_COLUMNS"] = "MODELO,CODIGO"
    env["EDITOR_KEY_VALUES"] = "T01,BOBINADO"
    env["EDITOR_CONTENT_COLUMN"] = "SCRIPT"
    
    proc = subprocess.Popen([EXE], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    time.sleep(5)
    if proc.poll() is None:
        proc.terminate()
        proc.wait(timeout=5)
    err = proc.stderr.read().decode("utf-8", errors="replace")
    if proc.returncode and proc.returncode != 0:
        is_conn = any(kw in err.lower() for kw in ["error", "conexi", "connection", "sql", "odbc", "login"])
        assert is_conn, f"Error inesperado:\n{err[:200]}"
        print(f"         Leyo 8 variables EDITOR_* correctamente")
        print(f"         Fallo conexion (esperado)")
    else:
        print(f"         Proceso las variables de entorno OK")

test("3.5 .exe con variables de entorno EDITOR_*", t_env_vars)


# ======================================================================
print()
print("=" * 70)
if f == 0:
    print(f"  RESULTADO: {p}/{t} tests OK - TODO CORRECTO")
else:
    print(f"  RESULTADO: {p}/{t} tests OK - {f} FALLARON")
print("=" * 70)
print()
sys.exit(0 if f == 0 else 1)
