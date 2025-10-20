"""
Generador de tráfico eficiente sin explosión de eventos
Genera paquetes en batch usando proceso Poisson precalculado
"""

import numpy as np
import random
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class PreGeneratedPacket:
    """Paquete pregenerado con timestamp"""
    arrival_time: float
    tcont_type: str
    size_bytes: int
    packet_id: str
    priority: int


class BatchTrafficGenerator:
    """
    Generador de tráfico en batch que precalcula todos los paquetes
    Evita explosión de eventos en la cola
    """

    def __init__(self, onu_id: str, lambda_rate: float, scenario_config: Dict,
                 simulation_duration: float):
        """
        Args:
            onu_id: ID de la ONU
            lambda_rate: Tasa de llegada (paquetes/segundo)
            scenario_config: Configuración del escenario
            simulation_duration: Duración total de la simulación
        """
        self.onu_id = onu_id
        self.lambda_rate = lambda_rate
        self.scenario_config = scenario_config
        self.simulation_duration = simulation_duration

        # Distribución de tipos de tráfico
        self.traffic_distribution = scenario_config.get('traffic_probs_range', {
            'highest': (0.1, 0.3),
            'high': (0.2, 0.4),
            'medium': (0.3, 0.6),
            'low': (0.2, 0.5),
            'lowest': (0.1, 0.2)
        })

        # Tamaños de paquetes
        self.packet_sizes = scenario_config.get('traffic_sizes_mb', {
            'highest': (0.050, 0.100),
            'high': (0.030, 0.070),
            'medium': (0.010, 0.025),
            'low': (0.005, 0.015),
            'lowest': (0.001, 0.005)
        })

        # Prioridades
        self.priority_map = {
            'highest': 1, 'high': 2, 'medium': 3, 'low': 4, 'lowest': 5
        }

        # Paquetes pregenerados
        self.packets: List[PreGeneratedPacket] = []
        self.current_index = 0

        # Generar todos los paquetes al inicio
        self._pregenerate_all_packets()

    def _pregenerate_all_packets(self):
        """Pregenerar todos los paquetes usando proceso Poisson"""

        # Calcular número esperado de paquetes
        expected_packets = int(self.lambda_rate * self.simulation_duration * 1.2)  # +20% buffer

        # Generar timestamps usando distribución exponencial (proceso Poisson)
        inter_arrivals = np.random.exponential(1.0 / self.lambda_rate, expected_packets)
        arrival_times = np.cumsum(inter_arrivals)

        # Filtrar solo los que caen dentro del tiempo de simulación
        valid_arrivals = arrival_times[arrival_times < self.simulation_duration]

        print(f"  ONU {self.onu_id}: Pregenerando {len(valid_arrivals)} paquetes "
              f"(λ={self.lambda_rate:.1f} pkt/s, T={self.simulation_duration:.1f}s)")

        # Crear paquetes
        for i, arrival_time in enumerate(valid_arrivals):
            # Seleccionar tipo de T-CONT
            tcont_type = self._select_tcont_type()

            # Seleccionar tamaño
            size_range = self.packet_sizes[tcont_type]
            size_mb = random.uniform(size_range[0], size_range[1])
            size_bytes = int(size_mb * 1024 * 1024)

            # Crear paquete
            packet = PreGeneratedPacket(
                arrival_time=float(arrival_time),
                tcont_type=tcont_type,
                size_bytes=size_bytes,
                packet_id=f"{self.onu_id}_pkt_{i}",
                priority=self.priority_map[tcont_type]
            )

            self.packets.append(packet)

        # Ordenar por tiempo de llegada (debería estar ordenado, pero asegurar)
        self.packets.sort(key=lambda p: p.arrival_time)

        print(f"    Total bytes: {sum(p.size_bytes for p in self.packets) / (1024*1024):.2f} MB")

    def _select_tcont_type(self) -> str:
        """Seleccionar tipo de T-CONT según distribuciones"""
        # Generar probabilidades
        current_probs = {}
        for tcont, (min_prob, max_prob) in self.traffic_distribution.items():
            current_probs[tcont] = random.uniform(min_prob, max_prob)

        # Selección ponderada
        total_weight = sum(current_probs.values())
        random_value = random.uniform(0, total_weight)

        cumulative = 0
        for tcont, prob in current_probs.items():
            cumulative += prob
            if random_value <= cumulative:
                return tcont

        return 'medium'

    def get_packets_until(self, current_time: float) -> List[PreGeneratedPacket]:
        """
        Obtener todos los paquetes que han llegado hasta current_time

        Args:
            current_time: Tiempo actual de simulación

        Returns:
            Lista de paquetes que llegaron hasta current_time
        """
        arrived_packets = []

        while self.current_index < len(self.packets):
            packet = self.packets[self.current_index]

            if packet.arrival_time <= current_time:
                arrived_packets.append(packet)
                self.current_index += 1
            else:
                break

        return arrived_packets

    def get_next_arrival_time(self) -> float:
        """Obtener tiempo del próximo paquete"""
        if self.current_index < len(self.packets):
            return self.packets[self.current_index].arrival_time
        return float('inf')

    def has_more_packets(self) -> bool:
        """Verificar si quedan más paquetes"""
        return self.current_index < len(self.packets)

    def get_statistics(self) -> Dict:
        """Obtener estadísticas del generador"""
        return {
            'total_packets_generated': len(self.packets),
            'packets_delivered': self.current_index,
            'packets_remaining': len(self.packets) - self.current_index,
            'total_bytes': sum(p.size_bytes for p in self.packets),
            'lambda_rate': self.lambda_rate
        }
