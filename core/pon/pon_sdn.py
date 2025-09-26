"""
PON SDN
Software-Defined Optical Line Terminal integrado de netPONPy con algoritmos DBA modulares
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from ..data.pon_request import Request
from .pon_onu import ONU
from ..connections.pon_link import Link
from ..algorithms.pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm

# Importación diferida para evitar ciclos
if TYPE_CHECKING:
    from ..connections.pon_connection import Connection

# Mapeo de prioridades para requests
PRIORITY_MAP = {"highest": 0, "high": 1, "medium": 2, "low": 3, "lowest": 4}
DEFAULT_PRIORITY = 99  # Para tipos de tráfico indefinidos o sin tráfico


class OLT_SDN:
    """Software-Defined Optical Line Terminal - Terminal de Línea Óptica con SDN"""
    
    def __init__(
        self,
        id: str,
        onus: Dict[str, ONU],
        dba_algorithm: Optional[DBAAlgorithmInterface] = None,
        links_data: Dict[str, Dict] = {"0": {"length": 0.5}, "1": {"length": 0.5}},
        transmission_rate: float = 4096.0,  # Mbps (corregido typo)
        seed: int = 12345,
    ):
        """
        Inicializar OLT_SDN con algoritmo DBA modular
        
        Args:
            id: Identificador único del OLT_SDN
            onus: Diccionario de ONUs registradas {onu_id: ONU}
            dba_algorithm: Algoritmo DBA a usar
            links_data: Configuración de enlaces {link_id: {length: km}}
            transmission_rate: Tasa de transmisión en Mbps (corregido typo)
            seed: Semilla para reproducibilidad
        """
        self.__id = id
        self.onus = onus
        self._onu_ids = list(self.onus.keys())
        self._n_onus = len(self._onu_ids)
        self.links: Dict[str, Link] = self.create_links(links_data)
        self.transmission_rate = transmission_rate  # Corregido typo
        self.__seed = seed
        self.clock: float = 0.0
        self.fragmented_time = 0.0
        
        # Algoritmo DBA modular
        self.dba_algorithm = dba_algorithm or FCFSDBAAlgorithm()
        
        # Estado interno para algoritmos
        self._last_action = None
        self._algorithm_state = {}
        self._last_processed_request = None
        
        # Estadísticas del OLT_SDN
        self.total_polls = 0
        self.successful_transmissions = 0
        self.failed_transmissions = 0

    @property
    def id(self) -> str:
        return self.__id

    @staticmethod
    def create_links(links_data: Dict[str, Dict]) -> Dict[str, Link]:
        """Crear enlaces del OLT_SDN según configuración"""
        links: Dict[str, Link] = {}
        for link_id, data in links_data.items():
            links[link_id] = Link(link_id, data["length"])
        return links

    def init(self) -> Request:
        """Inicializar OLT_SDN y obtener primera solicitud"""
        request = self._get_nearest_request()
        self.clock = request.created_at
        return request

    def set_dba_algorithm(self, algorithm: DBAAlgorithmInterface):
        """Configurar algoritmo DBA modular"""
        self.dba_algorithm = algorithm
        self._algorithm_state = {}  # Reiniciar estado interno

    def set_action(self, action):
        """Configurar acción para algoritmos RL"""
        self._last_action = action

    def execute_dba_algorithm(self, reports: Dict[str, List[Request]]) -> Request:
        """Ejecutar algoritmo DBA usando interfaz modular"""
        
        # Verificar si el algoritmo DBA tiene el nuevo método select_next_request
        if hasattr(self.dba_algorithm, 'select_next_request'):
            # Usar el nuevo método para mejores implementaciones de algoritmos
            selected_request = self.dba_algorithm.select_next_request(reports, self.clock)
            if selected_request:
                return selected_request
        
        # Fallback al método antiguo para compatibilidad (algoritmo RL)
        # Convertir reports a formato de solicitud de ancho de banda
        onu_requests = {}
        available_requests = {}
        
        for onu_id, request_list in reports.items():
            if request_list:
                # Tomar la primera solicitud de cada ONU
                request = request_list[0]
                available_requests[onu_id] = request
                # Calcular ancho de banda solicitado basado en el tráfico de la solicitud
                bandwidth_requested = request.get_total_traffic()
                onu_requests[onu_id] = bandwidth_requested
        
        if not onu_requests:
            # Si no hay solicitudes, intentar generar una
            return self._get_nearest_request()
        
        # Ejecutar algoritmo DBA usando la interfaz
        allocations = self.dba_algorithm.allocate_bandwidth(
            onu_requests, 
            self.transmission_rate,  # Corregido typo
            self._last_action
        )
        
        # Seleccionar solicitud basada en las asignaciones
        selected_request = self._select_request_from_allocations(
            allocations, available_requests
        )
        
        return selected_request

    def _select_request_from_allocations(self, allocations: Dict[str, float], 
                                       available_requests: Dict[str, Request]) -> Request:
        """Seleccionar solicitud basada en las asignaciones del algoritmo DBA"""
        if not allocations or not available_requests:
            return self._get_nearest_request()
        
        # Encontrar ONU con mayor asignación que tenga solicitudes disponibles
        best_onu = None
        best_allocation = 0
        
        for onu_id, allocation in allocations.items():
            if onu_id in available_requests and allocation > best_allocation:
                best_allocation = allocation
                best_onu = onu_id
        
        if best_onu and best_onu in available_requests:
            return available_requests[best_onu]
        
        # Fallback: retornar cualquier solicitud disponible
        return next(iter(available_requests.values()))

    def get_reports(self) -> Dict[str, List[Request]]:
        """Obtener reportes de todas las ONUs registradas"""
        self.total_polls += 1
        reports: Dict[str, List[Request]] = {}
        
        for onu_id in self._onu_ids:
            onu_requests = self.onus[onu_id].report(self.clock)
            if onu_requests is not None:
                reports[onu_id] = onu_requests
                
        if not reports:
            # Si no hay reportes, obtener solicitud más cercana
            report = self._get_nearest_request()
            reports[report.source_id] = [report]
            
        return reports

    def _get_nearest_request(self) -> Request:
        """Obtener la solicitud más cercana en el tiempo"""
        nearest_reports: Dict[str, Request] = {}
        
        for onu_id in self._onu_ids:
            if self.onus[onu_id].buffer:  # Solo si el buffer no está vacío
                nearest_reports[onu_id] = self.onus[onu_id].buffer[0]
        
        if not nearest_reports:
            # Si todos los buffers están vacíos, forzar generación de nuevas solicitudes
            for onu_id in self._onu_ids:
                self.onus[onu_id].report(self.clock)
                if self.onus[onu_id].buffer:
                    nearest_reports[onu_id] = self.onus[onu_id].buffer[0]
        
        if nearest_reports:
            return min(list(nearest_reports.values()), key=lambda r: r.created_at)
        else:
            # Si no hay solicitudes disponibles, lanzar excepción
            raise Exception("No requests available in any ONU")

    def get_next_request(self) -> Request:
        """Obtener próxima solicitud usando algoritmo DBA modular"""
        reports = self.get_reports()
        return self.execute_dba_algorithm(reports)

    def compute_time_slot(self, request: Request) -> float:
        """Calcular duración de time slot para una solicitud"""
        total_traffic = request.get_total_traffic()
        transmission_speed = min(
            self.onus[request.source_id].transmission_rate, self.transmission_rate  # Corregido typo
        )
        # TODO: Considerar tiempo de guarda y tiempo de tx en el time_slot
        time_slot = total_traffic / transmission_speed if transmission_speed > 0 else 0
        return time_slot

    def establish_connection(self, request: Request) -> "Connection":
        """Establecer conexión para una solicitud"""
        # Importación dinámica para evitar ciclos
        from ..connections.pon_connection import Connection
        
        path_links_id = [request.source_id]
        path = [self.links[link_id] for link_id in path_links_id if link_id in self.links]
        
        transmission_speed = min(
            self.onus[request.source_id].transmission_rate, self.transmission_rate  # Corregido typo
        )
        
        return Connection(
            self.clock,
            path,
            transmission_speed,  # Corregido typo
        )

    def proccess(self, request: Request) -> tuple[bool, Request]:
        """Procesar una solicitud de transmisión"""
        try:
            time_slot = self.compute_time_slot(request)
            next_clock = max(self.clock, request.created_at)
            self.fragmented_time = self.fragmented_time + (next_clock - self.clock)
            self.clock = next_clock
            
            connection = self.establish_connection(request)
            was_transmitted = self.onus[request.source_id].transmit(
                str(request.id), connection, time_slot
            )
            
            # Actualizar clock para incluir tiempo de transmisión
            self.clock = self.clock + time_slot
            
            if was_transmitted:
                # departure_time incluye el tiempo de transmisión
                request.departure_time = self.clock
                self.successful_transmissions += 1
            else:
                # El evento no se pudo transmitir completamente
                self.failed_transmissions += 1
            
            # Registrar último request procesado para callbacks RL
            self._last_processed_request = request
            
            return was_transmitted, request
            
        except Exception as e:
            print(f"❌ Error processing request {request.id}: {e}")
            self.failed_transmissions += 1
            return False, request

    def get_request_priority(self, request: Request) -> int:
        """Obtener prioridad de una solicitud"""
        min_priority_value = DEFAULT_PRIORITY
        
        if not request.traffic:  # Si el diccionario de tráfico está vacío
            return DEFAULT_PRIORITY
            
        has_any_traffic = False
        for traffic_type, amount in request.traffic.items():
            if amount is not None and amount > 0:
                has_any_traffic = True
                priority = PRIORITY_MAP.get(traffic_type, DEFAULT_PRIORITY)
                if priority < min_priority_value:
                    min_priority_value = priority
        
        # Si una solicitud no tiene ningún tipo de tráfico con cantidad > 0
        return min_priority_value if has_any_traffic else DEFAULT_PRIORITY

    def get_olt_stats(self) -> dict:
        """Obtener estadísticas completas del OLT_SDN"""
        success_rate = (
            (self.successful_transmissions / (self.successful_transmissions + self.failed_transmissions)) * 100
            if (self.successful_transmissions + self.failed_transmissions) > 0 else 0
        )
        
        # Estadísticas de enlaces
        link_stats = {}
        for link_id, link in self.links.items():
            link_stats[link_id] = link.get_link_stats()
        
        return {
            'id': self.id,
            'clock': self.clock,
            'fragmented_time': self.fragmented_time,
            'registered_onus': len(self._onu_ids),
            'transmission_rate': self.transmission_rate,  # Corregido typo
            'dba_algorithm': self.dba_algorithm.get_algorithm_name(),
            'total_polls': self.total_polls,
            'successful_transmissions': self.successful_transmissions,
            'failed_transmissions': self.failed_transmissions,
            'success_rate': success_rate,
            'link_stats': link_stats
        }
    
    def reset_stats(self):
        """Reiniciar estadísticas del OLT_SDN"""
        self.total_polls = 0
        self.successful_transmissions = 0
        self.failed_transmissions = 0
        self.clock = 0.0
        self.fragmented_time = 0.0
        
        # Reiniciar estadísticas de enlaces
        for link in self.links.values():
            link.reset_stats()
    
    def __str__(self) -> str:
        return f"OLT_SDN(id={self.id}, onus={len(self._onu_ids)}, algorithm={self.dba_algorithm.get_algorithm_name()})"
    
    def __repr__(self) -> str:
        return self.__str__()
