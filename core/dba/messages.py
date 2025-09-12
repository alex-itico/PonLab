from dataclasses import dataclass
from typing import Dict

@dataclass
class Report:
    #Reporte de una ONU hacia el OLT sobre su estado de colas.
    onu_id: str #Identificador único de la ONU (coincide con Device.id).
    queues_bytes: Dict[str, int] #Bytes acumulados por clase de servicio (p. ej., {"EF":0,"AF":1200,"BE":18000}).
    timestamp_ns: int #Instante del reporte en nanosegundos (ns).


@dataclass
class Grant:
    #Concesión del OLT a una ONU para transmitir.
    onu_id: str #ONU que recibe la asignación.
    size_bytes: int #Bytes útiles concedidos
    start_time_ns: int #Inicio del slot (ns) en el upstream.
    duration_ns: int #Duración total del slot (ns), incluyendo guard time.


@dataclass
class CycleTiming:
    #Parámetros físicos y de temporización compartidos por simulador y DBA.
    guard_time_ns: int = 1000 #Tiempo de guarda entre transmisiones (ns).
    line_rate_bps: int = 10_000_000_000 #Tasa de línea en bits por segundo (bps), Ejemplo 10_000_000_000 -> 10 Gbps.
    scale_m_per_px: float = 0.1 #Factor de conversión de pixeles (canvas) a metros (para distancias/RTT).
    n_fiber: float = 1.468 #Índice de refracción efectivo de la fibra (para estimar RTT ≈ 2*d/(c/n)).


def bytes_to_ns(size_bytes: int, line_rate_bps: int) -> int:
    """
    Convierte un tamaño en bytes al tiempo de transmisión (ns) según la tasa de línea.
    NO incluye guard time.
    Fórmula: t_ns = (bytes * 8 / bps) * 1e9
    """
    # Usamos int() para obtener un tiempo entero en ns (truncamiento conservador).
    return int((size_bytes * 8 * 1_000_000_000) / line_rate_bps) #Conversión de bytes a ns
