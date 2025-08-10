"""
Gestor de Configuraciones
Manejo de configuraciones persistentes de la aplicación
"""

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication
import os

class ConfigManager:
    """Gestor de configuraciones de la aplicación"""
    
    def __init__(self):
        # Configurar QSettings con información de la organización y aplicación
        self.settings = QSettings("SimuladorWDM", "Simulador de Redes Opticas")
        
        # Configuraciones por defecto
        self.defaults = {
            'theme_dark': False,
            'grid_visible': True,
            'grid_size': 20,
            'window_width': 1200,
            'window_height': 800,
            'window_maximized': False,
            'components_visible': True,
            'simulation_visible': True,
            'info_panel_visible': False,
            'zoom_factor': 1.0
        }
    
    def save_setting(self, key, value):
        """Guardar una configuración específica"""
        self.settings.setValue(key, value)
        self.settings.sync()  # Forzar escritura inmediata
    
    def get_setting(self, key, default_value=None):
        """Obtener una configuración específica"""
        if default_value is None and key in self.defaults:
            default_value = self.defaults[key]
        
        value = self.settings.value(key, default_value)
        
        # Convertir tipos apropiadamente desde QSettings
        if isinstance(default_value, bool):
            return value in [True, 'true', 'True', '1', 1]
        elif isinstance(default_value, int):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default_value
        elif isinstance(default_value, float):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default_value
        
        return value
    
    def save_window_state(self, window):
        """Guardar estado de la ventana"""
        self.save_setting('window_maximized', window.isMaximized())
        if not window.isMaximized():
            self.save_setting('window_width', window.width())
            self.save_setting('window_height', window.height())
            # También guardar posición
            self.save_setting('window_x', window.x())
            self.save_setting('window_y', window.y())
    
    def restore_window_state(self, window):
        """Restaurar estado de la ventana"""
        # Restaurar tamaño
        width = self.get_setting('window_width', 1200)
        height = self.get_setting('window_height', 800)
        window.resize(width, height)
        
        # Restaurar posición si existe
        x = self.get_setting('window_x')
        y = self.get_setting('window_y')
        if x is not None and y is not None:
            window.move(int(x), int(y))
        
        # Restaurar estado maximizado
        if self.get_setting('window_maximized', False):
            window.showMaximized()
    
    def save_theme_settings(self, dark_theme):
        """Guardar configuración del tema"""
        self.save_setting('theme_dark', dark_theme)
    
    def get_theme_settings(self):
        """Obtener configuración del tema"""
        return self.get_setting('theme_dark', False)
    
    def save_canvas_settings(self, canvas):
        """Guardar configuraciones del canvas"""
        if hasattr(canvas, 'grid_visible'):
            self.save_setting('grid_visible', canvas.grid_visible)
        if hasattr(canvas, 'grid_size'):
            self.save_setting('grid_size', canvas.grid_size)
        if hasattr(canvas, 'zoom_factor'):
            self.save_setting('zoom_factor', canvas.zoom_factor)
        if hasattr(canvas, 'info_panel_visible'):
            self.save_setting('info_panel_visible', canvas.info_panel_visible)
    
    def restore_canvas_settings(self, canvas):
        """Restaurar configuraciones del canvas"""
        # Restaurar visibilidad de cuadrícula
        grid_visible = self.get_setting('grid_visible', True)
        if hasattr(canvas, 'grid_visible'):
            canvas.grid_visible = grid_visible
            canvas.origin_visible = grid_visible  # El origen sigue a la cuadrícula
        
        # Restaurar tamaño de cuadrícula
        grid_size = self.get_setting('grid_size', 20)
        if hasattr(canvas, 'set_grid_size'):
            canvas.set_grid_size(grid_size)
        
        # Restaurar factor de zoom
        zoom_factor = self.get_setting('zoom_factor', 1.0)
        if hasattr(canvas, 'zoom_factor'):
            canvas.zoom_factor = zoom_factor
        
        # Restaurar panel de información
        info_visible = self.get_setting('info_panel_visible', False)
        if hasattr(canvas, 'info_panel_visible'):
            canvas.info_panel_visible = info_visible
    
    def save_ui_settings(self, main_window):
        """Guardar configuraciones de la UI"""
        if hasattr(main_window, 'components_visible'):
            self.save_setting('components_visible', main_window.components_visible)
        if hasattr(main_window, 'simulation_visible'):
            self.save_setting('simulation_visible', main_window.simulation_visible)
    
    def restore_ui_settings(self, main_window):
        """Restaurar configuraciones de la UI"""
        if hasattr(main_window, 'components_visible'):
            main_window.components_visible = self.get_setting('components_visible', True)
        if hasattr(main_window, 'simulation_visible'):
            main_window.simulation_visible = self.get_setting('simulation_visible', True)
    
    def reset_to_defaults(self):
        """Resetear todas las configuraciones a valores por defecto"""
        self.settings.clear()
        self.settings.sync()
    
    def get_all_settings(self):
        """Obtener todas las configuraciones actuales (útil para debug)"""
        all_keys = self.settings.allKeys()
        return {key: self.settings.value(key) for key in all_keys}

# Instancia global del gestor de configuraciones
config_manager = ConfigManager()
