"""
Diagnóstico con simulación más larga para capturar diversidad de tráfico
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.pon_adapter import PONAdapter
from core.pon_simulator import PONSimulator
from core.pon_event_onu import HybridONU
from core.pon_event_olt import HybridOLT
from core.pon_traffic import get_traffic_scenario, calculate_realistic_lambda
from core.pon_dba import FCFSDBAAlgorithm
import collections
import time

def test_longer_simulation():
    """Probar con simulación más larga para ver diversidad de T-CONTs"""
    
    print("=== SIMULACIÓN DIRECTA CON COMPONENTES ===")
    
    # Configurar componentes directamente
    scenario = get_traffic_scenario("residential_medium")
    
    # Crear ONUs con diferentes tasas para ver diversidad
    onus = {}
    for i in range(2):
        onu_id = str(i)
        sla = 100.0 + i * 50.0  # 100, 150 Mbps
        lambda_rate = calculate_realistic_lambda(sla, scenario)
        lambda_rate = min(lambda_rate, 25.0)  # Limitar para control
        
        onus[onu_id] = HybridONU(onu_id, lambda_rate, scenario)
        print(f"ONU {onu_id}: lambda_rate = {lambda_rate:.2f} paq/s")
    
    # Crear OLT
    dba_algorithm = FCFSDBAAlgorithm()
    olt = HybridOLT(onus, dba_algorithm, 1024.0)
    
    # Crear simulador
    simulator = PONSimulator(simulation_mode="events")
    simulator.onus = onus
    simulator.olt = olt
    
    print(f"\n=== EJECUTANDO SIMULACIÓN DE 0.2 SEGUNDOS ===")
    
    # Ejecutar simulación más larga
    success, results = simulator.run_event_simulation(0.2)  # 200ms
    
    if not success:
        print("Error en simulación")
        return
    
    print(f"Simulación completada exitosamente")
    print(f"Eventos procesados: {simulator.events_processed}")
    print(f"Tiempo simulado: {simulator.simulation_time:.6f}s")
    
    # Analizar métricas recolectadas
    print(f"\n=== MÉTRICAS RECOLECTADAS ===")
    print(f"Delays: {len(simulator.metrics['delays'])}")
    print(f"Throughputs: {len(simulator.metrics['throughputs'])}")
    print(f"Total transmitted: {simulator.metrics['total_transmitted']:.6f} MB")
    print(f"Total requests: {simulator.metrics['total_requests']}")
    print(f"Successful transmissions: {simulator.metrics['successful_transmissions']}")
    
    # Analizar contenido de los paquetes por T-CONT
    tcont_analysis = collections.defaultdict(lambda: {'count': 0, 'bytes': 0})
    
    # Buscar en las métricas de throughput, que contienen información por ONU
    for throughput_entry in simulator.metrics['throughputs']:
        onu_id = throughput_entry.get('onu_id')
        throughput = throughput_entry.get('throughput', 0)
        
        # Obtener información de la ONU correspondiente
        if onu_id in onus:
            # Necesitamos una forma de rastrear qué T-CONT se está usando
            # Vamos a examinar las colas de las ONUs
            pass
    
    print(f"\n=== ANÁLISIS DE COLAS POR ONU ===")
    
    for onu_id, onu in onus.items():
        print(f"\nONU {onu_id}:")
        print(f"  Paquetes generados: {onu.total_packets_generated}")
        print(f"  Bytes generados: {onu.total_bytes_generated:,}")
        print(f"  Stats: {onu.stats}")
        
        print(f"  Colas por T-CONT:")
        for tcont_id, queue in onu.queues.items():
            status = queue.get_status()
            print(f"    {tcont_id}: {status['queue_packets']} paquetes, {status['queue_bytes']:,} bytes")
            print(f"              dropped: {status['dropped_packets']}, received: {queue.total_packets_received}")
    
    # Obtener estadísticas del OLT
    print(f"\n=== ESTADÍSTICAS DEL OLT ===")
    olt_stats = olt.get_olt_statistics()
    olt_data = olt_stats['olt_stats']
    
    print(f"Ciclos ejecutados: {olt_data['cycles_executed']}")
    print(f"Reports recolectados: {olt_data['reports_collected']}")
    print(f"Grants asignados: {olt_data['grants_assigned']}")
    print(f"Total grants bytes: {olt_data['total_grants_bytes']:,}")
    print(f"Transmisiones exitosas: {olt_data['successful_transmissions']}")
    print(f"Transmisiones fallidas: {olt_data['failed_transmissions']}")
    print(f"Utilización promedio: {olt_stats.get('average_utilization', 0):.2f}%")
    
    # Examinar log de transmisiones
    transmission_log = olt_stats.get('transmission_log', [])
    print(f"\nTransmisiones registradas: {len(transmission_log)}")
    
    if transmission_log:
        tcont_transmissions = collections.defaultdict(lambda: {'count': 0, 'bytes': 0})
        
        for entry in transmission_log[:10]:  # Mostrar primeras 10
            onu_id = entry.get('onu_id', 'unknown')
            tcont_id = entry.get('tcont_id', 'unknown') 
            data_size_mb = entry.get('data_size_mb', 0)
            bytes_transmitted = int(data_size_mb * 1024 * 1024) if data_size_mb else 0
            
            tcont_transmissions[tcont_id]['count'] += 1
            tcont_transmissions[tcont_id]['bytes'] += bytes_transmitted
            
            print(f"  {onu_id}:{tcont_id} -> {bytes_transmitted:,} bytes (from {data_size_mb:.6f} MB)")
        
        print(f"\n=== RESUMEN POR T-CONT ===")
        for tcont, data in tcont_transmissions.items():
            print(f"  {tcont}: {data['count']} transmisiones, {data['bytes']:,} bytes totales")

if __name__ == "__main__":
    test_longer_simulation()