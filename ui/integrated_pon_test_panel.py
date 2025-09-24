"""
Integrated PON Test Panel
Panel de prueba mejorado que usa el adaptador integrado y muestra gráficos automáticamente
"""

import os

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSpinBox, QTextEdit,
                             QGroupBox, QGridLayout, QSizePolicy, QProgressBar,
                             QCheckBox, QSlider, QSplitter, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from core.pon_adapter import PONAdapter
from .pon_simulation_results_panel import PONResultsPanel
from .auto_graphics_saver import AutoGraphicsSaver
from .graphics_popup_window import GraphicsPopupWindow

# Importar ModelManager con manejo de errores
try:
    from core.rl_integration.model_bridge import ModelManager
    MODEL_BRIDGE_AVAILABLE = True
except ImportError as e:
    MODEL_BRIDGE_AVAILABLE = False
    print(f"[WARNING] Model Bridge no disponible: {e}")


class IntegratedPONTestPanel(QWidget):
    """Panel de prueba mejorado para la integración PON con visualización automática"""
    
    # Señales
    status_updated = pyqtSignal(str)
    simulation_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.adapter = PONAdapter()
        self.simulation_running = False
        self.step_count = 0
        self.canvas_reference = None  # Referencia al canvas para obtener topología
        
        # Panel de resultados integrado
        self.results_panel = None
        
        # Sistema de guardado automático y ventana emergente
        self.graphics_saver = AutoGraphicsSaver()
        self.popup_window = None  # Se crea cuando se necesita
        
        # Variables para detectar cambios
        self.last_onu_count = 0
        self.last_algorithm = "FCFS"
        self.last_scenario = ""
        self.last_duration = 10
        self.orchestrator_initialized = False
        self.auto_initialize = True  # Habilitar inicialización automática
        
        # Gestión de modelos RL
        self.model_manager = None
        self.current_rl_model = None
        self.rl_model_path = None
        self._initialize_model_manager()
        
        self.setup_ui()
        self.check_pon_status()
        
        # Inicializar estado de controles
        self.on_architecture_changed()
        
        # Realizar inicialización automática inicial si todo está listo
        if self.adapter.is_pon_available():
            QTimer.singleShot(1000, self.perform_initial_auto_initialization)
        
        # Agregar timer adicional para actualizar conteo de ONUs periódicamente
        self.onu_update_timer = QTimer()
        self.onu_update_timer.timeout.connect(self.periodic_onu_update)
        self.onu_update_timer.start(5000)  # Cada 5 segundos (reducir frecuencia)
    
    def _initialize_model_manager(self):
        """Inicializar ModelManager si está disponible"""
        if MODEL_BRIDGE_AVAILABLE:
            try:
                self.model_manager = ModelManager(self)
                # Conectar señales
                self.model_manager.model_loaded.connect(self._on_rl_model_loaded)
                self.model_manager.model_error.connect(self._on_rl_model_error)
                print("[OK] ModelManager inicializado")
            except Exception as e:
                print(f"[ERROR] Error inicializando ModelManager: {e}")
                self.model_manager = None
        else:
            print("[WARNING] ModelManager no disponible - modelos RL deshabilitados")
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Configurar política de tamaño del widget principal
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Solo mostrar panel de controles - los resultados se muestran en ventana emergente
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Panel de controles únicamente
        controls_panel = self.create_controls_panel()
        main_layout.addWidget(controls_panel)
        
        # Crear panel de resultados oculto solo para generar gráficos
        self.results_panel = PONResultsPanel()
        self.results_panel.setVisible(False)  # Oculto - solo para procesamiento interno
        
        # Conectar señales
        self.results_panel.results_updated.connect(self.on_results_updated)
        
    def create_controls_panel(self):
        """Crear panel de controles"""
        panel = QWidget()
        # Eliminar restricción de ancho - ahora usa todo el espacio del sidebar
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)  # Reducir espaciado
        layout.setContentsMargins(6, 6, 6, 6)  # Reducir márgenes
        
        # Título
        title = QLabel("Simulador PON Integrado")
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Estado
        self.status_group = QGroupBox("Estado del Sistema")
        status_layout = QVBoxLayout(self.status_group)
        
        self.status_label = QLabel("Verificando...")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(self.status_group)
        
        # Configuración de simulación
        config_group = QGroupBox("Configuración")
        config_layout = QGridLayout(config_group)
        
        # Número de ONUs conectadas (automático desde topología)
        config_layout.addWidget(QLabel("ONUs conectadas:"), 0, 0)
        
        # Layout horizontal para el conteo y botón de actualización
        onu_layout = QHBoxLayout()
        self.onu_count_label = QLabel("0")
        self.onu_count_label.setStyleSheet("font-weight: bold; color: #2563eb; padding: 4px; background-color: #f0f4ff; border-radius: 4px;")
        self.onu_count_label.setToolTip("Número de ONUs conectadas a OLTs detectadas automáticamente")
        onu_layout.addWidget(self.onu_count_label)
        
        onu_widget = QWidget()
        onu_widget.setLayout(onu_layout)
        config_layout.addWidget(onu_widget, 0, 1)
        
        # Algoritmo DBA
        config_layout.addWidget(QLabel("DBA:"), 1, 0)
        self.algorithm_combo = QComboBox()
        if self.adapter.is_pon_available():
            algorithms = self.adapter.get_available_algorithms()
            self.algorithm_combo.addItems(algorithms)
            
            # Agregar opción de agente RL si está disponible
            if MODEL_BRIDGE_AVAILABLE:
                self.algorithm_combo.addItem("RL Agent")
        
        self.algorithm_combo.currentTextChanged.connect(self.on_algorithm_changed)
        config_layout.addWidget(self.algorithm_combo, 1, 1)
        
        # Selector de modelo RL (inicialmente oculto)
        config_layout.addWidget(QLabel("Modelo RL:"), 2, 0)
        rl_layout = QHBoxLayout()
        
        self.rl_model_combo = QComboBox()
        self.rl_model_combo.setVisible(False)
        self.rl_model_combo.currentTextChanged.connect(self.on_rl_model_changed)
        rl_layout.addWidget(self.rl_model_combo)
        
        self.load_model_btn = QPushButton("📁")
        self.load_model_btn.setMaximumWidth(30)
        self.load_model_btn.setVisible(False)
        self.load_model_btn.setToolTip("Cargar modelo desde archivo")
        self.load_model_btn.clicked.connect(self.load_rl_model_from_file)
        rl_layout.addWidget(self.load_model_btn)
        
        rl_widget = QWidget()
        rl_widget.setLayout(rl_layout)
        config_layout.addWidget(rl_widget, 2, 1)
        
        # Actualizar lista de modelos RL
        self._update_rl_models_list()
        
        # Escenario de tráfico
        config_layout.addWidget(QLabel("Escenario:"), 3, 0)
        self.scenario_combo = QComboBox()
        if self.adapter.is_pon_available():
            self.scenario_combo.addItems(self.adapter.get_available_traffic_scenarios())
        self.scenario_combo.currentTextChanged.connect(self.on_scenario_changed)
        config_layout.addWidget(self.scenario_combo, 3, 1)
        
        # Arquitectura de simulación
        config_layout.addWidget(QLabel("Arquitectura:"), 4, 0)
        self.hybrid_checkbox = QCheckBox("Híbrida Event-Driven")
        self.hybrid_checkbox.setChecked(True)  # Por defecto usar híbrida
        self.hybrid_checkbox.setToolTip("Usar arquitectura híbrida con control temporal estricto")
        self.hybrid_checkbox.toggled.connect(self.on_architecture_changed)
        config_layout.addWidget(self.hybrid_checkbox, 4, 1)
        
        # Tiempo de simulación (para arquitectura híbrida)
        config_layout.addWidget(QLabel("Tiempo (s):"), 5, 0)
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 120)
        self.duration_spinbox.setValue(10)
        self.duration_spinbox.setToolTip("Duración en segundos (solo arquitectura híbrida)")
        self.duration_spinbox.valueChanged.connect(self.on_duration_changed)
        config_layout.addWidget(self.duration_spinbox, 5, 1)
        
        # Pasos de simulación (para arquitectura clásica)
        config_layout.addWidget(QLabel("Pasos:"), 6, 0)
        self.steps_spinbox = QSpinBox()
        self.steps_spinbox.setRange(100, 10000)
        self.steps_spinbox.setValue(1000)
        self.steps_spinbox.setSingleStep(100)
        self.steps_spinbox.setToolTip("Número de pasos (solo arquitectura clásica)")
        config_layout.addWidget(self.steps_spinbox, 6, 1)
        
        layout.addWidget(config_group)
        
        # Controles de simulación
        sim_group = QGroupBox("Simulación")
        sim_layout = QVBoxLayout(sim_group)
        
        # Botones principales
        buttons_layout = QGridLayout()
        
        self.init_btn = QPushButton("⚙️ Inicialización Manual")
        self.init_btn.clicked.connect(self.initialize_simulation)
        self.init_btn.setToolTip("Usar solo si la inicialización automática falló")
        self.init_btn.setVisible(False)  # Ocultar por defecto - inicialización es automática
        buttons_layout.addWidget(self.init_btn, 0, 0)
        
        self.start_btn = QPushButton("▶️ Ejecutar")
        self.start_btn.clicked.connect(self.run_full_simulation)
        self.start_btn.setEnabled(False)
        buttons_layout.addWidget(self.start_btn, 0, 1)
        
        sim_layout.addLayout(buttons_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        sim_layout.addWidget(self.progress_bar)
        
        # Opciones adicionales
        options_layout = QVBoxLayout()
        
        self.auto_charts_checkbox = QCheckBox("Mostrar graficos automaticamente")
        self.auto_charts_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_charts_checkbox)
        
        self.auto_save_checkbox = QCheckBox("Guardar graficos automaticamente")
        self.auto_save_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_save_checkbox)
        
        self.popup_window_checkbox = QCheckBox("Mostrar ventana emergente")
        self.popup_window_checkbox.setChecked(True)
        options_layout.addWidget(self.popup_window_checkbox)
        
        self.detailed_log_checkbox = QCheckBox("Logging detallado")
        self.detailed_log_checkbox.setChecked(True)
        self.detailed_log_checkbox.toggled.connect(self.toggle_detailed_logging)
        options_layout.addWidget(self.detailed_log_checkbox)
        
        self.auto_init_checkbox = QCheckBox("Inicialización automática")
        self.auto_init_checkbox.setChecked(True)
        self.auto_init_checkbox.setToolTip("Reinicializar automáticamente cuando cambien los parámetros")
        self.auto_init_checkbox.toggled.connect(self.toggle_auto_initialize)
        options_layout.addWidget(self.auto_init_checkbox)
        
        sim_layout.addLayout(options_layout)
        
        # Panel de información del agente RL (inicialmente oculto)
        self.rl_info_group = QGroupBox("Estado del Agente RL")
        self.rl_info_group.setVisible(False)
        rl_info_layout = QVBoxLayout(self.rl_info_group)
        
        self.rl_model_info_label = QLabel("Modelo: No cargado")
        self.rl_model_info_label.setWordWrap(True)
        rl_info_layout.addWidget(self.rl_model_info_label)
        
        self.rl_decisions_label = QLabel("Decisiones: 0")
        rl_info_layout.addWidget(self.rl_decisions_label)
        
        self.rl_last_action_label = QLabel("Última acción: N/A")
        self.rl_last_action_label.setWordWrap(True)
        rl_info_layout.addWidget(self.rl_last_action_label)
        
        sim_layout.addWidget(self.rl_info_group)
        
        # Información sobre visualización de resultados
        info_label = QLabel("Los resultados se mostraran en una ventana emergente al terminar la simulacion")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 4px;")
        sim_layout.addWidget(info_label)
        
        layout.addWidget(sim_group)
        
        
        layout.addStretch()
        
        return panel
    
    def check_pon_status(self):
        """Verificar estado del sistema PON"""
        if self.adapter.is_pon_available():
            self.status_label.setText("✅ PON Core disponible")
            self.status_label.setStyleSheet("color: green;")
            
            # Configurar callback de logging
            self.adapter.set_log_callback(self.results_panel.add_log_message)
            
        else:
            self.status_label.setText("❌ PON Core no disponible")
            self.status_label.setStyleSheet("color: red;")
            
            # Deshabilitar controles
            for widget in self.findChildren((QPushButton, QComboBox, QSpinBox)):
                widget.setEnabled(False)
    
    def auto_reinitialize(self, change_description="configuración"):
        """Reinicializar automáticamente cuando se detecten cambios"""
        if not self.auto_initialize or not self.adapter.is_pon_available():
            return
            
        self.status_label.setText(f"🔄 Auto-reinicializando por cambio en {change_description}...")
        self.status_label.setStyleSheet("color: blue;")
        
        # Pequeño delay para que el usuario vea el mensaje
        QTimer.singleShot(500, self.initialize_simulation)
    
    def get_onu_count_from_topology(self):
        """Obtener número de ONUs conectadas a OLTs desde la topología del canvas"""
        try:
            if not (self.canvas_reference and hasattr(self.canvas_reference, 'device_manager')):
                print(f"DEBUG Canvas reference: {self.canvas_reference}")
                if self.canvas_reference:
                    print(f"DEBUG Canvas tiene device_manager: {hasattr(self.canvas_reference, 'device_manager')}")
                return 0
            
            # Obtener estadísticas básicas
            device_stats = self.canvas_reference.device_manager.get_device_stats()
            total_devices = device_stats.get('total_devices', 0)
            olt_count = device_stats.get('olt_count', 0)
            total_onus = device_stats.get('onu_count', 0)
            
            # Si no hay conexiones, ninguna ONU está conectada
            if not hasattr(self.canvas_reference, 'connection_manager'):
                print(f"DEBUG Canvas no tiene connection_manager")
                return 0
            
            connection_manager = self.canvas_reference.connection_manager
            
            # Obtener todas las ONUs y OLTs
            all_onus = self.canvas_reference.device_manager.get_devices_by_type("ONU")
            all_olts = self.canvas_reference.device_manager.get_devices_by_type("OLT")
            
            print(f"DEBUG Dispositivos encontrados: {len(all_olts)} OLTs, {len(all_onus)} ONUs totales")
            
            # Contar ONUs conectadas a cualquier OLT
            connected_onus = 0
            connected_onu_names = []
            
            for onu in all_onus:
                # Verificar si esta ONU está conectada a alguna OLT
                is_connected = False
                for olt in all_olts:
                    connection = connection_manager.get_connection_between(onu, olt)
                    if connection:
                        is_connected = True
                        connected_onu_names.append(f"{onu.name}↔{olt.name}")
                        break
                
                if is_connected:
                    connected_onus += 1
            
            print(f"DEBUG Estadísticas: Total={total_devices}, OLTs={olt_count}, ONUs totales={total_onus}, ONUs conectadas={connected_onus}")
            if connected_onu_names:
                print(f"DEBUG ONUs conectadas: {connected_onu_names}")
            
            return connected_onus
            
        except Exception as e:
            print(f"ERROR obteniendo conteo de ONUs conectadas: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def update_onu_count_display(self):
        """Actualizar la visualización del conteo de ONUs"""
        try:
            print("DEBUG Iniciando update_onu_count_display()")
            current_onus = self.get_onu_count_from_topology()
            print(f"DEBUG Conteo obtenido: {current_onus}")
            
            # Actualizar el texto del label
            self.onu_count_label.setText(str(current_onus))
            print(f"DEBUG Label actualizado a: {self.onu_count_label.text()}")
            
            # Cambiar estilo según el número detectado
            if current_onus == 0:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #dc2626; padding: 4px; background-color: #fef2f2; border-radius: 4px;")
                self.onu_count_label.setToolTip("No se detectaron ONUs conectadas a OLTs")
                print("DEBUG Estilo aplicado: ROJO (0 ONUs conectadas)")
            elif current_onus < 2:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #f59e0b; padding: 4px; background-color: #fffbeb; border-radius: 4px;")
                self.onu_count_label.setToolTip("Se requieren al menos 2 ONUs conectadas para simulación")
                print("DEBUG Estilo aplicado: AMARILLO (< 2 ONUs conectadas)")
            else:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #059669; padding: 4px; background-color: #ecfdf5; border-radius: 4px;")
                self.onu_count_label.setToolTip(f"{current_onus} ONUs conectadas - listo para simular")
                print("DEBUG Estilo aplicado: VERDE (≥ 2 ONUs conectadas)")
            
            # Detectar cambios y reinicializar si es necesario
            if self.orchestrator_initialized and current_onus != self.last_onu_count:
                print(f"DEBUG Reinicializando: {self.last_onu_count} -> {current_onus}")
                self.auto_reinitialize(f"número de ONUs (detectadas: {current_onus})")
            elif not self.orchestrator_initialized and current_onus >= 2:
                print("DEBUG Orquestador no inicializado pero hay ONUs suficientes - intentando inicializar")
                # Intentar inicializar automáticamente si hay ONUs suficientes
                if self.auto_initialize:
                    QTimer.singleShot(500, self.initialize_simulation)
            
            self.last_onu_count = current_onus
            print(f"DEBUG Proceso completado. last_onu_count = {self.last_onu_count}")
            return current_onus
            
        except Exception as e:
            print(f"ERROR actualizando display de ONUs: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def on_algorithm_changed(self):
        """Manejar cambio de algoritmo DBA"""
        algorithm = self.algorithm_combo.currentText()
        
        # Mostrar/ocultar controles de modelo RL
        is_rl_algorithm = (algorithm == "RL Agent")
        self.rl_model_combo.setVisible(is_rl_algorithm)
        self.load_model_btn.setVisible(is_rl_algorithm)
        self.rl_info_group.setVisible(is_rl_algorithm)
        
        if self.orchestrator_initialized and algorithm != self.last_algorithm:
            self.auto_reinitialize(f"algoritmo DBA ({algorithm})")
        self.last_algorithm = algorithm
    
    def on_scenario_changed(self):
        """Manejar cambio de escenario de tráfico"""
        scenario = self.scenario_combo.currentText()
        if self.orchestrator_initialized and scenario != self.last_scenario:
            self.auto_reinitialize(f"escenario de tráfico ({scenario})")
        self.last_scenario = scenario
    
    def on_duration_changed(self):
        """Manejar cambio de duración de simulación"""
        duration = self.duration_spinbox.value()
        if self.orchestrator_initialized and duration != self.last_duration:
            self.auto_reinitialize(f"tiempo de simulación ({duration}s)")
        self.last_duration = duration
    
    def _update_rl_models_list(self):
        """Actualizar lista de modelos RL disponibles"""
        if not self.model_manager:
            return
        
        self.rl_model_combo.clear()
        available_models = self.model_manager.get_available_models()
        
        if available_models:
            self.rl_model_combo.addItem("Seleccionar modelo...")
            self.rl_model_combo.addItems(available_models)
        else:
            self.rl_model_combo.addItem("No hay modelos disponibles")
    
    def on_rl_model_changed(self):
        """Manejar cambio de modelo RL seleccionado"""
        model_name = self.rl_model_combo.currentText()
        
        if not model_name or model_name in ["Seleccionar modelo...", "No hay modelos disponibles"]:
            self.current_rl_model = None
            return
        
        # Obtener parámetros del entorno
        env_params = {
            'num_onus': self.get_onu_count_from_topology(),
            'traffic_scenario': self.scenario_combo.currentText()
        }
        
        # Cargar modelo
        if self.model_manager:
            self.current_rl_model = self.model_manager.load_model(model_name, env_params)
            
            if self.current_rl_model:
                self.results_panel.add_log_message(f"[RL] Modelo cargado: {model_name}")
                self._update_rl_info_display()
                
                # Reinicializar si es necesario
                if self.orchestrator_initialized:
                    self.auto_reinitialize(f"modelo RL ({model_name})")
            else:
                self.results_panel.add_log_message(f"[ERROR] Error cargando modelo RL: {model_name}")
    
    def load_rl_model_from_file(self):
        """Cargar modelo RL desde archivo"""
        if not self.model_manager:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar modelo RL",
            "",
            "Modelos RL (*.zip);;Todos los archivos (*)"
        )
        
        if file_path:
            try:
                # Copiar archivo a directorio de modelos si no está ahí
                model_name = os.path.basename(file_path)
                target_path = os.path.join(self.model_manager.models_directory, model_name)
                
                # Crear directorio si no existe
                os.makedirs(self.model_manager.models_directory, exist_ok=True)
                
                # Copiar archivo si no existe en el directorio de modelos
                if not os.path.exists(target_path):
                    import shutil
                    shutil.copy2(file_path, target_path)
                    print(f"[OK] Modelo copiado a: {target_path}")
                
                # Actualizar lista y seleccionar el modelo
                self._update_rl_models_list()
                
                # Seleccionar el modelo cargado
                index = self.rl_model_combo.findText(model_name)
                if index >= 0:
                    self.rl_model_combo.setCurrentIndex(index)
                
                self.results_panel.add_log_message(f"[RL] Modelo cargado desde archivo: {file_path}")
                
            except Exception as e:
                error_msg = f"Error cargando modelo desde archivo: {str(e)}"
                print(f"[ERROR] {error_msg}")
                self.results_panel.add_log_message(f"[ERROR] {error_msg}")
    
    def _on_rl_model_loaded(self, model_path):
        """Callback cuando se carga un modelo RL"""
        self.rl_model_path = model_path
        print(f"[OK] Modelo RL cargado: {model_path}")
    
    def _on_rl_model_error(self, error_msg):
        """Callback cuando hay error cargando modelo RL"""
        print(f"[ERROR] Error modelo RL: {error_msg}")
        if hasattr(self, 'results_panel'):
            self.results_panel.add_log_message(f"[ERROR] RL: {error_msg}")
    
    def _update_rl_info_display(self):
        """Actualizar visualización de información del agente RL"""
        if self.current_rl_model:
            # Obtener estadísticas del modelo
            stats = self.current_rl_model.get_statistics()
            
            model_name = stats.get('name', 'Desconocido')
            decisions_made = stats.get('decisions_made', 0)
            model_loaded = stats.get('model_loaded', False)
            
            self.rl_model_info_label.setText(f"Modelo: {model_name}")
            self.rl_decisions_label.setText(f"Decisiones: {decisions_made}")
            
            if model_loaded:
                self.rl_model_info_label.setStyleSheet("color: green;")
            else:
                self.rl_model_info_label.setStyleSheet("color: red;")
                
            self.rl_last_action_label.setText("Última acción: Esperando simulación...")
        else:
            self.rl_model_info_label.setText("Modelo: No cargado")
            self.rl_model_info_label.setStyleSheet("color: #666;")
            self.rl_decisions_label.setText("Decisiones: 0")
            self.rl_last_action_label.setText("Última acción: N/A")
    
    def _update_rl_stats_during_simulation(self):
        """Actualizar estadísticas del agente RL durante la simulación"""
        if self.current_rl_model and self.algorithm_combo.currentText() == "RL Agent":
            try:
                stats = self.current_rl_model.get_statistics()
                decisions_made = stats.get('decisions_made', 0)
                self.rl_decisions_label.setText(f"Decisiones: {decisions_made}")
            except Exception as e:
                print(f"Error actualizando estadísticas RL: {e}")
    
    def on_architecture_changed(self):
        """Manejar cambio de arquitectura"""
        use_hybrid = self.hybrid_checkbox.isChecked()
        self.adapter.set_use_hybrid_architecture(use_hybrid)
        
        # Actualizar visibilidad de controles
        self.duration_spinbox.setEnabled(use_hybrid)
        self.steps_spinbox.setEnabled(not use_hybrid)
        
        arch_name = "híbrida event-driven" if use_hybrid else "clásica timesteps"
        
        # Si está inicializado, reinicializar automáticamente
        if self.orchestrator_initialized:
            self.auto_reinitialize(f"arquitectura ({arch_name})")
        
        self.results_panel.add_log_message(f"Arquitectura cambiada a: {arch_name}")
    
    def toggle_detailed_logging(self, enabled):
        """Activar/desactivar logging detallado"""
        self.adapter.set_detailed_logging(enabled)
    
    def toggle_auto_initialize(self, enabled):
        """Activar/desactivar inicialización automática"""
        self.auto_initialize = enabled
        
        # Mostrar/ocultar botón de inicialización manual según el estado
        self.init_btn.setVisible(not enabled)
        
        if enabled:
            self.results_panel.add_log_message("✅ Inicialización automática habilitada")
        else:
            self.results_panel.add_log_message("⚠️ Inicialización automática deshabilitada - usar botón manual")
            self.init_btn.setVisible(True)
    
    def perform_initial_auto_initialization(self):
        """Realizar inicialización automática inicial al cargar el panel"""
        if self.auto_initialize and not self.orchestrator_initialized:
            # Actualizar conteo de ONUs antes de inicializar
            self.update_onu_count_display()
            
            # Solo inicializar si hay ONUs suficientes
            onu_count = self.get_onu_count_from_topology()
            if onu_count >= 2:
                self.status_label.setText("🚀 Inicialización automática inicial...")
                self.status_label.setStyleSheet("color: blue;")
                self.results_panel.add_log_message(f"🎯 Iniciando configuración automática inicial con {onu_count} ONUs conectadas...")
                QTimer.singleShot(500, self.initialize_simulation)
            else:
                self.status_label.setText("⏳ Esperando topología válida...")
                self.status_label.setStyleSheet("color: orange;")
                self.results_panel.add_log_message(f"⏳ Esperando al menos 2 ONUs conectadas a OLTs (actual: {onu_count})")
    
    def initialize_simulation(self):
        """Inicializar simulación"""
        print("DEBUG initialize_simulation() iniciada")
        
        if not self.adapter.is_pon_available():
            print("DEBUG Adapter no disponible")
            return
        
        # Obtener configuración automática
        num_onus = self.get_onu_count_from_topology()
        scenario = self.scenario_combo.currentText()
        algorithm = self.algorithm_combo.currentText()
        use_hybrid = self.hybrid_checkbox.isChecked()
        
        print(f"DEBUG Configuración: ONUs={num_onus}, Escenario={scenario}, Algoritmo={algorithm}, Híbrido={use_hybrid}")
        
        # Validar que hay ONUs conectadas suficientes
        if num_onus < 2:
            print(f"DEBUG ONUs conectadas insuficientes: {num_onus} < 2")
            self.status_label.setText("❌ Se requieren al menos 2 ONUs conectadas a OLTs")
            self.status_label.setStyleSheet("color: red;")
            self.results_panel.add_log_message(f"⚠️ Topología insuficiente: {num_onus} ONUs conectadas (se requieren mínimo 2)")
            return
        
        if use_hybrid:
            self.results_panel.add_log_message("🚀 Inicializando simulación híbrida...")
            success, message = self.adapter.initialize_hybrid_simulator(
                num_onus=num_onus,
                traffic_scenario=scenario,
                channel_capacity_mbps=1024.0
            )
        else:
            self.results_panel.add_log_message("🚀 Inicializando simulación clásica...")
            
            # Usar topología del canvas si está disponible
            if self.canvas_reference:
                success, message = self.adapter.initialize_orchestrator_from_topology(
                    self.canvas_reference.device_manager
                )
            else:
                success = self.adapter.initialize_orchestrator(num_onus)
                message = f"Orquestador inicializado con {num_onus} ONUs"
        
        if success:
            self.orchestrator_initialized = True
            self.last_onu_count = num_onus
            self.last_algorithm = algorithm
            
            # Configurar bridge RL si se seleccionó agente RL
            if algorithm == "RL Agent" and self.current_rl_model:
                self.adapter.set_rl_model_bridge(self.current_rl_model)
                self.results_panel.add_log_message(f"[RL] Bridge configurado: {self.current_rl_model.get_name()}")
            elif algorithm != "RL Agent":
                # Limpiar bridge RL si se cambió a otro algoritmo
                self.adapter.set_rl_model_bridge(None)
            
            # Configurar algoritmo
            if use_hybrid:
                success_alg, msg_alg = self.adapter.set_hybrid_dba_algorithm(algorithm)
                if not success_alg:
                    self.results_panel.add_log_message(f"Warning: {msg_alg}")
            else:
                success_alg, msg_alg = self.adapter.set_dba_algorithm(algorithm)
                if not success_alg:
                    self.results_panel.add_log_message(f"Warning: {msg_alg}")
            
            arch_type = "híbrida" if use_hybrid else "clásica"
            self.status_label.setText(f"✅ Simulación {arch_type} inicializada")
            self.status_label.setStyleSheet("color: green;")
            
            self.start_btn.setEnabled(True)
            
            self.results_panel.add_log_message(f"✅ {message}")
            
        else:
            self.status_label.setText(f"❌ Error: {message if 'message' in locals() else 'Error desconocido'}")
            self.status_label.setStyleSheet("color: red;")
    
    def run_full_simulation(self):
        """Ejecutar simulación completa"""
        if not self.orchestrator_initialized:
            return
        
        use_hybrid = self.hybrid_checkbox.isChecked()
        
        # Deshabilitar botones durante simulación
        self.start_btn.setEnabled(False)
        
        if use_hybrid:
            # Simulación híbrida por tiempo
            duration = self.duration_spinbox.value()
            
            # Configurar barra de progreso (estimación)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            
            self.results_panel.add_log_message(f"🏃 Ejecutando simulación híbrida: {duration}s...")
            
            # Callback para simulación híbrida
            def hybrid_callback(event_type, data):
                if event_type == "update":
                    # Actualizar progreso basado en tiempo simulado
                    sim_time = data.get('sim_time', 0)
                    progress = min(int((sim_time / duration) * 100), 100)
                    self.progress_bar.setValue(progress)
                    
                    # Log eventos importantes
                    if data.get('event_type') == 'polling_cycle':
                        cycle_num = data.get('data', {}).get('cycle_number', 0)
                        if cycle_num % 100 == 0:  # Log cada 100 ciclos
                            self.results_panel.add_log_message(f"Ciclo DBA: {cycle_num}")
                    
                elif event_type == "end":
                    self.progress_bar.setValue(100)
                    self.results_panel.add_log_message("✅ Simulación híbrida completada")
                    self.process_hybrid_results(data)
                    self.on_simulation_finished()
            
            # Ejecutar simulación híbrida
            success, result = self.adapter.run_hybrid_simulation(
                duration_seconds=duration, 
                callback=hybrid_callback
            )
            
            if not success:
                self.results_panel.add_log_message(f"❌ Error en simulación híbrida: {result}")
                self.on_simulation_finished()
        else:
            # Simulación clásica por pasos
            steps = self.steps_spinbox.value()
            
            # Mostrar barra de progreso
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, steps)
            self.progress_bar.setValue(0)
            
            self.results_panel.add_log_message(f"🏃 Ejecutando simulación clásica: {steps} pasos...")
            
            # Callback para monitoreo de progreso
            def simulation_callback(event_type, data):
                if event_type == "init":
                    self.results_panel.add_log_message("Simulacion NetSim iniciada")
                    
                elif event_type == "update":
                    current_step = data.get('steps', 0)
                    if current_step % 100 == 0:  # Actualizar cada 100 pasos
                        self.progress_bar.setValue(current_step)
                        
                        # Actualizar métricas en tiempo real
                        self.update_realtime_metrics(data)
                        
                elif event_type == "end":
                    self.progress_bar.setValue(steps)
                    self.results_panel.add_log_message("✅ Simulación clásica completada")
                    self.on_simulation_finished()
            
            # Ejecutar simulación clásica
            success = self.adapter.run_netsim_simulation(timesteps=steps, callback=simulation_callback)
            
            if not success:
                self.results_panel.add_log_message("❌ Error en simulación clásica")
                self.on_simulation_finished()
    
    def process_hybrid_results(self, results):
        """Procesar resultados de simulación híbrida"""
        try:
            # Convertir formato de resultados híbridos al formato esperado por el panel de resultados
            if results and isinstance(results, dict):
                # El simulador híbrido devuelve resultados completos
                self.results_panel.update_simulation_results(results)
                self.results_panel.add_log_message("📊 Resultados procesados y gráficos generados")
                
                # Mostrar ventana emergente si está habilitada
                if hasattr(self, 'show_popup_checkbox') and self.show_popup_checkbox.isChecked():
                    self.show_graphics_popup()
            else:
                self.results_panel.add_log_message("⚠️ No se recibieron resultados válidos")
                
        except Exception as e:
            self.results_panel.add_log_message(f"❌ Error procesando resultados híbridos: {str(e)}")
    
    
    
    def update_realtime_metrics(self, data):
        """Actualizar métricas en tiempo real"""
        steps = data.get('steps', 0)
        requests = data.get('total_requests_processed', 0)
        delay = data.get('mean_delay', 0)
        throughput = data.get('mean_throughput', 0)
        
        # Actualizar estadísticas del agente RL si está activo
        self._update_rl_stats_during_simulation()
        
        # Real-time metrics display removed
        # self.steps_label.setText(f"Pasos: {steps}")
        # self.requests_label.setText(f"Solicitudes: {requests}")
        # self.delay_label.setText(f"Delay: {delay:.6f}s")
        # self.throughput_label.setText(f"Throughput: {throughput:.2f} MB/s")
    
    def on_simulation_finished(self):
        """Callback cuando termina la simulación"""
        # Rehabilitar botones
        self.start_btn.setEnabled(True)
        
        # Ocultar barra de progreso
        self.progress_bar.setVisible(False)
        
        # Actualizar resultados finales
        self.results_panel.refresh_results()
        
        # Mostrar gráficos automáticamente en panel si está habilitado
        if self.auto_charts_checkbox.isChecked():
            self.results_panel.show_charts_on_simulation_end()
        
        # NUEVO: Guardar gráficos automáticamente y mostrar ventana emergente
        self.handle_automatic_graphics_processing()
        
        # Actualización final de estadísticas RL
        self._update_rl_stats_during_simulation()
        
        # Emitir señal
        self.simulation_finished.emit()
        
        self.results_panel.add_log_message("🎯 Simulación finalizada - Resultados y gráficos procesados")
    
    
    def handle_automatic_graphics_processing(self):
        """Manejar el procesamiento automático de gráficos al finalizar simulación"""
        try:
            # Verificar si alguna opción automática está habilitada
            should_save = self.auto_save_checkbox.isChecked()
            should_popup = self.popup_window_checkbox.isChecked()
            
            if not (should_save or should_popup):
                return  # No hacer nada si no hay opciones habilitadas
            
            # Obtener datos completos de la simulación
            # El adapter ya retorna la estructura correcta con 'simulation_summary'
            simulation_data = self.adapter.get_simulation_summary()
            
            # Agregar datos adicionales
            simulation_data.update({
                'current_state': self.adapter.get_current_state(),
                'orchestrator_stats': self.adapter.get_orchestrator_stats()
            })
            
            # Recopilar información de la sesión
            session_info = {
                'num_onus': self.get_onu_count_from_topology(),
                'algorithm': self.algorithm_combo.currentText(),
                'traffic_scenario': self.scenario_combo.currentText(),
                'steps': self.steps_spinbox.value(),
                'auto_charts': self.auto_charts_checkbox.isChecked(),
                'detailed_logging': self.detailed_log_checkbox.isChecked()
            }
            
            session_directory = ""
            
            # Guardar gráficos automáticamente si está habilitado
            if should_save and hasattr(self.results_panel, 'charts_panel'):
                self.results_panel.add_log_message("Guardando graficos automaticamente...")
                
                session_directory = self.graphics_saver.save_simulation_graphics_and_data(
                    self.results_panel.charts_panel,
                    simulation_data,
                    session_info
                )
                
                if session_directory:
                    self.results_panel.add_log_message(f"✅ Gráficos guardados en: {session_directory}")
                else:
                    self.results_panel.add_log_message("❌ Error guardando gráficos")
            
            # Mostrar ventana emergente si está habilitado
            if should_popup:
                self.show_graphics_popup_window(simulation_data, session_directory, session_info)
            
        except Exception as e:
            self.results_panel.add_log_message(f"❌ Error en procesamiento automático: {e}")
            print(f"❌ Error en handle_automatic_graphics_processing: {e}")
    
    def show_graphics_popup_window(self, 
                                 simulation_data: dict, 
                                 session_directory: str, 
                                 session_info: dict):
        """Mostrar ventana emergente con gráficos"""
        try:
            # Crear ventana emergente si no existe
            if not self.popup_window:
                self.popup_window = GraphicsPopupWindow(parent=self)
                
                # Conectar señales
                self.popup_window.window_closed.connect(self.on_popup_window_closed)
                self.popup_window.graphics_exported.connect(self.on_additional_graphics_exported)
            
            # Mostrar resultados en la ventana emergente
            self.popup_window.show_simulation_results(
                simulation_data, 
                session_directory, 
                session_info
            )
            
            self.results_panel.add_log_message("Ventana emergente de graficos mostrada")
            
        except Exception as e:
            self.results_panel.add_log_message(f"ERROR mostrando ventana emergente: {e}")
            print(f"ERROR en show_graphics_popup_window: {e}")
    
    def on_popup_window_closed(self):
        """Callback cuando se cierra la ventana emergente"""
        self.results_panel.add_log_message("Ventana emergente de graficos cerrada")
    
    def on_additional_graphics_exported(self, directory):
        """Callback cuando se exportan gráficos adicionales"""
        self.results_panel.add_log_message(f"Graficos adicionales exportados a: {directory}")
    
    def on_results_updated(self, results):
        """Callback cuando se actualizan los resultados"""
        # Aquí se pueden agregar acciones adicionales cuando se actualicen los resultados
        pass
    
    def set_canvas_reference(self, canvas):
        """Establecer referencia al canvas"""
        self.canvas_reference = canvas
        print(f"DEBUG Canvas reference establecida: {canvas}")
        
        # Actualizar inmediatamente el conteo de ONUs
        self.update_onu_count_display()
        
        # Conectar señal de cambios de dispositivos si no está conectada
        if canvas and hasattr(canvas, 'device_manager'):
            print("DEBUG Conectando señal devices_changed")
            # Desconectar señal anterior si existe para evitar duplicados
            try:
                canvas.device_manager.devices_changed.disconnect(self.on_devices_changed)
            except:
                pass  # No estaba conectada
            
            # Conectar nueva señal
            canvas.device_manager.devices_changed.connect(self.on_devices_changed)
        
        # También conectar señal de cambios de conexiones
        if canvas and hasattr(canvas, 'connection_manager'):
            print("DEBUG Conectando señal connections_changed")
            # Desconectar señal anterior si existe para evitar duplicados
            try:
                canvas.connection_manager.connections_changed.disconnect(self.on_connections_changed)
            except:
                pass  # No estaba conectada
            
            # Conectar nueva señal
            canvas.connection_manager.connections_changed.connect(self.on_connections_changed)
    
    def on_devices_changed(self):
        """Callback cuando cambian los dispositivos en el canvas"""
        print("DEBUG Dispositivos cambiaron - actualizando conteo de ONUs")
        self.update_onu_count_display()
    
    def on_connections_changed(self):
        """Callback cuando cambian las conexiones en el canvas"""
        print("DEBUG Conexiones cambiaron - actualizando conteo de ONUs conectadas")
        self.update_onu_count_display()
    
    def periodic_onu_update(self):
        """Actualización periódica del conteo de ONUs"""
        if self.canvas_reference:
            current_count = self.get_onu_count_from_topology()
            displayed_count = int(self.onu_count_label.text()) if self.onu_count_label.text().isdigit() else -1
            
            if current_count != displayed_count:
                print(f"DEBUG Actualizando conteo ONUs: {displayed_count} -> {current_count}")
                self.update_onu_count_display()
    
    def force_onu_count_update(self):
        """Forzar actualización del conteo de ONUs"""
        print("DEBUG Actualización manual de ONUs forzada por usuario")
        self.update_onu_count_display()
        
        # Mostrar información de debug al usuario
        if self.canvas_reference:
            all_devices = self.canvas_reference.device_manager.get_all_devices()
            all_onus = self.canvas_reference.device_manager.get_devices_by_type("ONU")
            connected_count = self.get_onu_count_from_topology()
            self.results_panel.add_log_message(f"🔍 Actualización manual: {connected_count} ONUs conectadas de {len(all_onus)} ONUs totales ({len(all_devices)} dispositivos)")
        else:
            self.results_panel.add_log_message("⚠️ No hay referencia al canvas para contar dispositivos")
    
    def update_topology_info(self):
        """Actualizar información de topología desde el canvas"""
        try:
            if self.canvas_reference:
                # Actualizar conteo de ONUs desde la topología
                self.update_onu_count_display()
                print("INFO Topologia actualizada desde canvas")
            else:
                print("WARNING Canvas reference no disponible para actualizar topologia")
        except Exception as e:
            print(f"ERROR actualizando topologia: {e}")
    
    def set_log_panel(self, log_panel):
        """Establecer referencia al panel de log externo"""
        self.log_panel_reference = log_panel
        print("INFO Log panel conectado al panel PON integrado")
    
    def reset_orchestrator(self):
        """Resetear el orquestador PON cuando cambia la topología"""
        try:
            if hasattr(self, 'adapter') and self.adapter:
                # Reset adapter internal state
                self.adapter.orchestrator = None
                self.adapter.netsim = None
                
                # Actualizar conteo de ONUs inmediatamente
                self.update_onu_count_display()
                
                # Si estaba inicializado, reinicializar automáticamente por cambio de topología
                if self.orchestrator_initialized:
                    self.auto_reinitialize("topología")
                
                print("INFO Orquestador PON reseteado por cambio de topologia")
            else:
                print("WARNING No hay adapter para resetear orquestador")
        except Exception as e:
            print(f"ERROR reseteando orquestador: {e}")
    
    def cleanup(self):
        """Limpiar recursos del panel"""
        try:
            # Parar timer de actualización de ONUs
            if hasattr(self, 'onu_update_timer') and self.onu_update_timer:
                self.onu_update_timer.stop()
                self.onu_update_timer = None
            
            if hasattr(self, 'adapter') and self.adapter:
                # Limpiar adapter si es necesario
                pass
            
            if hasattr(self, 'popup_window') and self.popup_window:
                self.popup_window.close()
                self.popup_window = None
            
            # Limpiar model manager
            if hasattr(self, 'model_manager') and self.model_manager:
                self.model_manager.cleanup()
                self.model_manager = None
            
            print("Panel PON integrado limpiado")
            
        except Exception as e:
            print(f"ERROR limpiando panel PON: {e}")
    
    def set_theme(self, dark_theme):
        """Aplicar tema al panel integrado PON"""
        # Aplicar tema al panel de resultados
        if hasattr(self, 'results_panel') and self.results_panel:
            self.results_panel.set_theme(dark_theme)
            
        # Aplicar tema a la ventana emergente si existe
        if hasattr(self, 'popup_window') and self.popup_window:
            self.popup_window.set_theme(dark_theme)
            
        # El estilo QSS se aplicará automáticamente desde la ventana principal