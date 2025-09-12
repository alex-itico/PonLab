from typing import List
from .engine import OltDbaEngine, register
from .messages import Report, Grant, bytes_to_ns

@register("ipact")
class IPACTLimited(OltDbaEngine):
    """
    IPACT-Limited (MVP robusto):
    - Interleaved polling: orden de ONUs según timestamp del Report (aprox. orden de llegada).
    - Asigna por ONU hasta MAX_GRANT_BYTES; si la ONU pidió más, el excedente queda en cola al próximo ciclo.
    - Si MIN_GRANT_BYTES > 0 y hay demanda, asegura un mínimo para evitar starvation de ONUs con solicitudes pequeñas.
    - Duración del slot = tiempo_tx(bytes) + guard_time_ns.
    Parámetros esperados en self.params:
      - MAX_GRANT_BYTES (int, p.ej. 12000)
      - MIN_GRANT_BYTES (int, opcional, p.ej. 0 o 1500)
    """

    def compute_grants(self, reports: List[Report], now_ns: int) -> List[Grant]:
        line_bps = self.timing.line_rate_bps
        guard = self.timing.guard_time_ns
        max_grant = int(self.params.get("MAX_GRANT_BYTES", 12_000))
        min_grant = int(self.params.get("MIN_GRANT_BYTES", 0))

        # Ordenar por marca de tiempo (interleaving). Si empatan, por onu_id.
        ordered = sorted(reports, key=lambda r: (r.timestamp_ns, r.onu_id))

        grants: List[Grant] = []
        cursor = now_ns

        for r in ordered:
            demand = sum(r.queues_bytes.values())
            if demand <= 0:
                continue

            # Tamaño concedido limitado + mínimo opcional
            size = min(demand, max_grant)
            if min_grant > 0:
                size = max(min_grant, size)

            # Duración = transmisión + guard
            tx_ns = bytes_to_ns(size, line_bps)
            dur_ns = tx_ns + guard

            grants.append(Grant(
                onu_id=r.onu_id,
                size_bytes=size,
                start_time_ns=cursor,
                duration_ns=dur_ns
            ))
            cursor += dur_ns  # siguiente slot comienza al terminar este

        return grants