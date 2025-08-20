"""
Device Types (Tipos de Dispositivos)
Implementaciones específicas para dispositivos OLT y ONU
"""

from .device import Device
from .upstream_scheduler import UpstreamScheduler
import numpy as np

class OLT(Device):
    """Optical Line Terminal - Equipo central de la red PON"""
    
    def __init__(self, name=None, x=0, y=0):
        super().__init__("OLT", name, x, y)
        
        # Propiedades básicas del OLT
        self.properties = {
            'model': 'OLT-Generic',
            'status': 'online',
            'location': '',
            'notes': '',
            'total_bandwidth': 10000,  # 10 Gbps
            'allocated_bandwidth': 0
        }
        
        # Crear scheduler después de definir las propiedades
        try:
            self.scheduler = UpstreamScheduler(self.properties['total_bandwidth'])
        except Exception as e:
            print(f"Error al crear scheduler: {e}")
            self.scheduler = None


class ONU(Device):
    """Optical Network Unit - Equipo terminal de la red PON"""
    
    def __init__(self, name=None, x=0, y=0):
        super().__init__("ONU", name, x, y)
        
        # Propiedades básicas de la ONU
        self.properties = {
            'model': 'ONU-Generic',  # Modelo del equipo
            'status': 'online',      # Estado operacional
            'location': '',          # Ubicación física
            'notes': '',              # Notas adicionales
            'upstream_bandwidth': 1000,  # 1 Gbps default request
            'allocated_bandwidth': 0,
            'traffic_profile': 'constant',
            'mean_rate': 500,  # Mbps
            'burst_size': 100   # Mbps
        }
        
    def generate_bandwidth_request(self):
        """Generate realistic bandwidth request based on traffic profile"""
        if self.properties['traffic_profile'] == 'constant':
            return self.properties['mean_rate']
            
        elif self.properties['traffic_profile'] == 'random':
            # Normal distribution around mean
            request = np.random.normal(
                self.properties['mean_rate'],
                self.properties['mean_rate'] * 0.2
            )
            return max(0, min(request, self.properties['upstream_bandwidth']))
            
        elif self.properties['traffic_profile'] == 'bursty':
            # Simple burst model
            if np.random.random() < 0.3:  # 30% burst probability
                return self.properties['mean_rate'] + self.properties['burst_size']
            return self.properties['mean_rate']


# Factory function para crear dispositivos
def create_device(device_type, name=None, x=0, y=0):
    """Factory para crear dispositivos según tipo"""
    if device_type.upper() == "OLT":
        return OLT(name, x, y)
    elif device_type.upper() == "ONU":
        return ONU(name, x, y)
    else:
        raise ValueError(f"Tipo de dispositivo no soportado: {device_type}")
