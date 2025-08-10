"""
Device Manager
Gestiona dispositivos en el canvas y sus operaciones
"""

from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QPen, QBrush, QColor, QFont
from .device_types import create_device
import json

class DeviceGraphicsItem(QGraphicsPixmapItem):
    """Item gráfico para representar un dispositivo en el canvas"""
    
    def __init__(self, device, parent=None):
        super().__init__(parent)
        
        self.device = device
        self.label_item = None  # Etiqueta de texto
        self.setup_graphics()
        
        # Conectar señales del dispositivo
        self.device.position_changed.connect(self.update_position)
        self.device.properties_changed.connect(self.update_graphics)
    
    def setup_graphics(self):
        """Configurar propiedades gráficas del item"""
        # Establecer pixmap del icono
        pixmap = self.device.get_icon_pixmap()
        self.setPixmap(pixmap)
        
        # Configurar posición (centrar el icono en las coordenadas del dispositivo)
        self.setOffset(-pixmap.width()/2, -pixmap.height()/2)
        self.setPos(self.device.x, self.device.y)
        
        # Habilitar selección y movimiento
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        
        # Z-value para superposición
        self.setZValue(100)  # Encima de la cuadrícula
        
        # Crear etiqueta
        self.create_label()
    
    def create_label(self):
        """Crear etiqueta de texto para el dispositivo"""
        if self.label_item is None:
            self.label_item = QGraphicsTextItem(self.device.name, self)
            
            # Configurar fuente
            font = QFont("Arial", 8)
            font.setBold(True)
            self.label_item.setFont(font)
            
            # Z-value para que aparezca encima
            self.label_item.setZValue(101)
            
        # Configurar color apropiado
        self.update_label_color()
        
        # Actualizar posición de la etiqueta
        self.update_label_position()
    
    def update_label_color(self):
        """Actualizar color de la etiqueta según el tema"""
        if self.label_item:
            # Buscar el canvas para obtener información del tema
            canvas = None
            scene_parent = self.scene().parent() if self.scene() else None
            if hasattr(scene_parent, 'dark_theme'):
                canvas = scene_parent
            else:
                # Buscar en views de la escena
                if self.scene():
                    for view in self.scene().views():
                        if hasattr(view, 'dark_theme'):
                            canvas = view
                            break
            
            # Determinar color basado en el tema
            if canvas and hasattr(canvas, 'dark_theme'):
                if canvas.dark_theme:
                    text_color = QColor(255, 255, 255)  # Blanco para tema oscuro
                else:
                    text_color = QColor(0, 0, 0)        # Negro para tema claro
            else:
                text_color = QColor(255, 255, 255)      # Por defecto blanco
            
            self.label_item.setDefaultTextColor(text_color)
    
    def update_label_position(self):
        """Actualizar posición de la etiqueta"""
        if self.label_item:
            pixmap = self.pixmap()
            device_height = pixmap.height()
            
            # Posicionar la etiqueta debajo del dispositivo
            label_rect = self.label_item.boundingRect()
            x = -label_rect.width() / 2  # Centrar horizontalmente
            y = device_height / 2 + 2    # Debajo del dispositivo con margen
            
            self.label_item.setPos(x, y)
    
    def update_position(self, x, y):
        """Actualizar posición gráfica cuando cambia la posición del dispositivo"""
        self.setPos(x, y)
    
    def update_graphics(self):
        """Actualizar apariencia gráfica"""
        pixmap = self.device.get_icon_pixmap()
        self.setPixmap(pixmap)
        
        # Recentrar el offset después del cambio de tamaño
        self.setOffset(-pixmap.width()/2, -pixmap.height()/2)
        
        # Actualizar etiqueta
        if self.label_item:
            self.label_item.setPlainText(self.device.name)
            self.update_label_color()  # Actualizar color también
            self.update_label_position()
    
    def mousePressEvent(self, event):
        """Manejar click del mouse para selección"""
        if event.button() == Qt.LeftButton:
            # Buscar el device manager en el canvas
            canvas = None
            scene_parent = self.scene().parent()
            if hasattr(scene_parent, 'device_manager'):
                canvas = scene_parent
            else:
                # Buscar en views de la escena
                for view in self.scene().views():
                    if hasattr(view, 'device_manager'):
                        canvas = view
                        break
            
            if canvas and hasattr(canvas, 'device_manager'):
                canvas.device_manager.select_device_by_object(self.device)
            else:
                # Fallback: selección directa
                was_selected = self.device.is_selected()
                self.device.set_selected(not was_selected)
            
        super().mousePressEvent(event)
    
    def itemChange(self, change, value):
        """Manejar cambios en el item gráfico"""
        if change == QGraphicsItem.ItemPositionChange:
            # Actualizar posición del dispositivo cuando se mueve el item gráfico
            new_pos = value
            self.device.set_position(new_pos.x(), new_pos.y())
        
        return super().itemChange(change, value)


class DeviceManager(QObject):
    """Gestor de dispositivos en el canvas"""
    
    # Señales
    device_added = pyqtSignal(object)  # Device object
    device_removed = pyqtSignal(str)   # Device ID
    device_selected = pyqtSignal(object)  # Device object
    devices_changed = pyqtSignal()
    
    def __init__(self, canvas_scene):
        super().__init__()
        
        self.canvas_scene = canvas_scene
        self.devices = {}  # ID -> Device
        self.graphics_items = {}  # ID -> DeviceGraphicsItem
        
        # Contadores para nombres automáticos
        self.device_counters = {
            'OLT': 0,
            'ONU': 0
        }
        
        # Dispositivo actualmente seleccionado
        self.selected_device = None
    
    def add_device(self, device_type, x, y, name=None):
        """Agregar nuevo dispositivo al canvas"""
        try:
            # Generar nombre automático si no se proporciona
            if name is None:
                self.device_counters[device_type] += 1
                name = f"{device_type}_{self.device_counters[device_type]}"
            
            # Crear dispositivo
            device = create_device(device_type, name, x, y)
            
            # Crear item gráfico
            graphics_item = DeviceGraphicsItem(device)
            
            # Agregar al diccionario y escena
            self.devices[device.id] = device
            self.graphics_items[device.id] = graphics_item
            self.canvas_scene.addItem(graphics_item)
            
            # Emitir señal
            self.device_added.emit(device)
            self.devices_changed.emit()
            
            return device
            
        except Exception as e:
            print(f"Error agregando dispositivo: {e}")
            return None
    
    def remove_device(self, device_id):
        """Remover dispositivo del canvas"""
        if device_id in self.devices:
            # Remover item gráfico de la escena
            graphics_item = self.graphics_items[device_id]
            self.canvas_scene.removeItem(graphics_item)
            
            # Limpiar referencias
            device = self.devices[device_id]
            if device == self.selected_device:
                self.selected_device = None
            
            # Remover de diccionarios
            del self.devices[device_id]
            del self.graphics_items[device_id]
            
            # Emitir señales
            self.device_removed.emit(device_id)
            self.devices_changed.emit()
            
            return True
        
        return False
    
    def get_device(self, device_id):
        """Obtener dispositivo por ID"""
        return self.devices.get(device_id)
    
    def get_all_devices(self):
        """Obtener todos los dispositivos"""
        return list(self.devices.values())
    
    def get_devices_by_type(self, device_type):
        """Obtener dispositivos por tipo"""
        return [device for device in self.devices.values() 
                if device.device_type == device_type]
    
    def select_device(self, device_id):
        """Seleccionar dispositivo"""
        if device_id in self.devices:
            # Deseleccionar dispositivo anterior
            if self.selected_device:
                self.selected_device.set_selected(False)
            
            # Seleccionar nuevo dispositivo
            device = self.devices[device_id]
            device.set_selected(True)
            self.selected_device = device
            
            # Emitir señal
            self.device_selected.emit(device)
            
            return True
        
        return False
    
    def select_device_by_object(self, device):
        """Seleccionar dispositivo por objeto"""
        # Deseleccionar dispositivo anterior
        if self.selected_device and self.selected_device != device:
            self.selected_device.set_selected(False)
        
        # Seleccionar nuevo dispositivo
        device.set_selected(True)
        self.selected_device = device
        
        # Emitir señal
        self.device_selected.emit(device)
    
    def deselect_all(self):
        """Deseleccionar todos los dispositivos"""
        if self.selected_device:
            self.selected_device.set_selected(False)
            self.selected_device = None
    
    def get_selected_device(self):
        """Obtener dispositivo seleccionado"""
        return self.selected_device
    
    def move_device(self, device_id, x, y):
        """Mover dispositivo a nueva posición"""
        if device_id in self.devices:
            device = self.devices[device_id]
            device.set_position(x, y)
            return True
        
        return False
    
    def get_device_at_position(self, x, y):
        """Obtener dispositivo en posición específica"""
        for device in self.devices.values():
            if device.contains_point(x, y):
                return device
        
        return None
    
    def snap_to_grid(self, device_id, grid_size):
        """Ajustar dispositivo a la cuadrícula"""
        if device_id in self.devices:
            device = self.devices[device_id]
            
            # Calcular posición ajustada a la cuadrícula
            snapped_x = round(device.x / grid_size) * grid_size
            snapped_y = round(device.y / grid_size) * grid_size
            
            device.set_position(snapped_x, snapped_y)
            return True
        
        return False
    
    def clear_all_devices(self):
        """Limpiar todos los dispositivos"""
        # Remover todos los items gráficos
        for graphics_item in self.graphics_items.values():
            self.canvas_scene.removeItem(graphics_item)
        
        # Limpiar diccionarios
        self.devices.clear()
        self.graphics_items.clear()
        self.selected_device = None
        
        # Resetear contadores
        self.device_counters = {
            'OLT': 0,
            'ONU': 0
        }
        
        # Emitir señal
        self.devices_changed.emit()
    
    def export_devices_data(self):
        """Exportar datos de dispositivos a diccionario"""
        return {
            device_id: device.to_dict() 
            for device_id, device in self.devices.items()
        }
    
    def import_devices_data(self, devices_data):
        """Importar datos de dispositivos desde diccionario"""
        # Limpiar dispositivos existentes
        self.clear_all_devices()
        
        # Crear dispositivos desde datos
        for device_id, device_data in devices_data.items():
            try:
                device = create_device(
                    device_data['device_type'],
                    device_data['name'],
                    device_data['x'],
                    device_data['y']
                )
                
                # Restaurar propiedades
                device.id = device_id
                device.icon_size = device_data.get('icon_size', 64)
                device.visible = device_data.get('visible', True)
                device.properties = device_data.get('properties', {})
                
                # Crear item gráfico
                graphics_item = DeviceGraphicsItem(device)
                
                # Agregar a gestión
                self.devices[device_id] = device
                self.graphics_items[device_id] = graphics_item
                self.canvas_scene.addItem(graphics_item)
                
            except Exception as e:
                print(f"Error importando dispositivo {device_id}: {e}")
        
        # Emitir señal de cambio
        self.devices_changed.emit()
    
    def get_device_count(self):
        """Obtener número total de dispositivos"""
        return len(self.devices)
    
    def get_device_stats(self):
        """Obtener estadísticas de dispositivos"""
        olts = self.get_devices_by_type("OLT")
        onus = self.get_devices_by_type("ONU")
        
        return {
            'total_devices': len(self.devices),
            'olt_count': len(olts),
            'onu_count': len(onus)
        }
    
    def update_label_colors(self, dark_theme=None):
        """Actualizar colores de todas las etiquetas de dispositivos"""
        for graphics_item in self.graphics_items.values():
            if hasattr(graphics_item, 'update_label_color'):
                graphics_item.update_label_color()
