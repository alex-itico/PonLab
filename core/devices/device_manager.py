"""
Device Manager
Gestiona dispositivos en el canvas y sus operaciones
"""

from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem
from PyQt5.QtGui import QPen, QBrush, QColor, QFont
from .device_types import create_device
from ..connections.connection_points import ConnectionPointsManager
import json

class DeviceGraphicsItem(QGraphicsPixmapItem):
    """Item gráfico para representar un dispositivo en el canvas"""
    
    def __init__(self, device, parent=None):
        super().__init__(parent)
        
        self.device = device
        self.label_item = None  # Etiqueta de texto
        self.connection_points_manager = None  # Gestor de puntos de conexión
        self.setup_graphics()
        
        # Conectar señales del dispositivo
        self.device.position_changed.connect(self.update_position)
        self.device.properties_changed.connect(self.update_graphics)
        self.device.selection_changed.connect(self.on_selection_changed)
    
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
        
        # Crear gestor de puntos de conexión
        self.connection_points_manager = ConnectionPointsManager(self)
    
    def create_label(self):
        """Crear etiqueta de texto para el dispositivo"""
        if self.label_item is None:
            # Verificar si el dispositivo es personalizado
            display_name = self.device.name
            if hasattr(self.device, 'is_custom') and self.device.is_custom:
                display_name = f"{self.device.name} ⚙"  # Añadir indicador custom
            
            self.label_item = QGraphicsTextItem(display_name, self)
            
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
                print(f"🎨 Tema encontrado: {'oscuro' if canvas.dark_theme else 'claro'}, color: {'blanco' if canvas.dark_theme else 'negro'}")
            else:
                # Por defecto asumir tema claro (negro para texto)
                text_color = QColor(0, 0, 0)  # Negro por defecto (tema claro)
                print("WARNING Canvas no encontrado, usando color negro por defecto")
            
            self.label_item.setDefaultTextColor(text_color)
    
    def set_label_color_direct(self, dark_theme):
        """Establecer color de etiqueta directamente según tema"""
        if self.label_item:
            if dark_theme:
                text_color = QColor(255, 255, 255)  # Blanco para tema oscuro
            else:
                text_color = QColor(0, 0, 0)        # Negro para tema claro
            
            self.label_item.setDefaultTextColor(text_color)
            print(f"Color de etiqueta establecido: {'blanco' if dark_theme else 'negro'}")
    
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
            # Verificar si el dispositivo es personalizado
            display_name = self.device.name
            if hasattr(self.device, 'is_custom') and self.device.is_custom:
                display_name = f"{self.device.name} ⚙"  # Añadir indicador custom
            
            self.label_item.setPlainText(display_name)
            self.update_label_color()  # Actualizar color también
            self.update_label_position()
        
        # Actualizar posiciones de los connection points
        if self.connection_points_manager:
            self.connection_points_manager.update_positions()
    
    def on_selection_changed(self, is_selected):
        """Manejar cambio de selección del dispositivo"""
        if self.connection_points_manager:
            if is_selected:
                self.connection_points_manager.show_points()
            else:
                self.connection_points_manager.hide_points()
    
    def itemChange(self, change, value):
        """Manejar cambios en el item gráfico (incluyendo selección)"""
        if change == QGraphicsItem.ItemPositionChange:
            # Actualizar posición del dispositivo cuando se mueve el item gráfico
            new_pos = value
            self.device.set_position(new_pos.x(), new_pos.y())
            
            # Actualizar conexiones que involucren este dispositivo
            self._update_device_connections()
            
        elif change == QGraphicsItem.ItemSelectedChange:
            # Manejar cambios de selección automáticamente
            is_selected = bool(value)
            
            # Sincronizar con el estado del dispositivo
            self.device.set_selected(is_selected)
            
            # Manejar vértices de conexión
            if self.connection_points_manager:
                if is_selected:
                    self.connection_points_manager.show_points()
                else:
                    self.connection_points_manager.hide_points()
        
        return super().itemChange(change, value)
    
    def _update_device_connections(self):
        """Actualizar las conexiones relacionadas con este dispositivo"""
        # Buscar el canvas para obtener el connection manager
        canvas = None
        for view in self.scene().views():
            if hasattr(view, 'connection_manager'):
                canvas = view
                break
        
        if canvas and hasattr(canvas, 'connection_manager'):
            # Obtener conexiones que involucren este dispositivo
            connections = canvas.connection_manager.get_connections_for_device(self.device)
            for connection in connections:
                if connection.graphics_item:
                    connection.graphics_item.update_line()
    
    def update_theme(self, dark_theme=False):
        """Actualizar tema de los elementos gráficos"""
        # Actualizar tema de la etiqueta
        self.update_label_color()
        
        # Actualizar tema de los connection points
        if self.connection_points_manager:
            self.connection_points_manager.update_theme(dark_theme)
    
    def mousePressEvent(self, event):
        """Manejar click del mouse para selección o conexión"""
        if event.button() == Qt.LeftButton:
            # Buscar el canvas
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
            
            if canvas:
                # Verificar si estamos en modo conexión
                if hasattr(canvas, 'handle_device_click_for_connection'):
                    connection_handled = canvas.handle_device_click_for_connection(self.device)
                    if connection_handled:
                        # Si se manejó la conexión, no hacer selección normal
                        super().mousePressEvent(event)
                        return
                
                # Selección normal
                if hasattr(canvas, 'device_manager'):
                    canvas.device_manager.select_device_by_object(self.device)
                else:
                    # Fallback: selección directa
                    was_selected = self.device.is_selected()
                    self.device.set_selected(not was_selected)
            else:
                # Fallback: selección directa
                was_selected = self.device.is_selected()
                self.device.set_selected(not was_selected)
            
        super().mousePressEvent(event)
    
    def cleanup(self):
        """Limpiar recursos del item gráfico"""
        if self.connection_points_manager:
            self.connection_points_manager.cleanup()
            self.connection_points_manager = None


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
        self.canvas = None  # Referencia al canvas (se asigna después)
        self.devices = {}  # ID -> Device
        self.graphics_items = {}  # ID -> DeviceGraphicsItem
        
        # Contadores para nombres automáticos
        self.device_counters = {
            'OLT': 0,
            'ONU': 0
        }
        
        # Dispositivo actualmente seleccionado
        self.selected_device = None
    
    def set_canvas_reference(self, canvas):
        """Establecer referencia al canvas"""
        self.canvas = canvas
    
    def add_device(self, device_type, x, y, name=None, device_name=None):
        """Agregar nuevo dispositivo al canvas
        
        Args:
            device_type: Tipo de dispositivo (OLT, ONU, CUSTOM_OLT, etc.)
            x, y: Coordenadas de posición
            name: Nombre automático generado
            device_name: Nombre personalizado del dispositivo (para custom devices)
        """
        try:
            # Para dispositivos personalizados, usar el device_name si se proporciona
            if device_type.startswith('CUSTOM_') and device_name:
                final_name = device_name
            elif name is None:
                # Generar nombre automático si no se proporciona
                # Para OLT_SDN, usar el contador de OLT
                counter_type = "OLT" if device_type == "OLT_SDN" else device_type
                self.device_counters[counter_type] += 1
                final_name = f"{device_type}_{self.device_counters[counter_type]}"
            else:
                final_name = name
            
            # Crear dispositivo
            device = create_device(device_type, final_name, x, y)
            
            # Crear item gráfico
            graphics_item = DeviceGraphicsItem(device)
            
            # Inicializar tema del nuevo dispositivo usando referencia directa
            if self.canvas and hasattr(self.canvas, 'dark_theme'):
                graphics_item.set_label_color_direct(self.canvas.dark_theme)
            else:
                # Fallback: intentar el método tradicional
                graphics_item.update_label_color()
            
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
            import traceback
            traceback.print_exc()
            return None
    
    def remove_device(self, device_id):
        """Remover dispositivo del canvas"""
        if device_id in self.devices:
            device = self.devices[device_id]
            
            # Notificar al connection manager antes de eliminar el dispositivo
            # Buscar canvas para obtener connection_manager
            canvas = None
            for view in self.canvas_scene.views():
                if hasattr(view, 'connection_manager'):
                    canvas = view
                    break
            
            if canvas and hasattr(canvas, 'connection_manager'):
                canvas.connection_manager.remove_connections_for_device(device)
            
            # Obtener item gráfico y limpiar recursos
            graphics_item = self.graphics_items[device_id]
            graphics_item.cleanup()  # Limpiar connection points
            
            # Remover item gráfico de la escena
            self.canvas_scene.removeItem(graphics_item)
            
            # Limpiar referencias
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
        if device_type == "OLT":
            # Para OLT, incluir tanto OLT como OLT_SDN
            return [device for device in self.devices.values() 
                    if device.device_type in ["OLT", "OLT_SDN"]]
        else:
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
                # Extraer custom_data si existe
                custom_data = device_data.get('custom_data', None)
                device_type = device_data['device_type']
                
                # Detectar si es un dispositivo custom (por device_type o por presencia de custom_data)
                is_custom_olt = (device_type == 'CUSTOM_OLT') or (device_type == 'OLT' and custom_data and custom_data.get('type') == 'CUSTOM_OLT')
                is_custom_onu = (device_type == 'CUSTOM_ONU') or (device_type == 'ONU' and custom_data and custom_data.get('type') == 'CUSTOM_ONU')
                
                if is_custom_olt:
                    # Dispositivo OLT personalizado
                    from core.devices.device_types import CustomOLT
                    device = CustomOLT(
                        device_data['name'],
                        device_data['x'],
                        device_data['y'],
                        custom_data
                    )
                elif is_custom_onu:
                    # Dispositivo ONU personalizado
                    from core.devices.device_types import CustomONU
                    device = CustomONU(
                        device_data['name'],
                        device_data['x'],
                        device_data['y'],
                        custom_data
                    )
                else:
                    # Dispositivos normales
                    device = create_device(
                        device_type,
                        device_data['name'],
                        device_data['x'],
                        device_data['y']
                    )
                
                # Restaurar propiedades comunes
                device.id = device_id
                device.icon_size = device_data.get('icon_size', 64)
                device.visible = device_data.get('visible', True)
                device.properties = device_data.get('properties', {})
                
                # Restaurar custom_color si existe (para dispositivos custom)
                if 'custom_color' in device_data:
                    device.custom_color = device_data['custom_color']
                
                # Crear item gráfico
                graphics_item = DeviceGraphicsItem(device)
                
                # Inicializar tema del dispositivo cargado usando referencia directa
                if self.canvas and hasattr(self.canvas, 'dark_theme'):
                    graphics_item.set_label_color_direct(self.canvas.dark_theme)
                else:
                    # Fallback: intentar el método tradicional
                    graphics_item.update_label_color()
                
                # Agregar a gestión
                self.devices[device_id] = device
                self.graphics_items[device_id] = graphics_item
                self.canvas_scene.addItem(graphics_item)
                
                print(f"✅ Dispositivo cargado: {device.name} (Tipo: {device.device_type}, Custom: {hasattr(device, 'is_custom')})")
                
            except Exception as e:
                print(f"❌ Error importando dispositivo {device_id}: {e}")
                import traceback
                traceback.print_exc()
        
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
        """Actualizar colores de todas las etiquetas de dispositivos y connection points"""
        # Buscar información del tema si no se proporciona
        if dark_theme is None:
            # Intentar obtener tema del canvas
            for graphics_item in self.graphics_items.values():
                if graphics_item.scene():
                    for view in graphics_item.scene().views():
                        if hasattr(view, 'dark_theme'):
                            dark_theme = view.dark_theme
                            break
                    break
            if dark_theme is None:
                dark_theme = False  # Default
        
        for graphics_item in self.graphics_items.values():
            # Actualizar etiquetas
            if hasattr(graphics_item, 'update_label_color'):
                graphics_item.update_label_color()
            # Actualizar connection points
            if hasattr(graphics_item, 'update_theme'):
                graphics_item.update_theme(dark_theme)
    
    def update_device_properties(self, device_id, new_properties):
        """Actualizar propiedades de un dispositivo específico"""
        try:
            if device_id not in self.devices:
                print(f"❌ Dispositivo {device_id} no encontrado")
                return False
            
            device = self.devices[device_id]
            
            # Actualizar propiedades del dispositivo
            if 'name' in new_properties:
                device.name = new_properties['name']
            
            if 'x' in new_properties and 'y' in new_properties:
                device.set_position(new_properties['x'], new_properties['y'])
            elif 'x' in new_properties:
                device.set_position(new_properties['x'], device.y)
            elif 'y' in new_properties:
                device.set_position(device.x, new_properties['y'])
            
            # Actualizar otras propiedades si existen
            for key, value in new_properties.items():
                if key not in ['name', 'x', 'y']:
                    # Verificar si es una propiedad específica del dispositivo (como transmission_rate)
                    if hasattr(device, 'properties') and key in device.properties:
                        device.properties[key] = value
                        # Sincronizar con PON core si es necesario
                        if hasattr(device, 'update_property'):
                            device.update_property(key, value)
                        print(f"📝 Propiedad {key} actualizada a: {value}")
                    elif hasattr(device, key):
                        setattr(device, key, value)
            
            # Actualizar gráficos
            if device_id in self.graphics_items:
                graphics_item = self.graphics_items[device_id]
                graphics_item.update_graphics()
            
            # Emitir señal de cambio
            self.devices_changed.emit()
            
            print(f"✅ Propiedades actualizadas para dispositivo {device_id}: {new_properties}")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando propiedades del dispositivo {device_id}: {e}")
            return False
