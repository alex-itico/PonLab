from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class UpstreamScheduler(QObject):
    """Planificador del canal de subida usando First-Fit"""
    
    bandwidth_allocated = pyqtSignal(dict)  # Emite asignaciones de ancho de banda
    simulation_step = pyqtSignal(int)  # Emite paso actual de simulación
    simulation_finished = pyqtSignal()
    
    def __init__(self, total_bandwidth=10000):
        super().__init__()
        self.total_bandwidth = total_bandwidth  # Usar el valor recibido
        self.simulation_running = False
        self.current_step = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._simulation_step)
        
    def first_fit_allocation(self, onus):
        """Implementación básica de First-Fit"""
        allocations = {}
        available_bandwidth = self.total_bandwidth
        
        for onu in onus:
            requested = onu.properties.get('upstream_bandwidth', 0)
            if requested <= available_bandwidth:
                allocated = requested
            else:
                allocated = available_bandwidth
                
            allocations[onu.id] = allocated
            available_bandwidth -= allocated
            
        return allocations
    
    def start_simulation(self, duration=60, step=1):
        """Iniciar simulación"""
        if not self.simulation_running:
            self.simulation_running = True
            self.current_step = 0
            self.timer.start(step * 1000)  # Convertir a milisegundos
    
    def stop_simulation(self):
        """Detener simulación"""
        if self.simulation_running:
            self.simulation_running = False
            self.timer.stop()
            self.simulation_finished.emit()
    
    def _simulation_step(self):
        """Ejecutar un paso de simulación"""
        if not self.simulation_running:
            return
            
        self.current_step += 1
        self.simulation_step.emit(self.current_step)