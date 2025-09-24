"""
Model Bridge
Bridge para usar modelos RL entrenados en simulaciones tradicionales
"""

import os
import sys
from typing import Dict, Any, Optional, List
from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np

# Intentar importar netPONpy y dependencias RL
try:
    # Agregar ruta de netPONpy al sys.path si no está
    netponpy_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'netPONPy')
    if os.path.exists(netponpy_path) and netponpy_path not in sys.path:
        sys.path.append(netponpy_path)
    
    from netPonPy.pon.pon_rl_env_v2 import create_pon_rl_env_v2
    from netPonPy.pon.interfaces.dba_algorithm_interface import DBAAlgorithmInterface
    from stable_baselines3 import PPO, A2C, DQN, SAC
    
    NETPONPY_AVAILABLE = True
    print("[OK] netPONpy RL modules loaded for model bridge")
    
except ImportError as e:
    NETPONPY_AVAILABLE = False
    print(f"[WARNING] netPONpy RL modules not available for model bridge: {e}")


class RLModelDBABridge(DBAAlgorithmInterface):
    """Bridge que implementa DBAAlgorithmInterface usando un modelo RL pre-entrenado"""
    
    def __init__(self, model_path: str, env_params: Dict[str, Any]):
        """
        Inicializar bridge con modelo RL
        
        Args:
            model_path: Ruta al modelo entrenado
            env_params: Parámetros del entorno RL
        """
        super().__init__()
        self.model_path = model_path
        self.env_params = env_params
        self.model = None
        self.temp_env = None
        self.last_observation = None
        self.decision_count = 0
        
        # Cargar modelo
        self._load_model()
    
    def _load_model(self):
        """Cargar modelo RL desde archivo"""
        if not NETPONPY_AVAILABLE:
            print("[ERROR] netPONpy no disponible - no se puede cargar modelo RL")
            return False
        
        try:
            # Detectar tipo de modelo por el nombre del archivo
            # Por simplicidad, usar PPO por defecto
            self.model = PPO.load(self.model_path)
            
            # Crear entorno temporal para obtener espacios de observación/acción
            self.temp_env = create_pon_rl_env_v2(
                num_onus=self.env_params.get('num_onus', 4),
                traffic_scenario=self.env_params.get('traffic_scenario', 'residential_medium'),
                episode_duration=1.0,  # Duración corta para el entorno temporal
                simulation_timestep=0.0005
            )
            
            print(f"[OK] Modelo RL cargado desde: {self.model_path}")
            print(f"    Observation space: {self.temp_env.observation_space}")
            print(f"    Action space: {self.temp_env.action_space}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error cargando modelo RL: {str(e)}")
            return False
    
    def get_name(self) -> str:
        """Obtener nombre del algoritmo"""
        return f"RL Agent ({os.path.basename(self.model_path)})"
    
    def get_algorithm_name(self) -> str:
        """Obtener nombre del algoritmo (requerido por DBAAlgorithmInterface)"""
        return f"RL_Agent_{os.path.splitext(os.path.basename(self.model_path))[0]}"
    
    def allocate_bandwidth(self, onu_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Asignar ancho de banda usando el modelo RL
        
        Args:
            onu_requests: Lista de solicitudes de ONUs
            
        Returns:
            Lista de asignaciones de ancho de banda
        """
        if not self.model or not self.temp_env:
            # Fallback a algoritmo simple si no hay modelo
            return self._fallback_allocation(onu_requests)
        
        try:
            # Convertir solicitudes a observación RL
            observation = self._convert_requests_to_observation(onu_requests)
            
            # Obtener acción del modelo RL
            action, _states = self.model.predict(observation, deterministic=True)
            
            # Convertir acción a asignaciones de ancho de banda
            allocations = self._convert_action_to_allocations(action, onu_requests)
            
            self.decision_count += 1
            
            # Log cada 100 decisiones
            if self.decision_count % 100 == 0:
                print(f"[RL] {self.decision_count} decisiones del agente RL procesadas")
            
            return allocations
            
        except Exception as e:
            print(f"[ERROR] Error en asignación RL: {str(e)}")
            return self._fallback_allocation(onu_requests)
    
    def _convert_requests_to_observation(self, onu_requests: List[Dict[str, Any]]) -> np.ndarray:
        """
        Convertir solicitudes de ONUs a observación RL
        
        Args:
            onu_requests: Lista de solicitudes
            
        Returns:
            Observación en formato numpy
        """
        # Simplificado: crear observación básica
        # En implementación real, esto debería coincidir con el espacio de observación del entrenamiento
        
        num_onus = len(onu_requests)
        
        # Crear observación básica con solicitudes normalizadas
        observation = np.zeros(num_onus * 3)  # Por ejemplo: [requested_bw, queue_size, priority] por ONU
        
        for i, request in enumerate(onu_requests):
            base_idx = i * 3
            
            # Normalizar valores (valores de ejemplo)
            requested_bw = min(request.get('requested_bandwidth', 0) / 1000.0, 1.0)  # Normalizar a [0,1]
            queue_size = min(request.get('queue_size', 0) / 100.0, 1.0)  # Normalizar a [0,1]
            priority = request.get('priority', 1) / 10.0  # Normalizar a [0,1]
            
            observation[base_idx] = requested_bw
            observation[base_idx + 1] = queue_size
            observation[base_idx + 2] = priority
        
        return observation
    
    def _convert_action_to_allocations(self, action: np.ndarray, 
                                     onu_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convertir acción RL a asignaciones de ancho de banda
        
        Args:
            action: Acción del modelo RL
            onu_requests: Solicitudes originales
            
        Returns:
            Lista de asignaciones
        """
        allocations = []
        
        # Simplificado: interpretar acción como porcentajes de asignación
        for i, request in enumerate(onu_requests):
            onu_id = request.get('onu_id', i)
            requested_bw = request.get('requested_bandwidth', 0)
            
            # Obtener porcentaje de asignación de la acción
            if len(action) > i:
                allocation_ratio = max(0.0, min(1.0, float(action[i])))
            else:
                allocation_ratio = 0.5  # Default al 50%
            
            allocated_bw = int(requested_bw * allocation_ratio)
            
            allocation = {
                'onu_id': onu_id,
                'allocated_bandwidth': allocated_bw,
                'requested_bandwidth': requested_bw,
                'allocation_ratio': allocation_ratio
            }
            
            allocations.append(allocation)
        
        return allocations
    
    def _fallback_allocation(self, onu_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Algoritmo de fallback simple cuando RL no está disponible
        
        Args:
            onu_requests: Lista de solicitudes
            
        Returns:
            Lista de asignaciones usando algoritmo simple
        """
        allocations = []
        
        for i, request in enumerate(onu_requests):
            onu_id = request.get('onu_id', i)
            requested_bw = request.get('requested_bandwidth', 0)
            
            # Asignación simple: 80% de lo solicitado
            allocated_bw = int(requested_bw * 0.8)
            
            allocation = {
                'onu_id': onu_id,
                'allocated_bandwidth': allocated_bw,
                'requested_bandwidth': requested_bw,
                'allocation_ratio': 0.8
            }
            
            allocations.append(allocation)
        
        return allocations
    
    def reset(self):
        """Resetear estado del algoritmo"""
        self.last_observation = None
        self.decision_count = 0
        print("[RL] Bridge reseteado")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del algoritmo"""
        return {
            'name': self.get_name(),
            'model_path': self.model_path,
            'decisions_made': self.decision_count,
            'model_loaded': self.model is not None,
            'netponpy_available': NETPONPY_AVAILABLE
        }
    
    def cleanup(self):
        """Limpiar recursos"""
        if self.temp_env:
            try:
                self.temp_env.close()
            except:
                pass
            self.temp_env = None
        
        self.model = None
        print("[RL] Bridge limpiado")


class ModelManager(QObject):
    """Gestor de modelos RL para la interfaz"""
    
    # Señales
    model_loaded = pyqtSignal(str)  # Ruta del modelo cargado
    model_error = pyqtSignal(str)   # Error cargando modelo
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.loaded_models = {}  # Dict[str, RLModelDBABridge]
        # Configurar directorio de modelos en PonLab/models/
        ponlab_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Subir 3 niveles desde core/rl_integration/model_bridge.py
        self.models_directory = os.path.join(ponlab_dir, "models")  # Carpeta models en la raíz
    
    def get_available_models(self) -> List[str]:
        """
        Obtener lista de modelos disponibles
        
        Returns:
            Lista de nombres de modelos
        """
        models = []
        
        if not os.path.exists(self.models_directory):
            return models
        
        try:
            for filename in os.listdir(self.models_directory):
                if filename.endswith('.zip'):  # Modelos de stable-baselines3
                    models.append(filename)
        
        except Exception as e:
            print(f"[ERROR] Error listando modelos: {str(e)}")
        
        return models
    
    def load_model(self, model_name: str, env_params: Dict[str, Any]) -> Optional[RLModelDBABridge]:
        """
        Cargar modelo RL
        
        Args:
            model_name: Nombre del archivo del modelo
            env_params: Parámetros del entorno
            
        Returns:
            Bridge del modelo o None si falló
        """
        model_path = os.path.join(self.models_directory, model_name)
        
        if not os.path.exists(model_path):
            error_msg = f"Modelo no encontrado: {model_path}"
            print(f"[ERROR] {error_msg}")
            self.model_error.emit(error_msg)
            return None
        
        try:
            bridge = RLModelDBABridge(model_path, env_params)
            
            if bridge.model is not None:
                self.loaded_models[model_name] = bridge
                self.model_loaded.emit(model_path)
                print(f"[OK] Modelo RL cargado: {model_name}")
                return bridge
            else:
                error_msg = f"Error cargando modelo: {model_name}"
                self.model_error.emit(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Error creando bridge para {model_name}: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.model_error.emit(error_msg)
            return None
    
    def get_model(self, model_name: str) -> Optional[RLModelDBABridge]:
        """Obtener modelo cargado"""
        return self.loaded_models.get(model_name)
    
    def unload_model(self, model_name: str):
        """Descargar modelo"""
        if model_name in self.loaded_models:
            self.loaded_models[model_name].cleanup()
            del self.loaded_models[model_name]
            print(f"[OK] Modelo descargado: {model_name}")
    
    def cleanup(self):
        """Limpiar todos los modelos"""
        for model_name in list(self.loaded_models.keys()):
            self.unload_model(model_name)
        print("[OK] ModelManager limpiado")