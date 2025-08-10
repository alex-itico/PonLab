"""
Utilidades para manejo de recursos
Gestión de iconos, imágenes y otros recursos de la aplicación
"""

import os
from PyQt5.QtGui import QIcon, QPixmap

class ResourceManager:
    """Gestor de recursos de la aplicación"""
    
    def __init__(self):
        # Obtener la ruta base del proyecto
        self.base_path = os.path.dirname(os.path.dirname(__file__))
        self.resources_path = os.path.join(self.base_path, 'resources')
        self.icons_path = os.path.join(self.resources_path, 'icons')
        
    def get_icon_path(self, icon_name):
        """Obtener la ruta completa de un icono"""
        return os.path.join(self.icons_path, icon_name)
    
    def get_app_icon(self, size=None):
        """Obtener el icono principal de la aplicación"""
        if size:
            icon_name = f"app_icon_{size}x{size}.png"
            icon_path = self.get_icon_path(icon_name)
            if os.path.exists(icon_path):
                return QIcon(icon_path)
        
        # Fallback al icono principal
        icon_path = self.get_icon_path("app_icon.ico")
        if os.path.exists(icon_path):
            return QIcon(icon_path)
            
        return QIcon()  # Icono vacío si no se encuentra
    
    def get_icon(self, icon_name):
        """Obtener un icono por nombre"""
        icon_path = self.get_icon_path(icon_name)
        if os.path.exists(icon_path):
            return QIcon(icon_path)
        return QIcon()
    
    def list_available_icons(self):
        """Listar todos los iconos disponibles"""
        if not os.path.exists(self.icons_path):
            return []
        
        icons = []
        for file in os.listdir(self.icons_path):
            if file.lower().endswith(('.png', '.ico', '.svg', '.jpg', '.jpeg')):
                icons.append(file)
        
        return sorted(icons)

# Instancia global del gestor de recursos
resource_manager = ResourceManager()
