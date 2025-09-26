"""
Módulo Core
Contiene la lógica de negocio principal y modelos organizados por funcionalidad
"""

# Imports directos de los archivos principales para evitar problemas de dependencias
try:
    # Dispositivos - imports directos
    from .devices.device import Device
    from .devices.device_manager import DeviceManager
    
    # Conexiones - imports directos
    from .connections.connection_manager import ConnectionManager
    
    # Simulación - imports directos  
    from .simulation.simulation_manager import SimulationManager
    
    # PON - imports directos
    from .pon.pon_adapter import PONAdapter
    
    # Función de importación diferida para device_types
    def get_device_types():
        """Importar tipos de dispositivos de forma diferida"""
        from .devices.device_types import OLT, OLT_SDN, ONU, create_device
        return OLT, OLT_SDN, ONU, create_device
    
    # Función de importación diferida para algoritmos DBA
    def get_dba_algorithms():
        """Importar algoritmos DBA de forma diferida"""
        from .algorithms.pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm, PriorityDBAAlgorithm, RLDBAAlgorithm
        return {
            'DBAAlgorithmInterface': DBAAlgorithmInterface,
            'FCFSDBAAlgorithm': FCFSDBAAlgorithm,
            'PriorityDBAAlgorithm': PriorityDBAAlgorithm,
            'RLDBAAlgorithm': RLDBAAlgorithm
        }
    
    print("✅ Core module loaded successfully")
    
except ImportError as e:
    print(f"❌ Error en core imports: {e}")
    raise

# Función helper para imports diferidos
def get_device_classes():
    """Obtiene las clases de dispositivos de forma diferida"""
    from .devices.device_types import OLT, OLT_SDN, ONU, create_device
    return {'OLT': OLT, 'OLT_SDN': OLT_SDN, 'ONU': ONU, 'create_device': create_device}

# Exports principales
__all__ = [
    'Device', 'DeviceManager', 'get_device_types', 'get_device_classes', 'get_dba_algorithms',
    'ConnectionManager', 'SimulationManager', 'PONAdapter'
]
