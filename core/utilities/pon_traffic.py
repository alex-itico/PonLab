"""
Realistic traffic scenario configuration for PON simulation
Integrado de netPONPy para PonLab
"""

def get_traffic_scenario(scenario_name: str) -> dict:
    """
    Retorna configuración de tráfico para el escenario especificado
    
    Args:
        scenario_name: Nombre del escenario
        
    Returns:
        dict: Configuración del escenario con parámetros de tráfico
    """
    
    scenarios = {
        "residential_light": {
            "description": "Uso residencial ligero - navegación básica",
            "traffic_probs_range": {
                "highest": (0.1, 0.3),   # Tráfico crítico ocasional
                "high": (0.2, 0.4),      # Aplicaciones importantes
                "medium": (0.3, 0.6),    # Navegación web
                "low": (0.4, 0.7),       # Tráfico de fondo
                "lowest": (0.1, 0.3)     # Telemetría/IoT
            },
            "traffic_sizes_mb": {
                "highest": (0.050, 0.100),  # 50-100KB: VoIP, control
                "high": (0.020, 0.050),     # 20-50KB: aplicaciones importantes
                "medium": (0.010, 0.025),   # 10-25KB: navegación web
                "low": (0.005, 0.015),      # 5-15KB: background apps
                "lowest": (0.001, 0.005)    # 1-5KB: IoT/telemetría
            },
            "sla_range": (50, 150),          # Mbps
            "target_utilization": 0.5,       # 50% del SLA
            "request_size_mb": 0.012,        # 12KB promedio por solicitud
            "inter_arrival_ms_target": 25    # ~40 req/s
        },
        
        "residential_medium": {
            "description": "Uso residencial normal - streaming HD, videollamadas",
            "traffic_probs_range": {
                "highest": (0.2, 0.5),   # Streaming HD ocasional
                "high": (0.3, 0.6),      # Videollamadas
                "medium": (0.4, 0.7),    # Navegación web
                "low": (0.3, 0.6),       # Apps de fondo
                "lowest": (0.1, 0.3)     # IoT/Actualizaciones
            },
            "traffic_sizes_mb": {
                "highest": (0.100, 0.200),  # 100-200KB: streaming HD
                "high": (0.040, 0.080),     # 40-80KB: videollamadas
                "medium": (0.015, 0.030),   # 15-30KB: navegación web
                "low": (0.008, 0.020),      # 8-20KB: apps de fondo
                "lowest": (0.002, 0.008)    # 2-8KB: IoT/updates
            },
            "sla_range": (100, 300),         # Mbps
            "target_utilization": 0.6,       # 60% del SLA
            "request_size_mb": 0.015,        # 15KB promedio por solicitud
            "inter_arrival_ms_target": 15   # ~67 req/s
        },
        
        "residential_heavy": {
            "description": "Uso residencial intensivo - streaming 4K, gaming",
            "traffic_probs_range": {
                "highest": (0.4, 0.7),   # Streaming 4K
                "high": (0.5, 0.8),      # Gaming/Video
                "medium": (0.6, 0.9),    # Múltiples streams
                "low": (0.3, 0.6),       # Tráfico de fondo
                "lowest": (0.2, 0.4)     # IoT
            },
            "traffic_sizes_mb": {
                "highest": (0.200, 0.500),  # 200-500KB: streaming 4K
                "high": (0.080, 0.150),     # 80-150KB: gaming/video
                "medium": (0.025, 0.050),   # 25-50KB: múltiples streams
                "low": (0.010, 0.025),      # 10-25KB: background
                "lowest": (0.003, 0.010)    # 3-10KB: IoT
            },
            "sla_range": (200, 500),         # Mbps
            "target_utilization": 0.7,       # 70% del SLA
            "request_size_mb": 0.018,        # 18KB promedio por solicitud
            "inter_arrival_ms_target": 10   # ~100 req/s
        },
        
        "enterprise": {
            "description": "Uso empresarial - aplicaciones críticas",
            "traffic_probs_range": {
                "highest": (0.6, 0.9),   # Aplicaciones críticas
                "high": (0.7, 0.9),      # VoIP/Videoconferencia
                "medium": (0.5, 0.8),    # Aplicaciones de negocio
                "low": (0.4, 0.7),       # Respaldos
                "lowest": (0.3, 0.5)     # Monitoreo
            },
            "traffic_sizes_mb": {
                "highest": (0.080, 0.150),  # 80-150KB: aplicaciones críticas
                "high": (0.030, 0.080),     # 30-80KB: VoIP/videoconf
                "medium": (0.020, 0.040),   # 20-40KB: apps de negocio
                "low": (0.050, 0.200),      # 50-200KB: respaldos
                "lowest": (0.001, 0.005)    # 1-5KB: monitoreo/telemetría
            },
            "sla_range": (300, 800),         # Mbps
            "target_utilization": 0.8,       # 80% del SLA
            "request_size_mb": 0.020,        # 20KB promedio por solicitud
            "inter_arrival_ms_target": 8    # ~125 req/s
        }
    }
    
    if scenario_name not in scenarios:
        print(f"Escenario '{scenario_name}' no encontrado. Usando 'residential_medium'")
        scenario_name = "residential_medium"
    
    return scenarios[scenario_name]

def calculate_realistic_lambda(sla_mbps: float, scenario_config: dict) -> float:
    """
    Calcula una tasa de llegada realista (λ) basada en el escenario

    Args:
        sla_mbps: SLA en Mbps
        scenario_config: Configuración del escenario

    Returns:
        float: Tasa de llegadas en solicitudes/segundo
    """

    # Calcular throughput objetivo en Mbps
    target_throughput_mbps = sla_mbps * scenario_config["target_utilization"]

    # Calcular tamaño promedio de paquete considerando probabilidades
    # Cada tipo de tráfico tiene una probabilidad y un tamaño
    avg_packet_size_mb = 0.0
    total_prob = 0.0

    for traffic_type in scenario_config["traffic_probs_range"].keys():
        # Probabilidad promedio para este tipo
        prob_range = scenario_config["traffic_probs_range"][traffic_type]
        avg_prob = (prob_range[0] + prob_range[1]) / 2

        # Tamaño promedio para este tipo
        if traffic_type in scenario_config["traffic_sizes_mb"]:
            size_range = scenario_config["traffic_sizes_mb"][traffic_type]
            avg_size = (size_range[0] + size_range[1]) / 2

            # Contribución ponderada por probabilidad
            avg_packet_size_mb += avg_prob * avg_size
            total_prob += avg_prob

    # Normalizar por la probabilidad total (ya que las probabilidades no suman 1)
    if total_prob > 0:
        avg_packet_size_mb = avg_packet_size_mb / total_prob

    # Convertir throughput de Mbps a MB/s
    target_throughput_mb_per_sec = target_throughput_mbps / 8.0

    # Calcular lambda: λ = Throughput(MB/s) / Tamaño_promedio(MB)
    if avg_packet_size_mb > 0:
        lambda_rate = target_throughput_mb_per_sec / avg_packet_size_mb
    else:
        lambda_rate = 10.0  # Fallback

    return max(lambda_rate, 5.0)  # Mínimo 5 solicitudes/segundo

def get_available_scenarios() -> list[str]:
    """Retorna lista de escenarios disponibles"""
    return ["residential_light", "residential_medium", "residential_heavy", "enterprise"]

def print_scenario_info(scenario_name: str):
    """Imprime información detallada del escenario"""
    config = get_traffic_scenario(scenario_name)
    
    print(f"Escenario: {scenario_name}")
    print(f"   {config['description']}")
    print(f"   - Rango SLA: {config['sla_range'][0]}-{config['sla_range'][1]} Mbps")
    print(f"   - Utilización objetivo: {config['target_utilization']*100:.0f}%")
    print(f"   - Tamaño de solicitud: {config['request_size_mb']*1024:.0f} KB")
    print(f"   - Tiempo entre llegadas objetivo: ~{config['inter_arrival_ms_target']} ms")
    print(f"   - Probabilidades de tráfico:")
    for traffic_type, (min_p, max_p) in config['traffic_probs_range'].items():
        print(f"     * {traffic_type}: {min_p:.1f}-{max_p:.1f}")

def get_scenario_summary() -> dict:
    """Obtener resumen de todos los escenarios disponibles"""
    scenarios = get_available_scenarios()
    summary = {}
    
    for scenario_name in scenarios:
        config = get_traffic_scenario(scenario_name)
        summary[scenario_name] = {
            'description': config['description'],
            'sla_range': config['sla_range'],
            'target_utilization': config['target_utilization'],
            'typical_throughput_range': (
                config['sla_range'][0] * config['target_utilization'],
                config['sla_range'][1] * config['target_utilization']
            )
        }
    
    return summary