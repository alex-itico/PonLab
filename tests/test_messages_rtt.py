# Ejecuta: python tests_messages_rtt.py
from core.dba.messages import CycleTiming
C = 299_792_458  # m/s

def compute_rtt_ns(distance_px: float, timing: CycleTiming) -> float:
    d_m = distance_px * timing.scale_m_per_px
    v = C / timing.n_fiber
    return 2 * d_m / v * 1e9  # ns

def main():
    timing = CycleTiming(scale_m_per_px=0.1, n_fiber=1.468)

    d1_px = 380.26964117583725  # ~38.0 m en tu GUI
    d2_px = 436.1249820865574   # ~43.6 m en tu GUI

    rtt1 = compute_rtt_ns(d1_px, timing)
    rtt2 = compute_rtt_ns(d2_px, timing)

    print(f"d1 = {d1_px*timing.scale_m_per_px:.4f} m  -> RTT ≈ {rtt1:.3f} ns")
    print(f"d2 = {d2_px*timing.scale_m_per_px:.4f} m  -> RTT ≈ {rtt2:.3f} ns")

    # Valores guía (aprox): 372 ns y 427 ns
    assert 300 <= rtt1 <= 500
    assert 350 <= rtt2 <= 550
    print("RTT sanity checks passed ✅")

if __name__ == "__main__":
    main()
