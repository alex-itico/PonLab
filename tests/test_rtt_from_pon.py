# Ejecuta: python -m tests.test_rtt_from_pon
from core.io.pon_loader import load_pon, extract_devices_connections, get_phy_params
from core.phy.rtt_assign import build_onu_rtts

def main():
    PON_PATH = "C:/Users/Varfyo/Desktop/PONLAB/mi_topologia.pon"  # ajusta ruta si corresponde
    pon = load_pon(PON_PATH)
    devices, connections = extract_devices_connections(pon)
    phy = get_phy_params(pon)

    rtts = build_onu_rtts(devices, connections, phy)
    print("RTTs por ONU (ns):", rtts)

    # Asserts mínimos de integración:
    assert len(rtts) > 0, "No se calcularon RTTs. ¿Hay enlaces OLT<->ONU?"
    # Valores sanos: RTT debe ser >0 y en rango "pequeño" (decenas a cientos de ns para decenas de metros)
    for onu, rtt in rtts.items():
        assert rtt > 0 and rtt < 5_000_000, f"RTT fuera de rango para {onu}: {rtt} ns"

    print("RTT from .pon OK ✅")

if __name__ == "__main__":
    main()
