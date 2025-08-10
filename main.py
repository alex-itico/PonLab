"""
Simulador de Redes Ópticas Pasivas
Punto de entrada principal de la aplicación
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer
from utils.resource_manager import resource_manager
from ui.splash_screen import SplashScreen
from ui.main_window import MainWindow

def main():
    """Función principal de la aplicación"""
    # Crear la aplicación Qt
    app = QApplication(sys.argv)
    
    # Configurar icono de la aplicación para la barra de tareas
    app_icon = resource_manager.get_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    
    # Crear y mostrar splash screen
    splash = SplashScreen()
    splash.show_splash(duration=3000)  # Mostrar por 3 segundos
    
    # Crear la ventana principal pero no mostrarla aún
    window = MainWindow()
    
    # Función para mostrar la ventana principal después del splash
    def show_main_window():
        window.show()
        splash.close()
    
    # Usar QTimer para mostrar la ventana principal después del splash
    QTimer.singleShot(3000, show_main_window)  # Esperar 3 segundos
    
    # Ejecutar el bucle principal de la aplicación
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
