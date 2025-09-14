"""
PON Simulation Results Panel
Panel de visualización de resultados de simulación PON integrado
"""

import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QTabWidget, QTableWidget,
                             QTableWidgetItem, QGroupBox, QGridLayout, 
                             QProgressBar, QSplitter, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from core.pon_adapter import PONAdapter
from .pon_metrics_charts import PONMetricsChartsPanel


class PONResultsPanel(QWidget):
    """Panel de visualización de resultados de simulación PON"""
    
    # Señales
    results_updated = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.adapter = PONAdapter()
        self.current_results = {}
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_results)
        self.dark_theme = False  # Estado del tema
        
        self.setup_ui()
        
    def set_theme(self, dark_theme):
        """Aplicar tema al panel de resultados"""
        self.dark_theme = dark_theme
        
        # Actualizar tema del panel de gráficos si existe
        if hasattr(self, 'charts_panel') and self.charts_panel:
            self.charts_panel.set_theme(dark_theme)
            
        # El estilo QSS se aplicará automáticamente desde la ventana principal
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("📊 Resultados de Simulación PON")
        title.setObjectName("pon_results_title")  # Identificador para QSS
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Crear tabs para diferentes tipos de resultados
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Resumen General
        self.setup_summary_tab()
        
        # Tab 2: Métricas de Red
        self.setup_network_metrics_tab()
        
        # Tab 3: Estadísticas por ONU
        self.setup_onu_stats_tab()
        
        # Tab 4: Historial Detallado
        self.setup_history_tab()
        
        # Tab 5: Gráficos de Métricas
        self.setup_charts_tab()
        
        # Tab 6: Log de Eventos
        self.setup_log_tab()
        
        # Botones de control
        controls_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setObjectName("pon_results_button")  # Identificador para QSS
        self.refresh_btn.clicked.connect(self.refresh_results)
        controls_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("📁 Exportar")
        self.export_btn.setObjectName("pon_results_button")  # Identificador para QSS
        self.export_btn.clicked.connect(self.export_results)
        controls_layout.addWidget(self.export_btn)
        
        self.auto_update_btn = QPushButton("⏱️ Auto-actualizar")
        self.auto_update_btn.setObjectName("pon_results_button")  # Identificador para QSS
        self.auto_update_btn.setCheckable(True)
        self.auto_update_btn.toggled.connect(self.toggle_auto_update)
        controls_layout.addWidget(self.auto_update_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
    def setup_summary_tab(self):
        """Configurar tab de resumen general"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Estado de la simulación
        status_group = QGroupBox("Estado de la Simulación")
        status_group.setObjectName("pon_results_group")
        status_layout = QGridLayout(status_group)
        
        self.status_label = QLabel("❓ No conectado")
        self.step_label = QLabel("Paso: 0")
        self.time_label = QLabel("Tiempo: 0.000s")
        self.algorithm_label = QLabel("Algoritmo: N/A")
        
        status_layout.addWidget(QLabel("Estado:"), 0, 0)
        status_layout.addWidget(self.status_label, 0, 1)
        status_layout.addWidget(QLabel("Paso actual:"), 1, 0)
        status_layout.addWidget(self.step_label, 1, 1)
        status_layout.addWidget(QLabel("Tiempo simulado:"), 2, 0)
        status_layout.addWidget(self.time_label, 2, 1)
        status_layout.addWidget(QLabel("Algoritmo DBA:"), 3, 0)
        status_layout.addWidget(self.algorithm_label, 3, 1)
        
        layout.addWidget(status_group)
        
        # Métricas principales
        metrics_group = QGroupBox("Métricas Principales")
        metrics_group.setObjectName("pon_results_group")
        metrics_layout = QGridLayout(metrics_group)
        
        self.requests_label = QLabel("0")
        self.transmitted_label = QLabel("0.000 MB")
        self.delay_label = QLabel("0.000 s")
        self.throughput_label = QLabel("0.000 MB/s")
        self.utilization_label = QLabel("0.0%")
        
        # Barra de progreso para utilización
        self.utilization_bar = QProgressBar()
        self.utilization_bar.setRange(0, 100)
        self.utilization_bar.setValue(0)
        
        metrics_layout.addWidget(QLabel("Solicitudes procesadas:"), 0, 0)
        metrics_layout.addWidget(self.requests_label, 0, 1)
        metrics_layout.addWidget(QLabel("Datos transmitidos:"), 1, 0)
        metrics_layout.addWidget(self.transmitted_label, 1, 1)
        metrics_layout.addWidget(QLabel("Delay promedio:"), 2, 0)
        metrics_layout.addWidget(self.delay_label, 2, 1)
        metrics_layout.addWidget(QLabel("Throughput promedio:"), 3, 0)
        metrics_layout.addWidget(self.throughput_label, 3, 1)
        metrics_layout.addWidget(QLabel("Utilización de red:"), 4, 0)
        metrics_layout.addWidget(self.utilization_label, 4, 1)
        metrics_layout.addWidget(self.utilization_bar, 5, 0, 1, 2)
        
        layout.addWidget(metrics_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "📋 Resumen")
        
    def setup_network_metrics_tab(self):
        """Configurar tab de métricas de red"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabla de métricas
        self.network_table = QTableWidget()
        self.network_table.setColumnCount(2)
        self.network_table.setHorizontalHeaderLabels(["Métrica", "Valor"])
        self.network_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.network_table)
        
        self.tabs.addTab(tab, "🌐 Red")
        
    def setup_onu_stats_tab(self):
        """Configurar tab de estadísticas por ONU"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabla de ONUs
        self.onu_table = QTableWidget()
        self.onu_table.setColumnCount(7)
        self.onu_table.setHorizontalHeaderLabels([
            "ONU ID", "Buffer (%)", "Solicitudes", "Transmitido (MB)", 
            "Tasa Respuesta (%)", "Pérdidas", "Estado"
        ])
        self.onu_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.onu_table)
        
        self.tabs.addTab(tab, "🏠 ONUs")
        
    def setup_history_tab(self):
        """Configurar tab de historial detallado"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Crear splitter para dividir horizontalmente
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Delays
        delays_group = QGroupBox("Historial de Delays")
        delays_group.setObjectName("pon_results_group")
        delays_layout = QVBoxLayout(delays_group)
        
        self.delays_table = QTableWidget()
        self.delays_table.setColumnCount(3)
        self.delays_table.setHorizontalHeaderLabels(["Tiempo", "ONU", "Delay (s)"])
        delays_layout.addWidget(self.delays_table)
        
        splitter.addWidget(delays_group)
        
        # Panel derecho: Throughputs
        throughputs_group = QGroupBox("Historial de Throughput")
        throughputs_group.setObjectName("pon_results_group")
        throughputs_layout = QVBoxLayout(throughputs_group)
        
        self.throughputs_table = QTableWidget()
        self.throughputs_table.setColumnCount(3)
        self.throughputs_table.setHorizontalHeaderLabels(["Tiempo", "ONU", "Throughput (MB/s)"])
        throughputs_layout.addWidget(self.throughputs_table)
        
        splitter.addWidget(throughputs_group)
        
        layout.addWidget(splitter)
        
        self.tabs.addTab(tab, "📈 Historial")
        
    def setup_charts_tab(self):
        """Configurar tab de gráficos de métricas"""
        # Crear panel de gráficos integrado
        self.charts_panel = PONMetricsChartsPanel()
        
        # Conectar señales
        self.charts_panel.chart_updated.connect(self.on_chart_updated)
        
        self.tabs.addTab(self.charts_panel, "📊 Gráficos")
        
    def setup_log_tab(self):
        """Configurar tab de log de eventos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        
        layout.addWidget(self.log_display)
        
        # Botones de control del log
        log_controls = QHBoxLayout()
        
        clear_log_btn = QPushButton("🗑️ Limpiar Log")
        clear_log_btn.clicked.connect(self.clear_log)
        log_controls.addWidget(clear_log_btn)
        
        log_controls.addStretch()
        layout.addLayout(log_controls)
        
        self.tabs.addTab(tab, "📝 Log")
        
    def set_adapter_reference(self, adapter):
        """Establecer referencia al adaptador PON"""
        self.adapter = adapter
        if adapter:
            adapter.set_log_callback(self.add_log_message)
            
    def add_log_message(self, message):
        """Agregar mensaje al log"""
        self.log_display.append(f"{message}")
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )
        
    def clear_log(self):
        """Limpiar el log"""
        self.log_display.clear()
        
    def refresh_results(self):
        """Actualizar todos los resultados"""
        if not self.adapter or not self.adapter.is_pon_available():
            self.update_status("❌ Adaptador no disponible")
            return
            
        try:
            # Obtener estado actual
            current_state = self.adapter.get_current_state()
            
            # Obtener estadísticas del orquestador
            orchestrator_stats = self.adapter.get_orchestrator_stats()
            
            # Obtener resumen de simulación si está disponible
            simulation_summary = self.adapter.get_simulation_summary()
            
            # Combinar todos los datos
            self.current_results = {
                'state': current_state,
                'orchestrator_stats': orchestrator_stats,
                'simulation_summary': simulation_summary
            }
            
            # Actualizar todas las interfaces
            self.update_summary_display()
            self.update_network_metrics_display()
            self.update_onu_stats_display()
            self.update_history_display()
            
            # Actualizar gráficos si está disponible
            if hasattr(self, 'charts_panel'):
                self.charts_panel.update_charts_with_data(self.current_results)
            
            self.results_updated.emit(self.current_results)
            
        except Exception as e:
            self.add_log_message(f"❌ Error actualizando resultados: {e}")
            
    def update_summary_display(self):
        """Actualizar display de resumen"""
        if not self.current_results:
            return
            
        state = self.current_results.get('state', {})
        simulation_summary = self.current_results.get('simulation_summary', {})
        
        # Actualizar estado
        if state.get('step', 0) > 0:
            self.status_label.setText("🟢 Simulación activa")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("🟡 Inicializada")
            self.status_label.setStyleSheet("color: orange;")
            
        self.step_label.setText(f"Paso: {state.get('step', 0)}")
        self.time_label.setText(f"Tiempo: {state.get('sim_time', 0):.6f}s")
        self.algorithm_label.setText(f"Algoritmo: {state.get('algorithm', 'N/A')}")
        
        # Actualizar métricas principales
        perf_metrics = simulation_summary.get('performance_metrics', {})
        
        requests = state.get('total_requests', 0)
        transmitted = state.get('total_transmitted', 0)
        delay = perf_metrics.get('mean_delay', 0)
        throughput = perf_metrics.get('mean_throughput', 0)
        utilization = perf_metrics.get('network_utilization', 0)
        
        self.requests_label.setText(str(requests))
        self.transmitted_label.setText(f"{transmitted:.3f} MB")
        self.delay_label.setText(f"{delay:.6f} s")
        self.throughput_label.setText(f"{throughput:.3f} MB/s")
        self.utilization_label.setText(f"{utilization:.1f}%")
        self.utilization_bar.setValue(int(utilization))
        
    def update_network_metrics_display(self):
        """Actualizar display de métricas de red"""
        orchestrator_stats = self.current_results.get('orchestrator_stats', {})
        olt_stats = orchestrator_stats.get('olt_stats', {})
        
        metrics = [
            ("Éxito de transmisión", f"{olt_stats.get('success_rate', 0):.1f}%"),
            ("Polls totales", str(olt_stats.get('total_polls', 0))),
            ("Transmisiones exitosas", str(olt_stats.get('successful_transmissions', 0))),
            ("Transmisiones fallidas", str(olt_stats.get('failed_transmissions', 0))),
            ("ONUs registradas", str(olt_stats.get('registered_onus', 0))),
            ("Tasa de transmisión", f"{olt_stats.get('transmition_rate', 0):.0f} Mbps"),
            ("Probabilidad de asignación", f"{orchestrator_stats.get('allocation_probability', 0):.3f}"),
            ("Probabilidad de bloqueo", f"{orchestrator_stats.get('blocking_probability', 0):.3f}")
        ]
        
        self.network_table.setRowCount(len(metrics))
        for i, (metric, value) in enumerate(metrics):
            self.network_table.setItem(i, 0, QTableWidgetItem(metric))
            self.network_table.setItem(i, 1, QTableWidgetItem(value))
            
    def update_onu_stats_display(self):
        """Actualizar display de estadísticas por ONU"""
        orchestrator_stats = self.current_results.get('orchestrator_stats', {})
        onu_stats = orchestrator_stats.get('onu_stats', {})
        
        self.onu_table.setRowCount(len(onu_stats))
        
        for row, (onu_id, stats) in enumerate(onu_stats.items()):
            buffer_occupancy = stats.get('buffer_occupancy', 0) * 100
            requests = stats.get('total_requests_generated', 0)
            transmitted = stats.get('data_transmitted', 0)
            response_rate = stats.get('response_rate', 0)
            losses = stats.get('lost_packets_count', 0)
            
            # Determinar estado
            if buffer_occupancy > 80:
                status = "🔴 Saturado"
                status_color = QColor(255, 0, 0)
            elif buffer_occupancy > 50:
                status = "🟡 Ocupado"
                status_color = QColor(255, 165, 0)
            else:
                status = "🟢 Normal"
                status_color = QColor(0, 255, 0)
            
            self.onu_table.setItem(row, 0, QTableWidgetItem(onu_id))
            self.onu_table.setItem(row, 1, QTableWidgetItem(f"{buffer_occupancy:.1f}%"))
            self.onu_table.setItem(row, 2, QTableWidgetItem(str(requests)))
            self.onu_table.setItem(row, 3, QTableWidgetItem(f"{transmitted:.3f}"))
            self.onu_table.setItem(row, 4, QTableWidgetItem(f"{response_rate:.1f}%"))
            self.onu_table.setItem(row, 5, QTableWidgetItem(str(losses)))
            
            status_item = QTableWidgetItem(status)
            status_item.setForeground(status_color)
            self.onu_table.setItem(row, 6, status_item)
            
    def update_history_display(self):
        """Actualizar display de historial"""
        # Implementación simplificada - en una versión completa se mostrarían más datos históricos
        state = self.current_results.get('state', {})
        
        delays = state.get('delays', [])[-10:]  # Últimos 10
        throughputs = state.get('throughputs', [])[-10:]  # Últimos 10
        
        # Actualizar tabla de delays
        self.delays_table.setRowCount(len(delays))
        for i, delay_data in enumerate(delays):
            self.delays_table.setItem(i, 0, QTableWidgetItem(f"{i}"))
            self.delays_table.setItem(i, 1, QTableWidgetItem(delay_data.get('onu_id', 'N/A')))
            self.delays_table.setItem(i, 2, QTableWidgetItem(f"{delay_data.get('delay', 0):.6f}"))
            
        # Actualizar tabla de throughputs
        self.throughputs_table.setRowCount(len(throughputs))
        for i, throughput_data in enumerate(throughputs):
            self.throughputs_table.setItem(i, 0, QTableWidgetItem(f"{i}"))
            self.throughputs_table.setItem(i, 1, QTableWidgetItem(throughput_data.get('onu_id', 'N/A')))
            self.throughputs_table.setItem(i, 2, QTableWidgetItem(f"{throughput_data.get('throughput', 0):.6f}"))
            
    def toggle_auto_update(self, enabled):
        """Activar/desactivar actualización automática"""
        if enabled:
            self.update_timer.start(2000)  # Actualizar cada 2 segundos
            self.auto_update_btn.setText("⏹️ Detener")
        else:
            self.update_timer.stop()
            self.auto_update_btn.setText("⏱️ Auto-actualizar")
            
    def export_results(self):
        """Exportar resultados a archivo JSON"""
        if not self.current_results:
            self.add_log_message("❌ No hay resultados para exportar")
            return
            
        try:
            from PyQt5.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Resultados PON",
                "resultados_simulacion.json",
                "JSON files (*.json)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_results, f, indent=2, ensure_ascii=False, default=str)
                
                self.add_log_message(f"✅ Resultados exportados a: {filename}")
                
        except Exception as e:
            self.add_log_message(f"❌ Error exportando resultados: {e}")
            
    def on_chart_updated(self, chart_type):
        """Callback cuando se actualiza un gráfico"""
        self.add_log_message(f"📊 Gráfico actualizado: {chart_type}")
    
    def show_charts_on_simulation_end(self):
        """Mostrar automáticamente los gráficos al finalizar simulación"""
        if hasattr(self, 'charts_panel') and self.current_results:
            # Cambiar al tab de gráficos
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == "📊 Gráficos":
                    self.tabs.setCurrentIndex(i)
                    break
            
            # Actualizar gráficos
            self.charts_panel.update_charts_with_data(self.current_results)
            self.add_log_message("📊 Gráficos actualizados automáticamente al finalizar simulación")
    
    def export_charts_to_directory(self, directory):
        """Exportar gráficos a directorio"""
        if hasattr(self, 'charts_panel'):
            success = self.charts_panel.export_charts(directory)
            if success:
                self.add_log_message(f"📁 Gráficos exportados a: {directory}")
                return True
            else:
                self.add_log_message("❌ Error exportando gráficos")
                return False
        return False
    
    def update_status(self, status):
        """Actualizar estado general"""
        self.status_label.setText(status)