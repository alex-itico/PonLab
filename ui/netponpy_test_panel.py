"""
NetPONPy Test Panel
Panel de prueba básico para verificar la integración con netPONpy
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSpinBox, QTextEdit,
                             QGroupBox, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from core.netponpy_adapter import NetPONPyAdapter

class NetPONPyTestPanel(QWidget):
    """Panel de prueba para la integración con netPONpy"""
    
    # Señales
    status_updated = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.adapter = NetPONPyAdapter()
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self.step_simulation)
        self.simulation_running = False
        self.step_count = 0
        
        self.setup_ui()
        self.check_netponpy_status()
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Configurar política de tamaño del widget principal
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Título más compacto
        title = QLabel("🔬 NetPONPy")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 2px; color: #2196F3;")
        layout.addWidget(title)
        
        # Estado de netPONpy
        self.setup_status_section(layout)
        
        # Configuración
        self.setup_config_section(layout)
        
        # Control de simulación
        self.setup_control_section(layout)
        
        # Monitor de estado
        self.setup_monitor_section(layout)
        
        # Agregar stretch al final para que el contenido se mantenga arriba
        layout.addStretch()
        
        # Aplicar estilos globales para responsive design
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 4px;
                font-size: 9px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px 0 4px;
            }
            QPushButton {
                padding: 3px 6px;
                font-size: 8px;
                border-radius: 3px;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #e6f3ff;
            }
            QPushButton:disabled {
                color: #999;
                background-color: #f5f5f5;
            }
        """)
        
    def setup_status_section(self, parent_layout):
        """Configurar sección de estado"""
        group = QGroupBox("Estado")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self.status_label = QLabel("Verificando...")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 4px;
                border-radius: 3px;
                font-size: 9px;
            }
        """)
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.status_label)
        
        parent_layout.addWidget(group)
        
    def setup_config_section(self, parent_layout):
        """Configurar sección de configuración"""
        group = QGroupBox("Configuración")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        
        # Número de ONUs en layout horizontal compacto
        onus_layout = QHBoxLayout()
        onus_label = QLabel("ONUs:")
        onus_label.setMinimumWidth(50)
        onus_layout.addWidget(onus_label)
        
        self.onus_spinbox = QSpinBox()
        self.onus_spinbox.setRange(2, 8)
        self.onus_spinbox.setValue(4)
        self.onus_spinbox.setMaximumWidth(60)
        onus_layout.addWidget(self.onus_spinbox)
        onus_layout.addStretch()
        layout.addLayout(onus_layout)
        
        # Algoritmo DBA en layout vertical para mejor legibilidad
        alg_label = QLabel("Algoritmo DBA:")
        layout.addWidget(alg_label)
        
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(self.adapter.get_available_algorithms())
        self.algorithm_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.algorithm_combo)
        
        # Botón inicializar
        self.init_button = QPushButton("🚀 Inicializar")
        self.init_button.clicked.connect(self.initialize_orchestrator)
        self.init_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.init_button)
        
        parent_layout.addWidget(group)
        
    def setup_control_section(self, parent_layout):
        """Configurar sección de control"""
        group = QGroupBox("Control")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Primera fila de botones
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(2)
        
        self.start_button = QPushButton("▶")
        self.start_button.setToolTip("Iniciar simulación automática")
        self.start_button.clicked.connect(self.start_simulation)
        self.start_button.setEnabled(False)
        self.start_button.setMaximumWidth(50)
        row1_layout.addWidget(self.start_button)
        
        self.step_button = QPushButton("⏯")
        self.step_button.setToolTip("Ejecutar un paso manual")
        self.step_button.clicked.connect(self.manual_step)
        self.step_button.setEnabled(False)
        self.step_button.setMaximumWidth(50)
        row1_layout.addWidget(self.step_button)
        
        self.stop_button = QPushButton("⏹")
        self.stop_button.setToolTip("Detener simulación")
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setEnabled(False)
        self.stop_button.setMaximumWidth(50)
        row1_layout.addWidget(self.stop_button)
        
        row1_layout.addStretch()
        layout.addLayout(row1_layout)
        
        parent_layout.addWidget(group)
        
    def setup_monitor_section(self, parent_layout):
        """Configurar sección de monitoreo"""
        group = QGroupBox("Monitor")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Información básica con mejor formato
        self.info_label = QLabel("Estado: No inicializado")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                padding: 4px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: #f9f9f9;
                font-size: 9px;
            }
        """)
        layout.addWidget(self.info_label)
        
        # Log de eventos más compacto
        log_label = QLabel("Log de eventos:")
        log_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(80)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-size: 8px;
                font-family: 'Courier New', monospace;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.log_text)
        
        parent_layout.addWidget(group)
        
    def check_netponpy_status(self):
        """Verificar estado de netPONpy"""
        if self.adapter.is_netponpy_available():
            self.status_label.setText("✅ NetPONpy disponible y listo")
            self.status_label.setStyleSheet("background-color: #d4edda; color: #155724; padding: 5px; border-radius: 3px;")
            self.init_button.setEnabled(True)
        else:
            self.status_label.setText("❌ NetPONpy no disponible")
            self.status_label.setStyleSheet("background-color: #f8d7da; color: #721c24; padding: 5px; border-radius: 3px;")
            self.init_button.setEnabled(False)
            
    def initialize_orchestrator(self):
        """Inicializar el orquestador"""
        num_onus = self.onus_spinbox.value()
        self.log("Inicializando orchestrator...")
        
        if self.adapter.initialize_orchestrator(num_onus):
            # Configurar algoritmo DBA
            algorithm = self.algorithm_combo.currentText()
            if self.adapter.set_dba_algorithm(algorithm):
                self.log(f"✅ Orchestrator inicializado con {num_onus} ONUs")
                self.log(f"✅ Algoritmo DBA: {algorithm}")
                self.start_button.setEnabled(True)
                self.step_button.setEnabled(True)
                self.init_button.setEnabled(False)
                self.update_info()
            else:
                self.log("❌ Error configurando algoritmo DBA")
        else:
            self.log("❌ Error inicializando orchestrator")
            
    def start_simulation(self):
        """Iniciar simulación automática"""
        if self.adapter.start_simulation():
            self.simulation_running = True
            self.step_count = 0
            self.simulation_timer.start(500)  # 500ms por paso
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.step_button.setEnabled(False)
            self.log("🚀 Simulación automática iniciada")
        else:
            self.log("❌ Error iniciando simulación")
            
    def stop_simulation(self):
        """Detener simulación"""
        self.simulation_running = False
        self.simulation_timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.step_button.setEnabled(True)
        self.log(f"⏹️ Simulación detenida en paso {self.step_count}")
        
    def manual_step(self):
        """Ejecutar paso manual"""
        self.step_simulation()
        
    def step_simulation(self):
        """Ejecutar un paso de simulación"""
        result = self.adapter.step_simulation()
        
        if result:
            self.step_count += 1
            status = result.get('status', 'UNKNOWN')
            done = result.get('done', False)
            
            # Actualizar información
            self.update_info()
            
            if self.step_count % 1 == 0:  # Log cada 10 pasos
                self.log(f"Paso {self.step_count}: {status}")
                
            # Si la simulación terminó
            if done and self.simulation_running:
                self.stop_simulation()
                self.log("✅ Simulación completada")
        else:
            self.log("❌ Error en paso de simulación")
            if self.simulation_running:
                self.stop_simulation()
                
    def update_info(self):
        """Actualizar información de estado"""
        state = self.adapter.get_current_state()
        
        sim_time = state.get('sim_time', 0.0)
        algorithm = state.get('algorithm', 'Unknown')
        total_requests = state.get('total_requests', 0)
        
        # Texto más compacto para mejor legibilidad en sidebar estrecho
        info_text = f"Paso: {self.step_count}\nTiempo: {sim_time:.2f}s\nAlg: {algorithm}\nReqs: {total_requests}"
        self.info_label.setText(info_text)
        
    def log(self, message):
        """Agregar mensaje al log"""
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def cleanup(self):
        """Limpiar recursos"""
        self.stop_simulation()
        self.adapter.cleanup()