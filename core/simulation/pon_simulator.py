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
                             channel_capacity_mbps: float = 1024.0, use_sdn: bool = False):
        """
        Configurar simulación por eventos discretos
        
        Args:
            num_onus: Número de ONUs en la red
            traffic_scenario: Escenario de tráfico a usar
            dba_algorithm: Algoritmo DBA (None = FCFS por defecto)
            channel_capacity_mbps: Capacidad del canal en Mbps
            use_sdn: Si es True, usa OLT_SDN en lugar de HybridOLT
        """
        if self.simulation_mode != "events":
            raise ValueError("Este método solo funciona en modo 'events'")
            
        self.num_onus = num_onus
        self.traffic_scenario = traffic_scenario
        self.channel_capacity = channel_capacity_mbps
        
        # Inicializar ONUs con tráfico optimizado
        self._setup_onus(traffic_scenario)
        self._setup_olt(dba_algorithm, use_sdn)
        
        olt_type = "OLT_SDN" if use_sdn else "HybridOLT"
        print(f"Simulación por eventos configurada: {num_onus} ONUs, {traffic_scenario}, {channel_capacity_mbps} Mbps, {olt_type}")
    
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
    
    def _setup_olt(self, dba_algorithm: Optional[DBAAlgorithmInterface], use_sdn: bool = False):
        """Configurar OLT para simulación por eventos"""
        if dba_algorithm is None:
            dba_algorithm = FCFSDBAAlgorithm()
        
        from ..events.event_queue import CycleTimeManager
        from ..pon.pon_sdn import OLT_SDN
        
        if use_sdn:
            self.olt = OLT_SDN("OLT_SDN_1", self.onus, dba_algorithm, {"0": {"length": 0.5}, "1": {"length": 0.5}}, self.channel_capacity)
        else:
            # El OLT ejecuta polling automáticamente cada 125µs sin crear eventos
            self.olt = HybridOLT(self.onus, dba_algorithm, self.channel_capacity)
    
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

            # ANTES de procesar el evento, ejecutar polling automático si es necesario
            if hasattr(self.olt, 'check_and_execute_polling'):
                self.olt.check_and_execute_polling(self.event_queue, self.simulation_time)

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

                # Acumular bytes transmitidos (el throughput se calcula al final como bytes_totales/tiempo_total)
                # No calculamos throughput por paquete individual ya que no es una métrica útil
                self.total_throughput += request.size_bytes
            else:
                self.failed_transmissions += 1
    
    def _update_cycle_metrics(self, dba_result: DBAResult):
        """Actualizar métricas del ciclo incluyendo estado de buffers"""
        # Capturar estado actual de buffers de todas las ONUs
        buffer_states = {}
        for onu_id, onu in self.network.onus.items():
            buffer_occupancy = onu.get_buffer_occupancy()
            # Convertir a porcentaje de utilización
            buffer_size = getattr(onu, 'buffer_size', 100)  # Tamaño por defecto si no está definido
            buffer_percent = (buffer_occupancy / buffer_size) * 100 if buffer_size > 0 else 0
            buffer_states[onu_id] = {
                'utilization_percent': buffer_percent,
                'used_mb': buffer_occupancy / (1024 * 1024),  # Convertir a MB
                'capacity_mb': buffer_size / (1024 * 1024)
            }

        cycle_metric = {
            'cycle_number': dba_result.cycle_number,
            'cycle_time': dba_result.cycle_start_time,
            'total_requests': dba_result.total_requests_processed,
            'total_bandwidth': dba_result.total_bandwidth_used,
            'utilization': (dba_result.total_bandwidth_used / self.network.channel_capacity) * 100,
            'buffer_states': buffer_states  # Agregar estado de buffers
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

        # Throughput promedio = bytes_totales / tiempo_total (en MB/s)
        total_transmitted_mb = self.total_throughput / (1024 * 1024)
        avg_throughput = total_transmitted_mb / self.simulation_time if self.simulation_time > 0 else 0

        success_rate = (self.successful_transmissions / max(self.total_requests_processed, 1)) * 100

        # Generar historiales desde métricas de ciclo
        delay_history = self._generate_cycle_history_for_delays()
        throughput_history = self._generate_cycle_history_for_throughput()
        buffer_history = self._generate_cycle_history_for_buffers()  # ← Agregar historial de buffers

        return {
            'simulation_summary': {
                'simulation_stats': {
                    'total_steps': self.cycles_executed,
                    'simulation_time': self.simulation_time,
                    'simulation_duration': self.simulation_time,  # En cycles mode, son iguales
                    'total_requests': self.total_requests_processed,
                    'successful_requests': self.successful_transmissions,
                    'success_rate': success_rate
                },
                'performance_metrics': {
                    'mean_delay': avg_delay,
                    'mean_throughput': avg_throughput,
                    'network_utilization': 0  # TODO: calcular correctamente desde métricas del canal
                },
                'episode_metrics': {
                    'delays': [{'delay': avg_delay, 'timestamp': self.simulation_time}],
                    'throughputs': [{'throughput': avg_throughput, 'timestamp': self.simulation_time}],
                    'delay_history': delay_history,  # Historial agregado
                    'throughput_history': throughput_history,  # Historial agregado
                    'buffer_levels_history': buffer_history,  # ← Ahora con datos reales!
                    'total_transmitted': total_transmitted_mb,  # MB
                    'total_requests': self.total_requests_processed
                }
            },
            'cycle_metrics': self.cycle_metrics,
            'onu_metrics': self.onu_metrics
        }

    def _generate_cycle_history_for_delays(self) -> List[Dict[str, float]]:
        """Generar historial de delays desde cycle_metrics (modo cycles)"""
        if not self.cycle_metrics:
            return []

        # Agrupar en ~100 bins para gráficos suaves
        num_bins = min(100, max(10, len(self.cycle_metrics) // 10))
        bin_size = max(1, len(self.cycle_metrics) // num_bins)

        history = []
        for i in range(0, len(self.cycle_metrics), bin_size):
            chunk = self.cycle_metrics[i:i + bin_size]
            if chunk:
                avg_time = np.mean([c['cycle_time'] for c in chunk])
                # Estimar delay promedio del chunk (simplificado)
                avg_delay = self.total_delay / max(self.successful_transmissions, 1) * 1000  # ms

                history.append({
                    'time': avg_time,
                    'value': avg_delay
                })

        return history

    def _generate_cycle_history_for_throughput(self) -> List[Dict[str, float]]:
        """Generar historial de throughput desde cycle_metrics (modo cycles)"""
        if not self.cycle_metrics:
            return []

        # Agrupar en ~100 bins para gráficos suaves
        num_bins = min(100, max(10, len(self.cycle_metrics) // 10))
        bin_size = max(1, len(self.cycle_metrics) // num_bins)

        history = []
        for i in range(0, len(self.cycle_metrics), bin_size):
            chunk = self.cycle_metrics[i:i + bin_size]
            if chunk:
                avg_time = np.mean([c['cycle_time'] for c in chunk])
                avg_bandwidth = np.mean([c['total_bandwidth'] for c in chunk])

                history.append({
                    'time': avg_time,
                    'value': avg_bandwidth
                })

        return history

    def _generate_cycle_history_for_buffers(self) -> List[Dict[str, Any]]:
        """Generar historial de buffers desde cycle_metrics (modo cycles)"""
        print(f"[BUFFER-LOG] _generate_cycle_history_for_buffers() llamado")
        print(f"[BUFFER-LOG] Total cycle_metrics: {len(self.cycle_metrics)}")

        if not self.cycle_metrics:
            print(f"[BUFFER-LOG] ⚠️ cycle_metrics está vacío!")
            return []

        # Filtrar solo ciclos que tienen buffer_states
        cycles_with_buffers = [c for c in self.cycle_metrics if 'buffer_states' in c]
        print(f"[BUFFER-LOG] Ciclos con buffer_states: {len(cycles_with_buffers)}")

        if not cycles_with_buffers:
            print(f"[BUFFER-LOG] ⚠️ Ningún ciclo tiene 'buffer_states'!")
            return []

        # Agrupar en ~100 puntos para gráficos (muestrear cada N ciclos)
        num_samples = min(100, len(cycles_with_buffers))
        sample_interval = max(1, len(cycles_with_buffers) // num_samples)

        buffer_history = []
        for i in range(0, len(cycles_with_buffers), sample_interval):
            cycle = cycles_with_buffers[i]
            buffer_entry = {
                'time': cycle['cycle_time'],
                'buffers': cycle['buffer_states']
            }
            buffer_history.append(buffer_entry)

        print(f"[BUFFER-LOG] Buffer history generado: {len(buffer_history)} entries")
        if len(buffer_history) > 0:
            print(f"[BUFFER-LOG] Primera entrada: {buffer_history[0]}")

        return buffer_history
    
    # ===== MÉTODOS INTERNOS - EVENTOS DISCRETOS =====
    
    def _initialize_events(self):
        """Inicializar eventos para simulación por eventos discretos"""
        start_time = 0.0
        
        # Programar primer paquete para cada ONU
        for i, onu in enumerate(self.onus.values()):
            spread_time = start_time + (i * 0.001)  # 1ms entre ONUs
            onu.schedule_first_packet(self.event_queue, spread_time)

        # NO programar eventos de polling - ahora son automáticos
        # El polling se ejecutará automáticamente cada 125µs
    
    def _process_event(self, event):
        """Procesar evento en simulación por eventos discretos"""
        try:
            if event.event_type == EventType.PACKET_GENERATED:
                self._handle_packet_generation(event)
            elif event.event_type == EventType.TRANSMISSION_COMPLETE:
                self._handle_transmission_complete(event)
            # Ya NO hay eventos POLLING_CYCLE - el polling es automático
            # Ya NO hay eventos GRANT_START - OPCIÓN 1 fusiona GRANT_START + TRANSMISSION_COMPLETE
        except Exception as e:
            print(f"Error procesando evento {event}: {e}")
    
    def _handle_packet_generation(self, event):
        """Manejar generación de paquete - continúa generando independientemente del tamaño de la cola"""
        onu = self.onus[event.onu_id]

        # Generar paquete si aún estamos dentro del tiempo de simulación
        # NO verificamos el tamaño de la cola para mantener comportamiento determinista
        if event.timestamp < self.simulation_duration:
            onu.generate_packet(self.event_queue, event.timestamp)

            # Advertencia periódica si la cola crece mucho (pero NO detenemos la simulación)
            pending = self.event_queue.get_pending_events_count()
            if pending > self.MAX_EVENTS_IN_QUEUE and pending % 100000 == 0:
                print(f"⚠️ Advertencia: {pending} eventos pendientes en cola (tiempo simulado: {event.timestamp:.3f}s)")
    
    def _handle_polling_cycle(self, event):
        """Manejar ciclo de polling del OLT"""
        self.olt.execute_polling_cycle(self.event_queue, event.timestamp)

        if len(self.metrics['buffer_levels_history']) < self.MAX_BUFFER_HISTORY:
            self._update_buffer_metrics()

    # Método eliminado: _handle_transmission_start
    # OPCIÓN 1: Los eventos GRANT_START fueron eliminados
    # Ahora se extrae paquetes y se programa TRANSMISSION_COMPLETE directamente en el polling

    def _handle_transmission_complete(self, event):
        """Manejar completación de transmisión"""
        packets = event.data.get('packets', [])
        transmitted_bytes = event.data.get('transmitted_bytes', 0)

        # Tiempo de transmisión (slot duration)
        slot_duration = event.data.get('slot_duration', 0.0)
        slot_start = event.data.get('slot_start', event.timestamp)

        # --- 1) Registrar delays por paquete ---
        if len(self.metrics['delays']) < self.MAX_METRICS_STORED:
            for packet in packets:
                # Delay: desde que el paquete llegó hasta que termina la transmisión
                delay = event.timestamp - packet.arrival_time

                self.metrics['delays'].append({
                    'delay': delay,
                    'onu_id': event.onu_id,
                    'timestamp': event.timestamp,
                    'tcont_id': packet.tcont_type
                })
        else:
            self.optimization_stats['metrics_dropped'] += len(packets)

        # --- 2) Guardar datos de transmisión para calcular throughput agregado después ---
        # NO calculamos throughput por slot porque slot_duration = bytes/line_rate
        # lo que siempre daría line_rate (constante inútil)
        if transmitted_bytes > 0:
            # Guardar datos para agregación temporal posterior
            if len(self.metrics['throughputs']) < self.MAX_METRICS_STORED:
                self.metrics['throughputs'].append({
                    'timestamp': event.timestamp,
                    'transmitted_bytes': transmitted_bytes,
                    'onu_id': event.onu_id,
                    'tcont_id': event.data.get('tcont_id', 'unknown'),
                    'slot_duration': slot_duration,
                    'packets_count': len(packets)
                })
        
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
        """Actualizar métricas de buffer con timestamp"""
        buffer_levels = {}

        for onu_id, onu in self.onus.items():
            total_bytes = sum(queue.total_bytes for queue in onu.queues.values())
            max_capacity = sum(queue.max_bytes for queue in onu.queues.values())

            buffer_levels[onu_id] = {
                'used_mb': total_bytes / (1024 * 1024),
                'capacity_mb': max_capacity / (1024 * 1024),
                'utilization_percent': (total_bytes / max_capacity) * 100 if max_capacity > 0 else 0
            }

        # Agregar entrada con timestamp para graficación temporal
        buffer_entry = {
            'time': self.simulation_time,
            'buffers': buffer_levels
        }

        self.metrics['buffer_levels_history'].append(buffer_entry)
    
    def _check_resource_limits(self) -> bool:
        """Verificar límites de recursos y aplicar limpieza si es necesario"""
        # Verificar cola de eventos - SOLO advertir, NO detener la simulación
        # Las métricas deben ser independientes del tamaño de la cola
        pending_events = self.event_queue.get_pending_events_count()
        if pending_events > self.MAX_EVENTS_IN_QUEUE * 2:  # Advertir a 2x el límite
            if pending_events % 500000 == 0:  # Advertir cada 500k eventos
                print(f"⚠️ Alto uso de memoria: {pending_events} eventos pendientes (tiempo: {self.simulation_time:.3f}s)")

        # Verificar métricas acumuladas y limpiar si es necesario
        # Esto es solo para gestión de memoria, NO afecta el comportamiento de la simulación
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

        # Generar historiales agregados para gráficos en tiempo real
        delay_history = self._generate_time_series_history(self.metrics['delays'], 'delay')
        throughput_history = self._generate_throughput_history(self.metrics['throughputs'])

        return {
            'simulation_summary': {
                'simulation_stats': {
                    'total_steps': olt_stats.get('current_cycle', 0),
                    'simulation_time': self.simulation_time,
                    'simulation_duration': self.simulation_duration,  # Pasar duración real
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
                    'delay_history': delay_history,  # Nuevo: historial agregado
                    'throughput_history': throughput_history,  # Nuevo: historial agregado
                    'buffer_levels_history': self.metrics['buffer_levels_history'],
                    'total_transmitted': self.metrics['total_transmitted'],
                    'total_requests': self.metrics['total_requests']
                }
            },
            'olt_stats': olt_stats,
            'optimization_stats': self.optimization_stats
        }

    def _generate_throughput_history(self, transmissions_list: List[Dict]) -> List[Dict[str, float]]:
        """
        Generar historial de throughput agregando bytes en ventanas de tiempo

        Args:
            transmissions_list: Lista de transmisiones con 'timestamp' y 'transmitted_bytes'

        Returns:
            Lista de diccionarios con 'time' (s) y 'value' (MB/s)
        """
        if not transmissions_list or self.simulation_time == 0:
            return []

        # Determinar número de puntos de muestreo
        num_samples = min(200, max(50, int(self.simulation_time * 10)))
        time_window = self.simulation_time / num_samples

        # Inicializar bins de tiempo
        time_bins = []
        for i in range(num_samples):
            time_bins.append({
                'time': (i + 0.5) * time_window,
                'bytes': 0  # Acumular bytes, no promediar
            })

        # Acumular bytes por ventana de tiempo
        for transmission in transmissions_list:
            timestamp = transmission.get('timestamp', 0)
            transmitted_bytes = transmission.get('transmitted_bytes', 0)

            # Encontrar bin correspondiente
            bin_index = min(int(timestamp / time_window), num_samples - 1)
            time_bins[bin_index]['bytes'] += transmitted_bytes

        # Convertir bytes acumulados a throughput (MB/s)
        history = []
        for bin_data in time_bins:
            # Throughput = bytes_en_ventana / duración_ventana (en MB/s)
            throughput_mbps = (bin_data['bytes'] / (1024 * 1024)) / time_window
            history.append({
                'time': bin_data['time'],
                'value': throughput_mbps  # MB/s
            })

        return history

    def _generate_time_series_history(self, metrics_list: List[Dict], metric_key: str) -> List[Dict[str, float]]:
        """
        Generar historial de serie temporal agregando métricas en ventanas de tiempo

        Args:
            metrics_list: Lista de métricas con 'timestamp' y el metric_key
            metric_key: Clave de la métrica a agregar ('delay', 'throughput', etc.)

        Returns:
            Lista de diccionarios con 'time' y 'value' agregados por ventanas de tiempo
        """
        if not metrics_list or self.simulation_time == 0:
            return []

        # Determinar número de puntos de muestreo (máximo 200 puntos para gráficos suaves)
        num_samples = min(200, max(50, int(self.simulation_time * 10)))  # ~10 puntos por segundo
        time_window = self.simulation_time / num_samples

        # Inicializar bins de tiempo
        time_bins = []
        for i in range(num_samples):
            time_bins.append({
                'time': (i + 0.5) * time_window,  # Punto medio del intervalo
                'values': []
            })

        # Asignar métricas a bins de tiempo
        for metric in metrics_list:
            timestamp = metric.get('timestamp', 0)
            value = metric.get(metric_key, 0)

            # Convertir delay a ms si es necesario
            if metric_key == 'delay':
                value = value * 1000  # convertir a ms

            # Encontrar bin correspondiente
            bin_index = min(int(timestamp / time_window), num_samples - 1)
            time_bins[bin_index]['values'].append(value)

        # Calcular promedio por bin
        history = []
        for bin_data in time_bins:
            if bin_data['values']:
                avg_value = np.mean(bin_data['values'])
                history.append({
                    'time': bin_data['time'],
                    'value': avg_value
                })
            elif history:  # Si no hay datos, usar el último valor conocido
                history.append({
                    'time': bin_data['time'],
                    'value': history[-1]['value']
                })
            else:  # Primer bin sin datos
                history.append({
                    'time': bin_data['time'],
                    'value': 0
                })

        return history
    
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