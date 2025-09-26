"""
PON SDN Dashboard
Panel para mostrar métricas y estadísticas del controlador SDN
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QScrollArea, QFrame, QProgressBar, QGridLayout,
                           QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import typing

# Importar PyQtChart con manejo de error
try:
    from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
    HAS_QTCHART = True
except ImportError:
    HAS_QTCHART = False
    print("Warning: PyQtChart no está instalado. La gráfica de fairness no estará disponible.")

class MetricCard(QFrame):
    """Widget para mostrar una métrica individual con título y valor"""
    
    def __init__(self, title: str, value: str, description: str = "", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Título
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Valor
        self.value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(16)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        
        # Descripción
        if description:
            desc_label = QLabel(description)
            desc_font = QFont()
            desc_font.setPointSize(8)
            desc_label.setFont(desc_font)
            desc_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(desc_label)
    
    def update_value(self, new_value: str):
        """Actualizar el valor mostrado"""
        self.value_label.setText(new_value)

class PONSDNDashboard(QWidget):
    """Panel para mostrar métricas y estadísticas del controlador SDN"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar la interfaz del dashboard"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Título del dashboard
        title_label = QLabel("📊 Dashboard SDN")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Área con scroll para métricas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget contenedor para métricas
        metrics_widget = QWidget()
        metrics_layout = QGridLayout(metrics_widget)
        
        # Métricas globales del controlador
        self.reconfig_card = MetricCard(
            "Reconfiguraciones",
            "0",
            "Número de ajustes automáticos"
        )
        metrics_layout.addWidget(self.reconfig_card, 0, 0)
        
        self.grant_util_card = MetricCard(
            "Utilización de Grants",
            "0%",
            "Porcentaje de grants utilizados"
        )
        metrics_layout.addWidget(self.grant_util_card, 0, 1)
        
        self.fairness_card = MetricCard(
            "Índice de Fairness",
            "0.0",
            "Índice de Jain (0-1)"
        )
        metrics_layout.addWidget(self.fairness_card, 1, 0)
        
        self.qos_card = MetricCard(
            "Violaciones QoS",
            "0",
            "Número de violaciones detectadas"
        )
        metrics_layout.addWidget(self.qos_card, 1, 1)
        
        # Tabla de métricas por ONU
        self.onu_table = QTableWidget()
        self.onu_table.setColumnCount(4)
        self.onu_table.setHorizontalHeaderLabels([
            "ONU ID",
            "Latencia Prom.",
            "Pérdida Paquetes",
            "Throughput"
        ])
        header = self.onu_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        metrics_layout.addWidget(self.onu_table, 2, 0, 1, 2)
        
        # Gráfica de fairness histórico (si PyQtChart está disponible)
        if HAS_QTCHART:
            self.fairness_chart = QChart()
            self.fairness_chart.setTitle("Histórico de Fairness")
            self.fairness_series = QLineSeries()
            self.fairness_chart.addSeries(self.fairness_series)
            
            # Configurar ejes
            axis_x = QValueAxis()
            axis_x.setTitleText("Tiempo")
            axis_y = QValueAxis()
            axis_y.setTitleText("Fairness")
            axis_y.setRange(0, 1)
            
            self.fairness_chart.setAxisX(axis_x, self.fairness_series)
            self.fairness_chart.setAxisY(axis_y, self.fairness_series)
            
            chart_view = QChartView(self.fairness_chart)
            metrics_layout.addWidget(chart_view, 3, 0, 1, 2)
        else:
            # Si PyQtChart no está disponible, mostrar un mensaje
            chart_placeholder = QLabel("Gráfica de fairness no disponible\n(Requiere PyQtChart)")
            chart_placeholder.setAlignment(Qt.AlignCenter)
            chart_placeholder.setStyleSheet("background-color: #f0f0f0; padding: 20px;")
            metrics_layout.addWidget(chart_placeholder, 3, 0, 1, 2)
        
        scroll_area.setWidget(metrics_widget)
        main_layout.addWidget(scroll_area)
    
    def update_metrics(self, sdn_metrics: dict):
        """Actualizar todas las métricas del dashboard"""
        global_metrics = sdn_metrics.get('global_metrics', {})
        
        # Actualizar métricas globales
        self.reconfig_card.update_value(str(global_metrics.get('total_reconfigurations', 0)))
        self.grant_util_card.update_value(f"{global_metrics.get('grant_utilization', 0):.1f}%")
        self.fairness_card.update_value(f"{global_metrics.get('current_fairness', 0):.3f}")
        self.qos_card.update_value(str(global_metrics.get('qos_violations', 0)))
        
        # Actualizar tabla de ONUs
        onu_metrics = sdn_metrics.get('onu_metrics', {})
        self.onu_table.setRowCount(len(onu_metrics))
        
        for row, (onu_id, metrics) in enumerate(onu_metrics.items()):
            # ONU ID
            self.onu_table.setItem(row, 0, QTableWidgetItem(onu_id))
            
            # Latencia promedio
            latency = QTableWidgetItem(f"{metrics.get('avg_latency', 0):.3f} ms")
            latency.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 1, latency)
            
            # Tasa de pérdida de paquetes
            loss = QTableWidgetItem(f"{metrics.get('packet_loss_rate', 0):.1f}%")
            loss.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 2, loss)
            
            # Throughput
            throughput = QTableWidgetItem(f"{metrics.get('avg_throughput', 0):.1f} Mbps")
            throughput.setTextAlignment(Qt.AlignCenter)
            self.onu_table.setItem(row, 3, throughput)
        
        # Actualizar gráfica de fairness si está disponible
        if HAS_QTCHART and 'current_fairness' in global_metrics:
            self.fairness_series.append(
                len(self.fairness_series),
                global_metrics['current_fairness']
            )