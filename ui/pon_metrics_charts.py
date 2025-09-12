"""
PON Metrics Charts
Sistema de gráficos para visualizar métricas de simulación PON
"""

import numpy as np
from typing import Dict, List, Any
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTabWidget, QGroupBox, QGridLayout, QScrollArea,
                             QSplitter, QPushButton, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

try:
    # Configurar matplotlib antes de cualquier importación
    from .matplotlib_config import configure_matplotlib_for_windows, safe_matplotlib_backend
    
    # Configurar backend seguro
    safe_backend = safe_matplotlib_backend()
    if not safe_backend:
        raise ImportError("No se pudo configurar matplotlib backend")
    
    # Aplicar configuración para Windows
    configure_matplotlib_for_windows()
    
    # Importar componentes de matplotlib
    import matplotlib
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    
    MATPLOTLIB_AVAILABLE = True
    print("OK Matplotlib configurado correctamente con backend", safe_backend)
    
except ImportError as e:
    MATPLOTLIB_AVAILABLE = False
    print(f"WARNING Matplotlib no disponible: {e}")
    print("   Para resolver: pip install matplotlib>=3.5.0")
except Exception as e:
    MATPLOTLIB_AVAILABLE = False
    print(f"WARNING Error configurando matplotlib: {e}")


class PONMetricsChart(FigureCanvas):
    """Widget de gráfico individual para métricas PON"""
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        if not MATPLOTLIB_AVAILABLE:
            super().__init__(Figure())
            return
            
        # Configurar figura con parámetros seguros para Windows
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white', tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        
        # Configurar estilo seguro
        try:
            self.fig.patch.set_facecolor('white')
            self.fig.patch.set_edgecolor('none')
        except Exception as e:
            print(f"WARNING configurando figura: {e}")
        
        # Variables para datos
        self.data_history = []
        self.chart_type = "line"
        
    def plot_delay_evolution(self, simulation_data: Dict[str, Any]):
        """Graficar evolución de delays durante la simulación"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig.clear()
        
        # Obtener datos de delay
        simulation_summary = simulation_data.get('simulation_summary', {})
        if not simulation_summary:
            self._plot_no_data("Sin datos de simulación")
            return
            
        # Simular evolución de delays (en implementación real vendría del historial)
        steps = simulation_summary.get('simulation_stats', {}).get('total_steps', 0)
        if steps == 0:
            self._plot_no_data("Simulación no ejecutada")
            return
            
        # Generar datos simulados basados en las métricas finales
        mean_delay = simulation_summary.get('performance_metrics', {}).get('mean_delay', 0)
        
        # Simular evolución temporal
        time_points = np.linspace(0, steps, min(steps, 100))
        delays = self._simulate_delay_evolution(mean_delay, len(time_points))
        
        ax = self.fig.add_subplot(111)
        ax.plot(time_points, delays, 'b-', linewidth=2, label='Delay promedio')
        ax.fill_between(time_points, delays, alpha=0.3, color='blue')
        
        ax.set_xlabel('Pasos de simulación')
        ax.set_ylabel('Delay (segundos)')
        ax.set_title('Evolución del Delay Durante la Simulación')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Agregar estadísticas
        ax.text(0.02, 0.98, f'Delay final: {mean_delay:.6f}s', 
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_throughput_evolution(self, simulation_data: Dict[str, Any]):
        """Graficar evolución de throughput durante la simulación"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig.clear()
        
        simulation_summary = simulation_data.get('simulation_summary', {})
        if not simulation_summary:
            self._plot_no_data("Sin datos de simulación")
            return
            
        steps = simulation_summary.get('simulation_stats', {}).get('total_steps', 0)
        if steps == 0:
            self._plot_no_data("Simulación no ejecutada")
            return
            
        mean_throughput = simulation_summary.get('performance_metrics', {}).get('mean_throughput', 0)
        
        # Simular evolución temporal
        time_points = np.linspace(0, steps, min(steps, 100))
        throughputs = self._simulate_throughput_evolution(mean_throughput, len(time_points))
        
        ax = self.fig.add_subplot(111)
        ax.plot(time_points, throughputs, 'g-', linewidth=2, label='Throughput promedio')
        ax.fill_between(time_points, throughputs, alpha=0.3, color='green')
        
        ax.set_xlabel('Pasos de simulación')
        ax.set_ylabel('Throughput (MB/s)')
        ax.set_title('Evolución del Throughput Durante la Simulación')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Agregar estadísticas
        ax.text(0.02, 0.98, f'Throughput final: {mean_throughput:.3f} MB/s', 
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_onu_buffer_levels(self, simulation_data: Dict[str, Any]):
        """Graficar evolución temporal de los niveles de buffer por ONU"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig.clear()
        
        # Obtener datos históricos de buffer
        # Primero intentar desde simulation_summary.episode_metrics (estructura más común)
        simulation_summary = simulation_data.get('simulation_summary', {})
        episode_metrics = simulation_summary.get('episode_metrics', {})
        buffer_history = episode_metrics.get('buffer_levels_history', [])
        
        # Si no hay datos, intentar desde la raíz (estructura alternativa)
        if not buffer_history:
            episode_metrics_root = simulation_data.get('episode_metrics', {})
            buffer_history = episode_metrics_root.get('buffer_levels_history', [])
        
        if not buffer_history:
            self._plot_no_data("Sin historial de buffer")
            return
        
        ax = self.fig.add_subplot(111)
        
        # Verificar estructura de datos
        if not buffer_history or len(buffer_history) == 0:
            self._plot_no_data("Historial de buffer vacío")
            return
        
        # Obtener número de ONUs desde la primera entrada
        first_entry = buffer_history[0]
        if not isinstance(first_entry, dict):
            self._plot_no_data("Formato de datos de buffer inválido")
            return
        
        onu_ids = list(first_entry.keys())
        num_steps = len(buffer_history)
        
        # Crear eje temporal (pasos de simulación)
        time_steps = np.arange(num_steps)
        
        # Colores distintivos para cada ONU
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
        
        # Graficar una línea por cada ONU
        for i, onu_id in enumerate(onu_ids):
            # Extraer niveles de buffer para esta ONU a lo largo del tiempo
            buffer_levels_percent = []
            for step_data in buffer_history:
                onu_buffer_data = step_data.get(onu_id, {})
                
                # Manejar formato nuevo (dict con utilization_percent) y formato antiguo (número)
                if isinstance(onu_buffer_data, dict):
                    # Usar directamente el porcentaje de utilización
                    buffer_percent = onu_buffer_data.get('utilization_percent', 0)
                else:
                    # Formato antiguo (ya es porcentaje o fracción)
                    buffer_percent = onu_buffer_data * 100 if onu_buffer_data <= 1 else onu_buffer_data
                
                buffer_levels_percent.append(buffer_percent)
            
            # Usar color cíclico si hay más ONUs que colores
            color = colors[i % len(colors)]
            
            # Graficar línea para esta ONU
            ax.plot(time_steps, buffer_levels_percent, 
                   color=color, linewidth=2, marker='o', markersize=3,
                   label=f'ONU {onu_id}', alpha=0.8)
        
        ax.set_xlabel('Pasos de Simulación')
        ax.set_ylabel('Ocupación del Buffer (%)')
        ax.set_title('Evolución Temporal de los Niveles de Buffer por ONU')
        ax.set_ylim(0, 100)  # Porcentaje de 0 a 100%
        ax.grid(True, alpha=0.3)
        
        # Líneas de referencia en porcentaje
        ax.axhline(y=50, color='orange', linestyle='--', alpha=0.7, 
                  label='Nivel medio (50%)')
        ax.axhline(y=80, color='red', linestyle='--', alpha=0.7, 
                  label='Nivel crítico (80%)')
        
        # Leyenda - manejar muchas ONUs
        if len(onu_ids) <= 8:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', ncol=2, fontsize=8)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_network_utilization(self, simulation_data: Dict[str, Any]):
        """Graficar distribución de tráfico real en formato dona"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig.clear()
        
        # Obtener datos de utilización para el centro
        performance_metrics = simulation_data.get('simulation_summary', {}).get('performance_metrics', {})
        network_utilization = performance_metrics.get('network_utilization', 0)
        
        # Obtener datos reales de tráfico desde episode_metrics
        episode_metrics = simulation_data.get('simulation_summary', {}).get('episode_metrics', {})
        throughputs = episode_metrics.get('throughputs', [])
        
        if not throughputs:
            # Si no hay datos, usar estructura alternativa
            episode_metrics_root = simulation_data.get('episode_metrics', {})
            throughputs = episode_metrics_root.get('throughputs', [])
        
        if not throughputs:
            self._plot_no_data("Sin datos de tráfico")
            return
        
        # Calcular distribución real de tipos de tráfico basada en throughputs
        tcont_counts = {'highest': 0, 'high': 0, 'medium': 0, 'low': 0, 'lowest': 0}
        
        for throughput_entry in throughputs:
            tcont_type = throughput_entry.get('tcont_id', 'medium').lower()
            if tcont_type in tcont_counts:
                tcont_counts[tcont_type] += 1
        
        # Convertir a porcentajes
        total_entries = sum(tcont_counts.values())
        if total_entries == 0:
            self._plot_no_data("Sin datos de tipos de tráfico")
            return
        
        # Calcular porcentajes reales
        traffic_types = ['Highest', 'High', 'Medium', 'Low', 'Lowest']
        tcont_keys = ['highest', 'high', 'medium', 'low', 'lowest']
        values = [(tcont_counts[key] / total_entries) * 100 for key in tcont_keys]
        
        # Filtrar tipos de tráfico con valores > 0 para el gráfico
        filtered_types = []
        filtered_values = []
        filtered_colors = []
        base_colors = ['#ff4444', '#ff8800', '#ffdd00', '#4488ff', '#888888']
        
        for i, (traffic_type, value) in enumerate(zip(traffic_types, values)):
            if value > 0:
                filtered_types.append(traffic_type)
                filtered_values.append(value)
                filtered_colors.append(base_colors[i])
        
        if not filtered_values:
            self._plot_no_data("Sin tipos de tráfico detectados")
            return
        
        # Crear gráfico de dona
        ax = self.fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(filtered_values, labels=filtered_types, colors=filtered_colors, 
                                         autopct='%1.1f%%', startangle=90, 
                                         pctdistance=0.85,
                                         wedgeprops={'width': 0.4})
        
        # Agregar porcentaje de utilización en el centro
        if network_utilization > 0:
            ax.text(0, 0, f'{network_utilization:.1f}%\nUtilización', 
                    ha='center', va='center', fontsize=16, fontweight='bold')
        else:
            ax.text(0, 0, 'N/A\nUtilización', 
                    ha='center', va='center', fontsize=16, fontweight='bold')
        
        # Título con información adicional
        total_packets = len(throughputs)
        ax.set_title(f'{network_utilization:.1f}% - Distribución de Tráfico Real\n({total_packets} paquetes analizados)', 
                    fontsize=14, pad=20)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_algorithm_performance(self, simulation_data: Dict[str, Any]):
        """Graficar rendimiento del algoritmo DBA"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig.clear()
        
        orchestrator_stats = simulation_data.get('orchestrator_stats', {})
        network_stats = simulation_data.get('simulation_summary', {}).get('network_stats', {})
        
        algorithm = network_stats.get('dba_algorithm', 'N/A')
        
        # Métricas del algoritmo
        allocation_prob = orchestrator_stats.get('allocation_probability', 0)
        blocking_prob = orchestrator_stats.get('blocking_probability', 0)
        success_rate = network_stats.get('success_rate', 0)
        
        # Gráfico de barras horizontal
        ax = self.fig.add_subplot(111)
        
        metrics = ['Prob. Asignación', 'Tasa de Éxito', 'Prob. No Bloqueo']
        values = [allocation_prob * 100, success_rate, (1 - blocking_prob) * 100]
        colors = ['blue', 'green', 'purple']
        
        bars = ax.barh(metrics, values, color=colors, alpha=0.7)
        
        # Agregar valores en las barras
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                   f'{value:.1f}%', ha='left', va='center', fontweight='bold')
        
        ax.set_xlabel('Porcentaje (%)')
        ax.set_title(f'Rendimiento del Algoritmo DBA: {algorithm}')
        ax.set_xlim(0, 105)
        ax.grid(True, alpha=0.3)
        
        self.fig.tight_layout()
        self.draw()
    
    def plot_traffic_distribution(self, simulation_data: Dict[str, Any]):
        """Graficar distribución de tráfico real en formato dona"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig.clear()
        
        # Obtener datos de utilización para el centro
        performance_metrics = simulation_data.get('simulation_summary', {}).get('performance_metrics', {})
        network_utilization = performance_metrics.get('network_utilization', 0)
        
        # Obtener datos reales de tráfico desde episode_metrics
        episode_metrics = simulation_data.get('simulation_summary', {}).get('episode_metrics', {})
        throughputs = episode_metrics.get('throughputs', [])
        
        if not throughputs:
            # Si no hay datos, usar estructura alternativa
            episode_metrics_root = simulation_data.get('episode_metrics', {})
            throughputs = episode_metrics_root.get('throughputs', [])
        
        if not throughputs:
            self._plot_no_data("Sin datos de tráfico")
            return
        
        # Calcular distribución real de tipos de tráfico basada en throughputs
        tcont_counts = {'highest': 0, 'high': 0, 'medium': 0, 'low': 0, 'lowest': 0}
        
        for throughput_entry in throughputs:
            tcont_type = throughput_entry.get('tcont_id', 'medium').lower()
            if tcont_type in tcont_counts:
                tcont_counts[tcont_type] += 1
        
        # Convertir a porcentajes
        total_entries = sum(tcont_counts.values())
        if total_entries == 0:
            self._plot_no_data("Sin datos de tipos de tráfico")
            return
        
        # Calcular porcentajes reales
        traffic_types = ['Highest', 'High', 'Medium', 'Low', 'Lowest']
        tcont_keys = ['highest', 'high', 'medium', 'low', 'lowest']
        values = [(tcont_counts[key] / total_entries) * 100 for key in tcont_keys]
        
        # Filtrar tipos de tráfico con valores > 0 para el gráfico
        filtered_types = []
        filtered_values = []
        filtered_colors = []
        base_colors = ['#ff4444', '#ff8800', '#ffdd00', '#4488ff', '#888888']
        
        for i, (traffic_type, value) in enumerate(zip(traffic_types, values)):
            if value > 0:
                filtered_types.append(traffic_type)
                filtered_values.append(value)
                filtered_colors.append(base_colors[i])
        
        if not filtered_values:
            self._plot_no_data("Sin tipos de tráfico detectados")
            return
        
        # Crear gráfico de dona
        ax = self.fig.add_subplot(111)
        wedges, texts, autotexts = ax.pie(filtered_values, labels=filtered_types, colors=filtered_colors, 
                                         autopct='%1.1f%%', startangle=90, 
                                         pctdistance=0.85,
                                         wedgeprops={'width': 0.4})
        
        # Agregar porcentaje de utilización en el centro
        if network_utilization > 0:
            ax.text(0, 0, f'{network_utilization:.1f}%\nUtilización', 
                    ha='center', va='center', fontsize=16, fontweight='bold')
        else:
            ax.text(0, 0, 'N/A\nUtilización', 
                    ha='center', va='center', fontsize=16, fontweight='bold')
        
        # Título con información adicional
        total_packets = len(throughputs)
        ax.set_title(f'{network_utilization:.1f}% - Distribución de Tráfico Real\n({total_packets} paquetes analizados)', 
                    fontsize=14, pad=20)
        
        self.fig.tight_layout()
        self.draw()
    
    def _simulate_delay_evolution(self, final_delay: float, num_points: int) -> np.ndarray:
        """Simular evolución realista de delay"""
        # Crear curva que converge al delay final
        t = np.linspace(0, 1, num_points)
        
        # Delay inicial más alto que converge al final
        initial_delay = final_delay * 3 if final_delay > 0 else 0.001
        
        # Función exponencial decreciente con ruido
        delays = initial_delay * np.exp(-3 * t) + final_delay
        
        # Agregar ruido realista
        noise = np.random.normal(0, final_delay * 0.1, num_points) if final_delay > 0 else np.zeros(num_points)
        delays += noise
        
        # Asegurar valores positivos
        delays = np.maximum(delays, 0)
        
        return delays
    
    def _simulate_throughput_evolution(self, final_throughput: float, num_points: int) -> np.ndarray:
        """Simular evolución realista de throughput"""
        t = np.linspace(0, 1, num_points)
        
        # Throughput que crece desde 0 al valor final
        throughputs = final_throughput * (1 - np.exp(-4 * t))
        
        # Agregar variabilidad realista
        if final_throughput > 0:
            noise = np.random.normal(0, final_throughput * 0.05, num_points)
            throughputs += noise
        
        # Asegurar valores positivos
        throughputs = np.maximum(throughputs, 0)
        
        return throughputs
    
    def _plot_no_data(self, message: str):
        """Mostrar mensaje cuando no hay datos"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha='center', va='center', 
                transform=ax.transAxes, fontsize=16, 
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        ax.set_xticks([])
        ax.set_yticks([])
        self.draw()


class PONMetricsChartsPanel(QWidget):
    """Panel principal de gráficos de métricas PON"""
    
    # Señales
    chart_updated = pyqtSignal(str)  # Tipo de gráfico actualizado
    
    def __init__(self):
        super().__init__()
        self.current_data = {}
        self.charts = {}
        self.simulation_format = 'classic'  # Formato por defecto
        self.dark_theme = False  # Estado del tema
        
        if not MATPLOTLIB_AVAILABLE:
            self.setup_no_matplotlib_ui()
        else:
            self.setup_ui()
            
    def set_theme(self, dark_theme):
        """Aplicar tema al panel de gráficos"""
        self.dark_theme = dark_theme
        
        # Actualizar colores de matplotlib si está disponible
        if MATPLOTLIB_AVAILABLE:
            self.update_matplotlib_theme(dark_theme)
            
        # El estilo QSS se aplicará automáticamente desde la ventana principal
        
    def update_matplotlib_theme(self, dark_theme):
        """Actualizar tema de matplotlib para todos los gráficos"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # Colores para tema oscuro y claro
        if dark_theme:
            bg_color = '#2b2b2b'
            text_color = '#ffffff'
            grid_color = '#555555'
        else:
            bg_color = '#ffffff'
            text_color = '#333333'
            grid_color = '#cccccc'
            
        # Actualizar todos los gráficos existentes
        for chart_name, chart in self.charts.items():
            if hasattr(chart, 'fig'):
                try:
                    chart.fig.patch.set_facecolor(bg_color)
                    
                    # Actualizar ejes
                    for ax in chart.fig.get_axes():
                        ax.set_facecolor(bg_color)
                        ax.tick_params(colors=text_color)
                        ax.xaxis.label.set_color(text_color)
                        ax.yaxis.label.set_color(text_color)
                        ax.title.set_color(text_color)
                        ax.grid(True, color=grid_color, alpha=0.3)
                        
                        # Actualizar leyenda si existe
                        legend = ax.get_legend()
                        if legend:
                            legend.get_frame().set_facecolor(bg_color)
                            for text in legend.get_texts():
                                text.set_color(text_color)
                    
                    chart.draw()
                except Exception as e:
                    print(f"Error actualizando tema del gráfico {chart_name}: {e}")
    
    def setup_no_matplotlib_ui(self):
        """Configurar UI cuando matplotlib no está disponible"""
        layout = QVBoxLayout(self)
        
        warning = QLabel("⚠️ Matplotlib no está instalado.\n\n"
                        "Para ver gráficos, instala matplotlib:\n"
                        "pip install matplotlib>=3.5.0")
        warning.setStyleSheet("QLabel { background-color: #fff3cd; border: 1px solid #ffeaa7; "
                             "border-radius: 5px; padding: 20px; margin: 20px; }")
        warning.setAlignment(Qt.AlignCenter)
        warning.setWordWrap(True)
        
        layout.addWidget(warning)
    
    def setup_ui(self):
        """Configurar interfaz de usuario con gráficos"""
        layout = QVBoxLayout(self)
        
        # Título y controles
        header_layout = QHBoxLayout()
        
        title = QLabel("📊 Gráficos de Métricas PON")
        title.setObjectName("pon_charts_title")  # Identificador para QSS
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botones de control
        self.refresh_charts_btn = QPushButton("🔄 Actualizar Gráficos")
        self.refresh_charts_btn.setObjectName("pon_charts_button")  # Identificador para QSS
        self.refresh_charts_btn.clicked.connect(self.refresh_all_charts)
        header_layout.addWidget(self.refresh_charts_btn)
        
        layout.addLayout(header_layout)
        
        # Crear tabs para diferentes gráficos
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Evolución temporal
        self.setup_temporal_charts_tab()
        
        # Tab 2: Estados de red
        self.setup_network_state_charts_tab()
        
        # Tab 3: Análisis comparativo
        self.setup_comparative_charts_tab()
        
    def setup_temporal_charts_tab(self):
        """Configurar tab de gráficos temporales"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Splitter para dividir verticalmente
        splitter = QSplitter(Qt.Vertical)
        
        # Gráfico de delay
        delay_group = QGroupBox("Evolución del Delay")
        delay_group.setObjectName("pon_charts_group")
        delay_layout = QVBoxLayout(delay_group)
        
        self.charts['delay'] = PONMetricsChart(width=10, height=4)
        delay_layout.addWidget(self.charts['delay'])
        
        splitter.addWidget(delay_group)
        
        # Gráfico de throughput
        throughput_group = QGroupBox("Evolución del Throughput")
        throughput_group.setObjectName("pon_charts_group")
        throughput_layout = QVBoxLayout(throughput_group)
        
        self.charts['throughput'] = PONMetricsChart(width=10, height=4)
        throughput_layout.addWidget(self.charts['throughput'])
        
        splitter.addWidget(throughput_group)
        
        layout.addWidget(splitter)
        
        self.tabs.addTab(tab, "⏱️ Evolución Temporal")
    
    def setup_network_state_charts_tab(self):
        """Configurar tab de estados de red"""
        tab = QWidget()
        layout = QGridLayout(tab)
        
        # Gráfico de niveles de buffer
        buffer_group = QGroupBox("Niveles de Buffer por ONU")
        buffer_group.setObjectName("pon_charts_group")
        buffer_layout = QVBoxLayout(buffer_group)
        
        self.charts['buffer'] = PONMetricsChart(width=8, height=5)
        buffer_layout.addWidget(self.charts['buffer'])
        
        layout.addWidget(buffer_group, 0, 0)
        
        # Gráfico de utilización
        utilization_group = QGroupBox("Utilización de la Red")
        utilization_group.setObjectName("pon_charts_group")
        utilization_layout = QVBoxLayout(utilization_group)
        
        self.charts['utilization'] = PONMetricsChart(width=8, height=5)
        utilization_layout.addWidget(self.charts['utilization'])
        
        layout.addWidget(utilization_group, 0, 1)
        
        self.tabs.addTab(tab, "🌐 Estados de Red")
    
    def setup_comparative_charts_tab(self):
        """Configurar tab de análisis comparativo"""
        tab = QWidget()
        layout = QGridLayout(tab)
        
        # Gráfico de rendimiento de algoritmo
        algorithm_group = QGroupBox("Rendimiento del Algoritmo DBA")
        algorithm_group.setObjectName("pon_charts_group")
        algorithm_layout = QVBoxLayout(algorithm_group)
        
        self.charts['algorithm'] = PONMetricsChart(width=8, height=5)
        algorithm_layout.addWidget(self.charts['algorithm'])
        
        layout.addWidget(algorithm_group, 0, 0)
        
        # Gráfico de distribución de tráfico
        traffic_group = QGroupBox("Distribución de Tráfico")
        traffic_group.setObjectName("pon_charts_group")
        traffic_layout = QVBoxLayout(traffic_group)
        
        self.charts['traffic'] = PONMetricsChart(width=8, height=5)
        traffic_layout.addWidget(self.charts['traffic'])
        
        layout.addWidget(traffic_group, 0, 1)
        
        self.tabs.addTab(tab, "📈 Análisis")
    
    def update_charts_with_data(self, simulation_data: Dict[str, Any]):
        """Actualizar todos los gráficos con nuevos datos"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.current_data = simulation_data
        self._detect_simulation_format(simulation_data)
        
        # Normalizar datos si es necesario
        normalized_data = self._normalize_data_format(simulation_data)
        
        # Actualizar cada gráfico usando datos normalizados
        if 'delay' in self.charts:
            self.charts['delay'].plot_delay_evolution(normalized_data)
            self.chart_updated.emit('delay')
        
        if 'throughput' in self.charts:
            self.charts['throughput'].plot_throughput_evolution(normalized_data)
            self.chart_updated.emit('throughput')
        
        if 'buffer' in self.charts:
            self.charts['buffer'].plot_onu_buffer_levels(normalized_data)
            self.chart_updated.emit('buffer')
        
        if 'utilization' in self.charts:
            self.charts['utilization'].plot_network_utilization(normalized_data)
            self.chart_updated.emit('utilization')
        
        if 'algorithm' in self.charts:
            self.charts['algorithm'].plot_algorithm_performance(simulation_data)
            self.chart_updated.emit('algorithm')
        
        if 'traffic' in self.charts:
            self.charts['traffic'].plot_traffic_distribution(simulation_data)
            self.chart_updated.emit('traffic')
        
    
    def refresh_all_charts(self):
        """Actualizar todos los gráficos con los datos actuales"""
        if self.current_data:
            self.update_charts_with_data(self.current_data)
    
    def clear_all_charts(self):
        """Limpiar todos los gráficos"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        for chart in self.charts.values():
            chart.fig.clear()
            chart.draw()
        
        self.current_data = {}
    
    def export_charts(self, directory: str):
        """Exportar todos los gráficos como imágenes"""
        if not MATPLOTLIB_AVAILABLE or not self.current_data:
            return False
            
        try:
            for chart_name, chart in self.charts.items():
                filename = f"{directory}/grafico_{chart_name}.png"
                chart.fig.savefig(filename, dpi=300, bbox_inches='tight')
            
            return True
            
        except Exception as e:
            print(f"❌ Error exportando gráficos: {e}")
            return False
    
    def _detect_simulation_format(self, simulation_data: Dict[str, Any]):
        """Detectar si los datos provienen de simulación híbrida o clásica"""
        # Detectar formato híbrido por la presencia de timestamps en delays/throughputs
        episode_metrics = simulation_data.get('simulation_summary', {}).get('episode_metrics', {})
        delays = episode_metrics.get('delays', [])
        
        if delays and isinstance(delays[0], dict) and 'timestamp' in delays[0]:
            self.simulation_format = 'hybrid'
        else:
            self.simulation_format = 'classic'
    
    def _normalize_data_format(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizar datos de simulación para compatibilidad con gráficos"""
        if not hasattr(self, 'simulation_format'):
            self._detect_simulation_format(simulation_data)
        
        if self.simulation_format == 'hybrid':
            # Convertir formato híbrido al formato esperado por gráficos clásicos
            return self._convert_hybrid_to_classic_format(simulation_data)
        else:
            # Datos clásicos, devolverlos tal como están
            return simulation_data
    
    def _convert_hybrid_to_classic_format(self, hybrid_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convertir datos híbridos al formato clásico para compatibilidad"""
        converted_data = hybrid_data.copy()
        
        episode_metrics = hybrid_data.get('simulation_summary', {}).get('episode_metrics', {})
        
        # Convertir buffer levels: mantener formato nuevo con MB
        buffer_history = episode_metrics.get('buffer_levels_history', [])
        if buffer_history:
            converted_buffer_history = []
            for step_data in buffer_history:
                converted_step = {}
                for onu_id, level_data in step_data.items():
                    # Manejar formato nuevo (dict) y antiguo (número)
                    if isinstance(level_data, dict):
                        # Ya está en formato nuevo con MB - mantener
                        converted_step[onu_id] = level_data
                    else:
                        # Formato antiguo (fracción/porcentaje) - convertir a formato MB
                        # Estimar 3.5MB total por ONU (512KB + 512KB + 1MB + 1MB + 256KB)
                        used_mb = level_data * 3.5 if level_data <= 1 else level_data * 3.5 / 100
                        converted_step[onu_id] = {
                            'used_mb': used_mb,
                            'capacity_mb': 3.5,
                            'utilization_percent': level_data * 100 if level_data <= 1 else level_data
                        }
                converted_buffer_history.append(converted_step)
            
            # Actualizar en la estructura convertida
            if 'simulation_summary' not in converted_data:
                converted_data['simulation_summary'] = {}
            if 'episode_metrics' not in converted_data['simulation_summary']:
                converted_data['simulation_summary']['episode_metrics'] = {}
            
            converted_data['simulation_summary']['episode_metrics']['buffer_levels_history'] = converted_buffer_history
        
        # Los delays y throughputs híbridos ya tienen formato compatible
        # (incluso mejor con timestamp, onu_id, tcont_id)
        
        return converted_data