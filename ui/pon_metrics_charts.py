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

        simulation_stats = simulation_summary.get('simulation_stats', {})
        episode_metrics = simulation_summary.get('episode_metrics', {})
        performance_metrics = simulation_summary.get('performance_metrics', {})

        # Obtener duración real y delay history
        simulation_duration = simulation_stats.get('simulation_duration', simulation_stats.get('simulation_time', 10))
        delay_history = episode_metrics.get('delay_history', [])
        mean_delay = performance_metrics.get('mean_delay', 0)

        if not delay_history and mean_delay == 0:
            self._plot_no_data("Sin datos de delay disponibles")
            return

        # Usar datos reales si están disponibles
        if delay_history:
            time_points = np.array([d['time'] for d in delay_history])
            delays = np.array([d['value'] / 1000 for d in delay_history])  # Convertir ms a segundos
        else:
            # Fallback: generar evolución simulada con duración correcta
            print(f"[ADVERTENCIA] No hay delay_history, usando datos sintéticos")
            time_points = np.linspace(0, simulation_duration, 100)
            delays = self._simulate_delay_evolution(mean_delay, len(time_points))

        ax = self.fig.add_subplot(111)
        ax.plot(time_points, delays, 'b-', linewidth=2, label='Delay promedio')
        ax.fill_between(time_points, delays, alpha=0.3, color='blue')

        ax.set_xlabel('Tiempo (s)')
        ax.set_ylabel('Delay (segundos)')
        ax.set_title(f'Evolución del Delay Durante la Simulación ({simulation_duration:.1f}s)')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Agregar estadísticas
        final_delay = delays[-1] if len(delays) > 0 else mean_delay
        ax.text(0.02, 0.98, f'Delay final: {final_delay:.6f}s',
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

        simulation_stats = simulation_summary.get('simulation_stats', {})
        episode_metrics = simulation_summary.get('episode_metrics', {})
        performance_metrics = simulation_summary.get('performance_metrics', {})

        # Obtener duración real y throughput history
        simulation_duration = simulation_stats.get('simulation_duration', simulation_stats.get('simulation_time', 10))
        throughput_history = episode_metrics.get('throughput_history', [])
        mean_throughput = performance_metrics.get('mean_throughput', 0)

        if not throughput_history and mean_throughput == 0:
            self._plot_no_data("Sin datos de throughput disponibles")
            return

        # Usar datos reales si están disponibles
        if throughput_history:
            time_points = np.array([d['time'] for d in throughput_history])
            throughputs = np.array([d['value'] for d in throughput_history])
        else:
            # Fallback: generar evolución simulada con duración correcta
            print(f"[ADVERTENCIA] No hay throughput_history, usando datos sintéticos")
            time_points = np.linspace(0, simulation_duration, 100)
            throughputs = self._simulate_throughput_evolution(mean_throughput, len(time_points))

        ax = self.fig.add_subplot(111)
        ax.plot(time_points, throughputs, 'g-', linewidth=2, label='Throughput promedio')
        ax.fill_between(time_points, throughputs, alpha=0.3, color='green')

        ax.set_xlabel('Tiempo (s)')
        ax.set_ylabel('Throughput (MB/s)')
        ax.set_title(f'Evolución del Throughput Durante la Simulación ({simulation_duration:.1f}s)')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Agregar estadísticas
        final_throughput = throughputs[-1] if len(throughputs) > 0 else mean_throughput
        ax.text(0.02, 0.98, f'Throughput final: {final_throughput:.3f} MB/s',
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

        self.fig.tight_layout()
        self.draw()
    
    def plot_event_queue_evolution(self, simulation_data: Dict[str, Any]):
        """Graficar evolución de eventos pendientes en la cola vs tiempo"""
        if not MATPLOTLIB_AVAILABLE:
            return

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # Obtener datos
        simulation_summary = simulation_data.get('simulation_summary', {})
        episode_metrics = simulation_summary.get('episode_metrics', {})
        simulation_stats = simulation_summary.get('simulation_stats', {})

        event_queue_history = episode_metrics.get('event_queue_history', [])

        if not event_queue_history:
            self._plot_no_data("Sin historial de cola de eventos disponible")
            return

        # Extraer datos
        times = [entry['time'] for entry in event_queue_history]
        pending_events = [entry['pending_events'] for entry in event_queue_history]

        # Graficar eventos pendientes
        ax.plot(times, pending_events, 'b-', linewidth=2, label='Eventos Pendientes')
        ax.fill_between(times, pending_events, alpha=0.3, color='blue')

        # Línea de referencia del límite (1M)
        max_limit = 1000000
        ax.axhline(y=max_limit, color='r', linestyle='--', linewidth=2,
                   label=f'Límite Máximo ({max_limit:,})', alpha=0.7)

        ax.set_xlabel('Tiempo Simulado (s)')
        ax.set_ylabel('Eventos Pendientes')
        ax.set_title('Evolución de la Cola de Eventos Durante la Simulación')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Formatear eje Y con separadores de miles
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))

        # Estadísticas
        max_pending = max(pending_events) if pending_events else 0
        avg_pending = np.mean(pending_events) if pending_events else 0
        final_pending = pending_events[-1] if pending_events else 0

        # Detectar crecimiento exponencial
        growth_type = "DESCONOCIDO"
        if len(pending_events) > 10:
            # Comparar primera mitad vs segunda mitad
            mid = len(pending_events) // 2
            first_half_avg = np.mean(pending_events[:mid])
            second_half_avg = np.mean(pending_events[mid:])

            if second_half_avg > first_half_avg * 2:
                growth_type = "⚠️ EXPONENCIAL"
                color = 'red'
            elif second_half_avg > first_half_avg * 1.2:
                growth_type = "⚠️ LINEAL CRECIENTE"
                color = 'orange'
            else:
                growth_type = "✓ ESTABLE/CONSTANTE"
                color = 'green'
        else:
            color = 'black'

        stats_text = (f'Tipo: {growth_type}\n'
                     f'Máximo: {max_pending:,}\n'
                     f'Promedio: {avg_pending:,.0f}\n'
                     f'Final: {final_pending:,}')

        ax.text(0.02, 0.98, stats_text,
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', edgecolor=color, linewidth=2, alpha=0.9),
                fontsize=10, fontweight='bold')

        self.fig.tight_layout()
        self.draw()

    def plot_onu_buffer_levels(self, simulation_data: Dict[str, Any]):
        """Graficar evolución temporal de los niveles de buffer por ONU"""
        print(f"[BUFFER-LOG-GUI] plot_onu_buffer_levels() llamado")

        if not MATPLOTLIB_AVAILABLE:
            return

        self.fig.clear()

        # Obtener datos históricos de buffer
        # Primero intentar desde simulation_summary.episode_metrics (estructura más común)
        simulation_summary = simulation_data.get('simulation_summary', {})
        episode_metrics = simulation_summary.get('episode_metrics', {})
        buffer_history = episode_metrics.get('buffer_levels_history', [])
        print(f"[BUFFER-LOG-GUI] buffer_history desde episode_metrics: {len(buffer_history)} entries")

        # Si no hay datos, intentar desde la raíz (estructura alternativa)
        if not buffer_history:
            episode_metrics_root = simulation_data.get('episode_metrics', {})
            buffer_history = episode_metrics_root.get('buffer_levels_history', [])
            print(f"[BUFFER-LOG-GUI] buffer_history desde raíz: {len(buffer_history)} entries")

        if not buffer_history:
            print(f"[BUFFER-LOG-GUI] ⚠️ ERROR: Sin historial de buffer disponible!")
            self._plot_no_data("Sin historial de buffer")
            return
        else:
            print(f"[BUFFER-LOG-GUI] ✅ buffer_history tiene {len(buffer_history)} entries")
            print(f"[BUFFER-LOG-GUI] Primera entrada: {buffer_history[0]}")

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

        # Detectar formato: nuevo (con 'time' y 'buffers') vs antiguo (solo buffers)
        has_timestamps = 'time' in first_entry and 'buffers' in first_entry

        if has_timestamps:
            # Formato nuevo: {'time': t, 'buffers': {onu_id: data}}
            time_steps = np.array([entry['time'] for entry in buffer_history])
            onu_ids = list(buffer_history[0]['buffers'].keys())
        else:
            # Formato antiguo: {onu_id: data} sin timestamps
            time_steps = np.arange(len(buffer_history))
            onu_ids = list(first_entry.keys())
        
        # Colores distintivos para cada ONU
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

        # Graficar una línea por cada ONU
        for i, onu_id in enumerate(onu_ids):
            # Extraer niveles de buffer para esta ONU a lo largo del tiempo
            buffer_levels_percent = []
            for step_data in buffer_history:
                # Obtener datos de buffer según el formato
                if has_timestamps:
                    # Formato nuevo: step_data = {'time': t, 'buffers': {onu_id: data}}
                    onu_buffer_data = step_data.get('buffers', {}).get(onu_id, {})
                else:
                    # Formato antiguo: step_data = {onu_id: data}
                    onu_buffer_data = step_data.get(onu_id, {})

                # Manejar formato de datos de buffer (dict con utilization_percent o número)
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

        # Etiquetar ejes según el formato de datos
        if has_timestamps:
            ax.set_xlabel('Tiempo de Simulación (s)')
        else:
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
    
    def plot_mean_delay_evolution(self, simulation_data: Dict[str, Any]):
        """Graficar evolución del Mean Delay vs Tiempo"""
        if not MATPLOTLIB_AVAILABLE:
            return

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # Obtener datos de métricas
        simulation_stats = simulation_data.get('simulation_summary', {}).get('simulation_stats', {})
        performance_metrics = simulation_data.get('simulation_summary', {}).get('performance_metrics', {})
        episode_metrics = simulation_data.get('simulation_summary', {}).get('episode_metrics', {})

        # Obtener duración real de la simulación
        simulation_duration = simulation_stats.get('simulation_duration', simulation_stats.get('simulation_time', 10))
        mean_delay = performance_metrics.get('mean_delay', 0)
        delay_history = episode_metrics.get('delay_history', [])

        # Usar datos reales si están disponibles
        if delay_history:
            # Extraer timestamps y valores reales
            time_points = np.array([d['time'] for d in delay_history])
            delay_values = np.array([d['value'] for d in delay_history])
        elif mean_delay > 0:
            # Fallback: generar evolución simulada SOLO si no hay datos reales
            print(f"[ADVERTENCIA] No hay delay_history disponible, usando datos sintéticos")
            time_points = np.linspace(0, simulation_duration, 100)
            delay_values = self._simulate_metric_evolution(mean_delay * 1000, len(time_points), 'delay')
        else:
            # Sin datos disponibles
            time_points = np.linspace(0, simulation_duration, 10)
            delay_values = np.zeros(10)

        # Graficar
        ax.plot(time_points, delay_values, 'b-', linewidth=2, label='Mean Delay', marker='o', markersize=3)
        ax.set_xlabel('Tiempo (s)')
        ax.set_ylabel('Delay (ms)')
        ax.set_title(f'Evolución del Mean Delay vs Tiempo ({simulation_duration:.1f}s)')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Estadísticas en el gráfico
        if len(delay_values) > 0:
            avg_delay = np.mean(delay_values)
            max_delay = np.max(delay_values)
            ax.text(0.02, 0.98, f'Promedio: {avg_delay:.3f}ms\nMáximo: {max_delay:.3f}ms',
                    transform=ax.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self.fig.tight_layout()
        self.draw()

    def plot_p95_delay_evolution(self, simulation_data: Dict[str, Any]):
        """Graficar evolución del P95 Delay vs Tiempo"""
        if not MATPLOTLIB_AVAILABLE:
            return

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # Obtener datos de métricas
        simulation_stats = simulation_data.get('simulation_summary', {}).get('simulation_stats', {})
        performance_metrics = simulation_data.get('simulation_summary', {}).get('performance_metrics', {})
        episode_metrics = simulation_data.get('simulation_summary', {}).get('episode_metrics', {})

        # Obtener duración real de la simulación
        simulation_duration = simulation_stats.get('simulation_duration', simulation_stats.get('simulation_time', 10))

        # Obtener P95 delay
        p95_delay = performance_metrics.get('p95_delay', 0)
        delay_percentiles = episode_metrics.get('delay_percentiles', {})
        p95_history = delay_percentiles.get('p95', [])

        # Calcular P95 desde delay_history si está disponible
        delay_history = episode_metrics.get('delay_history', [])
        if delay_history and not p95_history:
            # Calcular P95 desde datos reales
            p95_history = self._calculate_p95_from_history(delay_history)

        if p95_history:
            # Usar datos reales con timestamps
            if isinstance(p95_history[0], dict):
                time_points = np.array([d['time'] for d in p95_history])
                p95_values = np.array([d['value'] for d in p95_history])
            else:
                time_points = np.linspace(0, simulation_duration, len(p95_history))
                p95_values = np.array(p95_history)
        elif p95_delay > 0:
            # Fallback: generar evolución simulada
            print(f"[ADVERTENCIA] No hay p95_history disponible, usando datos sintéticos")
            time_points = np.linspace(0, simulation_duration, 100)
            p95_values = self._simulate_metric_evolution(p95_delay * 1000, len(time_points), 'percentile')
        else:
            # Sin datos, usar mean_delay como aproximación
            mean_delay = performance_metrics.get('mean_delay', 0)
            time_points = np.linspace(0, simulation_duration, 100)
            # P95 típicamente es ~1.5x el mean delay
            p95_approx = mean_delay * 1.5 * 1000 if mean_delay > 0 else 0
            p95_values = self._simulate_metric_evolution(p95_approx, len(time_points), 'percentile')

        # Graficar
        ax.plot(time_points, p95_values, 'r-', linewidth=2, label='P95 Delay', marker='s', markersize=3)
        ax.set_xlabel('Tiempo (s)')
        ax.set_ylabel('Delay (ms)')
        ax.set_title(f'Evolución del P95 Delay vs Tiempo ({simulation_duration:.1f}s)')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Estadísticas en el gráfico
        if len(p95_values) > 0:
            avg_p95 = np.mean(p95_values)
            max_p95 = np.max(p95_values)
            ax.text(0.02, 0.98, f'Promedio P95: {avg_p95:.3f}ms\nMáximo P95: {max_p95:.3f}ms',
                    transform=ax.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self.fig.tight_layout()
        self.draw()

    def plot_jitter_ipdv_evolution(self, simulation_data: Dict[str, Any]):
        """Graficar evolución del Jitter IPDV Mean vs Tiempo"""
        if not MATPLOTLIB_AVAILABLE:
            return

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # Obtener datos de métricas
        simulation_stats = simulation_data.get('simulation_summary', {}).get('simulation_stats', {})
        performance_metrics = simulation_data.get('simulation_summary', {}).get('performance_metrics', {})
        episode_metrics = simulation_data.get('simulation_summary', {}).get('episode_metrics', {})

        # Obtener duración real de la simulación
        simulation_duration = simulation_stats.get('simulation_duration', simulation_stats.get('simulation_time', 10))

        # Buscar datos de jitter en diferentes ubicaciones
        jitter_mean = performance_metrics.get('jitter_ipdv_mean', 0)
        if not jitter_mean:
            jitter_mean = performance_metrics.get('jitter_mean', 0)
        if not jitter_mean:
            jitter_mean = performance_metrics.get('jitter', 0)

        jitter_history = episode_metrics.get('jitter_history', [])
        if not jitter_history:
            jitter_history = episode_metrics.get('jitter_ipdv', [])

        # Calcular jitter desde delay_history si está disponible
        delay_history = episode_metrics.get('delay_history', [])
        if delay_history and not jitter_history:
            jitter_history = self._calculate_jitter_from_delays(delay_history)

        if jitter_history:
            # Usar datos reales con timestamps
            if isinstance(jitter_history[0], dict):
                time_points = np.array([d['time'] for d in jitter_history])
                jitter_values = np.array([d['value'] for d in jitter_history])
            else:
                time_points = np.linspace(0, simulation_duration, len(jitter_history))
                jitter_values = np.array(jitter_history)
        elif jitter_mean > 0:
            # Fallback: generar evolución simulada
            print(f"[ADVERTENCIA] No hay jitter_history disponible, usando datos sintéticos")
            time_points = np.linspace(0, simulation_duration, 100)
            jitter_values = self._simulate_metric_evolution(jitter_mean * 1000, len(time_points), 'jitter')
        else:
            # Estimar jitter basado en delay si no hay datos específicos
            mean_delay = performance_metrics.get('mean_delay', 0)
            time_points = np.linspace(0, simulation_duration, 100)
            # Jitter típicamente es ~10-20% del mean delay
            jitter_approx = mean_delay * 0.15 * 1000 if mean_delay > 0 else 0
            jitter_values = self._simulate_metric_evolution(jitter_approx, len(time_points), 'jitter')

        # Graficar
        ax.plot(time_points, jitter_values, 'g-', linewidth=2, label='Jitter IPDV Mean', marker='^', markersize=3)
        ax.set_xlabel('Tiempo (s)')
        ax.set_ylabel('Jitter (ms)')
        ax.set_title(f'Evolución del Jitter IPDV Mean vs Tiempo ({simulation_duration:.1f}s)')
        ax.grid(True, alpha=0.3)
        ax.legend()

        # Estadísticas en el gráfico
        if len(jitter_values) > 0:
            avg_jitter = np.mean(jitter_values)
            max_jitter = np.max(jitter_values)
            ax.text(0.02, 0.98, f'Promedio: {avg_jitter:.3f}ms\nMáximo: {max_jitter:.3f}ms',
                    transform=ax.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        self.fig.tight_layout()
        self.draw()
    
    def plot_onu_tcont_analysis(self, simulation_data: Dict[str, Any]):
        """Graficar análisis de tipos de TCONT por ONU"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.fig.clear()
        
        # Obtener datos de delays que contienen onu_id y tcont_id
        episode_metrics = simulation_data.get('simulation_summary', {}).get('episode_metrics', {})
        delays_data = episode_metrics.get('delays', [])
        
        if not delays_data:
            # Intentar desde la raíz del objeto
            delays_data = simulation_data.get('episode_metrics', {}).get('delays', [])
        
        if not delays_data:
            self._plot_no_data("Sin datos de ONUs y TCONTs")
            return
        
        # Analizar datos para extraer ONUs y sus TCONTs
        onu_tcont_counts = {}
        
        for delay_entry in delays_data:
            onu_id = delay_entry.get('onu_id', 'unknown')
            tcont_id = delay_entry.get('tcont_id', 'unknown')
            
            if onu_id not in onu_tcont_counts:
                onu_tcont_counts[onu_id] = {
                    'lowest': 0, 'low': 0, 'medium': 0, 'high': 0, 'highest': 0
                }
            
            if tcont_id in onu_tcont_counts[onu_id]:
                onu_tcont_counts[onu_id][tcont_id] += 1
        
        if not onu_tcont_counts:
            self._plot_no_data("No se encontraron datos de ONUs")
            return
        
        # Crear subgráficas para cada ONU
        num_onus = len(onu_tcont_counts)
        
        if num_onus == 1:
            # Una sola ONU
            rows, cols = 1, 1
        elif num_onus == 2:
            # Dos ONUs horizontalmente
            rows, cols = 1, 2
        elif num_onus <= 4:
            # Hasta 4 ONUs en 2x2
            rows, cols = 2, 2
        elif num_onus <= 6:
            # Hasta 6 ONUs en 2x3
            rows, cols = 2, 3
        else:
            # Más ONUs en 3x3
            rows, cols = 3, 3
        
        # Tipos de TCONT y colores
        tcont_types = ['lowest', 'low', 'medium', 'high', 'highest']
        tcont_colors = ['#ff4444', '#ff8800', '#ffdd00', '#4488ff', '#00aa44']
        tcont_labels = ['Lowest', 'Low', 'Medium', 'High', 'Highest']
        
        # Crear gráficas para cada ONU
        for i, (onu_id, tcont_data) in enumerate(onu_tcont_counts.items()):
            if i >= rows * cols:  # Limitar número de gráficas
                break
                
            ax = self.fig.add_subplot(rows, cols, i + 1)
            
            # Datos para la gráfica de barras
            values = [tcont_data[tcont_type] for tcont_type in tcont_types]
            
            # Crear gráfica de barras
            bars = ax.bar(tcont_labels, values, color=tcont_colors, alpha=0.7, edgecolor='black', linewidth=0.5)
            
            # Agregar valores encima de las barras
            for bar, value in zip(bars, values):
                if value > 0:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.01,
                           f'{int(value)}', ha='center', va='bottom', fontweight='bold')
            
            # Configurar gráfica
            ax.set_title(f'ONU {onu_id} - Distribución de TCONTs', fontweight='bold')
            ax.set_xlabel('Tipo de TCONT')
            ax.set_ylabel('Cantidad')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Rotar etiquetas si es necesario
            if num_onus > 2:
                ax.tick_params(axis='x', rotation=45)
            
            # Agregar estadísticas
            total_tconts = sum(values)
            max_tcont = max(values) if values else 0
            most_used = tcont_labels[values.index(max_tcont)] if max_tcont > 0 else 'N/A'
            
            ax.text(0.02, 0.98, f'Total: {total_tconts}\nMás usado: {most_used}', 
                    transform=ax.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                    fontsize=8)
        
        # Título general
        self.fig.suptitle(f'Análisis de TCONTs por ONU ({num_onus} ONUs detectadas)', 
                         fontsize=14, fontweight='bold')
        
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
    
    def _calculate_p95_from_history(self, delay_history: List[Dict]) -> List[Dict[str, float]]:
        """
        Calcular P95 delay desde historial de delays usando ventanas deslizantes

        Args:
            delay_history: Lista de diccionarios con 'time' y 'value'

        Returns:
            Lista de diccionarios con 'time' y 'value' (P95)
        """
        if not delay_history or len(delay_history) < 10:
            return []

        # Usar ventanas de ~20 puntos para calcular P95
        window_size = max(10, len(delay_history) // 10)
        p95_history = []

        for i in range(0, len(delay_history), window_size // 2):
            window = delay_history[i:i + window_size]
            if len(window) >= 5:  # Mínimo 5 puntos para calcular P95
                values = [d['value'] for d in window]
                p95_value = np.percentile(values, 95)
                avg_time = np.mean([d['time'] for d in window])

                p95_history.append({
                    'time': avg_time,
                    'value': p95_value
                })

        return p95_history

    def _calculate_jitter_from_delays(self, delay_history: List[Dict]) -> List[Dict[str, float]]:
        """
        Calcular jitter (IPDV) desde historial de delays

        Args:
            delay_history: Lista de diccionarios con 'time' y 'value'

        Returns:
            Lista de diccionarios con 'time' y 'value' (jitter)
        """
        if not delay_history or len(delay_history) < 2:
            return []

        jitter_history = []
        window_size = max(5, len(delay_history) // 20)

        for i in range(window_size, len(delay_history), window_size // 2):
            window = delay_history[i - window_size:i]
            if len(window) >= 2:
                delays = [d['value'] for d in window]
                # Jitter como desviación estándar de los delays en la ventana
                jitter_value = np.std(delays)
                avg_time = np.mean([d['time'] for d in window])

                jitter_history.append({
                    'time': avg_time,
                    'value': jitter_value
                })

        return jitter_history

    def _simulate_metric_evolution(self, final_value: float, num_points: int, metric_type: str) -> np.ndarray:
        """Simular evolución realista de métricas según el tipo"""
        if num_points <= 1:
            return np.array([final_value])
            
        t = np.linspace(0, 1, num_points)
        
        if metric_type == 'delay':
            # Delay: inicio alto, converge gradualmente
            base_curve = 1 - np.exp(-3 * t)
            noise = np.random.normal(0, 0.1, num_points) * final_value * 0.1
            values = final_value * base_curve + noise
            
        elif metric_type == 'percentile':
            # P95: más variabilidad que mean delay
            base_curve = 1 - np.exp(-2.5 * t)
            noise = np.random.normal(0, 0.15, num_points) * final_value * 0.15
            values = final_value * base_curve + noise
            
        elif metric_type == 'jitter':
            # Jitter: más oscilante, tiende a estabilizarse
            base_curve = 1 - np.exp(-4 * t)
            oscillation = np.sin(10 * t) * 0.2 * np.exp(-2 * t)
            noise = np.random.normal(0, 0.2, num_points) * final_value * 0.2
            values = final_value * (base_curve + oscillation) + noise
            
        else:
            # Curva genérica
            values = final_value * (1 - np.exp(-3 * t))
        
        # Asegurar que todos los valores sean no negativos
        values = np.maximum(values, 0)
        
        return values
    
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
        
        # Tab 4: Análisis ONUs
        self.setup_onu_analysis_tab()
        
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
        """Configurar tab de análisis comparativo con métricas de latencia y jitter"""
        tab = QWidget()
        layout = QGridLayout(tab)
        
        # Gráfico de Mean Delay vs Tiempo
        mean_delay_group = QGroupBox("Mean Delay vs Tiempo")
        mean_delay_group.setObjectName("pon_charts_group")
        mean_delay_layout = QVBoxLayout(mean_delay_group)
        
        self.charts['mean_delay'] = PONMetricsChart(width=8, height=5)
        mean_delay_layout.addWidget(self.charts['mean_delay'])
        
        layout.addWidget(mean_delay_group, 0, 0)
        
        # Gráfico de P95 Delay vs Tiempo
        p95_delay_group = QGroupBox("P95 Delay vs Tiempo")
        p95_delay_group.setObjectName("pon_charts_group")
        p95_delay_layout = QVBoxLayout(p95_delay_group)
        
        self.charts['p95_delay'] = PONMetricsChart(width=8, height=5)
        p95_delay_layout.addWidget(self.charts['p95_delay'])
        
        layout.addWidget(p95_delay_group, 0, 1)
        
        # Gráfico de Jitter IPDV Mean vs Tiempo
        jitter_group = QGroupBox("Jitter IPDV Mean vs Tiempo")
        jitter_group.setObjectName("pon_charts_group")
        jitter_layout = QVBoxLayout(jitter_group)
        
        self.charts['jitter_ipdv'] = PONMetricsChart(width=8, height=5)
        jitter_layout.addWidget(self.charts['jitter_ipdv'])
        
        layout.addWidget(jitter_group, 1, 0, 1, 2)  # Span across both columns
        
        self.tabs.addTab(tab, "📈 Análisis")
    
    def setup_onu_analysis_tab(self):
        """Configurar tab de análisis de ONUs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Crear área de scroll para manejar múltiples gráficas de ONUs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Widget container para las gráficas de ONUs
        onu_widget = QWidget()
        onu_layout = QVBoxLayout(onu_widget)
        
        # Grupo para análisis de TCONTs por ONU
        onu_analysis_group = QGroupBox("Análisis de Tipos de TCONT por ONU")
        onu_analysis_group.setObjectName("pon_charts_group")
        onu_analysis_layout = QVBoxLayout(onu_analysis_group)
        
        # Gráfica principal para análisis de ONUs
        self.charts['onu_tcont_analysis'] = PONMetricsChart(width=12, height=8)
        onu_analysis_layout.addWidget(self.charts['onu_tcont_analysis'])
        
        onu_layout.addWidget(onu_analysis_group)
        onu_layout.addStretch()
        
        scroll_area.setWidget(onu_widget)
        layout.addWidget(scroll_area)
        
        self.tabs.addTab(tab, "🔍 Análisis ONUs")
    
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
        
        # Nuevos gráficos de análisis de latencia y jitter
        if 'mean_delay' in self.charts:
            self.charts['mean_delay'].plot_mean_delay_evolution(simulation_data)
            self.chart_updated.emit('mean_delay')
        
        if 'p95_delay' in self.charts:
            self.charts['p95_delay'].plot_p95_delay_evolution(simulation_data)
            self.chart_updated.emit('p95_delay')
        
        if 'jitter_ipdv' in self.charts:
            self.charts['jitter_ipdv'].plot_jitter_ipdv_evolution(simulation_data)
            self.chart_updated.emit('jitter_ipdv')
        
        # Análisis de ONUs
        if 'onu_tcont_analysis' in self.charts:
            self.charts['onu_tcont_analysis'].plot_onu_tcont_analysis(simulation_data)
            self.chart_updated.emit('onu_tcont_analysis')
    
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
        
        # Convertir buffer levels: mantener formato nuevo con MB y timestamps
        buffer_history = episode_metrics.get('buffer_levels_history', [])
        print(f"[BUFFER-LOG-GUI] Normalizando datos. buffer_history tiene {len(buffer_history)} entries")
        if buffer_history:
            converted_buffer_history = []
            for step_data in buffer_history:
                # Detectar formato: nuevo (con 'time' y 'buffers') vs antiguo (solo buffers)
                if isinstance(step_data, dict) and 'time' in step_data and 'buffers' in step_data:
                    # Formato nuevo con timestamps - mantener tal cual
                    converted_buffer_history.append(step_data)
                    if len(converted_buffer_history) == 1:
                        print(f"[BUFFER-LOG-GUI] Formato NUEVO detectado con timestamps")
                else:
                    if len(converted_buffer_history) == 0:
                        print(f"[BUFFER-LOG-GUI] Formato ANTIGUO sin timestamps")
                    # Formato antiguo sin timestamps - convertir
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
            print(f"[BUFFER-LOG-GUI] Después de normalización: {len(converted_buffer_history)} entries")
        else:
            print(f"[BUFFER-LOG-GUI] ⚠️ buffer_history estaba VACÍO en entrada!")
        
        # Los delays y throughputs híbridos ya tienen formato compatible
        # (incluso mejor con timestamp, onu_id, tcont_id)
        
        return converted_data