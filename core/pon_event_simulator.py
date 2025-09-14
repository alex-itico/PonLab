"""
Simulador PON Híbrido Optimizado con control de recursos
Versión mejorada que previene consumo excesivo de memoria y CPU
"""

from typing import Dict, List, Optional, Any, Callable
import numpy as np
from .event_queue import EventQueue, EventType
from .pon_event_onu import HybridONU
from .pon_event_olt import HybridOLT
from .pon_traffic import get_traffic_scenario, calculate_realistic_lambda
from .pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm


class OptimizedHybridPONSimulator:
    """
    Simulador PON Híbrido Optimizado con controles de recursos estrictos
    Previene consumo excesivo de memoria y CPU
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
        
        # Límites de recursos muy altos para permitir simulaciones completas
        self.MAX_EVENTS_IN_QUEUE = 1000000   # 1M eventos pendientes (muy alto)
        self.MAX_METRICS_STORED = 100000     # 100K métricas almacenadas
        self.MAX_BUFFER_HISTORY = 50000      # 50K historial de buffer
        self.MIN_CYCLE_INTERVAL = 125e-6  # 125us mínimo entre ciclos
        
        # Componentes principales
        self.event_queue = EventQueue()
        self.onus = {}
        self.olt = None
        
        # Estado de simulación
        self.simulation_time = 0.0
        self.simulation_duration = 0.0
        self.is_running = False
        self.events_processed = 0
        
        # Métricas optimizadas (con límites)
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
        
        # Estadísticas de optimización
        self.optimization_stats = {
            'events_dropped': 0,
            'metrics_dropped': 0,
            'buffer_samples_dropped': 0
        }
        
        # Callback para eventos
        self.event_callback = None
        
        # Inicializar componentes con tasas reducidas
        self._initialize_onus_optimized(traffic_scenario)
        self._initialize_olt(dba_algorithm)
    
    def _initialize_onus_optimized(self, traffic_scenario: str):
        """Inicializar ONUs con tasas de tráfico optimizadas"""
        scenario_config = get_traffic_scenario(traffic_scenario)
        
        self.onus = {}
        for i in range(self.num_onus):
            onu_id = str(i)
            
            # SLA diferenciado por ONU pero más moderado
            sla = 50.0 + i * 25.0  # 50, 75, 100, 125 Mbps (reducido)
            lambda_rate = calculate_realistic_lambda(sla, scenario_config)
            
            # Reducir lambda rate para evitar explosión de eventos
            lambda_rate = min(lambda_rate, 50.0)  # Máximo 50 paquetes/segundo
            
            self.onus[onu_id] = HybridONU(onu_id, lambda_rate, scenario_config)
    
    def _initialize_olt(self, dba_algorithm: Optional[DBAAlgorithmInterface]):
        """Inicializar OLT con ciclo optimizado"""
        if dba_algorithm is None:
            dba_algorithm = FCFSDBAAlgorithm()
        
        # Usar ciclos menos frecuentes para reducir carga computacional
        from .event_queue import CycleTimeManager, TimeSlotManager
        
        self.olt = HybridOLT(self.onus, dba_algorithm, self.channel_capacity)
        # Reemplazar el cycle manager con intervalo más largo
        self.olt.cycle_manager = CycleTimeManager(self.MIN_CYCLE_INTERVAL)  # 125us
    
    def run_simulation(self, duration_seconds: float, 
                      callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Ejecutar simulación optimizada por tiempo específico
        
        Args:
            duration_seconds: Duración de la simulación en segundos
            callback: Callback opcional para eventos
            
        Returns:
            Resultados de la simulación
        """
        # Sin límites de duración - permitir simulaciones del tiempo solicitado
        
        self.simulation_duration = duration_seconds
        self.event_callback = callback
        self.is_running = True
        
        print(f"Iniciando simulación híbrida optimizada:")
        print(f"  Duración: {duration_seconds:.3f} segundos")
        print(f"  ONUs: {self.num_onus}")
        print(f"  Escenario: {self.traffic_scenario}")
        print(f"  Canal: {self.channel_capacity:.0f} Mbps")
        print(f"  Ciclo DBA: {self.MIN_CYCLE_INTERVAL*1000000:.0f}us")
        
        # Inicializar eventos
        self._initialize_events()
        
        # Bucle principal de eventos con controles de recursos
        self.events_processed = 0
        last_progress_time = 0
        last_cleanup_time = 0
        
        while (self.event_queue.has_events() and 
               self.event_queue.peek_next_time() <= duration_seconds and
               self.is_running):
            
            # Control de recursos cada 1000 eventos
            if self.events_processed % 1000 == 0:
                if not self._check_resource_limits():
                    print(f"⚠️ Límites de recursos alcanzados en evento {self.events_processed}")
                    break
            
            # Procesar siguiente evento
            event = self.event_queue.get_next_event()
            self.simulation_time = event.timestamp
            
            self._process_event(event)
            self.events_processed += 1
            
            # Progreso cada segundo simulado
            if self.simulation_time - last_progress_time >= 1.0:
                progress = (self.simulation_time / duration_seconds) * 100
                print(f"  Progreso: {progress:.1f}% (t={self.simulation_time:.3f}s, eventos={self.events_processed})")
                last_progress_time = self.simulation_time
            
            # Limpieza periódica cada 5 segundos simulados
            if self.simulation_time - last_cleanup_time >= 5.0:
                self._periodic_cleanup()
                last_cleanup_time = self.simulation_time
            
            # Callback externo
            if self.event_callback:
                self.event_callback(event, self.simulation_time)
        
        # Finalizar simulación
        self.is_running = False
        final_results = self._calculate_final_results()
        
        print(f"Simulación completada:")
        print(f"  Tiempo simulado: {self.simulation_time:.6f}s")
        print(f"  Eventos procesados: {self.events_processed}")
        print(f"  Paquetes transmitidos: {self.metrics['successful_transmissions']}")
        
        if final_results.get('simulation_summary', {}).get('performance_metrics'):
            performance_metrics = final_results['simulation_summary']['performance_metrics']
            print(f"  Throughput promedio: {performance_metrics['mean_throughput']:.3f} MB/s")
            print(f"  Utilización promedio: {performance_metrics['network_utilization']:.2f}%")
        
        # Mostrar estadísticas de optimización
        if any(self.optimization_stats.values()):
            print(f"  Optimizaciones aplicadas:")
            if self.optimization_stats['events_dropped']:
                print(f"    Eventos descartados: {self.optimization_stats['events_dropped']}")
            if self.optimization_stats['metrics_dropped']:
                print(f"    Métricas descartadas: {self.optimization_stats['metrics_dropped']}")
        
        return final_results
    
    def _check_resource_limits(self) -> bool:
        """Verificar límites de recursos y aplicar limpieza si es necesario"""
        # Verificar cola de eventos - solo limpiar, no cortar simulación
        pending_events = self.event_queue.get_pending_events_count()
        if pending_events > self.MAX_EVENTS_IN_QUEUE:
            print(f"⚠️ Cola de eventos llena ({pending_events}), aplicando limpieza")
            self._clean_event_queue()
        
        # Verificar métricas acumuladas
        if len(self.metrics['delays']) > self.MAX_METRICS_STORED:
            self._clean_metrics()
        
        if len(self.metrics['buffer_levels_history']) > self.MAX_BUFFER_HISTORY:
            self._clean_buffer_history()
        
        return True
    
    def _clean_event_queue(self):
        """Limpiar eventos excesivos manteniendo los más importantes"""
        # Esta es una medida extrema - indica un problema de diseño
        # Por ahora, detener la simulación
        print("⚠️ Deteniendo simulación por exceso de eventos")
        self.is_running = False
        self.optimization_stats['events_dropped'] += self.event_queue.get_pending_events_count()
    
    def _clean_metrics(self):
        """Limpiar métricas manteniendo solo las más recientes"""
        # Mantener solo la mitad más reciente
        keep_count = self.MAX_METRICS_STORED // 2
        
        dropped = len(self.metrics['delays']) - keep_count
        self.metrics['delays'] = self.metrics['delays'][-keep_count:]
        self.metrics['throughputs'] = self.metrics['throughputs'][-keep_count:]
        
        self.optimization_stats['metrics_dropped'] += dropped
    
    def _clean_buffer_history(self):
        """Limpiar historial de buffer manteniendo solo lo más reciente"""
        keep_count = self.MAX_BUFFER_HISTORY // 2
        
        dropped = len(self.metrics['buffer_levels_history']) - keep_count
        self.metrics['buffer_levels_history'] = self.metrics['buffer_levels_history'][-keep_count:]
        
        self.optimization_stats['buffer_samples_dropped'] += dropped
    
    def _periodic_cleanup(self):
        """Limpieza periódica para mantener memoria bajo control"""
        import gc
        gc.collect()  # Forzar garbage collection
    
    def _initialize_events(self):
        """Inicializar eventos iniciales"""
        start_time = 0.0
        
        # Programar primer paquete para cada ONU con spread temporal
        for i, onu in enumerate(self.onus.values()):
            # Spread inicial para evitar picos
            spread_time = start_time + (i * 0.001)  # 1ms entre ONUs
            onu.schedule_first_packet(self.event_queue, spread_time)
        
        # Programar primer ciclo de polling
        self.olt.schedule_first_polling(self.event_queue, start_time)
    
    def _process_event(self, event):
        """Procesar un evento específico con control de recursos"""
        try:
            if event.event_type == EventType.PACKET_GENERATED:
                self._handle_packet_generation_optimized(event)
                
            elif event.event_type == EventType.POLLING_CYCLE:
                self._handle_polling_cycle(event)
                
            elif event.event_type == EventType.GRANT_START:
                self._handle_transmission_start(event)
                
            elif event.event_type == EventType.TRANSMISSION_COMPLETE:
                self._handle_transmission_complete(event)
                
        except Exception as e:
            print(f"Error procesando evento {event}: {e}")
    
    def _handle_packet_generation_optimized(self, event):
        """Manejar generación de paquete con control de tasa"""
        onu = self.onus[event.onu_id]
        
        # Verificar si debemos seguir generando paquetes
        if (self.event_queue.get_pending_events_count() < self.MAX_EVENTS_IN_QUEUE and
            event.timestamp < self.simulation_duration - 0.01):  # Parar 10ms antes del final
            
            onu.generate_packet(self.event_queue, event.timestamp)
        else:
            # No generar más paquetes para evitar explosión de eventos
            pass
    
    def _handle_polling_cycle(self, event):
        """Manejar ciclo de polling del OLT"""
        self.olt.execute_polling_cycle(self.event_queue, event.timestamp)
        
        # Actualizar métricas de buffer (muestreo reducido)
        if len(self.metrics['buffer_levels_history']) < self.MAX_BUFFER_HISTORY:
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
        """Manejar completación de transmisión con muestreo de métricas"""
        onu_id = event.onu_id
        packets = event.data.get('packets', [])
        transmitted_bytes = event.data.get('transmitted_bytes', 0)
        
        # Actualizar métricas con muestreo (no todos los paquetes)
        if len(self.metrics['delays']) < self.MAX_METRICS_STORED:
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
        else:
            # Solo contar, no almacenar detalles
            self.optimization_stats['metrics_dropped'] += len(packets)
        
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
        """Actualizar métricas de buffer en MB reales"""
        buffer_levels = {}
        
        for onu_id, onu in self.onus.items():
            # Calcular nivel total de buffer en MB reales
            total_bytes = sum(queue.total_bytes for queue in onu.queues.values())
            max_capacity = sum(queue.max_bytes for queue in onu.queues.values())
            
            # Convertir bytes a MB para métricas
            buffer_level_mb = total_bytes / (1024 * 1024)  # Bytes a MB
            max_capacity_mb = max_capacity / (1024 * 1024)  # Bytes a MB
            
            buffer_levels[onu_id] = {
                'used_mb': buffer_level_mb,
                'capacity_mb': max_capacity_mb,
                'utilization_percent': (total_bytes / max_capacity) * 100 if max_capacity > 0 else 0
            }
        
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
                    'success_rate': (self.metrics['successful_transmissions'] / max(self.metrics['total_requests'], 1)) * 100,
                    'events_processed': self.events_processed
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
            'optimization_stats': self.optimization_stats,
            'event_queue_stats': {
                'final_time': self.simulation_time,
                'events_remaining': self.event_queue.get_pending_events_count(),
                'events_processed': self.events_processed
            }
        }
    
    def reset_simulation(self):
        """Reiniciar simulación manteniendo configuración"""
        self.event_queue.clear()
        self.simulation_time = 0.0
        self.is_running = False
        self.events_processed = 0
        
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
        
        # Reiniciar estadísticas de optimización
        self.optimization_stats = {
            'events_dropped': 0,
            'metrics_dropped': 0,
            'buffer_samples_dropped': 0
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
        """Obtener estado actual con buffer en MB"""
        buffer_levels = []
        for onu in self.onus.values():
            total_bytes = sum(queue.total_bytes for queue in onu.queues.values())
            max_capacity = sum(queue.max_bytes for queue in onu.queues.values())
            
            # Retornar en MB en lugar de porcentaje
            used_mb = total_bytes / (1024 * 1024)
            capacity_mb = max_capacity / (1024 * 1024)
            
            buffer_levels.append({
                'used_mb': used_mb,
                'capacity_mb': capacity_mb,
                'utilization_percent': (total_bytes / max_capacity) * 100 if max_capacity > 0 else 0
            })
        
        return {
            'buffer_levels': buffer_levels,
            'sim_time': self.simulation_time,
            'total_transmitted': self.metrics['total_transmitted'],
            'total_requests': self.metrics['total_requests'],
            'is_running': self.is_running,
            'events_processed': self.events_processed,
            'optimization_stats': self.optimization_stats
        }