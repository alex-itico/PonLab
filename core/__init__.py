"""
Módulo Core
Contiene la lógica de negocio principal y modelos organizados por funcionalidad
"""

# Imports directos de los archivos principales para evitar problemas de dependencias
try:
    # Dispositivos - imports directos
    from .devices.device import Device
    from .devices.device_manager import DeviceManager
    from .devices.device_types import OLT, OLT_SDN, ONU, create_device
    
    # Conexiones - imports directos
    from .connections.connection_manager import ConnectionManager
    
    # Simulación - imports directos  
    from .simulation.simulation_manager import SimulationManager
    
    # PON - imports directos
    from .pon.pon_adapter import PONAdapter
    
    print("✅ Core module loaded successfully")
    
except ImportError as e:
    print(f"❌ Error en core imports: {e}")
    raise

# Exports principales
__all__ = [
    'Device', 'DeviceManager', 'OLT', 'OLT_SDN', 'ONU', 'create_device',
    'ConnectionManager', 'SimulationManager', 'PONAdapter'
]
