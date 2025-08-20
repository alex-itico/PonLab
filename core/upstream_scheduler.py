from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import time
import numpy as np

class UpstreamScheduler(QObject):
    """Planificador del canal de subida usando First-Fit con protocolo PON realista"""
    
    bandwidth_allocated = pyqtSignal(dict)  # Emite asignaciones de ancho de banda
    simulation_step = pyqtSignal(int)       # Emite paso actual de simulación
    simulation_finished = pyqtSignal()      # Señal de simulación completada
    allocation_stats = pyqtSignal(dict)     # Estadísticas de asignación
    
    def __init__(self, total_bandwidth=10000):
        super().__init__()
        self.total_bandwidth = total_bandwidth  # Ancho de banda total en Mbps
        self.simulation_running = False
        self.current_step = 0
        self.max_steps = 60
        self.step_duration = 1.0  # segundos
        
        # Timers
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(self._simulation_step)
        
        # Estado del planificador
        self.registered_onus = {}
        self.current_allocations = {}
        self.allocation_history = []
        
        # Estadísticas
        self.stats = {
            'total_allocations': 0,
            'successful_allocations': 0,
            'rejected_requests': 0,
            'average_utilization': 0,
            'peak_utilization': 0,
            'allocation_efficiency': 0
        }
        
        # Configuración del algoritmo First-Fit
        self.min_allocation = 10  # Mbps mínimo a asignar
        self.guard_bandwidth = 100  # Mbps de ancho de banda de guarda
        self.fragmentation_threshold = 50  # Mbps mínimo para considerar útil
        
    def configure_simulation(self, params):
        """Configurar parámetros de simulación"""
        self.max_steps = int(params.get('simulation_time', 60))
        self.step_duration = params.get('time_step', 1.0)
        
        # Reiniciar estadísticas
        self.stats = {
            'total_allocations': 0,
            'successful_allocations': 0,
            'rejected_requests': 0,
            'average_utilization': 0,
            'peak_utilization': 0,
            'allocation_efficiency': 0
        }
        self.allocation_history = []
        
    def register_onu(self, onu):
        """Registrar ONU para asignación de ancho de banda"""
        self.registered_onus[onu.id] = onu
        print(f"📋 Scheduler: ONU {onu.name} registrada")
        
    def unregister_onu(self, onu_id):
        """Desregistrar ONU"""
        if onu_id in self.registered_onus:
            onu = self.registered_onus[onu_id]
            del self.registered_onus[onu_id]
            print(f"📋 Scheduler: ONU {onu.name} desregistrada")
    
    def first_fit_allocation(self, bandwidth_requests):
        """
        Implementación mejorada del algoritmo First-Fit para asignación de ancho de banda
        
        Args:
            bandwidth_requests: Lista de solicitudes [(onu_id, requested_bandwidth, priority)]
        
        Returns:
            dict: Asignaciones {onu_id: allocated_bandwidth}
        """
        allocations = {}
        available_bandwidth = self.total_bandwidth - self.guard_bandwidth
        
        # Ordenar solicitudes por prioridad (alta, normal, baja)
        priority_order = {'high': 0, 'normal': 1, 'low': 2}
        sorted_requests = sorted(
            bandwidth_requests,
            key=lambda x: (priority_order.get(x[2], 1), x[1])  # Por prioridad, luego por cantidad
        )
        
        # Estadísticas para este ciclo
        total_requested = sum(req[1] for req in sorted_requests)
        successful_count = 0
        
        for onu_id, requested, priority in sorted_requests:
            self.stats['total_allocations'] += 1
            
            if requested <= 0:
                allocations[onu_id] = 0
                continue
                
            # Aplicar First-Fit: asignar el primer espacio disponible que ajuste
            if requested <= available_bandwidth:
                # Asignación completa
                allocated = requested
                available_bandwidth -= allocated
                successful_count += 1
                self.stats['successful_allocations'] += 1
            elif available_bandwidth >= self.min_allocation:
                # Asignación parcial si hay al menos el mínimo disponible
                allocated = available_bandwidth
                available_bandwidth = 0
                successful_count += 1
                self.stats['successful_allocations'] += 1
            else:
                # Rechazar solicitud - no hay suficiente ancho de banda
                allocated = 0
                self.stats['rejected_requests'] += 1
            
            allocations[onu_id] = allocated
            
            # Si no queda ancho de banda útil, terminar
            if available_bandwidth < self.min_allocation:
                # Rechazar solicitudes restantes
                for remaining_onu_id, _, _ in sorted_requests[sorted_requests.index((onu_id, requested, priority))+1:]:
                    allocations[remaining_onu_id] = 0
                    self.stats['rejected_requests'] += 1
                break
        
        # Calcular estadísticas de utilización
        total_allocated = sum(allocations.values())
        utilization = (total_allocated / self.total_bandwidth) * 100
        
        self.stats['peak_utilization'] = max(self.stats['peak_utilization'], utilization)
        
        # Calcular eficiencia de asignación
        if total_requested > 0:
            efficiency = (total_allocated / total_requested) * 100
        else:
            efficiency = 100
            
        # Guardar en historial
        allocation_record = {
            'timestamp': time.time(),
            'step': self.current_step,
            'total_requested': total_requested,
            'total_allocated': total_allocated,
            'utilization': utilization,
            'efficiency': efficiency,
            'successful_requests': successful_count,
            'rejected_requests': len(sorted_requests) - successful_count,
            'fragmentation': available_bandwidth if available_bandwidth > 0 else 0
        }
        
        self.allocation_history.append(allocation_record)
        
        # Emitir estadísticas
        self.allocation_stats.emit(allocation_record)
        
        print(f"💻 First-Fit: {total_allocated:.1f}/{self.total_bandwidth} Mbps asignados "
              f"({utilization:.1f}% utilización, {efficiency:.1f}% eficiencia)")
        
        return allocations
    
    def process_bandwidth_requests(self, requests):
        """Procesar solicitudes de ancho de banda y enviar asignaciones a ONUs"""
        if not requests:
            return
            
        # Convertir solicitudes al formato requerido
        formatted_requests = []
        for request in requests:
            onu_id = request.get('onu_id')
            bandwidth = request.get('bandwidth_request', 0)
            priority = request.get('priority', 'normal')
            
            if onu_id in self.registered_onus and bandwidth > 0:
                formatted_requests.append((onu_id, bandwidth, priority))
        
        # Ejecutar algoritmo First-Fit
        allocations = self.first_fit_allocation(formatted_requests)
        
        # Enviar asignaciones a las ONUs
        for onu_id, allocated_bandwidth in allocations.items():
            if onu_id in self.registered_onus and allocated_bandwidth > 0:
                onu = self.registered_onus[onu_id]
                
                # Calcular ventana de transmisión (simplificado)
                transmission_window = {
                    'start_time': time.time() + 0.1,  # 100ms delay
                    'duration': self.step_duration * 0.8,  # 80% del ciclo
                    'bandwidth': allocated_bandwidth
                }
                
                onu.receive_grant(allocated_bandwidth, transmission_window)
        
        # Guardar asignaciones actuales
        self.current_allocations = allocations
        
        # Emitir señal con asignaciones
        self.bandwidth_allocated.emit(allocations)
    
    def start_simulation(self):
        """Iniciar simulación"""
        if not self.simulation_running:
            self.simulation_running = True
            self.current_step = 0
            
            # Iniciar generación de tráfico en ONUs
            for onu in self.registered_onus.values():
                onu.start_traffic_generation()
            
            timer_interval = int(self.step_duration * 1000)  # Convertir a ms
            self.simulation_timer.start(timer_interval)
            
            print(f"🚀 Simulación iniciada: {self.max_steps} pasos de {self.step_duration}s cada uno")
    
    def stop_simulation(self):
        """Detener simulación"""
        if self.simulation_running:
            self.simulation_running = False
            self.simulation_timer.stop()
            
            # Detener generación de tráfico en ONUs
            for onu in self.registered_onus.values():
                onu.stop_traffic_generation()
            
            # Calcular estadísticas finales
            self._calculate_final_stats()
            
            self.simulation_finished.emit()
            print("⏹️ Simulación detenida")
    
    def _simulation_step(self):
        """Ejecutar un paso de simulación"""
        if not self.simulation_running:
            return
            
        self.current_step += 1
        
        # Simular solicitudes de ancho de banda desde las ONUs registradas
        current_requests = []
        for onu in self.registered_onus.values():
            # Simular respuesta al polling (simplificado para el scheduler)
            response = onu.handle_poll_request()
            if response and response.get('bandwidth_request', 0) > 0:
                current_requests.append({
                    'onu_id': onu.id,
                    'bandwidth_request': response['bandwidth_request'],
                    'priority': 'normal',  # Simplificado por ahora
                    'queue_size': response.get('queue_size', 0)
                })
        
        # Procesar solicitudes con First-Fit
        if current_requests:
            self.process_bandwidth_requests(current_requests)
        
        # Emitir señal de paso
        self.simulation_step.emit(self.current_step)
        
        # Verificar si se completó la simulación
        if self.current_step >= self.max_steps:
            self.stop_simulation()
    
    def _calculate_final_stats(self):
        """Calcular estadísticas finales de la simulación"""
        if not self.allocation_history:
            return
            
        # Calcular promedios
        utilizations = [record['utilization'] for record in self.allocation_history]
        efficiencies = [record['efficiency'] for record in self.allocation_history]
        
        self.stats['average_utilization'] = np.mean(utilizations)
        self.stats['allocation_efficiency'] = np.mean(efficiencies)
        
        print(f"📊 Estadísticas finales:")
        print(f"   • Asignaciones totales: {self.stats['total_allocations']}")
        print(f"   • Asignaciones exitosas: {self.stats['successful_allocations']}")
        print(f"   • Solicitudes rechazadas: {self.stats['rejected_requests']}")
        print(f"   • Utilización promedio: {self.stats['average_utilization']:.1f}%")
        print(f"   • Utilización pico: {self.stats['peak_utilization']:.1f}%")
        print(f"   • Eficiencia promedio: {self.stats['allocation_efficiency']:.1f}%")
    
    def get_current_stats(self):
        """Obtener estadísticas actuales"""
        return self.stats.copy()
    
    def get_allocation_history(self):
        """Obtener historial de asignaciones"""
        return self.allocation_history.copy()