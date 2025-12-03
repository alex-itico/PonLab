"""
Unified Reward Functions for PON RL Environments

This module provides shared reward calculation logic to ensure consistency
between the simplified training environment (PonRLEnvironment) and the
realistic validation environment (RealPonEnv).
"""

import numpy as np
from typing import Dict, List, Tuple


def calculate_pon_reward(
    onu_requests: np.ndarray,
    allocations: np.ndarray,
    onu_delays: np.ndarray,
    onu_buffers: np.ndarray,
    total_bandwidth: float,
    weights: Dict[str, float] = None
) -> float:
    """
    Calculate unified reward for PON DBA problem.

    This function implements a multi-objective reward combining:
    1. Utilization efficiency (how much bandwidth is used)
    2. Demand satisfaction (how well requests are met)
    3. Fairness (equity across ONUs)
    4. Delay penalty (punishment for high delays)
    5. Buffer penalty (punishment for queue buildup)

    Args:
        onu_requests: Array of normalized bandwidth requests per ONU [0,1]
        allocations: Array of allocated bandwidth per ONU (in Mbps or bytes)
        onu_delays: Array of current delays per ONU (in seconds)
        onu_buffers: Array of normalized buffer occupancy per ONU [0,1]
        total_bandwidth: Total available bandwidth (Mbps or bytes/s)
        weights: Optional dict with keys 'utilization', 'satisfaction',
                 'fairness', 'delay', 'buffer'. Defaults to balanced weights.

    Returns:
        float: Reward value in range [0, 1]
    """
    # Default weights (can be overridden for experiments)
    if weights is None:
        weights = {
            'utilization': 0.25,
            'satisfaction': 0.30,
            'fairness': 0.20,
            'delay': 0.15,
            'buffer': 0.10
        }

    num_onus = len(onu_requests)

    # ==================== Component 1: Utilization Efficiency ====================
    total_allocated = np.sum(allocations)
    utilization_efficiency = min(total_allocated / total_bandwidth, 1.0)

    # ==================== Component 2: Demand Satisfaction ====================
    satisfaction_rewards = []
    for i in range(num_onus):
        requested = onu_requests[i] * total_bandwidth
        allocated = allocations[i]

        if requested > 0.001:  # Avoid division by zero
            satisfaction = min(allocated / requested, 1.0)
            satisfaction_rewards.append(satisfaction)
        else:
            # If ONU didn't request anything, satisfaction is perfect
            satisfaction_rewards.append(1.0)

    avg_satisfaction = np.mean(satisfaction_rewards) if satisfaction_rewards else 1.0

    # ==================== Component 3: Fairness (Jain's Index style) ====================
    if len(satisfaction_rewards) > 1:
        # Use coefficient of variation (std/mean) as unfairness measure
        std_satisfaction = np.std(satisfaction_rewards)
        fairness = 1.0 - min(std_satisfaction, 1.0)  # Clip to [0,1]
    else:
        fairness = 1.0

    # ==================== Component 4: Delay Penalty ====================
    avg_delay = np.mean(onu_delays)
    # Penalize delays > 100ms (0.1s) heavily
    # delay_penalty = 1.0 means no delay, 0.0 means very high delay
    delay_penalty = max(0.0, 1.0 - avg_delay * 10.0)

    # ==================== Component 5: Buffer Penalty ====================
    avg_buffer = np.mean(onu_buffers)
    # buffer_penalty = 1.0 means empty buffers, 0.0 means full buffers
    buffer_penalty = max(0.0, 1.0 - avg_buffer)

    # ==================== Weighted Sum ====================
    reward = (
        weights['utilization'] * utilization_efficiency +
        weights['satisfaction'] * avg_satisfaction +
        weights['fairness'] * fairness +
        weights['delay'] * delay_penalty +
        weights['buffer'] * buffer_penalty
    )

    return float(reward)


def get_reward_components(
    onu_requests: np.ndarray,
    allocations: np.ndarray,
    onu_delays: np.ndarray,
    onu_buffers: np.ndarray,
    total_bandwidth: float
) -> Dict[str, float]:
    """
    Get individual reward components for analysis.

    Useful for debugging, logging, and understanding what the agent is optimizing.

    Returns:
        Dict with keys: 'utilization_efficiency', 'avg_satisfaction',
                        'fairness', 'delay_penalty', 'buffer_penalty'
    """
    num_onus = len(onu_requests)

    # Utilization
    total_allocated = np.sum(allocations)
    utilization_efficiency = min(total_allocated / total_bandwidth, 1.0)

    # Satisfaction
    satisfaction_rewards = []
    for i in range(num_onus):
        requested = onu_requests[i] * total_bandwidth
        allocated = allocations[i]
        if requested > 0.001:
            satisfaction = min(allocated / requested, 1.0)
            satisfaction_rewards.append(satisfaction)
        else:
            satisfaction_rewards.append(1.0)
    avg_satisfaction = np.mean(satisfaction_rewards) if satisfaction_rewards else 1.0

    # Fairness
    if len(satisfaction_rewards) > 1:
        std_satisfaction = np.std(satisfaction_rewards)
        fairness = 1.0 - min(std_satisfaction, 1.0)
    else:
        fairness = 1.0

    # Delays
    avg_delay = np.mean(onu_delays)
    delay_penalty = max(0.0, 1.0 - avg_delay * 10.0)

    # Buffers
    avg_buffer = np.mean(onu_buffers)
    buffer_penalty = max(0.0, 1.0 - avg_buffer)

    return {
        'utilization_efficiency': float(utilization_efficiency),
        'avg_satisfaction': float(avg_satisfaction),
        'fairness': float(fairness),
        'delay_penalty': float(delay_penalty),
        'buffer_penalty': float(buffer_penalty),
        'avg_delay': float(avg_delay),
        'avg_buffer': float(avg_buffer),
        'satisfaction_rewards': satisfaction_rewards
    }


def calculate_alternative_rewards(
    onu_requests: np.ndarray,
    allocations: np.ndarray,
    onu_delays: np.ndarray,
    onu_buffers: np.ndarray,
    total_bandwidth: float
) -> Dict[str, float]:
    """
    Calculate alternative reward formulations for ablation studies.

    Useful for validating Hypothesis H4 (weighted reward balances multiple objectives).

    Returns:
        Dict with keys:
        - 'balanced': Standard balanced reward
        - 'latency_only': Only optimizes for low latency
        - 'throughput_only': Only optimizes for high throughput
        - 'fairness_only': Only optimizes for fairness
    """
    # Balanced (default)
    balanced = calculate_pon_reward(onu_requests, allocations, onu_delays, onu_buffers, total_bandwidth)

    # Latency-focused
    latency_only = calculate_pon_reward(
        onu_requests, allocations, onu_delays, onu_buffers, total_bandwidth,
        weights={'utilization': 0.05, 'satisfaction': 0.10, 'fairness': 0.05, 'delay': 0.70, 'buffer': 0.10}
    )

    # Throughput-focused
    throughput_only = calculate_pon_reward(
        onu_requests, allocations, onu_delays, onu_buffers, total_bandwidth,
        weights={'utilization': 0.50, 'satisfaction': 0.40, 'fairness': 0.05, 'delay': 0.025, 'buffer': 0.025}
    )

    # Fairness-focused
    fairness_only = calculate_pon_reward(
        onu_requests, allocations, onu_delays, onu_buffers, total_bandwidth,
        weights={'utilization': 0.10, 'satisfaction': 0.20, 'fairness': 0.60, 'delay': 0.05, 'buffer': 0.05}
    )

    return {
        'balanced': balanced,
        'latency_only': latency_only,
        'throughput_only': throughput_only,
        'fairness_only': fairness_only
    }
