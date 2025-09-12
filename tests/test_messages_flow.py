# Ejecuta: python tests_messages_flow.py
from core.dba.messages import Report, Grant, CycleTiming, bytes_to_ns

def trivial_engine(reports, timing, now_ns=0):
    """Motor ficticio: concede exactamente lo que se pide, en orden de llegada."""
    cursor = now_ns
    grants = []
    for r in reports:
        demand = sum(r.queues_bytes.values())
        if demand <= 0:
            continue
        tx_ns = bytes_to_ns(demand, timing.line_rate_bps)
        g = Grant(onu_id=r.onu_id, size_bytes=demand, start_time_ns=cursor, duration_ns=tx_ns + timing.guard_time_ns)
        grants.append(g)
        cursor += g.duration_ns
    return grants

def main():
    timing = CycleTiming()
    reports = [
        Report("ONU_A", {"EF":0,"AF":0,"BE":5000}, 0),
        Report("ONU_B", {"EF":0,"AF":2000,"BE":7000}, 0),
    ]
    grants = trivial_engine(reports, timing)
    for g in grants:
        print(f"Grant to {g.onu_id}: {g.size_bytes} B, start={g.start_time_ns} ns, dur={g.duration_ns} ns")

    assert len(grants) == 2
    assert grants[0].start_time_ns == 0
    assert grants[1].start_time_ns >= grants[0].start_time_ns + grants[0].duration_ns
    print("Flow contract ok ✅")

if __name__ == "__main__":
    main()
