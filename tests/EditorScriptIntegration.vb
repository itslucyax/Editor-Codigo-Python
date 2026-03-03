' ==================================================================
' CLASE DE INTEGRACIÓN - Copiar a tu proyecto VB.NET
' ==================================================================
' Esta clase maneja toda la comunicación con el editor Python
' Uso:
'   Dim editor As New EditorScriptIntegration("C:\RutaEditor\editor.exe")
'   editor.AbrirScript("T01", "BOBINADO")
' ==================================================================

Imports System.IO
Imports System.Diagnostics
Imports Newtonsoft.Json.Linq

Public Class EditorScriptIntegration
    
    Private ReadOnly _editorExecutablePath As String
    
    ' Constructor
    Public Sub New(editorPath As String)
        If Not File.Exists(editorPath) Then
            Throw New FileNotFoundException($"No se encuentra el editor en: {editorPath}")
        End If
        _editorExecutablePath = editorPath
    End Sub
    
    ''' <summary>
    ''' Abre el editor para un script específico
    ''' </summary>
    ''' <param name="server">Servidor SQL (ej: "servidor\instancia")</param>
    ''' <param name="database">Nombre de la base de datos</param>
    ''' <param name="table">Nombre de la tabla</param>
    ''' <param name="keyColumns">Columnas que forman la clave primaria</param>
    ''' <param name="keyValues">Valores de las claves</param>
    ''' <param name="user">Usuario SQL</param>
    ''' <param name="password">Contraseña SQL</param>
    ''' <param name="contentColumn">Columna con el contenido del script (default: "SCRIPT")</param>
    ''' <param name="editableColumns">Columnas editables por el usuario (opcional)</param>
    ''' <param name="waitForExit">Si True, espera a que el usuario cierre el editor</param>
    ''' <returns>True si se abrió correctamente, False si hubo error</returns>
    Public Function AbrirScript(
        server As String,
        database As String,
        table As String,
        keyColumns As String(),
        keyValues As String(),
        user As String,
        password As String,
        Optional contentColumn As String = "SCRIPT",
        Optional editableColumns As String() = Nothing,
        Optional waitForExit As Boolean = True
    ) As Boolean
        
        Try
            ' Validaciones
            If keyColumns.Length <> keyValues.Length Then
                Throw New ArgumentException("keyColumns y keyValues deben tener la misma longitud")
            End If
            
            ' Construir configuración JSON
            Dim config As New JObject(
                New JProperty("connection", New JObject(
                    New JProperty("server", server),
                    New JProperty("database", database),
                    New JProperty("table", table),
                    New JProperty("user", user),
                    New JProperty("password", password),
                    New JProperty("driver", "ODBC Driver 18 for SQL Server"),
                    New JProperty("trust_cert", True),
                    New JProperty("content_column", contentColumn)
                )),
                New JProperty("script", New JObject(
                    New JProperty("key_columns", New JArray(keyColumns)),
                    New JProperty("key_values", New JArray(keyValues))
                ))
            )
            
            ' Agregar columnas editables si se especificaron
            If editableColumns IsNot Nothing AndAlso editableColumns.Length > 0 Then
                DirectCast(config("script"), JObject).Add("editable_columns", New JArray(editableColumns))
            End If
            
            ' Crear archivo temporal
            Dim tempConfigPath As String = Path.Combine(
                Path.GetTempPath(), 
                $"editor_config_{Guid.NewGuid()}.json"
            )
            
            File.WriteAllText(tempConfigPath, config.ToString(), System.Text.Encoding.UTF8)
            
            ' Lanzar editor
            Dim proceso As New Process()
            proceso.StartInfo.FileName = _editorExecutablePath
            proceso.StartInfo.Arguments = $"--config-file ""{tempConfigPath}"""
            proceso.StartInfo.UseShellExecute = False
            proceso.StartInfo.CreateNoWindow = False
            proceso.Start()
            
            ' Esperar si se indicó
            If waitForExit Then
                proceso.WaitForExit()
            End If
            
            ' Limpiar archivo temporal
            If File.Exists(tempConfigPath) Then
                File.Delete(tempConfigPath)
            End If
            
            Return True
            
        Catch ex As Exception
            ' Manejar error
            Debug.WriteLine($"Error al abrir editor: {ex.Message}")
            MessageBox.Show(
                $"Error al abrir el editor:{vbCrLf}{ex.Message}", 
                "Error", 
                MessageBoxButtons.OK, 
                MessageBoxIcon.Error
            )
            Return False
        End Try
    End Function
    
    ''' <summary>
    ''' Sobrecarga simplificada para tabla G_SCRIPT con MODELO+CODIGO
    ''' </summary>
    Public Function AbrirScriptGScript(
        server As String,
        database As String,
        modelo As String,
        codigo As String,
        user As String,
        password As String,
        Optional editableColumns As String() = Nothing,
        Optional waitForExit As Boolean = True
    ) As Boolean
        
        Return AbrirScript(
            server, 
            database, 
            "G_SCRIPT", 
            {"MODELO", "CODIGO"}, 
            {modelo, codigo}, 
            user, 
            password,
            "SCRIPT",
            editableColumns,
            waitForExit
        )
    End Function
    
End Class


' ==================================================================
' EJEMPLO DE USO EN UN FORMULARIO
' ==================================================================

Public Class FormPrincipal
    
    Private _editorIntegration As EditorScriptIntegration
    
    Private Sub FormPrincipal_Load(sender As Object, e As EventArgs) Handles MyBase.Load
        ' Inicializar integración del editor
        ' (La ruta del editor debería venir de app.config)
        Dim editorPath As String = ConfigurationManager.AppSettings("EditorScriptPath")
        _editorIntegration = New EditorScriptIntegration(editorPath)
    End Sub
    
    ' Evento: Usuario hace clic en "Editar Script"
    Private Sub btnEditarScript_Click(sender As Object, e As EventArgs) Handles btnEditarScript.Click
        ' Obtener datos del formulario
        Dim modelo As String = txtModelo.Text
        Dim codigo As String = txtCodigo.Text
        
        ' Validar
        If String.IsNullOrWhiteSpace(modelo) OrElse String.IsNullOrWhiteSpace(codigo) Then
            MessageBox.Show("Debe especificar Modelo y Código", "Validación", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            Return
        End If
        
        ' Obtener configuración de BD (desde app.config, registry, etc.)
        Dim server As String = My.Settings.ServidorSQL
        Dim database As String = My.Settings.BaseDatos
        Dim user As String = My.Settings.UsuarioBD
        Dim password As String = DesencriptarPassword(My.Settings.PasswordBD)
        
        ' Abrir editor
        Dim exito As Boolean = _editorIntegration.AbrirScriptGScript(
            server,
            database,
            modelo,
            codigo,
            user,
            password,
            {"GRUPO"},  ' Columnas editables
            True        ' Esperar a que termine
        )
        
        If exito Then
            ' Opcional: Recargar datos para reflejar cambios
            RecargarDatosScript()
            MessageBox.Show("Edición completada", "Editor", MessageBoxButtons.OK, MessageBoxIcon.Information)
        End If
    End Sub
    
    ' Evento: Usuario hace doble clic en el DataGridView
    Private Sub dgvScripts_CellDoubleClick(sender As Object, e As DataGridViewCellEventArgs) Handles dgvScripts.CellDoubleClick
        If e.RowIndex < 0 Then Return
        
        Dim row As DataGridViewRow = dgvScripts.Rows(e.RowIndex)
        Dim modelo As String = row.Cells("MODELO").Value?.ToString()
        Dim codigo As String = row.Cells("CODIGO").Value?.ToString()
        
        If String.IsNullOrEmpty(modelo) OrElse String.IsNullOrEmpty(codigo) Then Return
        
        ' Abrir editor con los datos de la fila seleccionada
        _editorIntegration.AbrirScriptGScript(
            My.Settings.ServidorSQL,
            My.Settings.BaseDatos,
            modelo,
            codigo,
            My.Settings.UsuarioBD,
            DesencriptarPassword(My.Settings.PasswordBD),
            {"GRUPO"},
            True
        )
        
        ' Recargar grid
        RecargarDatosScript()
    End Sub
    
    Private Sub RecargarDatosScript()
        ' Tu código para recargar el DataGridView
    End Sub
    
    Private Function DesencriptarPassword(encrypted As String) As String
        ' Tu lógica de desencriptación
        ' Por ahora placeholder
        Return encrypted
    End Function
    
End Class


' ==================================================================
' APP.CONFIG - Agregar estas líneas
' ==================================================================
'
' <appSettings>
'   <add key="EditorScriptPath" value="C:\Aplicaciones\EditorVBS\editor.exe" />
'   <add key="ServidorSQL" value="miservidor\sql2019" />
'   <add key="BaseDatos" value="PRODUCCION" />
'   <add key="UsuarioBD" value="app_user" />
'   <add key="PasswordBD" value="[password_encriptado]" />
' </appSettings>
'
' ==================================================================


' ==================================================================
' INSTALACIÓN DE DEPENDENCIAS (NuGet Package Manager Console)
' ==================================================================
'
' Install-Package Newtonsoft.Json
'
' ==================================================================
