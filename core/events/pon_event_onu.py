"""
ONU híbrida con generación asíncrona de tráfico y colas por T-CONT
Arquitectura event-driven con timing exacto
"""

import random
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from .event_queue import EventQueue, EventType


@dataclass
class Packet:
    """Paquete de datos con información completa"""
    packet_id: str
    onu_id: str
    tcont_type: str
    size_bytes: int
    arrival_time: float
    priority: int
    data: Dict[str, Any]
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


class TContQueue:
    """Cola para un T-CONT específico"""
    
    def __init__(self, tcont_id: str, max_bytes: int = 1024 * 1024):  # 1MB default
        self.tcont_id = tcont_id
        self.max_bytes = max_bytes
        self.packets = []
        self.total_bytes = 0
        self.dropped_packets = 0
        self.total_packets_received = 0
        
    def add_packet(self, packet: Packet) -> bool:
        """
        Agregar paquete a la cola
        
        Args:
            packet: Paquete a agregar
            
        Returns:
            True si se agregó, False si se descartó por overflow
        """
        self.total_packets_received += 1
        
        if self.total_bytes + packet.size_bytes > self.max_bytes:
            # Buffer overflow
            self.dropped_packets += 1
            return False
        
        self.packets.append(packet)
        self.total_bytes += packet.size_bytes
        return True
    
    def transmit_packets(self, max_bytes: int) -> Tuple[List[Packet], int]:
        """
        Transmitir paquetes hasta agotar grant o cola
        
        Args:
            max_bytes: Máximo bytes a transmitir (grant)
            
        Returns:
            (paquetes_transmitidos, bytes_transmitidos)
        """
        transmitted_packets = []
        transmitted_bytes = 0
        
        while self.packets and transmitted_bytes < max_bytes:
            packet = self.packets[0]
            
            if transmitted_bytes + packet.size_bytes <= max_bytes:
                # Puede transmitir el paquete completo
                packet = self.packets.pop(0)
                transmitted_packets.append(packet)
                transmitted_bytes += packet.size_bytes
                self.total_bytes -= packet.size_bytes
            else:
                # No cabe el siguiente paquete
                break
        
        return transmitted_packets, transmitted_bytes
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual de la cola"""
        return {
            'tcont_id': self.tcont_id,
            'queue_bytes': self.total_bytes,
            'queue_packets': len(self.packets),
            'dropped_packets': self.dropped_packets,
            'utilization': self.total_bytes / self.max_bytes if self.max_bytes > 0 else 0
        }
    
    def is_empty(self) -> bool:
        """Verificar si la cola está vacía"""
        return len(self.packets) == 0
    
    def clear(self):
        """Limpiar la cola"""
        self.packets.clear()
        self.total_bytes = 0


class HybridONU:
    """
    ONU con generación asíncrona de tráfico
    Implementa protocolo PON real con timing exacto
    """
    
    def __init__(self, onu_id: str, lambda_rate: float, scenario_config: Dict[str, Any]):
        """
        Args:
            onu_id: Identificador único de la ONU
            lambda_rate: Tasa de llegada de paquetes (paquetes/segundo)
            scenario_config: Configuración del escenario de tráfico
        """
        self.onu_id = onu_id
        self.lambda_rate = lambda_rate
        self.scenario_config = scenario_config
        
        # Colas separadas por T-CONT
        self.queues = {
            'highest': TContQueue('highest', 512 * 1024),  # 512KB
            'high': TContQueue('high', 512 * 1024),
            'medium': TContQueue('medium', 1024 * 1024),   # 1MB
            'low': TContQueue('low', 1024 * 1024),
            'lowest': TContQueue('lowest', 256 * 1024)     # 256KB
        }
        
        # Distribución de tipos de tráfico por T-CONT
        self.traffic_distribution = scenario_config.get('traffic_probs_range', {
            'highest': (0.1, 0.3),
            'high': (0.2, 0.4),
            'medium': (0.3, 0.6),
            'low': (0.2, 0.5),
            'lowest': (0.1, 0.2)
        })
        
        # Tamaños de paquetes por T-CONT
        self.packet_sizes = scenario_config.get('traffic_sizes_mb', {
            'highest': (0.050, 0.100),  # 50-100KB
            'high': (0.030, 0.070),     # 30-70KB
            'medium': (0.010, 0.025),   # 10-25KB
            'low': (0.005, 0.015),      # 5-15KB
            'lowest': (0.001, 0.005)    # 1-5KB
        })
        
        # Estado de generación de tráfico
        self.next_packet_time = 0.0
        self.packet_counter = 0
        self.total_packets_generated = 0
        self.total_bytes_generated = 0
        
        # Estadísticas
        self.stats = {
            'packets_generated': 0,
            'bytes_generated': 0,
            'packets_transmitted': 0,
            'bytes_transmitted': 0,
            'reports_sent': 0,
            'grants_received': 0
        }
        
    def schedule_first_packet(self, event_queue: EventQueue, start_time: float):
        """
        Programar el primer paquete con distribución exponencial
        
        Args:
            event_queue: Cola de eventos del simulador
            start_time: Tiempo de inicio de la simulación
        """
        # Tiempo hasta el primer paquete (exponencial)
        inter_arrival = random.expovariate(self.lambda_rate)
        self.next_packet_time = start_time + inter_arrival
        
        event_queue.schedule_event(
            self.next_packet_time,
            EventType.PACKET_GENERATED,
            self.onu_id,
            {'packet_sequence': 0}
        )
        
    def generate_packet(self, event_queue: EventQueue, current_time: float):
        """
        Generar un nuevo paquete y programar el siguiente
        
        Args:
            event_queue: Cola de eventos del simulador
            current_time: Tiempo actual de la simulación
        """
        # Crear paquete
        packet = self._create_packet(current_time)
        
        # Intentar agregarlo a la cola correspondiente
        queue = self.queues[packet.tcont_type]
        success = queue.add_packet(packet)
        
        if success:
            self.stats['packets_generated'] += 1
            self.stats['bytes_generated'] += packet.size_bytes
            self.total_packets_generated += 1
            self.total_bytes_generated += packet.size_bytes
        # Si falla, el paquete se descarta (buffer overflow)
        
        # Programar siguiente paquete
        inter_arrival = random.expovariate(self.lambda_rate)
        self.next_packet_time = current_time + inter_arrival
        
        event_queue.schedule_event(
            self.next_packet_time,
            EventType.PACKET_GENERATED,
            self.onu_id,
            {'packet_sequence': self.packet_counter + 1}
        )
        
        self.packet_counter += 1
    
    def _create_packet(self, arrival_time: float) -> Packet:
        """
        Crear un paquete según las distribuciones configuradas
        
        Args:
            arrival_time: Tiempo de llegada del paquete
            
        Returns:
            Paquete creado
        """
        # Seleccionar tipo de T-CONT según distribución
        tcont_type = self._select_tcont_type()
        
        # Seleccionar tamaño según rango del T-CONT
        size_range = self.packet_sizes[tcont_type]
        size_mb = random.uniform(size_range[0], size_range[1])
        size_bytes = int(size_mb * 1024 * 1024)  # Convertir MB a bytes
        
        # Prioridad según T-CONT
        priority_map = {'highest': 1, 'high': 2, 'medium': 3, 'low': 4, 'lowest': 5}
        priority = priority_map[tcont_type]
        
        return Packet(
            packet_id=f"{self.onu_id}_pkt_{self.packet_counter}",
            onu_id=self.onu_id,
            tcont_type=tcont_type,
            size_bytes=size_bytes,
            arrival_time=arrival_time,
            priority=priority,
            data={'scenario': self.scenario_config.get('description', 'unknown')}
        )
    
    def _select_tcont_type(self) -> str:
        """
        Seleccionar tipo de T-CONT según distribuciones probabilísticas
        
        Returns:
            Tipo de T-CONT seleccionado
        """
        # Generar probabilidades actuales basadas en rangos
        current_probs = {}
        for tcont, (min_prob, max_prob) in self.traffic_distribution.items():
            current_probs[tcont] = random.uniform(min_prob, max_prob)
        
        # Selección aleatoria ponderada
        total_weight = sum(current_probs.values())
        random_value = random.uniform(0, total_weight)
        
        cumulative = 0
        for tcont, prob in current_probs.items():
            cumulative += prob
            if random_value <= cumulative:
                return tcont
        
        # Fallback
        return 'medium'
    
    def get_queue_status(self) -> Dict[str, int]:
        """
        Obtener estado de todas las colas (para reports)
        
        Returns:
            Contadores de bytes por T-CONT
        """
        self.stats['reports_sent'] += 1
        return {
            tcont: queue.total_bytes
            for tcont, queue in self.queues.items()
        }
    
    def transmit_from_queue(self, tcont_id: str, grant_bytes: int) -> Tuple[List[Packet], int]:
        """
        Transmitir paquetes de una cola específica
        
        Args:
            tcont_id: ID del T-CONT a transmitir
            grant_bytes: Bytes otorgados para transmisión
            
        Returns:
            (paquetes_transmitidos, bytes_transmitidos)
        """
        if tcont_id not in self.queues:
            return [], 0
        
        queue = self.queues[tcont_id]
        packets, bytes_transmitted = queue.transmit_packets(grant_bytes)
        
        # Actualizar estadísticas
        self.stats['packets_transmitted'] += len(packets)
        self.stats['bytes_transmitted'] += bytes_transmitted
        
        return packets, bytes_transmitted
    
    def receive_grant(self, grants: Dict[str, int]):
        """
        Recibir grants del OLT
        
        Args:
            grants: Dict de {tcont_id: bytes_granted}
        """
        self.stats['grants_received'] += 1
        # Los grants se procesan en handle_transmission_start
    
    def get_onu_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas completas de la ONU"""
        queue_stats = {
            tcont: queue.get_status()
            for tcont, queue in self.queues.items()
        }
        
        return {
            'onu_id': self.onu_id,
            'lambda_rate': self.lambda_rate,
            'scenario': self.scenario_config.get('description', 'unknown'),
            'stats': self.stats.copy(),
            'queue_status': queue_stats,
            'total_queue_bytes': sum(q.total_bytes for q in self.queues.values()),
            'total_queue_packets': sum(len(q.packets) for q in self.queues.values())
        }
    
    def reset_statistics(self):
        """Reiniciar estadísticas (mantener configuración)"""
        self.stats = {
            'packets_generated': 0,
            'bytes_generated': 0,
            'packets_transmitted': 0,
            'bytes_transmitted': 0,
            'reports_sent': 0,
            'grants_received': 0
        }
        
        for queue in self.queues.values():
            queue.dropped_packets = 0
            queue.total_packets_received = 0
    
    def clear_queues(self):
        """Limpiar todas las colas (para reset completo)"""
        for queue in self.queues.values():
            queue.clear()
        
        self.packet_counter = 0
        self.total_packets_generated = 0
        self.total_bytes_generated = 0