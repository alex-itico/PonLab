"""
PON Request
Clase de solicitud de transmisión integrada de netPONPy
"""

import numpy as np
import uuid
from typing import Dict, Optional


class Request:
    """Solicitud de transmisión en una red PON"""
    
    def __init__(
        self,
        source_id: str,
        traffic: Dict[str, float],
        created_at: float,
    ):
        """
        Inicializar solicitud de transmisión
        
        Args:
            source_id: ID de la ONU que origina la solicitud
            traffic: Diccionario con tipos de tráfico y cantidades (MB)
            created_at: Tiempo de creación de la solicitud
        """
        self.id = uuid.uuid4()
        self.source_id = source_id
        self.created_at = created_at
        self.traffic = traffic
        self.__departure_time = np.inf

    @property
    def departure_time(self) -> float:
        """Tiempo de salida de la solicitud"""
        return self.__departure_time

    @departure_time.setter
    def departure_time(self, departure_time: float):
        """Establecer tiempo de salida"""
        if departure_time < self.created_at:
            raise ValueError("Departure time must be greater than arrival time.")
        self.__departure_time = departure_time

    def get_delay(self) -> float:
        """Calcular delay de la solicitud"""
        if self.__departure_time == np.inf:
            return np.inf
        return self.departure_time - self.created_at

    def get_total_traffic(self) -> float:
        """Obtener tráfico total de la solicitud en MB"""
        if not self.traffic:
            return 0.0
        return sum(amount for amount in self.traffic.values() if amount is not None)
    
    def __str__(self) -> str:
        return f"Request(id={str(self.id)[:8]}, source={self.source_id}, traffic={self.get_total_traffic():.3f}MB, created_at={self.created_at:.3f})"
    
    def __repr__(self) -> str:
        return self.__str__()