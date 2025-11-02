"""
Diálogo para crear/editar dispositivos OLT personalizados
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QSpinBox, QPushButton, QFrame, QMessageBox, QGridLayout,
    QSlider, QRadioButton, QGroupBox, QButtonGroup
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QByteArray
from PyQt5.QtGui import QFont, QColor, QPalette, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from utils.custom_device_manager import custom_device_manager
from utils.translation_manager import tr
import os


class ColorButton(QPushButton):
    """Botón de color para el selector embebido"""
    
    color_selected = pyqtSignal(QColor)
    
    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()
        self.clicked.connect(lambda: self.color_selected.emit(self.color))
    
    def update_style(self):
        """Actualizar estilo del botón"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.name()};
                border: 2px solid #999999;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #000000;
            }}
        """)


class CustomOLTDialog(QDialog):
    """Diálogo modal para crear/editar OLT personalizado con selector de color integrado"""
    
    device_saved = pyqtSignal(dict)  # Emite el dispositivo guardado
    
    def __init__(self, parent=None, device_data=None, dark_theme=False):
        super().__init__(parent)
        self.device_data = device_data  # None = crear, Dict = editar
        self.dark_theme = dark_theme
        self.is_edit_mode = device_data is not None
        self.selected_color = QColor("#4a90e2")  # Color por defecto (azul)
        self.selected_standard = None  # Estándar PON seleccionado (None = manual)
        
        self.setup_ui()
        self.set_theme(dark_theme)
        
        # Cargar datos si es modo edición
        if self.is_edit_mode:
            self.load_device_data()
    
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        # Configuración del diálogo
        title = tr('custom_device.dialog_title_edit') if self.is_edit_mode else tr('custom_device.dialog_title_new_olt')
        self.setWindowTitle(title)
        self.setModal(True)  # Modal - no se puede cerrar sin acción
        self.setMinimumWidth(500)
        self.setMaximumWidth(650)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Título sin fondo
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        self.separator = separator
        
        # ===== FORMULARIO CON COLOR A LA DERECHA =====
        form_layout = QHBoxLayout()
        form_layout.setSpacing(15)
        
        # === Lado izquierdo: Propiedades ===
        properties_layout = QVBoxLayout()
        properties_layout.setSpacing(12)
        
        # Campo: Nombre
        name_layout = QHBoxLayout()
        name_label = QLabel(tr('custom_device.name_label'))
        name_label.setFixedWidth(120)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr('custom_device.name_placeholder_olt'))
        self.name_input.setMinimumHeight(35)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        properties_layout.addLayout(name_layout)
        
        # Campo: Tasa de Transmisión
        rate_layout = QHBoxLayout()
        rate_label = QLabel(tr('custom_device.transmission_rate_label'))
        rate_label.setFixedWidth(120)
        self.rate_input = QSpinBox()
        self.rate_input.setRange(1, 100000)
        self.rate_input.setValue(1000)
        self.rate_input.setSuffix(" Mbps")
        self.rate_input.setMinimumHeight(35)
        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.rate_input)
        properties_layout.addLayout(rate_layout)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        properties_layout.addWidget(separator)
        
        # === Estándares Predefinidos ===
        standards_label = QLabel(tr('custom_device.predefined_standards'))
        standards_label_font = QFont()
        standards_label_font.setBold(True)
        standards_label_font.setPointSize(9)
        standards_label.setFont(standards_label_font)
        properties_layout.addWidget(standards_label)
        
        # Grupo de radio buttons
        self.standards_group = QGroupBox()
        self.standards_group.setFlat(True)
        standards_group_layout = QVBoxLayout()
        standards_group_layout.setSpacing(6)
        standards_group_layout.setContentsMargins(10, 5, 10, 5)
        
        # Definir estándares PON con sus tasas
        self.pon_standards = {
            'EPON': 1250,      # 1.25 Gbps = 1250 Mbps
            'GPON': 1250,      # 1.25 Gbps = 1250 Mbps
            'XG-PON': 2500,    # 2.5 Gbps = 2500 Mbps
            'NG-PON2': 10000   # 10 Gbps = 10000 Mbps
        }
        
        # Crear QButtonGroup para poder deseleccionar radio buttons
        self.standards_button_group = QButtonGroup(self)
        self.standards_button_group.setExclusive(True)  # Solo uno seleccionado a la vez
        
        # Crear radio buttons para cada estándar
        self.standard_radios = {}
        for standard, rate in self.pon_standards.items():
            radio = QRadioButton(f"{standard} ({rate} Mbps)")
            radio.toggled.connect(lambda checked, s=standard, r=rate: self.on_standard_selected(checked, s, r))
            standards_group_layout.addWidget(radio)
            self.standard_radios[standard] = radio
            self.standards_button_group.addButton(radio)  # Agregar al grupo
        
        self.standards_group.setLayout(standards_group_layout)
        properties_layout.addWidget(self.standards_group)
        
        # Botón para deseleccionar
        deselect_button = QPushButton(tr('custom_device.deselect_standard'))
        deselect_button.setFixedHeight(30)
        deselect_button.clicked.connect(self.on_deselect_standard)
        properties_layout.addWidget(deselect_button)
        
        properties_layout.addStretch()
        
        form_layout.addLayout(properties_layout, 3)  # 60% del espacio
        
        # === Lado derecho: Selector de Color Embebido ===
        color_layout = QVBoxLayout()
        color_layout.setSpacing(8)
        color_layout.setAlignment(Qt.AlignTop)
        
        color_title = QLabel(tr('custom_device.device_color'))
        color_title_font = QFont()
        color_title_font.setBold(True)
        color_title_font.setPointSize(10)
        color_title.setFont(color_title_font)
        color_title.setAlignment(Qt.AlignCenter)
        color_layout.addWidget(color_title)
        
        # Vista previa con SVG del OLT
        self.svg_path = os.path.join('resources', 'devices', 'olt_icon_custom.svg')
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(140, 140)
        self.color_preview.setAlignment(Qt.AlignCenter)
        self.update_color_preview()
        color_layout.addWidget(self.color_preview, alignment=Qt.AlignCenter)
        
        # Etiqueta "Seleccionar:"
        select_label = QLabel(tr('custom_device.select_color_label'))
        select_label.setAlignment(Qt.AlignCenter)
        select_label_font = QFont()
        select_label_font.setPointSize(9)
        select_label.setFont(select_label_font)
        color_layout.addWidget(select_label)
        
        # Paleta de colores embebida (4x5 = 20 colores)
        colors_grid = QGridLayout()
        colors_grid.setSpacing(4)
        
        # Colores predefinidos (20 colores comunes)
        preset_colors = [
            "#FF0000", "#FF6B00", "#FFD700", "#90EE90", "#00FF00",  # Fila 1: Rojos, naranjas, amarillos, verdes
            "#00CED1", "#4A90E2", "#0000FF", "#8A2BE2", "#FF00FF",  # Fila 2: Cianos, azules, morados
            "#FF1493", "#FF69B4", "#FFA500", "#32CD32", "#00FA9A",  # Fila 3: Rosas, naranjas, verdes
            "#1E90FF", "#9370DB", "#DC143C", "#808080", "#000000"   # Fila 4: Azules, morados, rojos, grises
        ]
        
        row = 0
        col = 0
        for color_hex in preset_colors:
            color_btn = ColorButton(QColor(color_hex), self)
            color_btn.color_selected.connect(self.on_color_selected)
            colors_grid.addWidget(color_btn, row, col)
            
            col += 1
            if col >= 5:  # 5 columnas
                col = 0
                row += 1
        
        color_layout.addLayout(colors_grid)
        
        # ===== CONTROLES RGB =====
        rgb_label = QLabel(tr('custom_device.rgb_adjusters'))
        rgb_label.setAlignment(Qt.AlignCenter)
        rgb_label_font = QFont()
        rgb_label_font.setPointSize(9)
        rgb_label_font.setBold(True)
        rgb_label.setFont(rgb_label_font)
        color_layout.addWidget(rgb_label)
        
        # Slider R (Rojo)
        r_layout = QHBoxLayout()
        r_layout.setSpacing(5)
        r_label = QLabel("R:")
        r_label.setFixedWidth(15)
        r_label_font = QFont()
        r_label_font.setBold(True)
        r_label.setFont(r_label_font)
        r_layout.addWidget(r_label)
        
        self.r_slider = QSlider(Qt.Horizontal)
        self.r_slider.setRange(0, 255)
        self.r_slider.setValue(self.selected_color.red())
        self.r_slider.valueChanged.connect(self.on_rgb_changed)
        r_layout.addWidget(self.r_slider)
        
        self.r_value_label = QLabel(str(self.selected_color.red()))
        self.r_value_label.setFixedWidth(30)
        self.r_value_label.setAlignment(Qt.AlignCenter)
        r_layout.addWidget(self.r_value_label)
        
        color_layout.addLayout(r_layout)
        
        # Slider G (Verde)
        g_layout = QHBoxLayout()
        g_layout.setSpacing(5)
        g_label = QLabel("G:")
        g_label.setFixedWidth(15)
        g_label_font = QFont()
        g_label_font.setBold(True)
        g_label.setFont(g_label_font)
        g_layout.addWidget(g_label)
        
        self.g_slider = QSlider(Qt.Horizontal)
        self.g_slider.setRange(0, 255)
        self.g_slider.setValue(self.selected_color.green())
        self.g_slider.valueChanged.connect(self.on_rgb_changed)
        g_layout.addWidget(self.g_slider)
        
        self.g_value_label = QLabel(str(self.selected_color.green()))
        self.g_value_label.setFixedWidth(30)
        self.g_value_label.setAlignment(Qt.AlignCenter)
        g_layout.addWidget(self.g_value_label)
        
        color_layout.addLayout(g_layout)
        
        # Slider B (Azul)
        b_layout = QHBoxLayout()
        b_layout.setSpacing(5)
        b_label = QLabel("B:")
        b_label.setFixedWidth(15)
        b_label_font = QFont()
        b_label_font.setBold(True)
        b_label.setFont(b_label_font)
        b_layout.addWidget(b_label)
        
        self.b_slider = QSlider(Qt.Horizontal)
        self.b_slider.setRange(0, 255)
        self.b_slider.setValue(self.selected_color.blue())
        self.b_slider.valueChanged.connect(self.on_rgb_changed)
        b_layout.addWidget(self.b_slider)
        
        self.b_value_label = QLabel(str(self.selected_color.blue()))
        self.b_value_label.setFixedWidth(30)
        self.b_value_label.setAlignment(Qt.AlignCenter)
        b_layout.addWidget(self.b_value_label)
        
        color_layout.addLayout(b_layout)
        
        # Código hexadecimal del color (editable)
        hex_layout = QHBoxLayout()
        hex_label = QLabel("Hex:")
        hex_label.setFixedWidth(35)
        hex_layout.addWidget(hex_label)
        
        self.hex_input = QLineEdit(self.selected_color.name().upper())
        self.hex_input.setAlignment(Qt.AlignCenter)
        self.hex_input.setMaxLength(7)  # #RRGGBB
        self.hex_input.setPlaceholderText("#RRGGBB")
        hex_input_font = QFont()
        hex_input_font.setFamily("Courier New")
        self.hex_input.setFont(hex_input_font)
        self.hex_input.editingFinished.connect(self.on_hex_edited)
        hex_layout.addWidget(self.hex_input)
        
        color_layout.addLayout(hex_layout)
        
        color_layout.addStretch()
        
        form_layout.addLayout(color_layout, 2)  # 40% del espacio
        
        main_layout.addLayout(form_layout)
        
        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFixedHeight(1)
        main_layout.addWidget(separator2)
        self.separator2 = separator2
        
        # ===== BOTONES =====
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Botón Cancelar
        self.cancel_button = QPushButton(tr('custom_device.cancel'))
        self.cancel_button.setFixedWidth(120)
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        # Botón Guardar
        save_text = tr('custom_device.update') if self.is_edit_mode else tr('custom_device.save')
        self.save_button = QPushButton(save_text)
        self.save_button.setFixedWidth(120)
        self.save_button.setFixedHeight(40)
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_device)
        buttons_layout.addWidget(self.save_button)
        
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
    
    def on_color_selected(self, color):
        """Manejar selección de color desde la paleta embebida"""
        self.selected_color = color
        self.update_rgb_sliders()
        self.update_color_preview()
    
    def on_rgb_changed(self):
        """Manejar cambio en los sliders RGB"""
        r = self.r_slider.value()
        g = self.g_slider.value()
        b = self.b_slider.value()
        
        self.selected_color = QColor(r, g, b)
        
        # Actualizar etiquetas de valores
        self.r_value_label.setText(str(r))
        self.g_value_label.setText(str(g))
        self.b_value_label.setText(str(b))
        
        self.update_color_preview()
    
    def on_hex_edited(self):
        """Se ejecuta cuando el usuario termina de editar el código hex"""
        hex_text = self.hex_input.text().strip().upper()
        
        # Asegurar que empiece con #
        if not hex_text.startswith('#'):
            hex_text = '#' + hex_text
        
        # Validar formato hexadecimal
        if QColor.isValidColor(hex_text):
            # Aplicar el color
            self.selected_color = QColor(hex_text)
            self.update_color_preview()
            self.update_rgb_sliders()
        else:
            # Si el formato es inválido, restaurar el color actual
            self.hex_input.setText(self.selected_color.name().upper())
    
    def on_standard_selected(self, checked, standard, rate):
        """Manejar selección de estándar PON"""
        if checked:
            # Actualizar estándar seleccionado
            self.selected_standard = standard
            
            # Establecer tasa de transmisión automáticamente
            self.rate_input.setValue(rate)
            
            # Bloquear el campo de tasa para evitar cambios manuales
            self.rate_input.setEnabled(False)
            
            # Cambiar estilo visual para indicar que está bloqueado
            self.rate_input.setStyleSheet("background-color: #f0f0f0;")
    
    def on_deselect_standard(self):
        """Deseleccionar estándar PON y permitir configuración manual"""
        # Deseleccionar el botón activo del grupo
        # setExclusive(False) temporalmente para poder deseleccionar
        self.standards_button_group.setExclusive(False)
        
        # Deseleccionar todos los radio buttons
        for radio in self.standard_radios.values():
            radio.setChecked(False)
        
        # Restaurar exclusividad
        self.standards_button_group.setExclusive(True)
        
        # Limpiar estándar seleccionado
        self.selected_standard = None
        
        # Desbloquear campo de tasa para edición manual
        self.rate_input.setEnabled(True)
        
        # Restaurar estilo normal
        self.rate_input.setStyleSheet("")
    
    def update_rgb_sliders(self):
        """Actualizar sliders RGB con el color seleccionado"""
        # Bloquear señales temporalmente para evitar bucles
        self.r_slider.blockSignals(True)
        self.g_slider.blockSignals(True)
        self.b_slider.blockSignals(True)
        
        self.r_slider.setValue(self.selected_color.red())
        self.g_slider.setValue(self.selected_color.green())
        self.b_slider.setValue(self.selected_color.blue())
        
        self.r_value_label.setText(str(self.selected_color.red()))
        self.g_value_label.setText(str(self.selected_color.green()))
        self.b_value_label.setText(str(self.selected_color.blue()))
        self.hex_input.setText(self.selected_color.name().upper())
        
        # Reactivar señales
        self.r_slider.blockSignals(False)
        self.g_slider.blockSignals(False)
        self.b_slider.blockSignals(False)
    
    def update_color_preview(self):
        """Actualizar vista previa del SVG con el color seleccionado"""
        try:
            # Leer el archivo SVG
            with open(self.svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Reemplazar los colores principales del SVG con el color seleccionado
            # El SVG tiene colores #C62828 (rojo oscuro) y #F44336 (rojo claro)
            # Los reemplazamos con versiones del color seleccionado
            base_color = self.selected_color
            
            # Color oscuro (80% del brillo original)
            dark_color = QColor(
                int(base_color.red() * 0.8),
                int(base_color.green() * 0.8),
                int(base_color.blue() * 0.8)
            )
            
            # Reemplazar colores en el SVG
            svg_content = svg_content.replace('#C62828', dark_color.name())
            svg_content = svg_content.replace('#F44336', base_color.name())
            
            # Renderizar el SVG modificado
            svg_bytes = QByteArray(svg_content.encode('utf-8'))
            renderer = QSvgRenderer(svg_bytes)
            
            # Crear pixmap y renderizar
            pixmap = QPixmap(140, 140)
            pixmap.fill(Qt.transparent)
            
            from PyQt5.QtGui import QPainter
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            self.color_preview.setPixmap(pixmap)
            
        except Exception as e:
            print(f"Error actualizando preview SVG: {e}")
        
        # Actualizar campo hex si ya existe (puede no existir durante la inicialización)
        if hasattr(self, 'hex_input'):
            self.hex_input.blockSignals(True)
            self.hex_input.setText(self.selected_color.name().upper())
            self.hex_input.blockSignals(False)
    
    def load_device_data(self):
        """Cargar datos del dispositivo en modo edición"""
        if not self.device_data:
            return
        
        self.name_input.setText(self.device_data.get('name', ''))
        self.rate_input.setValue(self.device_data.get('transmission_rate', 1000))
        
        # Cargar color si existe
        color_hex = self.device_data.get('color', '#4a90e2')
        self.selected_color = QColor(color_hex)
        self.update_rgb_sliders()
        self.update_color_preview()
        
        # Cargar estándar PON si existe
        standard = self.device_data.get('standard', None)
        if standard and standard in self.standard_radios:
            # Seleccionar el radio button correspondiente
            self.standard_radios[standard].setChecked(True)
            # El campo de tasa ya está bloqueado por la señal toggled
    
    def validate_inputs(self) -> bool:
        """Validar campos del formulario"""
        # Validar nombre
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                tr('custom_device.validation_error'),
                tr('custom_device.name_required')
            )
            self.name_input.setFocus()
            return False
        
        if len(name) < 3:
            QMessageBox.warning(
                self,
                tr('custom_device.validation_error'),
                tr('custom_device.name_too_short')
            )
            self.name_input.setFocus()
            return False
        
        # Validar tasa de transmisión
        if self.rate_input.value() <= 0:
            QMessageBox.warning(
                self,
                tr('custom_device.validation_error'),
                tr('custom_device.invalid_transmission_rate')
            )
            self.rate_input.setFocus()
            return False
        
        return True
    
    def save_device(self):
        """Guardar dispositivo (crear o actualizar)"""
        # Validar
        if not self.validate_inputs():
            return
        
        # Recopilar datos simplificados
        device_data = {
            'name': self.name_input.text().strip(),
            'transmission_rate': self.rate_input.value(),
            'color': self.selected_color.name(),  # Guardar color en formato #RRGGBB
            'standard': self.selected_standard  # Guardar estándar PON seleccionado (None si manual)
        }
        
        try:
            if self.is_edit_mode:
                # Actualizar dispositivo existente
                device_id = self.device_data['id']
                saved_device = custom_device_manager.update_custom_olt(device_id, device_data)
            else:
                # Crear nuevo dispositivo
                saved_device = custom_device_manager.save_custom_olt(device_data)
            
            if saved_device:
                # Emitir señal con el dispositivo guardado
                self.device_saved.emit(saved_device)
                
                # Cerrar diálogo
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    tr('custom_device.save_error'),
                    tr('custom_device.save_error_message')
                )
        
        except ValueError as e:
            # Error de validación (nombre duplicado, etc.)
            QMessageBox.warning(
                self,
                tr('custom_device.validation_error'),
                str(e)
            )
            self.name_input.setFocus()
        
        except Exception as e:
            # Error general
            QMessageBox.critical(
                self,
                tr('custom_device.save_error'),
                f"{tr('custom_device.save_error_message')}\n\n{str(e)}"
            )
    
    def set_theme(self, dark_theme):
        """Aplicar tema al diálogo"""
        self.dark_theme = dark_theme
        
        if dark_theme:
            self.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
                QLineEdit, QSpinBox {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px;
                    border-radius: 4px;
                }
                QLineEdit:focus, QSpinBox:focus {
                    border: 2px solid #4a90e2;
                }
                QPushButton {
                    background-color: #4a90e2;
                    color: #ffffff;
                    border: none;
                    padding: 8px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a9ff2;
                }
                QPushButton:pressed {
                    background-color: #3a80d2;
                }
                QSlider::groove:horizontal {
                    background: #3c3c3c;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #4a90e2;
                    width: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QSlider::handle:horizontal:hover {
                    background: #5a9ff2;
                }
            """)
            # Separadores oscuros sutiles
            self.separator.setStyleSheet("background-color: #444444; border: none;")
            self.separator2.setStyleSheet("background-color: #444444; border: none;")
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                    background: transparent;
                }
                QLineEdit, QSpinBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    padding: 6px;
                    border-radius: 4px;
                }
                QLineEdit:focus, QSpinBox:focus {
                    border: 2px solid #4a90e2;
                }
                QPushButton {
                    background-color: #4a90e2;
                    color: #ffffff;
                    border: none;
                    padding: 8px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a9ff2;
                }
                QPushButton:pressed {
                    background-color: #3a80d2;
                }
                QSlider::groove:horizontal {
                    background: #e0e0e0;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #4a90e2;
                    width: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QSlider::handle:horizontal:hover {
                    background: #5a9ff2;
                }
            """)
            # Separadores claros sutiles
            self.separator.setStyleSheet("background-color: #e0e0e0; border: none;")
            self.separator2.setStyleSheet("background-color: #e0e0e0; border: none;")


class CustomONUDialog(QDialog):
    """Diálogo modal para crear/editar ONU personalizado con selector de color integrado"""
    
    device_saved = pyqtSignal(dict)  # Emite el dispositivo guardado
    
    def __init__(self, parent=None, device_data=None, dark_theme=False):
        super().__init__(parent)
        self.device_data = device_data  # None = crear, Dict = editar
        self.dark_theme = dark_theme
        self.is_edit_mode = device_data is not None
        self.selected_color = QColor("#ff9800")  # Color por defecto (naranja para ONU)
        
        self.setup_ui()
        self.set_theme(dark_theme)
        
        # Cargar datos si es modo edición
        if self.is_edit_mode:
            self.load_device_data()
    
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        # Configuración del diálogo
        title = tr('custom_device.dialog_title_edit') if self.is_edit_mode else tr('custom_device.dialog_title_new_onu')
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setMaximumWidth(650)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        self.separator = separator
        
        # ===== FORMULARIO CON COLOR A LA DERECHA =====
        form_layout = QHBoxLayout()
        form_layout.setSpacing(20)
        
        # === Lado izquierdo: Propiedades (40%) ===
        properties_layout = QVBoxLayout()
        properties_layout.setSpacing(12)
        properties_layout.setAlignment(Qt.AlignTop)
        
        # Campo: Nombre
        name_label = QLabel(tr('custom_device.name_label'))
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        properties_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(tr('custom_device.name_placeholder_onu'))
        self.name_input.setFixedHeight(35)
        properties_layout.addWidget(self.name_input)
        
        properties_layout.addStretch()
        
        form_layout.addLayout(properties_layout, 2)  # 40% del espacio
        
        # === Lado derecho: Selector de Color Embebido (60%) ===
        color_layout = QVBoxLayout()
        color_layout.setSpacing(8)
        color_layout.setAlignment(Qt.AlignTop)
        
        color_title = QLabel(tr('custom_device.device_color'))
        color_title_font = QFont()
        color_title_font.setBold(True)
        color_title_font.setPointSize(10)
        color_title.setFont(color_title_font)
        color_title.setAlignment(Qt.AlignCenter)
        color_layout.addWidget(color_title)
        
        # Vista previa con SVG del ONU
        self.svg_path = os.path.join('resources', 'devices', 'onu_icon_custom.svg')
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(140, 140)
        self.color_preview.setAlignment(Qt.AlignCenter)
        self.update_color_preview()
        color_layout.addWidget(self.color_preview, alignment=Qt.AlignCenter)
        
        # Etiqueta "Seleccionar:"
        select_label = QLabel(tr('custom_device.select_color_label'))
        select_label.setAlignment(Qt.AlignCenter)
        select_label_font = QFont()
        select_label_font.setPointSize(9)
        select_label.setFont(select_label_font)
        color_layout.addWidget(select_label)
        
        # Paleta de colores embebida (4x5 = 20 colores)
        colors_grid = QGridLayout()
        colors_grid.setSpacing(4)
        
        # Colores predefinidos para ONUs (tonos cálidos y naranja)
        preset_colors = [
            "#FF0000", "#FF6B00", "#FFD700", "#90EE90", "#00FF00",  # Fila 1
            "#00CED1", "#4A90E2", "#0000FF", "#8A2BE2", "#FF00FF",  # Fila 2
            "#FF1493", "#FF69B4", "#FFA500", "#32CD32", "#00FA9A",  # Fila 3
            "#1E90FF", "#9370DB", "#DC143C", "#808080", "#000000"   # Fila 4
        ]
        
        row = 0
        col = 0
        for color_hex in preset_colors:
            color_btn = ColorButton(QColor(color_hex), self)
            color_btn.color_selected.connect(self.on_color_selected)
            colors_grid.addWidget(color_btn, row, col)
            
            col += 1
            if col >= 5:  # 5 columnas
                col = 0
                row += 1
        
        color_layout.addLayout(colors_grid)
        
        # ===== CONTROLES RGB =====
        rgb_label = QLabel(tr('custom_device.rgb_adjusters'))
        rgb_label.setAlignment(Qt.AlignCenter)
        rgb_label_font = QFont()
        rgb_label_font.setPointSize(9)
        rgb_label_font.setBold(True)
        rgb_label.setFont(rgb_label_font)
        color_layout.addWidget(rgb_label)
        
        # Slider R (Rojo)
        r_layout = QHBoxLayout()
        r_layout.setSpacing(5)
        r_label = QLabel("R:")
        r_label.setFixedWidth(15)
        r_label_font = QFont()
        r_label_font.setBold(True)
        r_label.setFont(r_label_font)
        r_layout.addWidget(r_label)
        
        self.r_slider = QSlider(Qt.Horizontal)
        self.r_slider.setRange(0, 255)
        self.r_slider.setValue(self.selected_color.red())
        self.r_slider.valueChanged.connect(self.on_rgb_changed)
        r_layout.addWidget(self.r_slider)
        
        self.r_value_label = QLabel(str(self.selected_color.red()))
        self.r_value_label.setFixedWidth(30)
        self.r_value_label.setAlignment(Qt.AlignRight)
        r_layout.addWidget(self.r_value_label)
        color_layout.addLayout(r_layout)
        
        # Slider G (Verde)
        g_layout = QHBoxLayout()
        g_layout.setSpacing(5)
        g_label = QLabel("G:")
        g_label.setFixedWidth(15)
        g_label_font = QFont()
        g_label_font.setBold(True)
        g_label.setFont(g_label_font)
        g_layout.addWidget(g_label)
        
        self.g_slider = QSlider(Qt.Horizontal)
        self.g_slider.setRange(0, 255)
        self.g_slider.setValue(self.selected_color.green())
        self.g_slider.valueChanged.connect(self.on_rgb_changed)
        g_layout.addWidget(self.g_slider)
        
        self.g_value_label = QLabel(str(self.selected_color.green()))
        self.g_value_label.setFixedWidth(30)
        self.g_value_label.setAlignment(Qt.AlignRight)
        g_layout.addWidget(self.g_value_label)
        color_layout.addLayout(g_layout)
        
        # Slider B (Azul)
        b_layout = QHBoxLayout()
        b_layout.setSpacing(5)
        b_label = QLabel("B:")
        b_label.setFixedWidth(15)
        b_label_font = QFont()
        b_label_font.setBold(True)
        b_label.setFont(b_label_font)
        b_layout.addWidget(b_label)
        
        self.b_slider = QSlider(Qt.Horizontal)
        self.b_slider.setRange(0, 255)
        self.b_slider.setValue(self.selected_color.blue())
        self.b_slider.valueChanged.connect(self.on_rgb_changed)
        b_layout.addWidget(self.b_slider)
        
        self.b_value_label = QLabel(str(self.selected_color.blue()))
        self.b_value_label.setFixedWidth(30)
        self.b_value_label.setAlignment(Qt.AlignRight)
        b_layout.addWidget(self.b_value_label)
        color_layout.addLayout(b_layout)
        
        # Código hexadecimal editable
        hex_layout = QHBoxLayout()
        hex_layout.setSpacing(5)
        hex_label = QLabel("HEX:")
        hex_label.setFixedWidth(35)
        hex_layout.addWidget(hex_label)
        
        self.hex_input = QLineEdit()
        self.hex_input.setText(self.selected_color.name().upper())
        self.hex_input.setMaxLength(7)
        self.hex_input.setFixedWidth(80)
        self.hex_input.editingFinished.connect(self.on_hex_edited)
        hex_layout.addWidget(self.hex_input)
        hex_layout.addStretch()
        color_layout.addLayout(hex_layout)
        
        form_layout.addLayout(color_layout, 3)  # 60% del espacio
        
        main_layout.addLayout(form_layout)
        
        # Separador antes de botones
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFixedHeight(1)
        main_layout.addWidget(separator2)
        self.separator2 = separator2
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_button = QPushButton(tr('custom_device.cancel'))
        cancel_button.setFixedWidth(120)
        cancel_button.setFixedHeight(40)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        save_button_text = tr('custom_device.update') if self.is_edit_mode else tr('custom_device.save')
        save_button = QPushButton(save_button_text)
        save_button.setFixedWidth(120)
        save_button.setFixedHeight(40)
        save_button.clicked.connect(self.save_device)
        buttons_layout.addWidget(save_button)
        
        main_layout.addLayout(buttons_layout)
    
    def on_color_selected(self, color):
        """Manejar selección de color desde la paleta embebida"""
        self.selected_color = color
        self.update_rgb_sliders()
        self.update_color_preview()
    
    def on_rgb_changed(self):
        """Manejar cambio en los sliders RGB"""
        r = self.r_slider.value()
        g = self.g_slider.value()
        b = self.b_slider.value()
        
        self.selected_color = QColor(r, g, b)
        
        # Actualizar etiquetas de valores
        self.r_value_label.setText(str(r))
        self.g_value_label.setText(str(g))
        self.b_value_label.setText(str(b))
        
        self.update_color_preview()
    
    def on_hex_edited(self):
        """Se ejecuta cuando el usuario termina de editar el código hex"""
        hex_text = self.hex_input.text().strip().upper()
        
        # Asegurar que empiece con #
        if not hex_text.startswith('#'):
            hex_text = '#' + hex_text
        
        # Validar formato hexadecimal
        if QColor.isValidColor(hex_text):
            # Aplicar el color
            self.selected_color = QColor(hex_text)
            self.update_color_preview()
            self.update_rgb_sliders()
        else:
            # Si el formato es inválido, restaurar el color actual
            self.hex_input.setText(self.selected_color.name().upper())
    
    def update_rgb_sliders(self):
        """Actualizar sliders RGB con el color seleccionado"""
        # Bloquear señales temporalmente para evitar bucles
        self.r_slider.blockSignals(True)
        self.g_slider.blockSignals(True)
        self.b_slider.blockSignals(True)
        
        self.r_slider.setValue(self.selected_color.red())
        self.g_slider.setValue(self.selected_color.green())
        self.b_slider.setValue(self.selected_color.blue())
        
        self.r_value_label.setText(str(self.selected_color.red()))
        self.g_value_label.setText(str(self.selected_color.green()))
        self.b_value_label.setText(str(self.selected_color.blue()))
        self.hex_input.setText(self.selected_color.name().upper())
        
        # Reactivar señales
        self.r_slider.blockSignals(False)
        self.g_slider.blockSignals(False)
        self.b_slider.blockSignals(False)
    
    def update_color_preview(self):
        """Actualizar vista previa del icono ONU con color personalizado"""
        if not os.path.exists(self.svg_path):
            return
        
        try:
            # Leer el archivo SVG
            with open(self.svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Reemplazar los colores principales del SVG con el color seleccionado
            # El SVG de ONU tiene colores #E65100 (naranja oscuro) y #FF9800 (naranja claro)
            # Los reemplazamos con versiones del color seleccionado
            base_color = self.selected_color
            
            # Color oscuro (80% del brillo original)
            dark_color = QColor(
                int(base_color.red() * 0.8),
                int(base_color.green() * 0.8),
                int(base_color.blue() * 0.8)
            )
            
            # Reemplazar colores en el SVG
            svg_content = svg_content.replace('#E65100', dark_color.name())
            svg_content = svg_content.replace('#FF9800', base_color.name())
            
            # Renderizar el SVG modificado
            svg_bytes = QByteArray(svg_content.encode('utf-8'))
            renderer = QSvgRenderer(svg_bytes)
            
            # Crear pixmap y renderizar
            pixmap = QPixmap(140, 140)
            pixmap.fill(Qt.transparent)
            
            from PyQt5.QtGui import QPainter
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            # Mostrar en el label
            self.color_preview.setPixmap(pixmap)
            
        except Exception as e:
            print(f"❌ Error renderizando icono ONU: {e}")
            import traceback
            traceback.print_exc()
        
        # Actualizar campo hex si ya existe (puede no existir durante la inicialización)
        if hasattr(self, 'hex_input'):
            self.hex_input.blockSignals(True)
            self.hex_input.setText(self.selected_color.name().upper())
            self.hex_input.blockSignals(False)
    
    def load_device_data(self):
        """Cargar datos del dispositivo en modo edición"""
        if not self.device_data:
            return
        
        self.name_input.setText(self.device_data.get('name', ''))
        
        # Cargar color si existe
        color_hex = self.device_data.get('color', '#ff9800')
        self.selected_color = QColor(color_hex)
        self.update_rgb_sliders()
        self.update_color_preview()
    
    def validate_inputs(self) -> bool:
        """Validar campos del formulario"""
        # Validar nombre
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                tr('custom_device.validation_error'),
                tr('custom_device.name_required')
            )
            self.name_input.setFocus()
            return False
        
        if len(name) < 3:
            QMessageBox.warning(
                self,
                tr('custom_device.validation_error'),
                tr('custom_device.name_too_short')
            )
            self.name_input.setFocus()
            return False
        
        return True
    
    def save_device(self):
        """Guardar dispositivo (crear o actualizar)"""
        # Validar
        if not self.validate_inputs():
            return
        
        # Recopilar datos simplificados
        device_data = {
            'name': self.name_input.text().strip(),
            'color': self.selected_color.name()  # Guardar color en formato #RRGGBB
        }
        
        try:
            if self.is_edit_mode:
                # Actualizar dispositivo existente
                device_id = self.device_data['id']
                saved_device = custom_device_manager.update_custom_onu(device_id, device_data)
            else:
                # Crear nuevo dispositivo
                saved_device = custom_device_manager.save_custom_onu(device_data)
            
            if saved_device:
                # Emitir señal con el dispositivo guardado
                self.device_saved.emit(saved_device)
                
                # Cerrar diálogo
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    tr('custom_device.save_error'),
                    tr('custom_device.save_error_message')
                )
        
        except ValueError as e:
            # Error de validación (nombre duplicado, etc.)
            QMessageBox.warning(
                self,
                tr('custom_device.validation_error'),
                str(e)
            )
            self.name_input.setFocus()
        
        except Exception as e:
            # Error general
            QMessageBox.critical(
                self,
                tr('custom_device.save_error'),
                f"{tr('custom_device.save_error_message')}\n\n{str(e)}"
            )
    
    def set_theme(self, dark_theme):
        """Aplicar tema al diálogo"""
        self.dark_theme = dark_theme
        
        if dark_theme:
            self.setStyleSheet("""
                QDialog {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px;
                    border-radius: 4px;
                }
                QLineEdit:focus {
                    border: 2px solid #4a90e2;
                }
                QPushButton {
                    background-color: #4a90e2;
                    color: #ffffff;
                    border: none;
                    padding: 8px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a9ff2;
                }
                QPushButton:pressed {
                    background-color: #3a80d2;
                }
                QSlider::groove:horizontal {
                    background: #3c3c3c;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #4a90e2;
                    width: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QSlider::handle:horizontal:hover {
                    background: #5a9ff2;
                }
            """)
            # Separadores oscuros sutiles
            self.separator.setStyleSheet("background-color: #444444; border: none;")
            self.separator2.setStyleSheet("background-color: #444444; border: none;")
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #ffffff;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                    background: transparent;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    padding: 6px;
                    border-radius: 4px;
                }
                QLineEdit:focus {
                    border: 2px solid #4a90e2;
                }
                QPushButton {
                    background-color: #4a90e2;
                    color: #ffffff;
                    border: none;
                    padding: 8px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a9ff2;
                }
                QPushButton:pressed {
                    background-color: #3a80d2;
                }
                QSlider::groove:horizontal {
                    background: #e0e0e0;
                    height: 8px;
                    border-radius: 4px;
                }
                QSlider::handle:horizontal {
                    background: #4a90e2;
                    width: 16px;
                    margin: -4px 0;
                    border-radius: 8px;
                }
                QSlider::handle:horizontal:hover {
                    background: #5a9ff2;
                }
            """)
            # Separadores claros sutiles
            self.separator.setStyleSheet("background-color: #e0e0e0; border: none;")
            self.separator2.setStyleSheet("background-color: #e0e0e0; border: none;")
