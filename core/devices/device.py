"""
Device (Dispositivo Base)
Clase base para todos los dispositivos de la red óptica
"""

from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtSvg import QSvgRenderer
import os
import uuid

class Device(QObject):
    """Clase base para dispositivos de red óptica"""
    
    # Señales
    position_changed = pyqtSignal(float, float)  # x, y
    properties_changed = pyqtSignal()
    selection_changed = pyqtSignal(bool)  # is_selected
    
    def __init__(self, device_type, name=None, x=0, y=0):
        super().__init__()
        
        # Identificador único
        self.id = str(uuid.uuid4())
        
        # Propiedades básicas
        self.device_type = device_type  # "OLT" o "ONU"
        self.name = name or f"{device_type}_{self.id[:8]}"
        self.x = x
        self.y = y
        
        # Propiedades visuales
        self.icon_size = 64  # Tamaño del icono en píxeles
        self.selected = False
        self.visible = True
        
        # Propiedades específicas del dispositivo (sobrescribir en subclases)
        self.properties = {}
        
        # Cache del icono renderizado
        self._icon_pixmap = None
    
    def set_position(self, x, y):
        """Establecer posición del dispositivo"""
        if self.x != x or self.y != y:
            self.x = x
            self.y = y
            self.position_changed.emit(x, y)
    
    def get_position(self):
        """Obtener posición del dispositivo"""
        return (self.x, self.y)
    
    def set_selected(self, selected):
        """Establecer estado de selección"""
        if self.selected != selected:
            self.selected = selected
            self.selection_changed.emit(selected)
    
    def is_selected(self):
        """Verificar si está seleccionado"""
        return self.selected
    
    def get_icon_path(self):
        """Obtener ruta del icono SVG (implementar en subclases)"""
        # Construir ruta al directorio de recursos
        current_file = os.path.abspath(__file__)
        devices_dir = os.path.dirname(current_file)    # core/devices/
        core_dir = os.path.dirname(devices_dir)        # core/
        project_root = os.path.dirname(core_dir)       # PonLab/
        devices_path = os.path.join(project_root, 'resources', 'devices')
        
        if self.device_type == "OLT":
            return os.path.join(devices_path, 'olt_icon.svg')
        elif self.device_type == "OLT_SDN":
            return os.path.join(devices_path, 'olt_sdn_icon.svg')
        elif self.device_type == "ONU":
            return os.path.join(devices_path, 'onu_icon.svg')
        
        return None
    
    def get_icon_pixmap(self, size=None):
        """Obtener pixmap del icono renderizado"""
        if size is None:
            size = self.icon_size
            
        # Si ya tenemos el pixmap en cache y el tamaño es el mismo, devolverlo
        if self._icon_pixmap and self._icon_pixmap.width() == size:
            return self._icon_pixmap
        
        icon_path = self.get_icon_path()
        if not icon_path or not os.path.exists(icon_path):
            return self._create_fallback_pixmap(size)
        
        # Renderizar SVG a pixmap con alta calidad
        try:
            renderer = QSvgRenderer(icon_path)
            
            # Crear pixmap con mayor resolución para mejor calidad
            scale_factor = 2.0  # Renderizar a 2x resolución
            high_res_size = int(size * scale_factor)
            
            pixmap = QPixmap(high_res_size, high_res_size)
            pixmap.fill(Qt.transparent)  # Fondo completamente transparente
            
            painter = QPainter(pixmap)
            # Configurar renderizado de alta calidad
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            
            renderer.render(painter)
            painter.end()
            
            # Escalar de vuelta al tamaño deseado con suavizado
            final_pixmap = pixmap.scaled(
                size, size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Guardar en cache
            self._icon_pixmap = final_pixmap
            return final_pixmap
            
        except Exception as e:
            print(f"Error renderizando icono SVG: {e}")
            return self._create_fallback_pixmap(size)
    
    def _create_fallback_pixmap(self, size):
        """Crear pixmap de respaldo si no se puede cargar el SVG"""
        pixmap = QPixmap(size, size)
        pixmap.fill()
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dibujar un rectángulo simple con el tipo de dispositivo
        if self.device_type == "OLT":
            painter.setBrush(QBrush(QColor(0, 0, 255)))  # Azul
        else:
            painter.setBrush(QBrush(QColor(0, 255, 0)))  # Verde
        
        painter.drawRoundedRect(4, 4, size-8, size-8, 8, 8)
        
        # Dibujar texto
        painter.setPen(QPen(QColor(255, 255, 255)))  # Blanco
        painter.drawText(pixmap.rect(), 0x0084, self.device_type)  # Qt.AlignCenter
        
        painter.end()
        return pixmap
    
    def set_icon_size(self, size):
        """Establecer nuevo tamaño del icono"""
        if size != self.icon_size and 32 <= size <= 128:
            self.icon_size = size
            self._icon_pixmap = None  # Limpiar cache para regenerar
            self.properties_changed.emit()
    
    def get_icon_size(self):
        """Obtener tamaño actual del icono"""
        return self.icon_size
    
    def get_bounds(self):
        """Obtener límites del dispositivo para detección de colisiones"""
        half_size = self.icon_size / 2
        return {
            'x': self.x - half_size,
            'y': self.y - half_size,
            'width': self.icon_size,
            'height': self.icon_size
        }
    
    def contains_point(self, x, y):
        """Verificar si un punto está dentro del dispositivo"""
        bounds = self.get_bounds()
        return (bounds['x'] <= x <= bounds['x'] + bounds['width'] and
                bounds['y'] <= y <= bounds['y'] + bounds['height'])
    
    def to_dict(self):
        """Serializar dispositivo a diccionario"""
        return {
            'id': self.id,
            'device_type': self.device_type,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'icon_size': self.icon_size,
            'visible': self.visible,
            'properties': self.properties
        }
    
    @classmethod
    def from_dict(cls, data):
        """Crear dispositivo desde diccionario"""
        device = cls(
            device_type=data['device_type'],
            name=data['name'],
            x=data['x'],
            y=data['y']
        )
        device.id = data['id']
        device.icon_size = data.get('icon_size', 64)
        device.visible = data.get('visible', True)
        device.properties = data.get('properties', {})
        return device
    
    def __str__(self):
        return f"{self.device_type}({self.name}) at ({self.x:.1f}, {self.y:.1f})"
