"""
Simulation Manager
Gestor de simulaciones con modelos RL entrenados
"""

import os
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from .rl_adapter import RLAdapter
from .environment_bridge import EnvironmentBridge


class SimulationManager(QObject):
    """
    Gestor para ejecutar simulaciones usando modelos RL pre-entrenados
    """

    # Señales
    simulation_started = pyqtSignal(dict)       # Simulación iniciada
    simulation_progress = pyqtSignal(dict)      # Progreso de simulación
    simulation_completed = pyqtSignal(dict)     # Simulación completada con resultados
    simulation_stopped = pyqtSignal()           # Simulación detenida
    error_occurred = pyqtSignal(str)            # Error durante simulación
    agent_decision = pyqtSignal(dict)           # Decisión del agente RL

    def __init__(self, parent=None):
        super().__init__(parent)

        # Componentes principales
        self.rl_adapter = RLAdapter(self)
        self.env_bridge = EnvironmentBridge(self)

        # Estado de simulación
        self.is_simulating = False
        self.current_simulation_id = None
        self.loaded_model = None
        self.simulation_thread = None

        # Configuración de simulación
        self.simulation_config = {}
        self.simulation_metrics = []

        # Historial de métricas reales para gráficos
        self.real_metrics_history = {
            'delays': [],
            'throughputs': [],
            'buffer_levels_history': [],
            'network_utilization_history': []
        }


    def load_model_for_simulation(self, model_path: str) -> bool:
        """
        Cargar modelo pre-entrenado para simulación

        Args:
            model_path: Ruta del modelo a cargar

        Returns:
            True si se cargó exitosamente
        """
        try:
            # Verificar que el archivo existe
            if not os.path.exists(model_path):
                self.error_occurred.emit(f"Modelo no encontrado: {model_path}")
                return False

            # Cargar modelo usando el adapter
            if self.rl_adapter.load_model(model_path):
                self.loaded_model = self.rl_adapter.model
                return True
            else:
                self.error_occurred.emit("Error cargando modelo para simulación")
                return False

        except Exception as e:
            error_msg = f"Error cargando modelo: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def start_simulation(self, params: Dict[str, Any], canvas=None) -> bool:
        """
        Iniciar simulación con modelo RL

        Args:
            params: Parámetros de simulación
            canvas: Referencia al canvas de PonLab (opcional)

        Returns:
            True si la simulación se inició exitosamente
        """
        try:
            if self.is_simulating:
                print("WARNING: Simulacion ya esta en progreso")
                return False

            if not self.loaded_model:
                self.error_occurred.emit("No hay modelo cargado")
                return False


            # Generar ID de simulación
            self.current_simulation_id = self._generate_simulation_id()
            self.simulation_config = params.copy()
            self.simulation_metrics.clear()

            # Configurar entorno si no existe
            if not self.rl_adapter.env:
                env_params = {
                    'num_onus': params.get('num_onus', 4),
                    'traffic_scenario': params.get('traffic_scenario', 'residential_medium'),
                    'episode_duration': params.get('duration', 10.0),
                    'simulation_timestep': params.get('simulation_timestep', 0.0005)
                }

                if not self.rl_adapter.create_environment(env_params):
                    self.error_occurred.emit("Error creando entorno de simulación")
                    return False

            # Configurar canvas si se proporciona
            if canvas:
                self.env_bridge.set_canvas_reference(canvas)

            # Crear y iniciar hilo de simulación
            self.simulation_thread = SimulationThread(
                self.loaded_model,
                self.rl_adapter.env,
                params,
                self
            )

            # Conectar señales
            self.simulation_thread.progress_updated.connect(self._on_simulation_progress)
            self.simulation_thread.simulation_completed.connect(self._on_simulation_completed)
            self.simulation_thread.simulation_error.connect(self._on_simulation_error)
            self.simulation_thread.agent_decision_made.connect(self._on_agent_decision)

            # Iniciar simulación
            self.is_simulating = True
            self.simulation_thread.start()

            # Emitir señal de inicio
            start_info = {
                'simulation_id': self.current_simulation_id,
                'start_time': datetime.now().isoformat(),
                'config': self.simulation_config
            }

            self.simulation_started.emit(start_info)

            return True

        except Exception as e:
            error_msg = f"Error iniciando simulación: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def stop_simulation(self) -> bool:
        """
        Detener simulación en curso

        Returns:
            True si se detuvo exitosamente
        """
        try:
            if not self.is_simulating:
                return False


            # Detener hilo de simulación
            if self.simulation_thread and self.simulation_thread.isRunning():
                self.simulation_thread.stop()
                self.simulation_thread.wait()

            # Actualizar estado
            self.is_simulating = False
            self.current_simulation_id = None

            self.simulation_stopped.emit()

            return True

        except Exception as e:
            error_msg = f"Error deteniendo simulación: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def get_simulation_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de la simulación

        Returns:
            Diccionario con información de estado
        """
        return {
            'is_simulating': self.is_simulating,
            'simulation_id': self.current_simulation_id,
            'has_loaded_model': self.loaded_model is not None,
            'metrics_count': len(self.simulation_metrics),
            'configuration': self.simulation_config.copy()
        }

    def _generate_simulation_id(self) -> str:
        """Generar ID único para la simulación"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ponlab_sim_{timestamp}"

    def _on_simulation_progress(self, progress_data: Dict[str, Any]):
        """Callback para progreso de simulación"""
        try:
            # Usar métricas directamente (sin converter externo)
            converted_metrics = progress_data

            # Agregar información de simulación
            converted_metrics.update({
                'simulation_id': self.current_simulation_id,
                'timestamp': datetime.now().isoformat()
            })

            # Agregar al historial
            self.simulation_metrics.append(converted_metrics)

            # Capturar métricas reales del entorno si están disponibles
            self._capture_real_metrics(progress_data)

            # Emitir progreso
            self.simulation_progress.emit(converted_metrics)

        except Exception as e:
            print(f"ERROR procesando progreso: {e}")

    def _on_simulation_completed(self, results: Dict[str, Any]):
        """Callback cuando se completa la simulación"""
        try:
            self.is_simulating = False

            # Agregar información de finalización a los resultados
            final_results = results.copy()
            final_results.update({
                'simulation_id': self.current_simulation_id,
                'end_time': datetime.now().isoformat(),
                'total_metrics': len(self.simulation_metrics),
                'configuration': self.simulation_config,
                'real_metrics_history': self.real_metrics_history.copy()
            })

            # Guardar métricas si está configurado
            if self.simulation_config.get('save_metrics', False):
                self._save_simulation_metrics(final_results)

            self.simulation_completed.emit(final_results)

        except Exception as e:
            print(f"ERROR completando simulacion: {e}")

    def _on_simulation_error(self, error_msg: str):
        """Callback para errores de simulación"""
        self.is_simulating = False
        self.error_occurred.emit(error_msg)
        print(f"ERROR en simulacion: {error_msg}")

    def _on_agent_decision(self, decision_data: Dict[str, Any]):
        """Callback cuando el agente toma una decisión"""
        try:
            # Agregar información de contexto
            decision_with_context = decision_data.copy()
            decision_with_context.update({
                'simulation_id': self.current_simulation_id,
                'timestamp': datetime.now().isoformat()
            })

            self.agent_decision.emit(decision_with_context)

        except Exception as e:
            print(f"ERROR procesando decision del agente: {e}")

    def _save_simulation_metrics(self, results: Dict[str, Any]):
        """Guardar métricas de simulación en archivo"""
        try:
            import json

            # Crear directorio de resultados
            results_dir = os.path.join(os.getcwd(), "results", "simulations")
            os.makedirs(results_dir, exist_ok=True)

            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_results_{timestamp}.json"
            filepath = os.path.join(results_dir, filename)

            # Guardar resultados
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)


        except Exception as e:
            print(f"WARNING: Error guardando metricas: {e}")

    def cleanup(self):
        """Limpiar recursos del manager"""
        try:
            # Detener simulación si está activa
            if self.is_simulating:
                self.stop_simulation()

            # Limpiar componentes
            self.rl_adapter.cleanup()
            self.env_bridge.clear_mapping()

            # Limpiar estado
            self.loaded_model = None
            self.simulation_metrics.clear()

            # Limpiar historial de métricas reales
            for key in self.real_metrics_history:
                self.real_metrics_history[key].clear()

        except Exception as e:
            print(f"WARNING: Error durante cleanup: {e}")

    def _capture_real_metrics(self, progress_data: Dict[str, Any]):
        """Capturar métricas reales del entorno RL durante la simulación"""
        try:
            step_count = progress_data.get('step_count', 0)
            timestamp = progress_data.get('elapsed_time', 0)

            # Debug: mostrar información disponible cada 1000 pasos
            if step_count % 1000 == 0:
                self._debug_available_metrics(progress_data)

            # Intentar obtener métricas reales del entorno RL
            if hasattr(self, 'rl_adapter') and self.rl_adapter and self.rl_adapter.env:
                env = self.rl_adapter.env

                # Explorar qué métodos/atributos tiene el entorno
                if step_count % 1000 == 0:  # Debug cada 1000 pasos
                    self._debug_env_capabilities(env)

                # Capturar métricas de delay si está disponible
                if hasattr(env, 'get_current_delay'):
                    try:
                        current_delay = env.get_current_delay()
                        self.real_metrics_history['delays'].append({
                            'step': step_count,
                            'value': current_delay,
                            'timestamp': timestamp
                        })
                    except Exception as e:
                        print(f"WARNING: Error capturando delay: {e}")

                # Capturar métricas de throughput si está disponible
                if hasattr(env, 'get_current_throughput'):
                    try:
                        current_throughput = env.get_current_throughput()
                        self.real_metrics_history['throughputs'].append({
                            'step': step_count,
                            'value': current_throughput,
                            'timestamp': timestamp,
                            'tcont_id': 'mixed'
                        })
                    except Exception as e:
                        print(f"WARNING: Error capturando throughput: {e}")

                # Capturar niveles de buffer de ONUs si está disponible
                if hasattr(env, 'get_buffer_levels'):
                    try:
                        buffer_levels = env.get_buffer_levels()
                        if buffer_levels:
                            buffer_step = {}
                            for onu_id, level_data in buffer_levels.items():
                                if isinstance(level_data, dict):
                                    buffer_step[f'ONU_{onu_id}'] = level_data
                                else:
                                    buffer_step[f'ONU_{onu_id}'] = {
                                        'utilization_percent': level_data,
                                        'used_mb': level_data * 3.5 / 100,
                                        'capacity_mb': 3.5
                                    }

                            if buffer_step:
                                self.real_metrics_history['buffer_levels_history'].append(buffer_step)
                    except Exception as e:
                        print(f"WARNING: Error capturando buffer levels: {e}")

                # Intentar acceder al simulador interno para obtener métricas
                if hasattr(env, 'getSimulator'):
                    try:
                        self._capture_from_simulator(env.getSimulator(), step_count, timestamp)
                    except Exception as e:
                        print(f"WARNING: Error capturando desde simulador: {e}")

                # Si el entorno no tiene métodos específicos, intentar extraer del info general
                env_info = progress_data.get('env_info')
                if env_info:
                    try:
                        self._extract_metrics_from_info(env_info, step_count, timestamp)
                    except Exception as e:
                        print(f"WARNING: Error extrayendo métricas de info: {e}")

        except Exception as e:
            print(f"WARNING: Error capturando métricas reales: {e}")

    def _debug_available_metrics(self, progress_data: Dict[str, Any]):
        """Debug: mostrar qué datos están disponibles"""
        print(f"DEBUG: Datos disponibles en step {progress_data.get('step_count', 0)}:")
        for key, value in progress_data.items():
            if key == 'env_info' and value:
                print(f"  env_info: {list(value.keys()) if isinstance(value, dict) else type(value)}")
                if isinstance(value, dict):
                    for info_key, info_value in value.items():
                        print(f"    {info_key}: {type(info_value)} = {info_value}")
            else:
                print(f"  {key}: {type(value)}")

    def _debug_env_capabilities(self, env):
        """Debug: mostrar qué métodos/atributos tiene el entorno"""
        print(f"DEBUG: Capacidades del entorno:")

        # Métodos relacionados con métricas
        metric_methods = [
            'get_current_delay', 'get_current_throughput', 'get_buffer_levels',
            'get_network_utilization', 'getSimulator', 'get_metrics', 'get_stats'
        ]

        for method in metric_methods:
            if hasattr(env, method):
                print(f"  ✅ {method}: disponible")
            else:
                print(f"  ❌ {method}: no disponible")

        # Verificar si tiene atributos útiles
        useful_attrs = ['simulator', 'last_info', 'metrics', 'stats', 'observation']
        for attr in useful_attrs:
            if hasattr(env, attr):
                print(f"  ✅ {attr}: disponible")

    def _capture_from_simulator(self, simulator, step_count: int, timestamp: float):
        """Intentar capturar métricas del simulador netPONpy"""
        try:
            # Verificar si el simulador tiene métodos para obtener métricas
            if hasattr(simulator, 'get_statistics'):
                try:
                    stats = simulator.get_statistics()
                    if stats:
                        self._process_simulator_stats(stats, step_count, timestamp)
                except Exception as e:
                    print(f"WARNING: Error obteniendo estadísticas del simulador: {e}")

            # Intentar obtener estado de las ONUs
            if hasattr(simulator, 'get_onus_state'):
                try:
                    onus_state = simulator.get_onus_state()
                    if onus_state:
                        self._process_onus_state(onus_state, step_count, timestamp)
                except Exception as e:
                    print(f"WARNING: Error obteniendo estado ONUs: {e}")

        except Exception as e:
            print(f"WARNING: Error general capturando desde simulador: {e}")

    def _process_simulator_stats(self, stats, step_count: int, timestamp: float):
        """Procesar estadísticas del simulador"""
        try:
            if isinstance(stats, dict):
                # Buscar métricas conocidas en las estadísticas
                if 'average_delay' in stats:
                    self.real_metrics_history['delays'].append({
                        'step': step_count,
                        'value': stats['average_delay'],
                        'timestamp': timestamp
                    })

                if 'throughput' in stats:
                    self.real_metrics_history['throughputs'].append({
                        'step': step_count,
                        'value': stats['throughput'],
                        'timestamp': timestamp,
                        'tcont_id': 'simulator'
                    })

        except Exception as e:
            print(f"WARNING: Error procesando stats del simulador: {e}")

    def _process_onus_state(self, onus_state, step_count: int, timestamp: float):
        """Procesar estado de las ONUs"""
        try:
            if isinstance(onus_state, dict):
                buffer_step = {}
                for onu_id, onu_data in onus_state.items():
                    if isinstance(onu_data, dict) and 'buffer_level' in onu_data:
                        buffer_level = onu_data['buffer_level']
                        buffer_step[f'ONU_{onu_id}'] = {
                            'utilization_percent': buffer_level * 100 if buffer_level <= 1 else buffer_level,
                            'used_mb': buffer_level * 3.5 if buffer_level <= 1 else (buffer_level / 100) * 3.5,
                            'capacity_mb': 3.5
                        }

                if buffer_step:
                    self.real_metrics_history['buffer_levels_history'].append(buffer_step)

        except Exception as e:
            print(f"WARNING: Error procesando estado ONUs: {e}")

    def _extract_metrics_from_info(self, info_dict: Dict[str, Any], step_count: int, timestamp: float):
        """Extraer métricas del diccionario info del entorno"""
        try:
            # Buscar delay en diferentes posibles ubicaciones
            delay_keys = ['delay', 'average_delay', 'mean_delay', 'current_delay']
            for key in delay_keys:
                if key in info_dict:
                    self.real_metrics_history['delays'].append({
                        'step': step_count,
                        'value': info_dict[key],
                        'timestamp': timestamp
                    })
                    break

            # Buscar throughput
            throughput_keys = ['throughput', 'average_throughput', 'mean_throughput', 'current_throughput']
            for key in throughput_keys:
                if key in info_dict:
                    self.real_metrics_history['throughputs'].append({
                        'step': step_count,
                        'value': info_dict[key],
                        'timestamp': timestamp,
                        'tcont_id': 'mixed'
                    })
                    break

            # Buscar buffer levels
            buffer_keys = ['buffer_levels', 'onu_buffers', 'queue_levels']
            for key in buffer_keys:
                if key in info_dict and isinstance(info_dict[key], dict):
                    buffer_step = {}
                    for onu_id, level in info_dict[key].items():
                        buffer_step[f'ONU_{onu_id}'] = {
                            'utilization_percent': level if level <= 1 else level,
                            'used_mb': (level if level <= 1 else level/100) * 3.5,
                            'capacity_mb': 3.5
                        }

                    if buffer_step:
                        self.real_metrics_history['buffer_levels_history'].append(buffer_step)
                    break

        except Exception as e:
            print(f"WARNING: Error extrayendo métricas de info: {e}")


class SimulationThread(QThread):
    """Hilo para ejecutar simulación RL sin bloquear la UI"""

    progress_updated = pyqtSignal(dict)
    simulation_completed = pyqtSignal(dict)
    simulation_error = pyqtSignal(str)
    agent_decision_made = pyqtSignal(dict)

    def __init__(self, model, env, params, parent=None):
        super().__init__(parent)
        self.model = model
        self.env = env
        self.params = params
        self._stop_requested = False

    def run(self):
        """Ejecutar simulación"""
        try:
            duration = self.params.get('duration', 10.0)
            show_decisions = self.params.get('show_decisions', True)

            start_time = time.time()
            step_count = 0
            decisions_count = 0
            total_reward = 0.0


            # Resetear entorno - manejar tanto Gym API antigua como nueva
            try:
                # Intentar Gym API nueva (devuelve obs, info)
                reset_result = self.env.reset()
                if isinstance(reset_result, tuple):
                    obs, info = reset_result
                else:
                    obs = reset_result
            except:
                # Fallback a API antigua
                obs = self.env.reset()

            while not self._stop_requested:
                # Verificar tiempo transcurrido
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    break

                # Obtener acción del modelo - asegurar que obs es numpy array
                if isinstance(obs, tuple):
                    obs = obs[0]  # Extraer solo las observaciones si es tupla

                # Manejar diferentes tipos de modelo
                if hasattr(self.model, 'predict'):
                    # Modelo real de stable-baselines3
                    action, _ = self.model.predict(obs, deterministic=True)
                elif isinstance(self.model, dict) and 'smart_rl_algorithm' in self.model:
                    # Modelo Smart RL
                    smart_algorithm = self.model['smart_rl_algorithm']
                    # Verificar si tiene modelo interno de stable-baselines3
                    if hasattr(smart_algorithm, 'model') and smart_algorithm.model is not None:
                        action, _ = smart_algorithm.model.predict(obs, deterministic=True)
                    else:
                        # Fallback si no hay modelo cargado
                        action_space_size = self.env.action_space.shape[0] if hasattr(self.env, 'action_space') else 4
                        action = np.random.uniform(0, 1, action_space_size)
                        action = action / np.sum(action)  # Normalizar
                else:
                    # Fallback - acción aleatoria
                    action_space_size = self.env.action_space.shape[0] if hasattr(self.env, 'action_space') else 4
                    action = np.random.uniform(0, 1, action_space_size)
                    action = action / np.sum(action)  # Normalizar

                # Ejecutar acción en el entorno - manejar ambas APIs
                try:
                    # Intentar Gym API nueva
                    step_result = self.env.step(action)
                    if len(step_result) == 5:  # obs, reward, terminated, truncated, info
                        obs, reward, terminated, truncated, info = step_result
                        done = terminated or truncated
                    else:  # obs, reward, done, info
                        obs, reward, done, info = step_result
                except:
                    # Fallback a API antigua
                    obs, reward, done, info = self.env.step(action)

                step_count += 1
                decisions_count += 1
                total_reward += reward

                # Emitir decisión del agente si está habilitado
                if show_decisions and decisions_count % 10 == 0:  # Cada 10 decisiones
                    decision_data = {
                        'step': step_count,
                        'action': action.tolist() if hasattr(action, 'tolist') else action,
                        'reward': float(reward),
                        'observations': obs.tolist() if hasattr(obs, 'tolist') else obs
                    }
                    self.agent_decision_made.emit(decision_data)

                # Emitir progreso cada 100 pasos
                if step_count % 100 == 0:
                    progress_data = {
                        'elapsed_time': elapsed,
                        'progress_percent': min(100, (elapsed / duration) * 100),
                        'step_count': step_count,
                        'decisions_count': decisions_count,
                        'average_reward': total_reward / step_count,
                        'current_reward': float(reward),
                        'total_reward': total_reward,
                        'env_info': info  # Incluir info del entorno para captura de métricas
                    }
                    self.progress_updated.emit(progress_data)

                # Resetear si el episodio terminó
                if done:
                    try:
                        reset_result = self.env.reset()
                        if isinstance(reset_result, tuple):
                            obs, info = reset_result
                        else:
                            obs = reset_result
                    except:
                        obs = self.env.reset()

                # Pequeña pausa para no saturar
                time.sleep(0.001)

            # Resultados finales
            if not self._stop_requested:
                final_results = {
                    'total_duration': time.time() - start_time,
                    'total_steps': step_count,
                    'total_decisions': decisions_count,
                    'total_reward': total_reward,
                    'average_reward': total_reward / max(step_count, 1),
                    'steps_per_second': step_count / (time.time() - start_time)
                }
                self.simulation_completed.emit(final_results)

        except Exception as e:
            self.simulation_error.emit(str(e))

    def stop(self):
        """Solicitar detener simulación"""
        self._stop_requested = True