"""
NetPONPy Adapter
Adaptador que integra la lógica de simulación de netPONpy con PonLab
"""

import sys
import os

# Agregar netPONPy al path
netponpy_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'netPONPy')
if netponpy_path not in sys.path:
    sys.path.append(netponpy_path)

try:
    from netPonPy.pon.orchestrator.pon_orchestrator import PONOrchestrator
    from netPonPy.pon.interfaces.dba_algorithm_interface import (
        FCFSDBAAlgorithm, 
        PriorityDBAAlgorithm, 
        RLDBAAlgorithm
    )
    NETPONPY_AVAILABLE = True
    print("OK netPONpy importado correctamente")
except ImportError as e:
    print(f"Error importando netPONpy: {e}")
    NETPONPY_AVAILABLE = False

class NetPONPyAdapter:
    """Adaptador para integrar netPONpy con PonLab"""
    
    def __init__(self):
        self.orchestrator = None
        self.is_available = NETPONPY_AVAILABLE
        self.current_algorithm = "FCFS"
        self.detailed_logging = True
        self.log_callback = None  # Callback para enviar logs detallados
        
        # Configuración por defecto
        self.default_config = {
            'num_onus': 4,
            'traffic_scenario': 'residential_medium',
            'episode_duration': 10.0,  # 10 segundos por defecto
            'simulation_timestep': 0.1  # 100ms por paso
        }
        
    def is_netponpy_available(self):
        """Verificar si netPONpy está disponible"""
        return self.is_available
    
    def set_log_callback(self, callback):
        """Establecer callback para logs detallados"""
        self.log_callback = callback
        # Si ya existe el orquestador, propagarlo inmediatamente
        if self.orchestrator and hasattr(self.orchestrator, 'set_log_callback'):
            self.orchestrator.set_log_callback(callback)
        
    def set_detailed_logging(self, enabled):
        """Habilitar/deshabilitar logging detallado"""
        self.detailed_logging = enabled
    
    def _log_event(self, category, message):
        """Enviar evento al log callback si está disponible"""
        if self.log_callback and self.detailed_logging:
            formatted_message = f"[{category}] {message}"
            self.log_callback(formatted_message)
        
    def initialize_orchestrator_from_topology(self, device_manager):
        """Inicializar el orquestador basándose en la topología del canvas"""
        if not self.is_available:
            return False, "NetPONpy no está disponible"
            
        if not device_manager:
            return False, "Device manager no disponible"
            
        # Verificar que hay OLT en la topología
        olts = device_manager.get_devices_by_type("OLT")
        if not olts:
            return False, "No se encontró ningún OLT en la topología"
            
        if len(olts) > 1:
            return False, "Solo se soporta un OLT por simulación"
            
        # Obtener número de ONUs de la topología
        onus = device_manager.get_devices_by_type("ONU")
        if not onus:
            return False, "No se encontraron ONUs en la topología"
            
        num_onus = len(onus)
        
        try:
            self.orchestrator = PONOrchestrator(
                num_onus=num_onus,
                traffic_scenario='residential_medium',
                episode_duration=10.0,
                simulation_timestep=0.1
            )
            
            # Configurar algoritmo DBA por defecto (FCFS)
            self.set_dba_algorithm("FCFS")
            
            # Configurar callback de logging detallado en el orquestador
            if self.log_callback:
                self.orchestrator.set_log_callback(self.log_callback)
            
            print(f"🚀 PONOrchestrator inicializado con {num_onus} ONUs desde topología")
            return True, f"Orquestador inicializado con {num_onus} ONUs"
            
        except Exception as e:
            print(f"❌ Error inicializando orchestrator: {e}")
            return False, f"Error: {str(e)}"
    
    def initialize_orchestrator(self, num_onus=4):
        """Inicializar el orquestador de PON (método legacy)"""
        if not self.is_available:
            return False
            
        try:
            self.orchestrator = PONOrchestrator(
                num_onus=num_onus,
                traffic_scenario='residential_medium',
                episode_duration=10.0,
                simulation_timestep=0.1
            )
            
            # Configurar algoritmo DBA por defecto (FCFS)
            self.set_dba_algorithm("FCFS")
            
            # Configurar callback de logging detallado en el orquestador
            if self.log_callback:
                self.orchestrator.set_log_callback(self.log_callback)
            
            print(f"🚀 PONOrchestrator inicializado con {num_onus} ONUs")
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando orchestrator: {e}")
            return False
            
    def set_dba_algorithm(self, algorithm_name):
        """Configurar algoritmo DBA"""
        if not self.orchestrator:
            return False
            
        try:
            if algorithm_name == "FCFS":
                algorithm = FCFSDBAAlgorithm()
            elif algorithm_name == "Priority":
                algorithm = PriorityDBAAlgorithm(starvation_threshold=100.0)
            elif algorithm_name == "RL-DBA":
                algorithm = RLDBAAlgorithm()
            else:
                print(f"❌ Algoritmo desconocido: {algorithm_name}")
                return False
                
            self.orchestrator.set_dba_algorithm(algorithm)
            self.current_algorithm = algorithm_name
            print(f"✅ Algoritmo DBA configurado: {algorithm_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error configurando algoritmo DBA: {e}")
            return False
            
    def start_simulation(self):
        """Iniciar simulación"""
        if not self.orchestrator:
            print("❌ Orchestrator no inicializado")
            return False
            
        try:
            # Resetear orquestador
            self.orchestrator.reset()
            print("🚀 Simulación netPONpy iniciada")
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando simulación: {e}")
            return False
            
    def step_simulation(self, action=None):
        """Ejecutar un paso de simulación"""
        if not self.orchestrator:
            return None
            
        try:
            # Si no hay acción, usar None (algoritmos determinísticos)
            if action is None:
                action = [0.25, 0.25, 0.25, 0.25]  # Distribución equitativa por defecto
            
            result = self.orchestrator.step(action)
            
            return {
                'status': result.status.name,
                'done': result.done,
                'metrics': result.metrics,
                'info': result.info
            }
            
        except Exception as e:
            self._log_event("ERROR", f"Error en simulación: {e}")
            print(f"❌ Error en paso de simulación: {e}")
            return None
            
    def get_current_state(self):
        """Obtener estado actual de la simulación"""
        if not self.orchestrator:
            return {}
            
        try:
            state = self.orchestrator.get_state()
            return {
                'buffer_levels': state.get('buffer_levels', []),
                'sim_time': state.get('sim_time', 0.0),
                'step': state.get('step', 0),
                'algorithm': self.current_algorithm,
                'total_transmitted': state.get('total_transmitted', 0),
                'total_requests': state.get('total_requests', 0)
            }
        except Exception as e:
            print(f"❌ Error obteniendo estado: {e}")
            return {}
            
    def get_available_algorithms(self):
        """Obtener lista de algoritmos DBA disponibles"""
        return ["FCFS", "Priority", "RL-DBA"]
        
    def cleanup(self):
        """Limpiar recursos"""
        self.orchestrator = None
        self.log_callback = None
        print("🧹 Adaptador NetPONpy limpiado")