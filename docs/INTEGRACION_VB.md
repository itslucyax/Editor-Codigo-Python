# Integración del Editor con Aplicaciones Visual Basic

## Descripción del flujo

Tu aplicación VB principal → Lanza el editor Python → Usuario edita → Cambios guardados en BD → Vuelve a tu aplicación

El editor es **completamente independiente**: tu aplicación solo necesita lanzarlo con los parámetros correctos.

---

## Método 1: Generar archivo JSON y lanzar (RECOMENDADO)

### En tu aplicación VB.NET:

```vb
Imports System.IO
Imports System.Diagnostics
Imports Newtonsoft.Json.Linq ' Instalar via NuGet: Newtonsoft.Json

Public Class FormPrincipal
    Private EditorPath As String = "C:\RutaEditor\editor.exe"
    
    ' Método que se llama cuando el usuario hace clic en "Editar Script"
    Private Sub btnEditarScript_Click(sender As Object, e As EventArgs) Handles btnEditarScript.Click
        ' Obtener datos del registro actual (desde DataGridView, base de datos, etc.)
        Dim modelo As String = txtModelo.Text     ' Ej: "T01"
        Dim codigo As String = txtCodigo.Text      ' Ej: "BOBINADO"
        
        ' Crear configuración dinámica
        Dim config As New JObject(
            New JProperty("connection", New JObject(
                New JProperty("server", ObtenerServidorActual()),      ' Desde config de tu app
                New JProperty("database", ObtenerBaseDatosActual()),   ' Desde config de tu app
                New JProperty("table", "G_SCRIPT"),                    ' O desde configuración
                New JProperty("user", ObtenerUsuarioBD()),
                New JProperty("password", ObtenerPasswordBD()),
                New JProperty("driver", "ODBC Driver 18 for SQL Server"),
                New JProperty("trust_cert", True),
                New JProperty("content_column", "SCRIPT")              ' Columna con el script
            )),
            New JProperty("script", New JObject(
                New JProperty("key_columns", New JArray("MODELO", "CODIGO")),
                New JProperty("key_values", New JArray(modelo, codigo)),
                New JProperty("editable_columns", New JArray("GRUPO", "DESCRIPCION"))  ' Campos editables
            ))
        )
        
        ' Guardar JSON temporal
        Dim tempConfigPath As String = Path.Combine(Path.GetTempPath(), "editor_temp_config.json")
        File.WriteAllText(tempConfigPath, config.ToString())
        
        ' Lanzar el editor
        Try
            Dim proceso As New Process()
            proceso.StartInfo.FileName = EditorPath
            proceso.StartInfo.Arguments = $"--config-file ""{tempConfigPath}"""
            proceso.StartInfo.UseShellExecute = False
            proceso.Start()
            
            ' OPCIÓN A: Esperar a que el usuario termine
            proceso.WaitForExit()
            
            ' OPCIÓN B: No esperar, dejar que edite en paralelo
            ' (Comentar la línea anterior)
            
            ' Limpiar archivo temporal
            File.Delete(tempConfigPath)
            
            ' OPCIONAL: Recargar datos desde BD para reflejar cambios
            RecargarDatosGrid()
            
            MessageBox.Show("Edición completada", "Editor", MessageBoxButtons.OK, MessageBoxIcon.Information)
            
        Catch ex As Exception
            MessageBox.Show($"Error al lanzar editor: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        End Try
    End Sub
    
    ' Métodos auxiliares para obtener configuración de BD
    Private Function ObtenerServidorActual() As String
        ' Obtener desde tu archivo de configuración app.config, registry, etc.
        Return ConfigurationManager.AppSettings("ServidorSQL")
    End Function
    
    Private Function ObtenerBaseDatosActual() As String
        Return ConfigurationManager.AppSettings("BaseDatos")
    End Function
    
    Private Function ObtenerUsuarioBD() As String
        Return ConfigurationManager.AppSettings("UsuarioBD")
    End Function
    
    Private Function ObtenerPasswordBD() As String
        ' IMPORTANTE: Nunca guardar password en texto plano
        ' Usar encriptación, Windows Credentials, o Azure Key Vault
        Return DesencriptarPassword(ConfigurationManager.AppSettings("PasswordBD"))
    End Function
    
    Private Sub RecargarDatosGrid()
        ' Recargar DataGridView o los controles que muestran los scripts
        ' Para reflejar cambios hechos por el editor
    End Sub
End Class
```

---

## Método 2: Variables de entorno (Más simple, menos flexible)

### En VB.NET:

```vb
Private Sub AbrirEditor(modelo As String, codigo As String)
    ' Configurar variables de entorno
    Environment.SetEnvironmentVariable("EDITOR_SERVER", "miservidor\sql2019")
    Environment.SetEnvironmentVariable("EDITOR_DATABASE", "PRODUCCION")
    Environment.SetEnvironmentVariable("EDITOR_TABLE", "G_SCRIPT")
    Environment.SetEnvironmentVariable("EDITOR_KEY_COLUMNS", "MODELO,CODIGO")
    Environment.SetEnvironmentVariable("EDITOR_KEY_VALUES", $"{modelo},{codigo}")
    Environment.SetEnvironmentVariable("EDITOR_CONTENT_COLUMN", "SCRIPT")
    Environment.SetEnvironmentVariable("EDITOR_USER", GetConfigValue("DBUser"))
    Environment.SetEnvironmentVariable("EDITOR_PASSWORD", GetConfigValue("DBPassword"))
    Environment.SetEnvironmentVariable("EDITOR_EDITABLE_COLUMNS", "GRUPO,DESCRIPCION")
    
    ' Lanzar editor (lee variables automáticamente)
    Process.Start("C:\RutaEditor\editor.exe")
End Sub
```

---

## Método 3: Parámetros de línea de comandos (Menos seguro - password visible)

```vb
Private Sub AbrirEditor(modelo As String, codigo As String)
    Dim args As String = $"--server ""miservidor\sql2019"" " &
                         $"--database ""PRODUCCION"" " &
                         $"--table ""G_SCRIPT"" " &
                         $"--key-columns ""MODELO,CODIGO"" " &
                         $"--key-values ""{modelo},{codigo}"" " &
                         $"--content-column ""SCRIPT"" " &
                         $"--user ""sa"" " &
                         $"--password ""password123"""
    
    Process.Start("C:\RutaEditor\editor.exe", args)
End Sub
```

**⚠️ ADVERTENCIA:** Este método expone el password en la línea de comandos (visible con Process Explorer). Usar solo en entorno seguro.

---

## Integración con Visual Basic 6 (VB6)

```vb
' En un módulo o formulario VB6
Private Sub cmdEditarScript_Click()
    Dim modelo As String
    Dim codigo As String
    Dim configPath As String
    Dim editorPath As String
    
    modelo = txtModelo.Text
    codigo = txtCodigo.Text
    
    ' Crear archivo JSON manualmente (VB6 no tiene JSON nativo)
    configPath = Environ("TEMP") & "\editor_config.json"
    editorPath = "C:\RutaEditor\editor.exe"
    
    ' Escribir JSON
    Dim fso As Object
    Dim ts As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set ts = fso.CreateTextFile(configPath, True)
    
    ts.WriteLine "{"
    ts.WriteLine "  ""connection"": {"
    ts.WriteLine "    ""server"": ""miservidor\sql2019"","
    ts.WriteLine "    ""database"": ""PRODUCCION"","
    ts.WriteLine "    ""table"": ""G_SCRIPT"","
    ts.WriteLine "    ""user"": ""sa"","
    ts.WriteLine "    ""password"": ""password123"","
    ts.WriteLine "    ""content_column"": ""SCRIPT"""
    ts.WriteLine "  },"
    ts.WriteLine "  ""script"": {"
    ts.WriteLine "    ""key_columns"": [""MODELO"", ""CODIGO""],"
    ts.WriteLine "    ""key_values"": [""" & modelo & """, """ & codigo & """]"
    ts.WriteLine "  }"
    ts.WriteLine "}"
    ts.Close
    
    ' Lanzar editor
    Shell editorPath & " --config-file """ & configPath & """", vbNormalFocus
    
    ' Limpiar (después de que cierre - puede agregar timer o callback)
    ' Kill configPath
End Sub
```

---

## ¿Qué pasa internamente cuando se ejecuta?

### 1️⃣ **Tu aplicación VB genera la configuración**
```json
{
  "connection": {
    "server": "srv-prod\\sql2019",
    "database": "PRODUCCION_2026",
    "table": "SCRIPTS_CLIENTES",
    "user": "app_user",
    "content_column": "CODIGO_VBS"
  },
  "script": {
    "key_columns": ["ID_CLIENTE", "VERSION"],
    "key_values": ["C12345", "2.0"]
  }
}
```

### 2️⃣ **El editor se conecta y detecta automáticamente**
```python
# El editor ejecuta internamente:
schema = db.get_table_schema()  # Detecta TODAS las columnas
record = db.get_record_full(["ID_CLIENTE", "VERSION"], ["C12345", "2.0"])

# Resultado automático:
record = {
    "ID_CLIENTE": "C12345",
    "VERSION": "2.0",
    "CODIGO_VBS": "Sub Main()...",  # ← Esto va al editor
    "FECHA_CREACION": "2026-01-15",
    "AUTOR": "Juan Pérez",
    "CATEGORIA": "PRODUCCION",
    "VAR0": "VALOR_VAR0",
    "VAR1": "VALOR_VAR1",
    ...
}
```

### 3️⃣ **El sidebar se construye automáticamente**
```
╔════════════════════════╗
║ Sidebar (dinámico)     ║
╠════════════════════════╣
║ C12345                 ║  ← ID_CLIENTE (clave, destacado)
║ 2.0                    ║  ← VERSION (clave, destacado)
║                        ║
║ Fecha Creacion:        ║
║ 2026-01-15             ║
║                        ║
║ Autor:                 ║
║ Juan Pérez             ║
║                        ║
║ Categoria:             ║
║ PRODUCCION             ║
║                        ║
║ ─────────────────      ║
║ Variables del Script   ║
║                        ║
║ Var 0  [VALOR_VAR0]    ║
║ Var 1  [VALOR_VAR1]    ║
╚════════════════════════╝
```

### 4️⃣ **Usuario edita y guarda (Ctrl+S)**
```sql
-- Query generada automáticamente:
UPDATE [SCRIPTS_CLIENTES]
SET [CODIGO_VBS] = '...nuevo contenido...',
    [CATEGORIA] = 'DESARROLLO'  -- Si el campo era editable
WHERE [ID_CLIENTE] = 'C12345' AND [VERSION] = '2.0'
```

### 5️⃣ **Usuario cierra el editor**
Control retorna a tu aplicación VB, que puede recargar datos si es necesario.

---

## Ventajas para tu empresa

✅ **Funciona con CUALQUIER tabla**
- Hoy: `G_SCRIPT` con `MODELO+CODIGO`
- Mañana: `SCRIPTS_CLIENTES` con `ID_CLIENTE+VERSION`
- No requiere cambiar el editor

✅ **Detecta estructura automáticamente**
- Si agregan columnas nuevas a la tabla → Aparecen automáticamente en el sidebar
- Si cambian nombres → Se adapta solo
- Cero mantenimiento

✅ **Cada entorno tiene su configuración**
- Desarrollo: servidor dev, BD dev
- Testing: servidor test, BD test  
- Producción: servidor prod, BD prod
- Tu aplicación VB elige cuál usar

✅ **Seguridad centralizada**
- Credenciales manejadas por tu aplicación VB
- No están hardcodeadas en ningún lado
- Puedes usar Windows Authentication, Azure AD, etc.

✅ **Auditoría completa**
- Todos los eventos se registran en `%APPDATA%\EditorVBS\editor.log`
- Sabes quién editó qué y cuándo

---

## Ejemplo completo de integración real

```vb
' ===================================================================
' FORMULARIO PRINCIPAL DE TU APLICACIÓN VB
' ===================================================================
Public Class FormGestionScripts
    
    ' Configuración (desde app.config)
    Private Const EDITOR_PATH As String = "C:\Aplicaciones\EditorVBS\editor.exe"
    
    ' Evento: Usuario hace doble clic en un script del grid
    Private Sub dgvScripts_CellDoubleClick(sender As Object, e As DataGridViewCellEventArgs) Handles dgvScripts.CellDoubleClick
        If e.RowIndex < 0 Then Return
        
        ' Obtener datos de la fila seleccionada
        Dim row As DataGridViewRow = dgvScripts.Rows(e.RowIndex)
        Dim modelo As String = row.Cells("MODELO").Value.ToString()
        Dim codigo As String = row.Cells("CODIGO").Value.ToString()
        
        ' Abrir editor
        AbrirEditorScript(modelo, codigo)
    End Sub
    
    Private Sub AbrirEditorScript(modelo As String, codigo As String)
        ' Construir configuración JSON
        Dim config As New JObject(
            New JProperty("connection", New JObject(
                New JProperty("server", My.Settings.ServidorSQL),
                New JProperty("database", My.Settings.BaseDatos),
                New JProperty("table", "G_SCRIPT"),
                New JProperty("user", My.Settings.UsuarioBD),
                New JProperty("password", DecryptPassword(My.Settings.PasswordBD)),
                New JProperty("content_column", "SCRIPT")
            )),
            New JProperty("script", New JObject(
                New JProperty("key_columns", New JArray("MODELO", "CODIGO")),
                New JProperty("key_values", New JArray(modelo, codigo)),
                New JProperty("editable_columns", New JArray("GRUPO"))
            ))
        )
        
        ' Guardar config temporal
        Dim tempPath As String = Path.Combine(Path.GetTempPath(), $"editor_{Guid.NewGuid()}.json")
        File.WriteAllText(tempPath, config.ToString())
        
        ' Lanzar editor
        Dim proceso As New Process()
        proceso.StartInfo.FileName = EDITOR_PATH
        proceso.StartInfo.Arguments = $"--config-file ""{tempPath}"""
        proceso.Start()
        
        ' Esperar a que termine
        proceso.WaitForExit()
        
        ' Limpiar
        File.Delete(tempPath)
        
        ' Recargar datos
        CargarScripts()
        
        MessageBox.Show("Edición completada", "Editor", MessageBoxButtons.OK, MessageBoxIcon.Information)
    End Sub
    
    Private Sub CargarScripts()
        ' Tu código existente para cargar el grid
    End Sub
    
    Private Function DecryptPassword(encrypted As String) As String
        ' Tu lógica de desencriptación
        Return encrypted ' Placeholder
    End Function
End Class
```

---

## Preguntas frecuentes

**P: ¿Funciona con SQL Server de cualquier versión?**  
R: Sí, mientras tengas un driver ODBC compatible.

**P: ¿Puedo usar con Oracle, MySQL, PostgreSQL?**  
R: Actualmente solo SQL Server. Pero la arquitectura permite agregar otros conectores fácilmente.

**P: ¿Qué pasa si la tabla tiene 50 columnas?**  
R: El sidebar se construye dinámicamente y muestra todas. Usa scroll automáticamente.

**P: ¿Puedo ocultar algunas columnas?**  
R: Sí, puedes modificar `get_record_full()` para filtrar columnas específicas.

**P: ¿El usuario puede editar las claves primarias?**  
R: No, las claves se muestran readonly. Solo se editan los campos en `editable_columns`.

**P: ¿Cómo sé si el usuario guardó cambios?**  
R: Revisa el código de salida del proceso o consulta el log en `%APPDATA%\EditorVBS\editor.log`.

---

## Deployment

Para distribuir el editor con tu aplicación VB:

1. **Compilar a .exe** usando PyInstaller:
   ```bash
   pip install pyinstaller
   pyinstaller --onefile --windowed main.py
   ```

2. **Incluir en tu instalador** (InnoSetup, WiX, etc.)
3. **Configurar path** en `app.config` de tu aplicación VB
4. **Listo**: Tu aplicación lo llama transparentemente

¿Necesitas ayuda con algún aspecto específico de la integración?
