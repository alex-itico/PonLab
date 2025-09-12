# Ejecuta: python tests_messages_basic.py
from core.dba.messages import Report, Grant, CycleTiming, bytes_to_ns

def main():
    # 1) Instancias básicas
    timing = CycleTiming()  # usa defaults (10 Gbps, 1000 ns guard, etc.)
    r = Report(onu_id="ONU_X", queues_bytes={"EF":0,"AF":1200,"BE":18000}, timestamp_ns=0)
    size = 12_000  # 12 kB
    tx_ns = bytes_to_ns(size, timing.line_rate_bps)  # tiempo puro de TX a 10 Gbps
    g = Grant(onu_id=r.onu_id, size_bytes=size, start_time_ns=0, duration_ns=tx_ns + timing.guard_time_ns)

    print("OK import & construct:", isinstance(r, Report), isinstance(g, Grant), isinstance(timing, CycleTiming))
    print("tx_ns (12kB @ 10Gbps) =", tx_ns, "ns")
    print("grant duration (incl guard) =", g.duration_ns, "ns")

    # 2) Edge cases sanos
    assert bytes_to_ns(0, timing.line_rate_bps) == 0
    assert g.duration_ns > tx_ns  # incluye guard time

    print("All assertions passed ✅")

if __name__ == "__main__":
    main()
