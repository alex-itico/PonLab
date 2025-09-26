"""
Algorithms Module
Algoritmos DBA y scheduling para PON
"""

from .pon_dba import DBAAlgorithmInterface, FCFSDBAAlgorithm, PriorityDBAAlgorithm, RLDBAAlgorithm
from .upstream_scheduler import UpstreamScheduler

# Importaciones diferidas para evitar ciclos
def get_dba_cycle_classes():
    """Importar clases de DBA Cycle de forma diferida"""
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
