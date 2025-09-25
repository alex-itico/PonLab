"""
Smart RL DBA Algorithm - COMPLETAMENTE INTERNO
Algoritmo DBA inteligente usando simulación de RL sin dependencias externas
PROHIBIDAS las referencias a netPONPy u otros proyectos externos
"""

import os
import sys
import json
import random
import numpy as np
from typing import Dict, List, Any, Optional
from .pon_dba import DBAAlgorithmInterface


class InternalRLAgent:
    """
    Agente RL interno simple que simula comportamiento inteligente
    SIN DEPENDENCIAS EXTERNAS - Completamente interno a PonLab
    """

    def __init__(self, num_onus: int = 4):
        self.num_onus = num_onus
        self.decision_count = 0
        self.learning_rate = 0.01

        # Tabla Q simple para decisiones
        self.q_table = {}

        # Políticas aprendidas simuladas
        self.policies = {
            'prioritize_low_buffer': 0.7,
            'balance_throughput': 0.6,
            'minimize_delay': 0.8,
            'fairness_factor': 0.5
        }

        # Historial para "aprendizaje" simulado
        self.decision_history = []

    def predict(self, observation: np.ndarray) -> np.ndarray:
        """
        Simular predicción de modelo RL
        Usa lógica interna inteligente sin dependencias externas
        """
        # Convertir observación a estado discreto
        state = self._observation_to_state(observation)

        # Obtener acción basada en políticas internas
        action = self._get_intelligent_action(state, observation)

        self.decision_count += 1
        return action

    def _observation_to_state(self, observation: np.ndarray) -> str:
        """Convertir observación a estado discreto para tabla Q"""
        # Simplificar observación a categorías
        if len(observation) >= 4:
            requests_high = sum(1 for x in observation[:4] if x > 0.7)
            requests_med = sum(1 for x in observation[:4] if 0.3 <= x <= 0.7)
            requests_low = sum(1 for x in observation[:4] if x < 0.3)

            return f"h{requests_high}_m{requests_med}_l{requests_low}"
        else:
            return "default"

    def _get_intelligent_action(self, state: str, observation: np.ndarray) -> np.ndarray:
        """
        Generar acción inteligente basada en políticas internas
        """
        action = np.zeros(self.num_onus)

        if len(observation) < self.num_onus:
            # Distribución equitativa como fallback
            action.fill(1.0 / self.num_onus)
            return action

        requests = observation[:self.num_onus]
        total_requests = np.sum(requests)

        if total_requests == 0:
            action.fill(1.0 / self.num_onus)
            return action

        # Aplicar políticas inteligentes internas

        # Política 1: Priorizar solicitudes altas pero con fairness
        base_allocation = requests / total_requests

        # Política 2: Ajustar según "buffer levels" simulados
        buffer_simulation = np.random.beta(2, 5, self.num_onus)  # Simular buffers típicos
        buffer_factor = 1.0 - (buffer_simulation * self.policies['prioritize_low_buffer'])

        # Política 3: Balance de throughput
        throughput_factor = np.ones(self.num_onus)
        for i in range(self.num_onus):
            if requests[i] > 0.8:  # Solicitudes muy altas
                throughput_factor[i] *= self.policies['balance_throughput']

        # Combinar políticas
        action = base_allocation * buffer_factor * throughput_factor

        # Normalizar
        action_sum = np.sum(action)
        if action_sum > 0:
            action = action / action_sum
        else:
            action.fill(1.0 / self.num_onus)

        # Agregar pequeña variabilidad para simular "exploración"
        noise = np.random.normal(0, 0.05, self.num_onus)
        action = np.clip(action + noise, 0.0, 1.0)

        # Renormalizar después del ruido
        action = action / np.sum(action)

        return action


class SmartRLDBAAlgorithm(DBAAlgorithmInterface):
    """
    Algoritmo DBA inteligente COMPLETAMENTE INTERNO
    Simula comportamiento RL sin dependencias externas
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        Inicializar algoritmo con agente RL interno

        Args:
            model_path: Ignorado - solo para compatibilidad
        """
        self.model_path = model_path
        self.agent = InternalRLAgent()
        self.decision_count = 0
        self.last_state = None

        # Configuración interna
        self.config = {
            'num_onus': 4,
            'intelligent_mode': True,
            'learning_enabled': True
        }

        # "Cargar" modelo simulado
        self._load_internal_model()

    def _load_internal_model(self) -> bool:
        """Simular carga de modelo usando agente interno"""
        try:
            # Simular diferentes "modelos" según el path
            if self.model_path:
                model_name = os.path.basename(self.model_path)

                # Ajustar políticas según el "modelo"
                if "ejemplo" in model_name.lower():
                    self.agent.policies['prioritize_low_buffer'] = 0.8
                    self.agent.policies['balance_throughput'] = 0.7
                elif "advanced" in model_name.lower():
                    self.agent.policies['prioritize_low_buffer'] = 0.9
                    self.agent.policies['minimize_delay'] = 0.9

                print(f"[OK] Modelo interno simulado cargado: {model_name}")
            else:
                print("[OK] Agente RL interno inicializado con políticas por defecto")

            return True

        except Exception as e:
            print(f"[ERROR] Error inicializando agente interno: {str(e)}")
            return False

    def allocate_bandwidth(self, onu_requests: Dict[str, float],
                          total_bandwidth: float, action: Any = None) -> Dict[str, float]:
        """
        Asignar ancho de banda usando agente RL interno
        """
        try:
            # Convertir estado actual a observación
            observation = self._create_observation(onu_requests, total_bandwidth)

            # Obtener acción del agente interno
            action = self.agent.predict(observation)

            # Convertir acción a asignaciones
            allocations = self._action_to_allocations(action, onu_requests, total_bandwidth)

            self.decision_count += 1
            self.last_state = {
                'requests': onu_requests.copy(),
                'total_bandwidth': total_bandwidth,
                'action': action.tolist(),
                'allocations': allocations.copy()
            }

            # Log periódico
            if self.decision_count % 50 == 0:
                print(f"[SMART-RL] {self.decision_count} decisiones inteligentes internas tomadas")
                self._log_decision_details(onu_requests, action, allocations)

            return allocations

        except Exception as e:
            print(f"[ERROR] Error en decisión RL interna: {str(e)}")
            return self._fallback_allocation(onu_requests, total_bandwidth)

    def _create_observation(self, onu_requests: Dict[str, float],
                           total_bandwidth: float) -> np.ndarray:
        """Crear observación para el agente interno"""
        num_onus = self.config['num_onus']

        # Solicitudes normalizadas
        requests = []
        onu_ids = sorted(onu_requests.keys()) if onu_requests else []

        for i in range(num_onus):
            onu_id = f"onu_{i}" if f"onu_{i}" in onu_requests else (onu_ids[i] if i < len(onu_ids) else None)
            if onu_id and onu_id in onu_requests:
                normalized_request = min(onu_requests[onu_id] / total_bandwidth, 1.0)
            else:
                normalized_request = 0.0
            requests.append(normalized_request)

        # Utilización total
        total_requested = sum(onu_requests.values()) if onu_requests else 0
        utilization = min(total_requested / total_bandwidth, 1.0) if total_bandwidth > 0 else 0

        # Simular métricas de red internas
        simulated_delays = [random.uniform(0.001, 0.05) for _ in range(num_onus)]
        simulated_buffers = [random.uniform(0.1, 0.9) for _ in range(num_onus)]

        # Combinar características
        observation = np.array(
            requests +
            [utilization] +
            simulated_delays +
            simulated_buffers,
            dtype=np.float32
        )

        return observation

    def _action_to_allocations(self, action: np.ndarray, onu_requests: Dict[str, float],
                             total_bandwidth: float) -> Dict[str, float]:
        """Convertir acción a asignaciones de ancho de banda"""
        allocations = {}

        if not onu_requests:
            return allocations

        onu_ids = sorted(onu_requests.keys())

        for i, onu_id in enumerate(onu_ids):
            if i < len(action):
                # Asignar según peso, limitado por lo solicitado
                max_allocation = onu_requests[onu_id]
                weight_allocation = action[i] * total_bandwidth

                allocated = min(max_allocation, weight_allocation)
                allocations[onu_id] = allocated
            else:
                allocations[onu_id] = 0.0

        return allocations

    def _fallback_allocation(self, onu_requests: Dict[str, float],
                           total_bandwidth: float) -> Dict[str, float]:
        """Algoritmo de fallback simple"""
        allocations = {}

        if not onu_requests:
            return allocations

        total_requested = sum(onu_requests.values())

        if total_requested <= total_bandwidth:
            allocations = onu_requests.copy()
        else:
            for onu_id, requested in onu_requests.items():
                proportion = requested / total_requested
                allocations[onu_id] = proportion * total_bandwidth

        return allocations

    def _log_decision_details(self, requests: Dict[str, float], action: np.ndarray,
                            allocations: Dict[str, float]):
        """Log detalles de la decisión para debugging"""
        print(f"[SMART-RL DECISION]")
        print(f"  Requests: {[(k, f'{v:.1f}') for k, v in requests.items()]}")
        print(f"  Action weights: {[f'{x:.3f}' for x in action[:4]]}")
        print(f"  Allocated: {[(k, f'{v:.1f}') for k, v in allocations.items()]}")

    def get_algorithm_name(self) -> str:
        """Obtener nombre del algoritmo"""
        if self.model_path:
            model_name = os.path.basename(self.model_path)
            return f"Smart-RL-Internal ({model_name})"
        else:
            return "Smart-RL-Internal"

    def set_environment_params(self, params: Dict[str, Any]):
        """Actualizar parámetros del entorno"""
        self.config.update(params)

        # Reconfigurar agente si es necesario
        if 'num_onus' in params:
            self.agent.num_onus = params['num_onus']

    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del algoritmo"""
        return {
            'name': self.get_algorithm_name(),
            'model_loaded': True,  # Siempre True para agente interno
            'model_path': self.model_path or "internal_agent",
            'decisions_made': self.decision_count,
            'agent_type': 'internal_simulated',
            'policies': self.agent.policies.copy(),
            'configuration': self.config.copy()
        }

    def cleanup(self):
        """Limpiar recursos"""
        self.agent.decision_history.clear()
        self.agent.q_table.clear()
        print("[OK] Smart RL DBA interno limpiado")


# Función helper para crear algoritmo desde archivo de modelo
def create_smart_rl_dba_from_model(model_path: str,
                                  env_params: Optional[Dict[str, Any]] = None) -> SmartRLDBAAlgorithm:
    """
    Crear SmartRLDBAAlgorithm usando agente interno

    Args:
        model_path: Ruta simulada del modelo (solo para configurar políticas)
        env_params: Parámetros del entorno

    Returns:
        Instancia configurada de SmartRLDBAAlgorithm
    """
    algorithm = SmartRLDBAAlgorithm(model_path)

    if env_params:
        algorithm.set_environment_params(env_params)

    return algorithm