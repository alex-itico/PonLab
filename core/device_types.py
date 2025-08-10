"""
Device Types (Tipos de Dispositivos)
Implementaciones específicas para dispositivos OLT y ONU
"""

from .device import Device

class OLT(Device):
    """Optical Line Terminal - Equipo central de la red PON"""
    
    def __init__(self, name=None, x=0, y=0):
        super().__init__("OLT", name, x, y)
        
        # Propiedades básicas del OLT
        self.properties = {
            'model': 'OLT-Generic',  # Modelo del equipo
            'status': 'online',      # Estado operacional
            'location': '',          # Ubicación física
            'notes': ''              # Notas adicionales
        }


class ONU(Device):
    """Optical Network Unit - Equipo terminal de la red PON"""
    
    def __init__(self, name=None, x=0, y=0):
        super().__init__("ONU", name, x, y)
        
        # Propiedades básicas de la ONU
        self.properties = {
            'model': 'ONU-Generic',  # Modelo del equipo
            'status': 'online',      # Estado operacional
            'location': '',          # Ubicación física
            'notes': ''              # Notas adicionales
        }


# Factory function para crear dispositivos
def create_device(device_type, name=None, x=0, y=0):
    """Factory para crear dispositivos según tipo"""
    if device_type.upper() == "OLT":
        return OLT(name, x, y)
    elif device_type.upper() == "ONU":
        return ONU(name, x, y)
    else:
        raise ValueError(f"Tipo de dispositivo no soportado: {device_type}")
