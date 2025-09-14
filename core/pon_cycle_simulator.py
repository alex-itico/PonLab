"""
PON NetSim Realistic
Motor de simulación PON realista con ciclos DBA
"""

from typing import Optional, Dict, Any, List
from .pon_olt import OLT
from .pon_dba_cycle import DBACycleManager, DBAResult, DBAAllocation
from .pon_request import Request


class EventEvaluator:
    """Interfaz base para evaluadores de eventos"""
    
    def on_init(self):
        """Callback al iniciar simulación"""
        pass
    
    def on_cycle_start(self, cycle_number: int, cycle_time: float):
        """Callback al iniciar un ciclo DBA"""
        pass
    
    def on_cycle_end(self, dba_result: DBAResult):
        """Callback al finalizar un ciclo DBA"""
        pass
    
    def on_simulation_end(self, attributes: Dict[str, Any]):
        """Callback al finalizar simulación"""
        pass


class RealisticNetSim:
    """Simulador de red PON realista con ciclos DBA"""
    
    def __init__(self, network: OLT, cycle_duration: float = 0.000125):
        """
        Inicializar simulador realista
        
        Args:
            network: Red PON (OLT) a simular
            cycle_duration: Duración de ciclo DBA en segundos (125us default)
        """
        self.network = network
        self.dba_manager = DBACycleManager(cycle_duration)
        self.simulation_time = 0.0
        self.cycles_executed = 0
        
        # Métricas globales de simulación
        self.total_requests_processed = 0
        self.successful_transmissions = 0
        self.failed_transmissions = 0
        self.total_bandwidth_used = 0.0
        
        # Historial de métricas por ciclo
        self.cycle_history = []
        self.delay_history = []
        self.throughput_history = []
        self.buffer_levels_history = []
        self.utilization_history = []
        
    def run_cycles(self, num_cycles: int, callback: Optional[EventEvaluator] = None):
        """
        Ejecutar simulación por número de ciclos DBA
        
        Args:
            num_cycles: Número de ciclos DBA a ejecutar
            callback: Evaluador de eventos opcional
        """
        print(f"Iniciando simulacion realista: {num_cycles} ciclos DBA")
        print(f"   Duracion por ciclo: {self.dba_manager.cycle_duration*1000000:.1f}us")
        
        callback and callback.on_init()
        
        for cycle in range(num_cycles):
            try:
                callback and callback.on_cycle_start(cycle, self.simulation_time)
                
                # Ejecutar ciclo DBA completo
                dba_result = self.dba_manager.execute_dba_cycle(
                    onus=self.network.onus,
                    dba_algorithm=self.network.dba_algorithm,
                    total_bandwidth=self.network.transmition_rate,
                    current_time=self.simulation_time,
                    action=getattr(self.network, '_last_action', None)
                )
                
                # Procesar transmisiones del ciclo
                self._process_cycle_transmissions(dba_result)
                
                # Actualizar tiempo de simulación
                self.simulation_time += self.dba_manager.cycle_duration
                self.cycles_executed += 1
                
                # Recoger métricas del ciclo
                self._collect_cycle_metrics(dba_result)
                
                callback and callback.on_cycle_end(dba_result)
                
                # Log periódico
                if cycle % 100 == 0 and cycle > 0:
                    self._print_progress_log(cycle)
                    
            except Exception as e:
                print(f"ERROR en ciclo {cycle}: {e}")
                break
        
        # Estadísticas finales
        final_stats = self._calculate_final_statistics()
        
        print(f"Simulacion realista completada:")
        print(f"   • Ciclos ejecutados: {self.cycles_executed}")
        print(f"   • Tiempo simulado: {self.simulation_time*1000:.3f}ms")
        print(f"   • Requests procesados: {self.total_requests_processed}")
        print(f"   • Transmisiones exitosas: {self.successful_transmissions}")
        print(f"   • Throughput promedio: {final_stats.get('mean_throughput', 0):.3f}MB/s")
        print(f"   • Delay promedio: {final_stats.get('mean_delay', 0)*1000:.3f}ms")
        
        callback and callback.on_simulation_end(final_stats)
        
    def run_for_time(self, simulation_time: float, callback: Optional[EventEvaluator] = None):
        """
        Ejecutar simulación por tiempo específico
        
        Args:
            simulation_time: Tiempo total de simulación en segundos
            callback: Evaluador de eventos opcional
        """
        # Calcular número de ciclos necesarios
        num_cycles = int(simulation_time / self.dba_manager.cycle_duration)
        
        print(f"Simulacion por tiempo: {simulation_time*1000:.1f}ms")
        print(f"   Equivale a {num_cycles} ciclos DBA")
        
        self.run_cycles(num_cycles, callback)
        
    def _process_cycle_transmissions(self, dba_result: DBAResult):
        """Procesar todas las transmisiones de un ciclo DBA"""
        
        successful_in_cycle = 0
        failed_in_cycle = 0
        
        for allocation in dba_result.allocations:
            try:
                # Procesar cada request en el allocation
                for request in allocation.requests_to_process:
                    success = self._process_single_transmission(
                        request, allocation
                    )
                    
                    if success:
                        successful_in_cycle += 1
                        self.successful_transmissions += 1
                        
                        # Recoger métricas de delay
                        delay = request.departure_time - request.created_at
                        self.delay_history.append({
                            'cycle': self.cycles_executed,
                            'time': self.simulation_time,
                            'delay': delay,
                            'onu_id': request.source_id
                        })
                        
                        # Recoger métricas de throughput
                        throughput = request.get_total_traffic()
                        self.throughput_history.append({
                            'cycle': self.cycles_executed,
                            'time': self.simulation_time,
                            'throughput': throughput,
                            'onu_id': request.source_id
                        })
                        
                    else:
                        failed_in_cycle += 1
                        self.failed_transmissions += 1
                        
                    self.total_requests_processed += 1
                    
            except Exception as e:
                print(f"Error procesando allocation para ONU {allocation.onu_id}: {e}")
                failed_in_cycle += len(allocation.requests_to_process)
                self.failed_transmissions += len(allocation.requests_to_process)
                
        # Actualizar resultado del ciclo
        dba_result.successful_transmissions = successful_in_cycle
        dba_result.failed_transmissions = failed_in_cycle
        
    def _process_single_transmission(self, request: Request, allocation: DBAAllocation) -> bool:
        """Procesar una transmisión individual"""
        try:
            # Simular transmisión usando la ONU correspondiente
            onu = self.network.onus[allocation.onu_id]
            
            # Calcular tiempo de transmisión basado en el time-slot
            transmission_time = allocation.time_slot_duration
            
            # Establecer departure_time - debe ser mayor que arrival_time
            departure_time = max(allocation.time_slot_start + transmission_time, request.created_at + 0.001)
            request.departure_time = departure_time
            
            # Simular transmisión (simplificado)
            # En una implementación más completa, aquí se haría la transmisión real
            success = True  # Por ahora asumimos éxito
            
            if success:
                # Remover request del buffer de la ONU
                if request in onu.buffer:
                    onu.buffer.remove(request)
                    
                # Actualizar estadísticas de la ONU (verificar que existe el atributo)
                if hasattr(onu, 'successful_transmissions'):
                    onu.successful_transmissions += 1
                
                # Actualizar clock del OLT
                self.network.clock = request.departure_time
                
            return success
            
        except Exception as e:
            print(f"Error en transmisión individual: {e}")
            return False
            
    def _collect_cycle_metrics(self, dba_result: DBAResult):
        """Recoger métricas del ciclo completado"""
        
        # Agregar resultado a historial
        self.cycle_history.append(dba_result)
        
        # Recoger niveles de buffer de todas las ONUs
        current_buffer_levels = {}
        for onu_id, onu in self.network.onus.items():
            buffer_occupancy = (len(onu.buffer) / onu.buffer_size) * 100 if onu.buffer_size > 0 else 0
            current_buffer_levels[onu_id] = buffer_occupancy
            
        self.buffer_levels_history.append({
            'cycle': self.cycles_executed,
            'time': self.simulation_time,
            'buffer_levels': current_buffer_levels
        })
        
        # Calcular utilización de red del ciclo
        if self.network.transmition_rate > 0:
            cycle_utilization = (dba_result.total_bandwidth_used / self.network.transmition_rate) * 100
            self.utilization_history.append({
                'cycle': self.cycles_executed,
                'time': self.simulation_time,
                'utilization': cycle_utilization
            })
            
        # Actualizar total de ancho de banda usado
        self.total_bandwidth_used += dba_result.total_bandwidth_used
        
    def _print_progress_log(self, cycle: int):
        """Imprimir log de progreso"""
        mean_delay = self.get_mean_delay()
        mean_throughput = self.get_mean_throughput()
        
        print(f"Ciclo {cycle}: t={self.simulation_time*1000:.1f}ms, "
              f"Delay: {mean_delay*1000:.2f}ms, "
              f"Throughput: {mean_throughput:.2f}MB/s, "
              f"Requests: {self.total_requests_processed}")
              
    def _calculate_final_statistics(self) -> Dict[str, Any]:
        """Calcular estadísticas finales de la simulación"""
        
        return {
            'cycles_executed': self.cycles_executed,
            'simulation_time': self.simulation_time,
            'total_requests_processed': self.total_requests_processed,
            'successful_transmissions': self.successful_transmissions,
            'failed_transmissions': self.failed_transmissions,
            'success_rate': (self.successful_transmissions / max(self.total_requests_processed, 1)) * 100,
            'mean_delay': self.get_mean_delay(),
            'mean_throughput': self.get_mean_throughput(),
            'total_bandwidth_used': self.total_bandwidth_used,
            'network_utilization': (self.total_bandwidth_used / (self.network.transmition_rate * self.simulation_time)) * 100 if self.simulation_time > 0 else 0
        }
        
    def get_mean_delay(self) -> float:
        """Obtener delay promedio"""
        if not self.delay_history:
            return 0.0
        return sum(entry['delay'] for entry in self.delay_history) / len(self.delay_history)
        
    def get_mean_throughput(self) -> float:
        """Obtener throughput promedio"""
        if not self.throughput_history:
            return 0.0
        return sum(entry['throughput'] for entry in self.throughput_history) / len(self.throughput_history)
        
    def get_simulation_summary(self) -> Dict[str, Any]:
        """Obtener resumen completo de la simulación"""
        
        # Procesar buffer_levels_history para formato de gráficos
        processed_buffer_history = []
        for entry in self.buffer_levels_history:
            processed_buffer_history.append(entry['buffer_levels'])
            
        return {
            'simulation_summary': {
                'simulation_stats': {
                    'total_steps': self.cycles_executed,
                    'simulation_time': self.simulation_time,
                    'total_requests': self.total_requests_processed,
                    'successful_requests': self.successful_transmissions,
                    'success_rate': (self.successful_transmissions / max(self.total_requests_processed, 1)) * 100
                },
                'performance_metrics': {
                    'mean_delay': self.get_mean_delay(),
                    'mean_throughput': self.get_mean_throughput(),
                    'network_utilization': (self.total_bandwidth_used / (self.network.transmition_rate * self.simulation_time)) * 100 if self.simulation_time > 0 else 0,
                    'total_capacity_served': self.total_bandwidth_used
                },
                'episode_metrics': {
                    'delays': self.delay_history,
                    'throughputs': self.throughput_history,
                    'buffer_levels_history': processed_buffer_history,
                    'total_transmitted': self.total_bandwidth_used,
                    'total_requests': self.total_requests_processed
                }
            }
        }
        
    def reset_simulation(self):
        """Reiniciar simulación"""
        self.simulation_time = 0.0
        self.cycles_executed = 0
        self.total_requests_processed = 0
        self.successful_transmissions = 0
        self.failed_transmissions = 0
        self.total_bandwidth_used = 0.0
        
        # Limpiar historiales
        self.cycle_history = []
        self.delay_history = []
        self.throughput_history = []
        self.buffer_levels_history = []
        self.utilization_history = []
        
        # Reiniciar gestor DBA
        self.dba_manager.reset_metrics()
        
        # Reiniciar red
        self.network.clock = 0.0
        self.network.reset_stats()
        
        # Reiniciar ONUs
        for onu in self.network.onus.values():
            onu.buffer.clear()
            onu.lost_packets_count = 0
            onu.total_requests_generated = 0
            onu.polls_received = 0