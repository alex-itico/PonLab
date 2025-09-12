"""
Módulo Core
Contiene la lógica de negocio principal y modelos
"""

# Clases originales de PonLab
from .device import Device
from .device_types import OLT, ONU, create_device
from .device_manager import DeviceManager, DeviceGraphicsItem

# Clases integradas de netPONPy
from .pon_types import TrafficTypes, Traffic_Probability, Demands, Path
from .pon_request import Request
from .pon_link import Link
from .pon_connection import Connection
from .pon_event import Event
from .pon_random import ExpVariable, UniformVariable
from .pon_queue import Queue
from .pon_buffer import Buffer
from .pon_onu import ONU as PON_ONU
from .pon_olt import OLT as PON_OLT
from .pon_dba_interface import DBAAlgorithmInterface, FCFSDBAAlgorithm, PriorityDBAAlgorithm, RLDBAAlgorithm
from .pon_netsim import NetSim, EventEvaluator
from .pon_orchestrator import PONOrchestrator, SimulatorStatus, SimulationResult
from .traffic_scenarios import get_traffic_scenario, calculate_realistic_lambda, get_available_scenarios, print_scenario_info
from .integrated_netponpy_adapter import IntegratedPONAdapter

__all__ = [
    # PonLab original
    'Device',
    'OLT', 
    'ONU',
    'create_device',
    'DeviceManager',
    'DeviceGraphicsItem',
    
    # PON Core integrado
    'TrafficTypes',
    'Traffic_Probability', 
    'Demands',
    'Path',
    'Request',
    'Link',
    'Connection',
    'Event',
    'ExpVariable',
    'UniformVariable',
    'Queue',
    'Buffer',
    'PON_ONU',
    'PON_OLT',
    'DBAAlgorithmInterface',
    'FCFSDBAAlgorithm',
    'PriorityDBAAlgorithm', 
    'RLDBAAlgorithm',
    'NetSim',
    'EventEvaluator',
    'PONOrchestrator',
    'SimulatorStatus',
    'SimulationResult',
    'get_traffic_scenario',
    'calculate_realistic_lambda',
    'get_available_scenarios',
    'print_scenario_info',
    'IntegratedPONAdapter'
]
