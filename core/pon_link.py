"""
PON Link
Clase de enlace óptico integrada de netPONPy
"""

from .pon_request import Request


class Link:
    """Enlace óptico en una red PON"""
    
    def __init__(
        self,
        id: str,
        length: float,
    ):
        """
        Inicializar enlace óptico
        
        Args:
            id: Identificador único del enlace
            length: Longitud del enlace en km
        """
        self.id = id
        self.length = length
        self.bitrate_transmitted = 0.0  # MB transmitidos acumulados
        self.time_on = 0.0  # Tiempo activo acumulado en segundos
        
        # Estadísticas adicionales
        self.total_requests = 0
        self.utilization_history = []

    def update(self, request: Request, time_slot: float):
        """
        Actualizar estadísticas del enlace tras una transmisión
        
        Args:
            request: Solicitud transmitida
            time_slot: Duración de la transmisión en segundos
        """
        # Actualizar estadísticas básicas
        self.bitrate_transmitted += request.get_total_traffic()
        self.time_on += time_slot
        self.total_requests += 1
        
        # Calcular utilización instantánea
        if time_slot > 0:
            instantaneous_rate = request.get_total_traffic() / time_slot  # MB/s
            self.utilization_history.append({
                'timestamp': request.created_at,
                'rate_mbps': instantaneous_rate,
                'duration': time_slot
            })
    
    def get_average_utilization(self) -> float:
        """Obtener utilización promedio del enlace en MB/s"""
        if self.time_on == 0:
            return 0.0
        return self.bitrate_transmitted / self.time_on
    
    def get_link_stats(self) -> dict:
        """Obtener estadísticas completas del enlace"""
        return {
            'id': self.id,
            'length_km': self.length,
            'total_transmitted_mb': self.bitrate_transmitted,
            'total_active_time_s': self.time_on,
            'total_requests': self.total_requests,
            'avg_utilization_mbps': self.get_average_utilization(),
            'utilization_samples': len(self.utilization_history)
        }
    
    def reset_stats(self):
        """Reiniciar estadísticas del enlace"""
        self.bitrate_transmitted = 0.0
        self.time_on = 0.0
        self.total_requests = 0
        self.utilization_history.clear()
    
    def __str__(self) -> str:
        return f"Link(id={self.id}, length={self.length}km, transmitted={self.bitrate_transmitted:.3f}MB)"
    
    def __repr__(self) -> str:
        return self.__str__()