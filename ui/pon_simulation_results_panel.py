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
from core import PONAdapter
from .pon_metrics_charts import PONMetricsChartsPanel

# Importar sistema de traducciones
from utils.translation_manager import translation_manager
tr = translation_manager.get_text


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
        self.sdn_metrics_updated = pyqtSignal(dict)  # Nueva señal para métricas SDN
        
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
        self.title_label = QLabel(tr("simulation_results.title"))
        self.title_label.setObjectName("pon_results_title")  # Identificador para QSS
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
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
        
        self.refresh_btn = QPushButton(tr("simulation_results.buttons.refresh"))
        self.refresh_btn.setObjectName("pon_results_button")  # Identificador para QSS
        self.refresh_btn.clicked.connect(self.refresh_results)
        controls_layout.addWidget(self.refresh_btn)
        
        # Botón para actualizar Dashboard SDN desde datos guardados
        self.update_sdn_dashboard_btn = QPushButton(tr("simulation_results.buttons.sdn_dashboard"))
        self.update_sdn_dashboard_btn.setObjectName("pon_results_button")
        self.update_sdn_dashboard_btn.setToolTip(tr("simulation_results.buttons.sdn_dashboard_tip"))
        self.update_sdn_dashboard_btn.clicked.connect(self.update_sdn_dashboard_from_data)
        # Ahora siempre visible - el método validará si hay datos disponibles
        controls_layout.addWidget(self.update_sdn_dashboard_btn)
        
        self.export_btn = QPushButton(tr("simulation_results.buttons.export"))
        self.export_btn.setObjectName("pon_results_button")  # Identificador para QSS
        self.export_btn.clicked.connect(self.export_results)
        controls_layout.addWidget(self.export_btn)
        
        self.auto_update_btn = QPushButton(tr("simulation_results.buttons.auto_update"))
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
        self.status_group = QGroupBox(tr("simulation_results.summary.status_group"))
        self.status_group.setObjectName("pon_results_group")
        status_layout = QGridLayout(self.status_group)
        
        self.status_label = QLabel(tr("simulation_results.summary.status_disconnected"))
        self.step_label = QLabel(tr("simulation_results.summary.step").format(0))
        self.time_label = QLabel(tr("simulation_results.summary.time").format("0.000"))
        self.algorithm_label = QLabel(tr("simulation_results.summary.algorithm").format("N/A"))
        
        self.status_text_label = QLabel(tr("simulation_results.summary.status"))
        self.current_step_label = QLabel(tr("simulation_results.summary.current_step"))
        self.simulated_time_label = QLabel(tr("simulation_results.summary.simulated_time"))
        self.dba_algorithm_label = QLabel(tr("simulation_results.summary.dba_algorithm"))
        
        status_layout.addWidget(self.status_text_label, 0, 0)
        status_layout.addWidget(self.status_label, 0, 1)
        status_layout.addWidget(self.current_step_label, 1, 0)
        status_layout.addWidget(self.step_label, 1, 1)
        status_layout.addWidget(self.simulated_time_label, 2, 0)
        status_layout.addWidget(self.time_label, 2, 1)
        status_layout.addWidget(self.dba_algorithm_label, 3, 0)
        status_layout.addWidget(self.algorithm_label, 3, 1)
        
        layout.addWidget(self.status_group)
        
        # Métricas principales
        self.metrics_group = QGroupBox(tr("simulation_results.summary.metrics_group"))
        self.metrics_group.setObjectName("pon_results_group")
        metrics_layout = QGridLayout(self.metrics_group)
        
        self.requests_label = QLabel("0")
        self.transmitted_label = QLabel("0.000 MB")
        self.delay_label = QLabel("0.000 s")
        self.throughput_label = QLabel("0.000 MB/s")
        self.utilization_label = QLabel("0.0%")
        
        # Barra de progreso para utilización
        self.utilization_bar = QProgressBar()
        self.utilization_bar.setRange(0, 100)
        self.utilization_bar.setValue(0)
        
        self.requests_processed_label = QLabel(tr("simulation_results.summary.requests_processed"))
        self.data_transmitted_label = QLabel(tr("simulation_results.summary.data_transmitted"))
        self.average_delay_label = QLabel(tr("simulation_results.summary.average_delay"))
        self.average_throughput_label = QLabel(tr("simulation_results.summary.average_throughput"))
        self.network_utilization_label = QLabel(tr("simulation_results.summary.network_utilization"))
        
        metrics_layout.addWidget(self.requests_processed_label, 0, 0)
        metrics_layout.addWidget(self.requests_label, 0, 1)
        metrics_layout.addWidget(self.data_transmitted_label, 1, 0)
        metrics_layout.addWidget(self.transmitted_label, 1, 1)
        metrics_layout.addWidget(self.average_delay_label, 2, 0)
        metrics_layout.addWidget(self.delay_label, 2, 1)
        metrics_layout.addWidget(self.average_throughput_label, 3, 0)
        metrics_layout.addWidget(self.throughput_label, 3, 1)
        metrics_layout.addWidget(self.network_utilization_label, 4, 0)
        metrics_layout.addWidget(self.utilization_label, 4, 1)
        metrics_layout.addWidget(self.utilization_bar, 5, 0, 1, 2)
        
        layout.addWidget(self.metrics_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, tr("simulation_results.tabs.summary"))
        
    def setup_network_metrics_tab(self):
        """Configurar tab de métricas de red"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabla de métricas
        self.network_table = QTableWidget()
        self.network_table.setColumnCount(2)
        self.network_table.setHorizontalHeaderLabels([
            tr("simulation_results.network.table_headers.metric"),
            tr("simulation_results.network.table_headers.value")
        ])
        self.network_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.network_table)
        
        self.tabs.addTab(tab, tr("simulation_results.tabs.network"))
    
    def setup_onu_stats_tab(self):
        """Configurar tab de estadísticas por ONU"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabla de ONUs
        self.onu_table = QTableWidget()
        self.onu_table.setColumnCount(7)
        self.onu_table.setHorizontalHeaderLabels([
            tr("simulation_results.onus.table_headers.onu_id"),
            tr("simulation_results.onus.table_headers.buffer"),
            tr("simulation_results.onus.table_headers.requests"),
            tr("simulation_results.onus.table_headers.transmitted"),
            tr("simulation_results.onus.table_headers.response_rate"),
            tr("simulation_results.onus.table_headers.losses"),
            tr("simulation_results.onus.table_headers.status")
        ])
        self.onu_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.onu_table)
        
        self.tabs.addTab(tab, tr("simulation_results.tabs.onus"))
    
    def setup_history_tab(self):
        """Configurar tab de historial detallado"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Crear splitter para dividir horizontalmente
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel izquierdo: Delays
        self.delays_group = QGroupBox(tr("simulation_results.history.delays_group"))
        self.delays_group.setObjectName("pon_results_group")
        delays_layout = QVBoxLayout(self.delays_group)
        
        self.delays_table = QTableWidget()
        self.delays_table.setColumnCount(3)
        self.delays_table.setHorizontalHeaderLabels([
            tr("simulation_results.history.delays_headers.time"),
            tr("simulation_results.history.delays_headers.onu"),
            tr("simulation_results.history.delays_headers.delay")
        ])
        delays_layout.addWidget(self.delays_table)
        
        splitter.addWidget(self.delays_group)
        
        # Panel derecho: Throughputs
        self.throughputs_group = QGroupBox(tr("simulation_results.history.throughputs_group"))
        self.throughputs_group.setObjectName("pon_results_group")
        throughputs_layout = QVBoxLayout(self.throughputs_group)
        
        self.throughputs_table = QTableWidget()
        self.throughputs_table.setColumnCount(3)
        self.throughputs_table.setHorizontalHeaderLabels([
            tr("simulation_results.history.throughputs_headers.time"),
            tr("simulation_results.history.throughputs_headers.onu"),
            tr("simulation_results.history.throughputs_headers.throughput")
        ])
        throughputs_layout.addWidget(self.throughputs_table)
        
        splitter.addWidget(self.throughputs_group)
        
        layout.addWidget(splitter)
        
        self.tabs.addTab(tab, tr("simulation_results.tabs.history"))
        
    def setup_charts_tab(self):
        """Configurar tab de gráficos de métricas"""
        # Crear panel de gráficos integrado
        self.charts_panel = PONMetricsChartsPanel()
        
        # Conectar señales
        self.charts_panel.chart_updated.connect(self.on_chart_updated)
        
        self.tabs.addTab(self.charts_panel, tr("simulation_results.tabs.charts"))
    
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
        
        self.clear_log_btn = QPushButton(tr("simulation_results.buttons.clear_log"))
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_controls.addWidget(self.clear_log_btn)
        
        log_controls.addStretch()
        layout.addLayout(log_controls)
        
        self.tabs.addTab(tab, tr("simulation_results.tabs.log"))
        
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
    
    def update_sdn_dashboard_from_data(self):
        """Actualizar Dashboard SDN calculando métricas desde datos de simulación guardados"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            from core.pon.sdn_metrics_processor import SDNMetricsProcessor
            from pathlib import Path
            import os
            
            # Verificar que existe la carpeta simulation_results
            default_path = Path.cwd() / "simulation_results"
            if not default_path.exists():
                default_path = Path.cwd()
            
            self.add_log_message("📊 Abriendo selector de archivo...")
            self.add_log_message("💡 Busca el archivo 'datos_simulacion.json' en la carpeta simulation_results")
            
            # Abrir diálogo para seleccionar archivo
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar datos_simulacion.json",
                str(default_path),
                "JSON files (*.json);;All files (*.*)"
            )
            
            if not filename:
                self.add_log_message("⚠️ Selección cancelada")
                return
            
            self.add_log_message(f"📂 Archivo seleccionado: {os.path.basename(filename)}")
            self.add_log_message(f"📍 Ruta completa: {filename}")
            
            # Crear procesador de métricas SDN
            processor = SDNMetricsProcessor()
            
            # Cargar datos de simulación
            self.add_log_message("⏳ Cargando datos de simulación...")
            if not processor.load_simulation_data(filename):
                self.add_log_message("❌ Error: El archivo no contiene datos de simulación válidos")
                QMessageBox.warning(
                    self,
                    "Error",
                    "El archivo seleccionado no contiene datos de simulación válidos.\n"
                    "Asegúrate de seleccionar un archivo 'datos_simulacion.json' generado por una simulación."
                )
                return
            
            self.add_log_message("⚙️ Calculando métricas SDN avanzadas...")
            self.add_log_message("   - Métricas globales (Fairness, Eficiencia Espectral)")
            self.add_log_message("   - Métricas por ONU (Latencia, Jitter, Throughput)")
            self.add_log_message("   - Métricas del Controlador SDN")
            self.add_log_message("   - Distribución de Ancho de Banda por Servicio")
            self.add_log_message("   - Cumplimiento SLA por T-CONT")
            
            # Calcular métricas SDN
            sdn_metrics = processor.calculate_sdn_metrics()
            
            if not sdn_metrics:
                self.add_log_message("❌ Error calculando métricas SDN")
                QMessageBox.warning(
                    self,
                    "Error",
                    "No se pudieron calcular las métricas SDN.\n"
                    "Verifica que el archivo contenga datos de transmisión válidos."
                )
                return
            
            self.add_log_message("✅ Métricas SDN calculadas exitosamente")
            
            # Mostrar resumen de métricas calculadas
            global_metrics = sdn_metrics.get('global_metrics', {})
            self.add_log_message(f"   📈 Fairness Index: {global_metrics.get('fairness_index', 0):.3f}")
            self.add_log_message(f"   📊 ONUs analizadas: {len(sdn_metrics.get('onu_metrics', {}))}")
            
            # Emitir señal con las métricas calculadas
            main_window = self.window()
            if hasattr(main_window, 'update_sdn_dashboard_final'):
                main_window.update_sdn_dashboard_final(sdn_metrics)
                self.add_log_message("📊 Dashboard SDN actualizado con métricas calculadas")
                self.add_log_message("💡 El Dashboard SDN se mostrará automáticamente")
                self.add_log_message("💡 También puedes usar Ctrl+D para mostrar/ocultar el dashboard")
            else:
                self.add_log_message("⚠️ No se pudo acceder al dashboard SDN")
            
            # Guardar métricas en el mismo directorio
            metrics_path = str(Path(filename).parent / "metricas_sdn.json")
            if processor.save_metrics(metrics_path):
                self.add_log_message(f"💾 Métricas guardadas en: {os.path.basename(metrics_path)}")
                self.add_log_message(f"📍 Ruta: {metrics_path}")
            
        except Exception as e:
            self.add_log_message(f"❌ Error actualizando Dashboard SDN: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Error",
                f"Error al procesar el archivo:\n{str(e)}\n\nRevisa la consola para más detalles."
            )
    
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
        
    def cleanup(self):
        """Limpiar recursos del panel de resultados"""
        try:
            # Parar timer de actualización de forma segura
            if hasattr(self, 'update_timer') and self.update_timer:
                if self.update_timer.isActive():
                    self.update_timer.stop()
                self.update_timer.deleteLater()
                self.update_timer = None
                
            print("Panel de resultados PON limpiado")
        except Exception as e:
            print(f"Warning en cleanup de resultados PON: {e}")
    
    def retranslate_ui(self):
        """Actualizar todos los textos traducibles del panel"""
        # Título principal
        self.title_label.setText(tr("simulation_results.title"))
        
        # Botones
        self.refresh_btn.setText(tr("simulation_results.buttons.refresh"))
        self.update_sdn_dashboard_btn.setText(tr("simulation_results.buttons.sdn_dashboard"))
        self.update_sdn_dashboard_btn.setToolTip(tr("simulation_results.buttons.sdn_dashboard_tip"))
        self.export_btn.setText(tr("simulation_results.buttons.export"))
        self.auto_update_btn.setText(tr("simulation_results.buttons.auto_update"))
        
        # Nombres de pestañas
        self.tabs.setTabText(0, tr("simulation_results.tabs.summary"))
        self.tabs.setTabText(1, tr("simulation_results.tabs.network"))
        self.tabs.setTabText(2, tr("simulation_results.tabs.onus"))
        self.tabs.setTabText(3, tr("simulation_results.tabs.history"))
        self.tabs.setTabText(4, tr("simulation_results.tabs.charts"))
        self.tabs.setTabText(5, tr("simulation_results.tabs.log"))
        
        # Tab Resumen - GroupBox titles
        if hasattr(self, 'status_group'):
            self.status_group.setTitle(tr("simulation_results.summary.status_group"))
        if hasattr(self, 'metrics_group'):
            self.metrics_group.setTitle(tr("simulation_results.summary.metrics_group"))
        
        # Tab Resumen - Labels de estado
        if hasattr(self, 'status_text_label'):
            self.status_text_label.setText(tr("simulation_results.summary.status"))
        if hasattr(self, 'current_step_label'):
            self.current_step_label.setText(tr("simulation_results.summary.current_step"))
        if hasattr(self, 'simulated_time_label'):
            self.simulated_time_label.setText(tr("simulation_results.summary.simulated_time"))
        if hasattr(self, 'dba_algorithm_label'):
            self.dba_algorithm_label.setText(tr("simulation_results.summary.dba_algorithm"))
        
        # Tab Resumen - Labels de métricas
        if hasattr(self, 'requests_processed_label'):
            self.requests_processed_label.setText(tr("simulation_results.summary.requests_processed"))
        if hasattr(self, 'data_transmitted_label'):
            self.data_transmitted_label.setText(tr("simulation_results.summary.data_transmitted"))
        if hasattr(self, 'average_delay_label'):
            self.average_delay_label.setText(tr("simulation_results.summary.average_delay"))
        if hasattr(self, 'average_throughput_label'):
            self.average_throughput_label.setText(tr("simulation_results.summary.average_throughput"))
        if hasattr(self, 'network_utilization_label'):
            self.network_utilization_label.setText(tr("simulation_results.summary.network_utilization"))
        
        # Tab Red - Headers
        if hasattr(self, 'network_table'):
            self.network_table.setHorizontalHeaderLabels([
                tr("simulation_results.network.table_headers.metric"),
                tr("simulation_results.network.table_headers.value")
            ])
        
        # Tab ONUs - Headers
        if hasattr(self, 'onu_table'):
            self.onu_table.setHorizontalHeaderLabels([
                tr("simulation_results.onus.table_headers.onu_id"),
                tr("simulation_results.onus.table_headers.buffer"),
                tr("simulation_results.onus.table_headers.requests"),
                tr("simulation_results.onus.table_headers.transmitted"),
                tr("simulation_results.onus.table_headers.response_rate"),
                tr("simulation_results.onus.table_headers.losses"),
                tr("simulation_results.onus.table_headers.status")
            ])
        
        # Tab Historial - GroupBox titles y Headers
        if hasattr(self, 'delays_group'):
            self.delays_group.setTitle(tr("simulation_results.history.delays_group"))
        if hasattr(self, 'throughputs_group'):
            self.throughputs_group.setTitle(tr("simulation_results.history.throughputs_group"))
        
        if hasattr(self, 'delays_table'):
            self.delays_table.setHorizontalHeaderLabels([
                tr("simulation_results.history.delays_headers.time"),
                tr("simulation_results.history.delays_headers.onu"),
                tr("simulation_results.history.delays_headers.delay")
            ])
        
        if hasattr(self, 'throughputs_table'):
            self.throughputs_table.setHorizontalHeaderLabels([
                tr("simulation_results.history.throughputs_headers.time"),
                tr("simulation_results.history.throughputs_headers.onu"),
                tr("simulation_results.history.throughputs_headers.throughput")
            ])
        
        # Tab Log - Botón
        if hasattr(self, 'clear_log_btn'):
            self.clear_log_btn.setText(tr("simulation_results.buttons.clear_log"))