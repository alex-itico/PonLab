"""
Device Properties Dialog
Ventana de propiedades para dispositivos PON
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QGroupBox, 
                             QSpinBox, QDoubleSpinBox, QFrame, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from utils.translation_manager import translation_manager
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
        tr = translation_manager.get_text
        
        self.setWindowTitle(tr('properties_dialog.title', name=self.device.name))
        self.setModal(True)
        self.setFixedSize(500, 450)  # Aumentado de 400x350 a 500x450
        
        # Eliminar botón de "What's This?" (signo de interrogación)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)  # Aumentado de 10 a 15
        main_layout.setContentsMargins(20, 20, 20, 20)  # Aumentado de 15 a 20
        
        # Título
        title_label = QLabel(tr('properties_dialog.device_properties'))
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
        tr = translation_manager.get_text
        
        basic_group = QGroupBox(tr('properties_dialog.basic_info'))
        basic_layout = QFormLayout(basic_group)
        basic_layout.setSpacing(8)  # Espaciado entre filas
        
        # ID (solo lectura)
        self.id_edit = QLineEdit(self.device.id)
        self.id_edit.setReadOnly(True)
        self.id_edit.setMinimumWidth(300)  # Ancho mínimo
        basic_layout.addRow(tr('properties_dialog.id'), self.id_edit)
        
        # Tipo (solo lectura)
        self.type_edit = QLineEdit(self.device.device_type)
        self.type_edit.setReadOnly(True)
        self.type_edit.setMinimumWidth(300)
        basic_layout.addRow(tr('properties_dialog.type'), self.type_edit)
        
        # Nombre (editable)
        self.name_edit = QLineEdit(self.device.name)
        self.name_edit.setMaxLength(50)
        self.name_edit.setMinimumWidth(300)
        basic_layout.addRow(tr('properties_dialog.name'), self.name_edit)
        
        # Coordenadas (editables)
        coord_layout = QHBoxLayout()
        coord_layout.setSpacing(10)
        
        self.x_spinbox = QDoubleSpinBox()
        self.x_spinbox.setRange(-9999.0, 9999.0)
        self.x_spinbox.setDecimals(1)
        self.x_spinbox.setSuffix(" px")
        self.x_spinbox.setValue(self.device.x)
        self.x_spinbox.setMinimumWidth(120)
        
        self.y_spinbox = QDoubleSpinBox()
        self.y_spinbox.setRange(-9999.0, 9999.0)
        self.y_spinbox.setDecimals(1)
        self.y_spinbox.setSuffix(" px")
        self.y_spinbox.setValue(self.device.y)
        self.y_spinbox.setMinimumWidth(120)
        
        coord_layout.addWidget(QLabel(tr('properties_dialog.x_label')))
        coord_layout.addWidget(self.x_spinbox)
        coord_layout.addWidget(QLabel(tr('properties_dialog.y_label')))
        coord_layout.addWidget(self.y_spinbox)
        coord_layout.addStretch()  # Espacio flexible al final
        
        basic_layout.addRow(tr('properties_dialog.coordinates'), coord_layout)
        
        main_layout.addWidget(basic_group)
    
    def setup_specific_info_section(self, main_layout):
        """Configurar sección de información específica del tipo"""
        if self.device.device_type in ["OLT", "OLT_SDN"]:
            self.setup_olt_info(main_layout)
        elif self.device.device_type == "ONU":
            self.setup_onu_info(main_layout)
    
    def setup_olt_info(self, main_layout):
        """Configurar información específica de OLT"""
        tr = translation_manager.get_text
        
        olt_group = QGroupBox(tr('properties_dialog.olt_info'))
        olt_layout = QFormLayout(olt_group)
        olt_layout.setSpacing(8)  # Espaciado entre filas
        
        # Número de ONUs conectadas (calculado)
        connected_onus = self.calculate_connected_onus()
        self.onus_edit = QLineEdit(str(connected_onus))
        self.onus_edit.setReadOnly(True)
        self.onus_edit.setMinimumWidth(200)
        olt_layout.addRow(tr('properties_dialog.connected_onus'), self.onus_edit)
        
        # Tasa de transmisión (editable)
        self.transmission_rate_spinbox = QDoubleSpinBox()
        self.transmission_rate_spinbox.setDecimals(1)
        self.transmission_rate_spinbox.setMinimum(1.0)
        self.transmission_rate_spinbox.setMaximum(100000.0)  # 100 Gbps máximo
        self.transmission_rate_spinbox.setSuffix(" Mbps")
        self.transmission_rate_spinbox.setSingleStep(512.0)  # Incrementos de 512 Mbps
        # El valor se establecerá en load_device_data() para reflejar el valor actual
        self.transmission_rate_spinbox.setValue(4096.0)  # Valor temporal, se actualiza en load_device_data()
        self.transmission_rate_spinbox.setMinimumWidth(200)
        
        # Conectar la señal para actualización en tiempo real
        self.transmission_rate_spinbox.valueChanged.connect(self.on_transmission_rate_changed)
        
        olt_layout.addRow(tr('properties_dialog.transmission_rate'), self.transmission_rate_spinbox)
        
        main_layout.addWidget(olt_group)
    
    def setup_onu_info(self, main_layout):
        """Configurar información específica de ONU"""
        tr = translation_manager.get_text
        
        onu_group = QGroupBox(tr('properties_dialog.onu_info'))
        onu_layout = QFormLayout(onu_group)
        onu_layout.setSpacing(8)  # Espaciado entre filas
        
        # Distancia de la OLT conectada (calculado)
        olt_distance = self.calculate_olt_distance()
        distance_text = f"{olt_distance:.1f} m" if olt_distance is not None else tr('properties_dialog.not_connected')
        self.distance_edit = QLineEdit(distance_text)
        self.distance_edit.setReadOnly(True)
        self.distance_edit.setMinimumWidth(200)
        onu_layout.addRow(tr('properties_dialog.distance_to_olt'), self.distance_edit)
        
        main_layout.addWidget(onu_group)
    
    def setup_buttons(self, main_layout):
        """Configurar botones del diálogo"""
        tr = translation_manager.get_text
        
        # Agregar espacio flexible antes de los botones
        main_layout.addStretch()
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)  # Espaciado entre botones
        buttons_layout.addStretch()
        
        # Botón Cancelar
        self.cancel_button = QPushButton(tr('properties_dialog.cancel'))
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # Botón OK
        self.ok_button = QPushButton(tr('properties_dialog.save'))
        self.ok_button.setObjectName("ok_button")
        self.ok_button.setMinimumWidth(100)
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
        
        # Agregar transmission_rate para OLTs
        if self.device.device_type in ["OLT", "OLT_SDN"]:
            current_transmission_rate = self.device.properties.get('transmission_rate', 4096.0)
            self.original_properties['transmission_rate'] = current_transmission_rate
            # Actualizar el campo visual con el valor actual del dispositivo
            if hasattr(self, 'transmission_rate_spinbox'):
                self.transmission_rate_spinbox.setValue(current_transmission_rate)
    
    def calculate_connected_onus(self):
        """Calcular número de ONUs conectadas a esta OLT"""
        if not self.connection_manager or self.device.device_type not in ["OLT", "OLT_SDN"]:
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
            if connection.device_a.id == self.device.id and connection.device_b.device_type in ["OLT", "OLT_SDN"]:
                olt_device = connection.device_b
            elif connection.device_b.id == self.device.id and connection.device_a.device_type in ["OLT", "OLT_SDN"]:
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
        
        # Agregar transmission_rate si es un OLT
        if self.device.device_type in ["OLT", "OLT_SDN"] and hasattr(self, 'transmission_rate_spinbox'):
            new_transmission_rate = self.transmission_rate_spinbox.value()
            new_properties['transmission_rate'] = new_transmission_rate
            
            # Usar el método update_property para sincronización automática
            if hasattr(self.device, 'update_property'):
                self.device.update_property('transmission_rate', new_transmission_rate)
                print(f"🔄 Transmission rate actualizada desde UI: {new_transmission_rate} Mbps")
        
        # Emitir señal con cambios
        self.properties_updated.emit(self.device.id, new_properties)
        
        # Cerrar diálogo
        self.accept()
    
    def validate_data(self):
        """Validar todos los datos antes de guardar"""
        tr = translation_manager.get_text
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, tr('properties_dialog.validation_error'), 
                              tr('properties_dialog.empty_name_error'))
            return False
        
        # Validar transmission_rate para OLTs
        if self.device.device_type in ["OLT", "OLT_SDN"] and hasattr(self, 'transmission_rate_spinbox'):
            transmission_rate = self.transmission_rate_spinbox.value()
            if transmission_rate <= 0:
                QMessageBox.warning(self, tr('properties_dialog.validation_error'), 
                                  tr('properties_dialog.invalid_rate_error'))
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
    
    def on_transmission_rate_changed(self, value):
        """Manejar cambios en tiempo real del transmission_rate"""
        if self.device and self.device.device_type in ["OLT", "OLT_SDN"]:
            # Actualizar la propiedad inmediatamente
            self.device.properties['transmission_rate'] = float(value)
            
            # Emitir la señal para actualizar el sidebar
            new_properties = {'transmission_rate': float(value)}
            self.properties_updated.emit(self.device.id, new_properties)
    
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
