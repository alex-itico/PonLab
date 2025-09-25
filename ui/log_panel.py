"""
Log Panel
Panel de log para eventos de simulación ubicado debajo del canvas
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QFrame, QCheckBox, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCharFormat, QColor
import datetime
import re

class LogPanel(QWidget):
    """Panel de log para eventos de simulación"""
    
    # Señales
    cleared = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_theme = False
        self.all_log_entries = []  # Almacenar todos los logs para filtrado
        self.category_filters = {
            'SISTEMA': True,
            'OLT': True, 
            'ONU': True,
            'DBA': True,
            'TRANSMISION': True,
            'THROUGHPUT': True,
            'ERROR': True
        }
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz del panel de log"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(4)
        
        # Header con título y botón de limpiar
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Título
        title_label = QLabel("📋 Log de Eventos de Simulación")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Filtros de categoría - OCULTOS por solicitud del usuario
        # self.setup_category_filters(header_layout)
        
        # Botón limpiar
        self.clear_button = QPushButton("🗑️ Limpiar")
        self.clear_button.setMaximumWidth(80)
        self.clear_button.setToolTip("Limpiar todos los eventos del log")
        self.clear_button.clicked.connect(self.clear_log)
        header_layout.addWidget(self.clear_button)
        
        layout.addLayout(header_layout)
        
        # Área de texto para el log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)  # Altura fija compacta
        self.log_text.setMinimumHeight(80)
        
        # Configurar fuente monospace
        log_font = QFont("Consolas, Courier New, monospace")
        log_font.setPointSize(8)
        self.log_text.setFont(log_font)
        
        layout.addWidget(self.log_text)
        
        # Aplicar estilos iniciales
        self.apply_theme()
    
    def setup_category_filters(self, parent_layout):
        """Configurar filtros por categoría"""
        # Crear scroll area para los filtros
        filter_label = QLabel("Filtros:")
        filter_label.setStyleSheet("font-size: 8px; color: #666;")
        parent_layout.addWidget(filter_label)
        
        self.category_checkboxes = {}
        categories = ['SYS', 'OLT', 'ONU', 'DBA', 'TX']  # Versiones cortas
        category_mapping = {
            'SYS': 'SISTEMA',
            'OLT': 'OLT', 
            'ONU': 'ONU',
            'DBA': 'DBA',
            'TX': 'TRANSMISION'
        }
        
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(2)
        
        for short_cat in categories:
            full_cat = category_mapping[short_cat]
            checkbox = QCheckBox(short_cat)
            checkbox.setChecked(self.category_filters.get(full_cat, True))
            checkbox.setStyleSheet("font-size: 7px; color: #666;")
            checkbox.stateChanged.connect(lambda state, cat=full_cat: self.toggle_category_filter(cat, state == Qt.Checked))
            self.category_checkboxes[full_cat] = checkbox
            filters_layout.addWidget(checkbox)
        
        parent_layout.addLayout(filters_layout)
        
    def toggle_category_filter(self, category, enabled):
        """Alternar filtro de categoría"""
        self.category_filters[category] = enabled
        self.refresh_display()
        
    def apply_theme(self):
        """Aplicar tema al panel"""
        if self.dark_theme:
            self.setStyleSheet("""
                LogPanel {
                    background-color: #2c2c2c;
                    border-top: 2px solid #555555;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #666666;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 8px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #666666;
                    border-radius: 4px;
                    selection-background-color: #404040;
                }
            """)
        else:
            self.setStyleSheet("""
                LogPanel {
                    background-color: #f8f9fa;
                    border-top: 2px solid #d0d0d0;
                }
                QLabel {
                    color: #333333;
                    background: transparent;
                }
                QPushButton {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 8px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
                QPushButton:pressed {
                    background-color: #e0e0e0;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    selection-background-color: #e3f2fd;
                }
            """)
    
    def set_theme(self, dark_theme):
        """Establecer tema del panel"""
        self.dark_theme = dark_theme
        self.apply_theme()
    
    def add_log_entry(self, message):
        """Agregar entrada al log con timestamp y filtrado"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.") + f"{datetime.datetime.now().microsecond//1000:03d}"
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'category': self._extract_category(message)
        }
        
        # Almacenar en lista completa
        self.all_log_entries.append(log_entry)
        
        # Aplicar filtros y mostrar si la categoría está habilitada
        if self.category_filters.get(log_entry['category'], True):
            formatted_message = f"[{timestamp}] {message}"
            
            # Colorear según categoría
            self.log_text.append(self._format_message_with_color(formatted_message, log_entry['category']))
            
            # Auto-scroll al final
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def _extract_category(self, message):
        """Extraer categoría del mensaje"""
        # Buscar patrón [CATEGORIA] al inicio del mensaje
        match = re.match(r'\[([A-Z_]+)\]', message)
        if match:
            return match.group(1)
        return 'SISTEMA'  # Default
    
    def _format_message_with_color(self, message, category):
        """Formatear mensaje con color según categoría"""
        # Por simplicidad, retorno el mensaje tal como está
        # En el futuro se puede agregar HTML formatting
        return message
    
    def refresh_display(self):
        """Refrescar la visualización aplicando filtros"""
        self.log_text.clear()
        
        for entry in self.all_log_entries:
            if self.category_filters.get(entry['category'], True):
                formatted_message = f"[{entry['timestamp']}] {entry['message']}"
                self.log_text.append(formatted_message)
        
        # Auto-scroll al final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Limpiar el log"""
        self.log_text.clear()
        self.all_log_entries.clear()
        self.cleared.emit()
        self.add_log_entry("🧹 Log limpiado")
    
    def get_log_content(self):
        """Obtener contenido completo del log"""
        return self.log_text.toPlainText()
    
    def set_log_content(self, content):
        """Establecer contenido del log"""
        self.log_text.setPlainText(content)