"""
Integrated PON Test Panel
Panel de prueba mejorado que usa el adaptador integrado y muestra gráficos automáticamente
"""

print("[VERSIÓN] Cargando integrated_pon_test_panel.py v2.0 - con método _update_rl_models_list stub")

import os

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QSpinBox, QTextEdit,
                             QGroupBox, QGridLayout, QSizePolicy, QProgressBar,
                             QCheckBox, QSlider, QSplitter, QFileDialog, QMessageBox,
                             QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from core import PONAdapter
from .pon_simulation_results_panel import PONResultsPanel
from .auto_graphics_saver import AutoGraphicsSaver
from .graphics_popup_window import GraphicsPopupWindow

# Importar sistema de traducciones
from utils.translation_manager import translation_manager
tr = translation_manager.get_text

# Model Bridge no disponible - eliminado para independencia
MODEL_BRIDGE_AVAILABLE = False


class IntegratedPONTestPanel(QWidget):
    """Panel de prueba mejorado para la integración PON con visualización automática"""
    
    # Señales
    status_updated = pyqtSignal(str)
    simulation_finished = pyqtSignal()
    
    def __init__(self, training_manager=None):
        super().__init__()
        self.adapter = PONAdapter()
        self.training_manager = training_manager  # Referencia al TrainingManager para RL
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
        self.rl_model_loaded = False  # Estado del modelo RL
        
        
        # Control de debug verbose
        self.verbose_debug = False  # Controla mensajes DEBUG repetitivos
        
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
        self.title_label = QLabel(tr("integrated_pon_panel.title"))
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Estado
        self.status_group = QGroupBox(tr("integrated_pon_panel.status_group"))
        status_layout = QVBoxLayout(self.status_group)
        
        self.status_label = QLabel(tr("integrated_pon_panel.status_checking"))
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(self.status_group)
        
        # Configuración de simulación
        self.config_group = QGroupBox(tr("integrated_pon_panel.config_group"))
        config_layout = QGridLayout(self.config_group)
        
        # Número de ONUs conectadas (automático desde topología)
        self.onus_connected_label = QLabel(tr("integrated_pon_panel.onus_connected"))
        config_layout.addWidget(self.onus_connected_label, 0, 0)
        
        # Layout horizontal para el conteo y botón de actualización
        onu_layout = QHBoxLayout()
        self.onu_count_label = QLabel("0")
        self.onu_count_label.setStyleSheet("font-weight: bold; color: #2563eb; padding: 4px; background-color: #f0f4ff; border-radius: 4px;")
        self.onu_count_label.setToolTip(tr("integrated_pon_panel.onus_tooltip"))
        onu_layout.addWidget(self.onu_count_label)
        
        onu_widget = QWidget()
        onu_widget.setLayout(onu_layout)
        config_layout.addWidget(onu_widget, 0, 1)
        
        # Algoritmo DBA
        self.dba_label = QLabel(tr("integrated_pon_panel.dba"))
        config_layout.addWidget(self.dba_label, 1, 0)
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
        self.rl_model_label = QLabel(tr("integrated_pon_panel.rl_model"))
        config_layout.addWidget(self.rl_model_label, 2, 0)
        
        # Layout vertical para organizar mejor los elementos RL
        rl_main_layout = QVBoxLayout()
        
        # Layout vertical para los botones con mejor espaciado
        rl_buttons_layout = QVBoxLayout()
        rl_buttons_layout.setSpacing(8)  # Espacio entre botones
        
        # Smart RL model loading
        self.load_rl_model_btn = QPushButton(tr("integrated_pon_panel.load_rl_model"))
        self.load_rl_model_btn.setToolTip(tr("integrated_pon_panel.load_rl_model_tooltip"))
        self.load_rl_model_btn.setMinimumHeight(30)  # Altura mínima para botones
        self.load_rl_model_btn.clicked.connect(self.load_smart_rl_model)
        rl_buttons_layout.addWidget(self.load_rl_model_btn)

        # Botón para desactivar RL
        self.unload_rl_model_btn = QPushButton(tr("integrated_pon_panel.unload_rl_model"))
        self.unload_rl_model_btn.setToolTip(tr("integrated_pon_panel.unload_rl_model_tooltip"))
        self.unload_rl_model_btn.setMinimumHeight(30)  # Altura mínima
        self.unload_rl_model_btn.clicked.connect(self.unload_rl_model)
        self.unload_rl_model_btn.setVisible(False)  # Inicialmente oculto
        rl_buttons_layout.addWidget(self.unload_rl_model_btn)
        
        
        # Frame para contener los botones con mejor presentación vertical
        rl_buttons_frame = QFrame()
        rl_buttons_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        rl_buttons_frame.setLineWidth(1)
        rl_buttons_frame.setLayout(rl_buttons_layout)
        rl_buttons_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(240, 240, 240, 0.1);
                border: 1px solid #ccc;
                border-radius: 8px;
                margin: 3px;
                padding: 8px;
            }
        """)
        
        # Agregar frame de botones al layout principal
        rl_main_layout.addWidget(rl_buttons_frame)

        # RL model status en una línea separada con margen
        self.rl_status_label = QLabel(tr("integrated_pon_panel.rl_status_no_model"))
        self.rl_status_label.setStyleSheet("color: #666; font-size: 8pt; margin-top: 5px;")
        rl_main_layout.addWidget(self.rl_status_label)

        # LÍNEA 162 MODIFICADA - NO DEBE HABER ERROR AQUÍ
        # Crear widget de RL y agregarlo al layout
        rl_widget = QWidget()
        rl_widget.setLayout(rl_main_layout)
        config_layout.addWidget(rl_widget, 2, 1)

        # RL model list update removed - use internal RL-DBA instead
        
        # Escenario de tráfico
        self.scenario_label = QLabel(tr("integrated_pon_panel.scenario"))
        config_layout.addWidget(self.scenario_label, 3, 0)
        self.scenario_combo = QComboBox()
        if self.adapter.is_pon_available():
            self.scenario_combo.addItems(self.adapter.get_available_traffic_scenarios())
        self.scenario_combo.currentTextChanged.connect(self.on_scenario_changed)
        config_layout.addWidget(self.scenario_combo, 3, 1)
        
        # Arquitectura de simulación (OCULTA - siempre híbrida event-driven)
        self.architecture_label = QLabel(tr("integrated_pon_panel.architecture"))
        self.architecture_label.setVisible(False)  # Ocultar etiqueta
        config_layout.addWidget(self.architecture_label, 4, 0)
        self.hybrid_checkbox = QCheckBox(tr("integrated_pon_panel.hybrid_architecture"))
        self.hybrid_checkbox.setChecked(True)  # Por defecto usar híbrida (siempre activo)
        self.hybrid_checkbox.setVisible(False)  # Ocultar checkbox
        self.hybrid_checkbox.setToolTip(tr("integrated_pon_panel.hybrid_tooltip"))
        self.hybrid_checkbox.toggled.connect(self.on_architecture_changed)
        config_layout.addWidget(self.hybrid_checkbox, 4, 1)
        
        # Tiempo de simulación (para arquitectura híbrida)
        self.time_label = QLabel(tr("integrated_pon_panel.time_seconds"))
        config_layout.addWidget(self.time_label, 5, 0)
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 120)
        self.duration_spinbox.setValue(10)
        self.duration_spinbox.setToolTip(tr("integrated_pon_panel.time_tooltip"))
        self.duration_spinbox.valueChanged.connect(self.on_duration_changed)
        config_layout.addWidget(self.duration_spinbox, 5, 1)
        
        # Pasos de simulación (OCULTOS - no se usan en arquitectura híbrida)
        self.steps_label = QLabel(tr("integrated_pon_panel.steps"))
        self.steps_label.setVisible(False)  # Ocultar etiqueta
        config_layout.addWidget(self.steps_label, 6, 0)
        self.steps_spinbox = QSpinBox()
        self.steps_spinbox.setRange(100, 10000)
        self.steps_spinbox.setValue(1000)
        self.steps_spinbox.setSingleStep(100)
        self.steps_spinbox.setVisible(False)  # Ocultar control
        self.steps_spinbox.setToolTip(tr("integrated_pon_panel.steps_tooltip"))
        config_layout.addWidget(self.steps_spinbox, 6, 1)
        
        layout.addWidget(self.config_group)
        
        # Controles de simulación
        self.sim_group = QGroupBox(tr("integrated_pon_panel.simulation_group"))
        sim_layout = QVBoxLayout(self.sim_group)
        
        # Botones principales
        buttons_layout = QGridLayout()
        
        self.init_btn = QPushButton(tr("integrated_pon_panel.manual_init"))
        self.init_btn.clicked.connect(self.initialize_simulation)
        self.init_btn.setToolTip(tr("integrated_pon_panel.manual_init_tooltip"))
        self.init_btn.setVisible(False)  # Ocultar por defecto - inicialización es automática
        buttons_layout.addWidget(self.init_btn, 0, 0)
        
        self.start_btn = QPushButton(tr("integrated_pon_panel.execute"))
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
        
        self.popup_window_checkbox = QCheckBox(tr("integrated_pon_panel.show_popup"))
        self.popup_window_checkbox.setChecked(True)
        options_layout.addWidget(self.popup_window_checkbox)
        
        self.detailed_log_checkbox = QCheckBox(tr("integrated_pon_panel.detailed_logging"))
        self.detailed_log_checkbox.setChecked(True)
        self.detailed_log_checkbox.toggled.connect(self.toggle_detailed_logging)
        options_layout.addWidget(self.detailed_log_checkbox)
        
        self.auto_init_checkbox = QCheckBox(tr("integrated_pon_panel.auto_init"))
        self.auto_init_checkbox.setChecked(True)
        self.auto_init_checkbox.setToolTip(tr("integrated_pon_panel.auto_init_tooltip"))
        self.auto_init_checkbox.toggled.connect(self.toggle_auto_initialize)
        self.auto_init_checkbox.setVisible(False)  # Invisible pero siempre activo
        options_layout.addWidget(self.auto_init_checkbox)
        
        sim_layout.addLayout(options_layout)
        
        # Panel de información del agente RL (inicialmente oculto)
        self.rl_info_group = QGroupBox(tr("integrated_pon_panel.rl_agent_group"))
        self.rl_info_group.setVisible(False)
        rl_info_layout = QVBoxLayout(self.rl_info_group)
        
        self.rl_model_info_label = QLabel(tr("integrated_pon_panel.rl_model_info"))
        self.rl_model_info_label.setWordWrap(True)
        rl_info_layout.addWidget(self.rl_model_info_label)
        
        self.rl_decisions_label = QLabel(tr("integrated_pon_panel.rl_decisions").format(0))
        rl_info_layout.addWidget(self.rl_decisions_label)
        
        self.rl_last_action_label = QLabel(tr("integrated_pon_panel.rl_last_action"))
        self.rl_last_action_label.setWordWrap(True)
        rl_info_layout.addWidget(self.rl_last_action_label)
        
        sim_layout.addWidget(self.rl_info_group)
        
        # Información sobre visualización de resultados
        self.info_label = QLabel(tr("integrated_pon_panel.results_info"))
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #666; font-style: italic; padding: 4px;")
        sim_layout.addWidget(self.info_label)
        
        layout.addWidget(self.sim_group)
        
        
        layout.addStretch()
        
        return panel
    
    def check_pon_status(self):
        """Verificar estado del sistema PON"""
        if self.adapter.is_pon_available():
            self.status_label.setText(tr("integrated_pon_panel.status_available"))
            self.status_label.setStyleSheet("color: green;")
            
            # Configurar callback de logging
            self.adapter.set_log_callback(self.results_panel.add_log_message)
            
        else:
            self.status_label.setText(tr("integrated_pon_panel.status_unavailable"))
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
                if getattr(self, 'verbose_debug', False):
                    print(f"DEBUG Canvas no tiene connection_manager")
                return 0
            
            connection_manager = self.canvas_reference.connection_manager
            
            # Obtener todas las ONUs y OLTs
            all_onus = self.canvas_reference.device_manager.get_devices_by_type("ONU")
            all_olts = self.canvas_reference.device_manager.get_devices_by_type("OLT")
            
            # Solo mostrar debug si hay cambios significativos en dispositivos
            current_total = len(all_olts) + len(all_onus)
            if not hasattr(self, '_last_device_count') or self._last_device_count != current_total:
                if getattr(self, 'verbose_debug', False):
                    print(f"DEBUG Dispositivos encontrados: {len(all_olts)} OLTs, {len(all_onus)} ONUs totales")
                self._last_device_count = current_total
            
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
            
            # Solo mostrar estadísticas detalladas si hay cambios importantes
            if connected_onus != getattr(self, '_last_connected_count', -1):
                if getattr(self, 'verbose_debug', False):
                    print(f"DEBUG Estadísticas: Total={total_devices}, OLTs={olt_count}, ONUs totales={total_onus}, ONUs conectadas={connected_onus}")
                    if connected_onu_names:
                        print(f"DEBUG ONUs conectadas: {connected_onu_names}")
                self._last_connected_count = connected_onus
            
            return connected_onus
            
        except Exception as e:
            print(f"❌ Error obteniendo conteo de ONUs conectadas: {e}")
            if getattr(self, 'verbose_debug', False):
                import traceback
                traceback.print_exc()
            return 0
    
    def update_onu_count_display(self):
        """Actualizar la visualización del conteo de ONUs"""
        try:
            # Solo debug en modo verbose
            if getattr(self, 'verbose_debug', False):
                print("DEBUG Iniciando update_onu_count_display()")
                
            current_onus = self.get_onu_count_from_topology()
            
            # Solo mostrar debug si cambió el valor
            if not hasattr(self, '_last_debug_count') or self._last_debug_count != current_onus:
                if getattr(self, 'verbose_debug', False):
                    print(f"DEBUG Conteo obtenido: {current_onus}")
                self._last_debug_count = current_onus
            
            # Actualizar el texto del label
            self.onu_count_label.setText(str(current_onus))
            
            # Cambiar estilo según el número detectado (sin debug repetitivo)
            if current_onus == 0:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #dc2626; padding: 4px; background-color: #fef2f2; border-radius: 4px;")
                self.onu_count_label.setToolTip("No se detectaron ONUs conectadas a OLTs")
            elif current_onus < 2:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #f59e0b; padding: 4px; background-color: #fffbeb; border-radius: 4px;")
                self.onu_count_label.setToolTip(tr('integrated_pon_panel.onus_tooltip_insufficient'))
            else:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #059669; padding: 4px; background-color: #ecfdf5; border-radius: 4px;")
                self.onu_count_label.setToolTip(f"{current_onus} ONUs conectadas - listo para simular")
            
            # Detectar cambios y reinicializar si es necesario
            if self.orchestrator_initialized and current_onus != self.last_onu_count:
                # Solo log cuando realmente hay cambios importantes
                print(f"🔄 ONUs cambiaron: {self.last_onu_count} → {current_onus}")
                self.auto_reinitialize(f"número de ONUs (detectadas: {current_onus})")
            elif not self.orchestrator_initialized and current_onus >= 2:
                # Solo mostrar una vez cuando se detectan ONUs suficientes
                if not hasattr(self, '_onu_ready_logged') or not self._onu_ready_logged:
                    print(f"✅ Detectadas {current_onus} ONUs - listo para inicializar")
                    self._onu_ready_logged = True
                    
                # Intentar inicializar automáticamente si hay ONUs suficientes
                if self.auto_initialize:
                    QTimer.singleShot(500, self.initialize_simulation)
            
            self.last_onu_count = current_onus
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
        # RL model UI removed - functionality moved to internal RL-DBA
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

    def load_smart_rl_model(self):
        """Cargar modelo RL entrenado para Smart RL DBA"""
        # Diálogo para seleccionar archivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar modelo RL entrenado",
            "",
            "Modelos RL (*.zip);;Todos los archivos (*)"
        )

        if not file_path:
            return

        try:
            # Obtener parámetros del entorno actual
            env_params = {
                'num_onus': self.get_onu_count_from_topology(),
                'traffic_scenario': self.scenario_combo.currentText(),
                'episode_duration': self.duration_spinbox.value(),
                'simulation_timestep': 0.0005
            }

            # Cargar modelo usando PONAdapter
            success, message = self.adapter.load_rl_model(file_path, env_params)

            if success:
                # Actualizar UI
                model_name = os.path.basename(file_path)
                self.rl_status_label.setText(f"✅ {model_name}")
                self.rl_status_label.setStyleSheet("color: green; font-size: 8pt;")

                # Cuando se carga un modelo RL, permitir Smart-RL y Smart-RL-SDN
                self.algorithm_combo.clear()
                self.algorithm_combo.addItem("Smart-RL")
                self.algorithm_combo.addItem("Smart-RL-SDN")
                self.algorithm_combo.setCurrentText("Smart-RL")

                # Marcar que hay un modelo RL cargado
                self.rl_model_loaded = True

                # Mostrar botón de desactivar RL
                self.unload_rl_model_btn.setVisible(True)

                # Mostrar mensaje de éxito
                QMessageBox.information(
                    self,
                    "Modelo Cargado",
                    f"Modelo RL cargado exitosamente:\n{model_name}\n\nAlgoritmos disponibles: 'Smart-RL' y 'Smart-RL-SDN'."
                )

                # Log
                self.results_panel.add_log_message(f"[SMART-RL] Modelo cargado: {model_name}")

                # Auto-reinicializar si es necesario
                if self.orchestrator_initialized:
                    self.auto_reinitialize(f"modelo Smart-RL cargado")

            else:
                # Error cargando
                self.rl_status_label.setText("❌ Error cargando")
                self.rl_status_label.setStyleSheet("color: red; font-size: 8pt;")

                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error cargando modelo RL:\n{message}"
                )

                self.results_panel.add_log_message(f"[ERROR] Error cargando modelo RL: {message}")

        except Exception as e:
            error_msg = f"Error inesperado cargando modelo: {str(e)}"
            self.rl_status_label.setText("❌ Error")
            self.rl_status_label.setStyleSheet("color: red; font-size: 8pt;")

            QMessageBox.critical(self, "Error", error_msg)
            self.results_panel.add_log_message(f"[ERROR] {error_msg}")

    def unload_rl_model(self):
        """Desactivar modelo RL y volver a algoritmos normales"""
        try:
            # Log estado inicial
            self.results_panel.add_log_message("[DEBUG] Iniciando desactivación RL...")

            # Verificar estado antes de desactivar
            if hasattr(self.adapter, 'smart_rl_algorithm'):
                has_smart_rl = self.adapter.smart_rl_algorithm is not None
                self.results_panel.add_log_message(f"[DEBUG] PONAdapter.smart_rl_algorithm antes: {has_smart_rl}")

            # Descargar modelo del adapter (PONAdapter system)
            if hasattr(self.adapter, 'unload_rl_model'):
                success, message = self.adapter.unload_rl_model()
                self.results_panel.add_log_message(f"[PON-ADAPTER] Desactivación: {message}")

                # Verificar estado después
                if hasattr(self.adapter, 'smart_rl_algorithm'):
                    has_smart_rl_after = self.adapter.smart_rl_algorithm is not None
                    self.results_panel.add_log_message(f"[DEBUG] PONAdapter.smart_rl_algorithm después: {has_smart_rl_after}")

            # Descargar modelo del training manager (TrainingManager system)
            if self.training_manager and hasattr(self.training_manager, 'simulation_manager'):
                if hasattr(self.training_manager.simulation_manager, 'loaded_model'):
                    had_model = self.training_manager.simulation_manager.loaded_model is not None
                    self.training_manager.simulation_manager.loaded_model = None
                    self.results_panel.add_log_message(f"[TRAINING-MANAGER] Modelo desactivado (tenía modelo: {had_model})")

            # Restaurar algoritmos DBA normales
            self.algorithm_combo.clear()
            if self.adapter.is_pon_available():
                algorithms = self.adapter.get_available_algorithms()
                self.results_panel.add_log_message(f"[DEBUG] Algoritmos disponibles después: {algorithms}")
                self.algorithm_combo.addItems(algorithms)

                # Volver a FCFS por defecto
                self.algorithm_combo.setCurrentText("FCFS")

                # CRÍTICO: Actualizar algoritmo en el adapter
                if hasattr(self.adapter, 'set_dba_algorithm'):
                    self.adapter.set_dba_algorithm("FCFS")
                    self.results_panel.add_log_message("[DEBUG] Algoritmo del adapter cambiado a FCFS")

            # Actualizar UI
            self.rl_status_label.setText(tr("integrated_pon_panel.rl_status_no_model"))
            self.rl_status_label.setStyleSheet("color: #666; font-size: 8pt;")

            # Ocultar botón de desactivar
            self.unload_rl_model_btn.setVisible(False)

            # Marcar que no hay modelo cargado
            self.rl_model_loaded = False

            # Log
            self.results_panel.add_log_message("[SMART-RL] Modelo RL desactivado - Volviendo a algoritmos normales")

            # Auto-reinicializar si es necesario
            if self.orchestrator_initialized:
                self.auto_reinitialize("modelo RL desactivado")

            # Mostrar confirmación
            QMessageBox.information(
                self,
                "RL Desactivado",
                "Simulación RL desactivada.\nAhora puede usar algoritmos DBA normales."
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error desactivando modelo RL:\n{str(e)}"
            )

    def update_rl_status_display(self):
        """Actualizar visualización del estado del modelo RL"""
        if self.adapter.is_smart_rl_available():
            model_info = self.adapter.get_rl_model_info()
            if model_info:
                model_name = os.path.basename(model_info.get('model_path', 'Modelo'))
                decisions = model_info.get('decisions_made', 0)

                self.rl_status_label.setText(f"✅ {model_name} ({decisions} decisiones)")
                self.rl_status_label.setStyleSheet("color: green; font-size: 8pt;")
            else:
                self.rl_status_label.setText("✅ Modelo cargado")
                self.rl_status_label.setStyleSheet("color: green; font-size: 8pt;")
        else:
            self.rl_status_label.setText(tr("integrated_pon_panel.rl_status_no_model"))
            self.rl_status_label.setStyleSheet("color: #666; font-size: 8pt;")
    
    
    
    
    
    
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
        print("🚀 Inicializando simulación PON...")
        
        if not self.adapter.is_pon_available():
            if getattr(self, 'verbose_debug', False):
                print("DEBUG Adapter no disponible")
            return
        
        # Obtener configuración automática
        num_onus = self.get_onu_count_from_topology()
        scenario = self.scenario_combo.currentText()
        algorithm = self.algorithm_combo.currentText()
        use_hybrid = self.hybrid_checkbox.isChecked()
        
        print(f"📊 Configuración: {num_onus} ONUs, Escenario: {scenario}, Algoritmo: {algorithm}, Híbrido: {use_hybrid}")
        
        # Validar que hay ONUs conectadas suficientes
        if num_onus < 2:
            if getattr(self, 'verbose_debug', False):
                print(f"DEBUG ONUs conectadas insuficientes: {num_onus} < 2")
            self.status_label.setText(tr('integrated_pon_panel.status_insufficient_onus'))
            self.status_label.setStyleSheet("color: red;")
            self.results_panel.add_log_message(tr('integrated_pon_panel.status_insufficient_topology').format(num_onus))
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
            
            # RL Agent no disponible - removido por independencia
            if algorithm == "RL Agent":
                self.results_panel.add_log_message("[ERROR] RL Agent externo no disponible. Use RL-DBA interno.")
            
            # Configurar algoritmo
            if use_hybrid:
                success_alg, msg_alg = self.adapter.set_hybrid_dba_algorithm(algorithm)
                if not success_alg:
                    self.results_panel.add_log_message(f"Warning: {msg_alg}")
            else:
                success_alg, msg_alg = self.adapter.set_dba_algorithm(algorithm)
                if not success_alg:
                    self.results_panel.add_log_message(f"Warning: {msg_alg}")
            
            arch_type_key = "integrated_pon_panel.arch_hybrid" if use_hybrid else "integrated_pon_panel.arch_classic"
            arch_type = tr(arch_type_key)
            self.status_label.setText(tr('integrated_pon_panel.status_initialized').format(arch_type))
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
                            # Actualizar dashboard SDN durante la simulación
                            sdn_metrics = self.adapter.get_sdn_metrics()
                            if sdn_metrics:
                                self.results_panel.add_log_message(f"📊 Actualizando métricas SDN (ciclo {cycle_num})")
                                self.parent().update_sdn_metrics(sdn_metrics)
                            else:
                                self.results_panel.add_log_message("⚠️ No hay métricas SDN disponibles")
                    
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
    
    def force_sdn_metrics_update(self, attempt_desc=""):
        """Forzar actualización de métricas SDN con múltiples intentos"""
        try:
            sdn_metrics = self.adapter.get_sdn_metrics()
            if sdn_metrics:
                self.results_panel.add_log_message(f"📊 {attempt_desc}: Obtenidas métricas SDN para {len(sdn_metrics.get('onu_metrics', {}))} ONUs")
                self.parent().update_sdn_metrics(sdn_metrics)
                return True
            else:
                self.results_panel.add_log_message(f"⚠️ {attempt_desc}: No hay métricas SDN disponibles")
                return False
        except Exception as e:
            self.results_panel.add_log_message(f"❌ {attempt_desc}: Error obteniendo métricas SDN: {e}")
            return False
            
    def process_hybrid_results(self, results):
        """Procesar resultados de simulación híbrida"""
        try:
            # Convertir formato de resultados híbridos al formato esperado por el panel de resultados
            if results and isinstance(results, dict):
                # El simulador híbrido devuelve resultados completos
                self.results_panel.update_simulation_results(results)
                self.results_panel.add_log_message("📊 Resultados procesados y gráficos generados")
                
                # Forzar actualización final del dashboard SDN con múltiples intentos
                # Intentar inmediatamente
                if not self.force_sdn_metrics_update("Primer intento"):
                    # Si falla, intentar 3 veces más con delays crecientes
                    delays = [500, 1000, 2000]  # 0.5s, 1s, 2s
                    for i, delay in enumerate(delays):
                        QTimer.singleShot(delay, lambda: self.force_sdn_metrics_update(f"Intento {i+2}"))
                
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
        
        # Actualizar estado del agente RL si está activo
        self.update_rl_status_display()
        
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
        
        # NUEVO: Detectar y conectar OLT_SDN al dashboard si existe
        olt_sdn_instance = self.adapter.get_olt_sdn_instance()
        if olt_sdn_instance:
            self.results_panel.add_log_message("🔌 OLT_SDN detectado - Conectando al dashboard...")
            main_window = self.parent()
            if hasattr(main_window, 'connect_olt_sdn_to_dashboard'):
                main_window.connect_olt_sdn_to_dashboard(olt_sdn_instance)
                self.results_panel.add_log_message("✅ Dashboard SDN conectado y actualizado")
            else:
                self.results_panel.add_log_message("⚠️ Ventana principal no tiene método connect_olt_sdn_to_dashboard")
            
            # Habilitar botón de actualización de Dashboard SDN
            if hasattr(self.results_panel, 'enable_sdn_dashboard_button'):
                self.results_panel.enable_sdn_dashboard_button(True)
                self.results_panel.add_log_message("📊 Botón 'Actualizar Dashboard SDN' habilitado")
        
        # Múltiples intentos de actualizar el dashboard SDN (método antiguo como respaldo)
        max_attempts = 3
        for attempt in range(max_attempts):
            self.results_panel.add_log_message(f"📊 Intento {attempt + 1} de {max_attempts} de obtener métricas SDN...")
            sdn_metrics = self.adapter.get_sdn_metrics()
            if sdn_metrics:
                self.results_panel.add_log_message(f"📊 Dashboard SDN: Actualizando con {len(sdn_metrics.get('onu_metrics', {}))} ONUs")
                self.parent().update_sdn_metrics(sdn_metrics)
                self.results_panel.add_log_message("✅ Dashboard SDN actualizado exitosamente")
                break
            else:
                self.results_panel.add_log_message("⚠️ Intento fallido de obtener métricas SDN")
        else:
            self.results_panel.add_log_message("❌ No se pudieron obtener métricas SDN después de múltiples intentos")
        
        # Mostrar gráficos automáticamente en panel (siempre activo)
        self.results_panel.show_charts_on_simulation_end()
        
        # NUEVO: Guardar gráficos automáticamente y mostrar ventana emergente
        self.handle_automatic_graphics_processing()
        
        # Actualización final de estado RL
        self.update_rl_status_display()
        
        # Emitir señal
        self.simulation_finished.emit()
        
        self.results_panel.add_log_message("🎯 Simulación finalizada - Resultados y gráficos procesados")
    
    
    def handle_automatic_graphics_processing(self):
        """Manejar el procesamiento automático de gráficos al finalizar simulación"""
        try:
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
                'detailed_logging': self.detailed_log_checkbox.isChecked()
            }
            
            # Mostrar ventana emergente PRIMERO (sin bloquear)
            should_popup = self.popup_window_checkbox.isChecked()
            if should_popup:
                self.show_graphics_popup_window(simulation_data, "", session_info)
            
            # DESPUÉS guardar los archivos en HILO SEPARADO (no bloquea UI)
            if hasattr(self.results_panel, 'charts_panel'):
                self.results_panel.add_log_message("💾 Guardando datos de simulación en segundo plano...")
                
                # Guardar asíncronamente
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, lambda: self._save_simulation_async(simulation_data, session_info))
            
        except Exception as e:
            self.results_panel.add_log_message(f"❌ Error en procesamiento automático: {e}")
            print(f"❌ Error en handle_automatic_graphics_processing: {e}")
    
    def _save_simulation_async(self, simulation_data: dict, session_info: dict):
        """Guardar datos de simulación de forma asíncrona (no bloquea UI)"""
        try:
            session_directory = self.graphics_saver.save_simulation_graphics_and_data(
                self.results_panel.charts_panel,
                simulation_data,
                session_info
            )
            
            if session_directory:
                self.results_panel.add_log_message(f"✅ Datos guardados en: {session_directory}")
                
                # Actualizar ventana emergente con el directorio
                if self.popup_window:
                    self.popup_window.update_session_directory(session_directory)
            else:
                self.results_panel.add_log_message("❌ Error guardando datos de simulación")
                
        except Exception as e:
            self.results_panel.add_log_message(f"❌ Error guardando datos: {e}")
            print(f"❌ Error en _save_simulation_async: {e}")
    
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
        # Solo log cuando sea relevante
        if getattr(self, 'verbose_debug', False):
            print("DEBUG Dispositivos cambiaron - actualizando conteo de ONUs")
        self.update_onu_count_display()
    
    def on_connections_changed(self):
        """Callback cuando cambian las conexiones en el canvas"""
        # Solo log cuando sea relevante  
        if getattr(self, 'verbose_debug', False):
            print("DEBUG Conexiones cambiaron - actualizando conteo de ONUs conectadas")
        self.update_onu_count_display()
    
    def periodic_onu_update(self):
        """Actualización periódica del conteo de ONUs y estado RL"""
        if self.canvas_reference:
            current_count = self.get_onu_count_from_topology()
            displayed_count = int(self.onu_count_label.text()) if self.onu_count_label.text().isdigit() else -1

            if current_count != displayed_count:
                print(f"DEBUG Actualizando conteo ONUs: {displayed_count} -> {current_count}")
                self.update_onu_count_display()

        # Actualizar estado del modelo RL
        self.update_rl_status_display()
    
    def force_onu_count_update(self):
        """Forzar actualización del conteo de ONUs"""
        print("🔄 Actualización manual de conteo de ONUs solicitada")
        self.update_onu_count_display()
        
        # Mostrar información detallada al usuario solo cuando se solicite manualmente
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
            # Parar timer de actualización de ONUs de forma segura
            if hasattr(self, 'onu_update_timer') and self.onu_update_timer:
                if self.onu_update_timer.isActive():
                    self.onu_update_timer.stop()
                self.onu_update_timer.deleteLater()
                self.onu_update_timer = None
                
            # Limpiar results_panel si existe
            if hasattr(self, 'results_panel') and self.results_panel:
                self.results_panel.cleanup()
            
            if hasattr(self, 'adapter') and self.adapter:
                # Limpiar adapter si es necesario
                pass
            
            if hasattr(self, 'popup_window') and self.popup_window:
                self.popup_window.close()
                self.popup_window = None
            
            
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

    def _update_rl_models_list(self):
        """Método stub - ya no usado pero requerido para compatibilidad"""
        # Este método fue eliminado en la refactorización a Smart RL interno
        # pero se mantiene como stub para evitar errores de atributo
        pass
    
    def retranslate_ui(self):
        """Actualizar todos los textos traducibles del panel"""
        # Título
        if hasattr(self, 'title_label'):
            self.title_label.setText(tr("integrated_pon_panel.title"))
        
        # GroupBox titles
        if hasattr(self, 'status_group'):
            self.status_group.setTitle(tr("integrated_pon_panel.status_group"))
        if hasattr(self, 'config_group'):
            self.config_group.setTitle(tr("integrated_pon_panel.config_group"))
        if hasattr(self, 'sim_group'):
            self.sim_group.setTitle(tr("integrated_pon_panel.simulation_group"))
        if hasattr(self, 'rl_info_group'):
            self.rl_info_group.setTitle(tr("integrated_pon_panel.rl_agent_group"))
        
        # Labels de configuración
        if hasattr(self, 'onus_connected_label'):
            self.onus_connected_label.setText(tr("integrated_pon_panel.onus_connected"))
        if hasattr(self, 'onu_count_label'):
            self.onu_count_label.setToolTip(tr("integrated_pon_panel.onus_tooltip"))
        if hasattr(self, 'dba_label'):
            self.dba_label.setText(tr("integrated_pon_panel.dba"))
        if hasattr(self, 'rl_model_label'):
            self.rl_model_label.setText(tr("integrated_pon_panel.rl_model"))
        if hasattr(self, 'scenario_label'):
            self.scenario_label.setText(tr("integrated_pon_panel.scenario"))
        if hasattr(self, 'architecture_label'):
            self.architecture_label.setText(tr("integrated_pon_panel.architecture"))
        if hasattr(self, 'time_label'):
            self.time_label.setText(tr("integrated_pon_panel.time_seconds"))
        if hasattr(self, 'steps_label'):
            self.steps_label.setText(tr("integrated_pon_panel.steps"))
        
        # Botones
        if hasattr(self, 'load_rl_model_btn'):
            self.load_rl_model_btn.setText(tr("integrated_pon_panel.load_rl_model"))
            self.load_rl_model_btn.setToolTip(tr("integrated_pon_panel.load_rl_model_tooltip"))
        if hasattr(self, 'unload_rl_model_btn'):
            self.unload_rl_model_btn.setText(tr("integrated_pon_panel.unload_rl_model"))
            self.unload_rl_model_btn.setToolTip(tr("integrated_pon_panel.unload_rl_model_tooltip"))
        if hasattr(self, 'init_btn'):
            self.init_btn.setText(tr("integrated_pon_panel.manual_init"))
            self.init_btn.setToolTip(tr("integrated_pon_panel.manual_init_tooltip"))
        if hasattr(self, 'start_btn'):
            self.start_btn.setText(tr("integrated_pon_panel.execute"))
        
        # Checkboxes
        if hasattr(self, 'hybrid_checkbox'):
            self.hybrid_checkbox.setText(tr("integrated_pon_panel.hybrid_architecture"))
            self.hybrid_checkbox.setToolTip(tr("integrated_pon_panel.hybrid_tooltip"))
        if hasattr(self, 'popup_window_checkbox'):
            self.popup_window_checkbox.setText(tr("integrated_pon_panel.show_popup"))
        if hasattr(self, 'detailed_log_checkbox'):
            self.detailed_log_checkbox.setText(tr("integrated_pon_panel.detailed_logging"))
        if hasattr(self, 'auto_init_checkbox'):
            self.auto_init_checkbox.setText(tr("integrated_pon_panel.auto_init"))
            self.auto_init_checkbox.setToolTip(tr("integrated_pon_panel.auto_init_tooltip"))
        
        # Tooltips de spinboxes
        if hasattr(self, 'duration_spinbox'):
            self.duration_spinbox.setToolTip(tr("integrated_pon_panel.time_tooltip"))
        if hasattr(self, 'steps_spinbox'):
            self.steps_spinbox.setToolTip(tr("integrated_pon_panel.steps_tooltip"))
        
        # Labels del panel de info RL
        if hasattr(self, 'rl_model_info_label'):
            self.rl_model_info_label.setText(tr("integrated_pon_panel.rl_model_info"))
        if hasattr(self, 'rl_last_action_label'):
            self.rl_last_action_label.setText(tr("integrated_pon_panel.rl_last_action"))
        
        # Label de información
        if hasattr(self, 'info_label'):
            self.info_label.setText(tr("integrated_pon_panel.results_info"))
        
        # Actualizar el status label con el estado actual si está inicializado
        if hasattr(self, 'status_label') and self.orchestrator_initialized:
            use_hybrid = self.hybrid_checkbox.isChecked()
            arch_type_key = "integrated_pon_panel.arch_hybrid" if use_hybrid else "integrated_pon_panel.arch_classic"
            arch_type = tr(arch_type_key)
            self.status_label.setText(tr('integrated_pon_panel.status_initialized').format(arch_type))
        
        # Actualizar el estado del modelo RL
        if hasattr(self, 'update_rl_status_display'):
            self.update_rl_status_display()
        
        # Actualizar ventana popup de gráficos si existe
        if hasattr(self, 'popup_window') and self.popup_window:
            self.popup_window.retranslate_ui()
        
        # Recargar estado (si está disponible, mantiene el estado traducido)
        self.check_pon_status()