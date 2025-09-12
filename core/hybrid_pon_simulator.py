"""
Simulador PON Híbrido con arquitectura event-driven
Integración completa con sistema de métricas existente
"""

from typing import Dict, List, Optional, Any, Callable
import numpy as np
from .event_queue import EventQueue, EventType
from .hybrid_onu import HybridONU
from .hybrid_olt import HybridOLT
from .traffic_scenarios import get_traffic_scenario, calculate_realistic_lambda
from .pon_dba_interface import DBAAlgorithmInterface, FCFSDBAAlgorithm


class HybridPONSimulator:
    """
    Simulador PON con arquitectura híbrida event-driven
    Compatible con interfaz existente de PonLab
    """
    
    def __init__(self, num_onus: int = 4, traffic_scenario: str = "residential_medium",
                 dba_algorithm: Optional[DBAAlgorithmInterface] = None,
                 channel_capacity_mbps: float = 1024.0):
        """
        Args:
            num_onus: Número de ONUs en la red
            traffic_scenario: Escenario de tráfico a usar
            dba_algorithm: Algoritmo DBA (None = FCFS por defecto)
            channel_capacity_mbps: Capacidad del canal en Mbps
        """
        self.num_onus = num_onus
        self.traffic_scenario = traffic_scenario
        self.channel_capacity = channel_capacity_mbps
        
        # Componentes principales
        self.event_queue = EventQueue()
        self.onus = {}
        self.olt = None
        
        # Estado de simulación
        self.simulation_time = 0.0
        self.simulation_duration = 0.0
        self.is_running = False
        
        # Métricas compatibles con sistema existente
        self.metrics = {
            'delays': [],
            'throughputs': [],
            'buffer_levels_history': [],
            'total_transmitted': 0.0,
            'total_requests': 0,
            'successful_transmissions': 0,
            'failed_transmissions': 0,
            'utilization_history': []
        }
        
        # Callback para eventos
        self.event_callback = None
        
        # Inicializar componentes
        self._initialize_onus(traffic_scenario)
        self._initialize_olt(dba_algorithm)
    
    def _initialize_onus(self, traffic_scenario: str):
        """Inicializar ONUs con configuración del escenario"""
        scenario_config = get_traffic_scenario(traffic_scenario)
        
        self.onus = {}
        for i in range(self.num_onus):
            onu_id = str(i)
            
            # SLA diferenciado por ONU
            sla = 100.0 + i * 50.0  # 100, 150, 200, 250 Mbps
            lambda_rate = calculate_realistic_lambda(sla, scenario_config)
            
            self.onus[onu_id] = HybridONU(onu_id, lambda_rate, scenario_config)
    
    def _initialize_olt(self, dba_algorithm: Optional[DBAAlgorithmInterface]):
        """Inicializar OLT con algoritmo DBA"""
        if dba_algorithm is None:
            dba_algorithm = FCFSDBAAlgorithm()
        
        self.olt = HybridOLT(self.onus, dba_algorithm, self.channel_capacity)
    
    def run_simulation(self, duration_seconds: float, 
                      callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Ejecutar simulación por tiempo específico
        
        Args:
            duration_seconds: Duración de la simulación en segundos
            callback: Callback opcional para eventos
            
        Returns:
            Resultados de la simulación
        """
        self.simulation_duration = duration_seconds
        self.event_callback = callback
        self.is_running = True
        
        print(f"Iniciando simulación híbrida PON:")
        print(f"  Duración: {duration_seconds:.3f} segundos")
        print(f"  ONUs: {self.num_onus}")
        print(f"  Escenario: {self.traffic_scenario}")
        print(f"  Canal: {self.channel_capacity:.0f} Mbps")
        
        # Inicializar eventos
        self._initialize_events()
        
        # Bucle principal de eventos
        events_processed = 0
        last_progress_time = 0
        
        while (self.event_queue.has_events() and 
               self.event_queue.peek_next_time() <= duration_seconds and
               self.is_running):
            
            # Procesar siguiente evento
            event = self.event_queue.get_next_event()
            self.simulation_time = event.timestamp
            
            self._process_event(event)
            events_processed += 1
            
            # Progreso cada segundo simulado
            if self.simulation_time - last_progress_time >= 1.0:
                progress = (self.simulation_time / duration_seconds) * 100
                print(f"  Progreso: {progress:.1f}% (t={self.simulation_time:.3f}s, eventos={events_processed})")
                last_progress_time = self.simulation_time
            
            # Callback externo
            if self.event_callback:
                self.event_callback(event, self.simulation_time)
        
        # Finalizar simulación
        self.is_running = False
        final_results = self._calculate_final_results()
        
        print(f"Simulación completada:")
        print(f"  Tiempo simulado: {self.simulation_time:.6f}s")
        print(f"  Eventos procesados: {events_processed}")
        print(f"  Paquetes transmitidos: {self.metrics['successful_transmissions']}")
        performance_metrics = final_results['simulation_summary']['performance_metrics']
        print(f"  Throughput promedio: {performance_metrics['mean_throughput']:.3f} MB/s")
        print(f"  Utilización promedio: {performance_metrics['network_utilization']:.2f}%")
        
        return final_results
    
    def _initialize_events(self):
        """Inicializar eventos iniciales"""
        start_time = 0.0
        
        # Programar primer paquete para cada ONU
        for onu in self.onus.values():
            onu.schedule_first_packet(self.event_queue, start_time)
        
        # Programar primer ciclo de polling
        self.olt.schedule_first_polling(self.event_queue, start_time)
    
    def _process_event(self, event):
        """Procesar un evento específico"""
        try:
            if event.event_type == EventType.PACKET_GENERATED:
                self._handle_packet_generation(event)
                
            elif event.event_type == EventType.POLLING_CYCLE:
                self._handle_polling_cycle(event)
                
            elif event.event_type == EventType.GRANT_START:
                self._handle_transmission_start(event)
                
            elif event.event_type == EventType.TRANSMISSION_COMPLETE:
                self._handle_transmission_complete(event)
                
        except Exception as e:
            print(f"Error procesando evento {event}: {e}")
    
    def _handle_packet_generation(self, event):
        """Manejar generación de paquete"""
        onu = self.onus[event.onu_id]
        onu.generate_packet(self.event_queue, event.timestamp)
    
    def _handle_polling_cycle(self, event):
        """Manejar ciclo de polling del OLT"""
        self.olt.execute_polling_cycle(self.event_queue, event.timestamp)
        
        # Actualizar métricas de buffer
        self._update_buffer_metrics()
    
    def _handle_transmission_start(self, event):
        """Manejar inicio de transmisión"""
        onu_id = event.onu_id
        tcont_id = event.data['tcont_id']
        grant_bytes = event.data['grant_bytes']
        slot_duration = event.data['slot_duration']
        slot_end = event.data['slot_end']
        
        # Transmitir paquetes
        onu = self.onus[onu_id]
        packets, transmitted_bytes = onu.transmit_from_queue(tcont_id, grant_bytes)
        
        # Programar completación
        self.event_queue.schedule_event(
            slot_end,
            EventType.TRANSMISSION_COMPLETE,
            onu_id,
            {
                'tcont_id': tcont_id,
                'packets': packets,
                'transmitted_bytes': transmitted_bytes,
                'grant_bytes': grant_bytes
            }
        )
    
    def _handle_transmission_complete(self, event):
        """Manejar completación de transmisión"""
        onu_id = event.onu_id
        packets = event.data.get('packets', [])
        transmitted_bytes = event.data.get('transmitted_bytes', 0)
        
        # Actualizar métricas por paquete
        for packet in packets:
            delay = event.timestamp - packet.arrival_time
            throughput_mbps = (packet.size_bytes / (1024 * 1024)) / delay if delay > 0 else 0
            
            self.metrics['delays'].append({
                'delay': delay,
                'onu_id': onu_id,
                'tcont_id': packet.tcont_type,
                'timestamp': event.timestamp
            })
            
            self.metrics['throughputs'].append({
                'throughput': throughput_mbps,
                'onu_id': onu_id,
                'tcont_id': packet.tcont_type,
                'timestamp': event.timestamp
            })
        
        # Actualizar contadores globales
        if transmitted_bytes > 0:
            self.metrics['successful_transmissions'] += len(packets)
            self.metrics['total_transmitted'] += transmitted_bytes / (1024 * 1024)  # MB
        else:
            self.metrics['failed_transmissions'] += 1
        
        self.metrics['total_requests'] += len(packets)
        
        # Notificar al OLT
        self.olt.handle_transmission_complete(event.data, event.timestamp)
    
    def _update_buffer_metrics(self):
        """Actualizar métricas de buffer en cada ciclo"""
        buffer_levels = {}
        
        for onu_id, onu in self.onus.items():
            # Calcular nivel total de buffer como % de capacidad máxima
            total_bytes = sum(queue.total_bytes for queue in onu.queues.values())
            max_capacity = sum(queue.max_bytes for queue in onu.queues.values())
            
            buffer_level = (total_bytes / max_capacity) * 100 if max_capacity > 0 else 0
            buffer_levels[onu_id] = buffer_level
        
        self.metrics['buffer_levels_history'].append(buffer_levels)
    
    def _calculate_final_results(self) -> Dict[str, Any]:
        """Calcular resultados finales en formato compatible"""
        
        # Calcular estadísticas básicas
        mean_delay = np.mean([d['delay'] for d in self.metrics['delays']]) if self.metrics['delays'] else 0
        mean_throughput = self.metrics['total_transmitted'] / self.simulation_time if self.simulation_time > 0 else 0
        
        # Calcular utilización de red
        olt_stats = self.olt.get_olt_statistics()
        network_utilization = olt_stats.get('average_utilization', 0)
        
        # Estadísticas por ONU
        onu_stats = {}
        for onu_id, onu in self.onus.items():
            onu_stats[onu_id] = onu.get_onu_statistics()
        
        return {
            'simulation_summary': {
                'simulation_stats': {
                    'total_steps': olt_stats['current_cycle'],
                    'simulation_time': self.simulation_time,
                    'total_requests': self.metrics['total_requests'],
                    'successful_requests': self.metrics['successful_transmissions'],
                    'success_rate': (self.metrics['successful_transmissions'] / max(self.metrics['total_requests'], 1)) * 100
                },
                'performance_metrics': {
                    'mean_delay': mean_delay,
                    'mean_throughput': mean_throughput,
                    'network_utilization': network_utilization,
                    'total_capacity_served': self.metrics['total_transmitted']
                },
                'episode_metrics': {
                    'delays': self.metrics['delays'],
                    'throughputs': self.metrics['throughputs'],
                    'buffer_levels_history': self.metrics['buffer_levels_history'],
                    'total_transmitted': self.metrics['total_transmitted'],
                    'total_requests': self.metrics['total_requests']
                }
            },
            'olt_stats': olt_stats,
            'onu_stats': onu_stats,
            'event_queue_stats': {
                'final_time': self.simulation_time,
                'events_remaining': self.event_queue.get_pending_events_count()
            }
        }
    
    def reset_simulation(self):
        """Reiniciar simulación manteniendo configuración"""
        self.event_queue.clear()
        self.simulation_time = 0.0
        self.is_running = False
        
        # Reiniciar métricas
        self.metrics = {
            'delays': [],
            'throughputs': [],
            'buffer_levels_history': [],
            'total_transmitted': 0.0,
            'total_requests': 0,
            'successful_transmissions': 0,
            'failed_transmissions': 0,
            'utilization_history': []
        }
        
        # Reiniciar componentes
        for onu in self.onus.values():
            onu.reset_statistics()
            onu.clear_queues()
        
        self.olt.reset_statistics()
    
    def set_dba_algorithm(self, dba_algorithm: DBAAlgorithmInterface):
        """Cambiar algoritmo DBA"""
        self.olt.set_dba_algorithm(dba_algorithm)
    
    def get_current_state(self) -> Dict[str, Any]:
        """Obtener estado actual (compatible con interfaz existente)"""
        buffer_levels = []
        for onu in self.onus.values():
            total_bytes = sum(queue.total_bytes for queue in onu.queues.values())
            max_capacity = sum(queue.max_bytes for queue in onu.queues.values())
            level = total_bytes / max_capacity if max_capacity > 0 else 0
            buffer_levels.append(level)
        
        return {
            'buffer_levels': buffer_levels,
            'sim_time': self.simulation_time,
            'total_transmitted': self.metrics['total_transmitted'],
            'total_requests': self.metrics['total_requests'],
            'is_running': self.is_running
        }