"""
Real PON Environment for Reinforcement Learning
"""
import numpy as np
from typing import Dict, Any, Tuple, Optional

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYMNASIUM_AVAILABLE = True
except ImportError:
    GYMNASIUM_AVAILABLE = False
    class gym:
        Env = object
    class spaces:
        def Box(*args, **kwargs):
            return None


from ..simulation.pon_event_simulator import OptimizedHybridPONSimulator
from ..smart_rl_dba import SmartRLDBAAlgorithm

# Import unified reward function for consistency with PonRLEnvironment
from .reward_functions import calculate_pon_reward, get_reward_components

class RealPonEnv(gym.Env):
    """
    A gymnasium environment that wraps the OptimizedHybridPONSimulator.
    This allows a reinforcement learning agent to be trained on the "real"
    event-based simulation instead of a simplified mathematical model.
    """

    def __init__(self, num_onus: int = 4, traffic_scenario: str = "residential_medium", max_episode_steps: int = 1000):
        """
        Initializes the RealPonEnv.

        Args:
            num_onus (int): The number of ONUs in the network.
            traffic_scenario (str): The traffic scenario to use.
            max_episode_steps (int): The maximum number of steps per episode.
        """
        if not GYMNASIUM_AVAILABLE:
            raise ImportError("Cannot create RealPonEnv: gymnasium library is not installed.")

        super().__init__()

        # --- Simulation Configuration ---
        self.num_onus = num_onus
        self.traffic_scenario = traffic_scenario

        self.dba = SmartRLDBAAlgorithm(model_path=None, num_onus=self.num_onus)

        self.sim = OptimizedHybridPONSimulator(
            num_onus=self.num_onus,
            traffic_scenario=self.traffic_scenario,
            dba_algorithm=self.dba
        )

        # --- Environment Configuration ---
        self.max_episode_steps = max_episode_steps
        self.current_step = 0
        self.step_duration = 0.001  # Each step advances the simulation by 1ms

        # --- Gym Interface ---
        obs_size = self.num_onus * 3 + 1
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(obs_size,), dtype=np.float32)
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(self.num_onus,), dtype=np.float32)

    def _get_observation(self) -> np.ndarray:
        """
        Gathers the current state from the simulator and formats it as an observation vector.

        Returns:
            np.ndarray: The observation vector.
        """
        onu_requests = {}
        onu_delays = {}
        onu_buffers = {}

        reports = self.sim.olt._collect_reports()
        for onu_id, onu_report in reports.items():
            total_demand_bytes = sum(onu_report.values())
            if total_demand_bytes > 0:
                onu_requests[onu_id] = total_demand_bytes / (1024 * 1024)

        current_time = self.sim.simulation_time
        for onu_id, onu in self.sim.onus.items():
            total_bytes = sum(q.total_bytes for q in onu.queues.values())
            max_bytes = sum(q.max_bytes for q in onu.queues.values())
            onu_buffers[onu_id] = total_bytes / max_bytes if max_bytes > 0 else 0.0

            total_delay, packet_count = 0.0, 0
            for queue in onu.queues.values():
                for packet in queue.packets:
                    total_delay += current_time - packet.arrival_time
                    packet_count += 1
            onu_delays[onu_id] = total_delay / packet_count if packet_count > 0 else 0.0

        state = {
            "onu_requests": onu_requests,
            "onu_delays": onu_delays,
            "onu_buffers": onu_buffers,
            "total_bandwidth": self.sim.channel_capacity
        }
        return self.dba._create_observation(state)

    def _extract_metrics_from_simulator(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract metrics from the real simulator to use with unified reward function.

        Returns:
            Tuple of (onu_requests, allocations, onu_delays, onu_buffers)
        """
        onu_requests = np.zeros(self.num_onus, dtype=np.float32)
        onu_delays = np.zeros(self.num_onus, dtype=np.float32)
        onu_buffers = np.zeros(self.num_onus, dtype=np.float32)
        allocations = np.zeros(self.num_onus, dtype=np.float32)

        # Helper function to extract numeric index from ONU_ID string
        def get_onu_index(onu_id_str: str) -> int:
            """Extract numeric index from 'ONU_X' string."""
            if isinstance(onu_id_str, int):
                return onu_id_str
            # Extract number from string like "ONU_0" -> 0
            return int(onu_id_str.split('_')[-1])

        # Extract requests from OLT reports
        reports = self.sim.olt._collect_reports()
        for onu_id_str, onu_report in reports.items():
            try:
                onu_idx = get_onu_index(onu_id_str)
                if onu_idx < self.num_onus:
                    total_demand_bytes = sum(onu_report.values())
                    # Normalize to [0,1] relative to channel capacity
                    onu_requests[onu_idx] = min(total_demand_bytes / (self.sim.channel_capacity * 0.001), 1.0)
            except (ValueError, IndexError):
                continue

        # Extract current state from ONUs
        current_time = self.sim.simulation_time
        for onu_id_str, onu in self.sim.onus.items():
            try:
                onu_idx = get_onu_index(onu_id_str)
                if onu_idx >= self.num_onus:
                    continue

                # Buffer occupancy
                total_bytes = sum(q.total_bytes for q in onu.queues.values())
                max_bytes = sum(q.max_bytes for q in onu.queues.values())
                onu_buffers[onu_idx] = total_bytes / max_bytes if max_bytes > 0 else 0.0

                # Average delay per ONU
                total_delay, packet_count = 0.0, 0
                for queue in onu.queues.values():
                    for packet in queue.packets:
                        total_delay += current_time - packet.arrival_time
                        packet_count += 1
                onu_delays[onu_idx] = (total_delay / packet_count) if packet_count > 0 else 0.0
            except (ValueError, IndexError):
                continue

        # Extract REAL allocations from OLT (NO APPROXIMATION)
        last_allocations_dict = self.sim.olt.get_last_allocations()
        for onu_id_str, allocation_mb in last_allocations_dict.items():
            try:
                onu_idx = get_onu_index(onu_id_str)
                if onu_idx < self.num_onus:
                    # Allocations are in MB
                    allocations[onu_idx] = allocation_mb
            except (ValueError, IndexError):
                continue

        return onu_requests, allocations, onu_delays, onu_buffers

    def _calculate_reward(self, old_metrics: Dict, new_metrics: Dict) -> float:
        """
        Calculate reward using unified reward function.

        This ensures consistency with PonRLEnvironment for proper sim-to-real transfer.

        Args:
            old_metrics (Dict): The metrics from the previous step (kept for compatibility).
            new_metrics (Dict): The metrics from the current step (kept for compatibility).

        Returns:
            float: The calculated reward.
        """
        # Extract current state from simulator
        onu_requests, allocations, onu_delays, onu_buffers = self._extract_metrics_from_simulator()

        # Use unified reward function
        reward = calculate_pon_reward(
            onu_requests=onu_requests,
            allocations=allocations,
            onu_delays=onu_delays,
            onu_buffers=onu_buffers,
            total_bandwidth=self.sim.channel_capacity  # in bps
        )

        return float(reward)

    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """
        Resets the environment to an initial state.

        Args:
            seed (Optional[int]): The seed for the random number generator.
            options (Optional[Dict]): Additional options for resetting the environment.

        Returns:
            Tuple[np:ndarray, Dict]: A tuple containing the initial observation and an info dictionary.
        """
        super().reset(seed=seed)

        self.sim.reset_simulation()

        # CRITICAL FIX: Set simulation_duration to allow packet generation events
        # Without this, packet generation events won't regenerate because the check:
        # "if event.timestamp < self.simulation_duration" will always be False (0.0)
        # Set it to a large value to allow continuous packet generation
        self.sim.simulation_duration = self.max_episode_steps * self.step_duration * 10  # 10x safety margin

        self.sim._initialize_events()
        self.current_step = 0

        self._run_sim_step(duration=0.001)

        observation = self._get_observation()
        info = {}

        return observation, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Run one timestep of the environment's dynamics.

        Args:
            action (np.ndarray): The action to take.

        Returns:
            Tuple[np.ndarray, float, bool, bool, Dict]: A tuple containing the observation, reward, terminated flag, truncated flag, and an info dictionary.
        """
        self.sim.olt.set_rl_action(action)

        old_metrics = self.sim.metrics.copy()

        self._run_sim_step(duration=self.step_duration)

        new_metrics = self.sim.metrics.copy()

        reward = self._calculate_reward(old_metrics, new_metrics)

        observation = self._get_observation()

        self.current_step += 1
        terminated = self.current_step >= self.max_episode_steps
        truncated = False

        info = {'sim_time': self.sim.simulation_time}

        return observation, reward, terminated, truncated, info

    def _run_sim_step(self, duration: float):
        """
        Runs the event-based simulation for a given duration.

        Args:
            duration (float): The duration to run the simulation for.
        """
        if not self.sim.is_running:
            self.sim.is_running = True

        target_time = self.sim.simulation_time + duration

        while self.sim.event_queue.has_events() and self.sim.event_queue.peek_next_time() < target_time:

            event = self.sim.event_queue.get_next_event()

            self.sim.olt.check_and_execute_polling(self.sim.event_queue, event.timestamp)

            self.sim.simulation_time = event.timestamp
            self.sim._process_event(event)
            self.sim.events_processed += 1

        self.sim.simulation_time = target_time

    def render(self, mode='human'):
        """Not implemented"""
        pass

    def close(self):
        """Clean up resources"""
        self.sim.reset_simulation()

def create_real_pon_env(**kwargs):
    """
    Factory function for the environment.
    
    Returns:
        RealPonEnv: An instance of the RealPonEnv.
    """
    if not GYMNASIUM_AVAILABLE:
        return None
    return RealPonEnv(**kwargs)