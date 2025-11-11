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
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Título
        title_label = QLabel(title)
        title_label.setObjectName("MetricTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Valor
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        value_font = QFont()
        value_font.setPointSize(16)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Descripción
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("MetricDescription")
            desc_font = QFont()
            desc_font.setPointSize(8)
            desc_label.setFont(desc_font)
            desc_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(desc_label)
    
    def update_value(self, new_value: str):
        """Actualizar el valor mostrado"""
        self.value_label.setText(new_value)

class PONSDNDashboard(QWidget):
    """Panel para mostrar métricas y estadísticas avanzadas del controlador SDN"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PONSDNDashboard")
        self.setup_ui()
        
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
        
        # Pestaña 6: Mapa de Salud ONUs
        self.tab_health = self._create_health_map_tab()
        self.tabs.addTab(self.tab_health, "🏥 Mapa de Salud ONUs")
        
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
    
    def _create_health_map_tab(self):
        """Crear pestaña de mapa de salud de ONUs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Título de la sección
        title_label = QLabel("🏥 Mapa de Salud de ONUs PON")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        
        # Descripción
        desc_label = QLabel("Estado de salud calculado en base a: Latencia (30%), Jitter (20%), Pérdidas (25%), Congestión (25%)")
        desc_label.setFont(QFont("Arial", 9))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        content_layout.addWidget(desc_label)
        
        # Tabla principal de salud de ONUs
        self.health_table = QTableWidget()
        self.health_table.setObjectName("HealthTable")
        self.health_table.setColumnCount(7)
        self.health_table.setHorizontalHeaderLabels([
            "ONU ID",
            "Estado",
            "Score Salud",
            "Latencia",
            "Jitter",
            "Pérdidas",
            "Recomendaciones"
        ])
        header = self.health_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        self.health_table.setAlternatingRowColors(True)
        self.health_table.verticalHeader().setVisible(False)
        
        content_layout.addWidget(self.health_table)
        
        # Sección de desglose de scores por componente
        breakdown_label = QLabel("📊 Desglose de Scores por Componente")
        breakdown_label.setFont(QFont("Arial", 12, QFont.Bold))
        breakdown_label.setStyleSheet("margin-top: 20px;")
        content_layout.addWidget(breakdown_label)
        
        # Tabla de desglose de componentes
        self.component_table = QTableWidget()
        self.component_table.setObjectName("ComponentTable")
        self.component_table.setColumnCount(5)
        self.component_table.setHorizontalHeaderLabels([
            "ONU ID",
            "Score Latencia",
            "Score Jitter",
            "Score Pérdidas",
            "Score Congestión"
        ])
        header2 = self.component_table.horizontalHeader()
        header2.setSectionResizeMode(QHeaderView.Stretch)
        self.component_table.setAlternatingRowColors(True)
        self.component_table.verticalHeader().setVisible(False)
        
        content_layout.addWidget(self.component_table)
        
        # Leyenda de estados
        legend_label = QLabel("📌 Leyenda de Estados")
        legend_label.setFont(QFont("Arial", 12, QFont.Bold))
        legend_label.setStyleSheet("margin-top: 20px;")
        content_layout.addWidget(legend_label)
        
        legend_layout = QHBoxLayout()
        legend_layout.addStretch()
        
        legends = [
            ("🟢 Excelente", "Score ≥ 80", "#4CAF50"),
            ("🟡 Bueno", "Score 60-79", "#FFC107"),
            ("🟠 Regular", "Score 40-59", "#FF9800"),
            ("🔴 Crítico", "Score < 40", "#F44336")
        ]
        
        for emoji_status, range_text, color in legends:
            legend_item = QLabel(f"{emoji_status}: {range_text}")
            legend_item.setStyleSheet(f"background-color: {color}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;")
            legend_layout.addWidget(legend_item)
        
        legend_layout.addStretch()
        content_layout.addLayout(legend_layout)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        return tab
    
    def update_metrics(self, sdn_metrics: dict):
        """Actualizar todas las métricas avanzadas del dashboard"""
        if not sdn_metrics:
            return
            
        global_metrics = sdn_metrics.get('global_metrics', {})
        onu_metrics = sdn_metrics.get('onu_metrics', {})
        controller_metrics = sdn_metrics.get('controller_metrics', {})
        service_metrics = sdn_metrics.get('service_metrics', {})
        sla_metrics = sdn_metrics.get('sla_metrics', {})
        health_map = sdn_metrics.get('health_map', {})
        
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
                    met = QTableWidgetItem(str(compliance.get('packets_met', 0)))
                    met.setTextAlignment(Qt.AlignCenter)
                    self.sla_table.setItem(current_row, 2, met)
                    
                    # Violados
                    violated = QTableWidgetItem(str(compliance.get('packets_violated', 0)))
                    violated.setTextAlignment(Qt.AlignCenter)
                    self.sla_table.setItem(current_row, 3, violated)
                    
                    # % Cumplimiento
                    percentage = compliance.get('compliance', 0)
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
            
            # Calcular total de ancho de banda
            total_bw = sum(
                service_metrics.get(sc, {}).get('bandwidth', 0) 
                for sc in service_classes
            )
            
            for row, (service_class, priority) in enumerate(zip(service_classes, priorities)):
                service_data = service_metrics.get(service_class, {})
                
                # Extraer datos
                bw_assigned = service_data.get('bandwidth', 0) if isinstance(service_data, dict) else service_data
                packets = service_data.get('packets', 0) if isinstance(service_data, dict) else 0
                avg_latency = service_data.get('avg_latency', 0) if isinstance(service_data, dict) else 0
                
                percentage = (bw_assigned / total_bw * 100) if total_bw > 0 else 0
                
                # BW Asignado
                bw_item = QTableWidgetItem(f"{bw_assigned:.2f}")
                bw_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 1, bw_item)
                
                # % Total
                percent_item = QTableWidgetItem(f"{percentage:.1f}%")
                percent_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 2, percent_item)
                
                # Paquetes - ahora con valores reales
                packets_item = QTableWidgetItem(str(packets))
                packets_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 3, packets_item)
                
                # Latencia Promedio - ahora con valores reales (en ms)
                latency_item = QTableWidgetItem(f"{avg_latency * 1000:.2f} ms" if avg_latency > 0 else "0.00 ms")
                latency_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 4, latency_item)
                
                # Prioridad
                priority_item = QTableWidgetItem(priority)
                priority_item.setTextAlignment(Qt.AlignCenter)
                self.service_table.setItem(row, 5, priority_item)
    
        # ===== PESTAÑA MAPA DE SALUD ONUs =====
        try:
            if health_map:
                onu_ids = list(health_map.keys())
                self.health_table.setRowCount(len(onu_ids))
                self.component_table.setRowCount(len(onu_ids))

                for row, onu_id in enumerate(onu_ids):
                    entry = health_map.get(onu_id, {})

                    # Health table columns: ONU ID, Estado, Score Salud, Latencia, Jitter, Pérdidas, Recomendaciones
                    onu_item = QTableWidgetItem(str(onu_id))
                    onu_item.setTextAlignment(Qt.AlignCenter)
                    self.health_table.setItem(row, 0, onu_item)

                    status_text = f"{entry.get('emoji', '')} {entry.get('status', '')}"
                    status_item = QTableWidgetItem(status_text)
                    status_item.setTextAlignment(Qt.AlignCenter)
                    self.health_table.setItem(row, 1, status_item)

                    score_item = QTableWidgetItem(f"{entry.get('score', 0):.1f}")
                    score_item.setTextAlignment(Qt.AlignCenter)
                    # Color background según score
                    score_val = entry.get('score', 0)
                    if score_val >= 80:
                        score_item.setBackground(QColor('#4CAF50'))
                    elif score_val >= 60:
                        score_item.setBackground(QColor('#FFC107'))
                    elif score_val >= 40:
                        score_item.setBackground(QColor('#FF9800'))
                    else:
                        score_item.setBackground(QColor('#F44336'))
                    self.health_table.setItem(row, 2, score_item)

                    metrics = entry.get('metrics', {})
                    latency_item = QTableWidgetItem(f"{metrics.get('latency_ms', 0):.3f} ms")
                    latency_item.setTextAlignment(Qt.AlignCenter)
                    self.health_table.setItem(row, 3, latency_item)

                    jitter_item = QTableWidgetItem(f"{metrics.get('jitter_ms', 0):.3f} ms")
                    jitter_item.setTextAlignment(Qt.AlignCenter)
                    self.health_table.setItem(row, 4, jitter_item)

                    loss_item = QTableWidgetItem(f"{metrics.get('packet_loss_pct', 0):.2f}%")
                    loss_item.setTextAlignment(Qt.AlignCenter)
                    self.health_table.setItem(row, 5, loss_item)

                    recs = entry.get('recommendations', [])
                    recs_text = ", ".join(recs)
                    rec_item = QTableWidgetItem(recs_text)
                    rec_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    self.health_table.setItem(row, 6, rec_item)

                    # Component breakdown table
                    comp = entry.get('component_scores', {})
                    comp_onu_item = QTableWidgetItem(str(onu_id))
                    comp_onu_item.setTextAlignment(Qt.AlignCenter)
                    self.component_table.setItem(row, 0, comp_onu_item)

                    lat_score_item = QTableWidgetItem(f"{comp.get('latency', 0):.1f}")
                    lat_score_item.setTextAlignment(Qt.AlignCenter)
                    self.component_table.setItem(row, 1, lat_score_item)

                    jit_score_item = QTableWidgetItem(f"{comp.get('jitter', 0):.1f}")
                    jit_score_item.setTextAlignment(Qt.AlignCenter)
                    self.component_table.setItem(row, 2, jit_score_item)

                    loss_score_item = QTableWidgetItem(f"{comp.get('packet_loss', 0):.1f}")
                    loss_score_item.setTextAlignment(Qt.AlignCenter)
                    self.component_table.setItem(row, 3, loss_score_item)

                    cong_score_item = QTableWidgetItem(f"{comp.get('congestion', 0):.1f}")
                    cong_score_item.setTextAlignment(Qt.AlignCenter)
                    self.component_table.setItem(row, 4, cong_score_item)
        except Exception as e:
            print(f"❌ Error actualizando Mapa de Salud ONUs: {e}")
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

