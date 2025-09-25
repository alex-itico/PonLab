"""
Módulo para manejar las conexiones entre dispositivos
"""

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QPen, QColor, QFont
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsItem, QGraphicsTextItem
from typing import Tuple, Optional
import uuid
import math


class Connection:
    """Representa una conexión/línea entre dos dispositivos"""
    
    def __init__(self, device_a, device_b):
        """
        Inicializar una conexión entre dos dispositivos
        
        Args:
            device_a: Primer dispositivo a conectar
            device_b: Segundo dispositivo a conectar
        """
        self.id = str(uuid.uuid4())
        self.device_a = device_a
        self.device_b = device_b
        self.graphics_item = None
        self.is_selected = False
        
        # Colores para los estados
        self.normal_color = QColor(100, 149, 237)  # Azul acero
        self.selected_color = QColor(255, 165, 0)  # Naranja
        
    def create_graphics_item(self) -> 'ConnectionGraphicsItem':
        """Crear el item gráfico para la conexión"""
        if not self.graphics_item:
            self.graphics_item = ConnectionGraphicsItem(self)
        return self.graphics_item
    
    def calculate_distance(self) -> float:
        """Calcular la distancia euclidiana entre los dos dispositivos"""
        point_a, point_b = self.get_connection_points()
        dx = point_a.x() - point_b.x()
        dy = point_a.y() - point_b.y()
        return math.sqrt(dx * dx + dy * dy)
    
    def get_distance_text(self) -> str:
        """Obtener texto formateado de la distancia"""
        distance = self.calculate_distance()
        # Convertir a metros (asumiendo que las unidades del canvas son píxeles)
        # Escala: 1 pixel = 0.1 metros (ajustable según necesidades)
        distance_meters = distance * 0.1
        return f"{distance_meters:.1f}m"
    
    def get_connection_points(self) -> Tuple[QPointF, QPointF]:
        """
        Calcular los puntos de conexión entre los dos dispositivos
        Las líneas van de centro a centro de los dispositivos
        """
        # Obtener posiciones centrales de los dispositivos directamente
        point_a = QPointF(self.device_a.x, self.device_a.y)
        point_b = QPointF(self.device_b.x, self.device_b.y)
        
        return point_a, point_b
    
    def set_selected(self, selected: bool):
        """Cambiar el estado de selección de la conexión"""
        self.is_selected = selected
        if self.graphics_item:
            self.graphics_item.update_appearance()
    
    def get_other_device(self, device):
        """Obtener el otro dispositivo de la conexión"""
        if device == self.device_a:
            return self.device_b
        elif device == self.device_b:
            return self.device_a
        return None
    
    def contains_device(self, device) -> bool:
        """Verificar si la conexión contiene un dispositivo específico"""
        return device == self.device_a or device == self.device_b
    
    def __str__(self):
        return f"Connection({self.device_a.name} <-> {self.device_b.name})"


class ConnectionGraphicsItem(QGraphicsLineItem):
    """Item gráfico para renderizar una conexión en el canvas"""
    
    def __init__(self, connection: Connection):
        super().__init__()
        self.connection = connection
        
        # Configurar el item como seleccionable
        self.setFlags(QGraphicsItem.ItemIsSelectable)
        
        # Configurar Z-value para que se renderice debajo de los dispositivos
        self.setZValue(50)  # Dispositivos están en Z=100, conexiones en Z=50
        
        # Configurar el pen inicial con líneas más anchas
        self.normal_pen = QPen(connection.normal_color, 4)
        self.selected_pen = QPen(connection.selected_color, 5)
        
        # Color inicial para etiquetas (se actualizará con el tema)
        self.theme_label_color = QColor(100, 149, 237)  # Azul por defecto
        
        # Crear etiqueta de distancia
        self.distance_label = QGraphicsTextItem()
        self.distance_label.setParentItem(self)  # La etiqueta es hija de la línea
        self.setup_distance_label()
        
        # Establecer la línea inicial
        self.update_line()
        self.update_appearance()
    
    def setup_distance_label(self):
        """Configurar la etiqueta de distancia"""
        # Configurar fuente
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.distance_label.setFont(font)
        
        # Z-value para que aparezca por encima de la línea
        self.distance_label.setZValue(60)  # Mayor que la línea (50)
        
        # Actualizar texto y posición
        self.update_distance_label()
        self.update_appearance()
    
    def update_line(self):
        """Actualizar la geometría de la línea basada en las posiciones de los dispositivos"""
        start_point, end_point = self.connection.get_connection_points()
        self.setLine(start_point.x(), start_point.y(), end_point.x(), end_point.y())
        
        # Actualizar la etiqueta de distancia
        self.update_distance_label()
    
    def update_distance_label(self):
        """Actualizar texto y posición de la etiqueta de distancia"""
        # Actualizar texto con la distancia actual
        distance_text = self.connection.get_distance_text()
        self.distance_label.setPlainText(distance_text)
        
        # Calcular posición central de la línea
        line = self.line()
        mid_x = (line.x1() + line.x2()) / 2
        mid_y = (line.y1() + line.y2()) / 2
        
        # Obtener dimensiones del texto para centrarlo
        text_rect = self.distance_label.boundingRect()
        text_width = text_rect.width()
        text_height = text_rect.height()
        
        # Posicionar la etiqueta centrada sobre el punto medio de la línea
        # Offset hacia arriba para que esté por encima de la línea
        offset_y = -text_height - 5  # 5 píxeles de separación
        self.distance_label.setPos(
            mid_x - text_width / 2,
            mid_y + offset_y
        )
    
    def update_appearance(self):
        """Actualizar la apariencia visual de la línea y etiqueta"""
        if self.connection.is_selected or self.isSelected():
            self.setPen(self.selected_pen)
            # Cambiar color de la etiqueta cuando está seleccionada
            self.distance_label.setDefaultTextColor(self.connection.selected_color)
        else:
            self.setPen(self.normal_pen)
            # Color del tema para la etiqueta cuando no está seleccionada
            self.distance_label.setDefaultTextColor(self.theme_label_color)
    
    def update_theme_colors(self, dark_theme):
        """Actualizar colores según el tema actual"""
        if dark_theme:
            # Modo oscuro: etiquetas blancas
            self.theme_label_color = QColor(255, 255, 255)  # Blanco
        else:
            # Modo claro: etiquetas gris grafito
            self.theme_label_color = QColor(60, 60, 60)  # Gris grafito oscuro
        
        # Aplicar el cambio de color actualizando la apariencia
        self.update_appearance()
    
    def itemChange(self, change, value):
        """Manejar cambios en el item gráfico"""
        if change == QGraphicsItem.ItemSelectedChange:
            # Sincronizar con el estado de la conexión
            is_selected = bool(value)
            self.connection.set_selected(is_selected)
        
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        """Manejar clicks en la línea de conexión"""
        super().mousePressEvent(event)
