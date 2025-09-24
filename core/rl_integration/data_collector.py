"""
Data Collector
Sistema de captura de datos en tiempo real durante simulaciones RL
"""

import sys
import os
from typing import Dict, List, Any, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import numpy as np
from collections import deque
import time


class RealTimeDataCollector(QObject):
    """
    Colector de datos en tiempo real para simulaciones RL
    Captura métricas de red durante la simulación y las formatea para gráficos
    """

    # Señales
    data_collected = pyqtSignal(dict)  # Nuevos datos capturados
    metrics_updated = pyqtSignal(dict)  # Métricas actualizadas

    def __init__(self, max_history_size: int = 1000, parent=None):
        super().__init__(parent)

        self.max_history_size = max_history_size
        self.is_collecting = False
        self.env = None
        self.simulator = None

        # Buffers de datos históricos
        self.history = {
            'timestamps': deque(maxlen=max_history_size),
            'buffer_levels': deque(maxlen=max_history_size),
            'delays': deque(maxlen=max_history_size),
            'throughputs': deque(maxlen=max_history_size),
            'rewards': deque(maxlen=max_history_size),
            'actions': deque(maxlen=max_history_size),
            'episodes': deque(maxlen=max_history_size),
            'allocation_probability': deque(maxlen=max_history_size)
        }

        # Timer para captura periódica
        self.collection_timer = QTimer()
        self.collection_timer.timeout.connect(self._collect_data_point)
        self.collection_interval = 100  # ms

        # Estado de simulación
        self.current_episode = 0
        self.current_step = 0
        self.start_time = None
        self.last_reward = 0.0
        self.last_action = []

    def setup_environment(self, env):
        """
        Configurar el entorno RL para captura de datos

        Args:
            env: Entorno RL de netPONpy
        """
        try:
            self.env = env
            self.simulator = env.getSimulator() if hasattr(env, 'getSimulator') else None

            if not self.simulator:
                print("[WARNING] No se pudo obtener el simulador del entorno")
                return False

            print(f"[OK] DataCollector configurado para {self.simulator.num_onus} ONUs")
            return True

        except Exception as e:
            print(f"[ERROR] Error configurando entorno en DataCollector: {e}")
            return False

    def start_collection(self):
        """Iniciar captura de datos"""
        if not self.env or not self.simulator:
            print("[ERROR] No hay entorno configurado para captura de datos")
            return False

        try:
            self.is_collecting = True
            self.start_time = time.time()
            self.current_step = 0

            # Limpiar historial anterior
            for key in self.history:
                self.history[key].clear()

            # Iniciar timer de captura
            self.collection_timer.start(self.collection_interval)

            print("[OK] Captura de datos iniciada")
            return True

        except Exception as e:
            print(f"[ERROR] Error iniciando captura de datos: {e}")
            return False

    def stop_collection(self):
        """Detener captura de datos"""
        self.is_collecting = False
        self.collection_timer.stop()
        print("[OK] Captura de datos detenida")

    def _collect_data_point(self):
        """Capturar un punto de datos del simulador"""
        if not self.is_collecting or not self.simulator:
            return

        try:
            current_time = time.time() - self.start_time

            # Capturar datos del simulador
            buffer_levels = self.simulator.get_buffer_levels()
            delays = self.simulator.get_delays()
            throughputs = self.simulator.get_throughputs()
            allocation_prob = self.simulator.get_allocation_probability()

            # Procesar delays - obtener promedio por ONU
            delay_averages = [0.0] * self.simulator.num_onus
            if delays:
                for delay_data in delays:
                    onu_id = delay_data.get('onu_id', '0')
                    try:
                        onu_idx = int(onu_id)
                        if 0 <= onu_idx < self.simulator.num_onus:
                            delay_averages[onu_idx] = delay_data.get('delay', 0.0)
                    except (ValueError, TypeError):
                        continue

            # Procesar throughputs - obtener promedio por ONU
            throughput_averages = [0.0] * self.simulator.num_onus
            if throughputs:
                for throughput_data in throughputs:
                    onu_id = throughput_data.get('onu_id', '0')
                    try:
                        onu_idx = int(onu_id)
                        if 0 <= onu_idx < self.simulator.num_onus:
                            throughput_averages[onu_idx] = throughput_data.get('throughput', 0.0)
                    except (ValueError, TypeError):
                        continue

            # Guardar en historial
            self.history['timestamps'].append(current_time)
            self.history['buffer_levels'].append(buffer_levels.copy())
            self.history['delays'].append(delay_averages.copy())
            self.history['throughputs'].append(throughput_averages.copy())
            self.history['rewards'].append(self.last_reward)
            self.history['actions'].append(self.last_action.copy() if isinstance(self.last_action, list) else [])
            self.history['episodes'].append(self.current_episode)
            self.history['allocation_probability'].append(allocation_prob)

            # Crear punto de datos para emisión
            data_point = {
                'timestamp': current_time,
                'step': self.current_step,
                'episode': self.current_episode,
                'buffer_levels': buffer_levels,
                'delays': delay_averages,
                'throughputs': throughput_averages,
                'reward': self.last_reward,
                'action': self.last_action,
                'allocation_probability': allocation_prob
            }

            self.data_collected.emit(data_point)
            self.current_step += 1

        except Exception as e:
            print(f"[ERROR] Error capturando punto de datos: {e}")

    def update_rl_metrics(self, reward: float, action: Any, episode: int = None):
        """
        Actualizar métricas RL desde el training loop

        Args:
            reward: Recompensa del paso actual
            action: Acción tomada
            episode: Número de episodio actual
        """
        self.last_reward = reward

        # Convertir action a lista si es necesario
        if hasattr(action, '__iter__') and not isinstance(action, str):
            self.last_action = list(action)
        elif isinstance(action, (int, float)):
            self.last_action = [action]
        else:
            self.last_action = []

        if episode is not None:
            self.current_episode = episode

    def get_formatted_data_for_charts(self) -> Dict[str, Any]:
        """
        Formatear datos históricos para el sistema de gráficos de PonLab

        Returns:
            Diccionario con datos formateados para gráficos
        """
        if not self.history['timestamps']:
            return {}

        try:
            # Convertir deques a listas
            timestamps = list(self.history['timestamps'])
            buffer_levels_history = list(self.history['buffer_levels'])
            delays_history = list(self.history['delays'])
            throughputs_history = list(self.history['throughputs'])
            rewards_history = list(self.history['rewards'])
            allocation_prob_history = list(self.history['allocation_probability'])

            # Formatear datos según la estructura esperada por PONMetricsChartsPanel
            formatted_data = {
                'simulation_results': {
                    'metrics': {
                        'buffer_levels': [],
                        'delays': [],
                        'throughputs': [],
                        'allocation_probability': allocation_prob_history,
                        'rewards': rewards_history  # Específico para RL
                    },
                    'timestamps': timestamps,
                    'total_duration': timestamps[-1] if timestamps else 0.0,
                    'num_onus': self.simulator.num_onus if self.simulator else 4
                },
                'rl_specific': {
                    'rewards_per_step': rewards_history,
                    'average_reward': np.mean(rewards_history) if rewards_history else 0.0,
                    'total_steps': len(timestamps),
                    'episodes_completed': max(self.history['episodes']) if self.history['episodes'] else 0
                }
            }

            # Procesar datos por ONU
            if buffer_levels_history:
                num_onus = len(buffer_levels_history[0]) if buffer_levels_history[0] else 4

                for onu_idx in range(num_onus):
                    # Buffer levels por ONU
                    onu_buffers = [levels[onu_idx] if onu_idx < len(levels) else 0.0
                                 for levels in buffer_levels_history]

                    # Delays por ONU
                    onu_delays = [delays[onu_idx] if onu_idx < len(delays) else 0.0
                                for delays in delays_history]

                    # Throughputs por ONU
                    onu_throughputs = [throughputs[onu_idx] if onu_idx < len(throughputs) else 0.0
                                     for throughputs in throughputs_history]

                    formatted_data['simulation_results']['metrics']['buffer_levels'].append({
                        'onu_id': f'ONU_{onu_idx}',
                        'data': onu_buffers,
                        'timestamps': timestamps
                    })

                    formatted_data['simulation_results']['metrics']['delays'].append({
                        'onu_id': f'ONU_{onu_idx}',
                        'data': onu_delays,
                        'timestamps': timestamps,
                        'average': np.mean(onu_delays) if onu_delays else 0.0
                    })

                    formatted_data['simulation_results']['metrics']['throughputs'].append({
                        'onu_id': f'ONU_{onu_idx}',
                        'data': onu_throughputs,
                        'timestamps': timestamps,
                        'average': np.mean(onu_throughputs) if onu_throughputs else 0.0
                    })

            return formatted_data

        except Exception as e:
            print(f"[ERROR] Error formateando datos para gráficos: {e}")
            return {}

    def get_real_time_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de métricas en tiempo real

        Returns:
            Diccionario con resumen de métricas actuales
        """
        if not self.history['timestamps']:
            return {}

        try:
            # Últimos N puntos para promedios recientes
            recent_size = min(50, len(self.history['timestamps']))

            recent_rewards = list(self.history['rewards'])[-recent_size:]
            recent_allocation = list(self.history['allocation_probability'])[-recent_size:]

            # Buffer levels actuales
            current_buffers = list(self.history['buffer_levels'])[-1] if self.history['buffer_levels'] else []

            # Delays actuales
            current_delays = list(self.history['delays'])[-1] if self.history['delays'] else []

            # Throughputs actuales
            current_throughputs = list(self.history['throughputs'])[-1] if self.history['throughputs'] else []

            summary = {
                'current_step': self.current_step,
                'current_episode': self.current_episode,
                'elapsed_time': time.time() - self.start_time if self.start_time else 0.0,
                'average_reward_recent': np.mean(recent_rewards) if recent_rewards else 0.0,
                'current_reward': self.last_reward,
                'allocation_probability': np.mean(recent_allocation) if recent_allocation else 0.0,
                'buffer_levels': {
                    'current': current_buffers,
                    'average': [np.mean([levels[i] for levels in list(self.history['buffer_levels'])[-recent_size:] if i < len(levels)])
                              for i in range(len(current_buffers))] if current_buffers else []
                },
                'delays': {
                    'current': current_delays,
                    'average': [np.mean([delays[i] for delays in list(self.history['delays'])[-recent_size:] if i < len(delays)])
                              for i in range(len(current_delays))] if current_delays else []
                },
                'throughputs': {
                    'current': current_throughputs,
                    'average': [np.mean([throughputs[i] for throughputs in list(self.history['throughputs'])[-recent_size:] if i < len(throughputs)])
                              for i in range(len(current_throughputs))] if current_throughputs else []
                }
            }

            return summary

        except Exception as e:
            print(f"[ERROR] Error generando resumen en tiempo real: {e}")
            return {}

    def export_data(self, filepath: str) -> bool:
        """
        Exportar datos capturados a archivo

        Args:
            filepath: Ruta del archivo de salida

        Returns:
            True si se exportó correctamente
        """
        try:
            import json

            # Convertir deques a listas para serialización
            export_data = {}
            for key, deque_data in self.history.items():
                export_data[key] = list(deque_data)

            # Añadir metadata
            export_data['metadata'] = {
                'export_timestamp': time.time(),
                'simulation_duration': time.time() - self.start_time if self.start_time else 0.0,
                'total_steps': self.current_step,
                'total_episodes': self.current_episode,
                'collection_interval_ms': self.collection_interval
            }

            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)

            print(f"[OK] Datos exportados a: {filepath}")
            return True

        except Exception as e:
            print(f"[ERROR] Error exportando datos: {e}")
            return False

    def clear_history(self):
        """Limpiar historial de datos"""
        for key in self.history:
            self.history[key].clear()

        self.current_step = 0
        self.current_episode = 0
        print("[OK] Historial de datos limpiado")

    def set_collection_interval(self, interval_ms: int):
        """
        Configurar intervalo de captura de datos

        Args:
            interval_ms: Intervalo en milisegundos
        """
        self.collection_interval = interval_ms
        if self.collection_timer.isActive():
            self.collection_timer.setInterval(interval_ms)
        print(f"[OK] Intervalo de captura configurado a {interval_ms}ms")

    def get_data_statistics(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de los datos capturados

        Returns:
            Diccionario con estadísticas de los datos
        """
        if not self.history['timestamps']:
            return {}

        try:
            stats = {
                'total_data_points': len(self.history['timestamps']),
                'simulation_duration': list(self.history['timestamps'])[-1] if self.history['timestamps'] else 0.0,
                'data_collection_rate': len(self.history['timestamps']) / (time.time() - self.start_time) if self.start_time else 0.0,
                'memory_usage_mb': sum(len(deque_data) for deque_data in self.history.values()) * 0.001  # Aproximado
            }

            if self.history['rewards']:
                rewards = list(self.history['rewards'])
                stats['reward_statistics'] = {
                    'mean': np.mean(rewards),
                    'std': np.std(rewards),
                    'min': np.min(rewards),
                    'max': np.max(rewards),
                    'total': np.sum(rewards)
                }

            return stats

        except Exception as e:
            print(f"[ERROR] Error calculando estadísticas: {e}")
            return {}