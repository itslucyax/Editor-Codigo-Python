# -*- coding: utf-8 -*-
"""
Validador de sintaxis VBScript/VB.

Comprueba errores comunes antes de guardar:
- Script vacío
- Bloques sin cerrar (Sub/End Sub, Function/End Function, If/End If, etc.)
- Paréntesis desbalanceados
- Comillas sin cerrar en una línea
- Líneas extremadamente largas (posible error de pegado)
"""

import re
from typing import List, Tuple


# Pares de apertura/cierre en VBScript (case-insensitive)
# Cada tupla: (regex_apertura, regex_cierre, nombre_legible)
BLOCK_PAIRS = [
    (r"^\s*Sub\b",               r"^\s*End\s+Sub\b",        "Sub / End Sub"),
    (r"^\s*Function\b",          r"^\s*End\s+Function\b",   "Function / End Function"),
    (r"^\s*If\b.*\bThen\s*$",    r"^\s*End\s+If\b",         "If / End If"),
    (r"^\s*For\b",               r"^\s*Next\b",             "For / Next"),
    (r"^\s*Do\b",                r"^\s*Loop\b",             "Do / Loop"),
    (r"^\s*While\b",             r"^\s*Wend\b",             "While / Wend"),
    (r"^\s*Select\s+Case\b",     r"^\s*End\s+Select\b",     "Select Case / End Select"),
    (r"^\s*With\b",              r"^\s*End\s+With\b",       "With / End With"),
    (r"^\s*Class\b",             r"^\s*End\s+Class\b",      "Class / End Class"),
    (r"^\s*Property\b",          r"^\s*End\s+Property\b",   "Property / End Property"),
]


def _strip_comments(line: str) -> str:
    """Elimina comentarios de una línea VBS (todo lo que va después de ')."""
    in_string = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_string = not in_string
        elif ch == "'" and not in_string:
            return line[:i]
    return line


def _is_comment_line(line: str) -> bool:
    """Comprueba si una línea es enteramente un comentario."""
    stripped = line.strip()
    return stripped.startswith("'") or stripped.upper().startswith("REM ")


def validate_vbs(code: str) -> List[Tuple[str, str, int]]:
    """
    Valida código VBScript y devuelve una lista de problemas encontrados.
    
    Cada problema es una tupla: (nivel, mensaje, línea)
      - nivel: "error" | "aviso"
      - mensaje: Descripción del problema
      - línea: Número de línea (1-based), 0 si es global
    
    Returns:
        Lista de problemas encontrados (vacía si todo está bien).
    """
    problemas: List[Tuple[str, str, int]] = []
    
    if not code or not code.strip():
        problemas.append(("error", "El script está vacío", 0))
        return problemas
    
    lines = code.splitlines()
    
    # 1) Comprobar bloques abiertos/cerrados
    _check_blocks(lines, problemas)
    
    # 2) Comprobar comillas sin cerrar
    _check_quotes(lines, problemas)
    
    # 3) Comprobar paréntesis desbalanceados
    _check_parentheses(lines, problemas)
    
    # 4) Comprobar líneas muy largas
    _check_long_lines(lines, problemas)
    
    return problemas


def _check_blocks(lines: List[str], problemas: List):
    """Comprueba que cada bloque abierto tenga su cierre correspondiente."""
    for regex_open, regex_close, name in BLOCK_PAIRS:
        open_count = 0
        open_lines = []
        
        for i, line in enumerate(lines, start=1):
            if _is_comment_line(line):
                continue
            
            clean = _strip_comments(line)
            
            if re.search(regex_open, clean, re.IGNORECASE):
                open_count += 1
                open_lines.append(i)
            if re.search(regex_close, clean, re.IGNORECASE):
                open_count -= 1
                if open_lines:
                    open_lines.pop()
        
        if open_count > 0:
            linea_ref = open_lines[0] if open_lines else 0
            problemas.append((
                "error",
                f"Bloque sin cerrar: {name} "
                f"({open_count} apertura{'s' if open_count > 1 else ''} sin cierre)",
                linea_ref
            ))
        elif open_count < 0:
            #Cierre sin apertura ignorado - Patron valido en G21
            pass
            #Ignora "End Sub" suelto al inicio - Patron valido para G21
            """
            if name == "Sub / End Sub":
                pass
            else:
                problemas.append((
                    "aviso",
                    f"Cierre extra: {name} "
                    f"({abs(open_count)} cierre{'s' if abs(open_count) > 1 else ''} sin apertura)",
                    0
                ))
            """

def _check_quotes(lines: List[str], problemas: List):
    """Comprueba comillas dobles sin cerrar en cada línea."""
    for i, line in enumerate(lines, start=1):
        if _is_comment_line(line):
            continue
        
        clean = _strip_comments(line)
        
        # Contar comillas dobles — si es impar, hay una sin cerrar
        count = clean.count('"')
        if count % 2 != 0:
            problemas.append((
                "error",
                f"Comillas sin cerrar en esta línea",
                i
            ))


def _check_parentheses(lines: List[str], problemas: List):
    """Comprueba paréntesis desbalanceados globalmente."""
    total_open = 0
    
    for i, line in enumerate(lines, start=1):
        if _is_comment_line(line):
            continue
        
        clean = _strip_comments(line)
        
        # Excluir contenido dentro de strings
        in_string = False
        line_balance = 0
        for ch in clean:
            if ch == '"':
                in_string = not in_string
            elif not in_string:
                if ch == '(':
                    line_balance += 1
                elif ch == ')':
                    line_balance -= 1
        
        total_open += line_balance
        
        # Si el balance acumulado es negativo, hay un ) de más
        if total_open < 0:
            problemas.append((
                "aviso",
                f"Paréntesis de cierre ')' sin apertura correspondiente",
                i
            ))
            total_open = 0  # Reset para no repetir el aviso
    
    if total_open > 0:
        problemas.append((
            "aviso",
            f"Hay {total_open} paréntesis '(' sin cerrar en el script",
            0
        ))


def _check_long_lines(lines: List[str], problemas: List, max_length: int = 1000):
    """Avisa sobre líneas extremadamente largas."""
    for i, line in enumerate(lines, start=1):
        if len(line) > max_length:
            problemas.append((
                "aviso",
                f"Línea muy larga ({len(line)} caracteres). ¿Posible error de pegado?",
                i
            ))


def format_problemas(problemas: List[Tuple[str, str, int]]) -> str:
    """
    Formatea la lista de problemas en un texto legible para mostrar en un diálogo.
    
    Returns:
        Texto formateado con los problemas.
    """
    if not problemas:
        return ""
    
    errores = [p for p in problemas if p[0] == "error"]
    avisos = [p for p in problemas if p[0] == "aviso"]
    
    parts = []
    
    if errores:
        parts.append(f"  ERRORES ({len(errores)}):")
        for _, msg, linea in errores:
            loc = f" (línea {linea})" if linea > 0 else ""
            parts.append(f"    ✗ {msg}{loc}")
    
    if avisos:
        parts.append(f"\n  AVISOS ({len(avisos)}):")
        for _, msg, linea in avisos:
            loc = f" (línea {linea})" if linea > 0 else ""
            parts.append(f"    ⚠ {msg}{loc}")
    
    return "\n".join(parts)
