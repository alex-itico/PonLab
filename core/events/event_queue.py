"""
Sistema de cola de eventos para simulación PON híbrida
Control temporal estricto - sin colisiones de transmisión
"""

import heapq
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class EventType(Enum):
    """Tipos de eventos en la simulación PON"""
    PACKET_GENERATED = "packet_generated"
    POLLING_CYCLE = "polling_cycle"
    DBA_DECISION = "dba_decision"
    GRANT_START = "grant_start"
    TRANSMISSION_COMPLETE = "transmission_complete"


@dataclass
class Event:
    """Evento de simulación con timestamp exacto"""
    timestamp: float
    event_type: EventType
    onu_id: str
    data: Dict[str, Any]
    
    def __lt__(self, other):
        return self.timestamp < other.timestamp
    
    def __eq__(self, other):
        return self.timestamp == other.timestamp
    
    def __repr__(self):
        return f"Event({self.timestamp:.6f}us, {self.event_type.value}, {self.onu_id})"


class EventQueue:
    """
    Cola de eventos ordenada por timestamp
    Garantiza orden temporal estricto
    """
    
    def __init__(self):
        self.events = []  # heap queue
        self.current_time = 0.0
        self.event_count = 0
        
    def schedule_event(self, timestamp: float, event_type: EventType, 
                      onu_id: str, data: Dict[str, Any] = None):
        """
        Programar evento en timestamp específico
        
        Args:
            timestamp: Tiempo exacto del evento en segundos
            event_type: Tipo de evento
            onu_id: ID de la ONU asociada (o 'OLT' para eventos del OLT)
            data: Datos adicionales del evento
        """
        if data is None:
            data = {}
            
        event = Event(timestamp, event_type, onu_id, data)
        heapq.heappush(self.events, event)
        self.event_count += 1
        
    def get_next_event(self) -> Optional[Event]:
        """Obtener el próximo evento cronológicamente"""
        if self.events:
            event = heapq.heappop(self.events)
            self.current_time = event.timestamp
            return event
        return None
    
    def peek_next_time(self) -> float:
        """Ver el timestamp del próximo evento sin procesarlo"""
        return self.events[0].timestamp if self.events else float('inf')
    
    def has_events(self) -> bool:
        """Verificar si hay eventos pendientes"""
        return len(self.events) > 0
    
    def get_pending_events_count(self) -> int:
        """Obtener número de eventos pendientes"""
        return len(self.events)
    
    def clear(self):
        """Limpiar todos los eventos"""
        self.events.clear()
        self.event_count = 0
        self.current_time = 0.0


class TimeSlotManager:
    """
    Gestor de time-slots para evitar colisiones de transmisión
    Garantiza que solo una ONU transmita a la vez
    """
    
    def __init__(self, channel_capacity_mbps: float = 1024.0):
        """
        Args:
            channel_capacity_mbps: Capacidad del canal en Mbps
        """
        self.channel_capacity = channel_capacity_mbps
        self.current_transmission_end = 0.0  # Cuándo termina la transmisión actual
        self.transmission_log = []  # Para debugging
        
    def calculate_transmission_time(self, data_size_mb: float) -> float:
        """
        Calcular tiempo necesario para transmitir datos
        
        Args:
            data_size_mb: Tamaño de datos en MB
            
        Returns:
            Tiempo de transmisión en segundos
        """
        if data_size_mb <= 0:
            return 0.0
            
        # Tiempo = Datos / Velocidad
        # MB / (Mbps / 8) = MB / (MB/s) = segundos
        transmission_time = data_size_mb / (self.channel_capacity / 8)
        return transmission_time
    
    def allocate_time_slot(self, onu_id: str, tcont_id: str, 
                          data_size_mb: float, earliest_start: float) -> tuple[float, float]:
        """
        Asignar time-slot exclusivo para transmisión
        
        Args:
            onu_id: ID de la ONU
            tcont_id: ID del T-CONT
            data_size_mb: Tamaño de datos a transmitir
            earliest_start: Tiempo más temprano posible de inicio
            
        Returns:
            (start_time, end_time) del slot asignado
        """
        transmission_duration = self.calculate_transmission_time(data_size_mb)
        
        if transmission_duration == 0:
            return earliest_start, earliest_start
        
        # El slot no puede empezar antes de que termine la transmisión actual
        start_time = max(earliest_start, self.current_transmission_end)
        end_time = start_time + transmission_duration
        
        # Actualizar cuándo termina la próxima transmisión
        self.current_transmission_end = end_time
        
        # Log para debugging
        self.transmission_log.append({
            'onu_id': onu_id,
            'tcont_id': tcont_id,
            'start_time': start_time,
            'end_time': end_time,
            'duration': transmission_duration,
            'data_size_mb': data_size_mb
        })
        
        return start_time, end_time
    
    def get_channel_utilization(self, total_time: float) -> float:
        """
        Calcular utilización del canal en un período
        
        Args:
            total_time: Tiempo total del período
            
        Returns:
            Porcentaje de utilización (0-100)
        """
        if total_time <= 0 or not self.transmission_log:
            return 0.0
            
        total_transmission_time = sum(
            entry['duration'] for entry in self.transmission_log
        )
        
        utilization = (total_transmission_time / total_time) * 100
        return min(utilization, 100.0)  # Cap at 100%
    
    def reset(self):
        """Reiniciar el gestor de time-slots"""
        self.current_transmission_end = 0.0
        self.transmission_log.clear()
    
    def get_transmission_log(self) -> List[Dict]:
        """Obtener log de transmisiones para debugging"""
        return self.transmission_log.copy()


class CycleTimeManager:
    """
    Gestor de timing para ciclos DBA
    Garantiza ciclos regulares de 125us
    """
    
    def __init__(self, cycle_duration: float = 125e-6):
        """
        Args:
            cycle_duration: Duración del ciclo DBA en segundos (default: 125us)
        """
        self.cycle_duration = cycle_duration
        self.current_cycle = 0
        self.cycle_start_times = []
        self.last_scheduled_cycle_time = -1.0  # Evitar ciclos duplicados
        
    def get_next_cycle_start(self, current_time: float) -> float:
        """
        Obtener timestamp del próximo ciclo DBA
        
        Args:
            current_time: Tiempo actual
            
        Returns:
            Timestamp del próximo ciclo
        """
        # Si es el primer ciclo, empezar en el primer intervalo
        if self.last_scheduled_cycle_time < 0:
            next_cycle_time = self.cycle_duration
        else:
            # Siguiente ciclo es simplemente agregar la duración
            next_cycle_time = self.last_scheduled_cycle_time + self.cycle_duration
        
        self.last_scheduled_cycle_time = next_cycle_time
        self.current_cycle += 1
        self.cycle_start_times.append(next_cycle_time)
        
        return next_cycle_time
    
    def get_cycle_phases(self, cycle_start: float) -> Dict[str, tuple[float, float]]:
        """
        Obtener fases del ciclo DBA con timestamps exactos
        
        Args:
            cycle_start: Tiempo de inicio del ciclo
            
        Returns:
            Dict con fases y sus (start_time, end_time)
        """
        return {
            'report_phase': (cycle_start, cycle_start + 40e-6),  # 0-40us
            'dba_processing': (cycle_start + 40e-6, cycle_start + 50e-6),  # 40-50us
            'transmission_phase': (cycle_start + 50e-6, cycle_start + self.cycle_duration)  # 50-125us
        }
    
    def is_in_transmission_phase(self, current_time: float) -> bool:
        """
        Verificar si el tiempo actual está en fase de transmisión
        
        Args:
            current_time: Tiempo actual
            
        Returns:
            True si está en fase de transmisión
        """
        cycle_position = current_time % self.cycle_duration
        return cycle_position >= 50e-6  # Después de 50us del ciclo
    
    def get_current_cycle_number(self, current_time: float) -> int:
        """Obtener número del ciclo actual"""
        return int(current_time / self.cycle_duration)
    
    def get_cycle_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas de ciclos ejecutados"""
        return {
            'total_cycles': len(self.cycle_start_times),
            'cycle_duration': self.cycle_duration,
            'cycles_per_second': 1.0 / self.cycle_duration,
            'last_cycle_time': self.cycle_start_times[-1] if self.cycle_start_times else 0.0
        }