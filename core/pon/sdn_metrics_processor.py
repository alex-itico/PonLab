"""
SDN Metrics Processor
Procesa datos de simulación PON para generar métricas SDN avanzadas
"""

import json
import math
from typing import Dict, List, Optional
from pathlib import Path


class SDNMetricsProcessor:
    """Procesador de métricas SDN a partir de datos de simulación"""
    
    def __init__(self):
        self.simulation_data = None
        self.calculated_metrics = None
        
    def load_simulation_data(self, json_path: str) -> bool:
        """
        Cargar datos de simulación desde archivo JSON (soporta .json y .json.gz)

        Args:
            json_path: Ruta al archivo datos_simulacion.json o datos_simulacion.json.gz

        Returns:
            True si se cargó exitosamente
        """
        try:
            import gzip

            # Detectar si es comprimido por extensión
            if json_path.endswith('.gz'):
                with gzip.open(json_path, 'rt', encoding='utf-8') as f:
                    self.simulation_data = json.load(f)
                print(f"✅ Datos de simulación cargados (comprimidos): {json_path}")
            else:
                with open(json_path, 'r', encoding='utf-8') as f:
                    self.simulation_data = json.load(f)
                print(f"✅ Datos de simulación cargados: {json_path}")

            return True
        except Exception as e:
            print(f"❌ Error cargando datos de simulación: {e}")
            return False
    
    def calculate_sdn_metrics(self) -> Optional[Dict]:
        """
        Calcular todas las métricas SDN a partir de los datos de simulación
        
        Returns:
            Diccionario con métricas SDN en formato compatible con el dashboard
        """
        if not self.simulation_data:
            print("❌ No hay datos de simulación cargados")
            return None
        
        try:
            # Extraer datos relevantes
            sim_summary = self.simulation_data.get('simulation_summary', {})
            olt_stats = self.simulation_data.get('olt_stats', {}).get('olt_stats', {})
            transmission_log = self.simulation_data.get('olt_stats', {}).get('transmission_log', [])
            
            # Calcular métricas globales
            global_metrics = self._calculate_global_metrics(sim_summary, olt_stats)
            
            # Calcular métricas del controlador
            controller_metrics = self._calculate_controller_metrics(olt_stats, transmission_log)
            
            # Calcular métricas por ONU
            onu_metrics = self._calculate_onu_metrics(transmission_log)
            
            # Calcular distribución por servicio
            service_distribution = self._calculate_service_distribution(transmission_log)
            
            # Calcular cumplimiento SLA
            sla_compliance = self._calculate_sla_compliance(transmission_log, onu_metrics)
            
            self.calculated_metrics = {
                'global_metrics': global_metrics,
                'controller_metrics': controller_metrics,
                'onu_metrics': onu_metrics,
                'service_metrics': service_distribution,
                'sla_metrics': sla_compliance
            }
            
            print("✅ Métricas SDN calculadas exitosamente")
            return self.calculated_metrics
            
        except Exception as e:
            print(f"❌ Error calculando métricas SDN: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_global_metrics(self, sim_summary: Dict, olt_stats: Dict) -> Dict:
        """Calcular métricas globales del sistema"""
        sim_stats = sim_summary.get('simulation_stats', {})
        perf_metrics = sim_summary.get('performance_metrics', {})
        transmission_log = self.simulation_data.get('olt_stats', {}).get('transmission_log', [])
        
        # Calcular grants utilizados vs asignados
        grants_assigned = olt_stats.get('grants_assigned', 0)
        successful_tx = olt_stats.get('successful_transmissions', 0)
        failed_tx = olt_stats.get('failed_transmissions', 0)
        
        grant_utilization = (successful_tx / grants_assigned * 100) if grants_assigned > 0 else 0
        
        # Calcular fairness index real usando throughputs por ONU
        fairness, fairness_history = self._calculate_real_fairness_index(transmission_log)
        
        # Eficiencia espectral (bits/Hz)
        total_bits = olt_stats.get('total_grants_bytes', 0) * 8
        channel_capacity = self.simulation_data.get('olt_stats', {}).get('channel_capacity', 1024)
        simulation_time = sim_stats.get('simulation_time', 1)
        spectral_efficiency = (total_bits / (channel_capacity * 1e6 * simulation_time)) if simulation_time > 0 else 0
        
        # Calcular reconfiguraciones (cambios significativos en asignación de grants)
        reconfigurations = self._calculate_reconfigurations(transmission_log)
        
        # Calcular violaciones QoS (latencias > 10ms)
        qos_violations = self._calculate_qos_violations(transmission_log)
        
        # Calcular latencia promedio
        latencies = [tx.get('latency', 0) * 1000 for tx in transmission_log if 'latency' in tx]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        # Calcular throughput total
        total_data = sum(tx.get('data_size_mb', 0) for tx in transmission_log)
        total_throughput = (total_data * 8 / simulation_time) if simulation_time > 0 else 0
        
        # Calcular packet loss
        packet_loss = (failed_tx / (successful_tx + failed_tx) * 100) if (successful_tx + failed_tx) > 0 else 0
        
        return {
            'fairness_index': fairness,
            'fairness_history': fairness_history,
            'spectral_efficiency': spectral_efficiency,
            'grant_utilization': grant_utilization,
            'avg_latency': avg_latency,
            'total_throughput': total_throughput,
            'packet_loss': packet_loss,
            'reconfigurations': reconfigurations,
            'qos_violations': qos_violations,
        }
    
    def _calculate_controller_metrics(self, olt_stats: Dict, transmission_log: List) -> Dict:
        """Calcular métricas del controlador SDN"""
        
        total_decisions = olt_stats.get('grants_assigned', 0)
        total_cycles = olt_stats.get('cycles_executed', 0)
        
        # Tiempo de respuesta del controlador (basado en número de ONUs y complejidad)
        num_onus = len(set(tx.get('onu_id') for tx in transmission_log if 'onu_id' in tx))
        num_transmissions = len(transmission_log)
        
        # Tiempo base + overhead por ONU + overhead por decisión
        base_time = 0.0005  # 0.5ms base
        onu_overhead = num_onus * 0.0002  # 0.2ms por ONU
        decision_overhead = (num_transmissions / 10000) * 0.001  # Escala con transmisiones
        avg_controller_response = base_time + onu_overhead + decision_overhead
        
        # Latencia de decisión (75-85% del tiempo de respuesta)
        avg_decision_latency = avg_controller_response * 0.8
        
        # Tasa de reasignación: calcular cambios en patrones de grants
        reassignment_rate = self._calculate_reassignment_rate(transmission_log, total_decisions)
        
        # Utilización de ancho de banda
        channel_utilization = olt_stats.get('average_utilization', 0)
        
        return {
            'total_decisions': total_decisions,
            'avg_controller_response_time': avg_controller_response,
            'avg_decision_latency': avg_decision_latency,
            'reassignment_rate': reassignment_rate,
            'avg_bandwidth_utilization': channel_utilization,
        }
    
    def _calculate_onu_metrics(self, transmission_log: List) -> Dict:
        """Calcular métricas por ONU"""
        onu_data = {}
        
        for transmission in transmission_log:
            onu_id = transmission.get('onu_id', 'unknown')
            
            if onu_id not in onu_data:
                onu_data[onu_id] = {
                    'latencies': [],
                    'throughputs': [],
                    'grants_allocated': 0,
                    'grants_used': 0,
                    'losses': 0,
                }
            
            # Recopilar datos
            latency = transmission.get('latency', 0)
            throughput = transmission.get('data_size_mb', 0) / max(latency, 0.001)  # MB/s
            
            onu_data[onu_id]['latencies'].append(latency)
            onu_data[onu_id]['throughputs'].append(throughput)
            onu_data[onu_id]['grants_allocated'] += 1
            
            if transmission.get('success', True):
                onu_data[onu_id]['grants_used'] += 1
            else:
                onu_data[onu_id]['losses'] += 1
        
        # Calcular métricas agregadas por ONU
        onu_metrics = {}
        for onu_id, data in onu_data.items():
            latencies = data['latencies']
            throughputs = data['throughputs']
            
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            avg_throughput = sum(throughputs) / len(throughputs) if throughputs else 0
            
            # Calcular jitter (desviación estándar de latencias)
            avg_jitter = 0
            if len(latencies) > 1:
                mean_lat = avg_latency
                variance = sum((lat - mean_lat) ** 2 for lat in latencies) / len(latencies)
                avg_jitter = math.sqrt(variance)
            
            # Calcular nivel de congestión (0-1) más realista
            packet_loss_rate = (data['losses'] / data['grants_allocated'] * 100) if data['grants_allocated'] > 0 else 0
            
            # Factor de latencia: normalizar a 20ms (latencia alta)
            latency_factor = min(avg_latency / 0.02, 1.0)
            
            # Factor de pérdida de paquetes
            loss_factor = min(packet_loss_rate / 10, 1.0)  # 10% es muy alto
            
            # Factor de jitter (variabilidad)
            jitter_factor = min(avg_jitter / 0.005, 1.0)  # 5ms de jitter es alto
            
            # Factor de utilización de grants
            grant_utilization = data['grants_used'] / data['grants_allocated'] if data['grants_allocated'] > 0 else 0
            utilization_factor = 1.0 if grant_utilization > 0.9 else grant_utilization
            
            # Congestión combinada (ponderada)
            congestion_level = (
                latency_factor * 0.35 + 
                loss_factor * 0.30 + 
                jitter_factor * 0.20 + 
                utilization_factor * 0.15
            )
            
            onu_metrics[onu_id] = {
                'avg_latency': avg_latency,
                'avg_jitter': avg_jitter,
                'packet_loss_rate': packet_loss_rate,
                'avg_throughput': avg_throughput,
                'grant_efficiency': (data['grants_used'] / data['grants_allocated'] * 100) if data['grants_allocated'] > 0 else 0,
                'congestion_level': congestion_level,
                'avg_response_time': avg_latency * 1.2,  # Tiempo de respuesta incluye overhead
            }
        
        return onu_metrics
    
    def _calculate_service_distribution(self, transmission_log: List) -> Dict:
        """Calcular distribución de ancho de banda por clase de servicio"""
        service_distribution = {
            'highest': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'lowest': 0
        }
        
        # Asignar transmisiones a clases de servicio basado en tamaño
        for transmission in transmission_log:
            data_size = transmission.get('data_size_mb', 0)
            
            # Heurística: tamaño de paquete indica prioridad
            if data_size > 0.05:  # > 50KB
                service_distribution['highest'] += data_size
            elif data_size > 0.03:  # > 30KB
                service_distribution['high'] += data_size
            elif data_size > 0.015:  # > 15KB
                service_distribution['medium'] += data_size
            elif data_size > 0.005:  # > 5KB
                service_distribution['low'] += data_size
            else:
                service_distribution['lowest'] += data_size
        
        return service_distribution
    
    def _calculate_sla_compliance(self, transmission_log: List, onu_metrics: Dict) -> Dict:
        """Calcular cumplimiento de SLA por T-CONT"""
        sla_compliance = {}
        
        # Definir umbrales de SLA por T-CONT
        sla_thresholds = {
            'T1': 0.002,  # 2ms para Fixed Bandwidth
            'T2': 0.005,  # 5ms para Assured Bandwidth
            'T3': 0.010,  # 10ms para Non-assured
            'T4': 0.050,  # 50ms para Best Effort
        }
        
        for onu_id, metrics in onu_metrics.items():
            avg_latency = metrics.get('avg_latency', 0)
            
            sla_compliance[onu_id] = {}
            
            for tcont, threshold in sla_thresholds.items():
                met = 1 if avg_latency <= threshold else 0
                violated = 0 if avg_latency <= threshold else 1
                
                sla_compliance[onu_id][tcont] = {
                    'met': met,
                    'violated': violated
                }
        
        return sla_compliance
    
    def _calculate_real_fairness_index(self, transmission_log: List) -> tuple:
        """
        Calcular índice de fairness de Jain real basado en throughputs por ONU
        
        Returns:
            (fairness_index, fairness_history)
        """
        if not transmission_log:
            return 0.0, []
        
        # Agrupar transmisiones por ONU
        onu_throughputs = {}
        for tx in transmission_log:
            onu_id = tx.get('onu_id', 'unknown')
            data_size = tx.get('data_size_mb', 0)
            
            if onu_id not in onu_throughputs:
                onu_throughputs[onu_id] = 0
            onu_throughputs[onu_id] += data_size
        
        # Calcular índice de Jain: (Σx_i)² / (n * Σx_i²)
        throughputs = list(onu_throughputs.values())
        n = len(throughputs)
        
        if n == 0 or sum(throughputs) == 0:
            return 0.0, []
        
        sum_throughput = sum(throughputs)
        sum_squared = sum(t**2 for t in throughputs)
        
        fairness_index = (sum_throughput ** 2) / (n * sum_squared) if sum_squared > 0 else 0
        
        # Generar histórico de fairness (simulado por ventanas temporales)
        fairness_history = self._generate_fairness_history(transmission_log, onu_throughputs)
        
        return round(fairness_index, 3), fairness_history
    
    def _generate_fairness_history(self, transmission_log: List, onu_throughputs: Dict) -> List:
        """Generar histórico de fairness dividiendo en ventanas temporales"""
        if not transmission_log or len(transmission_log) < 10:
            return [0.85] * 10  # Valor por defecto
        
        # Dividir transmisiones en 10 ventanas
        window_size = len(transmission_log) // 10
        fairness_values = []
        
        for i in range(10):
            start_idx = i * window_size
            end_idx = start_idx + window_size if i < 9 else len(transmission_log)
            window_txs = transmission_log[start_idx:end_idx]
            
            # Calcular throughput por ONU en esta ventana
            window_throughputs = {}
            for tx in window_txs:
                onu_id = tx.get('onu_id', 'unknown')
                data_size = tx.get('data_size_mb', 0)
                
                if onu_id not in window_throughputs:
                    window_throughputs[onu_id] = 0
                window_throughputs[onu_id] += data_size
            
            # Calcular Jain para esta ventana
            throughputs = list(window_throughputs.values())
            n = len(throughputs)
            
            if n > 0 and sum(throughputs) > 0:
                sum_tp = sum(throughputs)
                sum_sq = sum(t**2 for t in throughputs)
                fairness = (sum_tp ** 2) / (n * sum_sq) if sum_sq > 0 else 0.85
                fairness_values.append(round(fairness, 2))
            else:
                fairness_values.append(0.85)
        
        return fairness_values
    
    def _calculate_reconfigurations(self, transmission_log: List) -> int:
        """
        Calcular número de reconfiguraciones (cambios significativos en asignación)
        """
        if not transmission_log or len(transmission_log) < 2:
            return 0
        
        reconfigurations = 0
        prev_onu_id = None
        onu_sequence_length = 0
        threshold = 3  # Cambiar de ONU al menos 3 veces seguidas cuenta como reconfiguración
        
        for tx in transmission_log:
            current_onu = tx.get('onu_id')
            
            if prev_onu_id is None:
                prev_onu_id = current_onu
                onu_sequence_length = 1
            elif current_onu == prev_onu_id:
                onu_sequence_length += 1
            else:
                # Cambio de ONU
                if onu_sequence_length >= threshold:
                    reconfigurations += 1
                prev_onu_id = current_onu
                onu_sequence_length = 1
        
        # También contar basado en cambios en tamaño de grant
        grant_size_changes = 0
        prev_size = None
        
        for tx in transmission_log:
            current_size = tx.get('data_size_mb', 0)
            
            if prev_size is not None:
                # Cambio significativo (>20%)
                if abs(current_size - prev_size) / max(prev_size, 0.001) > 0.2:
                    grant_size_changes += 1
            
            prev_size = current_size
        
        # Total de reconfiguraciones
        total_reconfigs = reconfigurations + (grant_size_changes // 10)
        
        return total_reconfigs
    
    def _calculate_qos_violations(self, transmission_log: List) -> int:
        """
        Calcular violaciones de QoS (latencias que superan umbrales)
        """
        violations = 0
        threshold = 0.010  # 10ms
        
        for tx in transmission_log:
            latency = tx.get('latency', 0)
            if latency > threshold:
                violations += 1
        
        return violations
    
    def _calculate_reassignment_rate(self, transmission_log: List, total_decisions: int) -> int:
        """
        Calcular tasa de reasignación (cuántas veces se reasignan grants)
        """
        if not transmission_log or total_decisions == 0:
            return 0
        
        # Contar cambios en patrones de asignación
        onu_grant_changes = {}
        prev_grants = {}
        
        for tx in transmission_log:
            onu_id = tx.get('onu_id')
            grant_size = tx.get('data_size_mb', 0)
            
            if onu_id not in onu_grant_changes:
                onu_grant_changes[onu_id] = 0
                prev_grants[onu_id] = grant_size
            else:
                # Si el grant cambió significativamente
                if abs(grant_size - prev_grants[onu_id]) / max(prev_grants[onu_id], 0.001) > 0.15:
                    onu_grant_changes[onu_id] += 1
                prev_grants[onu_id] = grant_size
        
        # Suma total de reasignaciones
        total_reassignments = sum(onu_grant_changes.values())
        
        return total_reassignments
    
    def get_metrics(self) -> Optional[Dict]:
        """Obtener las métricas calculadas"""
        return self.calculated_metrics
    
    def save_metrics(self, output_path: str) -> bool:
        """
        Guardar métricas calculadas a archivo JSON
        
        Args:
            output_path: Ruta donde guardar las métricas
            
        Returns:
            True si se guardó exitosamente
        """
        if not self.calculated_metrics:
            print("❌ No hay métricas calculadas para guardar")
            return False
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.calculated_metrics, f, indent=2)
            print(f"✅ Métricas SDN guardadas en: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error guardando métricas: {e}")
            return False
