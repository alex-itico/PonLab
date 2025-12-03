"""
Entorno RL nativo de PonLab
Implementación propia de entorno para entrenamiento RL
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
import random

# Import unified reward function
from .reward_functions import calculate_pon_reward, get_reward_components

# Importaciones condicionales
try:
    import gymnasium as gym
    from gymnasium import spaces
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False
    print("[WARNING] Gymnasium no disponible - usando implementación básica")


if GYMNASIUM_AVAILABLE:
    class PonRLEnvironment(gym.Env):
        """Entorno RL nativo de PonLab usando Gymnasium"""

        def __init__(self, num_onus=4, traffic_scenario='residential_medium', onu_configs=None):
            super().__init__()

            if onu_configs:
                self.onu_configs = onu_configs
                self.num_onus = len(onu_configs)
                self.traffic_scenario = 'custom' # Escenario mixto basado en topología
            else:
                self.onu_configs = None
                self.num_onus = num_onus
                self.traffic_scenario = traffic_scenario

            # Espacios de observación y acción
            obs_size = self.num_onus * 3 + 1
            self.observation_space = spaces.Box(
                low=0.0, high=1.0, shape=(obs_size,), dtype=np.float32
            )
            self.action_space = spaces.Box(
                low=0.0, high=1.0, shape=(self.num_onus,), dtype=np.float32
            )

            # Estado interno
            self.current_step = 0
            self.max_steps = 1000
            self.total_bandwidth = 1000.0  # Mbps

            # Métricas de red simuladas
            self.onu_requests = np.zeros(self.num_onus)
            self.onu_delays = np.zeros(self.num_onus)
            self.onu_buffers = np.zeros(self.num_onus)

            # Parámetros de escenario de tráfico
            if not self.onu_configs:
                self.traffic_params = self._get_traffic_params(self.traffic_scenario)

        def _get_traffic_params(self, scenario):
            """Obtener parámetros según escenario de tráfico"""
            scenarios = {
                'residential_light': {'base_demand': 0.2, 'variation': 0.1, 'peak_prob': 0.1},
                'residential_medium': {'base_demand': 0.4, 'variation': 0.2, 'peak_prob': 0.15},
                'residential_heavy': {'base_demand': 0.6, 'variation': 0.3, 'peak_prob': 0.2},
                'enterprise': {'base_demand': 0.7, 'variation': 0.15, 'peak_prob': 0.25},
                'business_standard': {'base_demand': 0.7, 'variation': 0.15, 'peak_prob': 0.25}, # Alias para enterprise
                'mixed': {'base_demand': 0.5, 'variation': 0.25, 'peak_prob': 0.18}
            }
            return scenarios.get(scenario, scenarios['residential_medium'])

        def reset(self, seed=None, options=None):
            """Reiniciar el entorno"""
            super().reset(seed=seed)
            self.current_step = 0

            # Generar estado inicial
            self.onu_requests = self._generate_traffic_demands()
            self.onu_delays = np.random.uniform(0.001, 0.01, self.num_onus)
            self.onu_buffers = np.random.uniform(0.1, 0.3, self.num_onus)

            observation = self._get_observation()
            info = {'step': self.current_step}

            return observation, info

        def step(self, action):
            """Ejecutar un paso en el entorno"""
            # Normalizar acción (distribución de ancho de banda)
            action = np.array(action, dtype=np.float32)
            action = np.clip(action, 0.0, 1.0)

            # Normalizar para que sume 1
            if np.sum(action) > 0:
                action = action / np.sum(action)
            else:
                action = np.ones(self.num_onus) / self.num_onus

            # Calcular asignaciones de ancho de banda
            allocations = action * self.total_bandwidth

            # Actualizar métricas de red basadas en asignaciones
            self._update_network_metrics(allocations)

            # Calcular recompensa
            reward = self._calculate_reward(allocations)

            # Generar nuevo tráfico para el siguiente paso
            self.onu_requests = self._generate_traffic_demands()

            self.current_step += 1
            terminated = self.current_step >= self.max_steps
            truncated = False

            observation = self._get_observation()
            info = {
                'step': self.current_step,
                'allocations': allocations,
                'requests': self.onu_requests.copy(),
                'reward_components': self._get_reward_components(allocations)
            }

            return observation, reward, terminated, truncated, info

        def _generate_traffic_demands(self):
            """Generar demandas de tráfico realistas para cada ONU."""
            demands = []
            if self.onu_configs:
                # Generar tráfico basado en la configuración individual de cada ONU
                for i in range(self.num_onus):
                    onu_config = self.onu_configs[i]
                    traffic_profile = onu_config.get('traffic_profile', 'residential_medium')
                    params = self._get_traffic_params(traffic_profile)
                    
                    base = params['base_demand']
                    variation = params['variation']
                    peak_prob = params['peak_prob']
                    
                    demand = base + np.random.uniform(-variation, variation)
                    if np.random.random() < peak_prob:
                        demand *= np.random.uniform(2.0, 4.0)
                    
                    demands.append(np.clip(demand, 0.0, 1.0))
            else:
                # Comportamiento anterior: usar un solo escenario para todas las ONUs
                params = self.traffic_params
                base = params['base_demand']
                variation = params['variation']
                peak_prob = params['peak_prob']
                
                for _ in range(self.num_onus):
                    demand = base + np.random.uniform(-variation, variation)
                    if np.random.random() < peak_prob:
                        demand *= np.random.uniform(2.0, 4.0)
                    demands.append(np.clip(demand, 0.0, 1.0))

            return np.array(demands, dtype=np.float32)

        def _update_network_metrics(self, allocations):
            """Actualizar métricas de red basadas en asignaciones"""
            for i in range(self.num_onus):
                requested = self.onu_requests[i] * self.total_bandwidth
                allocated = allocations[i]

                # Actualizar delay (aumenta si no se satisface la demanda)
                if allocated < requested:
                    satisfaction_ratio = allocated / max(requested, 0.1)
                    self.onu_delays[i] = min(0.1, self.onu_delays[i] * (2.0 - satisfaction_ratio))
                else:
                    self.onu_delays[i] = max(0.001, self.onu_delays[i] * 0.9)

                # Actualizar buffer (se llena si no se satisface demanda)
                if allocated < requested:
                    self.onu_buffers[i] = min(1.0, self.onu_buffers[i] + (requested - allocated) / self.total_bandwidth)
                else:
                    self.onu_buffers[i] = max(0.0, self.onu_buffers[i] - 0.1)

        def _calculate_reward(self, allocations):
            """
            Calculate reward using unified reward function.

            This ensures consistency with RealPonEnv for proper sim-to-real transfer.
            """
            reward = calculate_pon_reward(
                onu_requests=self.onu_requests,
                allocations=allocations,
                onu_delays=self.onu_delays,
                onu_buffers=self.onu_buffers,
                total_bandwidth=self.total_bandwidth
            )
            return reward

        def _get_reward_components(self, allocations):
            """
            Get individual reward components for analysis.

            Uses unified function to ensure consistency with RealPonEnv.
            """
            return get_reward_components(
                onu_requests=self.onu_requests,
                allocations=allocations,
                onu_delays=self.onu_delays,
                onu_buffers=self.onu_buffers,
                total_bandwidth=self.total_bandwidth
            )

        def _get_observation(self):
            """Construir observación del estado actual"""
            # Normalizar requests
            normalized_requests = self.onu_requests

            # Calcular utilización total
            total_utilization = np.sum(self.onu_requests)

            # Combinar todas las observaciones
            observation = np.concatenate([
                normalized_requests,      # Requests por ONU
                self.onu_delays,         # Delays por ONU
                self.onu_buffers,        # Buffer levels por ONU
                [total_utilization]      # Utilización total
            ])

            return observation.astype(np.float32)

else:
    # Implementación básica sin gymnasium para fallback
    class PonRLEnvironment:
        """Entorno RL básico sin Gymnasium (fallback)"""

        def __init__(self, num_onus=4, traffic_scenario='residential_medium', onu_configs=None):
            self.num_onus = len(onu_configs) if onu_configs else num_onus
            self.traffic_scenario = 'custom' if onu_configs else traffic_scenario
            self.current_step = 0
            self.max_steps = 1000

            print(f"[INFO] Entorno RL básico inicializado (fallback): {self.num_onus} ONUs, escenario {self.traffic_scenario}")

        def reset(self):
            self.current_step = 0
            observation = np.random.uniform(0, 1, self.num_onus * 3 + 1)
            return observation, {}

        def step(self, action):
            observation = np.random.uniform(0, 1, self.num_onus * 3 + 1)
            reward = np.random.uniform(0.3, 0.8)
            terminated = self.current_step >= self.max_steps
            self.current_step += 1
            return observation, reward, terminated, False, {}


def create_pon_rl_environment(num_onus=4, traffic_scenario='residential_medium', onu_configs=None, **kwargs):
    """Factory function para crear entorno RL de PonLab"""
    return PonRLEnvironment(
        num_onus=num_onus,
        traffic_scenario=traffic_scenario,
        onu_configs=onu_configs
    )