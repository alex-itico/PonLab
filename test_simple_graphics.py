"""
Test simple del sistema automatico de graficos
Version sin emojis para evitar problemas de encoding
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer

# Agregar PonLab al path
sys.path.append(os.path.dirname(__file__))

from ui.integrated_pon_test_panel import IntegratedPONTestPanel


class SimpleGraphicsTestWindow(QMainWindow):
    """Ventana de prueba simple para el sistema automatico de graficos"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Sistema Automatico de Graficos PON")
        self.setGeometry(100, 100, 1200, 800)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Panel de prueba integrado
        self.test_panel = IntegratedPONTestPanel()
        layout.addWidget(self.test_panel)
        
        # Timer para ejecutar simulacion automatica
        self.demo_timer = QTimer()
        self.demo_timer.singleShot(2000, self.run_demo_simulation)
        
    def run_demo_simulation(self):
        """Ejecutar simulacion de demostracion automatica"""
        print("Iniciando simulacion con guardado automatico de graficos...")
        
        # Configurar simulacion
        self.test_panel.onu_spinbox.setValue(3)  # 3 ONUs para demo rapida
        self.test_panel.algorithm_combo.setCurrentText("FCFS")
        self.test_panel.steps_spinbox.setValue(200)  # Simulacion corta
        
        # Habilitar todas las opciones automaticas
        self.test_panel.auto_charts_checkbox.setChecked(True)
        self.test_panel.auto_save_checkbox.setChecked(True) 
        self.test_panel.popup_window_checkbox.setChecked(True)
        self.test_panel.detailed_log_checkbox.setChecked(True)
        
        print("Opciones configuradas:")
        print("- Mostrar graficos en panel: SI")
        print("- Guardar automaticamente: SI")  
        print("- Ventana emergente: SI")
        print("- Logging detallado: SI")
        
        # Inicializar y ejecutar
        try:
            self.test_panel.initialize_simulation()
            # Esperar y ejecutar
            QTimer.singleShot(1000, self.test_panel.run_full_simulation)
        except Exception as e:
            print(f"Error iniciando simulacion: {e}")


def main():
    """Funcion principal"""
    print("=" * 60)
    print("TEST SISTEMA AUTOMATICO DE GRAFICOS PON")
    print("=" * 60)
    print()
    print("Esta aplicacion demuestra el sistema que:")
    print("- Guarda automaticamente graficos PNG de alta resolucion")
    print("- Muestra ventana emergente con graficos interactivos")
    print("- Exporta datos completos en JSON y TXT")
    print("- Organiza todo en carpetas con timestamp")
    print()
    
    # Verificar matplotlib
    try:
        import matplotlib
        print("OK Matplotlib disponible")
    except ImportError:
        print("ERROR Matplotlib no disponible")
        print("Instala con: pip install matplotlib")
        return
    
    print("La simulacion comenzara en 2 segundos...")
    print("Observa:")
    print("- Mensajes de progreso en consola")
    print("- Ventana emergente con graficos")
    print("- Creacion de carpeta simulation_results/")
    print()
    
    app = QApplication(sys.argv)
    
    window = SimpleGraphicsTestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()