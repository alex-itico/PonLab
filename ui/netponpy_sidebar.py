"""
NetPONPy Sidebar
Panel lateral derecho con modo intercambiable: Simulación ↔ Aprendizaje Reforzado
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
                             QFrame, QSizePolicy, QPushButton, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from utils.constants import DEFAULT_SIDEBAR_WIDTH
from .integrated_pon_test_panel import IntegratedPONTestPanel
from .rl_config_panel import RLConfigPanel

# Importar TrainingManager con manejo de errores
try:
    from core.rl_integration.training_manager import TrainingManager
    TRAINING_MANAGER_AVAILABLE = True
except ImportError as e:
    TRAINING_MANAGER_AVAILABLE = False
    print(f"[WARNING] TrainingManager no disponible: {e}")


class NetPONPySidebar(QWidget):
    """Panel lateral derecho intercambiable: Simulación ↔ Aprendizaje Reforzado"""
    
    # Señales
    mode_changed = pyqtSignal(str)  # 'simulation' | 'reinforcement_learning'
    rl_training_started = pyqtSignal(dict)  # Parámetros de entrenamiento RL
    rl_training_paused = pyqtSignal()
    rl_training_stopped = pyqtSignal()
    rl_model_saved = pyqtSignal(str)  # Ruta del modelo guardado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_theme = False
        self.current_mode = 'simulation'  # Modo inicial: simulación
        
        # Training Manager para RL
        self.training_manager = None
        self._initialize_training_manager()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar la interfaz del sidebar derecho"""
        # Configurar widget principal
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)  # Ligeramente más ancho para RL panel
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)
        
        # Header con título y botón toggle
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        
        # Título dinámico del panel
        self.title_label = QLabel("Simulación")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.title_label)
        
        # Botón toggle para cambiar modo
        self.mode_toggle_button = QPushButton("🤖")
        self.mode_toggle_button.setMaximumWidth(40)
        self.mode_toggle_button.setMaximumHeight(30)
        self.mode_toggle_button.setToolTip("Cambiar a Aprendizaje Reforzado")
        self.mode_toggle_button.clicked.connect(self.toggle_mode)
        header_layout.addWidget(self.mode_toggle_button)
        
        main_layout.addLayout(header_layout)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Stack widget para intercambiar entre paneles
        self.panel_stack = QStackedWidget()
        
        # Panel de simulación (actual)
        self.simulation_panel = IntegratedPONTestPanel(training_manager=self.training_manager)
        self.simulation_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Panel de aprendizaje reforzado (nuevo)
        self.rl_panel = RLConfigPanel()
        self.rl_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Conectar panel RL con TrainingManager
        if self.training_manager:
            self.rl_panel.set_training_manager(self.training_manager)
            
        # Conectar señales del panel RL
        self.rl_panel.training_started.connect(self.rl_training_started.emit)
        self.rl_panel.training_paused.connect(self.rl_training_paused.emit)
        self.rl_panel.training_stopped.connect(self.rl_training_stopped.emit)
        self.rl_panel.model_saved.connect(self.rl_model_saved.emit)
        
        # Agregar paneles al stack
        self.panel_stack.addWidget(self.simulation_panel)  # Índice 0
        self.panel_stack.addWidget(self.rl_panel)          # Índice 1
        
        # Mostrar panel de simulación por defecto
        self.panel_stack.setCurrentIndex(0)
        
        main_layout.addWidget(self.panel_stack)
        
        # Información adicional dinámica
        self.info_label = QLabel("Simulación avanzada")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(7)
        self.info_label.setFont(info_font)
        self.info_label.setStyleSheet("color: #666; padding: 2px;")
        main_layout.addWidget(self.info_label)
        
        # Ajustar ancho después de inicializar
        QTimer.singleShot(100, self.adjust_width_for_content)
    
    def _initialize_training_manager(self):
        """Inicializar TrainingManager si está disponible"""
        if TRAINING_MANAGER_AVAILABLE:
            try:
                self.training_manager = TrainingManager(self)
                print("[OK] TrainingManager inicializado exitosamente")
            except Exception as e:
                print(f"[ERROR] Error inicializando TrainingManager: {e}")
                self.training_manager = None
        else:
            print("[WARNING] TrainingManager no disponible - funciones RL limitadas")
    
    def toggle_mode(self):
        """Alternar entre modo simulación y aprendizaje reforzado"""
        if self.current_mode == 'simulation':
            self.switch_to_rl_mode()
        else:
            self.switch_to_simulation_mode()
    
    def switch_to_rl_mode(self):
        """Cambiar a modo Aprendizaje Reforzado"""
        self.current_mode = 'reinforcement_learning'
        
        # Actualizar UI
        self.title_label.setText("Aprendizaje Reforzado")
        self.mode_toggle_button.setText("📊")
        self.mode_toggle_button.setToolTip("Cambiar a Simulación")
        self.info_label.setText("Entrenamiento de agentes inteligentes")
        
        # Cambiar panel activo
        self.panel_stack.setCurrentIndex(1)  # RL panel
        
        # Aplicar estilos del modo RL
        self.update_title_style_for_rl()
        
        # Emitir señal
        self.mode_changed.emit('reinforcement_learning')
        
        print("[OK] Modo cambiado a: Aprendizaje Reforzado")
    
    def switch_to_simulation_mode(self):
        """Cambiar a modo Simulación"""
        self.current_mode = 'simulation'
        
        # Actualizar UI
        self.title_label.setText("Simulación")
        self.mode_toggle_button.setText("🤖")
        self.mode_toggle_button.setToolTip("Cambiar a Aprendizaje Reforzado")
        self.info_label.setText("Simulación avanzada")
        
        # Cambiar panel activo
        self.panel_stack.setCurrentIndex(0)  # Simulation panel
        
        # Aplicar estilos del modo simulación
        self.update_title_style_for_simulation()
        
        # Emitir señal
        self.mode_changed.emit('simulation')
        
        print("[OK] Modo cambiado a: Simulacion")
    
    def update_title_style_for_simulation(self):
        """Actualizar estilo del título para modo simulación"""
        if self.dark_theme:
            self.title_label.setStyleSheet("""
                QLabel {
                    padding: 4px;
                    background-color: #1e3a5f;
                    border-radius: 4px;
                    color: #64b5f6;
                    border: 1px solid #42a5f5;
                }
            """)
        else:
            self.title_label.setStyleSheet("""
                QLabel {
                    padding: 4px;
                    background-color: #e3f2fd;
                    border-radius: 4px;
                    color: #1976d2;
                    border: 1px solid #1976d2;
                }
            """)
    
    def update_title_style_for_rl(self):
        """Actualizar estilo del título para modo RL"""
        if self.dark_theme:
            self.title_label.setStyleSheet("""
                QLabel {
                    padding: 4px;
                    background-color: #2d1b69;
                    border-radius: 4px;
                    color: #ba68c8;
                    border: 1px solid #9c27b0;
                }
            """)
        else:
            self.title_label.setStyleSheet("""
                QLabel {
                    padding: 4px;
                    background-color: #f3e5f5;
                    border-radius: 4px;
                    color: #7b1fa2;
                    border: 1px solid #9c27b0;
                }
            """)
        
    def set_theme(self, dark_theme):
        """Actualizar tema del sidebar"""
        self.dark_theme = dark_theme
        
        # Aplicar tema a ambos paneles
        if hasattr(self, 'simulation_panel') and self.simulation_panel:
            self.simulation_panel.set_theme(dark_theme)
            
        if hasattr(self, 'rl_panel') and self.rl_panel:
            self.rl_panel.set_theme(dark_theme)
        
        # Actualizar estilo del título según el modo actual
        if self.current_mode == 'simulation':
            self.update_title_style_for_simulation()
        else:
            self.update_title_style_for_rl()
        
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
        """Establecer referencia al canvas para ambos paneles"""
        # Panel de simulación
        if hasattr(self, 'simulation_panel') and self.simulation_panel:
            self.simulation_panel.set_canvas_reference(canvas)
            # Actualizar información de topología inicial
            self.simulation_panel.update_topology_info()
        
        # TrainingManager para RL (pasar canvas para análisis de topología)
        if self.training_manager and hasattr(self.training_manager, 'env_bridge'):
            self.training_manager.env_bridge.set_canvas_reference(canvas)
            print("[OK] Canvas conectado con TrainingManager")
    
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
        if hasattr(self, 'simulation_panel') and self.simulation_panel:
            self.simulation_panel.cleanup()
        
        if hasattr(self, 'rl_panel') and self.rl_panel:
            # Detener cualquier entrenamiento en curso
            if self.rl_panel.training_active:
                self.rl_panel.stop_training()
        
        # Limpiar TrainingManager
        if self.training_manager:
            self.training_manager.cleanup()
            self.training_manager = None
        
        print("NetPONPy sidebar limpiado")
    
    # Métodos de conveniencia para acceder a los paneles
    @property
    def netponpy_panel(self):
        """Propiedad de compatibilidad para acceder al panel de simulación"""
        return self.simulation_panel
    
    def get_current_panel(self):
        """Obtener el panel actualmente visible"""
        if self.current_mode == 'simulation':
            return self.simulation_panel
        else:
            return self.rl_panel
    
    def get_rl_training_parameters(self):
        """Obtener parámetros de entrenamiento RL configurados"""
        if hasattr(self, 'rl_panel') and self.rl_panel:
            return self.rl_panel.get_training_parameters()
        return None