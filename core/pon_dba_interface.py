"""
PON DBA Interface
Interfaces para algoritmos DBA modulares integradas de netPONPy
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from .pon_request import Request


class DBAAlgorithmInterface(ABC):
    """
    Interface para algoritmos DBA configurables.
    
    Permite implementar diferentes estrategias DBA que pueden ser
    dinámicamente intercambiadas, siguiendo el patrón Strategy.
    """
    
    @abstractmethod
    def allocate_bandwidth(self, onu_requests: Dict[str, float], 
                          total_bandwidth: float, action: Any = None) -> Dict[str, float]:
        """
        Asignar ancho de banda a las ONUs.
        
        Args:
            onu_requests: Diccionario {onu_id: bandwidth_requested}
            total_bandwidth: Ancho de banda total disponible
            action: Acción del agente RL (opcional)
            
        Returns:
            Diccionario {onu_id: bandwidth_allocated}
        """
        pass
    
    def select_next_request(self, available_requests: Dict[str, List[Request]], 
                           clock_time: float) -> Optional[Request]:
        """
        Seleccionar la próxima solicitud a procesar según la política del algoritmo.
        
        Args:
            available_requests: Diccionario {onu_id: [list_of_requests]}
            clock_time: Tiempo actual de simulación
            
        Returns:
            Solicitud seleccionada para procesar
        """
        # Implementación por defecto - selecciona primera solicitud disponible
        for onu_id, request_list in available_requests.items():
            if request_list:
                return request_list[0]
        return None
    
    @abstractmethod
    def get_algorithm_name(self) -> str:
        """
        Obtener nombre del algoritmo.
        
        Returns:
            Nombre descriptivo del algoritmo
        """
        pass


class FCFSDBAAlgorithm(DBAAlgorithmInterface):
    """Algoritmo DBA First-Come-First-Served - selecciona solicitud más antigua"""
    
    def allocate_bandwidth(self, onu_requests: Dict[str, float], 
                          total_bandwidth: float, action: Any = None) -> Dict[str, float]:
        """Asignación FCFS: da ancho de banda completo a la ONU con solicitud más antigua"""
        allocations = {}
        
        # Dar ancho de banda completo solo a la primera ONU (asumiendo que tiene la solicitud más antigua)
        # La lógica real de FCFS sucede en select_next_request()
        if onu_requests:
            first_onu = next(iter(onu_requests))
            allocations[first_onu] = min(onu_requests[first_onu], total_bandwidth)
            
        return allocations
    
    def select_next_request(self, available_requests: Dict[str, List[Request]], 
                           clock_time: float) -> Optional[Request]:
        """Seleccionar la solicitud más antigua entre TODAS las ONUs (FCFS verdadero)"""
        all_requests = []
        
        # Recolectar todas las solicitudes de todas las ONUs
        for onu_id, request_list in available_requests.items():
            for request in request_list:
                all_requests.append(request)
        
        if not all_requests:
            return None
            
        # Retornar la solicitud con tiempo de creación más temprano (FCFS verdadero)
        oldest_request = min(all_requests, key=lambda r: r.created_at)
        return oldest_request
    
    def get_algorithm_name(self) -> str:
        return "FCFS"


class PriorityDBAAlgorithm(DBAAlgorithmInterface):
    """Algoritmo DBA basado en prioridades - prioriza por tipo de tráfico con prevención de inanición"""
    
    def __init__(self, starvation_threshold: float = 100.0):  # 100ms threshold
        """
        Args:
            starvation_threshold: Tiempo máximo de espera antes de promover a mayor prioridad (ms)
        """
        self.starvation_threshold = starvation_threshold / 1000.0  # Convertir a segundos
        
        # Prioridades de tipos de tráfico (menor número = mayor prioridad)
        self.traffic_priorities = {
            "highest": 1,
            "high": 2, 
            "medium": 3,
            "low": 4,
            "lowest": 5
        }
    
    def allocate_bandwidth(self, onu_requests: Dict[str, float], 
                          total_bandwidth: float, action: Any = None) -> Dict[str, float]:
        """Asignación por prioridad: da ancho de banda completo a solicitud de mayor prioridad"""
        allocations = {}
        
        # Dar ancho de banda completo a primera ONU (lógica real en select_next_request)
        if onu_requests:
            first_onu = next(iter(onu_requests))
            allocations[first_onu] = min(onu_requests[first_onu], total_bandwidth)
            
        return allocations
    
    def select_next_request(self, available_requests: Dict[str, List[Request]], 
                           clock_time: float) -> Optional[Request]:
        """Seleccionar solicitud de mayor prioridad con prevención de inanición"""
        all_requests = []
        
        # Recolectar todas las solicitudes de todas las ONUs
        for onu_id, request_list in available_requests.items():
            for request in request_list:
                all_requests.append(request)
        
        if not all_requests:
            return None
        
        # Calcular prioridad efectiva para cada solicitud
        prioritized_requests = []
        for request in all_requests:
            waiting_time = clock_time - request.created_at
            
            # Verificar inanición - promover a mayor prioridad si espera demasiado
            if waiting_time >= self.starvation_threshold:
                effective_priority = 0  # Mayor que prioridad "highest"
                prioritized_requests.append((0, request.created_at, request))
            else:
                # Obtener prioridad basada en tipo de tráfico
                request_priority = self._get_request_priority(request)
                prioritized_requests.append((request_priority, request.created_at, request))
        
        # Ordenar por: 1) Prioridad (menor = mejor), 2) Tiempo de creación (más antiguo = mejor)
        prioritized_requests.sort(key=lambda x: (x[0], x[1]))
        
        return prioritized_requests[0][2]  # Retornar la solicitud
    
    def _get_request_priority(self, request: Request) -> int:
        """Obtener la mayor prioridad de tipo de tráfico en la solicitud"""
        if not request.traffic:
            return 999  # Prioridad más baja para tráfico vacío
        
        highest_priority = 999
        for traffic_type, amount in request.traffic.items():
            if amount and amount > 0:
                priority = self.traffic_priorities.get(traffic_type, 999)
                if priority < highest_priority:
                    highest_priority = priority
        
        return highest_priority
    
    def get_algorithm_name(self) -> str:
        return "Priority"


class RLDBAAlgorithm(DBAAlgorithmInterface):
    """Algoritmo DBA controlado por RL"""
    
    def allocate_bandwidth(self, onu_requests: Dict[str, float], 
                          total_bandwidth: float, action: Any = None) -> Dict[str, float]:
        """Asignación controlada por agente RL"""
        allocations = {}
        
        if action is None:
            # Fallback a distribución equitativa
            num_onus = len(onu_requests)
            equal_share = total_bandwidth / num_onus if num_onus > 0 else 0
            for onu_id in onu_requests:
                allocations[onu_id] = min(onu_requests[onu_id], equal_share)
        else:
            # Asignación basada en acción del usuario
            # Verificar si la acción es un array válido con pesos
            if hasattr(action, '__len__') and len(action) == len(onu_requests):
                # Normalizar acciones
                action_sum = sum(action) if sum(action) > 0 else 1
                normalized_action = [a / action_sum for a in action]
                
                for i, onu_id in enumerate(sorted(onu_requests.keys())):
                    allocated_bandwidth = normalized_action[i] * total_bandwidth
                    allocations[onu_id] = min(onu_requests[onu_id], allocated_bandwidth)
            else:
                print("Warning: Action format not recognized, using equal distribution.")
                # Fallback si la acción no tiene formato esperado
                equal_share = total_bandwidth / len(onu_requests)
                for onu_id in onu_requests:
                    allocations[onu_id] = min(onu_requests[onu_id], equal_share)
                    
        return allocations
    
    def get_algorithm_name(self) -> str:
        return "RL-DBA"