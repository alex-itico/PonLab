"""
Constants
Constantes de la aplicación y valores de configuración
"""

# Constantes de la aplicación
APP_NAME = "PonLab - Simulador de Redes Ópticas Pasivas"
APP_VERSION = "2.0.0"

# Constantes de UI
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
DEFAULT_SIDEBAR_WIDTH = 320  # Aumentado de 250 a 280 para mejor espaciado

# Constantes de Canvas
DEFAULT_CANVAS_WIDTH = 2000
DEFAULT_CANVAS_HEIGHT = 1500
GRID_SIZE = 20

# Constantes de Nodo
DEFAULT_NODE_WIDTH = 100
DEFAULT_NODE_HEIGHT = 50
MIN_NODE_SIZE = 20
MAX_NODE_SIZE = 200

# Constantes de Línea
DEFAULT_LINE_WIDTH = 2
MIN_LINE_WIDTH = 1
MAX_LINE_WIDTH = 10

# Constantes de dispositivos
OLT_DEFAULT_NAME = "OLT"
ONU_DEFAULT_NAME = "ONU"
MAX_ONUS_PER_OLT = 64

# Algoritmos DBA disponibles
AVAILABLE_DBA_ALGORITHMS = ["FCFS", "Priority", "RL-DBA", "SDN", "Smart-RL", "Smart-RL-SDN"]
DBA_ALGORITHM_DESCRIPTIONS = {
    "FCFS": "First Come First Served - Algoritmo básico FIFO",
    "Priority": "Priority-based - Basado en prioridades",
    "RL-DBA": "Reinforcement Learning DBA - Algoritmo RL clásico", 
    "SDN": "Software Defined Network - Control centralizado con SDN",
    "Smart-RL": "Smart Reinforcement Learning - RL inteligente interno",
    "Smart-RL-SDN": "Smart RL + SDN - Híbrido de RL inteligente y SDN"
}

# Colores
PRIMARY_COLOR = "#2196F3"
SECONDARY_COLOR = "#FF9800"
SUCCESS_COLOR = "#4CAF50"
ERROR_COLOR = "#F44336"
WARNING_COLOR = "#FF9800"
