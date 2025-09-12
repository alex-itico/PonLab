from typing import List, Dict
from .messages import Report, Grant, CycleTiming

class OltDbaEngine:
    """
    Clase base para cualquier motor DBA.
    Los algoritmos concretos deben heredar de esta y redefinir compute_grants.
    """
    def __init__(self, timing: CycleTiming, params: Dict = None):
        self.timing = timing
        self.params = params or {}

    def compute_grants(self, reports: List[Report], now_ns: int) -> List[Grant]:
        """
        Debe recibir una lista de Reports y devolver una lista de Grants.
        - reports: estado actual de cada ONU.
        - now_ns: instante actual del simulador.
        """
        raise NotImplementedError("Debe implementarse en la subclase.")


# --- Registro de algoritmos ---
_REGISTRY = {}

def register(name: str):
    """
    Decorador para registrar un algoritmo bajo un nombre.
    Ejemplo:
        @register("test")
        class TestEngine(OltDbaEngine): ...
    """
    def decorator(cls):
        _REGISTRY[name.lower()] = cls
        return cls
    return decorator

def build_engine(name: str, timing: CycleTiming, params: Dict = None) -> OltDbaEngine:
    """
    Construir un motor DBA a partir del nombre y parámetros.
    """
    cls = _REGISTRY.get(name.lower())
    if not cls:
        raise ValueError(f"Algoritmo DBA desconocido: {name}")
    return cls(timing, params)
