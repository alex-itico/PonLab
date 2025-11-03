"""
PON DBA Interface
Interfaces para algoritmos DBA modulares integradas de netPONPy
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..data.pon_request import Request


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
        """Asignación FCFS realista: distribuye ancho de banda a todas las ONUs con requests"""
        allocations = {}
        
        if not onu_requests:
            return allocations
            
        # Calcular total solicitado
        total_requested = sum(onu_requests.values())
        
        if total_requested <= total_bandwidth:
            # Si hay suficiente ancho de banda, dar a cada ONU lo que pidió
            allocations = onu_requests.copy()
        else:
            # Si no hay suficiente, distribuir proporcionalmente
            for onu_id, requested in onu_requests.items():
                proportion = requested / total_requested
                allocations[onu_id] = total_bandwidth * proportion
                
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

class StrictPriorityMinShareDBA(DBAAlgorithmInterface):
    """
    Algoritmo DBA con prioridad estricta y garantías mínimas.
    Asegura mínimos por tipo de tráfico y luego reparte sobrante por prioridad.
    """
    def __init__(self):
        """Constructor simplificado"""
        pass

    def allocate_bandwidth(self, onu_requests, total_bandwidth, action=None):
        # Convertir formato de entrada si es necesario
        if isinstance(next(iter(onu_requests.values()), None), (int, float)):
            # Formato simple {onu_id: bandwidth} - convertir a formato TCONT
            converted_requests = {}
            for onu_id, bandwidth in onu_requests.items():
                # Distribuir la demanda entre TCONTs con prioridad decreciente
                converted_requests[onu_id] = {
                    'highest': bandwidth * 0.4,  # 40% a highest priority
                    'high': bandwidth * 0.3,     # 30% a high priority  
                    'medium': bandwidth * 0.2,   # 20% a medium priority
                    'low': bandwidth * 0.1,      # 10% a low priority
                    'lowest': 0                  # 0% a lowest priority
                }
            onu_requests = converted_requests
        
        # Asegura tipos
        budget_bytes = int(total_bandwidth * 1024 * 1024)  # MB to bytes
        allocations = {}

        # Demanda total por TCONT y por ONU/TCONT  
        tcont_priorities = ['highest', 'high', 'medium', 'low', 'lowest']
        demand_per_tcont = {t: 0 for t in tcont_priorities}
        
        for onu_id, tdict in onu_requests.items():
            for tcont_id, req_bytes in tdict.items():
                if tcont_id in demand_per_tcont:
                    demand_per_tcont[tcont_id] += max(0, int((req_bytes or 0) * 1024 * 1024))  # MB to bytes

        # 1) Asignar mínimos por TCONT (si hay demanda)
        assigned = 0
        min_shares = {
            'highest': 0.25,  # 25%
            'high': 0.20,     # 20%  
            'medium': 0.15,   # 15%
            'low': 0.10,      # 10%
            'lowest': 0.00    # 0%
        }
        
        for tcont_id in tcont_priorities:
            min_bytes = int(min_shares.get(tcont_id, 0.0) * budget_bytes)
            if min_bytes <= 0 or demand_per_tcont[tcont_id] <= 0:
                continue
            # repartir min_bytes proporcional a la demanda de cada ONU en ese TCONT
            total_dem_t = demand_per_tcont[tcont_id]
            for onu_id, tdict in onu_requests.items():
                req = max(0, int((tdict.get(tcont_id, 0) or 0) * 1024 * 1024))  # MB to bytes
                if req <= 0: 
                    continue
                share = int(min_bytes * (req / total_dem_t))
                if share <= 0:
                    continue
                # asignar sin exceder request ni budget
                give = min(share, req, budget_bytes - assigned)
                if give <= 0:
                    continue
                allocations.setdefault(onu_id, {})[tcont_id] = allocations.get(onu_id, {}).get(tcont_id, 0) + give
                assigned += give
                if assigned >= budget_bytes:
                    break
            if assigned >= budget_bytes:
                break

        # 2) Repartir sobrante por prioridad (de arriba hacia abajo) proporcional a demanda remanente
        if assigned < budget_bytes:
            for tcont_id in tcont_priorities:
                # demanda restante en este TCONT
                rem_total = 0
                rem_per_onu = {}
                for onu_id, tdict in onu_requests.items():
                    req = max(0, int((tdict.get(tcont_id, 0) or 0) * 1024 * 1024))  # MB to bytes
                    already = allocations.get(onu_id, {}).get(tcont_id, 0)
                    rem = max(0, req - already)
                    if rem > 0:
                        rem_per_onu[onu_id] = rem
                        rem_total += rem
                if rem_total <= 0:
                    continue

                # presupuesto disponible en esta vuelta
                leftover = budget_bytes - assigned
                if leftover <= 0:
                    break

                for onu_id, rem in rem_per_onu.items():
                    share = int(leftover * (rem / rem_total))
                    if share <= 0:
                        continue
                    give = min(share, rem, budget_bytes - assigned)
                    if give <= 0:
                        continue
                    allocations.setdefault(onu_id, {})[tcont_id] = allocations.get(onu_id, {}).get(tcont_id, 0) + give
                    assigned += give
                    if assigned >= budget_bytes:
                        break
                if assigned >= budget_bytes:
                    break

        # 3) Sanitizar y convertir de vuelta a formato simple
        final_allocations = {}
        for onu_id, tdict in allocations.items():
            total_onu_bytes = sum(tdict.values())
            # Convertir bytes a MB para compatibilidad
            final_allocations[onu_id] = total_onu_bytes / (1024 * 1024)
        
        return final_allocations
    
    def get_algorithm_name(self) -> str:
        return "SP-MINSHARE"

class TEST(DBAAlgorithmInterface):
    """
    Algoritmo DBA con prioridad estricta y garantías mínimas.
    Asegura mínimos por tipo de tráfico y luego reparte sobrante por prioridad.
    """
    def __init__(self):
        """Constructor simplificado"""
        pass

    def allocate_bandwidth(self, onu_requests, total_bandwidth, action=None):
        # Convertir formato de entrada si es necesario
        if isinstance(next(iter(onu_requests.values()), None), (int, float)):
            # Formato simple {onu_id: bandwidth} - convertir a formato TCONT
            converted_requests = {}
            for onu_id, bandwidth in onu_requests.items():
                # Distribuir la demanda entre TCONTs con prioridad decreciente
                converted_requests[onu_id] = {
                    'highest': bandwidth * 0.4,  # 40% a highest priority
                    'high': bandwidth * 0.3,     # 30% a high priority  
                    'medium': bandwidth * 0.2,   # 20% a medium priority
                    'low': bandwidth * 0.1,      # 10% a low priority
                    'lowest': 0                  # 0% a lowest priority
                }
            onu_requests = converted_requests
        
        # Asegura tipos
        budget_bytes = int(total_bandwidth * 1024 * 1024)  # MB to bytes
        allocations = {}

        # Demanda total por TCONT y por ONU/TCONT  
        tcont_priorities = ['highest', 'high', 'medium', 'low', 'lowest']
        demand_per_tcont = {t: 0 for t in tcont_priorities}
        
        for onu_id, tdict in onu_requests.items():
            for tcont_id, req_bytes in tdict.items():
                if tcont_id in demand_per_tcont:
                    demand_per_tcont[tcont_id] += max(0, int((req_bytes or 0) * 1024 * 1024))  # MB to bytes

        # 1) Asignar mínimos por TCONT (si hay demanda)
        assigned = 0
        min_shares = {
            'highest': 0.25,  # 25%
            'high': 0.20,     # 20%  
            'medium': 0.15,   # 15%
            'low': 0.10,      # 10%
            'lowest': 0.00    # 0%
        }
        
        for tcont_id in tcont_priorities:
            min_bytes = int(min_shares.get(tcont_id, 0.0) * budget_bytes)
            if min_bytes <= 0 or demand_per_tcont[tcont_id] <= 0:
                continue
            # repartir min_bytes proporcional a la demanda de cada ONU en ese TCONT
            total_dem_t = demand_per_tcont[tcont_id]
            for onu_id, tdict in onu_requests.items():
                req = max(0, int((tdict.get(tcont_id, 0) or 0) * 1024 * 1024))  # MB to bytes
                if req <= 0: 
                    continue
                share = int(min_bytes * (req / total_dem_t))
                if share <= 0:
                    continue
                # asignar sin exceder request ni budget
                give = min(share, req, budget_bytes - assigned)
                if give <= 0:
                    continue
                allocations.setdefault(onu_id, {})[tcont_id] = allocations.get(onu_id, {}).get(tcont_id, 0) + give
                assigned += give
                if assigned >= budget_bytes:
                    break
            if assigned >= budget_bytes:
                break

        # 2) Repartir sobrante por prioridad (de arriba hacia abajo) proporcional a demanda remanente
        if assigned < budget_bytes:
            for tcont_id in tcont_priorities:
                # demanda restante en este TCONT
                rem_total = 0
                rem_per_onu = {}
                for onu_id, tdict in onu_requests.items():
                    req = max(0, int((tdict.get(tcont_id, 0) or 0) * 1024 * 1024))  # MB to bytes
                    already = allocations.get(onu_id, {}).get(tcont_id, 0)
                    rem = max(0, req - already)
                    if rem > 0:
                        rem_per_onu[onu_id] = rem
                        rem_total += rem
                if rem_total <= 0:
                    continue

                # presupuesto disponible en esta vuelta
                leftover = budget_bytes - assigned
                if leftover <= 0:
                    break

                for onu_id, rem in rem_per_onu.items():
                    share = int(leftover * (rem / rem_total))
                    if share <= 0:
                        continue
                    give = min(share, rem, budget_bytes - assigned)
                    if give <= 0:
                        continue
                    allocations.setdefault(onu_id, {})[tcont_id] = allocations.get(onu_id, {}).get(tcont_id, 0) + give
                    assigned += give
                    if assigned >= budget_bytes:
                        break
                if assigned >= budget_bytes:
                    break

        # 3) Sanitizar y convertir de vuelta a formato simple
        final_allocations = {}
        for onu_id, tdict in allocations.items():
            total_onu_bytes = sum(tdict.values())
            # Convertir bytes a MB para compatibilidad
            final_allocations[onu_id] = total_onu_bytes / (1024 * 1024)
        
        return final_allocations
    
    def get_algorithm_name(self) -> str:
        return "TEST_A"

class TESTB(DBAAlgorithmInterface):
    """
    Algoritmo DBA con prioridad estricta y garantías mínimas.
    Asegura mínimos por tipo de tráfico y luego reparte sobrante por prioridad.
    """
    def __init__(self):
        """Constructor simplificado"""
        pass

    def allocate_bandwidth(self, onu_requests, total_bandwidth, action=None):
        # Convertir formato de entrada si es necesario
        if isinstance(next(iter(onu_requests.values()), None), (int, float)):
            # Formato simple {onu_id: bandwidth} - convertir a formato TCONT
            converted_requests = {}
            for onu_id, bandwidth in onu_requests.items():
                # Distribuir la demanda entre TCONTs con prioridad decreciente
                converted_requests[onu_id] = {
                    'highest': bandwidth * 0.4,  # 40% a highest priority
                    'high': bandwidth * 0.3,     # 30% a high priority  
                    'medium': bandwidth * 0.2,   # 20% a medium priority
                    'low': bandwidth * 0.1,      # 10% a low priority
                    'lowest': 0                  # 0% a lowest priority
                }
            onu_requests = converted_requests
        
        # Asegura tipos
        budget_bytes = int(total_bandwidth * 1024 * 1024)  # MB to bytes
        allocations = {}

        # Demanda total por TCONT y por ONU/TCONT  
        tcont_priorities = ['highest', 'high', 'medium', 'low', 'lowest']
        demand_per_tcont = {t: 0 for t in tcont_priorities}
        
        for onu_id, tdict in onu_requests.items():
            for tcont_id, req_bytes in tdict.items():
                if tcont_id in demand_per_tcont:
                    demand_per_tcont[tcont_id] += max(0, int((req_bytes or 0) * 1024 * 1024))  # MB to bytes

        # 1) Asignar mínimos por TCONT (si hay demanda)
        assigned = 0
        min_shares = {
            'highest': 0.25,  # 25%
            'high': 0.20,     # 20%  
            'medium': 0.15,   # 15%
            'low': 0.10,      # 10%
            'lowest': 0.00    # 0%
        }
        
        for tcont_id in tcont_priorities:
            min_bytes = int(min_shares.get(tcont_id, 0.0) * budget_bytes)
            if min_bytes <= 0 or demand_per_tcont[tcont_id] <= 0:
                continue
            # repartir min_bytes proporcional a la demanda de cada ONU en ese TCONT
            total_dem_t = demand_per_tcont[tcont_id]
            for onu_id, tdict in onu_requests.items():
                req = max(0, int((tdict.get(tcont_id, 0) or 0) * 1024 * 1024))  # MB to bytes
                if req <= 0: 
                    continue
                share = int(min_bytes * (req / total_dem_t))
                if share <= 0:
                    continue
                # asignar sin exceder request ni budget
                give = min(share, req, budget_bytes - assigned)
                if give <= 0:
                    continue
                allocations.setdefault(onu_id, {})[tcont_id] = allocations.get(onu_id, {}).get(tcont_id, 0) + give
                assigned += give
                if assigned >= budget_bytes:
                    break
            if assigned >= budget_bytes:
                break

        # 2) Repartir sobrante por prioridad (de arriba hacia abajo) proporcional a demanda remanente
        if assigned < budget_bytes:
            for tcont_id in tcont_priorities:
                # demanda restante en este TCONT
                rem_total = 0
                rem_per_onu = {}
                for onu_id, tdict in onu_requests.items():
                    req = max(0, int((tdict.get(tcont_id, 0) or 0) * 1024 * 1024))  # MB to bytes
                    already = allocations.get(onu_id, {}).get(tcont_id, 0)
                    rem = max(0, req - already)
                    if rem > 0:
                        rem_per_onu[onu_id] = rem
                        rem_total += rem
                if rem_total <= 0:
                    continue

                # presupuesto disponible en esta vuelta
                leftover = budget_bytes - assigned
                if leftover <= 0:
                    break

                for onu_id, rem in rem_per_onu.items():
                    share = int(leftover * (rem / rem_total))
                    if share <= 0:
                        continue
                    give = min(share, rem, budget_bytes - assigned)
                    if give <= 0:
                        continue
                    allocations.setdefault(onu_id, {})[tcont_id] = allocations.get(onu_id, {}).get(tcont_id, 0) + give
                    assigned += give
                    if assigned >= budget_bytes:
                        break
                if assigned >= budget_bytes:
                    break

        # 3) Sanitizar y convertir de vuelta a formato simple
        final_allocations = {}
        for onu_id, tdict in allocations.items():
            total_onu_bytes = sum(tdict.values())
            # Convertir bytes a MB para compatibilidad
            final_allocations[onu_id] = total_onu_bytes / (1024 * 1024)
        
        return final_allocations
    
    def get_algorithm_name(self) -> str:
        return "TEST_B"
