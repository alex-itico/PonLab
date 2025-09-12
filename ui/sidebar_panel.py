"""
SidebarPanel (Panel Lateral)
Panel lateral que contiene dispositivos y controles para el simulador de redes pasivas ópticas
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QPushButton, QSizePolicy, QApplication)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush, QDrag
from PyQt5.QtSvg import QSvgRenderer
from utils.constants import DEFAULT_SIDEBAR_WIDTH
from core.simulation_manager import SimulationManager
import os


class DeviceItem(QFrame):
    """Widget para representar un dispositivo individual"""
    
    device_clicked = pyqtSignal(str)  # Señal emitida al hacer click
    drag_started = pyqtSignal(str, str)  # device_name, device_type
    
    def __init__(self, device_name, device_type, parent=None):
        super().__init__(parent)
        self.device_name = device_name
        self.device_type = device_type
        self.drag_start_position = QPoint()
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz del dispositivo"""
        self.setFixedHeight(60)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Icono del dispositivo (placeholder)
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.setup_device_icon()
        layout.addWidget(self.icon_label)
        
        # Información del dispositivo
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Nombre del dispositivo
        name_label = QLabel(self.device_name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)
        
        # Tipo del dispositivo
        type_label = QLabel(self.device_type)
        type_font = QFont()
        type_font.setPointSize(8)
        type_label.setFont(type_font)
        type_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(type_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def setup_device_icon(self):
        """Cargar icono SVG para el dispositivo"""
        # Construir ruta correcta a los recursos
        # __file__ apunta a ui/sidebar_panel.py
        # Necesitamos ir a la carpeta padre (demo) y luego a resources/devices
        current_file = os.path.abspath(__file__)
        ui_dir = os.path.dirname(current_file)  # ui/
        project_root = os.path.dirname(ui_dir)  # demo/
        devices_path = os.path.join(project_root, 'resources', 'devices')
        
        # Determinar archivo de icono según tipo
        if self.device_type == "OLT":
            icon_file = "olt_icon.svg"
        elif self.device_type == "ONU":
            icon_file = "onu_icon.svg"
        else:
            # Fallback para otros tipos (crear icono simple)
            self.create_fallback_icon()
            return
        
        icon_path = os.path.join(devices_path, icon_file)
        
        # Verificar si existe el archivo SVG y cargarlo
        if os.path.exists(icon_path):
            self.load_svg_icon(icon_path)
        else:
            # Si no existe, crear icono fallback
            self.create_fallback_icon()
    
    def load_svg_icon(self, svg_path):
        """Cargar icono desde archivo SVG"""
        try:
            # Crear renderizador SVG
            renderer = QSvgRenderer(svg_path)
            
            if renderer.isValid():
                # Renderizar con alta calidad para evitar pixelado
                scale_factor = 2.0  # Renderizar a 2x resolución
                high_res_size = int(40 * scale_factor)
                
                # Crear pixmap para renderizar el SVG
                pixmap = QPixmap(high_res_size, high_res_size)
                pixmap.fill(Qt.transparent)  # Fondo completamente transparente
                
                # Renderizar SVG en el pixmap con alta calidad
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing, True)
                painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                renderer.render(painter)
                painter.end()
                
                # Escalar al tamaño final con suavizado
                final_pixmap = pixmap.scaled(
                    40, 40,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                self.icon_label.setPixmap(final_pixmap)
            else:
                self.create_fallback_icon()
                
        except Exception as e:
            print(f"Error cargando icono SVG {svg_path}: {e}")
            self.create_fallback_icon()
    
    def create_fallback_icon(self):
        """Crear icono fallback si no se puede cargar SVG"""
        # Crear un icono simple usando QPainter
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Color según tipo de dispositivo
        if self.device_type == "OLT":
            color = QColor(52, 152, 219)  # Azul
        elif self.device_type == "ONU":
            color = QColor(46, 204, 113)  # Verde
        else:
            color = QColor(149, 165, 166)  # Gris
        
        # Dibujar rectángulo redondeado
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color.lighter(180)))
        painter.drawRoundedRect(2, 2, 36, 36, 6, 6)
        
        # Dibujar texto inicial
        painter.setPen(QPen(Qt.white))
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, self.device_type[:2])
        
        painter.end()
        self.icon_label.setPixmap(pixmap)
    
    def mousePressEvent(self, event):
        """Manejar click del mouse"""
        if event.button() == Qt.LeftButton:
            self.device_clicked.emit(self.device_name)
            self.drag_start_position = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Manejar movimiento del mouse para iniciar drag"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if ((event.pos() - self.drag_start_position).manhattanLength() < 
            QApplication.startDragDistance()):
            return
        
        # Iniciar operación de drag
        self.start_drag()
    
    def start_drag(self):
        """Iniciar operación de drag & drop"""
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Establecer datos del dispositivo
        device_data = f"{self.device_name}|{self.device_type}"
        mime_data.setText(device_data)
        
        # Crear pixmap para mostrar durante el drag
        drag_pixmap = self.create_drag_pixmap()
        drag.setPixmap(drag_pixmap)
        drag.setHotSpot(QPoint(drag_pixmap.width()//2, drag_pixmap.height()//2))
        
        drag.setMimeData(mime_data)
        
        # Emitir señal de inicio de drag
        self.drag_started.emit(self.device_name, self.device_type)
        
        # Ejecutar drag
        drop_action = drag.exec_(Qt.CopyAction)
    
    def create_drag_pixmap(self):
        """Crear pixmap para mostrar durante el drag"""
        # Obtener el icono actual del dispositivo
        current_pixmap = self.icon_label.pixmap()
        
        if current_pixmap and not current_pixmap.isNull():
            # Crear una versión semi-transparente del icono para drag
            drag_pixmap = QPixmap(current_pixmap.size())
            drag_pixmap.fill(Qt.transparent)
            
            painter = QPainter(drag_pixmap)
            painter.setOpacity(0.7)  # Semi-transparente
            painter.drawPixmap(0, 0, current_pixmap)
            painter.end()
            
            return drag_pixmap
        else:
            # Crear pixmap de respaldo si no hay icono
            return self.create_fallback_drag_pixmap()
    
    def create_fallback_drag_pixmap(self):
        """Crear pixmap de respaldo para drag"""
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(0.7)
        
        # Color según tipo de dispositivo
        if self.device_type == "OLT":
            color = QColor(52, 152, 219)  # Azul
        elif self.device_type == "ONU":
            color = QColor(46, 204, 113)  # Verde
        else:
            color = QColor(149, 165, 166)  # Gris
        
        # Dibujar rectángulo redondeado
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color.lighter(180)))
        painter.drawRoundedRect(2, 2, 36, 36, 6, 6)
        
        # Dibujar texto inicial
        painter.setPen(QPen(Qt.white))
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, self.device_type[:2])
        
        painter.end()
        return pixmap
    
    def set_theme(self, dark_theme):
        """Actualizar tema del dispositivo"""
        if dark_theme:
            self.setStyleSheet("""
                DeviceItem {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 4px;
                }
                DeviceItem:hover {
                    background-color: #4a4a4a;
                    border-color: #4a90e2;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                DeviceItem {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                }
                DeviceItem:hover {
                    background-color: #f5f5f5;
                    border-color: #2196f3;
                }
                QLabel {
                    color: #333333;
                    background: transparent;
                }
            """)

class ConnectionItem(QFrame):
    """Widget para la herramienta de conexión con el mismo diseño que los dispositivos"""
    
    connection_mode_toggled = pyqtSignal(bool)  # Señal cuando se activa/desactiva
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.connection_mode = False
        self.dark_theme = False
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz de la herramienta de conexión"""
        self.setFixedHeight(60)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Icono de la herramienta
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.setup_connection_icon()
        layout.addWidget(self.icon_label)
        
        # Información de la herramienta
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Nombre de la herramienta
        name_label = QLabel("Añadir Conexiones")
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        name_label.setFont(name_font)
        info_layout.addWidget(name_label)
        
        # Descripción de la herramienta
        desc_label = QLabel("Conexión")
        desc_font = QFont()
        desc_font.setPointSize(8)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(desc_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def setup_connection_icon(self):
        """Cargar icono SVG para la herramienta de conexión"""
        try:
            # Seleccionar el archivo SVG según el tema
            if self.dark_theme:
                icon_filename = 'alicate_dark.svg'
            else:
                icon_filename = 'alicate_light.svg'
            
            # Construir ruta al archivo SVG
            current_file = os.path.abspath(__file__)
            ui_dir = os.path.dirname(current_file)
            project_root = os.path.dirname(ui_dir)
            icon_path = os.path.join(project_root, 'resources', 'devices', icon_filename)
            
            if os.path.exists(icon_path):
                self.load_svg_icon(icon_path)
            else:
                self.create_fallback_icon()
                
        except Exception as e:
            self.create_fallback_icon()
            print(f"Error cargando icono de conexión: {e}")
    
    def load_svg_icon(self, svg_path):
        """Cargar icono desde archivo SVG"""
        try:
            svg_renderer = QSvgRenderer(svg_path)
            
            # Crear pixmap con resolución alta (supersampling 2x)
            pixmap = QPixmap(80, 80)
            pixmap.fill(Qt.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            svg_renderer.render(painter)
            painter.end()
            
            # Escalar a tamaño final manteniendo la calidad
            final_pixmap = pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(final_pixmap)
            
        except Exception as e:
            self.create_fallback_icon()
            print(f"Error cargando SVG: {e}")
    
    def create_fallback_icon(self):
        """Crear icono fallback si no se puede cargar el SVG"""
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Color según tema
        if self.dark_theme:
            color = QColor(255, 255, 255)
        else:
            color = QColor(0, 0, 0)
        
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color))
        
        # Dibujar alicate simple
        painter.drawEllipse(16, 16, 8, 8)
        painter.drawLine(10, 10, 30, 30)
        painter.drawLine(30, 10, 10, 30)
        
        painter.end()
        self.icon_label.setPixmap(pixmap)
    
    def mousePressEvent(self, event):
        """Manejar click en la herramienta de conexión"""
        if event.button() == Qt.LeftButton:
            self.toggle_connection_mode()
        super().mousePressEvent(event)
    
    def toggle_connection_mode(self):
        """Toggle del modo conexión"""
        self.connection_mode = not self.connection_mode
        self.update_visual_state()
        self.connection_mode_toggled.emit(self.connection_mode)
        print(f"🔗 Modo conexión: {'ACTIVADO' if self.connection_mode else 'DESACTIVADO'}")
    
    def set_connection_mode(self, enabled):
        """Establecer el modo conexión programáticamente"""
        if self.connection_mode != enabled:
            self.connection_mode = enabled
            self.update_visual_state()
    
    def update_visual_state(self):
        """Actualizar el estado visual según el modo activo"""
        self.set_theme(self.dark_theme)  # Re-aplicar tema con estado actual
    
    def is_connection_mode_active(self):
        """Verificar si el modo conexión está activo"""
        return self.connection_mode
    
    def set_theme(self, dark_theme):
        """Actualizar tema de la herramienta de conexión"""
        self.dark_theme = dark_theme
        
        if self.connection_mode:
            # Estado activo (verde)
            self.setStyleSheet("""
                ConnectionItem {
                    background-color: #4CAF50;
                    border: 2px solid #45a049;
                    border-radius: 4px;
                }
                ConnectionItem:hover {
                    background-color: #45a049;
                    border-color: #3d8b40;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
            """)
        elif dark_theme:
            # Modo oscuro
            self.setStyleSheet("""
                ConnectionItem {
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 4px;
                }
                ConnectionItem:hover {
                    background-color: #4a4a4a;
                    border-color: #4a90e2;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
            """)
        else:
            # Modo claro
            self.setStyleSheet("""
                ConnectionItem {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                }
                ConnectionItem:hover {
                    background-color: #f5f5f5;
                    border-color: #2196f3;
                }
                QLabel {
                    color: #333333;
                    background: transparent;
                }
            """)
        
        # Actualizar icono según el tema
        self.setup_connection_icon()


class SidebarPanel(QWidget):
    """Panel lateral con dispositivos y controles"""
    
    device_selected = pyqtSignal(str, str)  # nombre_dispositivo, tipo_dispositivo
    connection_mode_toggled = pyqtSignal(bool)  # True cuando se activa modo conexión
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_theme = False
        self.device_items = []
        self.connection_item = None  # Referencia al item de conexión
        self.canvas = None  # Referencia al canvas
        
        # Crear gestor de simulación
        self.simulation_manager = SimulationManager()
        
        self.setup_ui()
        self.populate_devices()
    
    def setup_ui(self):
        """Configurar la interfaz del sidebar"""
        # Configurar widget principal
        self.setFixedWidth(DEFAULT_SIDEBAR_WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Título del panel
        title_label = QLabel("🔧 Dispositivos")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(40)
        main_layout.addWidget(title_label)
        
        # Área de scroll para dispositivos y herramientas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget contenedor de dispositivos y herramientas
        self.devices_widget = QWidget()
        self.devices_layout = QVBoxLayout(self.devices_widget)
        self.devices_layout.setContentsMargins(5, 5, 5, 5)
        self.devices_layout.setSpacing(5)
        self.devices_layout.addStretch()  # Stretch al final para alinear arriba
        
        scroll_area.setWidget(self.devices_widget)
        main_layout.addWidget(scroll_area)
        
        # Información del panel
        info_label = QLabel("Arrastra dispositivos al canvas\npara crear la topología")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(8)
        info_label.setFont(info_font)
        info_label.setFixedHeight(40)
        main_layout.addWidget(info_label)
        

        self.setLayout(main_layout)
        
        # Aplicar tema inicial
        self.set_theme(self.dark_theme)
    
    def setup_connection_tool(self):
        """Configurar la herramienta de conexión"""
        # Crear el item de conexión con las mismas dimensiones que los dispositivos
        self.connection_item = ConnectionItem()
        self.connection_item.connection_mode_toggled.connect(self.on_connection_mode_toggled)
        self.connection_item.set_theme(self.dark_theme)
        
        # Agregar al layout antes del stretch
        self.devices_layout.insertWidget(
            self.devices_layout.count() - 1, 
            self.connection_item
        )
    
    def on_connection_mode_toggled(self, enabled):
        """Manejar cambio en el modo conexión"""
        # Emitir la señal hacia arriba
        self.connection_mode_toggled.emit(enabled)
    
    def is_connection_mode_active(self):
        """Verificar si el modo conexión está activo"""
        if self.connection_item:
            return self.connection_item.is_connection_mode_active()
        return False
    
    def deactivate_connection_mode(self):
        """Desactivar el modo conexión"""
        if self.connection_item and self.connection_item.is_connection_mode_active():
            self.connection_item.set_connection_mode(False)
    
    def populate_devices(self):
        """Poblar el panel con dispositivos predefinidos y herramientas"""
        # Lista de dispositivos disponibles
        devices = [
            ("Terminal de Linea Óptica", "OLT"),      # nombre_mostrado, tipo_para_icono
            ("Unidad de Red Óptica", "ONU"), # nombre_mostrado, tipo_para_icono
        ]
        
        # Crear widgets de dispositivos
        for device_name, device_type in devices:
            device_item = DeviceItem(device_name, device_type)
            device_item.device_clicked.connect(self.on_device_clicked)
            device_item.set_theme(self.dark_theme)
            
            # Insertar antes del stretch
            self.devices_layout.insertWidget(
                self.devices_layout.count() - 1, 
                device_item
            )
            self.device_items.append(device_item)
        
        # Agregar herramienta de conexión después de los dispositivos
        self.setup_connection_tool()
    
    def on_device_clicked(self, device_name):
        """Manejar click en dispositivo"""
        # Encontrar el tipo de dispositivo
        device_type = None
        for item in self.device_items:
            if item.device_name == device_name:
                device_type = item.device_type
                break
        
        if device_type:
            self.device_selected.emit(device_name, device_type)
            print(f"Dispositivo seleccionado: {device_name} ({device_type})")
    
    def set_theme(self, dark_theme):
        """Cambiar tema del sidebar"""
        self.dark_theme = dark_theme
        
        if dark_theme:
            self.setStyleSheet("""
                SidebarPanel {
                    background-color: #2b2b2b;
                    border-right: 2px solid #555555;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
                QScrollArea {
                    background-color: #2b2b2b;
                    border: none;
                }
                QScrollBar:vertical {
                    background-color: #404040;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #666666;
                    min-height: 20px;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                SidebarPanel {
                    background-color: #f8f9fa;
                    border-right: 2px solid #d0d0d0;
                }
                QLabel {
                    color: #333333;
                    background: transparent;
                }
                QScrollArea {
                    background-color: #f8f9fa;
                    border: none;
                }
                QScrollBar:vertical {
                    background-color: #f0f0f0;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #c0c0c0;
                    min-height: 20px;
                    border-radius: 6px;
                }
            """)
        
        # Actualizar tema de todos los dispositivos
        for device_item in self.device_items:
            device_item.set_theme(dark_theme)
        
        # Actualizar tema del item de conexión
        if hasattr(self, 'connection_item') and self.connection_item:
            self.connection_item.set_theme(dark_theme)
    
    def add_device(self, device_name, device_type):
        """Agregar un nuevo dispositivo al panel"""
        device_item = DeviceItem(device_name, device_type)
        device_item.device_clicked.connect(self.on_device_clicked)
        device_item.set_theme(self.dark_theme)
        
        # Insertar antes del stretch
        self.devices_layout.insertWidget(
            self.devices_layout.count() - 1, 
            device_item
        )
        self.device_items.append(device_item)
    
    def clear_devices(self):
        """Limpiar todos los dispositivos"""
        for device_item in self.device_items:
            device_item.setParent(None)
        self.device_items.clear()
    
    def set_canvas_reference(self, canvas):
        """Establecer referencia al canvas para acceso a dispositivos"""
        self.canvas = canvas
        if canvas and hasattr(canvas, 'device_manager'):
            self.simulation_manager.set_device_manager(canvas.device_manager)
    
    def _handle_simulation_start(self, params):
        """Iniciar simulación usando el SimulationManager"""
        if not self.canvas or not hasattr(self.canvas, 'device_manager'):
            print("❌ No hay canvas o device manager disponible")
            return
        
        try:
            # Inicializar simulación con parámetros
            if self.simulation_manager.initialize_simulation(params):
                # Iniciar simulación
                success = self.simulation_manager.start_simulation()
                if not success:
                    print("❌ Error al iniciar la simulación")
                    self.sim_panel.on_simulation_stopped()
            else:
                print("❌ Error al inicializar la simulación")
                self.sim_panel.on_simulation_stopped()
                
        except Exception as e:
            print(f"❌ Error al iniciar simulación: {e}")
            self.sim_panel.on_simulation_stopped()
    
    def _handle_simulation_stop(self):
        """Detener simulación en curso"""
        try:
            self.simulation_manager.stop_simulation()
        except Exception as e:
            print(f"❌ Error al detener simulación: {e}")
    
    def cleanup(self):
        """Limpiar recursos del sidebar panel"""
        print("🧹 Sidebar panel limpiado")
