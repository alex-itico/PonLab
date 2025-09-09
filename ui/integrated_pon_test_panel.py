"""
Integrated PON Test Panel
Panel de prueba mejorado que usa el adaptador integrado y muestra gráficos automáticamente
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QSpinBox, QTextEdit,
                             QGroupBox, QGridLayout, QSizePolicy, QProgressBar,
                             QCheckBox, QSlider, QSplitter)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from core.integrated_netponpy_adapter import IntegratedPONAdapter
from .pon_simulation_results_panel import PONResultsPanel
from .auto_graphics_saver import AutoGraphicsSaver
from .graphics_popup_window import GraphicsPopupWindow


class IntegratedPONTestPanel(QWidget):
    """Panel de prueba mejorado para la integración PON con visualización automática"""
    
    # Señales
    status_updated = pyqtSignal(str)
    simulation_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.adapter = IntegratedPONAdapter()
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self.step_simulation)
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
        self.orchestrator_initialized = False
        
        self.setup_ui()
        self.check_pon_status()
        
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
        
        # Número de ONUs
        config_layout.addWidget(QLabel("ONUs:"), 0, 0)
        self.onu_spinbox = QSpinBox()
        self.onu_spinbox.setRange(2, 32)
        self.onu_spinbox.setValue(4)
        self.onu_spinbox.valueChanged.connect(self.on_config_changed)
        config_layout.addWidget(self.onu_spinbox, 0, 1)
        
        # Algoritmo DBA
        config_layout.addWidget(QLabel("Algoritmo DBA:"), 1, 0)
        self.algorithm_combo = QComboBox()
        if self.adapter.is_pon_available():
            self.algorithm_combo.addItems(self.adapter.get_available_algorithms())
        self.algorithm_combo.currentTextChanged.connect(self.on_algorithm_changed)
        config_layout.addWidget(self.algorithm_combo, 1, 1)
        
        # Escenario de tráfico
        config_layout.addWidget(QLabel("Escenario:"), 2, 0)
        self.scenario_combo = QComboBox()
        if self.adapter.is_pon_available():
            self.scenario_combo.addItems(self.adapter.get_available_traffic_scenarios())
        config_layout.addWidget(self.scenario_combo, 2, 1)
        
        # Pasos de simulación
        config_layout.addWidget(QLabel("Pasos:"), 3, 0)
        self.steps_spinbox = QSpinBox()
        self.steps_spinbox.setRange(100, 10000)
        self.steps_spinbox.setValue(1000)
        self.steps_spinbox.setSingleStep(100)
        config_layout.addWidget(self.steps_spinbox, 3, 1)
        
        layout.addWidget(config_group)
        
        # Controles de simulación
        sim_group = QGroupBox("Simulación")
        sim_layout = QVBoxLayout(sim_group)
        
        # Botones principales
        buttons_layout = QGridLayout()
        
        self.init_btn = QPushButton("🚀 Inicializar")
        self.init_btn.clicked.connect(self.initialize_simulation)
        buttons_layout.addWidget(self.init_btn, 0, 0)
        
        self.start_btn = QPushButton("▶️ Ejecutar")
        self.start_btn.clicked.connect(self.run_full_simulation)
        self.start_btn.setEnabled(False)
        buttons_layout.addWidget(self.start_btn, 0, 1)
        
        self.step_btn = QPushButton("👣 Paso a Paso")
        self.step_btn.clicked.connect(self.toggle_step_simulation)
        self.step_btn.setEnabled(False)
        buttons_layout.addWidget(self.step_btn, 1, 0)
        
        self.reset_btn = QPushButton("🔄 Reiniciar")
        self.reset_btn.clicked.connect(self.reset_simulation)
        buttons_layout.addWidget(self.reset_btn, 1, 1)
        
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
        
        sim_layout.addLayout(options_layout)
        
        # Información sobre visualización de resultados
        info_label = QLabel("Los resultados se mostraran en una ventana emergente al terminar la simulacion")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; padding: 4px;")
        sim_layout.addWidget(info_label)
        
        layout.addWidget(sim_group)
        
        # Métricas en tiempo real
        metrics_group = QGroupBox("Métricas en Tiempo Real")
        metrics_layout = QGridLayout(metrics_group)
        
        self.steps_label = QLabel("Pasos: 0")
        self.requests_label = QLabel("Solicitudes: 0")
        self.delay_label = QLabel("Delay: 0.000s")
        self.throughput_label = QLabel("Throughput: 0.00 MB/s")
        
        metrics_layout.addWidget(self.steps_label, 0, 0)
        metrics_layout.addWidget(self.requests_label, 0, 1)
        metrics_layout.addWidget(self.delay_label, 1, 0)
        metrics_layout.addWidget(self.throughput_label, 1, 1)
        
        layout.addWidget(metrics_group)
        
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
    
    def on_config_changed(self):
        """Manejar cambios en la configuración"""
        if self.orchestrator_initialized:
            current_onus = self.onu_spinbox.value()
            if current_onus != self.last_onu_count:
                self.status_label.setText("WARNING Configuracion cambiada - reinicializar")
                self.status_label.setStyleSheet("color: orange;")
                self.orchestrator_initialized = False
                self.start_btn.setEnabled(False)
                self.step_btn.setEnabled(False)
    
    def on_algorithm_changed(self):
        """Manejar cambio de algoritmo DBA"""
        if self.orchestrator_initialized:
            algorithm = self.algorithm_combo.currentText()
            if algorithm != self.last_algorithm:
                success = self.adapter.set_dba_algorithm(algorithm)
                if success:
                    self.last_algorithm = algorithm
                    self.results_panel.add_log_message(f"Algoritmo cambiado a: {algorithm}")
    
    def toggle_detailed_logging(self, enabled):
        """Activar/desactivar logging detallado"""
        self.adapter.set_detailed_logging(enabled)
    
    def initialize_simulation(self):
        """Inicializar simulación"""
        if not self.adapter.is_pon_available():
            return
        
        self.results_panel.add_log_message("🚀 Inicializando simulación...")
        
        # Obtener configuración
        num_onus = self.onu_spinbox.value()
        
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
            
            # Configurar algoritmo
            algorithm = self.algorithm_combo.currentText()
            self.adapter.set_dba_algorithm(algorithm)
            self.last_algorithm = algorithm
            
            self.status_label.setText("✅ Simulación inicializada")
            self.status_label.setStyleSheet("color: green;")
            
            self.start_btn.setEnabled(True)
            self.step_btn.setEnabled(True)
            
            self.results_panel.add_log_message(f"✅ {message}")
            
        else:
            self.status_label.setText(f"❌ Error: {message if 'message' in locals() else 'Error desconocido'}")
            self.status_label.setStyleSheet("color: red;")
    
    def run_full_simulation(self):
        """Ejecutar simulación completa"""
        if not self.orchestrator_initialized:
            return
        
        steps = self.steps_spinbox.value()
        
        # Mostrar barra de progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, steps)
        self.progress_bar.setValue(0)
        
        # Deshabilitar botones durante simulación
        self.start_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        
        self.results_panel.add_log_message(f"🏃 Ejecutando simulación completa: {steps} pasos...")
        
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
                self.results_panel.add_log_message("✅ Simulación NetSim completada")
                self.on_simulation_finished()
        
        # Ejecutar simulación
        success = self.adapter.run_netsim_simulation(timesteps=steps, callback=simulation_callback)
        
        if not success:
            self.results_panel.add_log_message("❌ Error en simulación")
            self.on_simulation_finished()
    
    def toggle_step_simulation(self):
        """Activar/desactivar simulación paso a paso"""
        if not self.orchestrator_initialized:
            return
        
        if not self.simulation_running:
            # Iniciar simulación paso a paso
            self.simulation_running = True
            self.step_btn.setText("⏸️ Pausar")
            self.start_btn.setEnabled(False)
            
            # Configurar timer para simulación paso a paso
            self.simulation_timer.start(100)  # 100ms entre pasos
            self.results_panel.add_log_message("🔄 Simulación paso a paso iniciada")
            
        else:
            # Pausar simulación paso a paso
            self.simulation_running = False
            self.step_btn.setText("👣 Paso a Paso")
            self.start_btn.setEnabled(True)
            
            self.simulation_timer.stop()
            self.results_panel.add_log_message("⏸️ Simulación paso a paso pausada")
    
    def step_simulation(self):
        """Ejecutar un paso de simulación"""
        if not self.simulation_running:
            return
        
        result = self.adapter.step_simulation()
        
        if result:
            self.step_count += 1
            
            # Actualizar métricas básicas
            self.steps_label.setText(f"Pasos: {self.step_count}")
            
            # Verificar si debe terminar
            if result.get('done', False) or self.step_count >= self.steps_spinbox.value():
                self.toggle_step_simulation()  # Detener simulación
                self.on_simulation_finished()
        else:
            self.toggle_step_simulation()  # Detener en caso de error
    
    def update_realtime_metrics(self, data):
        """Actualizar métricas en tiempo real"""
        steps = data.get('steps', 0)
        requests = data.get('total_requests_processed', 0)
        delay = data.get('mean_delay', 0)
        throughput = data.get('mean_throughput', 0)
        
        self.steps_label.setText(f"Pasos: {steps}")
        self.requests_label.setText(f"Solicitudes: {requests}")
        self.delay_label.setText(f"Delay: {delay:.6f}s")
        self.throughput_label.setText(f"Throughput: {throughput:.2f} MB/s")
    
    def on_simulation_finished(self):
        """Callback cuando termina la simulación"""
        # Rehabilitar botones
        self.start_btn.setEnabled(True)
        self.step_btn.setEnabled(True)
        self.step_btn.setText("👣 Paso a Paso")
        
        # Ocultar barra de progreso
        self.progress_bar.setVisible(False)
        
        # Actualizar resultados finales
        self.results_panel.refresh_results()
        
        # Mostrar gráficos automáticamente en panel si está habilitado
        if self.auto_charts_checkbox.isChecked():
            self.results_panel.show_charts_on_simulation_end()
        
        # NUEVO: Guardar gráficos automáticamente y mostrar ventana emergente
        self.handle_automatic_graphics_processing()
        
        # Emitir señal
        self.simulation_finished.emit()
        
        self.results_panel.add_log_message("🎯 Simulación finalizada - Resultados y gráficos procesados")
    
    def reset_simulation(self):
        """Reiniciar simulación"""
        # Detener simulación si está corriendo
        if self.simulation_running:
            self.toggle_step_simulation()
        
        # Reiniciar contadores
        self.step_count = 0
        self.orchestrator_initialized = False
        
        # Reiniciar estado de botones
        self.start_btn.setEnabled(False)
        self.step_btn.setEnabled(False)
        self.step_btn.setText("👣 Paso a Paso")
        
        # Limpiar métricas
        self.steps_label.setText("Pasos: 0")
        self.requests_label.setText("Solicitudes: 0")
        self.delay_label.setText("Delay: 0.000s")
        self.throughput_label.setText("Throughput: 0.00 MB/s")
        
        # Actualizar estado
        self.status_label.setText("🔄 Sistema reiniciado")
        self.status_label.setStyleSheet("color: blue;")
        
        # Limpiar resultados
        if hasattr(self.results_panel, 'charts_panel'):
            self.results_panel.charts_panel.clear_all_charts()
        
        self.results_panel.add_log_message("🔄 Sistema reiniciado - listo para nueva simulación")
    
    def handle_automatic_graphics_processing(self):
        """Manejar el procesamiento automático de gráficos al finalizar simulación"""
        try:
            # Verificar si alguna opción automática está habilitada
            should_save = self.auto_save_checkbox.isChecked()
            should_popup = self.popup_window_checkbox.isChecked()
            
            if not (should_save or should_popup):
                return  # No hacer nada si no hay opciones habilitadas
            
            # Obtener datos completos de la simulación
            simulation_data = {
                'current_state': self.adapter.get_current_state(),
                'simulation_summary': self.adapter.get_simulation_summary(),
                'orchestrator_stats': self.adapter.get_orchestrator_stats()
            }
            
            # Recopilar información de la sesión
            session_info = {
                'num_onus': self.onu_spinbox.value(),
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
    
    def update_topology_info(self):
        """Actualizar información de topología desde el canvas"""
        try:
            if self.canvas_reference:
                # Aquí se puede añadir lógica para actualizar info de topología
                # por ahora solo log que se ejecutó
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
                print("INFO Orquestador PON reseteado por cambio de topologia")
            else:
                print("WARNING No hay adapter para resetear orquestador")
        except Exception as e:
            print(f"ERROR reseteando orquestador: {e}")
    
    def cleanup(self):
        """Limpiar recursos del panel"""
        try:
            if hasattr(self, 'adapter') and self.adapter:
                # Limpiar adapter si es necesario
                pass
            
            if hasattr(self, 'popup_window') and self.popup_window:
                self.popup_window.close()
                self.popup_window = None
            
            print("Panel PON integrado limpiado")
            
        except Exception as e:
            print(f"ERROR limpiando panel PON: {e}")