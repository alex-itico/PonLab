"""
PON Adapter - Adaptador unificado para simulación PON
Combina todas las funcionalidades de simulación en una interfaz limpia
"""

# Importar clases core de PON
try:
    from .pon_orchestrator import PONOrchestrator
    from .pon_dba import (
        FCFSDBAAlgorithm, 
        PriorityDBAAlgorithm, 
        RLDBAAlgorithm
    )
    from .pon_simulator import PONSimulator, EventEvaluator
    from .pon_traffic import get_available_scenarios, print_scenario_info
    PON_CORE_AVAILABLE = True
    print("OK PON Core cargado exitosamente")
except ImportError as e:
    print(f"ERROR cargando PON Core: {e}")
    PON_CORE_AVAILABLE = False

# Importar bridge de modelos RL
try:
    from .rl_integration.model_bridge import RLModelDBABridge
    RL_MODEL_BRIDGE_AVAILABLE = True
    print("OK RL Model Bridge disponible")
except ImportError as e:
    RL_MODEL_BRIDGE_AVAILABLE = False
    print(f"WARNING RL Model Bridge no disponible: {e}")


class PONAdapter:
    """Adaptador unificado para simulación PON"""
    
    def __init__(self):
        # Core components
        self.orchestrator = None
        self.simulator = None
        
        # State management
        self.is_available = PON_CORE_AVAILABLE
        self.current_algorithm = "FCFS"
        self.simulation_mode = "events"  # "cycles" o "events"
        self.detailed_logging = True
        self.log_callback = None
        
        # Results storage
        self.last_simulation_results = None
        
        # RL Model Bridge
        self.rl_model_bridge = None
        
        # Default configuration
        self.config = {
            'num_onus': 4,
            'traffic_scenario': 'residential_medium',
            'episode_duration': 10.0,
            'simulation_timestep': 0.1,
            'channel_capacity_mbps': 1024.0
        }
        
    # ===== CORE METHODS =====
    
    def is_pon_available(self):
        """Verificar si el core PON está disponible"""
        return self.is_available
    
    def set_log_callback(self, callback):
        """Establecer callback para logs detallados"""
        self.log_callback = callback
        # Propagar a simuladores activos
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
    
    # ===== INITIALIZATION METHODS =====
    
    def initialize_from_topology(self, device_manager):
        """Inicializar simulación basándose en la topología del canvas"""
        if not self.is_available:
            return False, "PON Core no está disponible"
            
        if not device_manager:
            return False, "Device manager no disponible"
            
        # Validar topología
        olts = device_manager.get_devices_by_type("OLT")
        onus = device_manager.get_devices_by_type("ONU")
        
        if not olts:
            return False, "No se encontró OLT en la topología"
        if len(olts) > 1:
            return False, "Solo se soporta un OLT por simulación"
        if not onus:
            return False, "No se encontraron ONUs en la topología"
            
        num_onus = len(onus)
        
        # Inicializar según modo de simulación
        return self._initialize_simulator_from_topology(num_onus)
    
    def initialize_simulation(self, num_onus=None):
        """Inicializar simulación con número específico de ONUs"""
        if not self.is_available:
            return False, "PON Core no está disponible"
            
        if num_onus is None:
            num_onus = self.config['num_onus']
        
        # Inicializar simulador unificado
        return self._initialize_simulator(num_onus)
    
    def _initialize_simulator_from_topology(self, num_onus):
        """Inicializar simulador desde topología"""
        try:
            dba_algorithm = self._get_dba_algorithm()
            
            # Crear simulador unificado
            self.simulator = PONSimulator(simulation_mode=self.simulation_mode)
            
            if self.simulation_mode == "events":
                self.simulator.setup_event_simulation(
                    num_onus=num_onus,
                    traffic_scenario=self.config['traffic_scenario'],
                    dba_algorithm=dba_algorithm,
                    channel_capacity_mbps=self.config['channel_capacity_mbps']
                )
            elif self.simulation_mode == "cycles":
                # Configurar simulación por ciclos (requiere orquestador)
                self._initialize_orchestrator(num_onus)
                if self.orchestrator:
                    self.simulator.setup_cycle_simulation(self.orchestrator.olt)
            
            self._log_event("INIT", f"Simulador inicializado con {num_onus} ONUs desde topología (modo: {self.simulation_mode})")
            return True, f"Simulador inicializado con {num_onus} ONUs (modo: {self.simulation_mode})"
            
        except Exception as e:
            error_msg = f"Error inicializando simulador: {str(e)}"
            self._log_event("ERROR", error_msg)
            return False, error_msg
    
    def _initialize_orchestrator(self, num_onus):
        """Inicializar orquestador para simulación por ciclos"""
        try:
            self.orchestrator = PONOrchestrator(
                num_onus=num_onus,
                traffic_scenario=self.config['traffic_scenario'],
                episode_duration=self.config['episode_duration'],
                simulation_timestep=self.config['simulation_timestep']
            )
            
            self.set_dba_algorithm(self.current_algorithm)
            
            if self.log_callback:
                self.orchestrator.set_log_callback(self.log_callback)
            
            self._log_event("INIT", f"Orquestador inicializado con {num_onus} ONUs")
            return True
            
        except Exception as e:
            error_msg = f"Error inicializando orquestador: {str(e)}"
            self._log_event("ERROR", error_msg)
            return False
    
    def _initialize_simulator(self, num_onus):
        """Inicializar simulador unificado"""
        try:
            dba_algorithm = self._get_dba_algorithm()
            
            # Crear simulador unificado
            self.simulator = PONSimulator(simulation_mode=self.simulation_mode)
            
            if self.simulation_mode == "events":
                self.simulator.setup_event_simulation(
                    num_onus=num_onus,
                    traffic_scenario=self.config['traffic_scenario'],
                    dba_algorithm=dba_algorithm,
                    channel_capacity_mbps=self.config['channel_capacity_mbps']
                )
            elif self.simulation_mode == "cycles":
                # Configurar simulación por ciclos (requiere orquestador)
                self._initialize_orchestrator(num_onus)
                if self.orchestrator:
                    self.simulator.setup_cycle_simulation(self.orchestrator.olt)
            
            self._log_event("INIT", f"Simulador inicializado con {num_onus} ONUs (modo: {self.simulation_mode})")
            return True, f"Simulador inicializado exitosamente (modo: {self.simulation_mode})"
            
        except Exception as e:
            error_msg = f"Error inicializando simulador: {str(e)}"
            self._log_event("ERROR", error_msg)
            return False, error_msg
    
    
    # ===== SIMULATION CONTROL =====
    
    def set_simulation_mode(self, mode: str):
        """Seleccionar modo de simulación"""
        if mode in ["cycles", "events"]:
            self.simulation_mode = mode
            self._log_event("CONFIG", f"Modo de simulación cambiado a: {mode}")
        else:
            raise ValueError(f"Modo no soportado: {mode}")
    
    def run_simulation(self, duration_seconds=None, timesteps=None, callback=None):
        """Ejecutar simulación (detecta automáticamente el tipo)"""
        if not self.simulator:
            return False, "No hay simulador inicializado"
        
        try:
            if self.simulation_mode == "events":
                return self.run_event_simulation(duration_seconds or 10.0, callback)
            elif self.simulation_mode == "cycles":
                return self.run_cycle_simulation(timesteps or 1000, callback)
            else:
                return False, f"Modo de simulación no soportado: {self.simulation_mode}"
        except Exception as e:
            error_msg = f"Error ejecutando simulación: {str(e)}"
            self._log_event("ERROR", error_msg)
            return False, error_msg
    
    def run_event_simulation(self, duration_seconds=10.0, callback=None):
        """Ejecutar simulación por eventos por tiempo"""
        if not self.simulator or self.simulation_mode != "events":
            success, msg = self._initialize_simulator(self.config['num_onus'])
            if not success:
                return False, msg
        
        try:
            self._log_event("START", f"Iniciando simulación por eventos por {duration_seconds}s")
            
            # Crear callback wrapper si se proporciona
            event_callback = None
            if callback:
                def event_callback(event, sim_time):
                    callback("update", {
                        'sim_time': sim_time,
                        'event_type': event.event_type.value,
                        'onu_id': event.onu_id,
                        'data': event.data
                    })
            
            # Ejecutar simulación
            success, results = self.simulator.run_event_simulation(duration_seconds, event_callback)
            
            if success:
                # Almacenar resultados
                self.last_simulation_results = results
                
                # Callback final
                if callback:
                    callback("end", results)
                
                self._log_event("END", "Simulación por eventos completada exitosamente")
                return True, results
            else:
                return False, "Simulación por eventos falló"
            
        except Exception as e:
            error_msg = f"Error en simulación por eventos: {str(e)}"
            self._log_event("ERROR", error_msg)
            return False, error_msg
    
    def run_cycle_simulation(self, timesteps=1000, callback=None):
        """Ejecutar simulación por ciclos DBA por pasos"""
        if not self.simulator or self.simulation_mode != "cycles":
            return False, "Simulador por ciclos no inicializado"
            
        try:
            self._log_event("START", f"Iniciando simulación por ciclos: {timesteps} pasos")
            
            # Crear callback wrapper si se proporciona
            event_evaluator = None
            if callback:
                class CallbackEvaluator(EventEvaluator):
                    def __init__(self, cb):
                        self.callback = cb
                    
                    def on_init(self):
                        self.callback("init", {})
                    
                    def on_cycle_start(self, cycle_number: int, cycle_time: float):
                        self.callback("update", {
                            'steps': cycle_number,
                            'time': cycle_time,
                            'status': 'cycle_start'
                        })
                    
                    def on_cycle_end(self, dba_result):
                        self.callback("update", {
                            'steps': dba_result.cycle_number if hasattr(dba_result, 'cycle_number') else 0,
                            'time': dba_result.cycle_start_time if hasattr(dba_result, 'cycle_start_time') else 0,
                            'total_requests_processed': getattr(dba_result, 'total_requests_processed', 0),
                            'total_bandwidth_used': getattr(dba_result, 'total_bandwidth_used', 0),
                            'status': 'cycle_end'
                        })
                    
                    def on_simulation_end(self, attributes):
                        self.callback("end", attributes)
                
                event_evaluator = CallbackEvaluator(callback)
            
            # Ejecutar simulación
            success = self.simulator.run_cycle_simulation(timesteps, event_evaluator)
            
            if success:
                self._log_event("END", "Simulación por ciclos completada")
                return True, "Simulación completada exitosamente"
            else:
                return False, "Simulación por ciclos falló"
            
        except Exception as e:
            error_msg = f"Error en simulación por ciclos: {str(e)}"
            self._log_event("ERROR", error_msg)
            return False, error_msg
    
    # ===== DBA ALGORITHM MANAGEMENT =====
    
    def set_dba_algorithm(self, algorithm_name):
        """Configurar algoritmo DBA"""
        try:
            # Para simulador unificado
            if self.simulator and self.simulation_mode == "events":
                dba_algorithm = self._get_dba_algorithm_by_name(algorithm_name)
                # Reconfigurar simulación si es necesario
                # El algoritmo se aplicará en la próxima inicialización
            
            # Para simulación por ciclos
            if self.orchestrator:
                dba_algorithm = self._get_dba_algorithm_by_name(algorithm_name)
                self.orchestrator.set_dba_algorithm(dba_algorithm)
            
            self.current_algorithm = algorithm_name
            self._log_event("CONFIG", f"Algoritmo DBA configurado: {algorithm_name}")
            return True, f"Algoritmo cambiado a {algorithm_name}"
            
        except Exception as e:
            error_msg = f"Error configurando algoritmo DBA: {str(e)}"
            self._log_event("ERROR", error_msg)
            return False, error_msg
    
    def set_rl_model_bridge(self, rl_model_bridge):
        """Configurar bridge de modelo RL"""
        self.rl_model_bridge = rl_model_bridge
        if rl_model_bridge:
            self._log_event("CONFIG", f"Bridge RL configurado: {rl_model_bridge.get_name()}")
        else:
            self._log_event("CONFIG", "Bridge RL removido")
    
    def set_event_dba_algorithm(self, algorithm_name):
        """Cambiar algoritmo DBA específicamente para simulación por eventos (compatibilidad)"""
        return self.set_dba_algorithm(algorithm_name)
    
    def set_hybrid_dba_algorithm(self, algorithm_name):
        """Cambiar algoritmo DBA (método de compatibilidad - usa set_dba_algorithm)"""
        return self.set_dba_algorithm(algorithm_name)
    
    def _get_dba_algorithm(self):
        """Obtener algoritmo DBA actual"""
        return self._get_dba_algorithm_by_name(self.current_algorithm)
    
    def _get_dba_algorithm_by_name(self, algorithm_name):
        """Obtener instancia de algoritmo DBA por nombre"""
        algorithms = {
            "FCFS": FCFSDBAAlgorithm,
            "Priority": PriorityDBAAlgorithm,
            "RL-DBA": RLDBAAlgorithm
        }
        
        # Manejar agente RL pre-entrenado
        if algorithm_name == "RL Agent":
            if self.rl_model_bridge is not None:
                return self.rl_model_bridge
            else:
                raise ValueError("No se ha cargado ningún modelo RL. Seleccione un modelo primero.")
        
        if algorithm_name not in algorithms:
            raise ValueError(f"Algoritmo desconocido: {algorithm_name}")
            
        return algorithms[algorithm_name]()
    
    def get_available_algorithms(self):
        """Obtener lista de algoritmos DBA disponibles"""
        return ["FCFS", "Priority", "RL-DBA"]
    
    # ===== TRAFFIC SCENARIOS =====
    
    def get_available_traffic_scenarios(self):
        """Obtener escenarios de tráfico disponibles"""
        return get_available_scenarios()
    
    def print_traffic_scenario_info(self, scenario_name):
        """Imprimir información de escenario de tráfico"""
        print_scenario_info(scenario_name)
    
    # ===== STATE AND RESULTS =====
    
    def get_current_state(self):
        """Obtener estado actual de la simulación"""
        if self.simulator:
            return self.simulator.get_current_state()
        elif self.orchestrator:
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
                self._log_event("ERROR", f"Error obteniendo estado: {e}")
                return {}
        else:
            return {}
    
    def get_simulation_summary(self):
        """Obtener resumen completo de la simulación"""
        # Simulador unificado
        if self.simulator:
            if hasattr(self, 'last_simulation_results') and self.last_simulation_results:
                return self.last_simulation_results
            
            # Obtener resumen del simulador
            try:
                return self.simulator.get_simulation_summary()
            except Exception as e:
                self._log_event("ERROR", f"Error obteniendo resumen del simulador: {e}")
                # Fallback al estado actual
                current_state = self.simulator.get_current_state()
                return {
                    'simulation_summary': {
                        'simulation_stats': {
                            'simulation_time': current_state.get('sim_time', 0),
                            'total_requests': current_state.get('total_requests', 0),
                            'successful_requests': current_state.get('total_requests', 0),
                            'total_steps': current_state.get('events_processed', 0)
                        },
                        'performance_metrics': {
                            'total_transmitted': current_state.get('total_transmitted', 0),
                            'network_utilization': 0
                        },
                        'episode_metrics': {
                            'delays': [],
                            'throughputs': [], 
                            'buffer_levels_history': [],
                            'total_transmitted': current_state.get('total_transmitted', 0),
                            'total_requests': current_state.get('total_requests', 0)
                        }
                    },
                    'mode': self.simulation_mode
                }
        
        # No hay simulador
        else:
            return {}
    
    def get_orchestrator_stats(self):
        """Obtener estadísticas del orquestador"""
        if self.orchestrator:
            try:
                return self.orchestrator.get_orchestrator_stats()
            except Exception as e:
                self._log_event("ERROR", f"Error obteniendo estadísticas: {e}")
                return {}
        else:
            return {}
    
    def get_simulation_mode(self) -> str:
        """Obtener modo de simulación actual"""
        if self.simulator:
            return self.simulation_mode
        else:
            return "none"
    
    # ===== LEGACY COMPATIBILITY =====
    
    def initialize_orchestrator_from_topology(self, device_manager):
        """Método de compatibilidad (usa initialize_from_topology)"""
        return self.initialize_from_topology(device_manager)
    
    def initialize_orchestrator(self, num_onus=4):
        """Método de compatibilidad (usa initialize_simulation)"""
        success, msg = self.initialize_simulation(num_onus)
        return success  # Solo retorna bool para compatibilidad
    
    def run_netsim_simulation(self, timesteps=1000, callback=None):
        """Método de compatibilidad para simulación por ciclos"""
        success, result = self.run_cycle_simulation(timesteps, callback)
        return success  # Solo retorna bool para compatibilidad
    
    def initialize_event_simulator(self, num_onus=4, traffic_scenario='residential_medium', 
                                   channel_capacity_mbps=1024.0):
        """Método de compatibilidad para simulación por eventos"""
        # Actualizar config temporalmente
        old_scenario = self.config['traffic_scenario']
        old_capacity = self.config['channel_capacity_mbps']
        old_mode = self.simulation_mode
        
        self.config['traffic_scenario'] = traffic_scenario
        self.config['channel_capacity_mbps'] = channel_capacity_mbps
        self.simulation_mode = "events"
        
        result = self._initialize_simulator(num_onus)
        
        # Restaurar config
        self.config['traffic_scenario'] = old_scenario
        self.config['channel_capacity_mbps'] = old_capacity
        self.simulation_mode = old_mode
        
        return result
    
    # Métodos de compatibilidad para nombres antiguos
    def initialize_hybrid_simulator(self, num_onus=4, traffic_scenario='residential_medium', 
                                   channel_capacity_mbps=1024.0):
        """Método de compatibilidad (usa initialize_event_simulator)"""
        return self.initialize_event_simulator(num_onus, traffic_scenario, channel_capacity_mbps)
    
    def run_hybrid_simulation(self, duration_seconds=10.0, callback=None):
        """Método de compatibilidad (usa run_event_simulation)"""
        return self.run_event_simulation(duration_seconds, callback)
    
    def run_classic_simulation(self, timesteps=1000, callback=None):
        """Método de compatibilidad (usa run_cycle_simulation)"""
        return self.run_cycle_simulation(timesteps, callback)
    
    def set_use_hybrid_architecture(self, use_events: bool):
        """Método de compatibilidad (usa set_simulation_mode)"""
        mode = "events" if use_events else "cycles"
        self.set_simulation_mode(mode)
    
    
    # ===== CLEANUP =====
    
    def cleanup(self):
        """Limpiar todos los recursos"""
        if self.simulator:
            try:
                self.simulator.reset_simulation()
            except:
                pass
            self.simulator = None
        
        if self.orchestrator:
            self.orchestrator = None
        
        self.log_callback = None
        self.last_simulation_results = None
        
        self._log_event("CLEANUP", "Adaptador PON limpiado completamente")