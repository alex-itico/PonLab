"""
Prueba de visualización de T-CONTs corregida
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.pon_adapter import PONAdapter
import json

def test_tcont_visualization():
    """Probar que la visualización ahora detecta todos los T-CONTs"""
    
    print("=== PRUEBA DE VISUALIZACIÓN DE T-CONTs ===")
    
    # Configurar simulación
    adapter = PONAdapter()
    adapter.set_simulation_mode('events')
    
    success, message = adapter.initialize_simulation(num_onus=2)
    print(f"Inicialización: {success} - {message}")
    
    if not success:
        return
    
    # Ejecutar simulación más larga para obtener diversidad
    print("\n=== EJECUTANDO SIMULACIÓN DE 0.5 SEGUNDOS ===")
    success, results = adapter.run_simulation(duration_seconds=0.5)
    
    if not success:
        print("Error en simulación")
        return
    
    print("Simulación completada exitosamente")
    
    # Obtener resumen completo
    summary = adapter.get_simulation_summary()
    
    # Analizar datos de throughput
    print("\n=== ANÁLISIS DE DATOS DE THROUGHPUT ===")
    
    episode_metrics = summary.get('simulation_summary', {}).get('episode_metrics', {})
    throughputs = episode_metrics.get('throughputs', [])
    
    print(f"Total de entradas de throughput: {len(throughputs)}")
    
    if len(throughputs) > 0:
        # Mostrar primeras 10 entradas para verificar estructura
        print("\nPrimeras 10 entradas de throughput:")
        for i, entry in enumerate(throughputs[:10]):
            tcont_id = entry.get('tcont_id', 'NO ENCONTRADO')
            onu_id = entry.get('onu_id', 'N/A')
            throughput = entry.get('throughput', 0)
            timestamp = entry.get('timestamp', 0)
            print(f"  {i+1}: ONU {onu_id}, T-CONT {tcont_id}, Throughput: {throughput:.6f}, Time: {timestamp:.6f}")
    
    # Contar por T-CONT para verificar distribución
    print("\n=== DISTRIBUCIÓN POR T-CONT ===")
    tcont_counts = {}
    tcont_throughputs = {}
    
    for entry in throughputs:
        tcont_id = entry.get('tcont_id', 'unknown')
        throughput = entry.get('throughput', 0)
        
        if tcont_id not in tcont_counts:
            tcont_counts[tcont_id] = 0
            tcont_throughputs[tcont_id] = 0
        
        tcont_counts[tcont_id] += 1
        tcont_throughputs[tcont_id] += throughput
    
    total_entries = sum(tcont_counts.values())
    
    print(f"Total de transmisiones analizadas: {total_entries}")
    print("Distribución por T-CONT:")
    
    for tcont in ['highest', 'high', 'medium', 'low', 'lowest']:
        count = tcont_counts.get(tcont, 0)
        throughput = tcont_throughputs.get(tcont, 0)
        percentage = (count / total_entries) * 100 if total_entries > 0 else 0
        
        print(f"  {tcont:8}: {count:3} transmisiones ({percentage:5.1f}%), {throughput:.6f} throughput total")
    
    # Verificar entradas con tcont_id desconocido
    unknown_count = tcont_counts.get('unknown', 0) + tcont_counts.get('NO ENCONTRADO', 0)
    if unknown_count > 0:
        print(f"\n⚠️  ATENCIÓN: {unknown_count} entradas sin tcont_id válido")
    else:
        print(f"\n✅  ÉXITO: Todas las entradas tienen tcont_id válido")
    
    # Simular el procesamiento del gráfico
    print(f"\n=== SIMULANDO PROCESAMIENTO DEL GRÁFICO ===")
    
    # Código similar al que usa pon_metrics_charts.py
    tcont_counts_viz = {'highest': 0, 'high': 0, 'medium': 0, 'low': 0, 'lowest': 0}
    
    for throughput_entry in throughputs:
        tcont_type = throughput_entry.get('tcont_id', 'medium').lower()
        if tcont_type in tcont_counts_viz:
            tcont_counts_viz[tcont_type] += 1
    
    total_for_viz = sum(tcont_counts_viz.values())
    
    print(f"Procesamiento para visualización:")
    print(f"Total para gráfico: {total_for_viz}")
    
    if total_for_viz > 0:
        for tcont, count in tcont_counts_viz.items():
            percentage = (count / total_for_viz) * 100
            print(f"  {tcont:8}: {count:3} ({percentage:5.1f}%)")
        
        # Verificar cuántos tipos aparecerán en el gráfico
        visible_types = [tcont for tcont, count in tcont_counts_viz.items() if count > 0]
        print(f"\nTipos de T-CONT que aparecerán en gráfico: {visible_types}")
        
        if len(visible_types) > 1:
            print("✅  ÉXITO: Se detectan múltiples tipos de T-CONT")
        else:
            print("❌  PROBLEMA: Solo se detecta un tipo de T-CONT")
    
    return summary, throughputs

if __name__ == "__main__":
    test_tcont_visualization()