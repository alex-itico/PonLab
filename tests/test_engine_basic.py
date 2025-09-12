from core.dba.engine import OltDbaEngine, register, build_engine
from core.dba.messages import Report, CycleTiming, Grant

@register("test")
class TestEngine(OltDbaEngine):
    def compute_grants(self, reports, now_ns):
        grants = []
        cursor = now_ns
        for r in reports:
            demand = sum(r.queues_bytes.values())
            if demand > 0:
                grants.append(Grant(r.onu_id, demand, cursor, 1000))
                cursor += 1000
        return grants

def main():
    timing = CycleTiming()
    engine = build_engine("test", timing, {})
    reports = [
        Report("ONU1", {"BE": 5000}, 0),
        Report("ONU2", {"BE": 3000}, 0)
    ]
    grants = engine.compute_grants(reports, 0)
    for g in grants:
        print(g)

if __name__ == "__main__":
    main()
