from typing import Dict, Any
from core.phy.rtt import PhyParams, rtt_ns_from_px

def build_onu_rtts(devices: Dict[str, Any], connections: Dict[str, Any], params: PhyParams) -> Dict[str, int]:
    """
    Devuelve {onu_id: rtt_ns} usando la primera conexión OLT<->ONU que encuentre.
    """
    types = {did: (d.get("device_type") or d.get("type")) for did, d in devices.items()}
    rtts: Dict[str, int] = {}
    for _, c in connections.items():
        a = c.get("device_a_id") or c.get("device_a")
        b = c.get("device_b_id") or c.get("device_b")
        if not a or not b:
            continue
        dist_px = float(c.get("distance", 0.0))
        # OLT<->ONU en cualquier orden
        if types.get(a) == "OLT" and types.get(b) == "ONU":
            onu = b
        elif types.get(a) == "ONU" and types.get(b) == "OLT":
            onu = a
        else:
            continue
        if onu not in rtts:
            rtts[onu] = rtt_ns_from_px(dist_px, params)
    return rtts
