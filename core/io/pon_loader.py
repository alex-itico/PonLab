import json
from typing import Dict, Any, Tuple
from core.phy.rtt import PhyParams

def load_pon(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_devices_connections(pon: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    devices = pon.get("devices_data", {}) or pon.get("devices", {})
    connections = pon.get("connections_data", {}) or pon.get("connections", {})
    return devices, connections

def get_phy_params(pon: Dict[str, Any]) -> PhyParams:
    phy = pon.get("phy", {}) or {}
    return PhyParams(
        scale_m_per_px=float(phy.get("scale_m_per_px", 0.1)),
        n_fiber=float(phy.get("n_fiber", 1.468)),
    )
