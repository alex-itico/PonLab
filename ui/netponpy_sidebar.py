"""
NetPONPy Sidebar
Panel lateral derecho específico para NetPONPy
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from utils.constants import DEFAULT_SIDEBAR_WIDTH
from .integrated_pon_test_panel import IntegratedPONTestPanel


class NetPONPySidebar(QWidget):
    """Panel lateral derecho para NetPONPy"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_theme = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz del sidebar derecho"""
        # Configurar widget principal más compacto - solo controles
        self.setMinimumWidth(280)  # Más compacto solo para controles
        self.setMaximumWidth(350)  # Máximo reducido sin panel de resultados
        # Permitir que se expanda horizontalmente cuando hay espacio
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Título del panel más compacto
        title_label = QLabel("Simulación")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                padding: 4px;
                background-color: #e3f2fd;
                border-radius: 4px;
                color: #1976d2;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Área de scroll para el contenido
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(QFrame.NoFrame)
        
        # Widget contenedor con políticas responsive
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(2, 2, 2, 2)
        content_layout.setSpacing(4)
        
        # Panel de NetPONPy integrado con gráficos automáticos
        self.netponpy_panel = IntegratedPONTestPanel()
        self.netponpy_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.netponpy_panel)
        
        # Ajustar ancho después de añadir el panel
        QTimer.singleShot(100, self.adjust_width_for_content)  # Pequeño delay para que se renderice
        
        # Agregar stretch al final
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Información adicional más compacta
        info_label = QLabel("Simulación avanzada")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(7)
        info_label.setFont(info_font)
        info_label.setStyleSheet("color: #666; padding: 2px;")
        main_layout.addWidget(info_label)
        
    def set_theme(self, dark_theme):
        """Actualizar tema del sidebar"""
        self.dark_theme = dark_theme
        
        if dark_theme:
            self.setStyleSheet("""
                NetPONPySidebar {
                    background-color: #2c2c2c;
                    border-left: 2px solid #555555;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
                QScrollArea {
                    background-color: #2c2c2c;
                    border: none;
                }
                QScrollBar:vertical {
                    background-color: #3c3c3c;
                    width: 12px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical {
                    background-color: #606060;
                    min-height: 20px;
                    border-radius: 6px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #707070;
                }
            """)
        else:
            self.setStyleSheet("""
                NetPONPySidebar {
                    background-color: #f8f9fa;
                    border-left: 2px solid #d0d0d0;
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
                QScrollBar::handle:vertical:hover {
                    background-color: #a0a0a0;
                }
            """)
    
    def set_canvas_reference(self, canvas):
        """Establecer referencia al canvas para el panel NetPONPy"""
        if hasattr(self, 'netponpy_panel') and self.netponpy_panel:
            self.netponpy_panel.set_canvas_reference(canvas)
            # Actualizar información de topología inicial
            self.netponpy_panel.update_topology_info()
    
    def adjust_width_for_content(self):
        """Ajustar ancho del sidebar según su contenido"""
        try:
            # Calcular ancho necesario basado en el contenido del panel
            if hasattr(self, 'netponpy_panel') and self.netponpy_panel:
                # Obtener hint de tamaño del panel interno
                hint = self.netponpy_panel.sizeHint()
                optimal_width = min(max(hint.width() + 20, 280), 350)  # Entre 280-350px
                
                # Actualizar ancho mínimo si es necesario
                if optimal_width > self.minimumWidth():
                    self.setMinimumWidth(optimal_width)
                    print(f"Ancho del sidebar ajustado a: {optimal_width}px")
                
        except Exception as e:
            print(f"Warning ajustando ancho del sidebar: {e}")
    
    def cleanup(self):
        """Limpiar recursos del sidebar"""
        if hasattr(self, 'netponpy_panel') and self.netponpy_panel:
            self.netponpy_panel.cleanup()
        print("NetPONPy sidebar limpiado")