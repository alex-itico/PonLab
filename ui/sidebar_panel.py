"""
SidebarPanel (Panel Lateral)
Panel lateral que contiene dispositivos y controles para el simulador de redes pasivas ópticas
Con pestañas colapsables por categorías (OLT, ONU, Herramientas)
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QFrame, QPushButton, QSizePolicy, QApplication, 
                             QGroupBox, QFormLayout, QLineEdit, QDoubleSpinBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint, QPropertyAnimation, QEasingCurve, QByteArray
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QBrush, QDrag
from PyQt5.QtSvg import QSvgRenderer
from utils.constants import DEFAULT_SIDEBAR_WIDTH
from utils.translation_manager import tr
from utils.custom_device_manager import custom_device_manager
from core import SimulationManager
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
        self.name_label = QLabel(self.device_name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        self.name_label.setFont(name_font)
        info_layout.addWidget(self.name_label)
        
        # Tipo del dispositivo
        self.type_label = QLabel(self.device_type)
        type_font = QFont()
        type_font.setPointSize(8)
        self.type_label.setFont(type_font)
        self.type_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.type_label)
        
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
        elif self.device_type == "OLT_SDN":
            icon_file = "olt_sdn_icon.svg"
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
        elif self.device_type == "OLT_SDN":
            color = QColor(156, 39, 176)  # Morado (coincide con el ícono)
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
        self.name_label = QLabel(tr('sidebar.add_connections'))
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        self.name_label.setFont(name_font)
        info_layout.addWidget(self.name_label)
        
        # Descripción de la herramienta
        self.desc_label = QLabel(tr('sidebar.connection'))
        desc_font = QFont()
        desc_font.setPointSize(8)
        self.desc_label.setFont(desc_font)
        self.desc_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.desc_label)
        
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


class CreateDeviceButton(QFrame):
    """Botón para crear nuevo dispositivo personalizado"""
    
    create_clicked = pyqtSignal(str)  # device_type (OLT, ONU, etc.)
    
    def __init__(self, device_type, parent=None):
        super().__init__(parent)
        self.device_type = device_type
        self.dark_theme = False
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz del botón crear"""
        self.setFixedHeight(50)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Icono "+"
        icon_label = QLabel("➕")
        icon_font = QFont()
        icon_font.setPointSize(14)
        icon_label.setFont(icon_font)
        layout.addWidget(icon_label)
        
        # Texto
        text_key = f'custom_device.create_{self.device_type.lower()}'
        self.text_label = QLabel(tr(text_key))
        text_font = QFont()
        text_font.setPointSize(10)
        self.text_label.setFont(text_font)
        layout.addWidget(self.text_label)
        
        layout.addStretch()
    
    def mousePressEvent(self, event):
        """Detectar click"""
        if event.button() == Qt.LeftButton:
            self.create_clicked.emit(self.device_type)
    
    def update_text(self):
        """Actualizar texto del botón con el idioma actual"""
        text_key = f'custom_device.create_{self.device_type.lower()}'
        self.text_label.setText(tr(text_key))
    
    def set_theme(self, dark_theme):
        """Aplicar tema con borde punteado y opacidad"""
        self.dark_theme = dark_theme
        
        if dark_theme:
            self.setStyleSheet("""
                CreateDeviceButton {
                    background-color: rgba(43, 43, 43, 0.5);
                    border: 2px dashed #666666;
                    border-radius: 5px;
                }
                CreateDeviceButton:hover {
                    background-color: rgba(60, 60, 60, 0.7);
                    border-color: #888888;
                }
                QLabel {
                    color: #999999;
                    background: transparent;
                }
            """)
        else:
            self.setStyleSheet("""
                CreateDeviceButton {
                    background-color: rgba(248, 249, 250, 0.5);
                    border: 2px dashed #cccccc;
                    border-radius: 5px;
                }
                CreateDeviceButton:hover {
                    background-color: rgba(230, 230, 230, 0.7);
                    border-color: #999999;
                }
                QLabel {
                    color: #999999;
                    background: transparent;
                }
            """)


class CustomDeviceItem(QFrame):
    """Widget para dispositivo personalizado con opciones de editar/eliminar"""
    
    device_clicked = pyqtSignal(str)  # device_name
    drag_started = pyqtSignal(str, str)  # device_name, device_type
    edit_requested = pyqtSignal(dict)  # device_data
    delete_requested = pyqtSignal(str)  # device_id
    
    def __init__(self, device_data, parent=None):
        super().__init__(parent)
        self.device_data = device_data
        self.device_name = device_data['name']
        self.device_type = device_data['type']
        self.device_id = device_data['id']
        self.drag_start_position = QPoint()
        self.dark_theme = False
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz del dispositivo personalizado"""
        self.setFixedHeight(60)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Icono del dispositivo
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.setup_device_icon()
        main_layout.addWidget(self.icon_label)
        
        # Información del dispositivo
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)
        
        # Nombre
        self.name_label = QLabel(self.device_name)
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(10)
        self.name_label.setFont(name_font)
        info_layout.addWidget(self.name_label)
        
        # Tipo (mostrar estándar PON si está definido, sino "Personalizado")
        standard = self.device_data.get('standard', None)
        if standard:
            type_text = f"{standard}"  # Mostrar EPON, GPON, XG-PON o NG-PON2
        else:
            type_text = tr('custom_device.custom_label')  # Mostrar "Personalizado"
        
        self.type_label = QLabel(type_text)
        type_font = QFont()
        type_font.setPointSize(8)
        self.type_label.setFont(type_font)
        self.type_label.setStyleSheet("color: #4a90e2;")
        info_layout.addWidget(self.type_label)
        
        main_layout.addLayout(info_layout)
        main_layout.addStretch()
        
        # Botones de acción (esquina superior derecha)
        actions_layout = QVBoxLayout()
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(2)
        
        # Botón editar
        self.edit_button = QPushButton("✎")  # Símbolo de lápiz más visible
        self.edit_button.setFixedSize(20, 20)
        self.edit_button.setCursor(Qt.PointingHandCursor)
        self.edit_button.setToolTip(tr('custom_device.edit'))
        self.edit_button.clicked.connect(self.on_edit_clicked)
        edit_font = QFont()
        edit_font.setPointSize(12)
        edit_font.setBold(True)
        self.edit_button.setFont(edit_font)
        actions_layout.addWidget(self.edit_button)
        
        # Botón eliminar
        self.delete_button = QPushButton("✖")  # Símbolo de X más visible
        self.delete_button.setFixedSize(20, 20)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.setToolTip(tr('custom_device.delete'))
        self.delete_button.clicked.connect(self.on_delete_clicked)
        delete_font = QFont()
        delete_font.setPointSize(12)
        delete_font.setBold(True)
        self.delete_button.setFont(delete_font)
        actions_layout.addWidget(self.delete_button)
        
        main_layout.addLayout(actions_layout)
    
    def setup_device_icon(self):
        """Configurar icono del dispositivo personalizado con SVG coloreado"""
        try:
            # Determinar ruta del SVG según el tipo de dispositivo
            if "OLT" in self.device_type:
                svg_path = os.path.join('resources', 'devices', 'olt_icon_custom.svg')
            elif "ONU" in self.device_type:
                svg_path = os.path.join('resources', 'devices', 'onu_icon.svg')
            else:
                svg_path = None
            
            if svg_path and os.path.exists(svg_path):
                # Leer el archivo SVG
                with open(svg_path, 'r', encoding='utf-8') as f:
                    svg_content = f.read()
                
                # Obtener el color personalizado del dispositivo
                device_color = QColor(self.device_data.get('color', '#4a90e2'))
                
                # Color oscuro (80% del brillo)
                dark_color = QColor(
                    int(device_color.red() * 0.8),
                    int(device_color.green() * 0.8),
                    int(device_color.blue() * 0.8)
                )
                
                # Reemplazar colores en el SVG
                svg_content = svg_content.replace('#C62828', dark_color.name())
                svg_content = svg_content.replace('#F44336', device_color.name())
                
                # Renderizar el SVG modificado
                from PyQt5.QtCore import QByteArray
                svg_bytes = QByteArray(svg_content.encode('utf-8'))
                renderer = QSvgRenderer(svg_bytes)
                
                # Crear pixmap y renderizar
                pixmap = QPixmap(40, 40)
                pixmap.fill(Qt.transparent)
                
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                
                self.icon_label.setPixmap(pixmap)
            else:
                # Fallback a emoji si no hay SVG
                icon_text = "📦"
                if "OLT" in self.device_type:
                    icon_text = "🔷"
                elif "ONU" in self.device_type:
                    icon_text = "📱"
                
                self.icon_label.setText(icon_text)
                font = QFont()
                font.setPointSize(20)
                self.icon_label.setFont(font)
                
        except Exception as e:
            print(f"Error cargando icono SVG: {e}")
            # Fallback a emoji
            icon_text = "🔷" if "OLT" in self.device_type else "📱"
            self.icon_label.setText(icon_text)
            font = QFont()
            font.setPointSize(20)
            self.icon_label.setFont(font)
    
    def on_edit_clicked(self):
        """Manejar click en editar"""
        self.edit_requested.emit(self.device_data)
    
    def on_delete_clicked(self):
        """Manejar click en eliminar"""
        self.delete_requested.emit(self.device_id)
    
    def mousePressEvent(self, event):
        """Detectar inicio de drag o click"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        """Iniciar drag and drop"""
        if not (event.buttons() & Qt.LeftButton):
            return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
        
        # Iniciar drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"{self.device_name}|{self.device_type}")
        drag.setMimeData(mime_data)
        
        # Emitir señal
        self.drag_started.emit(self.device_name, self.device_type)
        
        # Ejecutar drag
        drag.exec_(Qt.CopyAction)
    
    def update_translations(self):
        """Actualizar textos con el idioma actual"""
        # Actualizar label de tipo (mostrar estándar PON si está definido, sino "Personalizado")
        standard = self.device_data.get('standard', None)
        if standard:
            type_text = f"{standard}"  # Mostrar EPON, GPON, XG-PON o NG-PON2
        else:
            type_text = tr('custom_device.custom_label')  # Mostrar "Personalizado"
        
        self.type_label.setText(type_text)
        
        # Actualizar tooltips de los botones
        self.edit_button.setToolTip(tr('custom_device.edit'))
        self.delete_button.setToolTip(tr('custom_device.delete'))
    
    def set_theme(self, dark_theme):
        """Aplicar tema con borde punteado y opacidad reducida"""
        self.dark_theme = dark_theme
        
        if dark_theme:
            self.setStyleSheet("""
                CustomDeviceItem {
                    background-color: rgba(43, 43, 43, 0.6);
                    border: 2px dashed #555555;
                    border-radius: 5px;
                }
                CustomDeviceItem:hover {
                    background-color: rgba(60, 60, 60, 0.8);
                    border-color: #777777;
                }
                QLabel {
                    color: #cccccc;
                    background: transparent;
                }
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                    color: #cccccc;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 3px;
                }
            """)
            # Color específico para botón de eliminar en tema oscuro
            self.delete_button.setStyleSheet("""
                QPushButton {
                    color: #ff6b6b;
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    color: #ff4444;
                    background-color: rgba(255, 107, 107, 0.2);
                    border-radius: 3px;
                }
            """)
            # Color específico para botón de editar en tema oscuro
            self.edit_button.setStyleSheet("""
                QPushButton {
                    color: #4a90e2;
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    color: #5aa3f5;
                    background-color: rgba(74, 144, 226, 0.2);
                    border-radius: 3px;
                }
            """)
        else:
            self.setStyleSheet("""
                CustomDeviceItem {
                    background-color: rgba(248, 249, 250, 0.6);
                    border: 2px dashed #cccccc;
                    border-radius: 5px;
                }
                CustomDeviceItem:hover {
                    background-color: rgba(230, 230, 230, 0.8);
                    border-color: #999999;
                }
                QLabel {
                    color: #555555;
                    background: transparent;
                }
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                    color: #333333;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                    border-radius: 3px;
                }
            """)
            # Color específico para botón de eliminar en tema claro
            self.delete_button.setStyleSheet("""
                QPushButton {
                    color: #d32f2f;
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    color: #b71c1c;
                    background-color: rgba(211, 47, 47, 0.1);
                    border-radius: 3px;
                }
            """)
            # Color específico para botón de editar en tema claro
            self.edit_button.setStyleSheet("""
                QPushButton {
                    color: #1976d2;
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    color: #0d47a1;
                    background-color: rgba(25, 118, 210, 0.1);
                    border-radius: 3px;
                }
            """)


class CollapsibleSection(QWidget):
    """Widget de sección colapsable (acordeón) para agrupar dispositivos"""
    
    def __init__(self, title="Section", parent=None):
        super().__init__(parent)
        self.is_expanded = True
        self.dark_theme = False
        self.title = title
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz de la sección colapsable"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Botón de encabezado simple (solo texto + flecha)
        self.header_button = QPushButton()
        self.header_button.setFixedHeight(28)
        self.header_button.setCursor(Qt.PointingHandCursor)
        self.header_button.clicked.connect(self.toggle_collapse)
        self.header_button.setFlat(True)
        
        # Layout del encabezado
        header_layout = QHBoxLayout(self.header_button)
        header_layout.setContentsMargins(5, 0, 5, 0)
        header_layout.setSpacing(6)
        
        # Indicador de expansión (▼ o ▶)
        self.arrow_label = QLabel("▼")
        arrow_font = QFont()
        arrow_font.setPointSize(9)
        self.arrow_label.setFont(arrow_font)
        header_layout.addWidget(self.arrow_label)
        
        # Título de la sección (texto más ligero)
        self.title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(10)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        self.main_layout.addWidget(self.header_button)
        
        # Separador sutil
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        self.main_layout.addWidget(separator)
        self.separator = separator
        
        # Contenedor para el contenido (dispositivos)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 4, 8, 4)
        self.content_layout.setSpacing(4)
        
        self.main_layout.addWidget(self.content_widget)
        
        # Aplicar tema inicial
        self.update_theme()
    
    def add_item(self, widget):
        """Agregar un widget (dispositivo) a la sección"""
        self.content_layout.addWidget(widget)
    
    def toggle_collapse(self):
        """Expandir/colapsar la sección"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content_widget.show()
            self.arrow_label.setText("▼")
            self.separator.show()
        else:
            self.content_widget.hide()
            self.arrow_label.setText("▶")
            self.separator.hide()
        
        self.update_theme()
    
    def set_expanded(self, expanded):
        """Establecer estado de expansión programáticamente"""
        if self.is_expanded != expanded:
            self.toggle_collapse()
    
    def set_theme(self, dark_theme):
        """Actualizar tema de la sección"""
        self.dark_theme = dark_theme
        self.update_theme()
    
    def update_theme(self):
        """Aplicar estilos según el tema - diseño minimalista"""
        if self.dark_theme:
            text_color = "#cccccc"
            arrow_color = "#888888"
            separator_color = "#444444"
            hover_bg = "rgba(255, 255, 255, 0.05)"
            
            self.header_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                }}
            """)
            
            self.title_label.setStyleSheet(f"color: {text_color}; background: transparent;")
            self.arrow_label.setStyleSheet(f"color: {arrow_color}; background: transparent;")
            self.separator.setStyleSheet(f"background-color: {separator_color}; border: none;")
            
            self.content_widget.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border: none;
                }
            """)
        else:
            text_color = "#555555"
            arrow_color = "#888888"
            separator_color = "#dddddd"
            hover_bg = "rgba(0, 0, 0, 0.03)"
            
            self.header_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    text-align: left;
                    padding: 2px;
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                }}
            """)
            
            self.title_label.setStyleSheet(f"color: {text_color}; background: transparent;")
            self.arrow_label.setStyleSheet(f"color: {arrow_color}; background: transparent;")
            self.separator.setStyleSheet(f"background-color: {separator_color}; border: none;")
            
            self.content_widget.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border: none;
                }
            """)


class DevicePropertiesPanel(QFrame):
    """Panel de propiedades de dispositivo en el sidebar"""
    
    edit_device_requested = pyqtSignal(str)  # device_id para abrir diálogo completo
    device_properties_changed = pyqtSignal(str, dict)  # device_id, new_properties
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_device = None
        self.connection_manager = None
        self.dark_theme = False
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz del panel de propiedades"""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)
        self.setFixedHeight(270)  # Altura aumentada para acomodar el botón guardar
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Márgenes más amplios
        main_layout.setSpacing(8)  # Mayor espaciado
        
        # Título del panel
        self.title_label = QLabel(tr('sidebar.properties.title'))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)
        
        # Crear contenedor de propiedades
        self.properties_group = QGroupBox("")
        props_layout = QFormLayout(self.properties_group)
        props_layout.setContentsMargins(8, 8, 8, 8)  # Márgenes más amplios
        props_layout.setSpacing(6)  # Espaciado aumentado entre campos
        props_layout.setHorizontalSpacing(10)  # Espaciado horizontal entre labels y campos
        
        # Campos editables
        self.device_name_edit = QLineEdit()
        self.device_name_edit.setPlaceholderText(tr('sidebar.properties.name'))
        self.device_name_edit.setMinimumHeight(22)  # Altura mínima para mejor legibilidad
        self.device_name_edit.textChanged.connect(self.on_name_changed)
        
        self.device_id_label = QLabel("--")  # ID no editable
        self.device_id_label.setWordWrap(True)
        self.device_id_label.setMinimumHeight(22)  # Consistencia en alturas
        
        # Campos de coordenadas editables
        coords_widget = QWidget()
        coords_layout = QHBoxLayout(coords_widget)
        coords_layout.setContentsMargins(0, 0, 0, 0)
        coords_layout.setSpacing(8)  # Mayor espaciado entre elementos
        
        self.x_coord_edit = QLineEdit()
        self.x_coord_edit.setPlaceholderText("X")
        self.x_coord_edit.setFixedWidth(60)  # Ancho aumentado
        self.x_coord_edit.setMinimumHeight(22)  # Altura consistente
        self.x_coord_edit.textChanged.connect(self.on_coords_changed)
        
        self.y_coord_edit = QLineEdit()
        self.y_coord_edit.setPlaceholderText("Y")
        self.y_coord_edit.setFixedWidth(60)  # Ancho aumentado
        self.y_coord_edit.setMinimumHeight(22)  # Altura consistente
        self.y_coord_edit.textChanged.connect(self.on_coords_changed)
        
        self.x_label = QLabel(tr('sidebar.properties.x_coord'))
        self.y_label = QLabel(tr('sidebar.properties.y_coord'))
        coords_layout.addWidget(self.x_label)
        coords_layout.addWidget(self.x_coord_edit)
        coords_layout.addWidget(self.y_label)
        coords_layout.addWidget(self.y_coord_edit)
        coords_layout.addStretch()
        
        self.specific_info_label = QLabel("--")  # Info específica no editable
        self.specific_info_label.setWordWrap(True)
        self.specific_info_label.setMinimumHeight(22)  # Altura consistente
        
        # Campo específico para OLT - Tasa de transmisión
        self.transmission_rate_edit = QDoubleSpinBox()
        self.transmission_rate_edit.setRange(1.0, 100000.0)  # 1 Mbps a 100 Gbps
        self.transmission_rate_edit.setValue(512.0)  # Valor inicial, se actualiza con el dispositivo
        self.transmission_rate_edit.setSuffix(" Mbps")
        self.transmission_rate_edit.setDecimals(1)
        self.transmission_rate_edit.setSingleStep(512.0)  # Incrementos de 512 Mbps
        self.transmission_rate_edit.setMinimumHeight(22)  # Altura consistente
        self.transmission_rate_edit.setMinimumWidth(120)  # Ancho mínimo para mejor legibilidad
        self.transmission_rate_edit.valueChanged.connect(self.on_transmission_rate_changed)
        self.transmission_rate_edit.setVisible(False)  # Oculto por defecto
        
        # Agregar campos al formulario con labels traducibles
        self.name_row_label = QLabel(tr('sidebar.properties.name'))
        self.id_row_label = QLabel(tr('sidebar.properties.id'))
        self.position_row_label = QLabel(tr('sidebar.properties.position'))
        self.transmission_row_label = QLabel(tr('sidebar.properties.transmission_rate'))
        self.info_row_label = QLabel(tr('sidebar.properties.info'))
        
        props_layout.addRow(self.name_row_label, self.device_name_edit)
        props_layout.addRow(self.id_row_label, self.device_id_label)
        props_layout.addRow(self.position_row_label, coords_widget)
        props_layout.addRow(self.transmission_row_label, self.transmission_rate_edit)
        props_layout.addRow(self.info_row_label, self.specific_info_label)
        
        main_layout.addWidget(self.properties_group)
        
        # Contenedor para botones
        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("QWidget { background-color: transparent; }")  # Fondo transparente
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        
        # Botón para guardar cambios
        self.save_button = QPushButton(tr('sidebar.properties.save'))
        self.save_button.setFixedHeight(28)
        self.save_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding: 4px 8px;
                background-color: #4CAF50;
                color: white;
                border: 1px solid #45a049;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
                border: 1px solid #cccccc;
            }
        """)
        self.save_button.clicked.connect(self.on_save_changes)
        self.save_button.setEnabled(False)  # Deshabilitado inicialmente
        
        # Botón para edición completa
        self.edit_button = QPushButton(tr('sidebar.properties.edit_full'))
        self.edit_button.setFixedHeight(28)  # Misma altura que el botón guardar
        self.edit_button.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                padding: 4px 8px;
            }
        """)
        self.edit_button.clicked.connect(self.on_edit_requested)
        
        # Agregar botones al layout
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.edit_button)
        main_layout.addWidget(buttons_widget)
        
        # Estado inicial
        self.show_no_selection()
    
    def show_no_selection(self):
        """Mostrar estado sin dispositivo seleccionado"""
        self.properties_group.setTitle(tr('sidebar.properties.no_selection'))
        self.device_name_edit.setText("")
        self.device_name_edit.setPlaceholderText(tr('sidebar.properties.select_device'))
        self.device_name_edit.setEnabled(False)
        
        self.device_id_label.setText(tr('sidebar.properties.to_view_properties'))
        
        self.x_coord_edit.setText("")
        self.x_coord_edit.setEnabled(False)
        self.y_coord_edit.setText("")
        self.y_coord_edit.setEnabled(False)
        
        # Ocultar campo transmission_rate
        self.transmission_rate_edit.setVisible(False)
        
        self.specific_info_label.setText("")
        self.edit_button.setEnabled(False)
        self.save_button.setEnabled(False)  # Deshabilitar botón guardar
        self.current_device = None
    
    def update_device_properties(self, device, connection_manager=None):
        """Actualizar propiedades mostradas para un dispositivo"""
        self.current_device = device
        self.connection_manager = connection_manager
        
        if not device:
            self.show_no_selection()
            return
        
        # Información básica (editable)
        self.properties_group.setTitle(f"{device.device_type} Seleccionado")
        
        # Temporalmente desconectar señales para evitar cambios durante actualización
        self.device_name_edit.textChanged.disconnect()
        self.x_coord_edit.textChanged.disconnect()
        self.y_coord_edit.textChanged.disconnect()
        self.transmission_rate_edit.valueChanged.disconnect()
        
        # Actualizar campos editables
        self.device_name_edit.setText(device.name)
        self.device_name_edit.setPlaceholderText("Nombre del dispositivo")
        self.device_name_edit.setEnabled(True)
        
        self.device_id_label.setText(device.id)
        
        self.x_coord_edit.setText(f"{device.x:.1f}")
        self.x_coord_edit.setEnabled(True)
        self.y_coord_edit.setText(f"{device.y:.1f}")
        self.y_coord_edit.setEnabled(True)
        
        # Manejar campo transmission_rate específico para OLT y OLT_SDN
        if device.device_type in ["OLT", "OLT_SDN"]:
            self.transmission_rate_edit.setVisible(True)
            # Obtener el valor desde las propiedades del dispositivo
            current_rate = device.properties.get('transmission_rate', 4096.0)
            self.transmission_rate_edit.setValue(current_rate)
        else:
            self.transmission_rate_edit.setVisible(False)
        
        # Reconectar señales
        self.device_name_edit.textChanged.connect(self.on_name_changed)
        self.x_coord_edit.textChanged.connect(self.on_coords_changed)
        self.y_coord_edit.textChanged.connect(self.on_coords_changed)
        self.transmission_rate_edit.valueChanged.connect(self.on_transmission_rate_changed)
        
        # Resetear estado del botón guardar
        self.save_button.setEnabled(False)
        
        # Información específica por tipo (no editable)
        if device.device_type in ["OLT", "OLT_SDN"]:
            connected_onus = self.calculate_connected_onus(device)
            self.specific_info_label.setText(f"ONUs conectadas: {connected_onus}")
        elif device.device_type == "ONU":
            olt_distance = self.calculate_olt_distance(device)
            distance_text = f"{olt_distance:.1f}m" if olt_distance is not None else "No conectada"
            self.specific_info_label.setText(f"Distancia OLT: {distance_text}")
        else:
            self.specific_info_label.setText("--")
        
        self.edit_button.setEnabled(True)
    
    def calculate_connected_onus(self, olt_device):
        """Calcular ONUs conectadas a una OLT o OLT_SDN"""
        if not self.connection_manager:
            return 0
        
        count = 0
        for connection in self.connection_manager.connections:
            if (connection.device_a.id == olt_device.id and connection.device_b.device_type == "ONU") or \
               (connection.device_b.id == olt_device.id and connection.device_a.device_type == "ONU"):
                count += 1
        return count
    
    def calculate_olt_distance(self, onu_device):
        """Calcular distancia de ONU a OLT/OLT_SDN conectada"""
        if not self.connection_manager:
            return None
        
        for connection in self.connection_manager.connections:
            if connection.device_a.id == onu_device.id and connection.device_b.device_type in ["OLT", "OLT_SDN"]:
                return connection.calculate_distance()
            elif connection.device_b.id == onu_device.id and connection.device_a.device_type in ["OLT", "OLT_SDN"]:
                return connection.calculate_distance()
        return None
    
    def on_edit_requested(self):
        """Solicitar edición completa del dispositivo"""
        if self.current_device:
            self.edit_device_requested.emit(self.current_device.id)
    
    def on_save_changes(self):
        """Guardar todos los cambios pendientes"""
        if not self.current_device:
            return
        
        changes = {}
        
        # Verificar cambio de nombre
        new_name = self.device_name_edit.text().strip()
        if new_name and new_name != self.current_device.name:
            changes['name'] = new_name
        
        # Verificar cambio de coordenadas
        try:
            x_text = self.x_coord_edit.text().strip()
            y_text = self.y_coord_edit.text().strip()
            
            if x_text and y_text:
                new_x = float(x_text)
                new_y = float(y_text)
                
                if new_x != self.current_device.x or new_y != self.current_device.y:
                    changes['x'] = new_x
                    changes['y'] = new_y
        except ValueError:
            pass  # Ignorar valores inválidos
        
        # Verificar cambio de transmission_rate para OLT/OLT_SDN
        if (self.current_device.device_type in ["OLT", "OLT_SDN"] and 
            self.transmission_rate_edit.isVisible()):
            new_rate = self.transmission_rate_edit.value()
            current_rate = self.current_device.properties.get('transmission_rate', 4096.0)
            if abs(new_rate - current_rate) > 0.1:
                changes['transmission_rate'] = new_rate
        
        # Aplicar cambios si hay alguno
        if changes:
            self.emit_property_change(changes)
            # Deshabilitar botón después de guardar
            self.save_button.setEnabled(False)
            print(f"💾 Cambios guardados: {changes}")
        else:
            print("⚠️ No hay cambios para guardar")
    
    def mark_changes_pending(self):
        """Marcar que hay cambios pendientes de guardar"""
        if hasattr(self, 'save_button'):
            self.save_button.setEnabled(True)
    
    def on_name_changed(self):
        """Manejar cambio de nombre del dispositivo"""
        if self.current_device and self.device_name_edit.text().strip():
            new_name = self.device_name_edit.text().strip()
            if new_name != self.current_device.name:
                self.mark_changes_pending()
    
    def on_coords_changed(self):
        """Manejar cambio de coordenadas del dispositivo"""
        if not self.current_device:
            return
        
        try:
            x_text = self.x_coord_edit.text().strip()
            y_text = self.y_coord_edit.text().strip()
            
            if x_text and y_text:
                new_x = float(x_text)
                new_y = float(y_text)
                
                if new_x != self.current_device.x or new_y != self.current_device.y:
                    self.mark_changes_pending()
        except ValueError:
            pass  # Ignorar valores inválidos
    
    def on_transmission_rate_changed(self):
        """Manejar cambio de tasa de transmisión del dispositivo OLT/OLT_SDN"""
        if not self.current_device or self.current_device.device_type not in ["OLT", "OLT_SDN"]:
            return
        
        new_rate = self.transmission_rate_edit.value()
        current_rate = self.current_device.properties.get('transmission_rate', 4096.0)
        
        if abs(new_rate - current_rate) > 0.1:  # Comparación con tolerancia para floats
            self.mark_changes_pending()
    
    def emit_property_change(self, properties):
        """Emitir señal de cambio de propiedades"""
        if self.current_device:
            self.device_properties_changed.emit(self.current_device.id, properties)
    
    def set_theme(self, dark_theme):
        """Aplicar tema al panel - Los estilos están en los archivos CSS globales"""
        self.dark_theme = dark_theme
        # Los estilos para DevicePropertiesPanel están definidos en:
        # - resources/styles/dark_theme.qss
        # - resources/styles/light_theme.qss
        # No necesitamos setStyleSheet aquí, se aplican automáticamente
    
    def update_device_properties_from_external(self, device_id, new_properties):
        """Actualizar propiedades del dispositivo desde una fuente externa (como el diálogo)"""
        if not self.current_device or self.current_device.id != device_id:
            return
        
        # Desconectar señales temporalmente para evitar loops
        self.transmission_rate_edit.valueChanged.disconnect()
        
        try:
            # Actualizar transmission_rate si está en las nuevas propiedades
            if 'transmission_rate' in new_properties and self.current_device.device_type in ["OLT", "OLT_SDN"]:
                new_rate = float(new_properties['transmission_rate'])
                self.transmission_rate_edit.setValue(new_rate)
            
            # Actualizar otros campos si es necesario
            if 'name' in new_properties:
                self.device_name_edit.setText(new_properties['name'])
            
            if 'x' in new_properties:
                self.x_coord_edit.setText(f"{new_properties['x']:.1f}")
            
            if 'y' in new_properties:
                self.y_coord_edit.setText(f"{new_properties['y']:.1f}")
                
        except Exception as e:
            print(f"❌ Error actualizando propiedades en sidebar: {e}")
        
        finally:
            # Reconectar señales
            self.transmission_rate_edit.valueChanged.connect(self.on_transmission_rate_changed)

    def update_device_properties_from_dialog(self, device_id, new_properties):
        """Actualizar las propiedades mostradas cuando cambian desde el diálogo"""
        try:
            # Solo actualizar si es el dispositivo actualmente mostrado
            if self.current_device and self.current_device.id == device_id:
                
                # Actualizar transmission_rate si cambió
                if 'transmission_rate' in new_properties:
                    new_rate = float(new_properties['transmission_rate'])
                    
                    # Desconectar temporalmente la señal para evitar bucles
                    self.transmission_rate_edit.valueChanged.disconnect()
                    
                    # Actualizar el valor mostrado
                    self.transmission_rate_edit.setValue(new_rate)
                    print(f"[DEBUG] Sidebar actualizado - transmission_rate: {new_rate} Mbps")
                    
                    # Reconectar la señal
                    self.transmission_rate_edit.valueChanged.connect(self.on_transmission_rate_changed)
                
                # Actualizar otros campos si es necesario
                if 'name' in new_properties:
                    self.device_name_edit.setText(new_properties['name'])
                    
                if 'x' in new_properties or 'y' in new_properties:
                    if 'x' in new_properties:
                        self.x_coord_edit.setText(f"{new_properties['x']:.1f}")
                    if 'y' in new_properties:
                        self.y_coord_edit.setText(f"{new_properties['y']:.1f}")
                
                # Limpiar estado de cambios pendientes ya que se actualizó externamente
                self.clear_changes_pending()
                
        except Exception as e:
            print(f"❌ Error actualizando sidebar: {e}")
    
    def retranslate_ui(self):
        """Actualizar todos los textos del panel de propiedades con el idioma actual"""
        # Actualizar título
        self.title_label.setText(tr('sidebar.properties.title'))
        
        # Actualizar labels de campos
        self.name_row_label.setText(tr('sidebar.properties.name'))
        self.id_row_label.setText(tr('sidebar.properties.id'))
        self.position_row_label.setText(tr('sidebar.properties.position'))
        self.transmission_row_label.setText(tr('sidebar.properties.transmission_rate'))
        self.info_row_label.setText(tr('sidebar.properties.info'))
        
        # Actualizar labels de coordenadas
        self.x_label.setText(tr('sidebar.properties.x_coord'))
        self.y_label.setText(tr('sidebar.properties.y_coord'))
        
        # Actualizar botones
        self.save_button.setText(tr('sidebar.properties.save'))
        self.edit_button.setText(tr('sidebar.properties.edit_full'))
        
        # Actualizar placeholder si no hay selección
        if not self.current_device:
            self.properties_group.setTitle(tr('sidebar.properties.no_selection'))
            self.device_name_edit.setPlaceholderText(tr('sidebar.properties.select_device'))
            self.device_id_label.setText(tr('sidebar.properties.to_view_properties'))


class SidebarPanel(QWidget):
    """Panel lateral con dispositivos y controles"""
    
    device_selected = pyqtSignal(str, str)  # nombre_dispositivo, tipo_dispositivo
    connection_mode_toggled = pyqtSignal(bool)  # True cuando se activa modo conexión
    edit_device_requested = pyqtSignal(str)  # device_id para edición completa
    device_properties_changed = pyqtSignal(str, dict)  # device_id, new_properties
    
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
        self.title_label = QLabel(tr('sidebar.title'))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFixedHeight(40)
        main_layout.addWidget(self.title_label)
        
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
        self.info_label = QLabel(tr('sidebar.drag_info'))
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(8)
        self.info_label.setFont(info_font)
        self.info_label.setFixedHeight(40)
        main_layout.addWidget(self.info_label)
        
        # Panel de propiedades de dispositivo
        self.properties_panel = DevicePropertiesPanel(self)
        self.properties_panel.edit_device_requested.connect(self.on_edit_device_requested)
        self.properties_panel.device_properties_changed.connect(self.on_device_properties_changed)
        main_layout.addWidget(self.properties_panel)

        self.setLayout(main_layout)
        
        # Aplicar tema inicial
        self.set_theme(self.dark_theme)
    
    def setup_connection_tool_in_section(self):
        """Configurar la herramienta de conexión dentro de la sección de herramientas"""
        # Crear el item de conexión
        self.connection_item = ConnectionItem()
        self.connection_item.connection_mode_toggled.connect(self.on_connection_mode_toggled)
        self.connection_item.set_theme(self.dark_theme)
        
        # Agregar a la sección de herramientas
        self.tools_section.add_item(self.connection_item)
    
    def setup_connection_tool(self):
        """Configurar la herramienta de conexión (método legacy)"""
        # Mantener para compatibilidad pero ahora usa la sección
        if not hasattr(self, 'connection_item'):
            self.setup_connection_tool_in_section()
    
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
        """Poblar el panel con dispositivos predefinidos, personalizados y herramientas usando secciones colapsables"""
        
        # ====== SECCIÓN OLT ======
        self.olt_section = CollapsibleSection(tr('sidebar.sections.olt'), self)
        self.olt_section.set_theme(self.dark_theme)
        self.devices_layout.insertWidget(self.devices_layout.count() - 1, self.olt_section)
        
        # Dispositivos OLT predefinidos (siempre primero)
        olt_devices = [
            ("sidebar.device_names.olt", "OLT"),
            ("sidebar.device_names.olt_sdn", "OLT_SDN"),
        ]
        
        for device_name_key, device_type in olt_devices:
            device_name = tr(device_name_key)
            device_item = DeviceItem(device_name, device_type)
            device_item.device_clicked.connect(self.on_device_clicked)
            device_item.set_theme(self.dark_theme)
            device_item.name_translation_key = device_name_key
            
            self.olt_section.add_item(device_item)
            self.device_items.append(device_item)
        
        # Cargar OLT personalizados (después de los predefinidos)
        self.load_custom_olts()
        
        # Botón "Crear OLT" (siempre al final)
        self.create_olt_button = CreateDeviceButton("OLT", self)
        self.create_olt_button.create_clicked.connect(self.on_create_device_clicked)
        self.create_olt_button.set_theme(self.dark_theme)
        self.olt_section.add_item(self.create_olt_button)
        # No agregar a device_items para que no se cuente en el orden
        
        # ====== SECCIÓN ONU ======
        self.onu_section = CollapsibleSection(tr('sidebar.sections.onu'), self)
        self.onu_section.set_theme(self.dark_theme)
        self.devices_layout.insertWidget(self.devices_layout.count() - 1, self.onu_section)
        
        # Dispositivos ONU predefinidos
        onu_devices = [
            ("sidebar.device_names.onu", "ONU"),
        ]
        
        for device_name_key, device_type in onu_devices:
            device_name = tr(device_name_key)
            device_item = DeviceItem(device_name, device_type)
            device_item.device_clicked.connect(self.on_device_clicked)
            device_item.set_theme(self.dark_theme)
            device_item.name_translation_key = device_name_key
            
            self.onu_section.add_item(device_item)
            self.device_items.append(device_item)
        
        # TODO: Cargar ONU personalizados (Fase 2)
        
        # ====== SECCIÓN HERRAMIENTAS ======
        self.tools_section = CollapsibleSection(tr('sidebar.sections.tools'), self)
        self.tools_section.set_theme(self.dark_theme)
        self.devices_layout.insertWidget(self.devices_layout.count() - 1, self.tools_section)
        
        # Agregar herramienta de conexión a la sección de herramientas
        self.setup_connection_tool_in_section()
    
    def load_custom_olts(self):
        """Cargar OLT personalizados desde el almacenamiento"""
        custom_olts = custom_device_manager.load_custom_olts()
        
        for olt_data in custom_olts:
            # Agregar directamente a la sección (se agregará al final, antes del botón Crear)
            custom_item = CustomDeviceItem(olt_data, self)
            custom_item.device_clicked.connect(self.on_device_clicked)
            custom_item.edit_requested.connect(self.on_edit_custom_device)
            custom_item.delete_requested.connect(self.on_delete_custom_device)
            custom_item.set_theme(self.dark_theme)
            
            # Agregar usando add_item (se agrega al final del layout)
            self.olt_section.add_item(custom_item)
            self.device_items.append(custom_item)
    
    def add_custom_olt_item(self, device_data):
        """Agregar un item de OLT personalizado a la sección (usado cuando se crea uno nuevo)"""
        custom_item = CustomDeviceItem(device_data, self)
        custom_item.device_clicked.connect(self.on_device_clicked)
        custom_item.edit_requested.connect(self.on_edit_custom_device)
        custom_item.delete_requested.connect(self.on_delete_custom_device)
        custom_item.set_theme(self.dark_theme)
        
        # El botón "Crear OLT" siempre es el último widget en content_layout
        # Insertar el nuevo dispositivo justo antes del botón
        layout = self.olt_section.content_layout
        insert_position = layout.count() - 1  # Antes del último (botón Crear)
        layout.insertWidget(insert_position, custom_item)
        
        self.device_items.append(custom_item)
    
    def on_create_device_clicked(self, device_type):
        """Manejar click en botón 'Crear dispositivo'"""
        print(f"🔧 Crear dispositivo: {device_type}")
        
        if device_type == "OLT":
            self.show_create_olt_dialog()
        elif device_type == "ONU":
            # TODO: Implementar en Fase 2
            QMessageBox.information(
                self,
                tr('custom_device.coming_soon'),
                tr('custom_device.onu_coming_soon')
            )
    
    def show_create_olt_dialog(self, device_data=None):
        """Mostrar diálogo para crear/editar OLT"""
        from ui.custom_device_dialog import CustomOLTDialog
        
        dialog = CustomOLTDialog(self, device_data, self.dark_theme)
        dialog.device_saved.connect(self.on_custom_device_saved)
        dialog.exec_()
    
    def on_custom_device_saved(self, device_data):
        """Manejar dispositivo personalizado guardado"""
        print(f"✅ Dispositivo guardado: {device_data['name']}")
        
        # Si es nuevo (no tiene widget), agregarlo
        if device_data['type'] == 'CUSTOM_OLT':
            # Verificar si ya existe (modo edición)
            existing = False
            for item in self.device_items:
                if isinstance(item, CustomDeviceItem) and item.device_id == device_data['id']:
                    # Actualizar item existente
                    item.device_data = device_data
                    item.device_name = device_data['name']
                    item.name_label.setText(device_data['name'])
                    
                    # Actualizar etiqueta de tipo (estándar PON o "Personalizado")
                    standard = device_data.get('standard', None)
                    if standard:
                        item.type_label.setText(f"{standard}")
                    else:
                        item.type_label.setText(tr('custom_device.custom_label'))
                    
                    # Refrescar el icono con el nuevo color
                    item.setup_device_icon()
                    existing = True
                    break
            
            # Si no existe, agregarlo
            if not existing:
                self.add_custom_olt_item(device_data)
    
    def on_edit_custom_device(self, device_data):
        """Manejar edición de dispositivo personalizado"""
        print(f"✏️ Editar dispositivo: {device_data['name']}")
        
        if device_data['type'] == 'CUSTOM_OLT':
            self.show_create_olt_dialog(device_data)
    
    def on_delete_custom_device(self, device_id):
        """Manejar eliminación de dispositivo personalizado"""
        # Confirmar eliminación
        reply = QMessageBox.question(
            self,
            tr('custom_device.confirm_delete_title'),
            tr('custom_device.confirm_delete_message'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Eliminar del almacenamiento
            success = custom_device_manager.delete_custom_olt(device_id)
            
            if success:
                # Eliminar del UI
                for i, item in enumerate(self.device_items):
                    if isinstance(item, CustomDeviceItem) and item.device_id == device_id:
                        # Remover del layout
                        item.setParent(None)
                        item.deleteLater()
                        # Remover de la lista
                        self.device_items.pop(i)
                        print(f"🗑️ Dispositivo eliminado: {device_id}")
                        break
    
    def on_device_clicked(self, device_name):
        """Manejar click en dispositivo"""
        # Encontrar el tipo de dispositivo
        device_type = None
        for item in self.device_items:
            if hasattr(item, 'device_name') and item.device_name == device_name:
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
        
        # Actualizar tema de las secciones colapsables
        if hasattr(self, 'olt_section'):
            self.olt_section.set_theme(dark_theme)
        if hasattr(self, 'onu_section'):
            self.onu_section.set_theme(dark_theme)
        if hasattr(self, 'tools_section'):
            self.tools_section.set_theme(dark_theme)
        
        # Actualizar tema del botón "Crear OLT"
        if hasattr(self, 'create_olt_button'):
            self.create_olt_button.set_theme(dark_theme)
        
        # Actualizar tema del item de conexión
        if hasattr(self, 'connection_item') and self.connection_item:
            self.connection_item.set_theme(dark_theme)
        
        # Actualizar tema del panel de propiedades
        if hasattr(self, 'properties_panel'):
            self.properties_panel.set_theme(dark_theme)
    
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
    
    def update_device_properties(self, device, connection_manager=None):
        """Actualizar el panel de propiedades con un dispositivo seleccionado"""
        if hasattr(self, 'properties_panel') and self.properties_panel:
            self.properties_panel.update_device_properties(device, connection_manager)
    
    def clear_device_selection(self):
        """Limpiar selección de dispositivo"""
        self.properties_panel.show_no_selection()
    
    def on_edit_device_requested(self, device_id):
        """Manejar solicitud de edición completa del dispositivo"""
        # Emitir señal que será capturada por el canvas para abrir el diálogo
        self.edit_device_requested.emit(device_id)
    
    def on_device_properties_changed(self, device_id, new_properties):
        """Manejar cambio de propiedades desde el panel editable"""
        # Reenviar señal al nivel superior para actualizar el dispositivo
        self.device_properties_changed.emit(device_id, new_properties)

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
    
    def retranslate_ui(self):
        """Actualizar todos los textos del sidebar con el idioma actual"""
        # Actualizar título del panel
        self.title_label.setText(tr('sidebar.title'))
        
        # Actualizar info de arrastrar
        self.info_label.setText(tr('sidebar.drag_info'))
        
        # Actualizar títulos de las secciones colapsables
        if hasattr(self, 'olt_section'):
            self.olt_section.title = tr('sidebar.sections.olt')
            self.olt_section.title_label.setText(self.olt_section.title)
        if hasattr(self, 'onu_section'):
            self.onu_section.title = tr('sidebar.sections.onu')
            self.onu_section.title_label.setText(self.onu_section.title)
        if hasattr(self, 'tools_section'):
            self.tools_section.title = tr('sidebar.sections.tools')
            self.tools_section.title_label.setText(self.tools_section.title)
        
        # Actualizar botón "Crear OLT"
        if hasattr(self, 'create_olt_button'):
            self.create_olt_button.update_text()
        
        # Actualizar nombres de dispositivos
        for device_item in self.device_items:
            if hasattr(device_item, 'name_translation_key'):
                translated_name = tr(device_item.name_translation_key)
                device_item.device_name = translated_name
                device_item.name_label.setText(translated_name)
            # Actualizar botones de crear dispositivo personalizado
            elif isinstance(device_item, CreateDeviceButton):
                device_item.update_text()
            # Actualizar dispositivos personalizados
            elif isinstance(device_item, CustomDeviceItem):
                device_item.update_translations()
        
        # Actualizar connection item
        if hasattr(self, 'connection_item'):
            self.connection_item.name_label.setText(tr('sidebar.add_connections'))
            self.connection_item.desc_label.setText(tr('sidebar.connection'))
        
        # Actualizar panel de propiedades
        if hasattr(self, 'properties_panel'):
            self.properties_panel.retranslate_ui()
