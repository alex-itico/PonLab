from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
                           QComboBox, QGroupBox, QProgressBar)
from PyQt5.QtCore import pyqtSignal, QTimer

class SimulationPanel(QWidget):
    """Panel de control para simulación PON"""
    
    start_simulation = pyqtSignal(dict)  # Emite parámetros de simulación
    stop_simulation = pyqtSignal()       # Señal para detener simulación
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.simulation_running = False
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self._update_progress)
        self.current_time = 0
        self.total_time = 60
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz completa de simulación"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Título del panel
        title_label = QLabel("🔬 Simulación PON")
        title_label.setStyleSheet("font-weight: bold; font-size: 12px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Grupo de configuración temporal
        time_group = QGroupBox("Configuración Temporal")
        time_layout = QVBoxLayout(time_group)
        
        # Tiempo total de simulación
        time_total_layout = QHBoxLayout()
        time_total_layout.addWidget(QLabel("Tiempo Total (s):"))
        self.time_total_spin = QSpinBox()
        self.time_total_spin.setRange(10, 3600)  # 10 segundos a 1 hora
        self.time_total_spin.setValue(60)
        self.time_total_spin.setSuffix(" s")
        time_total_layout.addWidget(self.time_total_spin)
        time_layout.addLayout(time_total_layout)
        
        # Intervalo de paso
        time_step_layout = QHBoxLayout()
        time_step_layout.addWidget(QLabel("Paso (s):"))
        self.time_step_spin = QDoubleSpinBox()
        self.time_step_spin.setRange(0.1, 10.0)
        self.time_step_spin.setValue(1.0)
        self.time_step_spin.setSingleStep(0.1)
        self.time_step_spin.setSuffix(" s")
        time_step_layout.addWidget(self.time_step_spin)
        time_layout.addLayout(time_step_layout)
        
        layout.addWidget(time_group)
        
        # Grupo de configuración de tráfico
        traffic_group = QGroupBox("Configuración de Tráfico")
        traffic_layout = QVBoxLayout(traffic_group)
        
        # Perfil de tráfico
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Perfil:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Constante", "Variable", "Ráfagas"])
        profile_layout.addWidget(self.profile_combo)
        traffic_layout.addLayout(profile_layout)
        
        # Tasa promedio
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Tasa (Mbps):"))
        self.rate_spin = QSpinBox()
        self.rate_spin.setRange(1, 10000)
        self.rate_spin.setValue(500)
        self.rate_spin.setSuffix(" Mbps")
        rate_layout.addWidget(self.rate_spin)
        traffic_layout.addLayout(rate_layout)
        
        layout.addWidget(traffic_group)
        
        # Progreso de simulación
        progress_group = QGroupBox("Progreso")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Listo para iniciar")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
        # Controles de simulación
        btn_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶ Iniciar Simulación")
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.stop_btn = QPushButton("⏹ Detener")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
    def _on_start_clicked(self):
        """Recopilar parámetros y iniciar simulación"""
        # Obtener perfil de tráfico
        profiles = {
            "Constante": "constant",
            "Variable": "variable", 
            "Ráfagas": "burst"
        }
        
        params = {
            'simulation_time': self.time_total_spin.value(),
            'time_step': self.time_step_spin.value(),
            'traffic_profile': profiles[self.profile_combo.currentText()],
            'mean_rate': self.rate_spin.value()
        }
        
        self.total_time = params['simulation_time']
        self.current_time = 0
        
        self.start_simulation.emit(params)
    
    def _on_stop_clicked(self):
        """Detener simulación"""
        self.stop_simulation.emit()

    def _update_progress(self):
        """Actualizar barra de progreso"""
        if self.simulation_running:
            self.current_time += 1
            progress = (self.current_time / self.total_time) * 100
            self.progress_bar.setValue(int(progress))
            self.status_label.setText(f"Ejecutando... {self.current_time}/{self.total_time}s")
            
            if self.current_time >= self.total_time:
                self.on_simulation_finished()
    
    def on_simulation_started(self):
        """Actualizar UI cuando inicia simulación"""
        self.simulation_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Configurar progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(self.total_time)
        self.progress_bar.setValue(0)
        self.current_time = 0
        
        # Iniciar timer de progreso
        self.progress_timer.start(1000)  # Actualizar cada segundo
        
        self.status_label.setText("Iniciando simulación...")
        
    def on_simulation_finished(self):
        """Actualizar UI cuando termina simulación"""
        self.simulation_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Detener timer y ocultar progreso
        self.progress_timer.stop()
        self.progress_bar.setVisible(False)
        
        self.status_label.setText("Simulación completada")
        
    def on_simulation_stopped(self):
        """Actualizar UI cuando se detiene manualmente la simulación"""
        self.simulation_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Detener timer y ocultar progreso
        self.progress_timer.stop()
        self.progress_bar.setVisible(False)
        
        self.status_label.setText("Simulación detenida")