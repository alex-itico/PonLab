"""
PON Event
Sistema de eventos discretos integrado de netPONPy
"""


class Event:
    """Evento discreto en la simulación PON"""
    
    def __init__(self, start_time: float):
        """
        Inicializar evento
        
        Args:
            start_time: Tiempo de llegada del evento
        """
        self._arrival_time = start_time

    @property
    def arrival_time(self) -> float:
        """Tiempo de llegada del evento"""
        return self._arrival_time
    
    def __str__(self) -> str:
        return f"Event(arrival_time={self._arrival_time:.6f})"
    
    def __repr__(self) -> str:
        return self.__str__()