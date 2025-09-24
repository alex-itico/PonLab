"""
Topology Bridge
Puente entre la topología del canvas de PonLab y netPONpy RL
"""

import sys
import os
import json
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal
import hashlib

# Importar netPONpy si está disponible
try:
    netponpy_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'netPONPy')
    if os.path.exists(netponpy_path) and netponpy_path not in sys.path:
        sys.path.append(netponpy_path)

    from netPonPy.pon.pon_rl_env_v2 import create_pon_rl_env_v2
    NETPONPY_AVAILABLE = True
except ImportError:
    NETPONPY_AVAILABLE = False


class TopologyBridge(QObject):
    """
    Puente que extrae la topología del canvas de PonLab y la configura en netPONpy
    """

    # Señales
    topology_extracted = pyqtSignal(dict)
    topology_validated = pyqtSignal(bool, str)  # válida, mensaje

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_topology = None
        self.topology_hash = None

    def extract_topology_from_canvas(self, canvas_widget) -> Dict[str, Any]:
        """
        Extraer topología desde el canvas de PonLab

        Args:
            canvas_widget: Widget del canvas de PonLab

        Returns:
            Diccionario con la configuración de topología
        """
        try:
            topology = {
                'num_onus': 0,
                'onus_config': {},
                'olt_config': {},
                'links_data': {},
                'canvas_nodes': [],
                'canvas_connections': []
            }

            # Buscar nodes del canvas
            if hasattr(canvas_widget, 'scene'):
                scene = canvas_widget.scene()
                nodes = []
                connections = []

                for item in scene.items():
                    # Buscar nodos ONU y OLT
                    if hasattr(item, 'node_type'):
                        node_data = {
                            'id': getattr(item, 'node_id', f'node_{len(nodes)}'),
                            'type': item.node_type,
                            'position': (item.pos().x(), item.pos().y()),
                            'properties': getattr(item, 'properties', {})
                        }
                        nodes.append(node_data)

                        # Configurar ONUs
                        if item.node_type == 'ONU':
                            onu_id = str(topology['num_onus'])
                            topology['onus_config'][onu_id] = {
                                'id': onu_id,
                                'name': node_data['id'],
                                'sla': node_data['properties'].get('sla', 100.0),
                                'buffer_size': node_data['properties'].get('buffer_size', 500),
                                'transmission_rate': node_data['properties'].get('transmission_rate', 100.0)
                            }
                            topology['num_onus'] += 1

                        # Configurar OLT
                        elif item.node_type == 'OLT':
                            topology['olt_config'] = {
                                'id': node_data['id'],
                                'transmission_rate': node_data['properties'].get('transmission_rate', 1024.0)
                            }

                    # Buscar conexiones
                    elif hasattr(item, 'connection_type'):
                        connection_data = {
                            'from_node': getattr(item, 'from_node', ''),
                            'to_node': getattr(item, 'to_node', ''),
                            'type': item.connection_type,
                            'properties': getattr(item, 'properties', {})
                        }
                        connections.append(connection_data)

                topology['canvas_nodes'] = nodes
                topology['canvas_connections'] = connections

                # Configurar enlaces basado en conexiones
                for i, conn in enumerate(connections):
                    link_id = str(i)
                    topology['links_data'][link_id] = {
                        'length': conn['properties'].get('length', 1.0),
                        'from': conn['from_node'],
                        'to': conn['to_node']
                    }

            # Si no hay ONUs en canvas, usar configuración por defecto
            if topology['num_onus'] == 0:
                print("[INFO] No se encontraron ONUs en canvas, usando configuración por defecto")
                topology['num_onus'] = 4
                for i in range(4):
                    onu_id = str(i)
                    topology['onus_config'][onu_id] = {
                        'id': onu_id,
                        'name': f'ONU_{i}',
                        'sla': 100.0 + i * 50.0,
                        'buffer_size': 500,
                        'transmission_rate': 100.0
                    }
                    topology['links_data'][onu_id] = {'length': 1.0 + i * 0.5}

                topology['olt_config'] = {
                    'id': 'OLT_default',
                    'transmission_rate': 1024.0
                }

            # Calcular hash de la topología para validación
            topology_str = json.dumps(topology, sort_keys=True)
            self.topology_hash = hashlib.md5(topology_str.encode()).hexdigest()
            topology['topology_hash'] = self.topology_hash

            self.current_topology = topology
            self.topology_extracted.emit(topology)

            print(f"[OK] Topología extraída: {topology['num_onus']} ONUs, hash: {self.topology_hash[:8]}")
            return topology

        except Exception as e:
            print(f"[ERROR] Error extrayendo topología del canvas: {e}")
            return self._get_default_topology()

    def _get_default_topology(self) -> Dict[str, Any]:
        """Obtener topología por defecto si falla la extracción"""
        topology = {
            'num_onus': 4,
            'onus_config': {},
            'olt_config': {
                'id': 'OLT_default',
                'transmission_rate': 1024.0
            },
            'links_data': {},
            'canvas_nodes': [],
            'canvas_connections': []
        }

        for i in range(4):
            onu_id = str(i)
            topology['onus_config'][onu_id] = {
                'id': onu_id,
                'name': f'ONU_{i}',
                'sla': 100.0 + i * 50.0,
                'buffer_size': 500,
                'transmission_rate': 100.0
            }
            topology['links_data'][onu_id] = {'length': 1.0 + i * 0.5}

        topology_str = json.dumps(topology, sort_keys=True)
        self.topology_hash = hashlib.md5(topology_str.encode()).hexdigest()
        topology['topology_hash'] = self.topology_hash

        self.current_topology = topology
        return topology

    def validate_topology_compatibility(self, model_metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validar que el modelo sea compatible con la topología actual

        Args:
            model_metadata: Metadata del modelo entrenado

        Returns:
            Tuple (es_compatible, mensaje_explicativo)
        """
        # Si no hay topología actual, intentar usar por defecto
        if not self.current_topology:
            print("[WARNING] No hay topología cargada, usando configuración por defecto para validación")
            self.current_topology = self._get_default_topology()

        if not self.current_topology:
            return False, "No se pudo cargar ninguna topología para validación"

        try:
            # Verificar hash de topología si existe
            model_topology_hash = model_metadata.get('topology_hash')
            if model_topology_hash and self.topology_hash:
                if model_topology_hash == self.topology_hash:
                    message = "[OK] Topologia exactamente igual - Compatible 100%"
                    self.topology_validated.emit(True, message)
                    return True, message

            # Verificar parámetros críticos
            model_num_onus = model_metadata.get('num_onus', 0)
            current_num_onus = self.current_topology['num_onus']

            # Si el modelo no tiene metadata de num_onus, asumir compatibilidad
            if model_num_onus == 0:
                message = f"[WARNING] Compatible (sin metadata): Asumiendo compatibilidad con {current_num_onus} ONUs"
                self.topology_validated.emit(True, message)
                return True, message

            if model_num_onus != current_num_onus:
                message = f"[ERROR] Incompatible: Modelo entrenado con {model_num_onus} ONUs, topologia actual tiene {current_num_onus}"
                self.topology_validated.emit(False, message)
                return False, message

            # Verificar estructura de observación y acción
            model_obs_space = model_metadata.get('observation_space_size')
            model_action_space = model_metadata.get('action_space_size')

            expected_obs_space = current_num_onus * 3 + 1  # buffer + delay + throughput + fairness
            expected_action_space = current_num_onus

            if model_obs_space and model_obs_space != expected_obs_space:
                message = f"⚠️ Posible incompatibilidad: Espacio de observación diferente ({model_obs_space} vs {expected_obs_space})"
                self.topology_validated.emit(False, message)
                return False, message

            if model_action_space and model_action_space != expected_action_space:
                message = f"❌ Incompatible: Espacio de acción diferente ({model_action_space} vs {expected_action_space})"
                self.topology_validated.emit(False, message)
                return False, message

            # Si llegamos aqui, parece compatible
            message = f"[OK] Compatible: {current_num_onus} ONUs, espacios de obs/accion correctos"
            self.topology_validated.emit(True, message)
            return True, message

        except Exception as e:
            message = f"❌ Error validando compatibilidad: {e}"
            self.topology_validated.emit(False, message)
            return False, message

    def create_rl_environment(self, traffic_scenario: str = "residential_medium",
                            episode_duration: float = 1.0,
                            simulation_timestep: float = 0.0005):
        """
        Crear entorno RL usando la topología actual

        Args:
            traffic_scenario: Escenario de tráfico
            episode_duration: Duración del episodio
            simulation_timestep: Timestep de simulación

        Returns:
            Entorno RL configurado con la topología actual
        """
        if not NETPONPY_AVAILABLE:
            raise RuntimeError("netPONpy no está disponible")

        if not self.current_topology:
            raise RuntimeError("No hay topología cargada")

        try:
            # Crear entorno base
            env = create_pon_rl_env_v2(
                num_onus=self.current_topology['num_onus'],
                traffic_scenario=traffic_scenario,
                episode_duration=episode_duration,
                simulation_timestep=simulation_timestep
            )

            # Configurar custom para que use nuestra topología
            self._configure_environment_topology(env)

            print(f"[OK] Entorno RL creado con topología del canvas ({self.current_topology['num_onus']} ONUs)")
            return env

        except Exception as e:
            print(f"[ERROR] Error creando entorno RL con topología: {e}")
            raise

    def _configure_environment_topology(self, env):
        """Configurar entorno RL con los parámetros específicos de la topología"""
        try:
            # Obtener el simulador del entorno
            simulator = env.getSimulator()

            # Configurar ONUs específicas según la topología
            onus_config = self.current_topology.get('onus_config', {})

            for onu_id, config in onus_config.items():
                if onu_id in simulator.olt.onus:
                    onu = simulator.olt.onus[onu_id]

                    # Aplicar configuración específica
                    if 'sla' in config:
                        onu.service_level_agreement = config['sla']
                    if 'buffer_size' in config:
                        onu.buffer.size = config['buffer_size']
                    if 'transmission_rate' in config:
                        onu.transmition_rate = config['transmission_rate']

            # Configurar OLT
            olt_config = self.current_topology.get('olt_config', {})
            if 'transmission_rate' in olt_config:
                simulator.olt.transmition_rate = olt_config['transmission_rate']

            # Configurar links
            links_data = self.current_topology.get('links_data', {})
            if hasattr(simulator.olt, 'links_data'):
                simulator.olt.links_data.update(links_data)

        except Exception as e:
            print(f"[WARNING] Error configurando topología específica: {e}")

    def get_topology_metadata(self) -> Dict[str, Any]:
        """
        Obtener metadata de la topología actual para guardar con el modelo

        Returns:
            Diccionario con metadata de la topología
        """
        if not self.current_topology:
            return {}

        return {
            'topology_hash': self.topology_hash,
            'num_onus': self.current_topology['num_onus'],
            'observation_space_size': self.current_topology['num_onus'] * 3 + 1,
            'action_space_size': self.current_topology['num_onus'],
            'olt_config': self.current_topology.get('olt_config', {}),
            'total_links': len(self.current_topology.get('links_data', {})),
            'extraction_timestamp': self._get_current_timestamp()
        }

    def _get_current_timestamp(self) -> str:
        """Obtener timestamp actual"""
        import datetime
        return datetime.datetime.now().isoformat()

    def save_topology_config(self, filepath: str):
        """Guardar configuración de topología en archivo"""
        if not self.current_topology:
            return False

        try:
            with open(filepath, 'w') as f:
                json.dump(self.current_topology, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Error guardando configuración de topología: {e}")
            return False

    def load_topology_config(self, filepath: str):
        """Cargar configuración de topología desde archivo"""
        try:
            with open(filepath, 'r') as f:
                topology = json.load(f)

            self.current_topology = topology
            self.topology_hash = topology.get('topology_hash')
            self.topology_extracted.emit(topology)

            return True
        except Exception as e:
            print(f"[ERROR] Error cargando configuración de topología: {e}")
            return False