"""
Core Module
Contains the main business logic and models organized by functionality
"""

# Direct imports of main files to avoid dependency issues
try:
    # Devices - direct imports
    from .devices.device import Device
    from .devices.device_manager import DeviceManager
    
    # Connections - direct imports
    from .connections.connection_manager import ConnectionManager
    
    # Simulation - direct imports  
    from .simulation.simulation_manager import SimulationManager
    
    # PON - direct imports
    from .pon.pon_adapter import PONAdapter
    
    # Deferred import function for device_types
    def get_device_types():
        """Import device types in a deferred manner"""
        from .devices.device_types import OLT, OLT_SDN, ONU, create_device
        return OLT, OLT_SDN, ONU, create_device
    
    # Deferred import function for DBA algorithms
    def get_dba_algorithms():
        """Import DBA algorithms in a deferred manner"""
        from .algorithms.pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm, PriorityDBAAlgorithm, RLDBAAlgorithm
        return {
            'DBAAlgorithmInterface': DBAAlgorithmInterface,
            'FCFSDBAAlgorithm': FCFSDBAAlgorithm,
            'PriorityDBAAlgorithm': PriorityDBAAlgorithm,
            'RLDBAAlgorithm': RLDBAAlgorithm
        }
    
    print("OK Core module loaded successfully")

except ImportError as e:
    print(f"ERROR in core imports: {e}")
    raise

# Helper function for deferred imports
def get_device_classes():
    """Obtains device classes in a deferred manner"""
    from .devices.device_types import OLT, OLT_SDN, ONU, create_device
    return {'OLT': OLT, 'OLT_SDN': OLT_SDN, 'ONU': ONU, 'create_device': create_device}

# Exports principales
__all__ = [
    'Device', 'DeviceManager', 'get_device_types', 'get_device_classes', 'get_dba_algorithms',
    'ConnectionManager', 'SimulationManager', 'PONAdapter'
]
