"""
PON Buffer
Buffer de solicitudes integrado de netPONPy
"""

from typing import List, Optional
from .pon_request import Request


class Buffer(list[Request]):
    """Buffer de solicitudes con capacidad limitada"""
    
    def __init__(self, size: int):
        """
        Inicializar buffer
        
        Args:
            size: Capacidad máxima del buffer
        """
        super().__init__()
        self.size = size
        self.dropped_requests = 0  # Contador de solicitudes descartadas
        self.total_arrivals = 0    # Contador total de intentos de inserción

    def append(self, request: Request) -> bool:
        """
        Agregar solicitud al buffer
        
        Args:
            request: Solicitud a agregar
            
        Returns:
            True si se agregó exitosamente, False si el buffer está lleno
        """
        self.total_arrivals += 1
        
        if len(self) < self.size:
            super().append(request)
            return True
        else:
            # Buffer lleno - descartar solicitud
            self.dropped_requests += 1
            return False

    def pop_request(self, request_id: str) -> Optional[Request]:
        """
        Remover solicitud específica por ID
        
        Args:
            request_id: ID de la solicitud a remover
            
        Returns:
            Solicitud removida o None si no se encuentra
        """
        for i, request in enumerate(self):
            if str(request.id) == str(request_id):
                return self.pop(i)
        return None

    def get_oldest_request(self) -> Optional[Request]:
        """
        Obtener la solicitud más antigua sin removerla
        
        Returns:
            Solicitud más antigua o None si el buffer está vacío
        """
        if not self:
            return None
        return min(self, key=lambda r: r.created_at)

    def get_highest_priority_request(self) -> Optional[Request]:
        """
        Obtener solicitud de mayor prioridad
        (Basado en los tipos de tráfico de netPONPy)
        
        Returns:
            Solicitud de mayor prioridad o None si está vacío
        """
        if not self:
            return None
            
        # Mapeo de prioridades (menor número = mayor prioridad)
        priority_map = {"highest": 0, "high": 1, "medium": 2, "low": 3, "lowest": 4}
        
        def get_request_priority(request: Request) -> int:
            if not request.traffic:
                return 99  # Prioridad más baja para tráfico vacío
                
            min_priority = 99
            for traffic_type, amount in request.traffic.items():
                if amount and amount > 0:
                    priority = priority_map.get(traffic_type, 99)
                    min_priority = min(min_priority, priority)
            return min_priority
        
        return min(self, key=get_request_priority)

    def get_buffer_utilization(self) -> float:
        """
        Obtener porcentaje de utilización del buffer
        
        Returns:
            Utilización entre 0.0 y 1.0
        """
        if self.size == 0:
            return 0.0
        return len(self) / self.size

    def get_buffer_stats(self) -> dict:
        """Obtener estadísticas completas del buffer"""
        loss_rate = (self.dropped_requests / self.total_arrivals) if self.total_arrivals > 0 else 0.0
        
        return {
            'size': self.size,
            'current_occupancy': len(self),
            'utilization': self.get_buffer_utilization(),
            'total_arrivals': self.total_arrivals,
            'dropped_requests': self.dropped_requests,
            'loss_rate': loss_rate,
            'successful_insertions': self.total_arrivals - self.dropped_requests
        }

    def reset_stats(self):
        """Reiniciar estadísticas del buffer"""
        self.dropped_requests = 0
        self.total_arrivals = 0

    def clear_buffer(self):
        """Limpiar buffer y reiniciar estadísticas"""
        self.clear()
        self.reset_stats()
    
    def __str__(self) -> str:
        return f"Buffer(size={self.size}, occupancy={len(self)}/{self.size}, utilization={self.get_buffer_utilization():.1%})"
    
    def __repr__(self) -> str:
        return self.__str__()