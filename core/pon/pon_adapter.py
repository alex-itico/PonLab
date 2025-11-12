"""
PON Adapter - Adaptador unificado para simulación PON
Combina todas las funcionalidades de simulación en una interfaz limpia
"""

from typing import Dict, Any

# Importar clases core de PON
try:
    from ..simulation.pon_orchestrator import PONOrchestrator
    from ..algorithms.pon_dba import (
        FCFSDBAAlgorithm,
        PriorityDBAAlgorithm,
        RLDBAAlgorithm,
        StrictPriorityMinShareDBA,
        StrictPriorityMinShareDBA2,
        TEST,
        TESTB
    )
    from ..smart_rl_dba import SmartRLDBAAlgorithm
    from ..simulation.pon_simulator import PONSimulator, EventEvaluator
    from ..utilities.pon_traffic import get_available_scenarios, print_scenario_info
    PON_CORE_AVAILABLE = True
    print("OK PON Core cargado exitosamente")
except ImportError as e:
    print(f"ERROR cargando PON Core: {e}")
    PON_CORE_AVAILABLE = False
    PONOrchestrator = None
    PONSimulator = None
    EventEvaluator = None
    SmartRLDBAAlgorithm = None
    FCFSDBAAlgorithm = None
    PriorityDBAAlgorithm = None
    RLDBAAlgorithm = None
    StrictPriorityMinShareDBA = None
    StrictPriorityMinShareDBA2 = None
    TEST = None
    TESTB = None
    get_available_scenarios = lambda: []
    print_scenario_info = lambda x: None

# RL Model Bridge no disponible - eliminado para independencia
RL_MODEL_BRIDGE_AVAILABLE = False


class PONAdapter:
    """Adaptador unificado para simulación PON"""
    
    def __init__(self):
        # Core components
        self.orchestrator = None
        self.simulator = None
        
        # State management
        self.is_available = PON_CORE_AVAILABLE
        self.current_algorithm = "FCFS"
        self.use_sdn = False
        
        # Configuration
        self.config = {
            'num_onus': 4,
            'traffic_scenario': 'residential_medium',
            'episode_duration': 10.0,
            'simulation_timestep': 0.1,
            'channel_capacity_mbps': 1024.0,
            'simulation_mode': 'hybrid'
        }
        
        # Logging and mode
        self.detailed_logging = False
        self.simulation_mode = "events"  # "cycles" o "events"
        self.log_callback = None

        # Smart RL DBA management
        self.smart_rl_algorithm = None
        self.loaded_model_path = None
        
        # Results storage
        self.last_simulation_results = None

        # Incremental data writing
        self.incremental_writer = None
        self.incremental_writing_enabled = False
        
    def get_olt(self):
        """Obtener el OLT actual de la simulación"""
        if self.simulator and hasattr(self.simulator, 'olt'):
            return self.simulator.olt
        return None
        
    def get_sdn_metrics(self):
        """Obtener métricas SDN en formato para el dashboard"""
        olt = self.get_olt()
        if not olt:
            self._log_event("DEBUG", "get_sdn_metrics: No hay OLT disponible")
            return None
        
        if not hasattr(olt, 'sdn_metrics'):
            self._log_event("DEBUG", "get_sdn_metrics: OLT no tiene sdn_metrics")
            return None
            
        if not hasattr(olt, 'sdn_controller_metrics'):
            self._log_event("DEBUG", "get_sdn_metrics: OLT no tiene sdn_controller_metrics")
            return None
            
        self._log_event("DEBUG", f"get_sdn_metrics: OLT encontrado, tipo: {type(olt)}")
            
        # Calcular métricas globales
        try:
            global_metrics = {
                'total_reconfigurations': olt.sdn_controller_metrics['reconfigurations'],
                'grant_utilization': (olt.sdn_controller_metrics['utilized_grants'] / 
                                    max(1, olt.sdn_controller_metrics['total_grants'])) * 100,
                'current_fairness': olt.sdn_controller_metrics['fairness_history'][-1] if olt.sdn_controller_metrics['fairness_history'] else 0,
                'qos_violations': olt.sdn_controller_metrics['qos_violations']
            }
            self._log_event("DEBUG", f"get_sdn_metrics: Métricas globales calculadas: {global_metrics}")
        except Exception as e:
            self._log_event("ERROR", f"get_sdn_metrics: Error calculando métricas globales: {str(e)}")
            return None
            
        # Procesar métricas por ONU
        onu_metrics = {}
        try:
            for onu_id, metrics in olt.sdn_metrics.items():
                onu_metrics[onu_id] = {
                    'avg_latency': sum(metrics['latency']) / max(1, len(metrics['latency'])),
                    'packet_loss_rate': (metrics['losses'] / max(1, metrics['grants_allocated'])) * 100,
                    'avg_throughput': sum(metrics['throughput']) / max(1, len(metrics['throughput']))
                }
            self._log_event("DEBUG", f"get_sdn_metrics: Métricas calculadas para {len(onu_metrics)} ONUs")
        except Exception as e:
            self._log_event("ERROR", f"get_sdn_metrics: Error calculando métricas de ONUs: {str(e)}")
            return None
            
        return {
            'global_metrics': global_metrics,
            'onu_metrics': onu_metrics
        }
    
    def get_olt_sdn_instance(self):
        """
        Obtener la instancia de OLT_SDN si existe
        
        Returns:
            OLT_SDN instance si se está usando OLT_SDN, None en caso contrario
        """
        olt = self.get_olt()
        if not olt:
            return None
        
        # Verificar si es una instancia de OLT_SDN
        from core.pon.pon_sdn import OLT_SDN
        if isinstance(olt, OLT_SDN):
            self._log_event("DEBUG", f"get_olt_sdn_instance: OLT_SDN encontrado: {olt.id}")
            return olt
        else:
            self._log_event("DEBUG", f"get_olt_sdn_instance: OLT no es OLT_SDN, es {type(olt)}")
            return None
        
    def set_detailed_logging(self, enabled: bool):
        """Activar o desactivar el logging detallado"""
        self.detailed_logging = enabled
        
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

    def _extract_onu_configs_from_devices(self, onu_devices):
        """
        Extraer configuraciones de tráfico de dispositivos ONU del canvas

        Args:
            onu_devices: Lista de dispositivos ONU del canvas

        Returns:
            dict: Configuraciones por ONU {onu_id: config_dict}
        """
        onu_configs = {}

        for idx, onu_device in enumerate(onu_devices):
            # Usar el nombre real del dispositivo como ID
            onu_id = onu_device.name  # 'casa', 'prueba', etc.

            # Extraer configuración del dispositivo
            config = {
                'traffic_scenario': onu_device.properties.get('traffic_scenario', 'residential_medium'),
                'sla': onu_device.properties.get('sla', 200.0),
                'buffer_size': onu_device.properties.get('buffer_size', 512),
                'use_custom_params': onu_device.properties.get('use_custom_params', False),
                'custom_traffic_probs': onu_device.properties.get('custom_traffic_probs', {}),
                'custom_traffic_sizes': onu_device.properties.get('custom_traffic_sizes', {}),
                'transmission_rate': onu_device.properties.get('transmission_rate', 1024.0),
                'index': idx  # Guardar índice numérico para compatibilidad
            }

            onu_configs[onu_id] = config
            self._log_event("CONFIG", f"ONU {onu_id}: {config['traffic_scenario']}, "
                          f"SLA={config['sla']} Mbps, custom={config['use_custom_params']}")

        return onu_configs

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

        # Extraer configuraciones de tráfico de cada ONU desde el canvas
        onu_configs = self._extract_onu_configs_from_devices(onus)

        # Inicializar según modo de simulación
        return self._initialize_simulator_from_topology(num_onus, onu_configs)
    
    def initialize_simulation(self, num_onus=None):
        """Inicializar simulación con número específico de ONUs"""
        if not self.is_available:
            return False, "PON Core no está disponible"
            
        if num_onus is None:
            num_onus = self.config['num_onus']
        
        # Inicializar simulador unificado
        return self._initialize_simulator(num_onus)
    
    def _initialize_simulator_from_topology(self, num_onus, onu_configs=None):
        """Inicializar simulador desde topología"""
        try:
            if not all([PONOrchestrator, PONSimulator, EventEvaluator]):
                return False, "Clases de simulación no disponibles"

            dba_algorithm = self._get_dba_algorithm()

            # Crear simulador unificado
            self.simulator = PONSimulator(simulation_mode=self.simulation_mode)

            if self.simulation_mode == "events":
                self.simulator.setup_event_simulation(
                    num_onus=num_onus,
                    traffic_scenario=self.config['traffic_scenario'],
                    dba_algorithm=dba_algorithm,
                    channel_capacity_mbps=self.config['channel_capacity_mbps'],
                    use_sdn=self.use_sdn,
                    onu_configs=onu_configs  # Pasar configuraciones individuales
                )
            elif self.simulation_mode == "cycles":
                # Configurar simulación por ciclos (requiere orquestador)
                self._initialize_orchestrator(num_onus, onu_configs)
                if self.orchestrator:
                    self.simulator.setup_cycle_simulation(self.orchestrator.olt)
            
            self._log_event("INIT", f"Simulador inicializado con {num_onus} ONUs desde topología (modo: {self.simulation_mode})")
            return True, f"Simulador inicializado con {num_onus} ONUs (modo: {self.simulation_mode})"
            
        except Exception as e:
            error_msg = f"Error inicializando simulador: {str(e)}"
            self._log_event("ERROR", error_msg)
            return False, error_msg
    
    def _initialize_orchestrator(self, num_onus, onu_configs=None):
        """Inicializar orquestador para simulación por ciclos"""
        try:
            if not PONOrchestrator:
                return False, "PONOrchestrator no disponible"

            self.orchestrator = PONOrchestrator(
                num_onus=num_onus,
                traffic_scenario=self.config['traffic_scenario'],
                episode_duration=self.config['episode_duration'],
                simulation_timestep=self.config['simulation_timestep'],
                onu_configs=onu_configs  # Pasar configuraciones individuales
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
    
    def _initialize_simulator(self, num_onus, onu_configs=None):
        """Inicializar simulador unificado"""
        try:
            if not PONSimulator:
                return False, "PONSimulator no disponible"
                
            dba_algorithm = self._get_dba_algorithm()
            
            # Crear simulador unificado
            self.simulator = PONSimulator(simulation_mode=self.simulation_mode)
            
            if self.simulation_mode == "events":
                self.simulator.setup_event_simulation(
                    num_onus=num_onus,
                    traffic_scenario=self.config['traffic_scenario'],
                    dba_algorithm=dba_algorithm,
                    channel_capacity_mbps=self.config['channel_capacity_mbps'],
                    use_sdn=self.use_sdn,
                    onu_configs=onu_configs  # ✨ AGREGADO: Pasar configuraciones individuales
                )
            elif self.simulation_mode == "cycles":
                # Configurar simulación por ciclos (requiere orquestador)
                self._initialize_orchestrator(num_onus, onu_configs)  # ✨ AGREGADO: Pasar onu_configs
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
                
                # Forzar actualización final de métricas SDN
                if self.use_sdn:
                    try:
                        olt = self.get_olt()
                        if olt:
                            self._log_event("DEBUG", "Forzando actualización final de métricas SDN")
                            # Asegurarse de que el OLT calcule las métricas finales
                            if hasattr(olt, '_update_sdn_metrics'):
                                self._log_event("DEBUG", "Actualizando métricas finales del OLT_SDN")
                                olt._update_sdn_metrics(None, True)  # Forzar actualización final
                    except Exception as e:
                        self._log_event("ERROR", f"Error actualizando métricas SDN finales: {str(e)}")
                
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
            # Actualizar estado SDN
            self.use_sdn = algorithm_name == "SDN"
            self.current_algorithm = algorithm_name
            self._log_event("DEBUG", f"Configurando algoritmo: {algorithm_name} (SDN: {self.use_sdn})")
            
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
        if not PON_CORE_AVAILABLE:
            raise ValueError("PON Core no está disponible")
            
        # Manejar Smart RL DBA (incluye variante SDN)
        if algorithm_name in ["Smart-RL", "Smart-RL-SDN"]:
            if self.smart_rl_algorithm:
                # Configurar SDN para Smart-RL-SDN
                if algorithm_name == "Smart-RL-SDN":
                    self.use_sdn = True
                    self._log_event("DEBUG", "Smart-RL ejecutándose con controlador SDN")
                else:
                    self.use_sdn = False
                return self.smart_rl_algorithm
            else:
                raise ValueError("No hay modelo RL cargado. Use 'load_rl_model()' primero.")

        algorithms = {
            "FCFS": FCFSDBAAlgorithm,
            "Priority": PriorityDBAAlgorithm,
            "RL-DBA": RLDBAAlgorithm,
            "SDN": FCFSDBAAlgorithm,  # Usar FCFS como base para SDN
            "SP-MINSHARE": StrictPriorityMinShareDBA,
            "TEST_A": TEST,
            "TEST_B": TESTB,
        }

        if algorithm_name not in algorithms:
            raise ValueError(f"Algoritmo desconocido: {algorithm_name}")
            
        # Obtener clase del algoritmo
        algorithm_class = algorithms[algorithm_name]
        if algorithm_class is None:
            raise ValueError(f"Algoritmo {algorithm_name} no está disponible")

        # Crear instancia del algoritmo
        algorithm = algorithm_class()
        
        # Configurar estado SDN si es necesario
        if algorithm_name == "SDN":
            self._log_event("DEBUG", "Usando algoritmo SDN con base FCFS")
            self.use_sdn = True
        elif algorithm_name not in ["Smart-RL-SDN"]:
            # No desactivar SDN si es Smart-RL-SDN (ya se configuró arriba)
            self.use_sdn = False
            
        return algorithm
    
    def get_available_algorithms(self):
        """Obtener lista de algoritmos DBA disponibles"""
        algorithms = ["FCFS", "Priority", "RL-DBA", "SDN", "SP-MINSHARE", "TEST_A", "TEST_B"]

        # Agregar Smart RL DBA si hay modelo cargado
        if self.smart_rl_algorithm:
            algorithms.extend(["Smart-RL", "Smart-RL-SDN"])

        return algorithms
    
    def is_predictive_algorithm(self, name: str = None) -> bool:
        """
        Indica si el algoritmo es de tipo predictivo.
        Actualmente ningún algoritmo es considerado predictivo.
        """
        return False
    
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
    
    
    # ===== SMART RL MODEL MANAGEMENT =====

    def load_rl_model(self, model_path: str, env_params: Dict[str, Any] = None):
        """
        Cargar modelo RL entrenado para usar con Smart-RL DBA

        Args:
            model_path: Ruta al archivo del modelo (.zip)
            env_params: Parámetros del entorno (opcional)

        Returns:
            tuple: (success, message)
        """
        try:
            if not SmartRLDBAAlgorithm:
                return False, "SmartRLDBAAlgorithm no está disponible"
                
            # Configurar parámetros del entorno
            if env_params is None:
                env_params = {
                    'num_onus': self.config.get('num_onus', 4),
                    'traffic_scenario': self.config.get('traffic_scenario', 'residential_medium'),
                    'episode_duration': self.config.get('episode_duration', 1.0),
                    'simulation_timestep': self.config.get('simulation_timestep', 0.0005)
                }

            # Crear Smart RL DBA Algorithm
            self.smart_rl_algorithm = SmartRLDBAAlgorithm(model_path)
            self.smart_rl_algorithm.set_environment_params(env_params)

            # Verificar que se cargó correctamente
            if self.smart_rl_algorithm.agent is None:
                self.smart_rl_algorithm = None
                return False, f"Error cargando modelo: {model_path}"

            self.loaded_model_path = model_path
            self._log_event("RL_MODEL", f"Modelo RL cargado: {model_path}")

            return True, f"Modelo RL cargado exitosamente: {model_path}"

        except Exception as e:
            error_msg = f"Error cargando modelo RL: {str(e)}"
            self._log_event("ERROR", error_msg)
            self.smart_rl_algorithm = None
            self.loaded_model_path = None
            return False, error_msg

    def unload_rl_model(self):
        """Descargar modelo RL actual"""
        if self.smart_rl_algorithm:
            self.smart_rl_algorithm.cleanup()
            self.smart_rl_algorithm = None
            self.loaded_model_path = None
            self._log_event("RL_MODEL", "Modelo RL descargado")
            return True, "Modelo RL descargado exitosamente"
        else:
            return False, "No hay modelo RL cargado"

    def get_rl_model_info(self):
        """Obtener información del modelo RL actual"""
        if self.smart_rl_algorithm:
            return self.smart_rl_algorithm.get_statistics()
        else:
            return None

    def is_smart_rl_available(self):
        """Verificar si Smart RL DBA está disponible"""
        return self.smart_rl_algorithm is not None

    # ===== INCREMENTAL DATA WRITING =====

    def enable_incremental_data_writing(self, session_dir: str) -> bool:
        """
        Habilitar escritura incremental de datos durante la simulación

        Args:
            session_dir: Directorio donde guardar los datos

        Returns:
            True si se habilitó correctamente
        """
        try:
            from ..simulation.incremental_data_writer import IncrementalDataWriter

            # Crear escritor incremental
            self.incremental_writer = IncrementalDataWriter(session_dir, use_compression=True)

            # Iniciar escritura
            if not self.incremental_writer.start_writing():
                self._log_event("ERROR", "No se pudo iniciar escritura incremental")
                return False

            # Iniciar secciones
            self.incremental_writer.start_section('buffer_snapshots')
            self.incremental_writer.start_section('transmission_log')

            # Habilitar en componentes del simulador
            if self.simulator:
                print(f"✅ Simulador encontrado: {type(self.simulator).__name__}")
                olt = self.get_olt()
                if olt:
                    print(f"✅ OLT encontrado: {type(olt).__name__}")
                    olt.enable_incremental_writing(self.incremental_writer)

                    # Habilitar también en slot_manager del OLT
                    if hasattr(olt, 'slot_manager'):
                        print(f"✅ slot_manager encontrado en OLT")
                        olt.slot_manager.enable_incremental_writing(self.incremental_writer)
                        self._log_event("INCREMENTAL_WRITE", "Slot manager habilitado")
                    else:
                        print(f"⚠️ OLT no tiene slot_manager")
                else:
                    print(f"❌ No se pudo obtener OLT del simulador")
                    self._log_event("ERROR", "No se pudo obtener OLT del simulador")
            else:
                print(f"❌ No hay simulador disponible")
                self._log_event("ERROR", "No hay simulador para habilitar escritura incremental")

            self.incremental_writing_enabled = True
            self._log_event("INCREMENTAL_WRITE", f"Escritura incremental habilitada: {session_dir}")
            return True

        except Exception as e:
            self._log_event("ERROR", f"Error habilitando escritura incremental: {e}")
            return False

    def finalize_incremental_data_writing(self) -> str:
        """
        Finalizar escritura incremental y guardar metadata

        Returns:
            Ruta del archivo final, o None si hubo error
        """
        if not self.incremental_writing_enabled or not self.incremental_writer:
            print("⚠️ Escritura incremental no estaba habilitada")
            return None

        try:
            print("🔄 Cerrando secciones del JSON...")

            # Cerrar secciones
            self.incremental_writer.close_section('buffer_snapshots')
            self.incremental_writer.close_section('transmission_log')

            print("📝 Recopilando metadata final...")

            # Escribir metadata final (simulation_summary, orchestrator_stats, etc.)
            # Recopilar cada sección con manejo de errores individual
            metadata = {}

            try:
                print("  - Obteniendo simulation_summary...")
                metadata['simulation_summary'] = self.get_simulation_summary()
            except Exception as e:
                print(f"  ⚠️ Error obteniendo simulation_summary: {e}")
                metadata['simulation_summary'] = {}

            try:
                print("  - Obteniendo current_state...")
                metadata['current_state'] = self.get_current_state()
            except Exception as e:
                print(f"  ⚠️ Error obteniendo current_state: {e}")
                metadata['current_state'] = {}

            try:
                print("  - Obteniendo orchestrator_stats...")
                metadata['orchestrator_stats'] = self.get_orchestrator_stats()
            except Exception as e:
                print(f"  ⚠️ Error obteniendo orchestrator_stats: {e}")
                metadata['orchestrator_stats'] = {}

            try:
                print("  - Obteniendo olt_stats...")
                metadata['olt_stats'] = self._get_olt_stats_without_large_arrays()
            except Exception as e:
                print(f"  ⚠️ Error obteniendo olt_stats: {e}")
                metadata['olt_stats'] = {}

            print(f"💾 Escribiendo metadata ({len(metadata)} secciones)...")
            self.incremental_writer.write_metadata(metadata)

            print("🏁 Finalizando archivo JSON...")
            # Finalizar y obtener ruta del archivo
            final_file = self.incremental_writer.finalize()

            # Deshabilitar escritura incremental en componentes
            if self.simulator:
                olt = self.get_olt()
                if olt:
                    olt.disable_incremental_writing()

                    # Deshabilitar también en slot_manager
                    if hasattr(olt, 'slot_manager'):
                        olt.slot_manager.disable_incremental_writing()

            self.incremental_writing_enabled = False
            self._log_event("INCREMENTAL_WRITE", f"Escritura incremental finalizada: {final_file}")

            return final_file

        except Exception as e:
            self._log_event("ERROR", f"Error finalizando escritura incremental: {e}")
            if self.incremental_writer:
                self.incremental_writer.abort()
            return None

    def _get_olt_stats_without_large_arrays(self) -> dict:
        """
        Obtener estadísticas de OLT sin arrays grandes (ya escritos incrementalmente)
        """
        olt = self.get_olt()
        if not olt:
            return {}

        # Obtener estadísticas básicas sin buffer_snapshots
        stats = {
            'cycles_executed': olt.stats.get('cycles_executed', 0),
            'reports_collected': olt.stats.get('reports_collected', 0),
            'grants_assigned': olt.stats.get('grants_assigned', 0),
            'total_grants_bytes': olt.stats.get('total_grants_bytes', 0),
            'successful_transmissions': olt.stats.get('successful_transmissions', 0),
            'failed_transmissions': olt.stats.get('failed_transmissions', 0),
            'channel_utilization_samples': olt.stats.get('channel_utilization_samples', [])
        }

        # Agregar info de transmission_log sin los datos (ya escritos)
        if hasattr(olt, 'slot_manager'):
            stats['transmission_log_count'] = len(olt.slot_manager.transmission_log)
            stats['buffer_snapshots_count'] = len(olt.buffer_snapshots)
        else:
            stats['transmission_log_count'] = 0
            stats['buffer_snapshots_count'] = len(olt.buffer_snapshots)

        return {'olt_stats': stats}

    def get_incremental_writing_statistics(self) -> dict:
        """
        Obtener estadísticas de escritura incremental en tiempo real

        Returns:
            Diccionario con estadísticas o vacío si no está habilitada
        """
        if self.incremental_writing_enabled and self.incremental_writer:
            return self.incremental_writer.get_statistics()
        return {}

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
        
        # Limpiar Smart RL DBA
        if self.smart_rl_algorithm:
            self.smart_rl_algorithm.cleanup()
            self.smart_rl_algorithm = None

        self.log_callback = None
        self.last_simulation_results = None
        
        self._log_event("CLEANUP", "Adaptador PON limpiado completamente")