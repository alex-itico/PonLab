"""
Gestor de proyectos para archivos .pon
Maneja guardado automático y carga de topologías PON
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class ProjectManager(QObject):
    """Gestor de archivos de proyecto .pon con auto-save"""
    
    # Señales
    project_loaded = pyqtSignal(dict)  # Datos del proyecto cargado
    project_saved = pyqtSignal(str)    # Ruta del archivo guardado
    
    def __init__(self):
        super().__init__()
        self.current_file_path = None
        
        # Crear carpeta para archivos temporales
        self.temp_dir = os.path.join(os.path.dirname(__file__), '..', 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Limpiar archivos temporales antiguos al inicializar
        self.cleanup_temp_files()
        
        # Archivo de auto-guardado en carpeta temporal
        self.auto_save_path = os.path.join(self.temp_dir, "sin_guardar.pon")
        self.project_data = self.get_empty_project()
    
    def get_empty_project(self) -> Dict[str, Any]:
        """Crear estructura de proyecto vacía"""
        return {
            "format_version": "1.0",
            "created_with": "PonLab v1.0",
            "metadata": {
                "name": "Sin guardar",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat()
            },
            "canvas": {
                "zoom": 1.0,
                "center": [0, 0],
                "grid_visible": True,
                "grid_size": 20
            },
            "devices": {},
            "connections": {}
        }
    
    def update_project_data(self, devices_data: dict, connections_data: dict, canvas_data: dict = None):
        """Actualizar datos del proyecto actual"""
        self.project_data["devices"] = devices_data
        self.project_data["connections"] = connections_data
        self.project_data["metadata"]["modified"] = datetime.now().isoformat()
        
        if canvas_data:
            self.project_data["canvas"].update(canvas_data)
        
        # Auto-save automático
        self.auto_save()
    
    def auto_save(self):
        """Guardar automáticamente en archivo temporal"""
        try:
            with open(self.auto_save_path, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Auto-guardado en carpeta temporal: temp/sin_guardar.pon")
            return True
        except Exception as e:
            print(f"❌ Error en auto-guardado: {e}")
            return False
    
    def save_as(self, file_path: str) -> bool:
        """Guardar proyecto en ruta específica"""
        try:
            # Actualizar metadatos
            self.project_data["metadata"]["name"] = os.path.splitext(os.path.basename(file_path))[0]
            self.project_data["metadata"]["modified"] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.project_data, f, indent=2, ensure_ascii=False)
            
            self.current_file_path = file_path
            self.project_saved.emit(file_path)
            print(f"💾 Proyecto guardado: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error al guardar proyecto: {e}")
            return False
    
    def load_project(self, file_path: str) -> bool:
        """Cargar proyecto desde archivo .pon - solo dispositivos y conexiones"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validar formato
            if not self.validate_project_format(data):
                print(f"❌ Formato de proyecto inválido: {file_path}")
                return False
            
            # Solo extraer dispositivos y conexiones
            filtered_data = {
                "devices": data.get("devices", {}),
                "connections": data.get("connections", {})
            }
            
            # Actualizar proyecto interno con datos completos para auto-save
            self.project_data["devices"] = filtered_data["devices"]
            self.project_data["connections"] = filtered_data["connections"] 
            self.project_data["metadata"]["modified"] = datetime.now().isoformat()
            
            self.current_file_path = file_path
            # Emitir solo dispositivos y conexiones
            self.project_loaded.emit(filtered_data)
            print(f"📂 Proyecto cargado: {file_path} - Solo dispositivos y conexiones")
            return True
            
        except Exception as e:
            print(f"❌ Error al cargar proyecto: {e}")
            return False
    
    def load_auto_save(self) -> bool:
        """Cargar archivo de auto-guardado si existe"""
        if os.path.exists(self.auto_save_path):
            return self.load_project(self.auto_save_path)
        return False
    
    def validate_project_format(self, data: dict) -> bool:
        """Validar que el archivo tenga el formato correcto"""
        required_keys = ["format_version", "devices", "connections"]
        return all(key in data for key in required_keys)
    
    def clear_project(self):
        """Limpiar proyecto actual"""
        self.project_data = self.get_empty_project()
        self.current_file_path = None
        self.auto_save()
    
    def get_project_info(self) -> dict:
        """Obtener información del proyecto actual"""
        return {
            "file_path": self.current_file_path or self.auto_save_path,
            "name": self.project_data["metadata"]["name"],
            "devices_count": len(self.project_data["devices"]),
            "connections_count": len(self.project_data["connections"]),
            "created": self.project_data["metadata"]["created"],
            "modified": self.project_data["metadata"]["modified"]
        }
    
    def cleanup_temp_files(self):
        """Limpiar archivos temporales antiguos"""
        try:
            if os.path.exists(self.temp_dir):
                for file in os.listdir(self.temp_dir):
                    if file.endswith('.pon'):
                        file_path = os.path.join(self.temp_dir, file)
                        # Borrar archivos temporales de más de 1 día
                        if os.path.getctime(file_path) < (datetime.now().timestamp() - 86400):
                            os.remove(file_path)
                            print(f"🧹 Archivo temporal eliminado: {file}")
        except Exception as e:
            print(f"⚠️ Error limpiando archivos temporales: {e}")
    
    def has_temp_save(self) -> bool:
        """Verificar si existe un archivo temporal"""
        return os.path.exists(self.auto_save_path)
