"""
PON DBA Cycle Manager
Manejo de ciclos DBA realistas para simulación PON
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from .pon_request import Request
from .pon_onu import ONU
from .pon_dba import DBAAlgorithmInterface


@dataclass
class DBAAllocation:
    """Asignación de ancho de banda para una ONU en un ciclo DBA"""
    onu_id: str
    bandwidth_allocated: float  # MB
    time_slot_start: float     # tiempo relativo al ciclo
    time_slot_duration: float  # duración del time-slot
    requests_to_process: List[Request]  # requests que se procesarán


@dataclass
class DBAResult:
    """Resultado de un ciclo DBA completo"""
    cycle_number: int
    cycle_start_time: float
    cycle_duration: float
    allocations: List[DBAAllocation]
    total_bandwidth_used: float
    total_requests_processed: int
    successful_transmissions: int
    failed_transmissions: int


class DBACycleManager:
    """Gestor de ciclos DBA realistas"""
    
    def __init__(self, cycle_duration: float = 0.000125):  # 125 microsegundos típico
        """
        Inicializar gestor de ciclos DBA
        
        Args:
            cycle_duration: Duración de un ciclo DBA en segundos (default: 125us)
        """
        self.cycle_duration = cycle_duration
        self.current_cycle = 0
        self.total_cycles_executed = 0
        
        # Fases del ciclo DBA (en porcentaje del ciclo total)
        self.polling_phase_ratio = 0.1      # 10% - Polling
        self.reporting_phase_ratio = 0.2     # 20% - Reporting  
        self.allocation_phase_ratio = 0.05   # 5% - Allocation calculation
        self.transmission_phase_ratio = 0.65 # 65% - Data transmission
        
        # Métricas del ciclo
        self.cycle_metrics = []
        
    def execute_dba_cycle(self, 
                         onus: Dict[str, ONU], 
                         dba_algorithm: DBAAlgorithmInterface,
                         total_bandwidth: float,
                         current_time: float,
                         action: Optional[any] = None) -> DBAResult:
        """
        Ejecutar un ciclo DBA completo
        
        Args:
            onus: Diccionario de ONUs {onu_id: ONU}
            dba_algorithm: Algoritmo DBA a usar
            total_bandwidth: Ancho de banda total disponible (Mbps)
            current_time: Tiempo actual de simulación
            action: Acción para algoritmos RL
            
        Returns:
            Resultado del ciclo DBA con todas las asignaciones
        """
        cycle_start = current_time
        
        # FASE 1: POLLING - Solicitar reportes a todas las ONUs
        polling_start = cycle_start
        polling_duration = self.cycle_duration * self.polling_phase_ratio
        
        # FASE 2: REPORTING - ONUs reportan sus necesidades
        reporting_start = polling_start + polling_duration
        reporting_duration = self.cycle_duration * self.reporting_phase_ratio
        
        # Recolectar reportes de todas las ONUs
        onu_reports = self._collect_onu_reports(onus, reporting_start)
        print(f"DEBUG: Reportes obtenidos de {len(onu_reports)} ONUs")
        
        # FASE 3: ALLOCATION - Calcular asignaciones DBA
        allocation_start = reporting_start + reporting_duration
        allocation_duration = self.cycle_duration * self.allocation_phase_ratio
        
        # Ejecutar algoritmo DBA para obtener asignaciones
        bandwidth_allocations = self._execute_dba_algorithm(
            onu_reports, dba_algorithm, total_bandwidth, action
        )
        print(f"DEBUG: Asignaciones DBA: {bandwidth_allocations}")
        
        # FASE 4: TRANSMISSION - Asignar time-slots y procesar
        transmission_start = allocation_start + allocation_duration
        transmission_duration = self.cycle_duration * self.transmission_phase_ratio
        
        # Crear asignaciones de time-slots
        dba_allocations = self._create_time_slot_allocations(
            bandwidth_allocations, onu_reports, transmission_start, transmission_duration
        )
        
        # Crear resultado del ciclo
        result = DBAResult(
            cycle_number=self.current_cycle,
            cycle_start_time=cycle_start,
            cycle_duration=self.cycle_duration,
            allocations=dba_allocations,
            total_bandwidth_used=sum(alloc.bandwidth_allocated for alloc in dba_allocations),
            total_requests_processed=sum(len(alloc.requests_to_process) for alloc in dba_allocations),
            successful_transmissions=0,  # Se actualiza durante procesamiento
            failed_transmissions=0
        )
        
        self.current_cycle += 1
        self.total_cycles_executed += 1
        
        return result
        
    def _collect_onu_reports(self, onus: Dict[str, ONU], report_time: float) -> Dict[str, List[Request]]:
        """Recolectar reportes de buffer de todas las ONUs"""
        reports = {}
        
        for onu_id, onu in onus.items():
            # Cada ONU reporta sus solicitudes pendientes
            onu_requests = onu.report(report_time)
            print(f"DEBUG: ONU {onu_id} reportó {len(onu_requests) if onu_requests else 0} requests")
            if onu_requests:
                reports[onu_id] = onu_requests
                
        return reports
        
    def _execute_dba_algorithm(self, 
                              onu_reports: Dict[str, List[Request]],
                              dba_algorithm: DBAAlgorithmInterface,
                              total_bandwidth: float,
                              action: Optional[any]) -> Dict[str, float]:
        """Ejecutar algoritmo DBA para calcular asignaciones"""
        
        # Convertir reportes a solicitudes de ancho de banda
        onu_requests = {}
        for onu_id, request_list in onu_reports.items():
            if request_list:
                # Debug detallado de cada request
                print(f"DEBUG: ONU {onu_id} tiene {len(request_list)} requests:")
                for i, req in enumerate(request_list):
                    traffic = req.get_total_traffic()
                    print(f"  Request {i}: traffic={traffic:.6f} MB, traffic_dict={req.traffic}")
                
                # Sumar todo el tráfico pendiente de la ONU
                total_traffic = sum(req.get_total_traffic() for req in request_list)
                onu_requests[onu_id] = total_traffic
                print(f"DEBUG: ONU {onu_id} solicita {total_traffic:.6f} MB de ancho de banda")
                
        # Ejecutar algoritmo DBA
        if onu_requests:
            return dba_algorithm.allocate_bandwidth(onu_requests, total_bandwidth, action)
        else:
            return {}
            
    def _create_time_slot_allocations(self, 
                                    bandwidth_allocations: Dict[str, float],
                                    onu_reports: Dict[str, List[Request]],
                                    transmission_start: float,
                                    transmission_duration: float) -> List[DBAAllocation]:
        """Crear asignaciones de time-slots para las ONUs"""
        
        allocations = []
        current_slot_start = 0.0  # Tiempo relativo al inicio de transmisión
        
        for onu_id, allocated_bandwidth in bandwidth_allocations.items():
            if allocated_bandwidth > 0 and onu_id in onu_reports:
                
                # Calcular duración del time-slot basado en ancho de banda asignado
                total_bandwidth = sum(bandwidth_allocations.values())
                if total_bandwidth > 0:
                    slot_ratio = allocated_bandwidth / total_bandwidth
                    slot_duration = transmission_duration * slot_ratio
                else:
                    slot_duration = 0
                    
                # Seleccionar requests que caben en el ancho de banda asignado
                requests_to_process = self._select_requests_for_bandwidth(
                    onu_reports[onu_id], allocated_bandwidth
                )
                
                # Crear asignación
                allocation = DBAAllocation(
                    onu_id=onu_id,
                    bandwidth_allocated=allocated_bandwidth,
                    time_slot_start=transmission_start + current_slot_start,
                    time_slot_duration=slot_duration,
                    requests_to_process=requests_to_process
                )
                
                allocations.append(allocation)
                current_slot_start += slot_duration
                
        return allocations
        
    def _select_requests_for_bandwidth(self, 
                                     requests: List[Request], 
                                     available_bandwidth: float) -> List[Request]:
        """Seleccionar requests que caben en el ancho de banda disponible"""
        selected = []
        used_bandwidth = 0.0
        
        # Ordenar por prioridad/timestamp (FCFS básico por ahora)
        sorted_requests = sorted(requests, key=lambda r: r.created_at)
        
        for request in sorted_requests:
            request_bandwidth = request.get_total_traffic()
            if used_bandwidth + request_bandwidth <= available_bandwidth:
                selected.append(request)
                used_bandwidth += request_bandwidth
            else:
                # No hay más espacio en este ciclo
                break
                
        return selected
        
    def get_cycle_metrics(self) -> Dict:
        """Obtener métricas del gestor de ciclos"""
        return {
            'total_cycles_executed': self.total_cycles_executed,
            'current_cycle': self.current_cycle,
            'cycle_duration': self.cycle_duration,
            'phase_ratios': {
                'polling': self.polling_phase_ratio,
                'reporting': self.reporting_phase_ratio,
                'allocation': self.allocation_phase_ratio,
                'transmission': self.transmission_phase_ratio
            }
        }
        
    def reset_metrics(self):
        """Reiniciar métricas del gestor"""
        self.current_cycle = 0
        self.total_cycles_executed = 0
        self.cycle_metrics = []