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
        self.canvas_reference = None  # Referencia al canvas para obtener topología
        self.log_panel_reference = None  # Referencia al panel de log externo
        
        # Variables para detectar cambios y evitar reinicializaciones innecesarias
        self.last_onu_count = 0
        self.last_algorithm = "FCFS"
        self.orchestrator_initialized = False
        
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
        title = QLabel("NetPONPy")
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
        
        # Monitor de estado (sin log, ya que se muestra abajo del canvas)
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
        
        # Información de topología (solo lectura)
        topology_layout = QHBoxLayout()
        topology_label = QLabel("🔗 ONUs en topología:")
        topology_label.setMinimumWidth(50)
        topology_label.setToolTip("Número de ONUs detectadas automáticamente en el canvas")
        topology_layout.addWidget(topology_label)
        
        self.onus_spinbox = QSpinBox()
        self.onus_spinbox.setRange(0, 32)
        self.onus_spinbox.setValue(0)
        self.onus_spinbox.setMaximumWidth(60)
        self.onus_spinbox.setEnabled(False)  # Solo lectura, se actualiza del canvas
        self.onus_spinbox.setStyleSheet("background-color: #f0f0f0; color: #666;")
        topology_layout.addWidget(self.onus_spinbox)
        topology_layout.addStretch()
        layout.addLayout(topology_layout)
        
        # Algoritmo DBA en layout vertical para mejor legibilidad
        alg_label = QLabel("Algoritmo DBA:")
        layout.addWidget(alg_label)
        
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(self.adapter.get_available_algorithms())
        self.algorithm_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.algorithm_combo.currentTextChanged.connect(self.on_algorithm_changed)
        layout.addWidget(self.algorithm_combo)
        
        parent_layout.addWidget(group)
        
    def setup_control_section(self, parent_layout):
        """Configurar sección de control"""
        group = QGroupBox("Control")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Primera fila de botones
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(2)
        
        self.start_button = QPushButton("▶ Iniciar")
        self.start_button.setToolTip("Iniciar simulación (configura automáticamente desde topología)")
        self.start_button.clicked.connect(self.start_simulation)
        self.start_button.setEnabled(True)  # Habilitado por defecto
        self.start_button.setMaximumWidth(50)
        row1_layout.addWidget(self.start_button)
        
        self.step_button = QPushButton("⏯")
        self.step_button.setToolTip("Ejecutar un paso manual (auto-configura si es necesario)")
        self.step_button.clicked.connect(self.manual_step)
        self.step_button.setEnabled(True)  # Habilitado por defecto
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
        
        # Nota sobre el log
        log_note = QLabel("📋 Los eventos se muestran en el panel inferior")
        log_note.setStyleSheet("font-size: 8px; color: #666; font-style: italic; padding: 4px;")
        log_note.setWordWrap(True)
        layout.addWidget(log_note)
        
        # Mantener log_text como fallback pero oculto
        self.log_text = QTextEdit()
        self.log_text.setVisible(False)  # Oculto, solo para fallback
        
        parent_layout.addWidget(group)
        
    def set_canvas_reference(self, canvas):
        """Establecer referencia al canvas para obtener topología"""
        self.canvas_reference = canvas
    
    def set_log_panel(self, log_panel):
        """Establecer referencia al panel de log externo"""
        self.log_panel_reference = log_panel
        # Configurar callback de logging detallado en el adaptador
        if self.adapter:
            self.adapter.set_log_callback(self.log_detailed)
            print("Callback de logging detallado configurado")
    
    def on_algorithm_changed(self, algorithm_name):
        """Manejar cambio de algoritmo DBA"""
        if algorithm_name != self.last_algorithm:
            self.orchestrator_initialized = False
            self.log(f"🔄 Algoritmo cambiado a {algorithm_name} - se reinicializará en próxima simulación")
        
    def check_netponpy_status(self):
        """Verificar estado de netPONpy"""
        if self.adapter.is_netponpy_available():
            self.status_label.setText("✅ NetPONpy disponible y listo")
            self.status_label.setStyleSheet("background-color: #d4edda; color: #155724; padding: 5px; border-radius: 3px;")
        else:
            self.status_label.setText("❌ NetPONpy no disponible")
            self.status_label.setStyleSheet("background-color: #f8d7da; color: #721c24; padding: 5px; border-radius: 3px;")
    
    def update_topology_info(self):
        """Actualizar información de la topología desde el canvas"""
        if not self.canvas_reference:
            self.onus_spinbox.setValue(0)
            return
            
        device_manager = self.canvas_reference.get_device_manager()
        if not device_manager:
            self.onus_spinbox.setValue(0)
            return
            
        # Obtener dispositivos de la topología
        olts = device_manager.get_devices_by_type("OLT")
        onus = device_manager.get_devices_by_type("ONU")
        
        # Actualizar spinbox con número de ONUs del canvas
        self.onus_spinbox.setValue(len(onus))
        
        # Invalidar inicialización si cambió la cantidad de ONUs
        if len(onus) != self.last_onu_count:
            self.orchestrator_initialized = False
            
    def start_simulation(self):
        """Iniciar simulación con configuración automática"""
        # Configurar automáticamente si es necesario
        if not self._auto_initialize_if_needed():
            return  # Error en inicialización
        
        # Iniciar simulación automática
        if self.adapter.start_simulation():
            self.simulation_running = True
            self.step_count = 0
            self.simulation_timer.start(500)  # 500ms por paso
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.step_button.setEnabled(False)  # Deshabilitar durante simulación automática
            self.update_info()
            self.log("🚀 Simulación automática iniciada")
        else:
            self.log("❌ Error iniciando simulación")
            
    def stop_simulation(self):
        """Detener simulación"""
        self.simulation_running = False
        self.simulation_timer.stop()
        self.start_button.setEnabled(True)  # Permitir reiniciar
        self.stop_button.setEnabled(False)
        self.step_button.setEnabled(False)  # Deshabilitar paso manual
        self.log(f"⏹️ Simulación detenida en paso {self.step_count}")
    
    def reset_orchestrator(self):
        """Resetear orquestador cuando cambia la topología"""
        # Detener simulación si está corriendo
        if self.simulation_running:
            self.stop_simulation()
        
        # Limpiar adaptador
        self.adapter.cleanup()
        
        # Invalidar estado de inicialización
        self.orchestrator_initialized = False
        
        # Resetear UI
        self.start_button.setEnabled(True)  # Siempre habilitado ahora
        self.step_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.step_count = 0
        
        # Actualizar topología 
        self.update_topology_info()
        
        self.log("🔄 Orquestador reseteado por cambio de topología")
        
    def manual_step(self):
        """Ejecutar paso manual con configuración automática si es necesario"""
        # Si no hay orquestador configurado, configurar automáticamente
        if not self.orchestrator_initialized:
            if not self._auto_initialize_if_needed():
                return  # Error en inicialización
        
        # Ejecutar paso de simulación
        self.step_simulation()
        
    def _auto_initialize_if_needed(self):
        """Configurar automáticamente el orquestador si es necesario"""
        # Verificar que netPONpy está disponible
        if not self.adapter.is_netponpy_available():
            self.log("❌ NetPONpy no está disponible")
            return False
        
        # Verificar que tenemos referencia al canvas
        if not self.canvas_reference:
            self.log("❌ Error: No hay referencia al canvas")
            return False
            
        device_manager = self.canvas_reference.get_device_manager()
        if not device_manager:
            self.log("❌ Error: No se pudo obtener device manager")
            return False
        
        # Obtener configuración actual de la topología
        olts = device_manager.get_devices_by_type("OLT")
        onus = device_manager.get_devices_by_type("ONU")
        current_algorithm = self.algorithm_combo.currentText()
        current_onu_count = len(onus)
        
        # Validar topología
        if len(olts) != 1:
            self.log("❌ Error: Se requiere exactamente 1 OLT en la topología")
            return False
        if current_onu_count == 0:
            self.log("❌ Error: Se requiere al menos 1 ONU en la topología")
            return False
        
        # Verificar si necesitamos reinicializar el orquestrador
        needs_reinit = (not self.orchestrator_initialized or 
                       current_onu_count != self.last_onu_count or 
                       current_algorithm != self.last_algorithm)
        
        if needs_reinit:
            self.log(f"🔄 Auto-configurando orquestador: {current_onu_count} ONUs, algoritmo {current_algorithm}")
            
            # Inicializar orquestador desde topología
            success, message = self.adapter.initialize_orchestrator_from_topology(device_manager)
            
            if not success:
                self.log(f"❌ {message}")
                return False
                
            # Configurar algoritmo DBA seleccionado
            if not self.adapter.set_dba_algorithm(current_algorithm):
                self.log("❌ Error configurando algoritmo DBA")
                return False
                
            # Actualizar estado
            self.orchestrator_initialized = True
            self.last_onu_count = current_onu_count
            self.last_algorithm = current_algorithm
            
            # Re-configurar el callback de logging después de inicializar
            if self.adapter and hasattr(self.adapter, 'set_log_callback'):
                self.adapter.set_log_callback(self.log_detailed)
                print("Re-configurando callback después de inicialización")
            
            self.log(f"✅ {message}")
            self.log(f"✅ Algoritmo DBA: {current_algorithm}")
            self.update_info()
        else:
            self.log("🔄 Usando configuración existente")
            
        return True
        
    def step_simulation(self):
        """Ejecutar un paso de simulación"""
        result = self.adapter.step_simulation()
        
        if result:
            self.step_count += 1
            status = result.get('status', 'UNKNOWN')
            done = result.get('done', False)
            
            # Actualizar información
            self.update_info()
            
            # No hacer log básico, ya que el orquestrador hace logging detallado
            # Solo log de eventos importantes
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
        """Agregar mensaje al log (usa panel externo si está disponible)"""
        if self.log_panel_reference:
            # Usar el panel de log externo
            self.log_panel_reference.add_log_entry(message)
        else:
            # Fallback al log local (por compatibilidad)
            self.log_text.append(message)
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
    
    def log_detailed(self, message):
        """Log detallado de eventos de simulación"""
        # Debug: verificar que se está llamando
        print(f"DEBUG: log_detailed called with: {message}")
        
        if self.log_panel_reference:
            # Usar el panel de log externo para eventos detallados
            self.log_panel_reference.add_log_entry(message)
        else:
            # Fallback al log local
            self.log_text.append(message)
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
        
    def cleanup(self):
        """Limpiar recursos"""
        self.stop_simulation()
        self.adapter.cleanup()