"""
PON ONU
Unidad de Red Óptica integrada de netPONPy con generación de tráfico realista
"""

import numpy as np
from typing import Dict, Optional, List, TYPE_CHECKING
from .pon_types import Traffic_Probability
from ..data.pon_request import Request
from ..data.pon_buffer import Buffer
from ..data.pon_queue import Queue

# Importación diferida para evitar ciclos
if TYPE_CHECKING:
    from ..connections.pon_connection import Connection


class ONU:
    """Optical Network Unit - Unidad de Red Óptica"""
    
    def __init__(
        self,
        id: str,
        name: str,
        traffic_transmition_probs: Traffic_Probability = {
            "highest": 0.5,
            "high": 0.7,
            "medium": 0.8,
            "low": 0.6,
            "lowest": 0.9,
        },
        transmission_rate: float = 1024.0,  # Mbps (corregido typo)
        service_level_agreement: float = 1024.0,  # Mbps
        buffer_size: int = 512,  # Número máximo de solicitudes en buffer
        mean_arrival_rate: Optional[float] = None,  # requests/second
        avg_request_size_mb: float = 0.015,  # 15KB por request por defecto
        traffic_sizes_mb: Optional[Dict[str, tuple]] = None,  # Tamaños por tipo
    ):
        """
        Inicializar ONU con generación de tráfico realista
        
        Args:
            id: Identificador único de la ONU
            name: Nombre descriptivo
            traffic_transmition_probs: Probabilidades por tipo de tráfico
            transmission_rate: Tasa de transmisión en Mbps (corregido typo)
            service_level_agreement: SLA en Mbps
            buffer_size: Capacidad máxima del buffer
            mean_arrival_rate: Tasa media de llegadas (req/s)
            avg_request_size_mb: Tamaño promedio de solicitud en MB
        """
        self._id = id
        self._name = name
        self.traffic_transmition_probs = traffic_transmition_probs
        self.buffer_size = buffer_size
        self.avg_request_size_mb = avg_request_size_mb
        self.traffic_sizes_mb = traffic_sizes_mb or {
            "highest": (0.050, 0.100),  # 50-100KB por defecto
            "high": (0.030, 0.070),     # 30-70KB
            "medium": (0.010, 0.025),   # 10-25KB
            "low": (0.005, 0.015),      # 5-15KB
            "lowest": (0.001, 0.005)    # 1-5KB
        }
        self.transmission_rate = transmission_rate  # Corregido typo
        self.service_level_agreement = service_level_agreement
        
        # Calcular tasa de llegadas si no se proporciona
        if mean_arrival_rate is None:
            # Cálculo simple basado en SLA y buffer
            simple_rate = service_level_agreement / buffer_size
            mean_arrival_rate = max(10.0, min(simple_rate, 200.0))  # Entre 10-200 req/s
            
        # Inicializar sistema de colas
        self.queue = Queue(mean_arrival_rate)
        
        # Inicializar estadísticas ANTES de crear requests
        self.lost_packets_count = 0
        self.total_requests_generated = 0
        self.total_data_transmitted = 0.0  # MB
        self.polls_received = 0
        self.responses_sent = 0
        
        # Inicializar buffer de solicitudes
        self.buffer = Buffer(buffer_size)
        
        # Inicializar con algunas solicitudes (después de stats)
        self.buffer.append(self._create_request())
        self.buffer.append(self._create_request())

    @property
    def id(self) -> str:
        return self._id

    @property 
    def name(self) -> str:
        return self._name
    
    def _create_request(self) -> Request:
        """
        Crear nueva solicitud de transmisión con tráfico realista
        
        Returns:
            Nueva solicitud generada
        """
        traffic: Dict[str, float] = {}
        
        # Generar tráfico según probabilidades configuradas
        for traffic_type, probability in self.traffic_transmition_probs.items():
            should_transmit = np.random.choice([0, 1], p=[1 - probability, probability])
            if should_transmit:
                # Usar tamaño variable según tipo de tráfico
                size_range = self.traffic_sizes_mb.get(traffic_type, (self.avg_request_size_mb, self.avg_request_size_mb))
                min_size, max_size = size_range
                traffic_size = np.random.uniform(min_size, max_size)
                traffic[traffic_type] = traffic_size
        
        # Obtener evento de la cola (tiempo de llegada)
        event = self.queue.get()
        
        # Actualizar contador
        self.total_requests_generated += 1
        
        return Request(self.id, traffic, event.arrival_time)
    
    def report(self, time: float) -> Optional[List[Request]]:
        """
        Responder a polling del OLT generando nuevas solicitudes si es necesario
        
        Args:
            time: Tiempo actual de simulación
            
        Returns:
            Lista de solicitudes en buffer o None si está vacío
        """
        self.polls_received += 1
        
        # Generar nuevas solicitudes hasta el tiempo actual
        while time >= self.queue.last_arrival_time:
            request = self._create_request()
            
            # Intentar agregar al buffer
            if not self.buffer.append(request):
                # Buffer lleno - contar como paquete perdido
                self.lost_packets_count += 1
                print(f"ONU {self.id}: Packet lost at t={time:.3f}, buffer full ({len(self.buffer)}/{self.buffer.size})")

        # Retornar contenido del buffer
        if not self.buffer:
            return None
        return list(self.buffer)

    def transmit(self, request_id_to_transmit: str, connection: "Connection", time_slot: float) -> bool:
        """
        Transmitir solicitud específica
        
        Args:
            request_id_to_transmit: ID de la solicitud a transmitir
            connection: Conexión para transmitir
            time_slot: Duración de la ventana de transmisión
            
        Returns:
            True si la transmisión fue exitosa
        """
        # Buscar solicitud en buffer
        request_to_send = None
        request_index = -1
        
        for i, req_in_buffer in enumerate(self.buffer):
            if str(req_in_buffer.id) == str(request_id_to_transmit):
                request_to_send = req_in_buffer
                request_index = i
                break
        
        if request_to_send is None:
            raise ValueError(
                f"ONU {self._id}: Request with id {request_id_to_transmit} was not found in the buffer."
            )
        
        # Intentar transmisión
        success = connection.flush(request_to_send, time_slot)
        
        if success:
            # Transmisión exitosa - remover del buffer
            self.release_traffic(request_id_to_transmit)
            self.responses_sent += 1
            self.total_data_transmitted += request_to_send.get_total_traffic()
            return True
        else:
            return False

    def release_traffic(self, request_id_to_remove: str):
        """
        Liberar solicitud del buffer
        
        Args:
            request_id_to_remove: ID de la solicitud a remover
        """
        for i, req_in_buffer in enumerate(self.buffer):
            if str(req_in_buffer.id) == str(request_id_to_remove):
                self.buffer.pop(i)
                break

    def get_buffer_occupancy(self) -> float:
        """Obtener nivel de ocupación del buffer (0.0-1.0)"""
        return len(self.buffer) / self.buffer.size if self.buffer.size > 0 else 0.0

    def get_onu_stats(self) -> dict:
        """Obtener estadísticas completas de la ONU"""
        response_rate = (self.responses_sent / self.polls_received * 100) if self.polls_received > 0 else 0
        
        return {
            'id': self.id,
            'name': self.name,
            'transmission_rate': self.transmission_rate,  # Corregido typo
            'sla': self.service_level_agreement,
            'buffer_occupancy': self.get_buffer_occupancy(),
            'buffer_stats': self.buffer.get_buffer_stats(),
            'queue_stats': self.queue.get_queue_stats(),
            'total_requests_generated': self.total_requests_generated,
            'lost_packets_count': self.lost_packets_count,
            'polls_received': self.polls_received,
            'responses_sent': self.responses_sent,
            'response_rate': response_rate,
            'data_transmitted': self.total_data_transmitted
        }
    
    def reset_stats(self):
        """Reiniciar estadísticas de la ONU"""
        self.lost_packets_count = 0
        self.total_requests_generated = 0
        self.total_data_transmitted = 0.0
        self.polls_received = 0
        self.responses_sent = 0
        self.buffer.reset_stats()
        
    def __str__(self) -> str:
        return f"ONU(id={self.id}, name={self.name}, buffer_occupancy={self.get_buffer_occupancy():.1%})"
    
    def __repr__(self) -> str:
        return self.__str__()