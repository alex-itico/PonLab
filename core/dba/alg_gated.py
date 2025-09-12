# core/dba/alg_gated.py
from typing import List
from .engine import OltDbaEngine, register
from .messages import Report, Grant, bytes_to_ns

@register("gated")
class Gated(OltDbaEngine):
    """
    Gated DBA:
    - Ordena por timestamp de Report.
    - Concede exactamente lo reportado (sin límite), salvo que se entregue
      MAX_GRANT_BYTES para acotar (no estándar).
    - Duración = tiempo_tx(bytes) + guard_time_ns.
    Parámetros opcionales:
      - MAX_GRANT_BYTES (int)
    """
    def compute_grants(self, reports: List[Report], now_ns: int) -> List[Grant]:
        line_bps = self.timing.line_rate_bps
        guard = self.timing.guard_time_ns
        opt = self.params.get("MAX_GRANT_BYTES", None)
        limit = int(opt) if opt is not None else None
        ordered = sorted(reports, key=lambda r: (r.timestamp_ns, r.onu_id))
        grants: List[Grant] = []
        cursor = now_ns

        for r in ordered:
            demand = sum(r.queues_bytes.values())
            if demand <= 0:
                continue

            size = demand if limit is None else min(demand, limit)
            tx_ns = bytes_to_ns(size, line_bps)
            dur_ns = tx_ns + guard

            grants.append(Grant(
                onu_id=r.onu_id,
                size_bytes=size,
                start_time_ns=cursor,
                duration_ns=dur_ns
            ))
            cursor += dur_ns

        return grants
