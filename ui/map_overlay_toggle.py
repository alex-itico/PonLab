"""
Map Overlay Toggle Button
Botón toggle para activar/desactivar la máscara de mapa
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QIcon
from PyQt5.QtCore import QRect

class MapOverlayToggle(QPushButton):
    """Botón toggle personalizado para la máscara de mapa"""
    
    # Señal emitida cuando cambia el estado
    toggled = pyqtSignal(bool)  # True = activado, False = desactivado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Estado del botón
        self.is_map_active = False
        
        # Configuración visual
        self.setFixedSize(100, 35)
        self.setCursor(Qt.PointingHandCursor)
        
        # Texto
        self.setText("🗺️ Mapa")
        
        # Configurar estilo inicial
        self.update_style()
        
        # Conectar clic
        self.clicked.connect(self.toggle_state)
    
    def toggle_state(self):
        """Alternar estado del botón"""
        self.is_map_active = not self.is_map_active
        self.update_style()
        self.toggled.emit(self.is_map_active)
    
    def set_active(self, active):
        """Establecer estado sin emitir señal"""
        if self.is_map_active != active:
            self.is_map_active = active
            self.update_style()
    
    def is_active(self):
        """Obtener estado actual"""
        return self.is_map_active
    
    def set_theme(self, dark_theme):
        """Actualizar estilo según el tema"""
        self.dark_theme = dark_theme
        self.update_style()
    
    def update_style(self):
        """Actualizar el estilo del botón según el estado y tema"""
        if hasattr(self, 'dark_theme') and self.dark_theme:
            # Tema oscuro
            if self.is_map_active:
                # Activado
                bg_color = "#3b82f6"  # Azul
                hover_color = "#2563eb"
                pressed_color = "#1d4ed8"
                text_color = "white"
                border_color = "#1e40af"
            else:
                # Desactivado
                bg_color = "#4b5563"  # Gris oscuro
                hover_color = "#6b7280"
                pressed_color = "#374151"
                text_color = "#d1d5db"
                border_color = "#6b7280"
        else:
            # Tema claro
            if self.is_map_active:
                # Activado
                bg_color = "#3b82f6"  # Azul
                hover_color = "#2563eb"
                pressed_color = "#1d4ed8"
                text_color = "white"
                border_color = "#1e40af"
            else:
                # Desactivado
                bg_color = "#e5e7eb"  # Gris claro
                hover_color = "#d1d5db"
                pressed_color = "#9ca3af"
                text_color = "#4b5563"
                border_color = "#9ca3af"
        
        # Aplicar estilo
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                font-weight: bold;
                padding: 6px 12px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {pressed_color};
            }}
        """)
