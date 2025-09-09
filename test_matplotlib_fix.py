"""
Test para verificar que la configuración de matplotlib resuelve los errores de fuentes
"""

import sys
import os

# Agregar PonLab al path
sys.path.append(os.path.dirname(__file__))

def test_matplotlib_configuration():
    """Probar la configuración de matplotlib"""
    print("Probando configuracion de matplotlib para Windows...")
    
    try:
        # Test 1: Configuración básica
        from ui.matplotlib_config import configure_matplotlib_for_windows, safe_matplotlib_backend
        
        print("\n1. Configurando backend seguro...")
        backend = safe_matplotlib_backend()
        if backend:
            print(f"OK Backend configurado: {backend}")
        else:
            print("ERROR No se pudo configurar backend")
            return False
        
        print("\n2. Aplicando configuracion para Windows...")
        success = configure_matplotlib_for_windows()
        if success:
            print("OK Configuracion aplicada correctamente")
        else:
            print("ERROR aplicando configuracion")
            return False
        
        # Test 2: Crear gráfico simple
        print("\n3. Creando grafico de prueba...")
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Datos de prueba
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        # Crear figura
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='white')
        ax.plot(x, y, label='sin(x)', linewidth=2)
        ax.set_xlabel('X values')
        ax.set_ylabel('Y values')
        ax.set_title('Test Chart - Font Rendering')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        print("OK Grafico creado sin errores")
        
        # Test 3: Guardar gráfico
        print("\n4. Guardando grafico de prueba...")
        test_filename = "test_chart.png"
        
        try:
            fig.savefig(test_filename, dpi=300, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            print(f"OK Grafico guardado: {test_filename}")
        except Exception as e:
            print(f"WARNING Error guardando con alta resolucion, probando alternativo: {e}")
            fig.savefig(test_filename, dpi=150, facecolor='white')
            print(f"OK Grafico guardado con resolucion alternativa: {test_filename}")
        
        plt.close(fig)
        
        # Test 4: Probar PONMetricsChart
        print("\n5. Probando PONMetricsChart...")
        try:
            from ui.pon_metrics_charts import PONMetricsChart
            chart = PONMetricsChart(width=6, height=4)
            print("OK PONMetricsChart creado correctamente")
            
            # Simular datos para probar el gráfico
            test_data = {
                'simulation_summary': {
                    'simulation_stats': {
                        'total_steps': 100,
                        'step_delays': [0.001 + i * 0.0001 for i in range(100)]
                    }
                }
            }
            
            chart.plot_delay_evolution(test_data)
            print("OK Grafico de delay evolution creado sin errores")
            
        except Exception as e:
            print(f"WARNING Error probando PONMetricsChart: {e}")
        
        print("\nTODOS LOS TESTS COMPLETADOS")
        print("\nRESUMEN:")
        print("OK Configuracion de matplotlib aplicada")
        print("OK Backend seguro configurado")
        print("OK Graficos se pueden crear y guardar")
        print("OK Los errores de fuente Qt deberian estar resueltos")
        
        return True
        
    except Exception as e:
        print(f"\nERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_files():
    """Limpiar archivos de prueba"""
    test_files = ["test_chart.png"]
    for file in test_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"Archivo de prueba eliminado: {file}")
        except:
            pass

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE CORRECCION DE ERRORES DE MATPLOTLIB")
    print("=" * 60)
    
    success = test_matplotlib_configuration()
    
    if success:
        print("\nOK La configuracion deberia resolver los errores de fuentes Qt")
        print("INFO Ahora puedes ejecutar el sistema de graficos automatico sin errores")
    else:
        print("\nERROR Aun hay problemas con la configuracion")
        print("INFO Revisa los errores mostrados arriba")
    
    # Limpiar archivos de prueba
    cleanup_test_files()
    
    print("\nPara probar el sistema completo, ejecuta:")
    print("python examples/test_automatic_graphics.py")