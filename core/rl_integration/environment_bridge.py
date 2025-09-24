"""
Environment Bridge
Puente entre el sistema de simulación de PonLab y el entorno RL de netPONpy
"""

from typing import Dict, List, Any, Optional
import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal


class EnvironmentBridge(QObject):
    """
    Puente que conecta la topología de PonLab con el entorno RL de netPONpy
    """
    
    # Señales
    topology_updated = pyqtSignal(dict)  # Topología actualizada
    metrics_updated = pyqtSignal(dict)   # Métricas actualizadas
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = None
        self.rl_env = None
        self.device_mapping = {}  # Mapeo dispositivos PonLab -> netPONpy
        
    def set_canvas_reference(self, canvas):
        """Establecer referencia al canvas de PonLab"""
        self.canvas = canvas
        print("Canvas reference set for EnvironmentBridge")
        
    def set_rl_environment(self, rl_env):
        """Establecer referencia al entorno RL"""
        self.rl_env = rl_env
        print("RL Environment reference set for EnvironmentBridge")
        
    def extract_topology_from_canvas(self) -> Dict[str, Any]:
        """
        Extraer topología de PonLab para uso en entorno RL
        
        Returns:
            Diccionario con información de topología
        """
        if not self.canvas:
            return {}
        
        try:
            topology = {
                'devices': [],
                'connections': [],
                'olt_count': 0,
                'onu_count': 0
            }
            
            # Extraer dispositivos del canvas
            if hasattr(self.canvas, 'devices'):
                for device_id, device in self.canvas.devices.items():
                    device_info = {
                        'id': device_id,
                        'type': device.get('type', 'unknown'),
                        'position': device.get('pos', (0, 0)),
                        'properties': device.get('properties', {})
                    }
                    
                    topology['devices'].append(device_info)
                    
                    # Contar tipos de dispositivos
                    if device_info['type'].lower() == 'olt':
                        topology['olt_count'] += 1
                    elif device_info['type'].lower() == 'onu':
                        topology['onu_count'] += 1
            
            # Extraer conexiones del canvas
            if hasattr(self.canvas, 'connections'):
                for conn_id, connection in self.canvas.connections.items():
                    conn_info = {
                        'id': conn_id,
                        'source': connection.get('source'),
                        'target': connection.get('target'),
                        'distance': connection.get('distance', 0),
                        'properties': connection.get('properties', {})
                    }
                    topology['connections'].append(conn_info)
            
            print(f"Topologia extraida: {topology['olt_count']} OLT, {topology['onu_count']} ONU")
            
            self.topology_updated.emit(topology)
            return topology
            
        except Exception as e:
            print(f"ERROR extrayendo topologia: {e}")
            return {}
    
    def validate_topology_for_rl(self, topology: Dict[str, Any]) -> bool:
        """
        Validar que la topología es compatible con RL
        
        Args:
            topology: Topología extraída del canvas
            
        Returns:
            True si es válida para RL
        """
        try:
            # Verificar que hay al menos 1 OLT
            if topology.get('olt_count', 0) < 1:
                print("WARNING: Se requiere al menos 1 OLT para RL")
                return False
            
            # Verificar que hay al menos 2 ONUs
            if topology.get('onu_count', 0) < 2:
                print("WARNING: Se requieren al menos 2 ONUs para RL")
                return False
            
            # Verificar que hay conexiones
            if len(topology.get('connections', [])) < 1:
                print("WARNING: Se requieren conexiones entre dispositivos")
                return False
            
            print("Topologia valida para RL")
            return True
            
        except Exception as e:
            print(f"ERROR validando topologia: {e}")
            return False
    
    def map_ponlab_to_netponpy(self, topology: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mapear topología de PonLab a formato compatible con netPONpy
        
        Args:
            topology: Topología de PonLab
            
        Returns:
            Configuración compatible con netPONpy
        """
        try:
            # Configuración básica para netPONpy
            netponpy_config = {
                'num_onus': topology.get('onu_count', 4),
                'olt_config': {},
                'onu_configs': [],
                'network_layout': {
                    'devices': topology.get('devices', []),
                    'connections': topology.get('connections', [])
                }
            }
            
            # Mapear dispositivos ONU
            onu_index = 0
            for device in topology.get('devices', []):
                if device['type'].lower() == 'onu':
                    onu_config = {
                        'id': onu_index,
                        'ponlab_id': device['id'],
                        'position': device['position'],
                        'properties': device.get('properties', {})
                    }
                    netponpy_config['onu_configs'].append(onu_config)
                    
                    # Mantener mapeo para referencia
                    self.device_mapping[device['id']] = onu_index
                    onu_index += 1
            
            print(f"Mapeo PonLab->netPONpy completado: {len(self.device_mapping)} dispositivos")
            return netponpy_config
            
        except Exception as e:
            print(f"ERROR mapeando topologia: {e}")
            return {}
    
    def sync_topology_with_rl(self) -> bool:
        """
        Sincronizar topología de PonLab con entorno RL
        
        Returns:
            True si la sincronización fue exitosa
        """
        try:
            # Extraer topología actual
            topology = self.extract_topology_from_canvas()
            
            if not topology:
                print("WARNING: No se pudo extraer topologia del canvas")
                return False
            
            # Validar topología
            if not self.validate_topology_for_rl(topology):
                print("WARNING: Topologia no valida para RL")
                return False
            
            # Mapear a formato netPONpy
            netponpy_config = self.map_ponlab_to_netponpy(topology)
            
            if not netponpy_config:
                print("WARNING: Error mapeando topologia")
                return False
            
            # Si hay entorno RL activo, actualizar configuración
            if self.rl_env:
                # Aquí se podría actualizar la configuración del entorno
                # Por ahora, solo reportamos la sincronización
                print("Topologia sincronizada con entorno RL")
                
            return True
            
        except Exception as e:
            print(f"ERROR sincronizando topologia: {e}")
            return False
    
    def get_canvas_metrics(self) -> Dict[str, Any]:
        """
        Obtener métricas actuales del canvas de PonLab
        
        Returns:
            Diccionario con métricas
        """
        if not self.canvas:
            return {}
        
        try:
            metrics = {
                'device_count': len(getattr(self.canvas, 'devices', {})),
                'connection_count': len(getattr(self.canvas, 'connections', {})),
                'canvas_size': {
                    'width': self.canvas.width(),
                    'height': self.canvas.height()
                },
                'zoom_level': getattr(self.canvas, 'scale_factor', 1.0),
                'timestamp': self._get_current_timestamp()
            }
            
            self.metrics_updated.emit(metrics)
            return metrics
            
        except Exception as e:
            print(f"ERROR obteniendo metricas del canvas: {e}")
            return {}
    
    def _get_current_timestamp(self) -> str:
        """Obtener timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_device_mapping(self) -> Dict[str, int]:
        """Obtener mapeo de dispositivos PonLab -> netPONpy"""
        return self.device_mapping.copy()
    
    def clear_mapping(self):
        """Limpiar mapeo de dispositivos"""
        self.device_mapping.clear()
        print("🧹 Mapeo de dispositivos limpiado")