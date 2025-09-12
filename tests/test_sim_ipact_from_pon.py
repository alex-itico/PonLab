# Ejecuta:  python -m tests.test_sim_ipact_from_pon
from core.sim.simulator import Simulator
from core.dba.messages import bytes_to_ns

def main():
    PON_PATH = "C:/Users/Varfyo/Desktop/PONLAB/mi_topologia_2.pon"   # ajusta si quieres probar con otro archivo
    sim = Simulator(PON_PATH)

    # Un ciclo de simulación
    reports, grants = sim.run_one_cycle()

    print("REPORTs (onu_id -> ts):")
    for r in sorted(reports, key=lambda x: (x.timestamp_ns, x.onu_id)):
        print(f"  {r.onu_id}: ts={r.timestamp_ns} ns, demand={sum(r.queues_bytes.values())} B")

    print("\nGRANTs:")
    for g in grants:
        print(f"  {g.onu_id}: size={g.size_bytes} B, start={g.start_time_ns} ns, dur={g.duration_ns} ns")

    # Checks mínimos:
    assert len(grants) > 0, "No hubo grants"
    # Encadenamiento temporal correcto:
    for i in range(1, len(grants)):
        prev = grants[i-1]
        cur  = grants[i]
        assert cur.start_time_ns >= prev.start_time_ns + prev.duration_ns

    # Duración = bytes_to_ns + guard
    guard = sim.timing.guard_time_ns
    for g in grants:
        tx_ns = bytes_to_ns(g.size_bytes, sim.timing.line_rate_bps)
        assert g.duration_ns == tx_ns + guard

    print("\nSimulación IPACT (1 ciclo) OK ✅")

if __name__ == "__main__":
    main()
