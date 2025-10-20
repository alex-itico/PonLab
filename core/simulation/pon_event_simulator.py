"""
Simulador PON Híbrido Optimizado con control de recursos
Versión mejorada que previene consumo excesivo de memoria y CPU
"""

# FORZAR RECARGA - Import version check
from ._version_buffer_fix import VERSION, BUFFER_TIMESTAMPS_ENABLED
print(f"[BUFFER-LOG] ===== PON EVENT SIMULATOR LOADING - VERSION: {VERSION} =====")

from typing import Dict, List, Optional, Any, Callable
import numpy as np
from ..events.event_queue import EventQueue, EventType
from ..events.pon_event_onu import HybridONU
from ..events.pon_event_olt import HybridOLT
from ..utilities.pon_traffic import get_traffic_scenario, calculate_realistic_lambda
from ..algorithms.pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm


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
            'utilization_history': [],
            'per_onu_bytes': {},
            'event_queue_history': [],  # Nuevo: historial de eventos pendientes
        }
        
        # Estadísticas de optimización
        self.optimization_stats = {
            'events_dropped': 0,
            'metrics_dropped': 0,
            'buffer_samples_dropped': 0
        }

        # Contadores de diagnóstico
        self.event_type_counts = {
            'PACKET_GENERATED': 0,
            'GRANT_START': 0,
            'TRANSMISSION_COMPLETE': 0
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

            print(f"  ONU {onu_id}: lambda={lambda_rate:.1f} pkt/s (SLA={sla:.0f} Mbps)")

            self.onus[onu_id] = HybridONU(onu_id, lambda_rate, scenario_config)
    
    def _initialize_olt(self, dba_algorithm: Optional[DBAAlgorithmInterface]):
        """Inicializar OLT con polling automático cada 125µs"""
        if dba_algorithm is None:
            dba_algorithm = FCFSDBAAlgorithm()

        # El OLT ahora ejecuta polling automáticamente cada 125µs
        # sin necesidad de crear eventos en la cola
        self.olt = HybridOLT(
            self.onus,
            dba_algorithm,
            self.channel_capacity
        )
    
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
        
        # Inicializar eventos
        self._initialize_events()
        
        # Bucle principal de eventos con controles de recursos
        self.events_processed = 0
        last_progress_time = 0
        last_cleanup_time = 0
        last_queue_sample_time = 0

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

            # ANTES de procesar el evento, verificar si debemos ejecutar polling(s)
            # Esto ejecuta todos los ciclos de 125µs que deberían haber ocurrido
            # entre el último evento y este
            pollings_executed = self.olt.check_and_execute_polling(self.event_queue, self.simulation_time)

            # Ahora sí procesar el evento
            self._process_event(event)
            self.events_processed += 1

            # Muestrear métricas cada 0.1 segundos simulados
            if self.simulation_time - last_queue_sample_time >= 0.1:
                pending_events = self.event_queue.get_pending_events_count()
                self.metrics['event_queue_history'].append({
                    'time': self.simulation_time,
                    'pending_events': pending_events,
                    'events_processed': self.events_processed
                })

                # También actualizar métricas de buffer
                if len(self.metrics['buffer_levels_history']) < self.MAX_BUFFER_HISTORY:
                    self._update_buffer_metrics()

                last_queue_sample_time = self.simulation_time

            # Progreso cada segundo simulado
            if self.simulation_time - last_progress_time >= 1.0:
                progress = (self.simulation_time / duration_seconds) * 100
                pending_events = self.event_queue.get_pending_events_count()
                total_packets = sum(onu.total_packets_generated for onu in self.onus.values())
                grants = self.event_type_counts.get('GRANT_START', 0)
                print(f"  Progreso: {progress:.1f}% (t={self.simulation_time:.3f}s, eventos={self.events_processed}, paquetes={total_packets}, grants={grants})")
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

        if len(self.metrics['buffer_levels_history']) > self.MAX_BUFFER_HISTORY:
            self._clean_buffer_history()

        return True
    
    def _clean_event_queue(self):
        """
        DEPRECADO: Esta función ya no se usa
        La simulación ahora es determinista y NO detiene la generación de eventos
        independientemente del tamaño de la cola
        """
        pass
    
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

        # NO programar eventos de polling - ahora son automáticos
        # El polling se ejecutará automáticamente cada 125µs
    
    def _process_event(self, event):
        """Procesar un evento específico con control de recursos"""
        try:
            # Contar tipos de eventos para diagnóstico
            if event.event_type.value in self.event_type_counts:
                self.event_type_counts[event.event_type.value] += 1

            if event.event_type == EventType.PACKET_GENERATED:
                self._handle_packet_generation_optimized(event)

            elif event.event_type == EventType.TRANSMISSION_COMPLETE:
                self._handle_transmission_complete(event)

            # Ya NO hay eventos POLLING_CYCLE - el polling es automático
            # Ya NO hay eventos GRANT_START - OPCIÓN 1 fusiona GRANT_START + TRANSMISSION_COMPLETE

        except Exception as e:
            print(f"Error procesando evento {event}: {e}")
    
    def _handle_packet_generation_optimized(self, event):
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
    
    # Método eliminado: _handle_polling_cycle
    # El polling ahora es automático y se ejecuta antes de cada evento

    # Método eliminado: _handle_transmission_start
    # OPCIÓN 1: Los eventos GRANT_START fueron eliminados
    # Ahora se extrae paquetes y se programa TRANSMISSION_COMPLETE directamente en el polling

    def _handle_transmission_complete(self, event):
        """Manejar completación de transmisión con muestreo de métricas"""
        onu_id = event.onu_id
        data = event.data or {}

        packets = data.get('packets', [])
        transmitted_bytes = int(data.get('transmitted_bytes', 0))

        # Tiempo de transmisión (slot duration) y tiempo desde última transmisión
        slot_duration = data.get('slot_duration', 0.0)
        slot_start = data.get('slot_start', event.timestamp)
        slot_end = data.get('slot_end', event.timestamp)

        # --- 1) Muestreo de delays por paquete y throughput agregado por transmisión ---
        # Asegura que exista el contador de dropped
        if 'metrics_dropped' not in self.optimization_stats:
            self.optimization_stats['metrics_dropped'] = 0

        # Registrar delays por paquete (si hay espacio)
        if len(self.metrics['delays']) < self.MAX_METRICS_STORED:
            for packet in packets:
                # Delay: desde que el paquete llegó hasta que termina la transmisión
                delay = float(event.timestamp - packet.arrival_time)

                self.metrics['delays'].append({
                    'delay': delay,
                    'onu_id': onu_id,
                    'tcont_id': packet.tcont_type,
                    'timestamp': event.timestamp
                })
        else:
            # Solo contar delays no almacenados
            self.optimization_stats['metrics_dropped'] += len(packets)

        # Guardar información de transmisión para calcular throughput agregado después
        # NO calculamos throughput por slot individual porque slot_duration = bytes/line_rate
        # lo que siempre daría line_rate (constante inútil)
        if transmitted_bytes > 0:
            # Guardar datos de esta transmisión para agregación posterior
            if len(self.metrics['throughputs']) < self.MAX_METRICS_STORED:
                self.metrics['throughputs'].append({
                    'timestamp': event.timestamp,
                    'transmitted_bytes': transmitted_bytes,
                    'onu_id': onu_id,
                    'tcont_id': data.get('tcont_id', 'unknown'),
                    'slot_duration': slot_duration,
                    'packets_count': len(packets)
                })

        # --- 2) Contadores globales y fairness por ONU ---
        if transmitted_bytes > 0:
            # contabiliza éxito por cantidad de paquetes servidos en este slot
            self.metrics['successful_transmissions'] += len(packets)

            # total_transmitted en MB
            self.metrics['total_transmitted'] += transmitted_bytes / (1024 * 1024)

            # Acumula bytes por ONU para calcular fairness de Jain al final
            pob = self.metrics.get('per_onu_bytes', {})
            pob[onu_id] = pob.get(onu_id, 0) + transmitted_bytes
            self.metrics['per_onu_bytes'] = pob
        else:
            self.metrics['failed_transmissions'] += 1

        # Total de paquetes “atendidos” (o intentados) en este fin de grant
        self.metrics['total_requests'] += len(packets)

        # --- 3) Notificar al OLT (mantén tu lógica existente) ---
        self.olt.handle_transmission_complete(event.data, event.timestamp)

    
    def _update_buffer_metrics(self):
        """Actualizar métricas de buffer en MB reales con timestamp"""
        print(f"[BUFFER-LOG] _update_buffer_metrics() llamado en t={self.simulation_time:.3f}s")

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

        # Agregar entrada con timestamp para graficación temporal
        buffer_entry = {
            'time': self.simulation_time,
            'buffers': buffer_levels
        }

        self.metrics['buffer_levels_history'].append(buffer_entry)
        print(f"[BUFFER-LOG] Buffer entry agregado. Total entries: {len(self.metrics['buffer_levels_history'])}")
    
    def _calculate_throughput_time_series(self, window_size: float = 0.1) -> List[Dict]:
        """
        Calcular throughput agregado en ventanas de tiempo para visualización

        IMPORTANTE: Throughput = Bytes transmitidos en ventana / Duración de ventana
        Esto mide cuántos datos útiles se transmitieron por unidad de tiempo.

        Args:
            window_size: Tamaño de ventana en segundos (default: 0.1s = 100ms)

        Returns:
            Lista de {timestamp, throughput (MB/s), bytes_transmitted, transmissions_count}
        """
        if self.simulation_time == 0:
            return []

        # Crear ventanas de tiempo fijas
        num_windows = int(np.ceil(self.simulation_time / window_size))
        throughput_series = []

        for i in range(num_windows):
            window_start = i * window_size
            window_end = (i + 1) * window_size
            window_center = (window_start + window_end) / 2

            # Acumular TODOS los bytes transmitidos en esta ventana temporal
            bytes_in_window = 0
            transmissions_in_window = 0

            for transmission in self.metrics.get('throughputs', []):
                if window_start <= transmission['timestamp'] < window_end:
                    bytes_in_window += transmission['transmitted_bytes']
                    transmissions_in_window += 1

            # Throughput efectivo = bytes_totales_en_ventana / duración_ventana (en MB/s)
            # Esto captura el rendimiento real de la red en este período
            throughput_mbps = (bytes_in_window / (1024 * 1024)) / window_size

            throughput_series.append({
                'timestamp': window_center,
                'throughput': throughput_mbps,  # MB/s
                'bytes_transmitted': bytes_in_window,
                'transmissions_count': transmissions_in_window,
                'window_start': window_start,
                'window_end': window_end
            })

        return throughput_series

    def _extract_onu_buffer_histories_from_olt(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extraer historiales de buffer individuales por ONU desde los snapshots del OLT
        Convierte el formato agregado del OLT a historiales separados por ONU

        Returns:
            Dict de {onu_id: [list of samples]}
        """
        # Obtener snapshots del OLT
        olt_stats = self.olt.get_olt_statistics()
        buffer_snapshots = olt_stats.get('buffer_snapshots', [])

        print(f"[BUFFER-COLLECT-POLLING] Extrayendo historiales desde {len(buffer_snapshots)} snapshots del OLT")

        # Reorganizar por ONU
        onu_histories = {}

        for snapshot in buffer_snapshots:
            time = snapshot['time']
            buffers = snapshot['buffers']

            for onu_id, onu_data in buffers.items():
                if onu_id not in onu_histories:
                    onu_histories[onu_id] = []

                # Crear entrada para esta ONU en este timestamp
                entry = {
                    'time': time,
                    'buffer_state': onu_data.get('tconts', {}),
                    'total_used_mb': onu_data.get('total_used_mb', 0),
                    'total_capacity_mb': onu_data.get('total_capacity_mb', 0),
                    'total_utilization_percent': onu_data.get('total_utilization_percent', 0)
                }

                onu_histories[onu_id].append(entry)

        # Log resultado
        for onu_id, history in onu_histories.items():
            print(f"[BUFFER-COLLECT-POLLING] ONU {onu_id}: {len(history)} samples desde polling")

        total_samples = sum(len(h) for h in onu_histories.values())
        print(f"[BUFFER-COLLECT-POLLING] Total: {total_samples} samples de {len(onu_histories)} ONUs")

        return onu_histories

    def _convert_onu_histories_to_buffer_levels_history(self, onu_histories: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Convertir historiales organizados por ONU a formato de buffer_levels_history organizado por timestamp
        Esto permite que los graficos existentes usen los datos de polling

        Args:
            onu_histories: Dict de {onu_id: [list of samples with time]}

        Returns:
            Lista de snapshots con formato {'time': t, 'buffers': {onu_id: data}}
        """
        if not onu_histories:
            return []

        print(f"[BUFFER-CONVERT] Convirtiendo historiales de ONU a buffer_levels_history")

        # Recolectar todos los timestamps únicos
        all_timestamps = set()
        for onu_id, history in onu_histories.items():
            for entry in history:
                all_timestamps.add(entry['time'])

        # Ordenar timestamps
        sorted_timestamps = sorted(all_timestamps)

        print(f"[BUFFER-CONVERT] Encontrados {len(sorted_timestamps)} timestamps únicos")

        # Construir estructura organizada por timestamp
        buffer_levels_history = []

        for timestamp in sorted_timestamps:
            snapshot = {
                'time': timestamp,
                'buffers': {}
            }

            # Recolectar datos de cada ONU para este timestamp
            for onu_id, history in onu_histories.items():
                # Buscar la entrada con este timestamp
                for entry in history:
                    if entry['time'] == timestamp:
                        snapshot['buffers'][onu_id] = {
                            'used_mb': entry['total_used_mb'],
                            'capacity_mb': entry['total_capacity_mb'],
                            'utilization_percent': entry['total_utilization_percent']
                        }
                        break

            buffer_levels_history.append(snapshot)

        print(f"[BUFFER-CONVERT] Creados {len(buffer_levels_history)} snapshots para graficos")

        return buffer_levels_history

    def _calculate_final_results(self) -> Dict[str, Any]:
        """Calcular resultados finales en formato compatible"""

        # --- Delays y métricas derivadas ---
        delays_list = [d['delay'] for d in self.metrics.get('delays', [])]
        mean_delay = float(np.mean(delays_list)) if delays_list else 0.0
        p95_delay = float(np.percentile(delays_list, 95)) if delays_list else 0.0

        # Jitter estilo IPDV: promedio de |Δdelay| por ONU (diferencias sucesivas)
        mean_jitter = 0.0
        if self.metrics.get('delays'):
            by_onu = {}
            for d in self.metrics['delays']:
                by_onu.setdefault(d['onu_id'], []).append(d['delay'])
            ipdv_samples = []
            for seq in by_onu.values():
                if len(seq) > 1:
                    # Si tus delays ya llegan en orden temporal, no es necesario ordenar
                    diffs = [abs(seq[i] - seq[i-1]) for i in range(1, len(seq))]
                    ipdv_samples.extend(diffs)
            mean_jitter = float(np.mean(ipdv_samples)) if ipdv_samples else 0.0

        # Throughput medio (MB/s) ya acumulado
        mean_throughput = (self.metrics.get('total_transmitted', 0.0) / self.simulation_time) if self.simulation_time > 0 else 0.0

        # Throughput en serie de tiempo (para visualización)
        throughput_time_series = self._calculate_throughput_time_series(window_size=0.1)

        # Utilización de red (si no viene, usa 0)
        olt_stats = self.olt.get_olt_statistics()
        network_utilization = olt_stats.get('average_utilization', 0.0)

        # Fairness de Jain por ONU con bytes transmitidos acumulados
        per_onu = list(self.metrics.get('per_onu_bytes', {}).values())
        if per_onu:
            x = np.array(per_onu, dtype=float)
            jain = float((x.sum() ** 2) / (len(x) * (x ** 2).sum())) if (x ** 2).sum() > 0 else 1.0
        else:
            jain = 1.0  # neutral si nadie transmitió

        # Estadísticas por ONU
        onu_stats = {}
        for onu_id, onu in self.onus.items():
            onu_stats[onu_id] = onu.get_onu_statistics()

        total_requests = self.metrics.get('total_requests', 0)
        successful = self.metrics.get('successful_transmissions', 0)

        # Extraer buffer histories individuales desde los snapshots del OLT
        onu_buffer_histories = self._extract_onu_buffer_histories_from_olt()

        # Convertir a formato buffer_levels_history para compatibilidad con graficos
        buffer_levels_history = self._convert_onu_histories_to_buffer_levels_history(onu_buffer_histories)

        return {
            'simulation_summary': {
                'simulation_stats': {
                    'total_steps': olt_stats.get('current_cycle', 0),
                    'simulation_time': self.simulation_time,
                    'total_requests': total_requests,
                    'successful_requests': successful,
                    'success_rate': (successful / max(total_requests, 1)) * 100.0,
                    'events_processed': self.events_processed
                },
                'performance_metrics': {
                    'mean_delay': mean_delay,
                    'p95_delay': p95_delay,
                    'jitter_ipdv_mean': mean_jitter,
                    'mean_throughput': mean_throughput,
                    'network_utilization': network_utilization,
                    'total_capacity_served': self.metrics.get('total_transmitted', 0.0),
                    'jain_fairness_per_onu': jain,
                },
                'episode_metrics': {
                    'delays': self.metrics.get('delays', []),
                    'throughputs': self.metrics.get('throughputs', []),  # Throughput por transmisión (ruidoso)
                    'throughput_time_series': throughput_time_series,  # Throughput suavizado en ventanas
                    'buffer_levels_history': buffer_levels_history,  # Datos desde polling convertidos a formato para graficos
                    'event_queue_history': self.metrics.get('event_queue_history', []),
                    'total_transmitted': self.metrics.get('total_transmitted', 0.0),
                    'total_requests': total_requests
                }
            },
            'olt_stats': olt_stats,
            'onu_stats': onu_stats,
            'onu_buffer_histories': onu_buffer_histories,  # Formato detallado por ONU
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
            'utilization_history': [],
            'per_onu_bytes': {},
            'event_queue_history': [],
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