"""
Metrics Converter
Convertidor de métricas entre PonLab y netPONpy RL
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from datetime import datetime


class MetricsConverter:
    """
    Convertidor de métricas entre formatos de PonLab y netPONpy RL
    """
    
    def __init__(self):
        self.metric_history = []
        self.conversion_stats = {
            'total_conversions': 0,
            'successful_conversions': 0,
            'last_conversion_time': None
        }
    
    def convert_rl_metrics_to_ponlab(self, rl_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertir métricas de netPONpy RL a formato compatible con PonLab
        
        Args:
            rl_metrics: Métricas del entorno RL
            
        Returns:
            Métricas en formato PonLab
        """
        try:
            ponlab_metrics = {
                'timestamp': datetime.now().isoformat(),
                'source': 'netponpy_rl',
                'simulation_data': {},
                'performance_data': {},
                'network_data': {}
            }
            
            # Datos de simulación
            if 'episode' in rl_metrics:
                ponlab_metrics['simulation_data']['episode'] = rl_metrics['episode']
            
            if 'step' in rl_metrics:
                ponlab_metrics['simulation_data']['step'] = rl_metrics['step']
            
            if 'sim_time' in rl_metrics:
                ponlab_metrics['simulation_data']['simulation_time'] = rl_metrics['sim_time']
            
            # Datos de rendimiento
            if 'reward' in rl_metrics:
                ponlab_metrics['performance_data']['reward'] = float(rl_metrics['reward'])
            
            if 'loss' in rl_metrics:
                ponlab_metrics['performance_data']['loss'] = float(rl_metrics['loss'])
            
            if 'blocking_probability' in rl_metrics:
                ponlab_metrics['performance_data']['blocking_probability'] = float(rl_metrics['blocking_probability'])
            
            # Datos de red
            if 'buffer_levels' in rl_metrics:
                ponlab_metrics['network_data']['buffer_levels'] = self._convert_buffer_levels(rl_metrics['buffer_levels'])
            
            if 'delays' in rl_metrics:
                ponlab_metrics['network_data']['delays'] = self._convert_delays(rl_metrics['delays'])
            
            if 'throughputs' in rl_metrics:
                ponlab_metrics['network_data']['throughputs'] = self._convert_throughputs(rl_metrics['throughputs'])
            
            # Actualizar estadísticas
            self._update_conversion_stats(True)
            
            return ponlab_metrics
            
        except Exception as e:
            print(f"❌ Error convirtiendo métricas RL->PonLab: {e}")
            self._update_conversion_stats(False)
            return {}
    
    def convert_ponlab_metrics_to_rl(self, ponlab_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertir métricas de PonLab a formato compatible con netPONpy RL
        
        Args:
            ponlab_metrics: Métricas de PonLab
            
        Returns:
            Métricas en formato RL
        """
        try:
            rl_metrics = {
                'timestamp': datetime.now().timestamp(),
                'source': 'ponlab'
            }
            
            # Extraer datos de simulación
            sim_data = ponlab_metrics.get('simulation_data', {})
            if 'bandwidth_allocations' in sim_data:
                rl_metrics['bandwidth_allocations'] = sim_data['bandwidth_allocations']
            
            if 'utilization' in sim_data:
                rl_metrics['utilization'] = float(sim_data['utilization'])
            
            # Extraer datos de red
            network_data = ponlab_metrics.get('network_data', {})
            if 'buffer_occupancy' in network_data:
                rl_metrics['buffer_levels'] = self._normalize_buffer_data(network_data['buffer_occupancy'])
            
            if 'latency' in network_data:
                rl_metrics['delays'] = self._normalize_delay_data(network_data['latency'])
            
            if 'throughput' in network_data:
                rl_metrics['throughputs'] = self._normalize_throughput_data(network_data['throughput'])
            
            # Actualizar estadísticas
            self._update_conversion_stats(True)
            
            return rl_metrics
            
        except Exception as e:
            print(f"❌ Error convirtiendo métricas PonLab->RL: {e}")
            self._update_conversion_stats(False)
            return {}
    
    def _convert_buffer_levels(self, buffer_data: Any) -> List[float]:
        """Convertir datos de buffer a formato PonLab"""
        try:
            if isinstance(buffer_data, (list, np.ndarray)):
                return [float(x) for x in buffer_data]
            elif isinstance(buffer_data, (int, float)):
                return [float(buffer_data)]
            else:
                return []
        except:
            return []
    
    def _convert_delays(self, delay_data: Any) -> List[Dict[str, Any]]:
        """Convertir datos de delays a formato PonLab"""
        try:
            if isinstance(delay_data, list):
                converted = []
                for item in delay_data:
                    if isinstance(item, dict):
                        converted.append({
                            'onu_id': item.get('onu_id', 'unknown'),
                            'delay_ms': float(item.get('delay', 0)) * 1000,  # Convertir a ms
                            'timestamp': item.get('timestamp', datetime.now().isoformat())
                        })
                return converted
            return []
        except:
            return []
    
    def _convert_throughputs(self, throughput_data: Any) -> List[Dict[str, Any]]:
        """Convertir datos de throughput a formato PonLab"""
        try:
            if isinstance(throughput_data, list):
                converted = []
                for item in throughput_data:
                    if isinstance(item, dict):
                        converted.append({
                            'onu_id': item.get('onu_id', 'unknown'),
                            'throughput_mbps': float(item.get('throughput', 0)),
                            'timestamp': item.get('timestamp', datetime.now().isoformat())
                        })
                return converted
            return []
        except:
            return []
    
    def _normalize_buffer_data(self, buffer_data: Any) -> List[float]:
        """Normalizar datos de buffer para RL"""
        try:
            if isinstance(buffer_data, (list, np.ndarray)):
                # Normalizar a rango [0, 1]
                data = np.array(buffer_data, dtype=float)
                if data.max() > 0:
                    return (data / data.max()).tolist()
                return data.tolist()
            return []
        except:
            return []
    
    def _normalize_delay_data(self, delay_data: Any) -> List[Dict[str, Any]]:
        """Normalizar datos de delay para RL"""
        try:
            if isinstance(delay_data, (list, np.ndarray)):
                normalized = []
                for i, delay in enumerate(delay_data):
                    normalized.append({
                        'onu_id': str(i),
                        'delay': float(delay) / 1000.0,  # Convertir ms a s
                        'timestamp': datetime.now().isoformat()
                    })
                return normalized
            return []
        except:
            return []
    
    def _normalize_throughput_data(self, throughput_data: Any) -> List[Dict[str, Any]]:
        """Normalizar datos de throughput para RL"""
        try:
            if isinstance(throughput_data, (list, np.ndarray)):
                normalized = []
                for i, tput in enumerate(throughput_data):
                    normalized.append({
                        'onu_id': str(i),
                        'throughput': float(tput),
                        'timestamp': datetime.now().isoformat()
                    })
                return normalized
            return []
        except:
            return []
    
    def compute_fairness_metrics(self, metrics: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcular métricas de equidad (fairness)
        
        Args:
            metrics: Métricas de entrada
            
        Returns:
            Métricas de equidad calculadas
        """
        try:
            fairness_metrics = {}
            
            # Fairness de throughput (Jain's fairness index)
            if 'throughputs' in metrics:
                throughputs = [float(t.get('throughput', 0)) for t in metrics['throughputs']]
                if throughputs:
                    jain_index = self._calculate_jain_fairness(throughputs)
                    fairness_metrics['jain_fairness_throughput'] = jain_index
            
            # Fairness de delays
            if 'delays' in metrics:
                delays = [float(d.get('delay', 0)) for d in metrics['delays']]
                if delays:
                    # Coeficiente de variación (menor = más justo)
                    cv = np.std(delays) / np.mean(delays) if np.mean(delays) > 0 else 0
                    fairness_metrics['delay_coefficient_variation'] = cv
                    fairness_metrics['delay_fairness'] = max(0, 1 - cv)  # Convertir a métrica de fairness
            
            # Fairness de buffer levels
            if 'buffer_levels' in metrics:
                buffers = metrics['buffer_levels']
                if buffers:
                    cv = np.std(buffers) / np.mean(buffers) if np.mean(buffers) > 0 else 0
                    fairness_metrics['buffer_fairness'] = max(0, 1 - cv)
            
            return fairness_metrics
            
        except Exception as e:
            print(f"❌ Error calculando métricas de equidad: {e}")
            return {}
    
    def _calculate_jain_fairness(self, values: List[float]) -> float:
        """
        Calcular índice de equidad de Jain
        
        Args:
            values: Lista de valores (ej. throughputs)
            
        Returns:
            Índice de Jain (0-1, donde 1 es perfecto fairness)
        """
        try:
            if not values or len(values) == 0:
                return 0.0
            
            values = np.array(values)
            n = len(values)
            
            if np.sum(values) == 0:
                return 1.0  # Si todos son 0, consideramos fairness perfecto
            
            numerator = (np.sum(values)) ** 2
            denominator = n * np.sum(values ** 2)
            
            return float(numerator / denominator) if denominator > 0 else 0.0
            
        except:
            return 0.0
    
    def aggregate_metrics_over_time(self, time_window_seconds: int = 60) -> Dict[str, Any]:
        """
        Agregar métricas sobre una ventana de tiempo
        
        Args:
            time_window_seconds: Ventana de tiempo en segundos
            
        Returns:
            Métricas agregadas
        """
        try:
            current_time = datetime.now().timestamp()
            cutoff_time = current_time - time_window_seconds
            
            # Filtrar métricas recientes
            recent_metrics = [
                m for m in self.metric_history 
                if datetime.fromisoformat(m.get('timestamp', '1970-01-01')).timestamp() > cutoff_time
            ]
            
            if not recent_metrics:
                return {}
            
            # Agregar datos
            aggregated = {
                'window_seconds': time_window_seconds,
                'sample_count': len(recent_metrics),
                'timestamp': datetime.now().isoformat(),
                'performance_summary': {},
                'network_summary': {}
            }
            
            # Agregar datos de rendimiento
            rewards = [m.get('performance_data', {}).get('reward', 0) for m in recent_metrics]
            if rewards:
                aggregated['performance_summary']['avg_reward'] = np.mean(rewards)
                aggregated['performance_summary']['std_reward'] = np.std(rewards)
                aggregated['performance_summary']['min_reward'] = np.min(rewards)
                aggregated['performance_summary']['max_reward'] = np.max(rewards)
            
            # Agregar datos de red
            blocking_probs = [m.get('performance_data', {}).get('blocking_probability', 0) for m in recent_metrics]
            if blocking_probs:
                aggregated['network_summary']['avg_blocking_probability'] = np.mean(blocking_probs)
                aggregated['network_summary']['max_blocking_probability'] = np.max(blocking_probs)
            
            return aggregated
            
        except Exception as e:
            print(f"❌ Error agregando métricas: {e}")
            return {}
    
    def add_to_history(self, metrics: Dict[str, Any]):
        """Agregar métricas al historial"""
        try:
            metrics['conversion_timestamp'] = datetime.now().isoformat()
            self.metric_history.append(metrics)
            
            # Mantener solo las últimas 1000 entradas
            if len(self.metric_history) > 1000:
                self.metric_history = self.metric_history[-1000:]
                
        except Exception as e:
            print(f"❌ Error agregando al historial: {e}")
    
    def _update_conversion_stats(self, success: bool):
        """Actualizar estadísticas de conversión"""
        self.conversion_stats['total_conversions'] += 1
        if success:
            self.conversion_stats['successful_conversions'] += 1
        self.conversion_stats['last_conversion_time'] = datetime.now().isoformat()
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de conversión"""
        stats = self.conversion_stats.copy()
        if stats['total_conversions'] > 0:
            stats['success_rate'] = stats['successful_conversions'] / stats['total_conversions']
        else:
            stats['success_rate'] = 0.0
        return stats

    def convert_simulation_metrics(self, sim_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertir métricas de simulación RL a formato PonLab

        Args:
            sim_metrics: Métricas de simulación del SimulationManager

        Returns:
            Métricas convertidas en formato PonLab
        """
        try:
            converted = {
                'timestamp': datetime.now().isoformat(),
                'metric_type': 'simulation',
                'conversion_successful': True
            }

            # Datos de progreso
            if 'progress_percent' in sim_metrics:
                converted['progress_data'] = {
                    'progress_percent': sim_metrics['progress_percent'],
                    'elapsed_time': sim_metrics.get('elapsed_time', 0)
                }

            # Datos de rendimiento del agente
            if 'average_reward' in sim_metrics:
                converted['performance_data'] = {
                    'average_reward': sim_metrics['average_reward'],
                    'current_reward': sim_metrics.get('current_reward', 0),
                    'total_reward': sim_metrics.get('total_reward', 0)
                }

            # Datos de simulación
            if 'step_count' in sim_metrics:
                converted['simulation_data'] = {
                    'step_count': sim_metrics['step_count'],
                    'decisions_count': sim_metrics.get('decisions_count', 0),
                    'steps_per_second': sim_metrics.get('steps_per_second', 0)
                }

            # Métricas de red (si están disponibles)
            network_metrics = {}
            if 'throughput' in sim_metrics:
                network_metrics['throughput'] = sim_metrics['throughput']
            if 'latency' in sim_metrics:
                network_metrics['latency'] = sim_metrics['latency']
            if 'blocking_probability' in sim_metrics:
                network_metrics['blocking_probability'] = sim_metrics['blocking_probability']

            if network_metrics:
                converted['network_data'] = network_metrics

            # Actualizar estadísticas de conversión
            self.conversion_stats['total_conversions'] += 1
            self.conversion_stats['successful_conversions'] += 1
            self.conversion_stats['last_conversion_time'] = datetime.now().isoformat()

            return converted

        except Exception as e:
            print(f"❌ Error convirtiendo métricas de simulación: {e}")
            self.conversion_stats['total_conversions'] += 1
            return {
                'timestamp': datetime.now().isoformat(),
                'metric_type': 'simulation',
                'conversion_successful': False,
                'error': str(e)
            }

    def clear_history(self):
        """Limpiar historial de métricas"""
        self.metric_history.clear()
        print("🧹 Historial de métricas limpiado")