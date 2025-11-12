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

# Importar sistema de traducciones
from utils.translation_manager import translation_manager
tr = translation_manager.get_text

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
        
        # Guardar los textos originales (keys de traducción) - se setean después de crear la instancia
        self.title_key = ""
        self.description_key = ""
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Título
        self.title_label = QLabel(title)
        self.title_label.setObjectName("MetricTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(16)  # Título más visible
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)  # Centrado
        self.title_label.setWordWrap(True)  # Permitir salto de línea si es necesario
        layout.addWidget(self.title_label)
        
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
            self.desc_label = QLabel(description)
            self.desc_label.setObjectName("MetricDescription")
            desc_font = QFont()
            desc_font.setPointSize(14)  # Descripción más legible
            self.desc_label.setFont(desc_font)
            self.desc_label.setAlignment(Qt.AlignCenter)
            self.desc_label.setWordWrap(True)  # Permitir salto de línea si es necesario
            layout.addWidget(self.desc_label)
        else:
            self.desc_label = None
    
    def update_value(self, new_value: str):
        """Actualizar el valor mostrado"""
        self.value_label.setText(new_value)
    
    def retranslate(self):
        """Actualizar textos traducidos"""
        if self.title_key:
            self.title_label.setText(tr(self.title_key))
        if self.desc_label and self.description_key:
            self.desc_label.setText(tr(self.description_key))

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
        self.title_label = QLabel(tr('sdn_dashboard.title'))
        self.title_label.setObjectName("DashboardTitle")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)
        
        # Botón para cargar última simulación
        test_button_layout = QHBoxLayout()
        self.test_button = QPushButton(tr('sdn_dashboard.load_simulation'))
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
        self.tabs.addTab(self.tab_global, tr('sdn_dashboard.tabs.global'))
        
        # Pestaña 2: Métricas por ONU
        self.tab_onu = self._create_onu_tab()
        self.tabs.addTab(self.tab_onu, tr('sdn_dashboard.tabs.onu_metrics'))
        
        # Pestaña 3: QoS y SLA
        self.tab_qos = self._create_qos_tab()
        self.tabs.addTab(self.tab_qos, tr('sdn_dashboard.tabs.qos_sla'))
        
        # Pestaña 4: Controlador SDN
        self.tab_controller = self._create_controller_tab()
        self.tabs.addTab(self.tab_controller, tr('sdn_dashboard.tabs.controller'))
        
        # Pestaña 5: Ancho de Banda
        self.tab_bandwidth = self._create_bandwidth_tab()
        self.tabs.addTab(self.tab_bandwidth, tr('sdn_dashboard.tabs.bandwidth'))
        
        # Pestaña 6: Mapa de Salud ONUs
        self.tab_health = self._create_health_map_tab()
        self.tabs.addTab(self.tab_health, tr('sdn_dashboard.health.tab_title'))
        
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
            tr("sdn_dashboard.global.reconfigurations"),
            "0",
            tr("sdn_dashboard.global.reconfigurations_desc")
        )
        self.reconfig_card.title_key = "sdn_dashboard.global.reconfigurations"
        self.reconfig_card.description_key = "sdn_dashboard.global.reconfigurations_desc"
        content_layout.addWidget(self.reconfig_card, 0, 0)
        
        self.grant_util_card = MetricCard(
            tr("sdn_dashboard.global.grant_utilization"),
            "0%",
            tr("sdn_dashboard.global.grant_utilization_desc")
        )
        self.grant_util_card.title_key = "sdn_dashboard.global.grant_utilization"
        self.grant_util_card.description_key = "sdn_dashboard.global.grant_utilization_desc"
        content_layout.addWidget(self.grant_util_card, 0, 1)
        
        self.fairness_card = MetricCard(
            tr("sdn_dashboard.global.fairness_index"),
            "0.0",
            tr("sdn_dashboard.global.fairness_desc")
        )
        self.fairness_card.title_key = "sdn_dashboard.global.fairness_index"
        self.fairness_card.description_key = "sdn_dashboard.global.fairness_desc"
        content_layout.addWidget(self.fairness_card, 1, 0)
        
        self.qos_card = MetricCard(
            tr("sdn_dashboard.global.qos_violations"),
            "0",
            tr("sdn_dashboard.global.qos_violations_desc")
        )
        self.qos_card.title_key = "sdn_dashboard.global.qos_violations"
        self.qos_card.description_key = "sdn_dashboard.global.qos_violations_desc"
        content_layout.addWidget(self.qos_card, 1, 1)
        
        self.spectral_eff_card = MetricCard(
            tr("sdn_dashboard.global.spectral_efficiency"),
            "0.0 bits/Hz",
            tr("sdn_dashboard.global.spectral_efficiency_desc")
        )
        self.spectral_eff_card.title_key = "sdn_dashboard.global.spectral_efficiency"
        self.spectral_eff_card.description_key = "sdn_dashboard.global.spectral_efficiency_desc"
        content_layout.addWidget(self.spectral_eff_card, 2, 0)
        
        self.total_decisions_card = MetricCard(
            tr("sdn_dashboard.global.total_decisions"),
            "0",
            tr("sdn_dashboard.global.total_decisions_desc")
        )
        self.total_decisions_card.title_key = "sdn_dashboard.global.total_decisions"
        self.total_decisions_card.description_key = "sdn_dashboard.global.total_decisions_desc"
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
        
        # Título
        self.onu_title_label = QLabel(tr('sdn_dashboard.onu.title'))
        self.onu_title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.onu_title_label)
        
        # Tabla de métricas por ONU
        self.onu_table = QTableWidget()
        self.onu_table.setObjectName("ONUMetricsTable")
        self.onu_table.setColumnCount(6)
        self.onu_table.setHorizontalHeaderLabels([
            tr('sdn_dashboard.onu.table_headers.onu_id'),
            tr('sdn_dashboard.onu.table_headers.avg_bw'),
            tr('sdn_dashboard.onu.table_headers.peak_bw'),
            tr('sdn_dashboard.onu.table_headers.latency'),
            tr('sdn_dashboard.onu.table_headers.jitter'),
            tr('sdn_dashboard.onu.table_headers.packet_loss')
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
        self.sla_label = QLabel(tr('sdn_dashboard.qos.title'))
        self.sla_label.setFont(QFont("Arial", 12, QFont.Bold))
        content_layout.addWidget(self.sla_label)
        
        self.sla_table = QTableWidget()
        self.sla_table.setObjectName("SLATable")
        self.sla_table.setColumnCount(5)
        self.sla_table.setHorizontalHeaderLabels([
            tr('sdn_dashboard.qos.table_headers.onu_id'),
            tr('sdn_dashboard.qos.table_headers.tcont'),
            tr('sdn_dashboard.qos.table_headers.met'),
            tr('sdn_dashboard.qos.table_headers.violated'),
            tr('sdn_dashboard.qos.table_headers.compliance')
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
            tr("sdn_dashboard.controller.response_time"),
            "0.0 ms",
            tr("sdn_dashboard.controller.response_time_desc")
        )
        self.controller_response_card.title_key = "sdn_dashboard.controller.response_time"
        self.controller_response_card.description_key = "sdn_dashboard.controller.response_time_desc"
        content_layout.addWidget(self.controller_response_card, 0, 0)
        
        self.decision_latency_card = MetricCard(
            tr("sdn_dashboard.controller.decision_latency"),
            "0.0 ms",
            tr("sdn_dashboard.controller.decision_latency_desc")
        )
        self.decision_latency_card.title_key = "sdn_dashboard.controller.decision_latency"
        self.decision_latency_card.description_key = "sdn_dashboard.controller.decision_latency_desc"
        content_layout.addWidget(self.decision_latency_card, 0, 1)
        
        self.reassignment_rate_card = MetricCard(
            tr("sdn_dashboard.controller.reassignment_rate"),
            "0",
            tr("sdn_dashboard.controller.reassignment_rate_desc")
        )
        self.reassignment_rate_card.title_key = "sdn_dashboard.controller.reassignment_rate"
        self.reassignment_rate_card.description_key = "sdn_dashboard.controller.reassignment_rate_desc"
        content_layout.addWidget(self.reassignment_rate_card, 1, 0)
        
        self.bw_utilization_card = MetricCard(
            tr("sdn_dashboard.controller.bw_utilization"),
            "0.0%",
            tr("sdn_dashboard.controller.bw_utilization_desc")
        )
        self.bw_utilization_card.title_key = "sdn_dashboard.controller.bw_utilization"
        self.bw_utilization_card.description_key = "sdn_dashboard.controller.bw_utilization_desc"
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
        self.service_label = QLabel(tr('sdn_dashboard.bandwidth.title'))
        self.service_label.setFont(QFont("Arial", 12, QFont.Bold))
        content_layout.addWidget(self.service_label)
        
        self.service_table = QTableWidget()
        self.service_table.setObjectName("ServiceTable")
        self.service_table.setColumnCount(6)
        self.service_table.setHorizontalHeaderLabels([
            tr('sdn_dashboard.bandwidth.table_headers.service_class'),
            tr('sdn_dashboard.bandwidth.table_headers.assigned_bw'),
            tr('sdn_dashboard.bandwidth.table_headers.total_percent'),
            tr('sdn_dashboard.bandwidth.table_headers.packets'),
            tr('sdn_dashboard.bandwidth.table_headers.avg_latency'),
            tr('sdn_dashboard.bandwidth.table_headers.priority')
        ])
        header = self.service_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.service_table.setAlternatingRowColors(True)
        self.service_table.setRowCount(5)
        
        # Definir clases de servicio (guardadas para retranslate)
        self.service_classes_keys = [
            "sdn_dashboard.bandwidth.service_classes.critical",
            "sdn_dashboard.bandwidth.service_classes.high",
            "sdn_dashboard.bandwidth.service_classes.medium",
            "sdn_dashboard.bandwidth.service_classes.low",
            "sdn_dashboard.bandwidth.service_classes.best_effort"
        ]
        
        for row, service_key in enumerate(self.service_classes_keys):
            item = QTableWidgetItem(tr(service_key))
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
        self.health_title_label = QLabel(tr('sdn_dashboard.health.title'))
        self.health_title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.health_title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.health_title_label)
        
        # Descripción
        self.health_desc_label = QLabel(tr('sdn_dashboard.health.description'))
        self.health_desc_label.setFont(QFont("Arial", 9))
        self.health_desc_label.setAlignment(Qt.AlignCenter)
        self.health_desc_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        content_layout.addWidget(self.health_desc_label)
        
        # Tabla principal de salud de ONUs
        self.health_table = QTableWidget()
        self.health_table.setObjectName("HealthTable")
        self.health_table.setColumnCount(7)
        self.health_table.setHorizontalHeaderLabels([
            tr('sdn_dashboard.health.table_headers.onu_id'),
            tr('sdn_dashboard.health.table_headers.status'),
            tr('sdn_dashboard.health.table_headers.health_score'),
            tr('sdn_dashboard.health.table_headers.latency'),
            tr('sdn_dashboard.health.table_headers.jitter'),
            tr('sdn_dashboard.health.table_headers.packet_loss'),
            tr('sdn_dashboard.health.table_headers.recommendations')
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
        self.breakdown_label = QLabel(tr('sdn_dashboard.health.breakdown_title'))
        self.breakdown_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.breakdown_label.setStyleSheet("margin-top: 20px;")
        content_layout.addWidget(self.breakdown_label)
        
        # Tabla de desglose de componentes
        self.component_table = QTableWidget()
        self.component_table.setObjectName("ComponentTable")
        self.component_table.setColumnCount(5)
        self.component_table.setHorizontalHeaderLabels([
            tr('sdn_dashboard.health.table_headers.onu_id'),
            tr('sdn_dashboard.health.table_headers.latency_score'),
            tr('sdn_dashboard.health.table_headers.jitter_score'),
            tr('sdn_dashboard.health.table_headers.packet_loss_score'),
            tr('sdn_dashboard.health.table_headers.congestion_score')
        ])
        header2 = self.component_table.horizontalHeader()
        header2.setSectionResizeMode(QHeaderView.Stretch)
        self.component_table.setAlternatingRowColors(True)
        self.component_table.verticalHeader().setVisible(False)
        
        content_layout.addWidget(self.component_table)
        
        # Leyenda de estados
        self.legend_label = QLabel(tr('sdn_dashboard.health.legend_title'))
        self.legend_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.legend_label.setStyleSheet("margin-top: 20px;")
        content_layout.addWidget(self.legend_label)
        
        legend_layout = QHBoxLayout()
        legend_layout.addStretch()
        
        # Guardar las leyendas para retranslate
        self.legend_items = []
        legend_keys = ['excellent', 'good', 'regular', 'critical']
        legend_colors = ["#4CAF50", "#FFC107", "#FF9800", "#F44336"]
        
        for key, color in zip(legend_keys, legend_colors):
            label_text = f"{tr(f'sdn_dashboard.health.status_labels.{key}')}: {tr(f'sdn_dashboard.health.status_ranges.{key}')}"
            legend_item = QLabel(label_text)
            legend_item.setStyleSheet(f"background-color: {color}; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;")
            legend_layout.addWidget(legend_item)
            self.legend_items.append((legend_item, key))
        
        legend_layout.addStretch()
        content_layout.addLayout(legend_layout)
        
        content_layout.addStretch()
        
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
        if hasattr(self, 'health_table'):
            self.health_table.setStyleSheet(table_style)
        if hasattr(self, 'component_table'):
            self.component_table.setStyleSheet(table_style)
    
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
        if hasattr(self, 'health_table'):
            self.health_table.setStyleSheet(table_style)
        if hasattr(self, 'component_table'):
            self.component_table.setStyleSheet(table_style)
    
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
    
    def retranslate_ui(self):
        """Actualizar todos los textos traducibles del dashboard"""
        # Título principal
        self.title_label.setText(tr('sdn_dashboard.title'))
        
        # Botón de carga
        self.test_button.setText(tr('sdn_dashboard.load_simulation'))
        
        # Nombres de pestañas
        self.tabs.setTabText(0, tr('sdn_dashboard.tabs.global'))
        self.tabs.setTabText(1, tr('sdn_dashboard.tabs.onu_metrics'))
        self.tabs.setTabText(2, tr('sdn_dashboard.tabs.qos_sla'))
        self.tabs.setTabText(3, tr('sdn_dashboard.tabs.controller'))
        self.tabs.setTabText(4, tr('sdn_dashboard.tabs.bandwidth'))
        
        # Tarjetas de métricas globales
        self.reconfig_card.retranslate()
        self.grant_util_card.retranslate()
        self.fairness_card.retranslate()
        self.qos_card.retranslate()
        self.spectral_eff_card.retranslate()
        self.total_decisions_card.retranslate()
        
        # Tabla ONU
        if hasattr(self, 'onu_title_label'):
            self.onu_title_label.setText(tr('sdn_dashboard.onu.title'))
        self.onu_table.setHorizontalHeaderLabels([
            tr('sdn_dashboard.onu.table_headers.onu_id'),
            tr('sdn_dashboard.onu.table_headers.avg_bw'),
            tr('sdn_dashboard.onu.table_headers.peak_bw'),
            tr('sdn_dashboard.onu.table_headers.latency'),
            tr('sdn_dashboard.onu.table_headers.jitter'),
            tr('sdn_dashboard.onu.table_headers.packet_loss')
        ])
        
        # Tabla QoS
        if hasattr(self, 'sla_label'):
            self.sla_label.setText(tr('sdn_dashboard.qos.title'))
        self.sla_table.setHorizontalHeaderLabels([
            tr('sdn_dashboard.qos.table_headers.onu_id'),
            tr('sdn_dashboard.qos.table_headers.tcont'),
            tr('sdn_dashboard.qos.table_headers.met'),
            tr('sdn_dashboard.qos.table_headers.violated'),
            tr('sdn_dashboard.qos.table_headers.compliance')
        ])
        
        # Tarjetas del controlador
        self.controller_response_card.retranslate()
        self.decision_latency_card.retranslate()
        self.reassignment_rate_card.retranslate()
        self.bw_utilization_card.retranslate()
        
        # Tabla Bandwidth
        if hasattr(self, 'service_label'):
            self.service_label.setText(tr('sdn_dashboard.bandwidth.title'))
        self.service_table.setHorizontalHeaderLabels([
            tr('sdn_dashboard.bandwidth.table_headers.service_class'),
            tr('sdn_dashboard.bandwidth.table_headers.assigned_bw'),
            tr('sdn_dashboard.bandwidth.table_headers.total_percent'),
            tr('sdn_dashboard.bandwidth.table_headers.packets'),
            tr('sdn_dashboard.bandwidth.table_headers.avg_latency'),
            tr('sdn_dashboard.bandwidth.table_headers.priority')
        ])
        
        # Actualizar clases de servicio en la tabla
        if hasattr(self, 'service_classes_keys'):
            for row, service_key in enumerate(self.service_classes_keys):
                item = self.service_table.item(row, 0)
                if item:
                    item.setText(tr(service_key))
        
        # Pestaña de Salud
        self.tabs.setTabText(5, tr('sdn_dashboard.health.tab_title'))
        
        if hasattr(self, 'health_title_label'):
            self.health_title_label.setText(tr('sdn_dashboard.health.title'))
        if hasattr(self, 'health_desc_label'):
            self.health_desc_label.setText(tr('sdn_dashboard.health.description'))
        if hasattr(self, 'breakdown_label'):
            self.breakdown_label.setText(tr('sdn_dashboard.health.breakdown_title'))
        if hasattr(self, 'legend_label'):
            self.legend_label.setText(tr('sdn_dashboard.health.legend_title'))
        
        # Tablas de salud
        if hasattr(self, 'health_table'):
            self.health_table.setHorizontalHeaderLabels([
                tr('sdn_dashboard.health.table_headers.onu_id'),
                tr('sdn_dashboard.health.table_headers.status'),
                tr('sdn_dashboard.health.table_headers.health_score'),
                tr('sdn_dashboard.health.table_headers.latency'),
                tr('sdn_dashboard.health.table_headers.jitter'),
                tr('sdn_dashboard.health.table_headers.packet_loss'),
                tr('sdn_dashboard.health.table_headers.recommendations')
            ])
        
        if hasattr(self, 'component_table'):
            self.component_table.setHorizontalHeaderLabels([
                tr('sdn_dashboard.health.table_headers.onu_id'),
                tr('sdn_dashboard.health.table_headers.latency_score'),
                tr('sdn_dashboard.health.table_headers.jitter_score'),
                tr('sdn_dashboard.health.table_headers.packet_loss_score'),
                tr('sdn_dashboard.health.table_headers.congestion_score')
            ])
        
        # Actualizar leyendas
        if hasattr(self, 'legend_items'):
            for legend_item, key in self.legend_items:
                label_text = f"{tr(f'sdn_dashboard.health.status_labels.{key}')}: {tr(f'sdn_dashboard.health.status_ranges.{key}')}"
                legend_item.setText(label_text)
    
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
            
            # Buscar archivos datos_simulacion.json y datos_simulacion.json.gz
            json_files = list(sim_results_path.rglob("datos_simulacion.json"))
            json_gz_files = list(sim_results_path.rglob("datos_simulacion.json.gz"))
            all_files = json_files + json_gz_files

            if not all_files:
                print("❌ No se encontraron archivos de simulación")
                self._show_error_message("No se encontraron archivos de simulación.\nEjecuta una simulación primero.")
                return

            # Obtener el archivo más reciente (puede ser .json o .json.gz)
            latest_file = max(all_files, key=lambda p: p.stat().st_mtime)
            
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

