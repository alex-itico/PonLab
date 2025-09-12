"""
PON Queue
Sistema de colas para generación de tráfico integrado de netPONPy
"""

from .pon_event import Event
from .pon_random import ExpVariable


class Queue:
    """Cola de eventos para generación de tráfico Poisson"""
    
    def __init__(self, mLambda: float = 500, seed: int = 12345):
        """
        Inicializar cola de eventos
        
        Args:
            mLambda: Tasa de llegadas (eventos por segundo)
            seed: Semilla para reproducibilidad
        """
        self.__seed = seed
        self.__lambda = mLambda
        self.__arriveVariable = ExpVariable(self.__seed, self.__lambda)
        self.last_arrival_time = 0.0
        
        # Estadísticas
        self.total_events_generated = 0
        self.average_interarrival_time = 0.0

    def get(self) -> Event:
        """
        Obtener siguiente evento en la cola
        
        Returns:
            Event: Próximo evento generado
        """
        # Generar tiempo entre arribos según distribución exponencial
        interarrival_time = self.__arriveVariable.getNextValue()
        
        # Crear evento en el tiempo absoluto
        event = Event(self.last_arrival_time + interarrival_time)
        self.last_arrival_time = event.arrival_time
        
        # Actualizar estadísticas
        self.total_events_generated += 1
        if self.total_events_generated > 1:
            # Calcular promedio móvil del tiempo entre arribos
            new_avg = ((self.average_interarrival_time * (self.total_events_generated - 1)) + 
                      interarrival_time) / self.total_events_generated
            self.average_interarrival_time = new_avg
        else:
            self.average_interarrival_time = interarrival_time
        
        return event
    
    def get_queue_stats(self) -> dict:
        """Obtener estadísticas de la cola"""
        theoretical_rate = self.__lambda
        empirical_rate = (1 / self.average_interarrival_time) if self.average_interarrival_time > 0 else 0
        
        return {
            'theoretical_lambda': theoretical_rate,
            'empirical_lambda': empirical_rate,
            'total_events_generated': self.total_events_generated,
            'last_arrival_time': self.last_arrival_time,
            'average_interarrival_time': self.average_interarrival_time,
            'seed': self.__seed
        }
    
    def reset(self, new_lambda: float = None):
        """
        Reiniciar la cola
        
        Args:
            new_lambda: Nueva tasa de arribos (opcional)
        """
        if new_lambda is not None:
            self.__lambda = new_lambda
            self.__arriveVariable = ExpVariable(self.__seed, self.__lambda)
        
        self.last_arrival_time = 0.0
        self.total_events_generated = 0
        self.average_interarrival_time = 0.0
    
    def __str__(self) -> str:
        return f"Queue(lambda={self.__lambda}, events_generated={self.total_events_generated})"
    
    def __repr__(self) -> str:
        return self.__str__()