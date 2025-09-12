# core/dba/alg_limited.py
from typing import List
from .engine import OltDbaEngine, register
from .messages import Report, Grant, bytes_to_ns

@register("limited")
class Limited(OltDbaEngine):
    """
    Limited DBA:
    - Ordena ONUs por timestamp de Report (aprox. orden de llegada).
    - Concede hasta MAX_GRANT_BYTES a cada ONU por ciclo.
    - Duración = tiempo_tx(bytes) + guard_time_ns.
    Parámetros:
      - MAX_GRANT_BYTES (int, opcional; por defecto 12000)
    """
    def compute_grants(self, reports: List[Report], now_ns: int) -> List[Grant]:
        line_bps = self.timing.line_rate_bps
        guard = self.timing.guard_time_ns
        max_grant = int(self.params.get("MAX_GRANT_BYTES", 12_000))

        ordered = sorted(reports, key=lambda r: (r.timestamp_ns, r.onu_id))
        grants: List[Grant] = []
        cursor = now_ns

        for r in ordered:
            demand = sum(r.queues_bytes.values())
            if demand <= 0:
                continue

            size = min(demand, max_grant)
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
