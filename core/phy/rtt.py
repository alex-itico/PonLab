from dataclasses import dataclass

C = 299_792_458  # m/s

@dataclass
class PhyParams:
    scale_m_per_px: float = 0.1
    n_fiber: float = 1.468

def px_to_m(px: float, scale_m_per_px: float) -> float:
    return float(px) * float(scale_m_per_px)

def propagation_speed_mps(n_fiber: float) -> float:
    return C / float(n_fiber)

def one_way_delay_ns(distance_m: float, n_fiber: float) -> float:
    return (distance_m / propagation_speed_mps(n_fiber)) * 1e9

def rtt_ns_from_px(distance_px: float, params: PhyParams) -> int:
    d_m = px_to_m(distance_px, params.scale_m_per_px)
    rtt = 2.0 * one_way_delay_ns(d_m, params.n_fiber)
    return int(rtt)
