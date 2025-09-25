"""
PON Simulator - Simulador unificado para redes PON
Combina simulación por ciclos DBA y por eventos discretos
"""

from typing import Optional, Dict, Any, List, Callable
import numpy as np
from ..pon.pon_olt import OLT
from ..algorithms.pon_dba_cycle import DBACycleManager, DBAResult, DBAAllocation
from ..data.pon_request import Request
from ..events.event_queue import EventQueue, EventType
from ..events.pon_event_onu import HybridONU
from ..events.pon_event_olt import HybridOLT
from ..utilities.pon_traffic import get_traffic_scenario, calculate_realistic_lambda
from ..algorithms.pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm


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


class PONSimulator:
    """
    Simulador PON unificado que soporta dos modos de operación:
    1. Simulación por ciclos DBA (modo clásico)
    2. Simulación por eventos discretos (modo avanzado)
    """
    
    def __init__(self, simulation_mode: str = "cycles"):
        """
        Args:
            simulation_mode: "cycles" para simulación por ciclos DBA, 
                           "events" para simulación por eventos discretos
        """
        self.simulation_mode = simulation_mode
        self.simulation_time = 0.0
        self.is_running = False
        
        # Componentes según el modo
        if simulation_mode == "cycles":
            self._init_cycle_mode()
        elif simulation_mode == "events":
            self._init_event_mode()
        else:
            raise ValueError(f"Modo de simulación no soportado: {simulation_mode}")
    
    def _init_cycle_mode(self):
        """Inicializar simulación por ciclos DBA"""
        self.network = None
        self.dba_manager = None
        self.cycles_executed = 0
        self.total_requests_processed = 0
        self.successful_transmissions = 0
        self.failed_transmissions = 0
        self.total_packets_queued = 0
        self.total_delay = 0.0
        self.total_throughput = 0.0
        
        # Métricas detalladas
        self.cycle_metrics = []
        self.onu_metrics = {}
    
    def _init_event_mode(self):
        """Inicializar simulación por eventos discretos"""
        self.num_onus = 4
        self.traffic_scenario = "residential_medium"
        self.channel_capacity = 1024.0
        self.events_processed = 0
        
        # Límites de recursos
        self.MAX_EVENTS_IN_QUEUE = 1000000
        self.MAX_METRICS_STORED = 100000
        self.MAX_BUFFER_HISTORY = 50000
        self.MIN_CYCLE_INTERVAL = 125e-6
        
        # Componentes
        self.event_queue = EventQueue()
        self.onus = {}
        self.olt = None
        
        # Métricas
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
    
    # ===== CONFIGURACIÓN =====
    
    def setup_cycle_simulation(self, network: OLT, cycle_duration: float = 0.000125):
        """
        Configurar simulación por ciclos DBA
        
        Args:
            network: Red PON (OLT) a simular
            cycle_duration: Duración de ciclo DBA en segundos (125us default)
        """
        if self.simulation_mode != "cycles":
            raise ValueError("Este método solo funciona en modo 'cycles'")
            
        self.network = network
        self.dba_manager = DBACycleManager(cycle_duration)
        print(f"Simulación por ciclos configurada: {cycle_duration*1000000:.0f}us por ciclo")
    
    def setup_event_simulation(self, num_onus: int = 4, traffic_scenario: str = "residential_medium",
                             dba_algorithm: Optional[DBAAlgorithmInterface] = None,
                             channel_capacity_mbps: float = 1024.0):
        """
        Configurar simulación por eventos discretos
        
        Args:
            num_onus: Número de ONUs en la red
            traffic_scenario: Escenario de tráfico a usar
            dba_algorithm: Algoritmo DBA (None = FCFS por defecto)
            channel_capacity_mbps: Capacidad del canal en Mbps
        """
        if self.simulation_mode != "events":
            raise ValueError("Este método solo funciona en modo 'events'")
            
        self.num_onus = num_onus
        self.traffic_scenario = traffic_scenario
        self.channel_capacity = channel_capacity_mbps
        
        # Inicializar ONUs con tráfico optimizado
        self._setup_onus(traffic_scenario)
        self._setup_olt(dba_algorithm)
        
        print(f"Simulación por eventos configurada: {num_onus} ONUs, {traffic_scenario}, {channel_capacity_mbps} Mbps")
    
    def _setup_onus(self, traffic_scenario: str):
        """Configurar ONUs para simulación por eventos"""
        scenario_config = get_traffic_scenario(traffic_scenario)
        
        self.onus = {}
        for i in range(self.num_onus):
            onu_id = str(i)
            
            # SLA diferenciado por ONU
            sla = 50.0 + i * 25.0  # 50, 75, 100, 125 Mbps
            lambda_rate = calculate_realistic_lambda(sla, scenario_config)
            
            # Limitar tasa para evitar sobrecarga
            lambda_rate = min(lambda_rate, 50.0)  # Máximo 50 paquetes/segundo
            
            self.onus[onu_id] = HybridONU(onu_id, lambda_rate, scenario_config)
    
    def _setup_olt(self, dba_algorithm: Optional[DBAAlgorithmInterface]):
        """Configurar OLT para simulación por eventos"""
        if dba_algorithm is None:
            dba_algorithm = FCFSDBAAlgorithm()
        
        from ..events.event_queue import CycleTimeManager
        
        self.olt = HybridOLT(self.onus, dba_algorithm, self.channel_capacity)
        self.olt.cycle_manager = CycleTimeManager(self.MIN_CYCLE_INTERVAL)
    
    # ===== EJECUCIÓN DE SIMULACIÓN =====
    
    def run_simulation(self, duration_or_steps, callback: Optional[Callable] = None):
        """
        Ejecutar simulación según el modo configurado
        
        Args:
            duration_or_steps: Duración en segundos (events) o número de pasos (cycles)
            callback: Callback opcional para eventos
        """
        if self.simulation_mode == "cycles":
            return self.run_cycle_simulation(duration_or_steps, callback)
        elif self.simulation_mode == "events":
            return self.run_event_simulation(duration_or_steps, callback)
    
    def run_cycle_simulation(self, timesteps: int, evaluator: Optional[EventEvaluator] = None):
        """Ejecutar simulación por ciclos DBA"""
        if not self.network or not self.dba_manager:
            raise ValueError("Simulación por ciclos no configurada")
        
        print(f"Iniciando simulación por ciclos: {timesteps} pasos")
        
        if evaluator:
            evaluator.on_init()
        
        self.is_running = True
        self.cycles_executed = 0
        
        for step in range(timesteps):
            if not self.is_running:
                break
                
            cycle_start_time = self.simulation_time
            
            if evaluator:
                evaluator.on_cycle_start(step, cycle_start_time)
            
            # Ejecutar ciclo DBA
            dba_result = self._execute_dba_cycle(step, cycle_start_time)
            
            if evaluator:
                evaluator.on_cycle_end(dba_result)
            
            # Actualizar métricas
            self._update_cycle_metrics(dba_result)
            
            # Avanzar tiempo de simulación
            self.simulation_time += self.dba_manager.cycle_duration
            self.cycles_executed += 1
            
            # Progress cada 1000 ciclos
            if step % 1000 == 0 and step > 0:
                print(f"  Progreso: {step}/{timesteps} ciclos ({(step/timesteps)*100:.1f}%)")
        
        self.is_running = False
        
        # Generar resumen final
        final_summary = self._generate_cycle_summary()
        
        if evaluator:
            evaluator.on_simulation_end(final_summary)
        
        print(f"Simulación por ciclos completada: {self.cycles_executed} ciclos")
        return True
    
    def run_event_simulation(self, duration_seconds: float, callback: Optional[Callable] = None):
        """Ejecutar simulación por eventos discretos"""
        if not self.onus or not self.olt:
            raise ValueError("Simulación por eventos no configurada")
        
        print(f"Iniciando simulación por eventos: {duration_seconds:.3f} segundos")
        
        self.simulation_duration = duration_seconds
        self.is_running = True
        self.events_processed = 0
        
        # Inicializar eventos
        self._initialize_events()
        
        # Bucle principal de eventos
        last_progress_time = 0
        
        while (self.event_queue.has_events() and 
               self.event_queue.peek_next_time() <= duration_seconds and
               self.is_running):
            
            # Control de recursos cada 1000 eventos
            if self.events_processed % 1000 == 0:
                if not self._check_resource_limits():
                    break
            
            # Procesar siguiente evento
            event = self.event_queue.get_next_event()
            self.simulation_time = event.timestamp
            
            self._process_event(event)
            self.events_processed += 1
            
            # Callback externo
            if callback:
                callback(event, self.simulation_time)
            
            # Progreso cada segundo simulado
            if self.simulation_time - last_progress_time >= 1.0:
                progress = (self.simulation_time / duration_seconds) * 100
                print(f"  Progreso: {progress:.1f}% (t={self.simulation_time:.3f}s, eventos={self.events_processed})")
                last_progress_time = self.simulation_time
        
        self.is_running = False
        
        # Generar resumen final
        final_results = self._generate_event_summary()
        
        print(f"Simulación por eventos completada: {self.simulation_time:.6f}s, {self.events_processed} eventos")
        return True, final_results
    
    # ===== MÉTODOS INTERNOS - CICLOS DBA =====
    
    def _execute_dba_cycle(self, cycle_number: int, cycle_start_time: float) -> DBAResult:
        """Ejecutar un ciclo DBA completo"""
        # Recopilar reportes de buffer de todas las ONUs
        reports = {}
        for onu_id, onu in self.network.onus.items():
            buffer_occupancy = onu.get_buffer_occupancy()
            reports[onu_id] = buffer_occupancy
        
        # Ejecutar algoritmo DBA
        dba_result = self.dba_manager.execute_dba_cycle(
            cycle_number=cycle_number,
            cycle_start_time=cycle_start_time,
            buffer_reports=reports,
            dba_algorithm=self.network.dba_algorithm
        )
        
        # Procesar transmisiones basadas en asignaciones
        for allocation in dba_result.allocations:
            self._process_transmission(allocation, cycle_start_time)
        
        return dba_result
    
    def _process_transmission(self, allocation: DBAAllocation, cycle_start_time: float):
        """Procesar transmisión de una ONU"""
        onu = self.network.get_onu(allocation.onu_id)
        if not onu:
            return
        
        # Transmitir paquetes según la asignación
        transmitted_requests = onu.transmit_requests(allocation.granted_bytes)
        
        # Actualizar métricas
        self.total_requests_processed += len(transmitted_requests)
        
        for request in transmitted_requests:
            if request.transmitted:
                self.successful_transmissions += 1
                delay = cycle_start_time - request.arrival_time
                self.total_delay += delay
                
                # Calcular throughput
                throughput = request.size_bytes / delay if delay > 0 else 0
                self.total_throughput += throughput
            else:
                self.failed_transmissions += 1
    
    def _update_cycle_metrics(self, dba_result: DBAResult):
        """Actualizar métricas del ciclo"""
        cycle_metric = {
            'cycle_number': dba_result.cycle_number,
            'cycle_time': dba_result.cycle_start_time,
            'total_requests': dba_result.total_requests_processed,
            'total_bandwidth': dba_result.total_bandwidth_used,
            'utilization': (dba_result.total_bandwidth_used / self.network.channel_capacity) * 100
        }
        
        self.cycle_metrics.append(cycle_metric)
        
        # Métricas por ONU
        for allocation in dba_result.allocations:
            onu_id = allocation.onu_id
            if onu_id not in self.onu_metrics:
                self.onu_metrics[onu_id] = {
                    'requests_processed': 0,
                    'bytes_transmitted': 0,
                    'grants_received': 0
                }
            
            self.onu_metrics[onu_id]['requests_processed'] += allocation.requests_processed
            self.onu_metrics[onu_id]['bytes_transmitted'] += allocation.granted_bytes
            self.onu_metrics[onu_id]['grants_received'] += 1
    
    def _generate_cycle_summary(self) -> Dict[str, Any]:
        """Generar resumen final de simulación por ciclos"""
        avg_delay = self.total_delay / max(self.successful_transmissions, 1)
        avg_throughput = self.total_throughput / max(self.successful_transmissions, 1)
        success_rate = (self.successful_transmissions / max(self.total_requests_processed, 1)) * 100
        
        return {
            'simulation_summary': {
                'simulation_stats': {
                    'total_steps': self.cycles_executed,
                    'simulation_time': self.simulation_time,
                    'total_requests': self.total_requests_processed,
                    'successful_requests': self.successful_transmissions,
                    'success_rate': success_rate
                },
                'performance_metrics': {
                    'mean_delay': avg_delay,
                    'mean_throughput': avg_throughput,
                    'network_utilization': (self.total_throughput / self.channel_capacity) * 100 if hasattr(self, 'channel_capacity') else 0
                },
                'episode_metrics': {
                    'delays': [{'delay': avg_delay, 'timestamp': self.simulation_time}],
                    'throughputs': [{'throughput': avg_throughput, 'timestamp': self.simulation_time}],
                    'buffer_levels_history': [],
                    'total_transmitted': self.total_throughput / (1024 * 1024),  # MB
                    'total_requests': self.total_requests_processed
                }
            },
            'cycle_metrics': self.cycle_metrics,
            'onu_metrics': self.onu_metrics
        }
    
    # ===== MÉTODOS INTERNOS - EVENTOS DISCRETOS =====
    
    def _initialize_events(self):
        """Inicializar eventos para simulación por eventos discretos"""
        start_time = 0.0
        
        # Programar primer paquete para cada ONU
        for i, onu in enumerate(self.onus.values()):
            spread_time = start_time + (i * 0.001)  # 1ms entre ONUs
            onu.schedule_first_packet(self.event_queue, spread_time)
        
        # Programar primer ciclo de polling
        self.olt.schedule_first_polling(self.event_queue, start_time)
    
    def _process_event(self, event):
        """Procesar evento en simulación por eventos discretos"""
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
        
        if (self.event_queue.get_pending_events_count() < self.MAX_EVENTS_IN_QUEUE and
            event.timestamp < self.simulation_duration - 0.01):
            onu.generate_packet(self.event_queue, event.timestamp)
    
    def _handle_polling_cycle(self, event):
        """Manejar ciclo de polling del OLT"""
        self.olt.execute_polling_cycle(self.event_queue, event.timestamp)
        
        if len(self.metrics['buffer_levels_history']) < self.MAX_BUFFER_HISTORY:
            self._update_buffer_metrics()
    
    def _handle_transmission_start(self, event):
        """Manejar inicio de transmisión"""
        onu_id = event.onu_id
        tcont_id = event.data['tcont_id']
        grant_bytes = event.data['grant_bytes']
        slot_end = event.data['slot_end']
        
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
        packets = event.data.get('packets', [])
        transmitted_bytes = event.data.get('transmitted_bytes', 0)
        
        # Actualizar métricas
        if len(self.metrics['delays']) < self.MAX_METRICS_STORED:
            for packet in packets:
                delay = event.timestamp - packet.arrival_time
                throughput_mbps = (packet.size_bytes / (1024 * 1024)) / delay if delay > 0 else 0
                
                self.metrics['delays'].append({
                    'delay': delay,
                    'onu_id': event.onu_id,
                    'timestamp': event.timestamp,
                    'tcont_id': packet.tcont_type
                })
                
                self.metrics['throughputs'].append({
                    'throughput': throughput_mbps,
                    'onu_id': event.onu_id,
                    'timestamp': event.timestamp,
                    'tcont_id': packet.tcont_type
                })
        else:
            self.optimization_stats['metrics_dropped'] += len(packets)
        
        # Actualizar contadores
        if transmitted_bytes > 0:
            self.metrics['successful_transmissions'] += len(packets)
            self.metrics['total_transmitted'] += transmitted_bytes / (1024 * 1024)
        else:
            self.metrics['failed_transmissions'] += 1
        
        self.metrics['total_requests'] += len(packets)
        
        # Notificar al OLT
        self.olt.handle_transmission_complete(event.data, event.timestamp)
    
    def _update_buffer_metrics(self):
        """Actualizar métricas de buffer"""
        buffer_levels = {}
        
        for onu_id, onu in self.onus.items():
            total_bytes = sum(queue.total_bytes for queue in onu.queues.values())
            max_capacity = sum(queue.max_bytes for queue in onu.queues.values())
            
            buffer_levels[onu_id] = {
                'used_mb': total_bytes / (1024 * 1024),
                'capacity_mb': max_capacity / (1024 * 1024),
                'utilization_percent': (total_bytes / max_capacity) * 100 if max_capacity > 0 else 0
            }
        
        self.metrics['buffer_levels_history'].append(buffer_levels)
    
    def _check_resource_limits(self) -> bool:
        """Verificar límites de recursos"""
        pending_events = self.event_queue.get_pending_events_count()
        if pending_events > self.MAX_EVENTS_IN_QUEUE:
            print(f"Cola de eventos llena ({pending_events}), deteniendo simulación")
            self.is_running = False
            return False
        
        if len(self.metrics['delays']) > self.MAX_METRICS_STORED:
            self._clean_metrics()
        
        return True
    
    def _clean_metrics(self):
        """Limpiar métricas para liberar memoria"""
        keep_count = self.MAX_METRICS_STORED // 2
        
        dropped = len(self.metrics['delays']) - keep_count
        self.metrics['delays'] = self.metrics['delays'][-keep_count:]
        self.metrics['throughputs'] = self.metrics['throughputs'][-keep_count:]
        
        self.optimization_stats['metrics_dropped'] += dropped
    
    def _generate_event_summary(self) -> Dict[str, Any]:
        """Generar resumen final de simulación por eventos"""
        mean_delay = np.mean([d['delay'] for d in self.metrics['delays']]) if self.metrics['delays'] else 0
        mean_throughput = self.metrics['total_transmitted'] / self.simulation_time if self.simulation_time > 0 else 0
        
        olt_stats = self.olt.get_olt_statistics() if self.olt else {}
        network_utilization = olt_stats.get('average_utilization', 0)
        
        return {
            'simulation_summary': {
                'simulation_stats': {
                    'total_steps': olt_stats.get('current_cycle', 0),
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
            'optimization_stats': self.optimization_stats
        }
    
    # ===== UTILIDADES =====
    
    def reset_simulation(self):
        """Reiniciar simulación manteniendo configuración"""
        self.simulation_time = 0.0
        self.is_running = False
        
        if self.simulation_mode == "cycles":
            self.cycles_executed = 0
            self.total_requests_processed = 0
            self.successful_transmissions = 0
            self.failed_transmissions = 0
            self.total_delay = 0.0
            self.total_throughput = 0.0
            self.cycle_metrics = []
            self.onu_metrics = {}
        
        elif self.simulation_mode == "events":
            self.event_queue.clear()
            self.events_processed = 0
            
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
            
            self.optimization_stats = {
                'events_dropped': 0,
                'metrics_dropped': 0,
                'buffer_samples_dropped': 0
            }
            
            # Reiniciar componentes
            for onu in self.onus.values():
                onu.reset_statistics()
                onu.clear_queues()
            
            if self.olt:
                self.olt.reset_statistics()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Obtener estado actual de la simulación"""
        if self.simulation_mode == "cycles":
            return {
                'simulation_time': self.simulation_time,
                'cycles_executed': self.cycles_executed,
                'total_requests_processed': self.total_requests_processed,
                'successful_transmissions': self.successful_transmissions,
                'is_running': self.is_running
            }
        
        elif self.simulation_mode == "events":
            buffer_levels = []
            for onu in self.onus.values():
                total_bytes = sum(queue.total_bytes for queue in onu.queues.values())
                max_capacity = sum(queue.max_bytes for queue in onu.queues.values())
                
                buffer_levels.append({
                    'used_mb': total_bytes / (1024 * 1024),
                    'capacity_mb': max_capacity / (1024 * 1024),
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
    
    def get_simulation_summary(self):
        """Obtener resumen de la simulación según el modo"""
        if self.simulation_mode == "cycles":
            return self._generate_cycle_summary()
        elif self.simulation_mode == "events":
            return self._generate_event_summary()
        else:
            return {}