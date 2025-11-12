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
            olt_stats_parent = self.simulation_data.get('olt_stats', {})  # Nivel padre con average_utilization
            olt_stats = olt_stats_parent.get('olt_stats', {})  # Nivel hijo con stats
            transmission_log = olt_stats_parent.get('transmission_log', [])
            
            # Calcular métricas globales
            global_metrics = self._calculate_global_metrics(sim_summary, olt_stats)
            
            # Calcular métricas del controlador (pasar nivel padre para average_utilization)
            controller_metrics = self._calculate_controller_metrics(olt_stats, transmission_log, olt_stats_parent)
            
            # Calcular métricas por ONU
            onu_metrics = self._calculate_onu_metrics(transmission_log)
            
            # Calcular distribución por servicio
            service_distribution = self._calculate_service_distribution(transmission_log)
            
            # Calcular cumplimiento SLA
            sla_compliance = self._calculate_sla_compliance(transmission_log, onu_metrics)
            
            # Calcular mapa de salud de ONUs
            health_map = self._calculate_onu_health_map(onu_metrics)
            
            self.calculated_metrics = {
                'global_metrics': global_metrics,
                'controller_metrics': controller_metrics,
                'onu_metrics': onu_metrics,
                'service_metrics': service_distribution,
                'sla_metrics': sla_compliance,
                'health_map': health_map
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
    
    def _calculate_controller_metrics(self, olt_stats: Dict, transmission_log: List, olt_stats_parent: Dict = None) -> Dict:
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
        
        # Utilización de ancho de banda - leer del nivel padre si está disponible
        channel_utilization = 0
        if olt_stats_parent:
            channel_utilization = olt_stats_parent.get('average_utilization', 0)
        
        # Si no hay utilización en olt_stats_parent, calcularla manualmente
        if channel_utilization == 0 and transmission_log:
            # Calcular utilización basada en datos transmitidos vs capacidad
            total_data = sum(tx.get('data_size_mb', 0) for tx in transmission_log)
            total_time = max(tx.get('end_time', 0) for tx in transmission_log) if transmission_log else 1
            
            # Capacidad del canal PON (asumiendo 1 Gbps = 125 MB/s)
            channel_capacity_mbps = 125  # MB/s
            
            # Utilización = (datos / (capacidad * tiempo)) * 100
            if total_time > 0:
                channel_utilization = (total_data / (channel_capacity_mbps * total_time)) * 100
                channel_utilization = min(channel_utilization, 100)  # Máximo 100%
        
        return {
            'total_decisions': total_decisions,
            'avg_controller_response_time': avg_controller_response,
            'avg_decision_latency': avg_decision_latency,
            'reassignment_rate': reassignment_rate,
            'avg_bandwidth_utilization': channel_utilization,
        }
    
    def _calculate_onu_metrics(self, transmission_log: List) -> Dict:
        """Calcular métricas por ONU usando transmission_log y delays"""
        # Obtener también los delays para calcular latencias
        delays = self.simulation_data.get('simulation_summary', {}).get('episode_metrics', {}).get('delays', [])
        
        onu_data = {}
        
        # Procesar transmission_log para throughput y grants
        for transmission in transmission_log:
            onu_id = str(transmission.get('onu_id', 'unknown'))
            
            if onu_id not in onu_data:
                onu_data[onu_id] = {
                    'latencies': [],
                    'data_transmitted': 0,
                    'grants_allocated': 0,
                    'total_duration': 0,
                    'tcont_data': {}  # Datos por tipo de servicio
                }
            
            # Datos de transmisión
            data_size_mb = transmission.get('data_size_mb', 0)
            duration = transmission.get('duration', 0)
            tcont_id = transmission.get('tcont_id', 'unknown')
            
            onu_data[onu_id]['data_transmitted'] += data_size_mb
            onu_data[onu_id]['grants_allocated'] += 1
            onu_data[onu_id]['total_duration'] += duration
            
            # Agrupar por T-CONT
            if tcont_id not in onu_data[onu_id]['tcont_data']:
                onu_data[onu_id]['tcont_data'][tcont_id] = {
                    'count': 0,
                    'data': 0
                }
            onu_data[onu_id]['tcont_data'][tcont_id]['count'] += 1
            onu_data[onu_id]['tcont_data'][tcont_id]['data'] += data_size_mb
        
        # Procesar delays para obtener latencias reales
        for delay_entry in delays:
            onu_id = str(delay_entry.get('onu_id', 'unknown'))
            delay_value = delay_entry.get('delay', 0)
            
            if onu_id in onu_data:
                onu_data[onu_id]['latencies'].append(delay_value)
        
        # Calcular métricas agregadas por ONU
        onu_metrics = {}
        for onu_id, data in onu_data.items():
            latencies = data['latencies']
            
            # Latencia promedio (en segundos, se convertirá a ms en dashboard)
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            # Throughput real: total de datos / tiempo total
            # Convertir de MB a Mbps (MB * 8 bits/byte / tiempo en segundos)
            if data['total_duration'] > 0:
                avg_throughput = (data['data_transmitted'] * 8) / data['total_duration']
            else:
                avg_throughput = 0
            
            # Calcular jitter (desviación estándar de latencias)
            avg_jitter = 0
            if len(latencies) > 1:
                mean_lat = avg_latency
                variance = sum((lat - mean_lat) ** 2 for lat in latencies) / len(latencies)
                avg_jitter = math.sqrt(variance)
            
            # Pérdida de paquetes: comparar grants vs transmisiones exitosas
            # Si no hay latencia registrada, asumimos que falló
            successful_tx = len(latencies)
            allocated_grants = data['grants_allocated']
            losses = allocated_grants - successful_tx
            packet_loss_rate = (losses / allocated_grants * 100) if allocated_grants > 0 else 0
            
            # Calcular nivel de congestión (0-1) más realista
            # Factor de latencia: normalizar a 20ms (latencia alta)
            latency_factor = min(avg_latency / 0.02, 1.0)
            
            # Factor de pérdida de paquetes
            loss_factor = min(packet_loss_rate / 10, 1.0)  # 10% es muy alto
            
            # Factor de jitter (variabilidad)
            jitter_factor = min(avg_jitter / 0.005, 1.0)  # 5ms de jitter es alto
            
            # Factor de utilización de grants
            grant_utilization = (successful_tx / allocated_grants * 100) if allocated_grants > 0 else 0
            utilization_factor = 1.0 if grant_utilization > 90 else (grant_utilization / 100)
            
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
                'grant_efficiency': grant_utilization,
                'congestion_level': congestion_level,
                'grants_received': allocated_grants,
                'tcont_data': data['tcont_data']  # Guardar datos por T-CONT
            }
        
        return onu_metrics
    
    def _calculate_service_distribution(self, transmission_log: List) -> Dict:
        """Calcular distribución de ancho de banda por clase de servicio con conteo de paquetes y latencias"""
        
        # Obtener delays para calcular latencias por servicio
        delays = self.simulation_data.get('simulation_summary', {}).get('episode_metrics', {}).get('delays', [])
        
        # Inicializar estructura con datos detallados
        service_data = {
            'highest': {'bandwidth': 0, 'packets': 0, 'latencies': []},
            'high': {'bandwidth': 0, 'packets': 0, 'latencies': []},
            'medium': {'bandwidth': 0, 'packets': 0, 'latencies': []},
            'low': {'bandwidth': 0, 'packets': 0, 'latencies': []},
            'lowest': {'bandwidth': 0, 'packets': 0, 'latencies': []}
        }
        
        # Procesar transmission_log para ancho de banda y conteo de paquetes
        for transmission in transmission_log:
            tcont_id = transmission.get('tcont_id', 'unknown')
            data_size = transmission.get('data_size_mb', 0)
            
            # Usar tcont_id real del JSON
            if tcont_id in service_data:
                service_data[tcont_id]['bandwidth'] += data_size
                service_data[tcont_id]['packets'] += 1
        
        # Procesar delays para obtener latencias por servicio
        for delay_entry in delays:
            tcont_id = delay_entry.get('tcont_id', 'unknown')
            delay_value = delay_entry.get('delay', 0)
            
            if tcont_id in service_data:
                service_data[tcont_id]['latencies'].append(delay_value)
        
        # Calcular métricas agregadas por servicio
        service_distribution = {}
        for service_class, data in service_data.items():
            avg_latency = sum(data['latencies']) / len(data['latencies']) if data['latencies'] else 0
            
            service_distribution[service_class] = {
                'bandwidth': data['bandwidth'],
                'packets': data['packets'],
                'avg_latency': avg_latency
            }
        
        return service_distribution
    
    def _calculate_sla_compliance(self, transmission_log: List, onu_metrics: Dict) -> Dict:
        """Calcular cumplimiento de SLA por T-CONT con conteo de paquetes por ONU y servicio
        Usa percentiles realistas basados en la distribución de delays (percentil 85 como umbral)
        """
        
        # Obtener delays del JSON que tienen tcont_id
        delays = self.simulation_data.get('simulation_summary', {}).get('episode_metrics', {}).get('delays', [])
        
        # Mapeo de tcont_id del JSON a T-CONT estándar
        tcont_mapping = {
            'highest': 'T1',
            'high': 'T2',
            'medium': 'T3',
            'low': 'T4',
            'lowest': 'T4'
        }
        
        # Estructura para almacenar datos por ONU y T-CONT
        sla_data = {}
        
        # Primer paso: recolectar todos los delays por ONU y T-CONT
        for delay_entry in delays:
            onu_id = str(delay_entry.get('onu_id', 'unknown'))
            delay_value = delay_entry.get('delay', 0)
            tcont_id = delay_entry.get('tcont_id', 'unknown')
            
            # Mapear a T-CONT estándar
            tcont = tcont_mapping.get(tcont_id, 'T4')
            
            # Inicializar estructura si no existe
            if onu_id not in sla_data:
                sla_data[onu_id] = {
                    'T1': {'met': 0, 'violated': 0, 'latencies': []},
                    'T2': {'met': 0, 'violated': 0, 'latencies': []},
                    'T3': {'met': 0, 'violated': 0, 'latencies': []},
                    'T4': {'met': 0, 'violated': 0, 'latencies': []},
                }
            
            # Guardar latencia
            sla_data[onu_id][tcont]['latencies'].append(delay_value)
        
        # Segundo paso: calcular umbrales basados en percentil 85 por cada combinación ONU-TCONT
        for onu_id, tconts in sla_data.items():
            for tcont, data in tconts.items():
                if not data['latencies']:
                    continue
                
                # Ordenar latencias
                sorted_latencies = sorted(data['latencies'])
                
                # Calcular percentil 85 como umbral (15% de peores delays se consideran violaciones)
                p85_index = int(len(sorted_latencies) * 0.85)
                threshold = sorted_latencies[p85_index] if p85_index < len(sorted_latencies) else sorted_latencies[-1]
                
                # Ahora clasificar cada delay como cumplido o violado
                for latency in data['latencies']:
                    if latency <= threshold:
                        data['met'] += 1
                    else:
                        data['violated'] += 1
                
                # Guardar el umbral calculado
                data['threshold'] = threshold
        
        # Calcular porcentajes y latencias promedio
        sla_compliance = {}
        for onu_id, tconts in sla_data.items():
            sla_compliance[onu_id] = {}
            
            for tcont, data in tconts.items():
                total_packets = data['met'] + data['violated']
                compliance_percentage = (data['met'] / total_packets * 100) if total_packets > 0 else 100.0
                avg_latency = sum(data['latencies']) / len(data['latencies']) if data['latencies'] else 0
                
                sla_compliance[onu_id][tcont] = {
                    'threshold': data['threshold'],
                    'compliance': compliance_percentage,
                    'avg_latency': avg_latency,
                    'packets_met': data['met'],
                    'packets_violated': data['violated'],
                    'total_packets': total_packets
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
        Calcular violaciones de QoS (latencias que superan umbrales específicos por T-CONT)
        Usa percentiles realistas basados en la distribución de delays
        """
        # Obtener delays reales del JSON
        delays = self.simulation_data.get('simulation_summary', {}).get('episode_metrics', {}).get('delays', [])
        
        if not delays:
            return 0
        
        # Agrupar delays por tcont_id
        delays_by_tcont = {
            'highest': [],
            'high': [],
            'medium': [],
            'low': [],
            'lowest': []
        }
        
        for delay_entry in delays:
            tcont_id = delay_entry.get('tcont_id', 'medium')
            delay_value = delay_entry.get('delay', 0)
            if tcont_id in delays_by_tcont:
                delays_by_tcont[tcont_id].append(delay_value)
        
        violations = 0
        
        # Para cada servicio, considerar como violación el percentil 90
        # (el 10% de los peores delays se consideran violaciones)
        for tcont_id, tcont_delays in delays_by_tcont.items():
            if not tcont_delays:
                continue
            
            # Ordenar delays
            sorted_delays = sorted(tcont_delays)
            
            # Calcular percentil 90 como umbral
            p90_index = int(len(sorted_delays) * 0.90)
            threshold = sorted_delays[p90_index] if p90_index < len(sorted_delays) else sorted_delays[-1]
            
            # Contar cuántos superan el percentil 90
            violations_for_tcont = sum(1 for d in tcont_delays if d > threshold)
            violations += violations_for_tcont
        
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
    
    def _calculate_onu_health_map(self, onu_metrics: Dict) -> Dict:
        """
        Calcular mapa de salud de ONUs con scores y recomendaciones
        
        Args:
            onu_metrics: Métricas calculadas por ONU
            
        Returns:
            Diccionario con health scores y recomendaciones por ONU
        """
        health_map = {}
        
        for onu_id, metrics in onu_metrics.items():
            # Normalizar métricas a escala 0-100 (100 = excelente)
            
            # 1. Score de Latencia (30% del total)
            # Latencia óptima: < 1ms, crítica: > 5ms
            avg_latency_ms = metrics.get('avg_latency', 0) * 1000
            if avg_latency_ms <= 1.0:
                latency_score = 100
            elif avg_latency_ms >= 5.0:
                latency_score = 0
            else:
                latency_score = 100 - ((avg_latency_ms - 1.0) / 4.0) * 100
            
            # 2. Score de Jitter (20% del total)
            # Jitter óptimo: < 0.5ms, crítico: > 3ms
            avg_jitter_ms = metrics.get('avg_jitter', 0) * 1000
            if avg_jitter_ms <= 0.5:
                jitter_score = 100
            elif avg_jitter_ms >= 3.0:
                jitter_score = 0
            else:
                jitter_score = 100 - ((avg_jitter_ms - 0.5) / 2.5) * 100
            
            # 3. Score de Pérdida de Paquetes (25% del total)
            # Óptimo: 0%, crítico: > 5%
            packet_loss = metrics.get('packet_loss_rate', 0)
            if packet_loss <= 0.1:
                loss_score = 100
            elif packet_loss >= 5.0:
                loss_score = 0
            else:
                loss_score = 100 - (packet_loss / 5.0) * 100
            
            # 4. Score de Congestión (25% del total)
            # Óptimo: < 0.3, crítico: > 0.8
            congestion = metrics.get('congestion_level', 0)
            if congestion <= 0.3:
                congestion_score = 100
            elif congestion >= 0.8:
                congestion_score = 0
            else:
                congestion_score = 100 - ((congestion - 0.3) / 0.5) * 100
            
            # Calcular score total ponderado
            total_score = (
                latency_score * 0.30 +
                jitter_score * 0.20 +
                loss_score * 0.25 +
                congestion_score * 0.25
            )
            
            # Determinar estado y emoji
            if total_score >= 80:
                status = 'Excelente'
                emoji = '🟢'
                priority = 'low'
            elif total_score >= 60:
                status = 'Bueno'
                emoji = '🟡'
                priority = 'medium'
            elif total_score >= 40:
                status = 'Regular'
                emoji = '🟠'
                priority = 'high'
            else:
                status = 'Crítico'
                emoji = '🔴'
                priority = 'critical'
            
            # Generar recomendaciones basadas en métricas
            recommendations = []
            
            if latency_score < 60:
                recommendations.append('↓ Reducir latencia')
            if jitter_score < 60:
                recommendations.append('📊 Estabilizar jitter')
            if loss_score < 60:
                recommendations.append('📦 Investigar pérdidas')
            if congestion_score < 60:
                recommendations.append('↑ Aumentar ancho de banda')
            
            if not recommendations:
                recommendations.append('✓ Operación óptima')
            
            # Agregar métricas detalladas
            health_map[onu_id] = {
                'score': round(total_score, 1),
                'status': status,
                'emoji': emoji,
                'priority': priority,
                'recommendations': recommendations,
                'component_scores': {
                    'latency': round(latency_score, 1),
                    'jitter': round(jitter_score, 1),
                    'packet_loss': round(loss_score, 1),
                    'congestion': round(congestion_score, 1)
                },
                'metrics': {
                    'latency_ms': round(avg_latency_ms, 3),
                    'jitter_ms': round(avg_jitter_ms, 3),
                    'packet_loss_pct': round(packet_loss, 2),
                    'congestion_level': round(congestion, 3),
                    'throughput_mbps': round(metrics.get('avg_throughput', 0), 2),
                    'grant_efficiency': round(metrics.get('grant_efficiency', 0), 1)
                }
            }
        
        return health_map
    
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
