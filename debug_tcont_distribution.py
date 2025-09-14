"""
Diagnóstico de distribución de T-CONTs
Verifica si la generación de tráfico está sesgada hacia ciertos T-CONTs
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.pon_event_onu import HybridONU
from core.pon_traffic import get_traffic_scenario
import collections
import random

def test_tcont_distribution():
    """Probar distribución de T-CONTs en generación de paquetes"""
    
    # Configurar escenario
    scenario = get_traffic_scenario("residential_medium")
    onu = HybridONU("test_onu", lambda_rate=10.0, scenario_config=scenario)
    
    print("=== CONFIGURACIÓN DE ESCENARIO ===")
    print("Escenario: residential_medium")
    print(f"Probabilidades por T-CONT:")
    for tcont, (min_prob, max_prob) in scenario['traffic_probs_range'].items():
        print(f"  {tcont}: {min_prob:.1f} - {max_prob:.1f}")
    print()
    
    # Generar muchos paquetes y contar distribución
    tcont_counts = collections.Counter()
    total_packets = 10000
    
    print(f"=== GENERANDO {total_packets} PAQUETES ===")
    
    # Establecer semilla para reproducibilidad
    random.seed(42)
    
    for i in range(total_packets):
        packet = onu._create_packet(float(i))
        tcont_counts[packet.tcont_type] += 1
    
    print("Distribución observada:")
    for tcont in ['highest', 'high', 'medium', 'low', 'lowest']:
        count = tcont_counts[tcont]
        percentage = (count / total_packets) * 100
        print(f"  {tcont}: {count} paquetes ({percentage:.1f}%)")
    
    print()
    
    # Probar el método de selección directamente
    print("=== PROBANDO MÉTODO _select_tcont_type DIRECTAMENTE ===")
    
    random.seed(42)
    direct_counts = collections.Counter()
    
    for i in range(total_packets):
        tcont = onu._select_tcont_type()
        direct_counts[tcont] += 1
    
    print("Distribución del método _select_tcont_type:")
    for tcont in ['highest', 'high', 'medium', 'low', 'lowest']:
        count = direct_counts[tcont]
        percentage = (count / total_packets) * 100
        print(f"  {tcont}: {count} selecciones ({percentage:.1f}%)")
    
    print()
    
    # Analizar el algoritmo de selección
    print("=== ANÁLISIS DEL ALGORITMO DE SELECCIÓN ===")
    random.seed(42)
    
    # Tomar una muestra del proceso de selección
    for i in range(5):
        print(f"\nMuestra {i+1}:")
        
        # Generar probabilidades actuales basadas en rangos
        current_probs = {}
        for tcont, (min_prob, max_prob) in onu.traffic_distribution.items():
            prob = random.uniform(min_prob, max_prob)
            current_probs[tcont] = prob
            print(f"  {tcont}: prob = {prob:.3f}")
        
        total_weight = sum(current_probs.values())
        print(f"  Total weight: {total_weight:.3f}")
        
        random_value = random.uniform(0, total_weight)
        print(f"  Random value: {random_value:.3f}")
        
        cumulative = 0
        selected = None
        for tcont, prob in current_probs.items():
            cumulative += prob
            print(f"  {tcont}: cumulative = {cumulative:.3f}")
            if random_value <= cumulative and selected is None:
                selected = tcont
                print(f"  -> SELECTED: {tcont}")
        
        if selected is None:
            selected = 'medium'  # fallback
            print(f"  -> FALLBACK: {selected}")
    
    return tcont_counts, direct_counts

if __name__ == "__main__":
    test_tcont_distribution()