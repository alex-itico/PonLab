"""
Device Properties Dialog
Ventana de propiedades para dispositivos PON
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QPushButton, QGroupBox,
                             QSpinBox, QDoubleSpinBox, QFrame, QMessageBox,
                             QComboBox, QCheckBox, QTabWidget, QWidget, QScrollArea)
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

        # Ajustar tamaño según el tipo de dispositivo
        if self.device.device_type in ["ONU", "CUSTOM_ONU"]:
            self.setFixedSize(550, 700)  # Más grande para ONU con configuración de tráfico
        else:
            self.setFixedSize(500, 450)

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
        if self.device.device_type in ["OLT", "OLT_SDN", "CUSTOM_OLT"]:
            self.setup_olt_info(main_layout)
        elif self.device.device_type in ["ONU", "CUSTOM_ONU"]:
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

        # Agregar configuración de perfil de tráfico
        self.setup_traffic_profile_section(main_layout)

    def setup_traffic_profile_section(self, main_layout):
        """Configurar sección de perfil de tráfico para ONU"""
        tr = translation_manager.get_text
        
        traffic_group = QGroupBox(tr("properties_dialog.traffic_profile_title"))
        traffic_layout = QVBoxLayout(traffic_group)
        traffic_layout.setSpacing(10)

        # Selector de escenario de tráfico
        scenario_layout = QFormLayout()
        scenario_layout.setSpacing(8)

        self.traffic_scenario_combo = QComboBox()
        self.traffic_scenario_combo.addItems([
            "residential_light",
            "residential_medium",
            "residential_heavy",
            "enterprise"
        ])
        self.traffic_scenario_combo.setMinimumWidth(250)
        self.traffic_scenario_combo.currentTextChanged.connect(self.on_traffic_scenario_changed)
        scenario_layout.addRow(tr("properties_dialog.scenario_label"), self.traffic_scenario_combo)

        # Descripción del escenario
        self.scenario_description_label = QLabel()
        self.scenario_description_label.setWordWrap(True)
        self.scenario_description_label.setStyleSheet("QLabel { color: gray; font-style: italic; }")
        scenario_layout.addRow("", self.scenario_description_label)

        traffic_layout.addLayout(scenario_layout)

        # Parámetros básicos
        params_layout = QFormLayout()
        params_layout.setSpacing(8)

        # SLA
        self.sla_spinbox = QDoubleSpinBox()
        self.sla_spinbox.setRange(10.0, 10000.0)
        self.sla_spinbox.setSuffix(" Mbps")
        self.sla_spinbox.setSingleStep(10.0)
        self.sla_spinbox.setMinimumWidth(150)
        params_layout.addRow(tr("properties_dialog.sla_label"), self.sla_spinbox)

        # Buffer Size
        self.buffer_size_spinbox = QSpinBox()
        self.buffer_size_spinbox.setRange(100, 2000)
        self.buffer_size_spinbox.setSuffix(tr("properties_dialog.buffer_suffix"))
        self.buffer_size_spinbox.setSingleStep(50)
        self.buffer_size_spinbox.setMinimumWidth(150)
        params_layout.addRow(tr("properties_dialog.buffer_size_label"), self.buffer_size_spinbox)

        traffic_layout.addLayout(params_layout)

        # Checkbox para habilitar personalización
        self.use_custom_params_checkbox = QCheckBox(tr("properties_dialog.use_custom_params"))
        self.use_custom_params_checkbox.stateChanged.connect(self.on_custom_params_toggled)
        traffic_layout.addWidget(self.use_custom_params_checkbox)

        # Área de parámetros personalizados (colapsable)
        self.custom_params_widget = QWidget()
        custom_params_layout = QVBoxLayout(self.custom_params_widget)
        custom_params_layout.setContentsMargins(0, 0, 0, 0)

        # Probabilidades personalizadas
        probs_group = QGroupBox(tr("properties_dialog.traffic_probs_title"))
        probs_layout = QFormLayout(probs_group)
        probs_layout.setSpacing(5)

        self.traffic_prob_spinboxes = {}
        priority_labels = {
            'highest': tr("properties_dialog.priority_highest"),
            'high': tr("properties_dialog.priority_high"),
            'medium': tr("properties_dialog.priority_medium"),
            'low': tr("properties_dialog.priority_low"),
            'lowest': tr("properties_dialog.priority_lowest")
        }
        for traffic_type in ['highest', 'high', 'medium', 'low', 'lowest']:
            spinbox = QDoubleSpinBox()
            spinbox.setRange(0.0, 1.0)
            spinbox.setSingleStep(0.05)
            spinbox.setDecimals(2)
            spinbox.setMinimumWidth(100)
            probs_layout.addRow(f"{priority_labels[traffic_type]}:", spinbox)
            self.traffic_prob_spinboxes[traffic_type] = spinbox

        custom_params_layout.addWidget(probs_group)

        # Tamaños de tráfico personalizados
        sizes_group = QGroupBox(tr("properties_dialog.traffic_sizes_title"))
        sizes_layout = QFormLayout(sizes_group)
        sizes_layout.setSpacing(5)

        self.traffic_size_spinboxes = {}
        for traffic_type in ['highest', 'high', 'medium', 'low', 'lowest']:
            min_spinbox = QDoubleSpinBox()
            min_spinbox.setRange(0.001, 1.0)
            min_spinbox.setSingleStep(0.01)
            min_spinbox.setDecimals(3)
            min_spinbox.setMinimumWidth(80)

            max_spinbox = QDoubleSpinBox()
            max_spinbox.setRange(0.001, 1.0)
            max_spinbox.setSingleStep(0.01)
            max_spinbox.setDecimals(3)
            max_spinbox.setMinimumWidth(80)

            size_layout = QHBoxLayout()
            size_layout.addWidget(QLabel(tr("properties_dialog.min_label")))
            size_layout.addWidget(min_spinbox)
            size_layout.addWidget(QLabel(tr("properties_dialog.max_label")))
            size_layout.addWidget(max_spinbox)
            size_layout.addStretch()

            sizes_layout.addRow(f"{priority_labels[traffic_type]}:", size_layout)
            self.traffic_size_spinboxes[traffic_type] = (min_spinbox, max_spinbox)

        custom_params_layout.addWidget(sizes_group)
        traffic_layout.addWidget(self.custom_params_widget)

        # Ocultar parámetros personalizados por defecto
        self.custom_params_widget.setVisible(False)

        main_layout.addWidget(traffic_group)

    def on_traffic_scenario_changed(self, scenario_name):
        """Manejar cambio de escenario de tráfico"""
        # Importar get_traffic_scenario
        try:
            from ..core.utilities.pon_traffic import get_traffic_scenario
            scenario_config = get_traffic_scenario(scenario_name)

            # Actualizar descripción
            self.scenario_description_label.setText(scenario_config.get('description', ''))

            # Si no está usando parámetros personalizados, actualizar valores según el escenario
            if not self.use_custom_params_checkbox.isChecked():
                # Actualizar SLA con el valor medio del rango
                sla_range = scenario_config.get('sla_range', (100, 300))
                sla_default = (sla_range[0] + sla_range[1]) / 2
                self.sla_spinbox.setValue(sla_default)

                # Actualizar probabilidades
                traffic_probs_range = scenario_config.get('traffic_probs_range', {})
                for traffic_type, (min_p, max_p) in traffic_probs_range.items():
                    if traffic_type in self.traffic_prob_spinboxes:
                        # Usar valor medio del rango
                        self.traffic_prob_spinboxes[traffic_type].setValue((min_p + max_p) / 2)

                # Actualizar tamaños
                traffic_sizes_mb = scenario_config.get('traffic_sizes_mb', {})
                for traffic_type, (min_size, max_size) in traffic_sizes_mb.items():
                    if traffic_type in self.traffic_size_spinboxes:
                        min_spinbox, max_spinbox = self.traffic_size_spinboxes[traffic_type]
                        min_spinbox.setValue(min_size)
                        max_spinbox.setValue(max_size)

        except Exception as e:
            print(f"Error al cargar escenario de tráfico: {e}")

    def on_custom_params_toggled(self, state):
        """Manejar toggle de parámetros personalizados"""
        is_checked = state == Qt.Checked
        self.custom_params_widget.setVisible(is_checked)

        # Si se desactiva, recargar valores del escenario
        if not is_checked:
            current_scenario = self.traffic_scenario_combo.currentText()
            self.on_traffic_scenario_changed(current_scenario)

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
        if self.device.device_type in ["OLT", "OLT_SDN", "CUSTOM_OLT"]:
            current_transmission_rate = self.device.properties.get('transmission_rate', 4096.0)
            self.original_properties['transmission_rate'] = current_transmission_rate
            # Actualizar el campo visual con el valor actual del dispositivo
            if hasattr(self, 'transmission_rate_spinbox'):
                self.transmission_rate_spinbox.setValue(current_transmission_rate)

        # Cargar configuración de tráfico para ONUs
        if self.device.device_type in ["ONU", "CUSTOM_ONU"] and hasattr(self, 'traffic_scenario_combo'):
            # Cargar escenario de tráfico
            traffic_scenario = self.device.properties.get('traffic_scenario', 'residential_medium')
            index = self.traffic_scenario_combo.findText(traffic_scenario)
            if index >= 0:
                self.traffic_scenario_combo.setCurrentIndex(index)

            # Cargar SLA y buffer size
            self.sla_spinbox.setValue(self.device.properties.get('sla', 200.0))
            self.buffer_size_spinbox.setValue(self.device.properties.get('buffer_size', 512))

            # Cargar use_custom_params
            use_custom = self.device.properties.get('use_custom_params', False)
            self.use_custom_params_checkbox.setChecked(use_custom)

            # Cargar probabilidades personalizadas
            custom_probs = self.device.properties.get('custom_traffic_probs', {})
            for traffic_type, spinbox in self.traffic_prob_spinboxes.items():
                spinbox.setValue(custom_probs.get(traffic_type, 0.3))

            # Cargar tamaños personalizados
            custom_sizes = self.device.properties.get('custom_traffic_sizes', {})
            for traffic_type, (min_spinbox, max_spinbox) in self.traffic_size_spinboxes.items():
                size_range = custom_sizes.get(traffic_type, (0.01, 0.1))
                min_spinbox.setValue(size_range[0])
                max_spinbox.setValue(size_range[1])

            # Guardar en original_properties
            self.original_properties.update({
                'traffic_scenario': traffic_scenario,
                'sla': self.device.properties.get('sla', 200.0),
                'buffer_size': self.device.properties.get('buffer_size', 512),
                'use_custom_params': use_custom,
                'custom_traffic_probs': custom_probs,
                'custom_traffic_sizes': custom_sizes
            })
    
    def calculate_connected_onus(self):
        """Calcular número de ONUs conectadas a esta OLT"""
        if not self.connection_manager or self.device.device_type not in ["OLT", "OLT_SDN", "CUSTOM_OLT"]:
            return 0
        
        connected_count = 0
        for connection in self.connection_manager.connections:
            if (connection.device_a.id == self.device.id and connection.device_b.device_type in ["ONU", "CUSTOM_ONU"]) or \
               (connection.device_b.id == self.device.id and connection.device_a.device_type in ["ONU", "CUSTOM_ONU"]):
                connected_count += 1
        
        return connected_count
    
    def calculate_olt_distance(self):
        """Calcular distancia a la OLT conectada"""
        if not self.connection_manager or self.device.device_type not in ["ONU", "CUSTOM_ONU"]:
            return None
        
        for connection in self.connection_manager.connections:
            olt_device = None
            if connection.device_a.id == self.device.id and connection.device_b.device_type in ["OLT", "OLT_SDN", "CUSTOM_OLT"]:
                olt_device = connection.device_b
            elif connection.device_b.id == self.device.id and connection.device_a.device_type in ["OLT", "OLT_SDN", "CUSTOM_OLT"]:
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
        if self.device.device_type in ["OLT", "OLT_SDN", "CUSTOM_OLT"] and hasattr(self, 'transmission_rate_spinbox'):
            new_transmission_rate = self.transmission_rate_spinbox.value()
            new_properties['transmission_rate'] = new_transmission_rate

            # Usar el método update_property para sincronización automática
            if hasattr(self.device, 'update_property'):
                self.device.update_property('transmission_rate', new_transmission_rate)
                print(f"🔄 Transmission rate actualizada desde UI: {new_transmission_rate} Mbps")

        # Agregar configuración de tráfico si es una ONU
        if self.device.device_type in ["ONU", "CUSTOM_ONU"] and hasattr(self, 'traffic_scenario_combo'):
            # Recopilar configuración de tráfico
            traffic_scenario = self.traffic_scenario_combo.currentText()
            sla = self.sla_spinbox.value()
            buffer_size = self.buffer_size_spinbox.value()
            use_custom = self.use_custom_params_checkbox.isChecked()

            # Recopilar probabilidades personalizadas
            custom_probs = {}
            for traffic_type, spinbox in self.traffic_prob_spinboxes.items():
                custom_probs[traffic_type] = spinbox.value()

            # Recopilar tamaños personalizados
            custom_sizes = {}
            for traffic_type, (min_spinbox, max_spinbox) in self.traffic_size_spinboxes.items():
                custom_sizes[traffic_type] = (min_spinbox.value(), max_spinbox.value())

            # Actualizar propiedades del dispositivo
            self.device.properties['traffic_scenario'] = traffic_scenario
            self.device.properties['sla'] = sla
            self.device.properties['buffer_size'] = buffer_size
            self.device.properties['use_custom_params'] = use_custom
            self.device.properties['custom_traffic_probs'] = custom_probs
            self.device.properties['custom_traffic_sizes'] = custom_sizes

            # Agregar a new_properties para emitir señal
            new_properties.update({
                'traffic_scenario': traffic_scenario,
                'sla': sla,
                'buffer_size': buffer_size,
                'use_custom_params': use_custom,
                'custom_traffic_probs': custom_probs,
                'custom_traffic_sizes': custom_sizes
            })

            print(f"✅ Configuración de tráfico actualizada para {self.device.name}: {traffic_scenario}")

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
        if self.device.device_type in ["OLT", "OLT_SDN", "CUSTOM_OLT"] and hasattr(self, 'transmission_rate_spinbox'):
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
        if self.device and self.device.device_type in ["OLT", "OLT_SDN", "CUSTOM_OLT"]:
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
