"""
Device Properties Dialog
Ventana de propiedades para dispositivos PON
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QGroupBox, 
                             QSpinBox, QDoubleSpinBox, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import os


class DevicePropertiesDialog(QDialog):
    """Diálogo para mostrar y editar propiedades de dispositivos"""
    
    # Señal emitida cuando se actualizan las propiedades
    properties_updated = pyqtSignal(str, dict)  # device_id, new_properties
    
    def __init__(self, device, connection_manager=None, parent=None):
        super().__init__(parent)
        self.device = device
        self.connection_manager = connection_manager
        self.original_properties = {}
        
        self.setup_ui()
        self.load_device_data()
        self.setup_connections()
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        self.setWindowTitle(f"Propiedades - {self.device.name}")
        self.setModal(True)
        self.setFixedSize(400, 350)
        
        # Eliminar botón de "What's This?" (signo de interrogación)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        title_label = QLabel(f"Propiedades del Dispositivo")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Información básica
        self.setup_basic_info_section(main_layout)
        
        # Información específica del tipo
        self.setup_specific_info_section(main_layout)
        
        # Botones
        self.setup_buttons(main_layout)
        
        # Aplicar tema dinámico
        self.apply_theme()
    
    def setup_basic_info_section(self, main_layout):
        """Configurar sección de información básica"""
        basic_group = QGroupBox("Información Básica")
        basic_layout = QFormLayout(basic_group)
        
        # ID (solo lectura)
        self.id_edit = QLineEdit(self.device.id)
        self.id_edit.setReadOnly(True)
        basic_layout.addRow("ID:", self.id_edit)
        
        # Tipo (solo lectura)
        self.type_edit = QLineEdit(self.device.device_type)
        self.type_edit.setReadOnly(True)
        basic_layout.addRow("Tipo:", self.type_edit)
        
        # Nombre (editable)
        self.name_edit = QLineEdit(self.device.name)
        self.name_edit.setMaxLength(50)
        basic_layout.addRow("Nombre:", self.name_edit)
        
        # Coordenadas (editables)
        coord_layout = QHBoxLayout()
        
        self.x_spinbox = QDoubleSpinBox()
        self.x_spinbox.setRange(-9999.0, 9999.0)
        self.x_spinbox.setDecimals(1)
        self.x_spinbox.setSuffix(" px")
        self.x_spinbox.setValue(self.device.x)
        
        self.y_spinbox = QDoubleSpinBox()
        self.y_spinbox.setRange(-9999.0, 9999.0)
        self.y_spinbox.setDecimals(1)
        self.y_spinbox.setSuffix(" px")
        self.y_spinbox.setValue(self.device.y)
        
        coord_layout.addWidget(QLabel("X:"))
        coord_layout.addWidget(self.x_spinbox)
        coord_layout.addWidget(QLabel("Y:"))
        coord_layout.addWidget(self.y_spinbox)
        
        basic_layout.addRow("Coordenadas:", coord_layout)
        
        main_layout.addWidget(basic_group)
    
    def setup_specific_info_section(self, main_layout):
        """Configurar sección de información específica del tipo"""
        if self.device.device_type == "OLT":
            self.setup_olt_info(main_layout)
        elif self.device.device_type == "ONU":
            self.setup_onu_info(main_layout)
    
    def setup_olt_info(self, main_layout):
        """Configurar información específica de OLT"""
        olt_group = QGroupBox("Información OLT")
        olt_layout = QFormLayout(olt_group)
        
        # Número de ONUs conectadas (calculado)
        connected_onus = self.calculate_connected_onus()
        self.onus_edit = QLineEdit(str(connected_onus))
        self.onus_edit.setReadOnly(True)
        olt_layout.addRow("ONUs Conectadas:", self.onus_edit)
        
        main_layout.addWidget(olt_group)
    
    def setup_onu_info(self, main_layout):
        """Configurar información específica de ONU"""
        onu_group = QGroupBox("Información ONU")
        onu_layout = QFormLayout(onu_group)
        
        # Distancia de la OLT conectada (calculado)
        olt_distance = self.calculate_olt_distance()
        distance_text = f"{olt_distance:.1f} m" if olt_distance is not None else "No conectada"
        self.distance_edit = QLineEdit(distance_text)
        self.distance_edit.setReadOnly(True)
        onu_layout.addRow("Distancia a OLT:", self.distance_edit)
        
        main_layout.addWidget(onu_group)
    
    def setup_buttons(self, main_layout):
        """Configurar botones del diálogo"""
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Botón Cancelar
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # Botón OK
        self.ok_button = QPushButton("Guardar")
        self.ok_button.setObjectName("ok_button")
        self.ok_button.clicked.connect(self.accept_changes)
        self.ok_button.setDefault(True)
        buttons_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(buttons_layout)
    
    def setup_connections(self):
        """Configurar conexiones de señales"""
        # Validar nombre en tiempo real
        self.name_edit.textChanged.connect(self.validate_input)
    
    def load_device_data(self):
        """Cargar datos actuales del dispositivo"""
        self.original_properties = {
            'name': self.device.name,
            'x': self.device.x,
            'y': self.device.y
        }
    
    def calculate_connected_onus(self):
        """Calcular número de ONUs conectadas a esta OLT"""
        if not self.connection_manager or self.device.device_type != "OLT":
            return 0
        
        connected_count = 0
        for connection in self.connection_manager.connections:
            if (connection.device_a.id == self.device.id and connection.device_b.device_type == "ONU") or \
               (connection.device_b.id == self.device.id and connection.device_a.device_type == "ONU"):
                connected_count += 1
        
        return connected_count
    
    def calculate_olt_distance(self):
        """Calcular distancia a la OLT conectada"""
        if not self.connection_manager or self.device.device_type != "ONU":
            return None
        
        for connection in self.connection_manager.connections:
            olt_device = None
            if connection.device_a.id == self.device.id and connection.device_b.device_type == "OLT":
                olt_device = connection.device_b
            elif connection.device_b.id == self.device.id and connection.device_a.device_type == "OLT":
                olt_device = connection.device_a
            
            if olt_device:
                return connection.calculate_distance()
        
        return None
    
    def validate_input(self):
        """Validar entrada de datos"""
        # Validar que el nombre no esté vacío
        name_valid = len(self.name_edit.text().strip()) > 0
        
        # Habilitar/deshabilitar botón OK
        self.ok_button.setEnabled(name_valid)
    
    def accept_changes(self):
        """Aceptar y aplicar cambios"""
        # Validar datos
        if not self.validate_data():
            return
        
        # Crear diccionario con nuevas propiedades
        new_properties = {
            'name': self.name_edit.text().strip(),
            'x': self.x_spinbox.value(),
            'y': self.y_spinbox.value()
        }
        
        # Emitir señal con cambios
        self.properties_updated.emit(self.device.id, new_properties)
        
        # Cerrar diálogo
        self.accept()
    
    def validate_data(self):
        """Validar todos los datos antes de guardar"""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Error de Validación", 
                              "El nombre del dispositivo no puede estar vacío.")
            return False
        
        return True
    
    def get_changes(self):
        """Obtener cambios realizados"""
        current_properties = {
            'name': self.name_edit.text().strip(),
            'x': self.x_spinbox.value(),
            'y': self.y_spinbox.value()
        }
        
        changes = {}
        for key, value in current_properties.items():
            if value != self.original_properties.get(key):
                changes[key] = value
        
        return changes
    
    def detect_theme(self):
        """Detectar si se está usando tema oscuro o claro"""
        try:
            # Intentar obtener tema del parent (MainWindow o Canvas)
            if self.parent():
                if hasattr(self.parent(), 'dark_theme'):
                    return self.parent().dark_theme
                elif hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'dark_theme'):
                    return self.parent().parent().dark_theme
            
            # Detectar por el color de fondo de la paleta
            background_color = self.palette().color(self.palette().Window)
            # Si el fondo es más oscuro que gris medio, es tema oscuro
            return background_color.lightness() < 128
            
        except:
            return False  # Default a tema claro
    
    def apply_theme(self):
        """Aplicar tema dinámico basado en la detección"""
        is_dark = self.detect_theme()
        
        if is_dark:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    
    def apply_light_theme(self):
        """Aplicar tema claro"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #000000;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #000000;
            }
            QLabel {
                color: #000000;
                background-color: transparent;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #ffffff;
                color: #000000;
            }
            QLineEdit:read-only, QSpinBox:read-only, QDoubleSpinBox:read-only {
                background-color: #f5f5f5;
                color: #666666;
                border: 1px solid #dddddd;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: #ffffff;
                color: #000000;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #e6f3ff;
                border-color: #0066cc;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #cce6ff;
                border-color: #0052a3;
            }
            QPushButton#ok_button {
                background-color: #2563eb;
                color: #ffffff;
                border-color: #1e40af;
            }
            QPushButton#ok_button:hover {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QPushButton#ok_button:pressed {
                background-color: #1d4ed8;
                color: #ffffff;
            }
            QFrame[frameShape="4"] {
                color: #cccccc;
            }
        """)
    
    def apply_dark_theme(self):
        """Aplicar tema oscuro"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #3c3c3c;
                color: #ffffff;
            }
            QLineEdit:read-only, QSpinBox:read-only, QDoubleSpinBox:read-only {
                background-color: #404040;
                color: #aaaaaa;
                border: 1px solid #666666;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #555555;
                border-radius: 4px;
                background-color: #404040;
                color: #ffffff;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #0088ff;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #505050;
                border-color: #0066cc;
            }
            QPushButton#ok_button {
                background-color: #2563eb;
                color: #ffffff;
                border-color: #1e40af;
            }
            QPushButton#ok_button:hover {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QPushButton#ok_button:pressed {
                background-color: #1d4ed8;
                color: #ffffff;
            }
            QFrame[frameShape="4"] {
                color: #555555;
            }
        """)
