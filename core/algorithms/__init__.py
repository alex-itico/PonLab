"""
Algorithms Module
DBA and scheduling algorithms for PON
"""

from .pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm, PriorityDBAAlgorithm, RLDBAAlgorithm
from .upstream_scheduler import UpstreamScheduler

# Deferred imports to avoid cycles
def get_dba_cycle_classes():
    """Import DBA Cycle classes in a deferred manner"""
    from .pon_dba_cycle import DBACycleManager, DBAResult, DBAAllocation
    return {'DBACycleManager': DBACycleManager, 'DBAResult': DBAResult, 'DBAAllocation': DBAAllocation}

__all__ = [
    'DBAAlgorithmInterface', 
    'FCFSDBAAlgorithm', 
    'PriorityDBAAlgorithm', 
    'RLDBAAlgorithm',
    'UpstreamScheduler',
    'get_dba_cycle_classes'
]
