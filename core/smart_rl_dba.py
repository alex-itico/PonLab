"""
Smart RL DBA Algorithm - External Model Integration
Algoritmo DBA que carga y utiliza un modelo entrenado con Stable-Baselines3.
"""

import os
import zipfile
import json
import tempfile
import numpy as np
from typing import Dict, Any, Optional

from .algorithms.pon_dba import DBAAlgorithmInterface

# --- Importación condicional de Stable-Baselines3 ---
RL_AVAILABLE = False
BaseAlgorithm = None
PPO = None
A2C = None
DQN = None
SAC = None

try:
    from stable_baselines3.common.base_class import BaseAlgorithm
    from stable_baselines3 import PPO, A2C, DQN, SAC
    RL_AVAILABLE = True
    print("[INFO] SmartRLDBA: Bibliotecas de Stable-Baselines3 disponibles.")
except (ImportError, OSError) as e:
    # ImportError: bibliotecas no instaladas
    # OSError: problemas con DLLs de PyTorch en Windows
    print("[WARNING] SmartRLDBA: 'stable-baselines3' o 'torch' no están disponibles.")
    print(f"[WARNING] Razón: {type(e).__name__}")
    print("[INFO] Instale con: pip install stable-baselines3 torch")
    print("[INFO] En Windows, si hay error de DLL, instale: pip install torch --index-url https://download.pytorch.org/whl/cpu")
# ---------------------------------------------------

# Mapeo de nombres de algoritmos a clases de SB3
ALGORITHM_MAP = {
    "PPO": PPO,
    "A2C": A2C,
    "DQN": DQN,
    "SAC": SAC,
} if RL_AVAILABLE else {}


class SmartRLDBAAlgorithm(DBAAlgorithmInterface):
    """
    Algoritmo DBA que utiliza un modelo de RL externo entrenado con Stable-Baselines3.
    """

    def __init__(self, model_path: Optional[str] = None, num_onus: int = 4):
        """
        Inicializa el algoritmo cargando un modelo de RL externo.

        Args:
            model_path: Ruta al archivo .zip del modelo entrenado.
            num_onus: Número de ONUs en la topología (para dimensionar la observación).
        """
        self.model_path = model_path
        self.model: Optional["BaseAlgorithm"] = None
        self.model_metadata: Dict[str, Any] = {}
        self.num_onus = num_onus
        self.decision_count = 0

        if model_path:
            self._load_external_model(model_path)
        else:
            print("[WARNING] SmartRLDBA: No se proporcionó una ruta de modelo (model_path).")
            print("[INFO] El algoritmo usará fallback equitativo hasta que se entrene un modelo.")

    def _load_external_model(self, path: str) -> bool:
        """
        Carga un modelo de RL desde un archivo .zip compatible.
        El .zip debe contener 'model.json' (metadatos) y 'sb3_model.zip' (el modelo real).
        """
        if not RL_AVAILABLE:
            print("[ERROR] SmartRLDBA: No se pueden cargar modelos porque 'stable-baselines3' no está disponible.")
            return False

        if not os.path.exists(path):
            print(f"[ERROR] SmartRLDBA: Archivo de modelo no encontrado en '{path}'")
            return False

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Cargar metadatos
                metadata_path = os.path.join(temp_dir, 'model.json')
                if not os.path.exists(metadata_path):
                    print(f"[ERROR] SmartRLDBA: 'model.json' no encontrado en el archivo zip.")
                    return False

                with open(metadata_path, 'r') as f:
                    self.model_metadata = json.load(f)

                # Cargar modelo de Stable-Baselines3
                sb3_model_path = os.path.join(temp_dir, 'sb3_model.zip')
                if not os.path.exists(sb3_model_path):
                    print(f"[ERROR] SmartRLDBA: 'sb3_model.zip' no encontrado en el archivo zip.")
                    return False

                model_class_name = self.model_metadata.get("algorithm", "PPO")
                ModelClass = ALGORITHM_MAP.get(model_class_name)

                if not ModelClass:
                    print(f"[ERROR] SmartRLDBA: Algoritmo '{model_class_name}' no es soportado o es desconocido.")
                    return False

                self.model = ModelClass.load(sb3_model_path)
                print(f"[OK] SmartRLDBA: Modelo '{model_class_name}' cargado exitosamente desde '{self.model_path}'")
                return True

        except Exception as e:
            print(f"[ERROR] SmartRLDBA: Fallo al cargar el modelo desde '{path}'. Causa: {e}")
            self.model = None
            return False

    def allocate_bandwidth(self, onu_requests: Dict[str, float],
                          total_bandwidth: float, action: Any = None) -> Dict[str, float]:
        """
        Asigna ancho de banda utilizando el modelo de RL cargado.

        Args:
            onu_requests: Dict {onu_id: bandwidth_requested_mb}
            total_bandwidth: float, capacidad total del canal en Mbps
            action: IGNORADO (el modelo RL genera sus propias acciones)

        Returns:
            Dict {onu_id: bandwidth_allocated_mb}
        """
        # Construir el diccionario de estado desde los parámetros
        state = {
            'onu_requests': onu_requests,
            'total_bandwidth': total_bandwidth,
            'onu_delays': {},  # Será poblado si está disponible
            'onu_buffers': {}  # Será poblado si está disponible
        }

        if not self.model:
            # Si no hay modelo cargado, usar fallback equitativo
            return self._fallback_allocation(state)

        try:
            # 1. Crear la observación a partir del estado de la red
            observation = self._create_observation(state)

            # 2. Obtener la acción del modelo de RL
            action, _ = self.model.predict(observation, deterministic=True)

            # 3. Convertir la acción en asignaciones de ancho de banda
            allocations = self._action_to_allocations(action, state)

            self.decision_count += 1
            if self.decision_count % 100 == 0:
                print(f"[SmartRL-DBA] Decisiones tomadas: {self.decision_count}")

            return allocations

        except Exception as e:
            print(f"[ERROR] SmartRLDBA: Error durante la predicción/asignación. Causa: {e}")
            return self._fallback_allocation(state)

    def _create_observation(self, state: Dict[str, Any]) -> np.ndarray:
        """
        Construye el vector de observación para el modelo de RL.
        El formato debe coincidir EXACTAMENTE con el de PonRLEnvironment.
        IMPORTANTE: Usa self.num_onus del modelo (fijo), NO del estado actual.
        """
        onu_requests = state.get('onu_requests', {})
        onu_delays = state.get('onu_delays', {})
        onu_buffers = state.get('onu_buffers', {})
        total_bandwidth = state.get('total_bandwidth', 1.0)

        # Asegurar un orden consistente de ONUs
        sorted_onu_ids = sorted(onu_requests.keys())
        num_actual_onus = len(sorted_onu_ids)

        # IMPORTANTE: NO cambiar self.num_onus - debe coincidir con el modelo entrenado
        # Si hay menos ONUs en la simulación, rellenamos con ceros
        # Si hay más, solo usamos las primeras self.num_onus

        # Advertencia si hay desajuste (solo una vez)
        if not hasattr(self, '_mismatch_warned'):
            if num_actual_onus != self.num_onus:
                print(f"[WARNING] SmartRLDBA: Modelo entrenado con {self.num_onus} ONUs, pero la simulación tiene {num_actual_onus} ONUs.")
                if num_actual_onus < self.num_onus:
                    print(f"[INFO] Rellenando con ceros para las {self.num_onus - num_actual_onus} ONUs faltantes.")
                else:
                    print(f"[INFO] Usando solo las primeras {self.num_onus} ONUs de la simulación.")
                self._mismatch_warned = True

        requests_norm = np.zeros(self.num_onus, dtype=np.float32)
        delays_norm = np.zeros(self.num_onus, dtype=np.float32)
        buffers_norm = np.zeros(self.num_onus, dtype=np.float32)

        # Llenar solo hasta min(len(sorted_onu_ids), self.num_onus)
        for i in range(min(len(sorted_onu_ids), self.num_onus)):
            onu_id = sorted_onu_ids[i]

            # Normalizar solicitudes
            req_bw = onu_requests.get(onu_id, 0.0)
            requests_norm[i] = min(req_bw / total_bandwidth, 1.0) if total_bandwidth > 0 else 0.0

            # Normalizar delays (ej: suponer que 0.1s es el delay máximo)
            delay = onu_delays.get(onu_id, 0.0)
            delays_norm[i] = min(delay / 0.1, 1.0)

            # Los buffers ya están normalizados (0.0 a 1.0)
            buffers_norm[i] = onu_buffers.get(onu_id, 0.0)

        # Utilización total
        total_requested = sum(onu_requests.values())
        total_utilization = min(total_requested / total_bandwidth, 1.0) if total_bandwidth > 0 else 0.0

        # Concatenar en el orden correcto: [requests, delays, buffers, utilización]
        observation = np.concatenate([
            requests_norm,
            delays_norm,
            buffers_norm,
            np.array([total_utilization], dtype=np.float32)
        ])

        return observation

    def _action_to_allocations(self, action: np.ndarray, state: Dict[str, Any]) -> Dict[str, float]:
        """
        Convierte la acción del modelo (pesos) en asignaciones de ancho de banda.
        IMPORTANTE: La acción tiene longitud self.num_onus (del modelo),
        pero la simulación puede tener menos ONUs.
        """
        onu_requests = state.get('onu_requests', {})
        total_bandwidth = state.get('total_bandwidth', 0)
        allocations = {}

        if not onu_requests:
            return allocations

        sorted_onu_ids = sorted(onu_requests.keys())
        num_actual_onus = len(sorted_onu_ids)

        # La acción viene del modelo con longitud self.num_onus
        # Solo usamos las primeras num_actual_onus acciones
        action_slice = action[:num_actual_onus]

        # Normalizar la acción para que sume 1 (distribución de probabilidad)
        action_sum = np.sum(action_slice)
        if action_sum > 0:
            normalized_action = action_slice / action_sum
        else:
            # Si la acción es cero, distribuir equitativamente entre ONUs actuales
            normalized_action = np.ones(num_actual_onus, dtype=np.float32) / num_actual_onus

        for i, onu_id in enumerate(sorted_onu_ids):
            # La asignación es una proporción del ancho de banda total
            # No debe exceder lo que la ONU realmente solicitó
            requested_bw = onu_requests[onu_id]
            assigned_bw = normalized_action[i] * total_bandwidth
            allocations[onu_id] = min(requested_bw, assigned_bw)

        return allocations

    def _fallback_allocation(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Algoritmo de fallback simple: FCFS/proporcional."""
        onu_requests = state.get('onu_requests', {})
        total_bandwidth = state.get('total_bandwidth', 0)
        allocations = {}

        if not onu_requests:
            return allocations

        total_requested = sum(onu_requests.values())
        if total_requested <= total_bandwidth:
            return onu_requests.copy()

        for onu_id, requested in onu_requests.items():
            proportion = requested / total_requested
            allocations[onu_id] = proportion * total_bandwidth

        return allocations

    def get_algorithm_name(self) -> str:
        """Retorna el nombre del algoritmo y el modelo cargado."""
        if self.model:
            model_name = os.path.basename(self.model_path) if self.model_path else "loaded_model"
            algo_type = self.model_metadata.get('algorithm', 'RL')
            return f"Smart-RL ({algo_type} - {model_name})"
        return "Smart-RL (Fallback)"

    def set_environment_params(self, params: Dict[str, Any]):
        """Actualiza parámetros del entorno, como el número de ONUs."""
        if 'num_onus' in params:
            self.num_onus = params['num_onus']
            print(f"[INFO] SmartRLDBA: Número de ONUs actualizado a {self.num_onus}")

    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del algoritmo."""
        return {
            'name': self.get_algorithm_name(),
            'model_loaded': self.model is not None,
            'model_path': self.model_path,
            'decisions_made': self.decision_count,
            'agent_type': 'external_stable_baselines3' if self.model else 'fallback',
            'model_metadata': self.model_metadata,
        }

    def cleanup(self):
        """Limpia recursos."""
        self.model = None
        print("[OK] Smart RL DBA (External) limpiado.")


def create_smart_rl_dba_from_model(model_path: str,
                                  env_params: Optional[Dict[str, Any]] = None) -> SmartRLDBAAlgorithm:
    """
    Factory function para crear una instancia de SmartRLDBAAlgorithm con un modelo.
    """
    num_onus = env_params.get('num_onus', 4) if env_params else 4
    algorithm = SmartRLDBAAlgorithm(model_path=model_path, num_onus=num_onus)

    if env_params:
        algorithm.set_environment_params(env_params)

    return algorithm
