"""
PON SDN Dashboard
Panel para mostrar métricas y estadísticas avanzadas del controlador SDN
Incluye métricas exclusivas de SDN: eficiencia espectral, SLA compliance, 
tiempo de respuesta del controlador, nivel de congestión, etc.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QFrame, QProgressBar, QGridLayout,
                           QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QPushButton,
                           QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter
import typing
import json
from pathlib import Path
import os

# Importar PyQtChart con manejo de error
try:
    from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QBarSet, QBarSeries, QBarCategoryAxis
    HAS_QTCHART = True
except ImportError:
    HAS_QTCHART = False
    print("Warning: PyQtChart no está instalado. Las gráficas avanzadas no estarán disponibles.")

class MetricCard(QFrame):
    """Widget para mostrar una métrica individual con título y valor"""
    
    def __init__(self, title: str, value: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setObjectName("MetricCard")  # Para identificación en CSS
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)  # Título más visible
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)  # Centrado
        title_label.setWordWrap(True)  # Permitir salto de línea si es necesario
        layout.addWidget(title_label)
        
        # Valor
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        value_font = QFont()
        value_font.setPointSize(30)  # Valor prominente
        value_font.setBold(True)  # Hacerlo más prominente
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Descripción
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("MetricDescription")
            desc_font = QFont()
            desc_font.setPointSize(14)  # Descripción más legible
            desc_label.setFont(desc_font)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setWordWrap(True)  # Permitir salto de línea si es necesario
            layout.addWidget(desc_label)
    
    def update_value(self, new_value: str):
        """Actualizar el valor mostrado"""
        self.value_label.setText(new_value)

class PONSDNDashboard(QWidget):
    """Panel para mostrar métricas y estadísticas avanzadas del controlador SDN"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PONSDNDashboard")
        
        # Detectar tema del parent si existe
        self.dark_theme = False
        if parent and hasattr(parent, 'dark_theme'):
            self.dark_theme = parent.dark_theme
        
        self.setup_ui()
        
        # Aplicar tema inicial
        self.set_theme(self.dark_theme)
        
    def setup_ui(self):
        """Configurar la interfaz del dashboard con pestañas"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Título del dashboard
        title_label = QLabel("📊 Dashboard SDN - Métricas Avanzadas")
        title_label.setObjectName("DashboardTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Botón para cargar última simulación
        test_button_layout = QHBoxLayout()
        self.test_button = QPushButton("📂 CARGAR ÚLTIMA SIMULACIÓN")
        self.test_button.setObjectName("TestButton")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #3D8B40;
            }
        """)
        self.test_button.clicked.connect(self.load_latest_simulation)
        test_button_layout.addWidget(self.test_button)
        main_layout.addLayout(test_button_layout)
        
        # Crear pestañas para organizar las métricas
        self.tabs = QTabWidget()
        self.tabs.setObjectName("SDNDashboardTabs")
        
        # Pestaña 1: Resumen Global
        self.tab_global = self._create_global_tab()
        self.tabs.addTab(self.tab_global, "🌐 Resumen Global")
        
        # Pestaña 2: Métricas por ONU
        self.tab_onu = self._create_onu_tab()
        self.tabs.addTab(self.tab_onu, "📡 Métricas por ONU")
        
        # Pestaña 3: QoS y SLA
        self.tab_qos = self._create_qos_tab()
        self.tabs.addTab(self.tab_qos, "✅ QoS y SLA")
        
        # Pestaña 4: Controlador SDN
        self.tab_controller = self._create_controller_tab()
        self.tabs.addTab(self.tab_controller, "🎛️ Controlador SDN")
        
        # Pestaña 5: Ancho de Banda
        self.tab_bandwidth = self._create_bandwidth_tab()
        self.tabs.addTab(self.tab_bandwidth, "📊 Ancho de Banda")
        
        main_layout.addWidget(self.tabs)
    
    def _create_global_tab(self):
        """Crear pestaña de resumen global"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Área con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QGridLayout(content)
        
        # Métricas globales principales
        self.reconfig_card = MetricCard(
            "Reconfiguraciones",
            "0",
            "Ajustes automáticos del controlador"
        )
        content_layout.addWidget(self.reconfig_card, 0, 0)
        
        self.grant_util_card = MetricCard(
            "Utilización de Grants",
            "0%",
            "Porcentaje de grants utilizados"
        )
        content_layout.addWidget(self.grant_util_card, 0, 1)
        
        self.fairness_card = MetricCard(
            "Índice de Fairness (Jain)",
            "0.0",
            "Equidad en distribución de recursos (0-1)"
        )
        content_layout.addWidget(self.fairness_card, 1, 0)
        
        self.qos_card = MetricCard(
            "Violaciones QoS",
            "0",
            "Violaciones de calidad de servicio"
        )
        content_layout.addWidget(self.qos_card, 1, 1)
        
        self.spectral_eff_card = MetricCard(
            "Eficiencia Espectral",
            "0.0 bits/Hz",
            "Eficiencia en uso del espectro"
        )
        content_layout.addWidget(self.spectral_eff_card, 2, 0)
        
        self.total_decisions_card = MetricCard(
            "Decisiones del Controlador",
            "0",
            "Total de decisiones DBA tomadas"
        )
        content_layout.addWidget(self.total_decisions_card, 2, 1)
        
        # Gráfica de fairness histórico
        if HAS_QTCHART:
            self.fairness_chart = QChart()
            self.fairness_chart.setTitle("Histórico de Fairness")
            self.fairness_series = QLineSeries()
            self.fairness_chart.addSeries(self.fairness_series)
            
            axis_x = QValueAxis()
            axis_x.setTitleText("Ciclos")
            axis_y = QValueAxis()
            axis_y.setTitleText("Fairness")
            axis_y.setRange(0, 1)
            
            self.fairness_chart.setAxisX(axis_x, self.fairness_series)
            self.fairness_chart.setAxisY(axis_y, self.fairness_series)
            
            chart_view = QChartView(self.fairness_chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            content_layout.addWidget(chart_view, 3, 0, 1, 2)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab
    
    def _create_onu_tab(self):
        """Crear pestaña de métricas por ONU"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabla de métricas por ONU
        self.onu_table = QTableWidget()
        self.onu_table.setObjectName("ONUMetricsTable")
        self.onu_table.setColumnCount(7)
        self.onu_table.setHorizontalHeaderLabels([
            "ONU ID",
            "Latencia Prom.",
            "Jitter",
            "Pérdidas",
            "Throughput",
            "Eficiencia Grant",
            "Congestión"
        ])
        header = self.onu_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.onu_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.onu_table)
        return tab
    
    def _create_qos_tab(self):
        """Crear pestaña de QoS y cumplimiento SLA"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Área con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Tabla de cumplimiento SLA por T-CONT
        sla_label = QLabel("📋 Cumplimiento SLA por T-CONT")
        sla_label.setFont(QFont("Arial", 12, QFont.Bold))
        content_layout.addWidget(sla_label)
        
        self.sla_table = QTableWidget()
        self.sla_table.setObjectName("SLATable")
        self.sla_table.setColumnCount(5)
        self.sla_table.setHorizontalHeaderLabels([
            "ONU ID",
            "T-CONT",
            "Cumplidos",
            "Violados",
            "% Cumplimiento"
        ])
        header = self.sla_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.sla_table.setAlternatingRowColors(True)
        
        content_layout.addWidget(self.sla_table)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab
    
    def _create_controller_tab(self):
        """Crear pestaña del controlador SDN"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QGridLayout(content)
        
        # Métricas del controlador
        self.controller_response_card = MetricCard(
            "Tiempo de Respuesta",
            "0.0 ms",
            "Tiempo medio de respuesta del controlador"
        )
        content_layout.addWidget(self.controller_response_card, 0, 0)
        
        self.decision_latency_card = MetricCard(
            "Latencia de Decisión",
            "0.0 ms",
            "Latencia promedio en toma de decisiones"
        )
        content_layout.addWidget(self.decision_latency_card, 0, 1)
        
        self.reassignment_rate_card = MetricCard(
            "Tasa de Reasignación",
            "0",
            "Número de reasignaciones de recursos"
        )
        content_layout.addWidget(self.reassignment_rate_card, 1, 0)
        
        self.bw_utilization_card = MetricCard(
            "Utilización de Ancho de Banda",
            "0.0%",
            "Porcentaje promedio de uso de BW"
        )
        content_layout.addWidget(self.bw_utilization_card, 1, 1)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab
    
    def _create_bandwidth_tab(self):
        """Crear pestaña de ancho de banda por servicio"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Tabla de distribución por clase de servicio
        service_label = QLabel("📊 Distribución de Ancho de Banda por Clase de Servicio")
        service_label.setFont(QFont("Arial", 12, QFont.Bold))
        content_layout.addWidget(service_label)
        
        self.service_table = QTableWidget()
        self.service_table.setObjectName("ServiceTable")
        self.service_table.setColumnCount(6)
        self.service_table.setHorizontalHeaderLabels([
            "Clase de Servicio",
            "BW Asignado (Mbps)",
            "% Total",
            "Paquetes",
            "Latencia Prom.",
            "Prioridad"
        ])
        header = self.service_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.service_table.setAlternatingRowColors(True)
        self.service_table.setRowCount(5)
        
        # Definir clases de servicio
        service_classes = [
            ("Highest", "🔴 Crítico"),
            ("High", "🟠 Alto"),
            ("Medium", "🟡 Medio"),
            ("Low", "🟢 Bajo"),
            ("Lowest", "🔵 Best Effort")
        ]
        
        for row, (service_class, display_name) in enumerate(service_classes):
            item = QTableWidgetItem(display_name)
            item.setTextAlignment(Qt.AlignCenter)
            self.service_table.setItem(row, 0, item)
        
        content_layout.addWidget(self.service_table)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab
    
    def set_theme(self, dark_mode):
        """Aplicar tema al dashboard y todos sus componentes"""
        self.dark_theme = dark_mode
        
        if dark_mode:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()
    
    def _apply_dark_theme(self):
        """Aplicar tema oscuro al dashboard"""
        # Estilos para QTabWidget
        tab_style = """
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #555555;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2b2b2b;
                color: #ffffff;
                border-bottom: 2px solid #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #4a4a4a;
            }
        """
        
        # Estilos para tablas
        table_style = """
            QTableWidget {
                background-color: #2b2b2b;
                alternate-background-color: #353535;
                color: #e0e0e0;
                gridline-color: #555555;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                padding: 5px;
                color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: #e0e0e0;
                padding: 5px;
                border: 1px solid #555555;
                font-weight: bold;
            }
        """
        
        # Aplicar estilos a tabs
        self.tabs.setStyleSheet(tab_style)
        
        # Aplicar estilos a todas las tablas
        if hasattr(self, 'onu_table'):
            self.onu_table.setStyleSheet(table_style)
        if hasattr(self, 'sla_table'):
            self.sla_table.setStyleSheet(table_style)
        if hasattr(self, 'service_table'):
            self.service_table.setStyleSheet(table_style)
    
    def _apply_light_theme(self):
        """Aplicar tema claro al dashboard"""
        # Estilos para QTabWidget
        tab_style = """
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #000000;
                border-bottom: 2px solid #4CAF50;
            }
            QTabBar::tab:hover {
                background-color: #e0e0e0;
            }
        """
        
        # Estilos para tablas
        table_style = """
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f5f5f5;
                color: #333333;
                gridline-color: #cccccc;
                border: 1px solid #cccccc;
            }
            QTableWidget::item {
                padding: 5px;
                color: #333333;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                color: #333333;
                padding: 5px;
                border: 1px solid #cccccc;
                font-weight: bold;
            }
        """
        
        # Aplicar estilos a tabs
        self.tabs.setStyleSheet(tab_style)
        
        # Aplicar estilos a todas las tablas
        if hasattr(self, 'onu_table'):
            self.onu_table.setStyleSheet(table_style)
        if hasattr(self, 'sla_table'):
            self.sla_table.setStyleSheet(table_style)
        if hasattr(self, 'service_table'):
            self.service_table.setStyleSheet(table_style)
    
    def update_metrics(self, sdn_metrics: dict):
        """Actualizar todas las métricas avanzadas del dashboard"""
        if not sdn_metrics:
            return
            
        global_metrics = sdn_metrics.get('global_metrics', {})
        onu_metrics = sdn_metrics.get('onu_metrics', {})
        controller_metrics = sdn_metrics.get('controller_metrics', {})
        service_metrics = sdn_metrics.get('service_metrics', {})
        sla_metrics = sdn_metrics.get('sla_metrics', {})
        
        # ===== PESTAÑA GLOBAL =====
        self.reconfig_card.update_value(str(global_metrics.get('reconfigurations', 0)))
        self.grant_util_card.update_value(f"{global_metrics.get('grant_utilization', 0):.1f}%")
        self.fairness_card.update_value(f"{global_metrics.get('fairness_index', 0):.3f}")
        self.qos_card.update_value(str(global_metrics.get('qos_violations', 0)))
        
        # Eficiencia espectral
        spectral_eff = global_metrics.get('spectral_efficiency', 0)
        self.spectral_eff_card.update_value(f"{spectral_eff:.2f} bits/Hz")
        
        # Total de decisiones
        total_decisions = controller_metrics.get('total_decisions', 0)
        self.total_decisions_card.update_value(str(total_decisions))
        
        # Actualizar gráfica de fairness con histórico real
        if HAS_QTCHART and 'fairness_history' in global_metrics:
            fairness_history = global_metrics['fairness_history']
            self.fairness_series.clear()
            
            for i, fairness_value in enumerate(fairness_history):
                self.fairness_series.append(i, fairness_value)
        
        # ===== PESTAÑA ONU =====
        self.onu_table.setRowCount(len(onu_metrics))
        
        for row, (onu_id, metrics) in enumerate(onu_metrics.items()):
            # ONU ID
            onu_id_item = QTableWidgetItem(onu_id)
            onu_id_item.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 0, onu_id_item)
            
            # Latencia promedio
            latency = QTableWidgetItem(f"{metrics.get('avg_latency', 0)*1000:.2f} ms")
            latency.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 1, latency)
            
            # Jitter
            jitter = QTableWidgetItem(f"{metrics.get('avg_jitter', 0)*1000:.2f} ms")
            jitter.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 2, jitter)
            
            # Tasa de pérdida de paquetes
            loss = QTableWidgetItem(f"{metrics.get('packet_loss_rate', 0):.1f}%")
            loss.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 3, loss)
            
            # Throughput
            throughput = QTableWidgetItem(f"{metrics.get('avg_throughput', 0):.1f} Mbps")
            throughput.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 4, throughput)
            
            # Eficiencia de grants
            efficiency = QTableWidgetItem(f"{metrics.get('grant_efficiency', 0):.1f}%")
            efficiency.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 5, efficiency)
            
            # Nivel de congestión
            congestion = metrics.get('congestion_level', 0)
            congestion_item = QTableWidgetItem(f"{congestion*100:.1f}%")
            congestion_item.setTextAlignment(Qt.AlignCenter)
            
            # Colorear según nivel de congestión
            if congestion > 0.8:
                congestion_item.setBackground(QColor(255, 100, 100))  # Rojo
            elif congestion > 0.5:
                congestion_item.setBackground(QColor(255, 200, 100))  # Naranja
            else:
                congestion_item.setBackground(QColor(100, 255, 100))  # Verde
            
            self.onu_table.setItem(row, 6, congestion_item)
        
        # ===== PESTAÑA QoS Y SLA =====
        if sla_metrics:
            # Contar filas necesarias
            total_rows = sum(len(tconts) for tconts in sla_metrics.values())
            self.sla_table.setRowCount(total_rows)
            
            current_row = 0
            for onu_id, tconts in sla_metrics.items():
                for tcont, compliance in tconts.items():
                    # ONU ID
                    onu_item = QTableWidgetItem(onu_id)
                    onu_item.setTextAlignment(Qt.AlignCenter)
                    self.sla_table.setItem(current_row, 0, onu_item)
                    
                    # T-CONT
                    tcont_item = QTableWidgetItem(tcont)
                    tcont_item.setTextAlignment(Qt.AlignCenter)
                    self.sla_table.setItem(current_row, 1, tcont_item)
                    
                    # Cumplidos
                    met = QTableWidgetItem(str(compliance.get('met', 0)))
                    met.setTextAlignment(Qt.AlignCenter)
                    self.sla_table.setItem(current_row, 2, met)
                    
                    # Violados
                    violated = QTableWidgetItem(str(compliance.get('violated', 0)))
                    violated.setTextAlignment(Qt.AlignCenter)
                    self.sla_table.setItem(current_row, 3, violated)
                    
                    # % Cumplimiento
                    total = compliance.get('met', 0) + compliance.get('violated', 0)
                    percentage = (compliance.get('met', 0) / total * 100) if total > 0 else 0
                    percent_item = QTableWidgetItem(f"{percentage:.1f}%")
                    percent_item.setTextAlignment(Qt.AlignCenter)
                    
                    # Colorear según cumplimiento
                    if percentage >= 95:
                        percent_item.setBackground(QColor(100, 255, 100))  # Verde
                    elif percentage >= 80:
                        percent_item.setBackground(QColor(255, 200, 100))  # Naranja
                    else:
                        percent_item.setBackground(QColor(255, 100, 100))  # Rojo
                    
                    self.sla_table.setItem(current_row, 4, percent_item)
                    current_row += 1
        
        # ===== PESTAÑA CONTROLADOR =====
        # Tiempo de respuesta del controlador
        controller_response = controller_metrics.get('avg_controller_response_time', 0)
        self.controller_response_card.update_value(f"{controller_response*1000:.2f} ms")
        
        # Latencia de decisión
        decision_latency = controller_metrics.get('avg_decision_latency', 0)
        self.decision_latency_card.update_value(f"{decision_latency*1000:.2f} ms")
        
        # Tasa de reasignación
        reassignment = controller_metrics.get('reassignment_rate', 0)
        self.reassignment_rate_card.update_value(str(reassignment))
        
        # Utilización de ancho de banda
        bw_util = controller_metrics.get('avg_bandwidth_utilization', 0)
        self.bw_utilization_card.update_value(f"{bw_util:.1f}%")
        
        # ===== PESTAÑA ANCHO DE BANDA =====
        if service_metrics:
            service_classes = ['highest', 'high', 'medium', 'low', 'lowest']
            priorities = ['1 (Máxima)', '2', '3', '4', '5 (Mínima)']
            
            total_bw = sum(service_metrics.values())
            
            for row, (service_class, priority) in enumerate(zip(service_classes, priorities)):
                bw_assigned = service_metrics.get(service_class, 0)
                percentage = (bw_assigned / total_bw * 100) if total_bw > 0 else 0
                
                # BW Asignado
                bw_item = QTableWidgetItem(f"{bw_assigned:.2f}")
                bw_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 1, bw_item)
                
                # % Total
                percent_item = QTableWidgetItem(f"{percentage:.1f}%")
                percent_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 2, percent_item)
                
                # Paquetes (placeholder - se puede agregar después)
                packets_item = QTableWidgetItem("N/A")
                packets_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 3, packets_item)
                
                # Latencia Prom. (placeholder - se puede agregar después)
                latency_item = QTableWidgetItem("N/A")
                latency_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 4, latency_item)
                
                # Prioridad
                priority_item = QTableWidgetItem(priority)
                priority_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 5, priority_item)
    
    def load_latest_simulation(self):
        """Cargar datos desde el último archivo de simulación guardado"""
        try:
            from pathlib import Path
            from core.pon.sdn_metrics_processor import SDNMetricsProcessor
            import os
            
            print("🔍 Buscando archivo de simulación más reciente...")
            
            # Buscar en la carpeta simulation_results
            sim_results_path = Path.cwd() / "simulation_results"
            
            if not sim_results_path.exists():
                print("❌ No se encontró la carpeta simulation_results")
                self._show_error_message("No se encontró la carpeta 'simulation_results'.\nEjecuta una simulación primero.")
                return
            
            # Buscar todos los archivos datos_simulacion.json
            json_files = list(sim_results_path.rglob("datos_simulacion.json"))
            
            if not json_files:
                print("❌ No se encontraron archivos de simulación")
                self._show_error_message("No se encontraron archivos de simulación.\nEjecuta una simulación primero.")
                return
            
            # Obtener el archivo más reciente
            latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
            
            print(f"📂 Archivo encontrado: {latest_file.parent.name}/{latest_file.name}")
            print(f"📍 Ruta completa: {latest_file}")
            
            # Crear procesador de métricas SDN
            processor = SDNMetricsProcessor()
            
            # Cargar datos de simulación
            print("⏳ Cargando datos de simulación...")
            if not processor.load_simulation_data(str(latest_file)):
                print("❌ Error: El archivo no contiene datos de simulación válidos")
                self._show_error_message("El archivo de simulación no contiene datos válidos.")
                return
            
            print("⚙️ Calculando métricas SDN desde datos reales...")
            print("   - Analizando transmission_log...")
            print("   - Calculando métricas por ONU...")
            print("   - Calculando compliance SLA...")
            print("   - Calculando métricas del controlador...")
            
            # Calcular métricas SDN
            sdn_metrics = processor.calculate_sdn_metrics()
            
            if not sdn_metrics:
                print("❌ Error calculando métricas SDN")
                self._show_error_message("No se pudieron calcular las métricas SDN.")
                return
            
            print("✅ Métricas SDN calculadas exitosamente desde datos reales")
            
            # Mostrar resumen
            global_metrics = sdn_metrics.get('global_metrics', {})
            onu_metrics = sdn_metrics.get('onu_metrics', {})
            
            print(f"   📈 Fairness Index: {global_metrics.get('fairness_index', 0):.3f}")
            print(f"   📊 ONUs detectadas: {len(onu_metrics)}")
            print(f"   🚀 Eficiencia Espectral: {global_metrics.get('spectral_efficiency', 0):.2f} bits/Hz")
            print(f"   📡 Grant Utilization: {global_metrics.get('grant_utilization', 0):.1f}%")
            print(f"   ⏱️ Latencia promedio: {global_metrics.get('avg_latency', 0):.2f} ms")
            
            # Actualizar el dashboard con los datos reales
            self.update_metrics(sdn_metrics)
            
            print("💡 ¡Dashboard actualizado con datos REALES de la simulación!")
            print(f"💾 Archivo procesado: {latest_file.parent.name}")
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            import traceback
            traceback.print_exc()
            self._show_error_message(f"Error al procesar el archivo:\n{str(e)}")
    
    def _show_error_message(self, message):
        """Mostrar mensaje de error al usuario"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", message)
        except:
            print(f"Error: {message}")

