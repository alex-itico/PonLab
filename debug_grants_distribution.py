"""
Diagnóstico de distribución de grants por T-CONT
Verifica cómo el OLT distribuye los grants entre los diferentes T-CONTs
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.pon_adapter import PONAdapter
import collections
import time

def test_grants_distribution():
    """Probar distribución de grants en una simulación real"""
    
    # Crear adapter y configurar
    adapter = PONAdapter()
    adapter.set_simulation_mode('events')
    
    # Configurar simulación con tráfico diverso
    success, message = adapter.initialize_simulation(num_onus=2)
    print(f"Inicialización: {success} - {message}")
    
    if not success:
        return
    
    # Crear un callback para capturar eventos
    grant_data = []
    transmission_data = []
    
    def capture_callback(event_type, data):
        if event_type == "update" and 'event_type' in data:
            if data['event_type'] == 'grant_start':
                grant_data.append(data)
            elif data['event_type'] == 'transmission_complete':
                transmission_data.append(data)
    
    print("\n=== EJECUTANDO SIMULACIÓN CORTA ===")
    
    # Ejecutar simulación muy corta para capturar datos
    success, results = adapter.run_simulation(duration_seconds=0.02, callback=capture_callback)
    
    if not success:
        print("Error en simulación")
        return
    
    print(f"Simulación completada. Eventos capturados:")
    print(f"  Grants: {len(grant_data)}")
    print(f"  Transmissions: {len(transmission_data)}")
    
    # Analizar grants por T-CONT
    grant_by_tcont = collections.defaultdict(list)
    for grant in grant_data:
        if 'data' in grant and 'tcont_id' in grant['data']:
            tcont = grant['data']['tcont_id']
            grant_bytes = grant['data'].get('grant_bytes', 0)
            grant_by_tcont[tcont].append(grant_bytes)
    
    print(f"\n=== ANÁLISIS DE GRANTS POR T-CONT ===")
    if grant_by_tcont:
        for tcont, grants in grant_by_tcont.items():
            total_bytes = sum(grants)
            avg_bytes = total_bytes / len(grants) if grants else 0
            print(f"  {tcont}: {len(grants)} grants, {total_bytes:,} bytes totales, {avg_bytes:.1f} bytes promedio")
    else:
        print("  No se capturaron datos de grants específicos por T-CONT")
    
    # Analizar transmisiones por T-CONT
    transmission_by_tcont = collections.defaultdict(list)
    for transmission in transmission_data:
        if 'data' in transmission and 'tcont_id' in transmission['data']:
            tcont = transmission['data']['tcont_id']
            transmitted_bytes = transmission['data'].get('transmitted_bytes', 0)
            transmission_by_tcont[tcont].append(transmitted_bytes)
    
    print(f"\n=== ANÁLISIS DE TRANSMISIONES POR T-CONT ===")
    if transmission_by_tcont:
        for tcont, transmissions in transmission_by_tcont.items():
            total_bytes = sum(transmissions)
            avg_bytes = total_bytes / len(transmissions) if transmissions else 0
            print(f"  {tcont}: {len(transmissions)} transmisiones, {total_bytes:,} bytes totales, {avg_bytes:.1f} bytes promedio")
    else:
        print("  No se capturaron datos de transmisiones específicos por T-CONT")
    
    # Obtener estadísticas del simulador
    print(f"\n=== ESTADÍSTICAS DEL SIMULADOR ===")
    summary = adapter.get_simulation_summary()
    
    if 'simulation_summary' in summary:
        sim_stats = summary['simulation_summary']
        
        if 'simulation_stats' in sim_stats:
            stats = sim_stats['simulation_stats']
            print(f"  Total requests: {stats.get('total_requests', 0)}")
            print(f"  Successful requests: {stats.get('successful_requests', 0)}")
        
        if 'performance_metrics' in sim_stats:
            perf = sim_stats['performance_metrics']
            print(f"  Total transmitted: {perf.get('total_transmitted', 0)} MB")
            print(f"  Network utilization: {perf.get('network_utilization', 0):.1f}%")
    
    # Obtener estado del simulador para ver distribución de buffers
    print(f"\n=== ESTADO DE BUFFERS POR ONU ===")
    state = adapter.get_current_state()
    if 'buffer_levels' in state:
        for i, buffer_info in enumerate(state['buffer_levels']):
            print(f"  ONU {i}:")
            print(f"    Utilización total: {buffer_info.get('utilization_percent', 0):.1f}%")
            print(f"    Usado: {buffer_info.get('used_mb', 0):.3f} MB")
            print(f"    Capacidad: {buffer_info.get('capacity_mb', 0):.3f} MB")
    
    return grant_data, transmission_data

if __name__ == "__main__":
    test_grants_distribution()