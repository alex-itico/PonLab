from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel)
from PyQt5.QtCore import pyqtSignal

class SimulationPanel(QWidget):
    """Panel de control para simulación PON"""
    
    start_simulation = pyqtSignal(dict)  # Change to emit dictionary of parameters
    stop_simulation = pyqtSignal()   # Changed from stop_requested
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz básica"""
        layout = QVBoxLayout(self)
        
        # Controles básicos
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Iniciar Simulación")
        self.start_btn.clicked.connect(self._on_start_clicked)
        
        self.stop_btn = QPushButton("Detener")
        self.stop_btn.clicked.connect(self.stop_simulation.emit)
        self.stop_btn.setEnabled(False)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
    def _on_start_clicked(self):
        """Gather parameters and emit start signal"""
        params = {
            'simulation_time': 60,  # Default 60 seconds
            'time_step': 1,        # Default 1 second
            'traffic_profile': 'constant',
            'mean_rate': 500       # Default 500 Mbps
        }
        self.start_simulation.emit(params)

    def on_simulation_started(self):
        """Actualizar UI cuando inicia simulación"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
    def on_simulation_finished(self):
        """Actualizar UI cuando termina simulación"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)