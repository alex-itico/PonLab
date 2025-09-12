"""
PON Connection
Clase de conexión integrada de netPONPy
"""

from typing import List
from .pon_types import Path
from .pon_request import Request
from .pon_link import Link


class Connection:
    """Conexión de transmisión en una red PON"""
    
    def __init__(
        self,
        clock: float,
        path: Path,
        speed: float = 500.0,
        protocol: str = "EPON",
    ):
        """
        Inicializar conexión PON
        
        Args:
            clock: Tiempo actual del sistema
            path: Ruta de enlaces por donde transmitir
            speed: Velocidad máxima de transmisión en Mbps
            protocol: Protocolo usado (EPON, GPON, etc.)
        """
        self.created_at = clock
        self.path = path
        self.speed = speed  # Mbps
        self.protocol = protocol
        
        # Estadísticas de la conexión
        self.total_data_transmitted = 0.0  # MB
        self.transmission_count = 0
        self.success_rate = 1.0

    def flush(self, request: Request, time_slot: float, bit_error_rate: float = 10e-9) -> bool:
        """
        Transmitir solicitud a través de la conexión
        
        Args:
            request: Solicitud a transmitir
            time_slot: Duración de la ventana de transmisión
            bit_error_rate: Tasa de error de bits
            
        Returns:
            True si la transmisión fue exitosa
        """
        try:
            # Calcular si la transmisión es físicamente posible
            data_size_mb = request.get_total_traffic()
            max_transmissible = (self.speed * time_slot) / 8  # Convertir Mbps*s a MB
            
            if data_size_mb > max_transmissible:
                print(f"⚠️ Warning: Request size ({data_size_mb:.3f}MB) exceeds transmission capacity ({max_transmissible:.3f}MB)")
                # En una implementación real, esto podría fragmentar la transmisión
                # Por ahora, transmitimos lo que sea posible
                data_size_mb = max_transmissible
            
            # Actualizar estadísticas de cada enlace en la ruta
            for link in self.path:
                link.update(request, time_slot)
            
            # Actualizar estadísticas de la conexión
            self.total_data_transmitted += data_size_mb
            self.transmission_count += 1
            
            # Simular errores de transmisión (simplificado)
            # En una implementación real, consideraríamos:
            # - Distancia del enlace
            # - Calidad del medio óptico
            # - Interferencia
            success = self._simulate_transmission_success(data_size_mb, bit_error_rate)
            
            if success:
                return True
            else:
                print(f"❌ Transmission failed for request {request.id} due to bit errors")
                return False
                
        except Exception as e:
            print(f"❌ Connection flush error: {e}")
            return False

    def _simulate_transmission_success(self, data_size_mb: float, bit_error_rate: float) -> bool:
        """
        Simular éxito de transmisión considerando tasa de error
        
        Args:
            data_size_mb: Tamaño de datos en MB
            bit_error_rate: Tasa de error de bits
            
        Returns:
            True si la transmisión es exitosa
        """
        # Por simplicidad, asumimos que las transmisiones siempre son exitosas
        # En una implementación real, consideraríamos:
        # total_bits = data_size_mb * 8 * 1_048_576  # MB to bits
        # error_probability = 1 - (1 - bit_error_rate) ** total_bits
        # success = random.random() > error_probability
        return True
    
    def get_connection_stats(self) -> dict:
        """Obtener estadísticas de la conexión"""
        avg_data_per_transmission = (
            self.total_data_transmitted / self.transmission_count
            if self.transmission_count > 0 else 0
        )
        
        return {
            'created_at': self.created_at,
            'speed_mbps': self.speed,
            'protocol': self.protocol,
            'total_transmitted_mb': self.total_data_transmitted,
            'transmission_count': self.transmission_count,
            'avg_data_per_transmission': avg_data_per_transmission,
            'path_length': len(self.path),
            'success_rate': self.success_rate
        }
    
    def __str__(self) -> str:
        return f"Connection(speed={self.speed}Mbps, path_len={len(self.path)}, transmitted={self.total_data_transmitted:.3f}MB)"
    
    def __repr__(self) -> str:
        return self.__str__()