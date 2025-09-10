"""
Integrated NetPONPy Adapter
Adaptador completamente integrado que usa las clases PON nativas de PonLab
"""

# Importar clases integradas directamente del core de PonLab
try:
    from .pon_orchestrator import PONOrchestrator
    from .pon_dba_interface import (
        FCFSDBAAlgorithm, 
        PriorityDBAAlgorithm, 
        RLDBAAlgorithm
    )
    from .pon_netsim_realistic import RealisticNetSim, EventEvaluator as RealisticEventEvaluator
    from .traffic_scenarios import get_available_scenarios, print_scenario_info
    PONCORE_AVAILABLE = True
    print("OK PON Core integrado correctamente")
except ImportError as e:
    print(f"ERROR importando PON Core integrado: {e}")
    PONCORE_AVAILABLE = False


class IntegratedPONAdapter:
    """Adaptador completamente integrado para PON usando clases nativas de PonLab"""
    
    def __init__(self):
        self.orchestrator = None
        self.realistic_netsim = None
        self.is_available = PONCORE_AVAILABLE
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
        
    def is_pon_available(self):
        """Verificar si el core PON está disponible"""
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
            return False, "PON Core no está disponible"
            
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
            
            # Crear simulador realista
            self.realistic_netsim = RealisticNetSim(self.orchestrator.olt)
            
            print(f"PONOrchestrator integrado inicializado con {num_onus} ONUs desde topologia")
            self._log_event("INIT", f"Orquestador integrado inicializado con {num_onus} ONUs")
            return True, f"Orquestador integrado inicializado con {num_onus} ONUs"
            
        except Exception as e:
            print(f"ERROR inicializando orquestador integrado: {e}")
            return False, f"Error: {str(e)}"
    
    def initialize_orchestrator(self, num_onus=4):
        """Inicializar el orquestador integrado (método legacy)"""
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
            
            # Crear simulador realista
            self.realistic_netsim = RealisticNetSim(self.orchestrator.olt)
            
            print(f"PONOrchestrator integrado inicializado con {num_onus} ONUs")
            self._log_event("INIT", f"Orquestador integrado inicializado con {num_onus} ONUs")
            return True
            
        except Exception as e:
            print(f"ERROR inicializando orquestador integrado: {e}")
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
                print(f"ERROR Algoritmo desconocido: {algorithm_name}")
                return False
                
            self.orchestrator.set_dba_algorithm(algorithm)
            self.current_algorithm = algorithm_name
            print(f"OK Algoritmo DBA integrado configurado: {algorithm_name}")
            self._log_event("DBA", f"Algoritmo configurado: {algorithm_name}")
            return True
            
        except Exception as e:
            print(f"ERROR configurando algoritmo DBA: {e}")
            return False
            
    def start_simulation(self):
        """Iniciar simulación"""
        if not self.orchestrator:
            print("ERROR Orquestador no inicializado")
            return False
            
        try:
            # Resetear orquestador
            self.orchestrator.reset()
            print("Simulacion PON integrada iniciada")
            self._log_event("START", "Simulación iniciada")
            return True
            
        except Exception as e:
            print(f"ERROR iniciando simulacion: {e}")
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
            print(f"ERROR en paso de simulacion: {e}")
            return None
    
    def run_netsim_simulation(self, timesteps=1000, callback=None):
        """Ejecutar simulación PON realista con ciclos DBA"""
        print(f"🚀 EJECUTANDO SIMULACION PON REALISTA con {timesteps} ciclos")
        print(f"📊 DEBUG: Adaptador inicializado - realistic_netsim existe: {self.realistic_netsim is not None}")
        
        if not self.realistic_netsim:
            print("❌ ERROR: Simulador PON realista no inicializado")
            return False
            
        print(f"✅ Simulador realista OK - ejecutando {timesteps} ciclos...")
            
        return self.run_realistic_simulation(timesteps, callback)
    
    def run_realistic_simulation(self, timesteps=1000, callback=None):
        """Ejecutar simulación realista con ciclos DBA"""
        if not self.realistic_netsim:
            print("ERROR RealisticNetSim no inicializado")
            return False
            
        try:
            # Crear callback de eventos si se proporciona
            event_evaluator = None
            if callback:
                print("🔧 DEBUG: Creando callback evaluator para UI")
                class RealisticCallbackEvaluator(RealisticEventEvaluator):
                    def __init__(self, cb):
                        self.callback = cb
                        print("🔧 DEBUG: RealisticCallbackEvaluator inicializado")
                    
                    def on_init(self):
                        print("🔧 DEBUG: on_init llamado - enviando callback a UI")
                        self.callback("init", {})
                    
                    def on_cycle_start(self, cycle_number: int, cycle_time: float):
                        print(f"🔧 DEBUG: on_cycle_start ciclo {cycle_number}")
                        self.callback("update", {
                            'cycle': cycle_number,
                            'time': cycle_time,
                            'status': 'cycle_start'
                        })
                    
                    def on_cycle_end(self, dba_result):
                        print(f"🔧 DEBUG: on_cycle_end ciclo {dba_result.cycle_number}, requests: {dba_result.total_requests_processed}")
                        self.callback("update", {
                            'cycle': dba_result.cycle_number,
                            'time': dba_result.cycle_start_time,
                            'requests_processed': dba_result.total_requests_processed,
                            'bandwidth_used': dba_result.total_bandwidth_used,
                            'status': 'cycle_end'
                        })
                    
                    def on_simulation_end(self, attributes):
                        print(f"🔧 DEBUG: on_simulation_end - enviando datos finales a UI")
                        print(f"🔧 DEBUG: attributes keys: {list(attributes.keys()) if attributes else 'None'}")
                        self.callback("end", attributes)
                
                event_evaluator = RealisticCallbackEvaluator(callback)
            else:
                print("⚠️ DEBUG: No hay callback de UI - simulación sin feedback")
            
            print(f"Iniciando simulacion PON realista: {timesteps} ciclos DBA")
            self._log_event("REALISTIC", f"Iniciando simulación realista de {timesteps} ciclos")
            
            # Ejecutar simulación realista
            self.realistic_netsim.run_cycles(timesteps, event_evaluator)
            
            # DEBUG: Verificar datos post-simulación
            print(f"🔍 DEBUG: Post-simulación - verificando datos:")
            print(f"   - Cycles executed: {self.realistic_netsim.cycles_executed}")
            print(f"   - Requests processed: {self.realistic_netsim.total_requests_processed}")
            print(f"   - Successful transmissions: {self.realistic_netsim.successful_transmissions}")
            print(f"   - Simulation time: {self.realistic_netsim.simulation_time}")
            
            print("✅ Simulacion PON realista completada")
            self._log_event("REALISTIC", "Simulación realista completada")
            return True
            
        except Exception as e:
            print(f"ERROR en simulacion realista: {e}")
            return False
    
    def run_realistic_time_simulation(self, simulation_time=10.0, callback=None):
        """Ejecutar simulación realista por tiempo específico"""
        if not self.realistic_netsim:
            print("ERROR RealisticNetSim no inicializado")
            return False
            
        try:
            # Crear callback de eventos si se proporciona
            event_evaluator = None
            if callback:
                class RealisticCallbackEvaluator(RealisticEventEvaluator):
                    def __init__(self, cb):
                        self.callback = cb
                    
                    def on_init(self):
                        self.callback("init", {})
                    
                    def on_cycle_end(self, dba_result):
                        self.callback("update", {
                            'cycle': dba_result.cycle_number,
                            'time': dba_result.cycle_start_time
                        })
                    
                    def on_simulation_end(self, attributes):
                        self.callback("end", attributes)
                
                event_evaluator = RealisticCallbackEvaluator(callback)
            
            print(f"Iniciando simulacion PON realista por tiempo: {simulation_time}s")
            self._log_event("REALISTIC", f"Iniciando simulación realista de {simulation_time}s")
            
            self.realistic_netsim.run_for_time(simulation_time, event_evaluator)
            
            print("OK Simulacion PON realista por tiempo completada")
            self._log_event("REALISTIC", "Simulación realista por tiempo completada")
            return True
            
        except Exception as e:
            print(f"ERROR en simulacion realista por tiempo: {e}")
            return False
    
    def run_time_simulation(self, simulation_time=10.0, callback=None):
        """Ejecutar simulación por tiempo específico"""
        if not self.netsim:
            print("ERROR NetSim no inicializado")
            return False
            
        try:
            # Crear callback de eventos si se proporciona
            event_evaluator = None
            if callback:
                class CallbackEvaluator(EventEvaluator):
                    def __init__(self, cb):
                        self.callback = cb
                    
                    def on_init(self):
                        self.callback("init", {})
                    
                    def on_update(self, attributes):
                        self.callback("update", attributes)
                    
                    def on_run_end(self, attributes):
                        self.callback("end", attributes)
                
                event_evaluator = CallbackEvaluator(callback)
            
            print(f"Iniciando simulacion NetSim por tiempo: {simulation_time}s")
            self._log_event("NETSIM", f"Iniciando simulación de {simulation_time}s")
            
            self.netsim.run_for_time(simulation_time, event_evaluator)
            
            print("OK Simulacion NetSim por tiempo completada")
            self._log_event("NETSIM", "Simulación por tiempo completada")
            return True
            
        except Exception as e:
            print(f"ERROR en simulacion NetSim por tiempo: {e}")
            return False
            
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
            print(f"ERROR obteniendo estado: {e}")
            return {}
    
    def get_simulation_summary(self):
        """Obtener resumen completo de la simulación realista"""
        print(f"DEBUG: get_simulation_summary llamado")
        
        if not self.realistic_netsim:
            print("ERROR DEBUG: realistic_netsim es None")
            return {}
            
        try:
            summary = self.realistic_netsim.get_simulation_summary()
            print(f"DEBUG: Datos obtenidos de realistic_netsim:")
            print(f"   - Keys principales: {list(summary.keys())}")
            print(f"   - Tiene simulation_summary: {'simulation_summary' in summary}")
            if 'simulation_summary' in summary:
                sim_summary = summary['simulation_summary']
                sim_stats = sim_summary.get('simulation_stats', {})
                perf_metrics = sim_summary.get('performance_metrics', {})
                episode_metrics = sim_summary.get('episode_metrics', {})
                
                print(f"   - Total steps: {sim_stats.get('total_steps', 'N/A')}")
                print(f"   - Total requests: {sim_stats.get('total_requests', 'N/A')}")
                print(f"   - Simulation time: {sim_stats.get('simulation_time', 'N/A')}")
                print(f"   - Success rate: {sim_stats.get('success_rate', 'N/A')}")
                print(f"   - Mean delay: {perf_metrics.get('mean_delay', 'N/A')}")
                print(f"   - Buffer history entries: {len(episode_metrics.get('buffer_levels_history', []))}")
                
                # Debug primera entrada de buffer si existe
                buffer_history = episode_metrics.get('buffer_levels_history', [])
                if buffer_history:
                    print(f"   - Primera entrada buffer: {buffer_history[0]}")
                    
            return summary
        except Exception as e:
            print(f"ERROR obteniendo resumen realista: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_orchestrator_stats(self):
        """Obtener estadísticas completas del orquestador"""
        if not self.orchestrator:
            return {}
            
        try:
            return self.orchestrator.get_orchestrator_stats()
        except Exception as e:
            print(f"ERROR obteniendo estadisticas: {e}")
            return {}
            
    def get_available_algorithms(self):
        """Obtener lista de algoritmos DBA disponibles"""
        return ["FCFS", "Priority", "RL-DBA"]
    
    def get_available_traffic_scenarios(self):
        """Obtener escenarios de tráfico disponibles"""
        return get_available_scenarios()
    
    def print_traffic_scenario_info(self, scenario_name):
        """Imprimir información de escenario de tráfico"""
        print_scenario_info(scenario_name)
        
    def cleanup(self):
        """Limpiar recursos"""
        if self.realistic_netsim:
            self.realistic_netsim.reset_simulation()
            self.realistic_netsim = None
        
        self.orchestrator = None
        self.log_callback = None
        print("Adaptador PON integrado limpiado")
        
    def get_simulation_mode(self) -> str:
        """Obtener modo de simulación actual"""
        return "realistic" if self.realistic_netsim else "none"