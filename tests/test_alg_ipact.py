# tests/test_alg_ipact.py
# Ejecuta con:  python -m tests.test_alg_ipact

from core.dba.messages import Report, CycleTiming
from core.dba.engine import build_engine
import core.dba.alg_ipact

def main():
    timing = CycleTiming(guard_time_ns=1000, line_rate_bps=10_000_000_000)
    engine = build_engine("ipact", timing, {"MAX_GRANT_BYTES": 12000, "MIN_GRANT_BYTES": 0})

    # Tres ONUs con distintas demandas; timestamps simulan orden de llegada de REPORTs
    reports = [
        Report("ONU_B", {"BE": 5000},  10),   # llega 2°
        Report("ONU_A", {"BE": 20000},  0),   # llega 1°
        Report("ONU_C", {"BE": 40000}, 20),   # llega 3°
    ]

    grants = engine.compute_grants(reports, now_ns=0)

    # Mostrar resultados
    for g in grants:
        print(f"{g.onu_id} -> size={g.size_bytes}B start={g.start_time_ns}ns dur={g.duration_ns}ns")

    # Asserts básicos:
    # 1) Orden por timestamp: A, B, C
    assert [g.onu_id for g in grants] == ["ONU_A", "ONU_B", "ONU_C"]

    # 2) Límite por ONU (12kB): A (pide 20k) recibe 12k; B (5k) recibe 5k; C (40k) recibe 12k
    sizes = {g.onu_id: g.size_bytes for g in grants}
    assert sizes["ONU_A"] == 12000
    assert sizes["ONU_B"] == 5000
    assert sizes["ONU_C"] == 12000

    # 3) Encadenamiento temporal correcto (cada start es >= fin del anterior)
    for i in range(1, len(grants)):
        prev = grants[i-1]
        cur = grants[i]
        assert cur.start_time_ns >= prev.start_time_ns + prev.duration_ns

    print("IPACT-Limited OK ✅")

if __name__ == "__main__":
    main()
