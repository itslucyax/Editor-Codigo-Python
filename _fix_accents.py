# Script temporal para quitar acentos de comentarios y docstrings
import os

ACCENT_MAP = str.maketrans('áéíóúñüÁÉÍÓÚÑÜ', 'aeiounuAEIOUNU')

def remove_accents(s):
    return s.translate(ACCENT_MAP)

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    in_docstring = False
    docstring_char = None
    
    for line in lines:
        stripped = line.lstrip()
        
        if in_docstring:
            new_lines.append(remove_accents(line))
            if docstring_char in stripped and not stripped.startswith(docstring_char):
                in_docstring = False
            elif stripped == docstring_char or stripped.endswith(docstring_char):
                in_docstring = False
            continue
        
        # Detectar inicio de docstring
        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_char = stripped[:3]
            rest = stripped[3:]
            if docstring_char in rest:
                # Single-line docstring
                new_lines.append(remove_accents(line))
            else:
                in_docstring = True
                new_lines.append(remove_accents(line))
            continue
        
        # Detectar comentarios # (solo la parte del comentario)
        if '#' in line:
            in_str = None
            comment_pos = -1
            for i, ch in enumerate(line):
                if ch in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                    if in_str is None:
                        in_str = ch
                    elif ch == in_str:
                        in_str = None
                elif ch == '#' and in_str is None:
                    comment_pos = i
                    break
            
            if comment_pos >= 0:
                code_part = line[:comment_pos]
                comment_part = line[comment_pos:]
                new_lines.append(code_part + remove_accents(comment_part))
                continue
        
        new_lines.append(line)
    
    result = '\n'.join(new_lines)
    if result != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result)
        return True
    return False

root = r'c:\Users\lucia\OneDrive\Escritorio\Editor-Codigo-Python'
py_files = []
for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = [d for d in dirnames if d != '__pycache__']
    for fn in filenames:
        if fn.endswith('.py'):
            py_files.append(os.path.join(dirpath, fn))

changed = 0
for f in sorted(py_files):
    if process_file(f):
        rel = os.path.relpath(f, root)
        print(f'  Modificado: {rel}')
        changed += 1

print(f'\nTotal: {changed} archivos modificados')
