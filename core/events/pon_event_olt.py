"""
OLT híbrido con polling determinístico y asignación secuencial de grants
Arquitectura event-driven con control temporal estricto
"""

from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from .event_queue import EventQueue, EventType, TimeSlotManager, CycleTimeManager
from .pon_event_onu import HybridONU

if TYPE_CHECKING:
    from ..algorithms.pon_dba import DBAAlgorithmInterface


class HybridOLT:
    """
    OLT con arquitectura híbrida event-driven
    Polling determinístico cada 125us + asignación secuencial de grants
    """
    
    def __init__(self, onus: Dict[str, HybridONU],
                 dba_algorithm: Optional['DBAAlgorithmInterface'] = None,
                 channel_capacity_mbps: float = 1024.0,
                 guard_time_s: float = 2e-6):
        """
        Args:
            onus: Diccionario de ONUs {onu_id: HybridONU}
            dba_algorithm: Algoritmo DBA a usar
            channel_capacity_mbps: Capacidad del canal en Mbps
            guard_time_s: Tiempo de guarda entre transmisiones
        """
        self.onus = onus
        if dba_algorithm is None:
            # Lazy import to avoid circular dependency
            from ..algorithms.pon_dba import FCFSDBAAlgorithm
            self.dba_algorithm = FCFSDBAAlgorithm()
        else:
            self.dba_algorithm = dba_algorithm
        self.channel_capacity = channel_capacity_mbps
        self.guard_time_s = guard_time_s

        # Configuración de polling automático
        self.cycle_duration = 125e-6  # 125us por ciclo

        # Gestores de tiempo
        self.cycle_manager = CycleTimeManager(self.cycle_duration)
        self.slot_manager = TimeSlotManager(channel_capacity_mbps)

        # Estado del OLT
        self.current_cycle = 0
        self.last_reports = {}
        self.pending_grants = {}

        # Control de polling sin eventos
        self.last_polling_time = 0.0  # Último momento en que se ejecutó polling
        self.next_polling_time = self.cycle_duration  # Próximo polling esperado

        # Estadísticas
        self.stats = {
            'cycles_executed': 0,
            'reports_collected': 0,
            'grants_assigned': 0,
            'total_grants_bytes': 0,
            'successful_transmissions': 0,
            'failed_transmissions': 0,
            'channel_utilization_samples': []
        }

        print(f"  OLT: Polling automático cada {self.cycle_duration*1e6:.0f}us (sin eventos en cola)")
    
    def check_and_execute_polling(self, event_queue: EventQueue, current_time: float):
        """
        Verificar si es necesario ejecutar polling y ejecutarlo automáticamente
        Este método se llama ANTES de procesar cada evento

        Args:
            event_queue: Cola de eventos del simulador
            current_time: Tiempo actual de la simulación (timestamp del próximo evento)

        Returns:
            Número de ciclos de polling ejecutados
        """
        cycles_executed = 0

        # Verificar si han pasado 125µs o más desde el último polling
        while current_time >= self.next_polling_time:
            # Ejecutar un ciclo de polling SIN crear evento
            self._execute_single_polling_cycle(event_queue, self.next_polling_time)

            # Actualizar tiempos
            self.last_polling_time = self.next_polling_time
            self.next_polling_time += self.cycle_duration
            cycles_executed += 1

        return cycles_executed
    
    def _execute_single_polling_cycle(self, event_queue: EventQueue, cycle_time: float):
        """
        Ejecutar un único ciclo de DBA sin crear eventos en la cola
        Este método es llamado automáticamente cuando pasan 125µs

        Args:
            event_queue: Cola de eventos del simulador
            cycle_time: Tiempo exacto del ciclo (múltiplo de 125µs)
        """
        # FASE 1: Recolectar reports (0-40us del ciclo)
        reports = self._collect_reports()

        # FASE 2: Ejecutar DBA (40-50us del ciclo)
        grants = self._execute_dba_algorithm(reports, cycle_time)

        # FASE 3: Programar transmisiones (50-125us del ciclo)
        # Solo programar transmisiones si hay grants
        if grants:
            phases = self.cycle_manager.get_cycle_phases(cycle_time)
            transmission_start = phases['transmission_phase'][0]
            # OPCIÓN 1: Usar método fusionado que extrae paquetes y programa TRANSMISSION_COMPLETE directamente
            self._schedule_transmissions_directly(event_queue, grants, transmission_start)

        # Actualizar estadísticas del ciclo
        self.current_cycle += 1
        self.stats['cycles_executed'] += 1
        self.stats['reports_collected'] += len(reports)
        
    def _collect_reports(self) -> Dict[str, Dict[str, int]]:
        """
        Recolectar reports de estado de todas las ONUs
        
        Returns:
            Dict de {onu_id: {tcont_id: bytes}}
        """
        reports = {}
        
        for onu_id, onu in self.onus.items():
            # Obtener solo contadores (no datos reales)
            onu_report = onu.get_queue_status()
            if any(bytes_count > 0 for bytes_count in onu_report.values()):
                reports[onu_id] = onu_report
        
        self.last_reports = reports.copy()
        return reports
    
    def _execute_dba_algorithm(self, reports: Dict[str, Dict[str, int]], 
                              current_time: float) -> Dict[str, Dict[str, int]]:
        """
        Ejecutar algoritmo DBA con reports de todas las ONUs
        
        Args:
            reports: Reports recolectados de las ONUs
            current_time: Tiempo actual
            
        Returns:
            Grants asignados {onu_id: {tcont_id: bytes}}
        """
        if not reports:
            return {}
        
        # Calcular demanda total agregada por ONU
        onu_demands = {}
        for onu_id, onu_report in reports.items():
            total_demand = sum(onu_report.values())
            if total_demand > 0:
                onu_demands[onu_id] = total_demand / (1024 * 1024)  # Convertir a MB
        
        if not onu_demands:
            return {}
        
        # Ejecutar DBA con demanda agregada
        allocations = self.dba_algorithm.allocate_bandwidth(
            onu_demands,
            self.channel_capacity,
            None  # Por ahora sin RL action
        )
        
        # Convertir allocations en grants específicos por T-CONT
        grants = self._convert_allocations_to_grants(allocations, reports)
        
        self.stats['grants_assigned'] += len(grants)
        self.stats['total_grants_bytes'] += sum(
            sum(tcont_grants.values()) for tcont_grants in grants.values()
        )
        
        return grants
    
    def _convert_allocations_to_grants(self, allocations: Dict[str, float],
                                     reports: Dict[str, Dict[str, int]]) -> Dict[str, Dict[str, int]]:
        """
        Convertir allocations del DBA en grants específicos por T-CONT
        
        Args:
            allocations: Allocations del DBA {onu_id: MB_allocated}
            reports: Reports originales {onu_id: {tcont_id: bytes}}
            
        Returns:
            Grants específicos {onu_id: {tcont_id: bytes}}
        """
        grants = {}
        
        for onu_id, allocated_mb in allocations.items():
            if onu_id not in reports or allocated_mb <= 0:
                continue
            
            allocated_bytes = int(allocated_mb * 1024 * 1024)  # MB a bytes
            onu_report = reports[onu_id]
            
            # Distribuir bytes según prioridades T-CONT
            onu_grants = self._distribute_grant_by_priority(onu_report, allocated_bytes)
            
            if any(grant > 0 for grant in onu_grants.values()):
                grants[onu_id] = onu_grants
        
        return grants
    
    def _distribute_grant_by_priority(self, onu_report: Dict[str, int],
                                    total_grant_bytes: int) -> Dict[str, int]:
        """
        Distribuir grant entre T-CONTs según prioridades
        
        Args:
            onu_report: Report de la ONU {tcont_id: bytes}
            total_grant_bytes: Total de bytes a distribuir
            
        Returns:
            Grants por T-CONT {tcont_id: bytes}
        """
        # Orden de prioridad (highest primero)
        priority_order = ['highest', 'high', 'medium', 'low', 'lowest']
        grants = {tcont: 0 for tcont in priority_order}
        
        remaining_bytes = total_grant_bytes
        
        # Asignar por prioridad
        for tcont in priority_order:
            if remaining_bytes <= 0:
                break
            
            demand = onu_report.get(tcont, 0)
            if demand > 0:
                granted = min(demand, remaining_bytes)
                grants[tcont] = granted
                remaining_bytes -= granted
        
        return grants
    
    def _schedule_sequential_transmissions(self, event_queue: EventQueue,
                                         grants: Dict[str, Dict[str, int]],
                                         transmission_start: float):
        """
        Programar transmisiones secuenciales sin colisiones
        
        Args:
            event_queue: Cola de eventos del simulador
            grants: Grants asignados
            transmission_start: Tiempo de inicio de transmisiones
        """
        current_slot_start = transmission_start
        
        # Procesar grants en orden de prioridad global
        scheduled_grants = self._prioritize_grants(grants)
        
        for onu_id, tcont_id, grant_bytes in scheduled_grants:
            if grant_bytes <= 0:
                continue
            
            # Calcular time-slot sin colisiones
            grant_mb = grant_bytes / (1024 * 1024)
            slot_start, slot_end = self.slot_manager.allocate_time_slot(
                onu_id, tcont_id, grant_mb, current_slot_start
            )
            
            gt = getattr(self, 'guard_time_s', 0.0)
            slot_end_with_guard = slot_end + gt
            slot_duration_with_guard = slot_end_with_guard - slot_start
            
            # Programar inicio de transmisión
            event_queue.schedule_event(
                slot_start,
                EventType.GRANT_START,
                onu_id,
                {
                    'tcont_id': tcont_id,
                    'grant_bytes': grant_bytes,
                    'slot_duration': slot_duration_with_guard,
                    'slot_end': slot_end_with_guard,
                    'line_rate_bps': self.channel_capacity * 1e6,
                    'guard_time_s': gt
                }
            )
            
            current_slot_start = slot_end_with_guard  # Próximo slot después de este
    
    def _prioritize_grants(self, grants: Dict[str, Dict[str, int]]) -> List[Tuple[str, str, int]]:
        """
        Ordenar grants por prioridad global

        Args:
            grants: Grants por ONU y T-CONT

        Returns:
            Lista de (onu_id, tcont_id, grant_bytes) ordenada por prioridad
        """
        priority_map = {'highest': 1, 'high': 2, 'medium': 3, 'low': 4, 'lowest': 5}
        scheduled_grants = []

        for onu_id, onu_grants in grants.items():
            for tcont_id, grant_bytes in onu_grants.items():
                if grant_bytes > 0:
                    priority = priority_map.get(tcont_id, 6)
                    scheduled_grants.append((priority, onu_id, tcont_id, grant_bytes))

        # Ordenar por prioridad (1=highest, 5=lowest)
        scheduled_grants.sort(key=lambda x: x[0])

        # Retornar sin prioridad
        return [(onu_id, tcont_id, grant_bytes)
                for _, onu_id, tcont_id, grant_bytes in scheduled_grants]

    def _schedule_transmissions_directly(self, event_queue: EventQueue,
                                        grants: Dict[str, Dict[str, int]],
                                        transmission_start: float):
        """
        Programar transmisiones directamente como TRANSMISSION_COMPLETE
        OPCIÓN 1: Fusiona GRANT_START + TRANSMISSION_COMPLETE en un solo evento

        Este método:
        1. Extrae paquetes de las colas de las ONUs
        2. Calcula time-slots sin colisiones
        3. Programa eventos TRANSMISSION_COMPLETE directamente (sin GRANT_START)

        Args:
            event_queue: Cola de eventos del simulador
            grants: Grants asignados
            transmission_start: Tiempo de inicio de transmisiones
        """
        current_slot_start = transmission_start

        # Procesar grants en orden de prioridad global
        scheduled_grants = self._prioritize_grants(grants)

        for onu_id, tcont_id, grant_bytes in scheduled_grants:
            if grant_bytes <= 0:
                continue

            # Calcular time-slot sin colisiones
            grant_mb = grant_bytes / (1024 * 1024)
            slot_start, slot_end = self.slot_manager.allocate_time_slot(
                onu_id, tcont_id, grant_mb, current_slot_start
            )

            gt = getattr(self, 'guard_time_s', 0.0)
            slot_end_with_guard = slot_end + gt
            slot_duration_with_guard = slot_end_with_guard - slot_start

            # NUEVO: Extraer paquetes inmediatamente (lo que antes hacía GRANT_START)
            onu = self.onus[onu_id]
            packets, transmitted_bytes = onu.transmit_from_queue(tcont_id, grant_bytes)

            # Programar TRANSMISSION_COMPLETE directamente (saltando GRANT_START)
            event_queue.schedule_event(
                slot_end_with_guard,
                EventType.TRANSMISSION_COMPLETE,
                onu_id,
                {
                    'tcont_id': tcont_id,
                    'packets': packets,
                    'transmitted_bytes': transmitted_bytes,
                    'grant_bytes': grant_bytes,
                    'slot_start': slot_start,
                    'slot_end': slot_end_with_guard,
                    'slot_duration': slot_duration_with_guard,
                    'line_rate_bps': self.channel_capacity * 1e6,
                    'guard_time_s': gt
                }
            )

            current_slot_start = slot_end_with_guard  # Próximo slot después de este

    def handle_transmission_complete(self, event_data: Dict[str, Any], 
                                   completion_time: float):
        """
        Manejar completación de transmisión
        
        Args:
            event_data: Datos del evento de transmisión
            completion_time: Tiempo de completación
        """
        onu_id = event_data.get('onu_id')
        transmitted_bytes = event_data.get('transmitted_bytes', 0)
        
        if transmitted_bytes > 0:
            self.stats['successful_transmissions'] += 1
        else:
            self.stats['failed_transmissions'] += 1
        
        # Calcular utilización del canal para este ciclo específico
        if self.current_cycle > 0:
            cycle_duration = self.cycle_manager.cycle_duration
            
            # Obtener transmisiones de este ciclo únicamente
            cycle_start = (self.current_cycle - 1) * cycle_duration
            cycle_end = self.current_cycle * cycle_duration
            
            cycle_transmissions = [
                entry for entry in self.slot_manager.transmission_log
                if cycle_start <= entry['start_time'] < cycle_end
            ]
            
            # Calcular utilización solo para este ciclo
            cycle_transmission_time = sum(entry['duration'] for entry in cycle_transmissions)
            transmission_window = cycle_duration * 0.6  # 60% del ciclo disponible para transmisión (75us de 125us)
            
            cycle_utilization = (cycle_transmission_time / transmission_window) * 100 if transmission_window > 0 else 0
            cycle_utilization = min(cycle_utilization, 100.0)
            
            self.stats['channel_utilization_samples'].append(cycle_utilization)
    
    def get_olt_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas completas del OLT"""
        avg_utilization = 0
        if self.stats['channel_utilization_samples']:
            avg_utilization = sum(self.stats['channel_utilization_samples']) / len(self.stats['channel_utilization_samples'])
        
        return {
            'olt_stats': self.stats.copy(),
            'current_cycle': self.current_cycle,
            'cycle_duration': self.cycle_manager.cycle_duration,
            'channel_capacity': self.channel_capacity,
            'average_utilization': avg_utilization,
            'cycle_stats': self.cycle_manager.get_cycle_statistics(),
            'transmission_log': self.slot_manager.get_transmission_log()
        }
    
    def reset_statistics(self):
        """Reiniciar estadísticas del OLT"""
        self.stats = {
            'cycles_executed': 0,
            'reports_collected': 0,
            'grants_assigned': 0,
            'total_grants_bytes': 0,
            'successful_transmissions': 0,
            'failed_transmissions': 0,
            'channel_utilization_samples': []
        }
        
        self.current_cycle = 0
        self.slot_manager.reset()
        self.last_reports.clear()
        self.pending_grants.clear()
    
    def set_dba_algorithm(self, dba_algorithm: 'DBAAlgorithmInterface'):
        """Cambiar algoritmo DBA"""
        self.dba_algorithm = dba_algorithm