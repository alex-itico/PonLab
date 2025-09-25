"""
Connection Points System
Sistema de vértices de conexión para dispositivos
"""

from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPen, QBrush, QColor
from enum import Enum

class ConnectionPointType(Enum):
    """Tipos de puntos de conexión"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    RIGHT_CENTER = "right_center"
    BOTTOM_RIGHT = "bottom_right"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_LEFT = "bottom_left"
    LEFT_CENTER = "left_center"

class ConnectionPoint(QGraphicsEllipseItem):
    """Punto de conexión individual para dispositivos"""
    
    def __init__(self, point_type: ConnectionPointType, parent_device, parent=None):
        super().__init__(parent)
        
        self.point_type = point_type
        self.parent_device = parent_device
        self.size = 8  # Tamaño base del punto
        
        # Configurar propiedades del punto
        self.setup_point()
        
    def setup_point(self):
        """Configurar las propiedades visuales del punto"""
        # Establecer el tamaño del punto
        radius = self.size / 2
        self.setRect(-radius, -radius, self.size, self.size)
        
        # Configurar colores por defecto
        self.update_theme(dark_theme=False)  # Se actualizará después
        
        # Z-value para aparecer encima del dispositivo pero debajo de etiquetas
        self.setZValue(102)
        
        # Configurar flags
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        
    def update_theme(self, dark_theme=False):
        """Actualizar colores según el tema"""
        if dark_theme:
            # Tema oscuro: puntos claros con borde
            pen_color = QColor(255, 255, 255)  # Blanco
            brush_color = QColor(100, 150, 255, 180)  # Azul claro transparente
        else:
            # Tema claro: puntos oscuros con borde
            pen_color = QColor(50, 50, 50)  # Gris oscuro
            brush_color = QColor(100, 150, 255, 180)  # Azul transparente
        
        # Configurar pen (borde)
        pen = QPen(pen_color)
        pen.setWidth(2)
        self.setPen(pen)
        
        # Configurar brush (relleno)
        brush = QBrush(brush_color)
        self.setBrush(brush)
    
    def update_position(self, device_rect):
        """Actualizar posición del punto basado en el rectángulo del dispositivo"""
        # Obtener dimensiones del dispositivo
        width = device_rect.width()
        height = device_rect.height()
        
        # Calcular posición según el tipo de punto
        x, y = self._calculate_position(width, height)
        
        # Establecer posición relativa al dispositivo
        self.setPos(x, y)
    
    def _calculate_position(self, device_width, device_height):
        """Calcular la posición x, y del punto según su tipo"""
        # Posiciones relativas al centro del dispositivo
        half_width = device_width / 2
        half_height = device_height / 2
        
        positions = {
            ConnectionPointType.TOP_LEFT: (-half_width, -half_height),
            ConnectionPointType.TOP_CENTER: (0, -half_height),
            ConnectionPointType.TOP_RIGHT: (half_width, -half_height),
            ConnectionPointType.RIGHT_CENTER: (half_width, 0),
            ConnectionPointType.BOTTOM_RIGHT: (half_width, half_height),
            ConnectionPointType.BOTTOM_CENTER: (0, half_height),
            ConnectionPointType.BOTTOM_LEFT: (-half_width, half_height),
            ConnectionPointType.LEFT_CENTER: (-half_width, 0)
        }
        
        return positions.get(self.point_type, (0, 0))
    
    def get_connection_info(self):
        """Obtener información del punto para conexiones"""
        return {
            'type': self.point_type.value,
            'device': self.parent_device,
            'position': self.pos()
        }

class ConnectionPointsManager:
    """Gestor de todos los puntos de conexión de un dispositivo"""
    
    def __init__(self, device_graphics_item):
        self.device_graphics_item = device_graphics_item
        self.connection_points = {}
        self.visible = False
        
        # Crear todos los puntos de conexión
        self._create_connection_points()
    
    def _create_connection_points(self):
        """Crear los 8 puntos de conexión"""
        for point_type in ConnectionPointType:
            point = ConnectionPoint(
                point_type, 
                self.device_graphics_item.device,
                self.device_graphics_item
            )
            point.hide()  # Inicialmente ocultos
            self.connection_points[point_type] = point
    
    def show_points(self):
        """Mostrar todos los puntos de conexión"""
        if not self.visible:
            self.visible = True
            for point in self.connection_points.values():
                point.show()
            self.update_positions()
    
    def hide_points(self):
        """Ocultar todos los puntos de conexión"""
        if self.visible:
            self.visible = False
            for point in self.connection_points.values():
                point.hide()
    
    def update_positions(self):
        """Actualizar posiciones de todos los puntos"""
        if not self.visible:
            return
        
        # Obtener rectángulo del dispositivo
        device_rect = self.device_graphics_item.pixmap().rect()
        
        # Actualizar cada punto
        for point in self.connection_points.values():
            point.update_position(device_rect)
    
    def update_theme(self, dark_theme=False):
        """Actualizar tema de todos los puntos"""
        for point in self.connection_points.values():
            point.update_theme(dark_theme)
    
    def get_point(self, point_type: ConnectionPointType):
        """Obtener un punto específico"""
        return self.connection_points.get(point_type)
    
    def get_all_points(self):
        """Obtener todos los puntos"""
        return list(self.connection_points.values())
    
    def cleanup(self):
        """Limpiar recursos"""
        for point in self.connection_points.values():
            if point.scene():
                point.scene().removeItem(point)
        self.connection_points.clear()
