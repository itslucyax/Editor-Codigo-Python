# -*- coding: utf-8 -*-
"""
Cargador de configuración multi-fuente sin hardcodeo.

Permite cargar la configuración desde:
1. Variables de entorno (prefijo EDITOR_)
2. Archivo de configuración JSON (--config-file)
3. Parámetros de línea de comandos (prioridad más alta)

CERO hardcodeo: Todo es configurable externamente.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("EditorVBS.config")


class ConfigLoader:
    """
    Carga configuración desde múltiples fuentes con prioridad:
    1. CLI args (prioridad alta)
    2. Variables de entorno
    3. Archivo JSON
    4. Valores por defecto (solo para opcionales)
    """
    
    # Prefijo para variables de entorno
    ENV_PREFIX = "EDITOR_"
    
    # Mapeo de nombres de configuración a variables de entorno
    ENV_MAPPING = {
        "connection_string": "CONNECTION_STRING",
        "server": "SERVER",
        "database": "DATABASE",
        "table": "TABLE",
        "user": "USER",
        "password": "PASSWORD",
        "driver": "DRIVER",
        "trust_cert": "TRUST_CERT",
        "content_column": "CONTENT_COLUMN",
        "key_columns": "KEY_COLUMNS",  # Formato: "MODELO,CODIGO"
        "key_values": "KEY_VALUES",    # Formato: "T01,SCRIPT001"
        "var_columns": "VAR_COLUMNS",  # Formato: "VAR0,VAR1,VAR2"
        "config_file": "CONFIG_FILE",
    }
    
    def __init__(self):
        self.config = {}  # Dict[str, Any]
        self._file_config = {}  # Dict[str, Any]
        self._env_config = {}  # Dict[str, Any]
    
    def load_from_file(self, config_file: str) -> None:
        """
        Carga configuración desde un archivo JSON.
        
        Args:
            config_file: Ruta al archivo JSON
            
        Formato esperado:
        {
            "connection": {
                "server": "servidor\\instancia",
                "database": "MIBD",
                "table": "G_SCRIPT",
                "user": "sa",
                "password": "password123",
                "driver": "ODBC Driver 18 for SQL Server",
                "trust_cert": true,
                "content_column": "SCRIPT"
            },
            "script": {
                "key_columns": ["MODELO", "CODIGO"],
                "key_values": ["T01", "BOBINADO"],
                "var_columns": ["VAR0", "VAR1", "VAR2", "VAR3"]
            }
        }
        """
        if not os.path.exists(config_file):
            logger.warning("Archivo de configuración no encontrado: %s", config_file)
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Aplanar estructura JSON
            if "connection" in data:
                self._file_config.update(data["connection"])
            if "script" in data:
                self._file_config.update(data["script"])
            
            # También soportar estructura plana
            for key in self.ENV_MAPPING.keys():
                if key in data:
                    self._file_config[key] = data[key]
            
            logger.info("Configuración cargada desde archivo: %s", config_file)
            logger.debug("Config file: %s", self._file_config)
        
        except Exception as e:
            logger.error("Error al cargar archivo de configuración: %s", e)
    
    def load_from_env(self) -> None:
        """
        Carga configuración desde variables de entorno con prefijo EDITOR_.
        
        Ejemplos:
            EDITOR_SERVER=servidor\\instancia
            EDITOR_DATABASE=MIBD
            EDITOR_TABLE=G_SCRIPT
            EDITOR_KEY_COLUMNS=MODELO,CODIGO
            EDITOR_KEY_VALUES=T01,SCRIPT001
        """
        for config_key, env_suffix in self.ENV_MAPPING.items():
            env_var = f"{self.ENV_PREFIX}{env_suffix}"
            value = os.environ.get(env_var)
            
            if value:
                # Convertir strings especiales
                if config_key in ["key_columns", "var_columns"]:
                    # Convertir "COL1,COL2" a lista
                    self._env_config[config_key] = [v.strip() for v in value.split(",")]
                elif config_key == "key_values":
                    # Convertir "VAL1,VAL2" a lista
                    self._env_config[config_key] = [v.strip() for v in value.split(",")]
                elif config_key == "trust_cert":
                    # Convertir "true"/"false" a booleano
                    self._env_config[config_key] = value.lower() in ["true", "1", "yes"]
                else:
                    self._env_config[config_key] = value
        
        if self._env_config:
            logger.info("Configuración cargada desde variables de entorno")
            logger.debug("Env config: %s", self._env_config)
    
    def merge(self, cli_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combina todas las fuentes de configuración con prioridad:
        CLI args > Variables de entorno > Archivo JSON
        
        Args:
            cli_args: Diccionario con argumentos de línea de comandos
            
        Returns:
            Diccionario con configuración final
        """
        # Orden: archivo → env → cli (cada uno sobrescribe el anterior)
        self.config = {}
        
        # 1. Archivo JSON (prioridad más baja)
        self.config.update(self._file_config)
        
        # 2. Variables de entorno
        self.config.update(self._env_config)
        
        # 3. CLI args (prioridad más alta)
        # Solo sobrescribir si el valor no es None
        for key, value in cli_args.items():
            if value is not None:
                self.config[key] = value
        
        logger.info("Configuración final combinada")
        logger.debug("Final config: %s", {k: v if k != "password" else "***" for k, v in self.config.items()})
        
        return self.config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor de configuración."""
        return self.config.get(key, default)
    
    def get_required(self, key: str) -> Any:
        """
        Obtiene un valor requerido. Lanza error si no existe.
        
        Raises:
            ValueError: Si la configuración requerida no está presente
        """
        if key not in self.config:
            raise ValueError(
                f"Configuración requerida '{key}' no encontrada.\n"
                f"Especifica via:\n"
                f"  - Variable de entorno: {self.ENV_PREFIX}{self.ENV_MAPPING.get(key, key.upper())}\n"
                f"  - Archivo JSON: --config-file\n"
                f"  - Parámetro CLI: --{key.replace('_', '-')}"
            )
        return self.config[key]
    
    def validate_connection_config(self) -> None:
        """
        Valida que exista configuración mínima para conectar a la BD.
        
        Soporta dos modos:
        1. Connection string completa
        2. Parámetros individuales (server, database, user, password)
        
        Raises:
            ValueError: Si falta configuración requerida
        """
        # Opción 1: Connection string completa
        if "connection_string" in self.config:
            logger.info("Usando connection string completa")
            return
        
        # Opción 2: Parámetros individuales
        required = ["server", "database", "table", "user", "password"]
        missing = [k for k in required if k not in self.config]
        
        if missing:
            raise ValueError(
                f"Configuración de conexión incompleta. Faltan: {', '.join(missing)}\n"
                "Opciones:\n"
                "1. Proporcionar connection_string completa\n"
                "2. Proporcionar: server, database, table, user, password"
            )
    
    def validate_script_config(self) -> None:
        """
        Valida que exista configuración mínima para identificar el script.
        
        Raises:
            ValueError: Si falta configuración requerida
        """
        required = ["key_columns", "key_values", "content_column"]
        missing = [k for k in required if k not in self.config]
        
        if missing:
            raise ValueError(
                f"Configuración de script incompleta. Faltan: {', '.join(missing)}"
            )
        
        # Validar que key_columns y key_values tengan la misma longitud
        key_cols = self.config.get("key_columns", [])
        key_vals = self.config.get("key_values", [])
        
        if len(key_cols) != len(key_vals):
            raise ValueError(
                f"key_columns tiene {len(key_cols)} elementos pero "
                f"key_values tiene {len(key_vals)} elementos"
            )


def create_config_example(output_file: str = "editor_config.example.json") -> None:
    """
    Crea un archivo de ejemplo de configuración JSON.
    
    Args:
        output_file: Ruta donde crear el archivo
    """
    example = {
        "_comment": "Configuración de ejemplo para el Editor VBS",
        "connection": {
            "server": "servidor\\instancia",
            "database": "MIBD",
            "table": "G_SCRIPT",
            "user": "sa",
            "password": "tu_password_aqui",
            "driver": "ODBC Driver 18 for SQL Server",
            "trust_cert": True,
            "content_column": "SCRIPT"
        },
        "script": {
            "key_columns": ["MODELO", "CODIGO"],
            "key_values": ["T01", "BOBINADO"],
            "var_columns": ["VAR0", "VAR1", "VAR2", "VAR3", "VAR4", "VAR5", "VAR6", "VAR7", "VAR8", "VAR9"]
        },
        "_comment_2": "Alternativamente, puedes usar connection_string:",
        "connection_string_example": "Driver={ODBC Driver 18 for SQL Server};Server=servidor\\instancia;Database=MIBD;UID=sa;PWD=password;TrustServerCertificate=Yes"
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(example, f, indent=2, ensure_ascii=False)
    
    print(f"Archivo de ejemplo creado: {output_file}")


if __name__ == "__main__":
    # Crear archivo de ejemplo
    create_config_example()
