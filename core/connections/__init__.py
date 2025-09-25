"""
Connections Module
Sistema de conexiones y enlaces entre dispositivos
"""

from .connection import Connection
from .connection_manager import ConnectionManager
from .connection_points import ConnectionPoint
from .pon_connection import Connection as PONConnection
from .pon_link import Link

__all__ = ['Connection', 'ConnectionManager', 'ConnectionPoint', 'PONConnection', 'Link']
