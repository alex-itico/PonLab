"""
Simulation Manager
Coordinador principal de la simulación PON que integra todos los componentes
"""

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import time

class SimulationManager(QObject):
    """Gestor principal de simulación que coordina OLT, ONUs y protocolos"""
    
    # Señales para la interfaz
    simulation_started = pyqtSignal()
    simulation_stopped = pyqtSignal()
    simulation_finished = pyqtSignal()
    simulation_step = pyqtSignal(int)  # Paso actual
    statistics_updated = pyqtSignal(dict)  # Estadísticas actualizadas
    sdn_metrics_updated = pyqtSignal(dict)  # Métricas del controlador SDN
    
    def __init__(self):
        super().__init__()
        
        # Estado de la simulación
        self.is_running = False
        self.current_step = 0
        self.total_steps = 60
        self.step_duration = 1.0
        
        # Componentes de la simulación
        self.olt = None
        self.onus = []
        self.device_manager = None
        
        # Configuración de simulación
        self.simulation_params = {}
        
        # Estadísticas globales
        self.global_stats = {
            'start_time': None,
            'total_duration': 0,
            'total_polling_cycles': 0,
            'total_bandwidth_allocated': 0,
            'network_utilization': 0,
            'successful_transmissions': 0,
            'failed_transmissions': 0
        }
        
        # Timer principal de coordinación
        self.coordination_timer = QTimer()
        self.coordination_timer.timeout.connect(self._coordination_step)
        
    def set_device_manager(self, device_manager):
        """Establecer referencia al gestor de dispositivos"""
        self.device_manager = device_manager
        
    def initialize_simulation(self, params):
        """Inicializar la simulación con los parámetros dados"""
        self.simulation_params = params
        self.total_steps = int(params.get('simulation_time', 60))
        self.step_duration = params.get('time_step', 1.0)
        
        # Buscar dispositivos en el canvas
        if not self.device_manager:
            print("❌ Error: No hay device manager disponible")
            return False
            
        # Obtener OLT y ONUs del canvas
        self._discover_devices()
        
        if not self.olt:
            print("❌ Error: No se encontró un OLT en el canvas")
            return False
            
        if not self.onus:
            print("❌ Error: No se encontraron ONUs en el canvas")
            return False
            
        # Configurar la red PON
        self._setup_pon_network()
        
        # Configurar parámetros de simulación en dispositivos
        self._configure_devices()
        
        print(f"✅ Simulación inicializada: OLT con {len(self.onus)} ONUs")
        return True
        
    def _discover_devices(self):
        """Descubrir dispositivos OLT y ONU en el canvas"""
        if not self.device_manager:
            return
            
        # Buscar OLT
        olts = self.device_manager.get_devices_by_type("OLT")
        if olts:
            self.olt = olts[0]  # Usar el primer OLT encontrado
            print(f"🔍 OLT encontrado: {self.olt.name}")
        
        # Buscar ONUs
        self.onus = self.device_manager.get_devices_by_type("ONU")
        print(f"🔍 {len(self.onus)} ONUs encontradas")
        
    def _setup_pon_network(self):
        """Configurar la red PON registrando ONUs en el OLT"""
        if not self.olt or not self.onus:
            return
            
        # Registrar ONUs en el OLT
        for onu in self.onus:
            self.olt.register_onu(onu)
            
        # Registrar ONUs en el scheduler del OLT
        if self.olt.scheduler:
            for onu in self.onus:
                self.olt.scheduler.register_onu(onu)
                
        print(f"🔗 Red PON configurada: {len(self.onus)} ONUs registradas")
        
    def _configure_devices(self):
        """Configurar dispositivos con parámetros de simulación"""
        # Configurar perfil de tráfico en ONUs
        traffic_profile = self.simulation_params.get('traffic_profile', 'constant')
        mean_rate = self.simulation_params.get('mean_rate', 500)
        
        for onu in self.onus:
            onu.properties['traffic_profile'] = traffic_profile
            onu.properties['mean_rate'] = mean_rate
            
        # Configurar scheduler del OLT
        if self.olt and self.olt.scheduler:
            self.olt.scheduler.configure_simulation(self.simulation_params)
            
        print(f"⚙️ Dispositivos configurados: perfil={traffic_profile}, tasa={mean_rate}Mbps")
        
    def start_simulation(self):
        """Iniciar la simulación completa"""
        if self.is_running:
            print("⚠️ La simulación ya está en ejecución")
            return False
            
        if not self.olt or not self.onus:
            print("❌ Error: Dispositivos no configurados correctamente")
            return False
            
        # Reiniciar estadísticas
        self.current_step = 0
        self.global_stats = {
            'start_time': time.time(),
            'total_duration': 0,
            'total_polling_cycles': 0,
            'total_bandwidth_allocated': 0,
            'network_utilization': 0,
            'successful_transmissions': 0,
            'failed_transmissions': 0
        }
        
        # Iniciar simulación
        self.is_running = True
        
        # Iniciar polling en el OLT
        self.olt.start_polling()
        
        # Iniciar scheduler del OLT
        if self.olt.scheduler:
            self.olt.scheduler.start_simulation()
            
        # Iniciar timer de coordinación
        coordination_interval = int(self.step_duration * 1000)  # ms
        self.coordination_timer.start(coordination_interval)
        
        # Emitir señales
        self.simulation_started.emit()
        
        print(f"🚀 Simulación iniciada: {self.total_steps} pasos de {self.step_duration}s")
        return True
        
    def stop_simulation(self):
        """Detener la simulación"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        # Detener timer de coordinación
        self.coordination_timer.stop()
        
        # Detener polling del OLT
        if self.olt:
            self.olt.stop_polling()
            
        # Detener scheduler del OLT
        if self.olt and self.olt.scheduler:
            self.olt.scheduler.stop_simulation()
            
        # Calcular duración total
        if self.global_stats['start_time']:
            self.global_stats['total_duration'] = time.time() - self.global_stats['start_time']
            
        # Emitir señales
        self.simulation_stopped.emit()
        
        print(f"⏹️ Simulación detenida en paso {self.current_step}")
        
    def _coordination_step(self):
        """Ejecutar un paso de coordinación de la simulación"""
        if not self.is_running:
            return
            
        self.current_step += 1
        
        # Recopilar estadísticas de todos los componentes
        self._collect_statistics()
        
        # Emitir señales de progreso
        self.simulation_step.emit(self.current_step)
        self.statistics_updated.emit(self.get_current_statistics())
        
        # Verificar si la simulación debe terminar
        if self.current_step >= self.total_steps:
            self._finish_simulation()
            
    def _collect_statistics(self):
        """Recopilar estadísticas de todos los componentes"""
        # Estadísticas del OLT
        if self.olt:
            olt_stats = self.olt.get_polling_stats()
            self.global_stats['total_polling_cycles'] = olt_stats.get('total_polls', 0)
            
            # Si es un OLT_SDN, recopilar métricas SDN
            if hasattr(self.olt, 'get_sdn_dashboard'):
                sdn_metrics = self.olt.get_sdn_dashboard()
                self.sdn_metrics_updated.emit(sdn_metrics)
            
        # Estadísticas del scheduler
        if self.olt and self.olt.scheduler:
            scheduler_stats = self.olt.scheduler.get_current_stats()
            self.global_stats['total_bandwidth_allocated'] = scheduler_stats.get('successful_allocations', 0)
            self.global_stats['network_utilization'] = scheduler_stats.get('average_utilization', 0)
            
        # Estadísticas de las ONUs
        total_transmissions = 0
        successful_transmissions = 0
        
        for onu in self.onus:
            onu_stats = onu.get_onu_stats()
            total_transmissions += onu_stats.get('polls_received', 0)
            successful_transmissions += onu_stats.get('responses_sent', 0)
            
        self.global_stats['successful_transmissions'] = successful_transmissions
        self.global_stats['failed_transmissions'] = total_transmissions - successful_transmissions
        
    def _finish_simulation(self):
        """Finalizar la simulación"""
        self.stop_simulation()
        
        # Mostrar resumen final
        self._print_final_summary()
        
        # Emitir señal de finalización
        self.simulation_finished.emit()
        
    def _print_final_summary(self):
        """Imprimir resumen final de la simulación"""
        print(f"\n📊 RESUMEN FINAL DE SIMULACIÓN")
        print(f"{'='*50}")
        print(f"• Duración total: {self.global_stats['total_duration']:.1f} segundos")
        print(f"• Pasos completados: {self.current_step}/{self.total_steps}")
        print(f"• Ciclos de polling: {self.global_stats['total_polling_cycles']}")
        print(f"• Asignaciones de BW: {self.global_stats['total_bandwidth_allocated']}")
        print(f"• Utilización promedio: {self.global_stats['network_utilization']:.1f}%")
        print(f"• Transmisiones exitosas: {self.global_stats['successful_transmissions']}")
        print(f"• Transmisiones fallidas: {self.global_stats['failed_transmissions']}")
        
        # Estadísticas por dispositivo
        print(f"\n📋 ESTADÍSTICAS POR DISPOSITIVO:")
        if self.olt:
            olt_stats = self.olt.get_polling_stats()
            print(f"• OLT {self.olt.name}:")
            print(f"  - Tasa de éxito: {olt_stats.get('success_rate', 0):.1f}%")
            print(f"  - ONUs registradas: {olt_stats.get('registered_onus', 0)}")
            
        for i, onu in enumerate(self.onus):
            onu_stats = onu.get_onu_stats()
            print(f"• ONU {onu.name}:")
            print(f"  - Respuestas enviadas: {onu_stats.get('responses_sent', 0)}")
            print(f"  - Datos transmitidos: {onu_stats.get('data_transmitted', 0):.1f} MB")
            print(f"  - Tasa de respuesta: {onu_stats.get('response_rate', 0):.1f}%")
            
    def get_current_statistics(self):
        """Obtener estadísticas actuales de la simulación"""
        current_stats = self.global_stats.copy()
        current_stats['current_step'] = self.current_step
        current_stats['total_steps'] = self.total_steps
        current_stats['progress_percentage'] = (self.current_step / self.total_steps) * 100
        
        # Agregar estadísticas detalladas si están disponibles
        if self.olt:
            current_stats['olt_stats'] = self.olt.get_polling_stats()
            
        if self.olt and self.olt.scheduler:
            current_stats['scheduler_stats'] = self.olt.scheduler.get_current_stats()
            
        current_stats['onu_count'] = len(self.onus)
        current_stats['onu_stats'] = [onu.get_onu_stats() for onu in self.onus]
        
        return current_stats
        
    def get_device_statistics(self):
        """Obtener estadísticas detalladas de dispositivos"""
        device_stats = {}
        
        if self.olt:
            device_stats['olt'] = {
                'name': self.olt.name,
                'polling_stats': self.olt.get_polling_stats(),
                'registered_onus': len(self.olt.registered_onus)
            }
            
            if self.olt.scheduler:
                device_stats['olt']['scheduler_stats'] = self.olt.scheduler.get_current_stats()
                device_stats['olt']['allocation_history'] = self.olt.scheduler.get_allocation_history()
                
        device_stats['onus'] = []
        for onu in self.onus:
            onu_data = {
                'name': onu.name,
                'id': onu.id,
                'stats': onu.get_onu_stats(),
                'properties': onu.properties.copy()
            }
            device_stats['onus'].append(onu_data)
            
        return device_stats
        
    def is_simulation_running(self):
        """Verificar si la simulación está en ejecución"""
        return self.is_running
        
    def get_simulation_progress(self):
        """Obtener progreso actual de la simulación"""
        if self.total_steps == 0:
            return 0
        return (self.current_step / self.total_steps) * 100