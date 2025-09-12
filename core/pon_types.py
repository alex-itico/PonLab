"""
PON Types
Tipos básicos para el simulador PON integrado con netPONPy
"""

from typing import Literal, Dict, Optional, List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pon_link import Link

# Traffic types as defined in netPONPy
TrafficTypes = Literal[
    "lowest",
    "low", 
    "medium",
    "high",
    "highest",
]

# Type aliases
Traffic_Probability = Dict[TrafficTypes, Optional[float]]
Demands = Dict[TrafficTypes, Optional[float]]
Path = List['Link']