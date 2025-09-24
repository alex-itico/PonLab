"""
RL Adapter
Adaptador principal para conectar PonLab con netPONpy RL
"""

import sys
import os
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import numpy as np
from .topology_bridge import TopologyBridge
from .data_collector import RealTimeDataCollector

# Intentar importar netPONpy
try:
    # Agregar ruta de netPONpy al sys.path si no está
    netponpy_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'netPONPy')
    if os.path.exists(netponpy_path) and netponpy_path not in sys.path:
        sys.path.append(netponpy_path)
    
    from netPonPy.pon.pon_rl_env_v2 import create_pon_rl_env_v2
    from netPonPy.pon.interfaces.dba_algorithm_interface import RLDBAAlgorithm
    from stable_baselines3 import PPO, A2C, DQN, SAC
    
    NETPONPY_AVAILABLE = True
    print("[OK] netPONpy RL modules loaded successfully")
    
except ImportError as e:
    NETPONPY_AVAILABLE = False
    print(f"[WARNING] netPONpy RL modules not available: {e}")
    print("   Install dependencies: pip install gymnasium stable-baselines3 torch")


class RLAdapter(QObject):
    """Adaptador principal para la integración con netPONpy RL"""

    # Señales
    environment_created = pyqtSignal(object)  # Entorno RL creado
    training_progress = pyqtSignal(dict)      # Progreso de entrenamiento
    training_completed = pyqtSignal(object)   # Entrenamiento completado (modelo)
    training_error = pyqtSignal(str)          # Error en entrenamiento
    topology_loaded = pyqtSignal(dict)        # Topología cargada
    real_time_data = pyqtSignal(dict)         # Datos en tiempo real

    def __init__(self, parent=None):
        super().__init__(parent)
        self.env = None
        self.model = None
        self.training_thread = None
        self.is_training = False

        # Nuevos componentes integrados
        self.topology_bridge = TopologyBridge()
        self.data_collector = RealTimeDataCollector()
        self.canvas_widget = None

        # Conectar señales
        self.topology_bridge.topology_extracted.connect(self.topology_loaded.emit)
        self.data_collector.data_collected.connect(self.real_time_data.emit)
        
    @staticmethod
    def is_available():
        """Verificar si netPONpy RL está disponible"""
        return NETPONPY_AVAILABLE
    
    def setup_canvas_integration(self, canvas_widget):
        """Configurar integración con el canvas de PonLab"""
        try:
            self.canvas_widget = canvas_widget
            print("[OK] Canvas configurado para integración RL")
            return True
        except Exception as e:
            print(f"[ERROR] Error configurando canvas: {e}")
            return False

    def extract_topology_from_canvas(self) -> bool:
        """Extraer topología del canvas actual"""
        if not self.canvas_widget:
            self.training_error.emit("Canvas no configurado. Use setup_canvas_integration() primero.")
            return False

        try:
            topology = self.topology_bridge.extract_topology_from_canvas(self.canvas_widget)
            if topology:
                print(f"[OK] Topología extraída: {topology['num_onus']} ONUs")
                return True
            return False
        except Exception as e:
            error_msg = f"Error extrayendo topología: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.training_error.emit(error_msg)
            return False

    def create_environment(self, params: Dict[str, Any]) -> bool:
        """
        Crear entorno RL con los parámetros especificados
        
        Args:
            params: Diccionario con parámetros del entorno
            
        Returns:
            True si se creó exitosamente, False en caso contrario
        """
        if not NETPONPY_AVAILABLE:
            self.training_error.emit("netPONpy RL no está disponible. Instale las dependencias.")
            return False
        
        try:
            print(f"[RL] Creando entorno RL con parametros: {params}")

            # Usar topología del canvas si está disponible
            use_canvas_topology = params.get('use_canvas_topology', True)

            if use_canvas_topology and self.topology_bridge.current_topology:
                print("[RL] Usando topología del canvas")
                self.env = self.topology_bridge.create_rl_environment(
                    traffic_scenario=params.get('traffic_scenario', 'residential_medium'),
                    episode_duration=params.get('episode_duration', 1.0),
                    simulation_timestep=params.get('simulation_timestep', 0.0005)
                )
            else:
                print("[RL] Usando configuración por defecto")
                # Crear entorno usando netPONpy con parámetros por defecto
                self.env = create_pon_rl_env_v2(
                    num_onus=params.get('num_onus', 4),
                    traffic_scenario=params.get('traffic_scenario', 'residential_medium'),
                    episode_duration=params.get('episode_duration', 1.0),
                    simulation_timestep=params.get('simulation_timestep', 0.0005)
                )
            
            # Configurar algoritmo DBA RL
            rl_dba = RLDBAAlgorithm()
            self.env.getSimulator().set_dba_algorithm(rl_dba)
            
            # Iniciar entorno
            self.env.start(verbose=True)

            # Configurar data collector
            data_collection_success = self.data_collector.setup_environment(self.env)
            if data_collection_success:
                print("[OK] Data collector configurado")
            else:
                print("[WARNING] Data collector no se pudo configurar")

            print(f"[OK] Entorno RL creado exitosamente")
            print(f"   Observation space: {self.env.observation_space}")
            print(f"   Action space: {self.env.action_space}")

            self.environment_created.emit(self.env)
            return True
            
        except Exception as e:
            error_msg = f"Error creando entorno RL: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.training_error.emit(error_msg)
            return False
    
    def create_model(self, params: Dict[str, Any]) -> bool:
        """
        Crear modelo RL con los parámetros especificados
        
        Args:
            params: Diccionario con parámetros del modelo
            
        Returns:
            True si se creó exitosamente, False en caso contrario
        """
        if not NETPONPY_AVAILABLE or self.env is None:
            self.training_error.emit("Entorno RL no disponible")
            return False
        
        try:
            algorithm = params.get('algorithm', 'PPO')
            
            # Parámetros comunes
            common_params = {
                'env': self.env,
                'learning_rate': params.get('learning_rate', 3e-4),
                'verbose': 1
            }
            
            # Crear modelo según el algoritmo
            if algorithm == 'PPO':
                self.model = PPO(
                    "MlpPolicy",
                    **common_params,
                    n_steps=2048,
                    batch_size=params.get('batch_size', 64),
                    n_epochs=10,
                    gamma=params.get('gamma', 0.99)
                )
            elif algorithm == 'A2C':
                self.model = A2C(
                    "MlpPolicy",
                    **common_params,
                    n_steps=5,
                    gamma=params.get('gamma', 0.99)
                )
            elif algorithm == 'DQN':
                self.model = DQN(
                    "MlpPolicy",
                    **common_params,
                    buffer_size=10000,
                    gamma=params.get('gamma', 0.99)
                )
            elif algorithm == 'SAC':
                self.model = SAC(
                    "MlpPolicy",
                    **common_params,
                    gamma=params.get('gamma', 0.99)
                )
            else:
                raise ValueError(f"Algoritmo no soportado: {algorithm}")
            
            print(f"[OK] Modelo {algorithm} creado exitosamente")
            return True
            
        except Exception as e:
            error_msg = f"Error creando modelo RL: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.training_error.emit(error_msg)
            return False
    
    def start_training(self, params: Dict[str, Any]):
        """
        Iniciar entrenamiento en un hilo separado
        
        Args:
            params: Parámetros de entrenamiento
        """
        if self.is_training:
            print("[WARNING] Entrenamiento ya esta en progreso")
            return
        
        if not NETPONPY_AVAILABLE or self.model is None:
            self.training_error.emit("Modelo RL no disponible")
            return
        
        # Crear y iniciar hilo de entrenamiento
        self.training_thread = TrainingThread(self.model, params, self.data_collector)
        self.training_thread.progress_updated.connect(self.training_progress.emit)
        self.training_thread.training_completed.connect(self._on_training_completed)
        self.training_thread.training_error.connect(self.training_error.emit)
        
        self.is_training = True
        self.training_thread.start()
        
        print("[OK] Entrenamiento iniciado en hilo separado")
    
    def stop_training(self):
        """Detener entrenamiento"""
        if self.training_thread and self.training_thread.isRunning():
            self.training_thread.stop()
            self.training_thread.wait()
        
        self.is_training = False
        print("[OK] Entrenamiento detenido")
    
    def save_model(self, path: str) -> bool:
        """
        Guardar modelo entrenado
        
        Args:
            path: Ruta donde guardar el modelo
            
        Returns:
            True si se guardó exitosamente
        """
        if self.model is None:
            return False
        
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Guardar modelo
            self.model.save(path)
            print(f"[OK] Modelo guardado en: {path}")
            return True
            
        except Exception as e:
            error_msg = f"Error guardando modelo: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.training_error.emit(error_msg)
            return False
    
    def validate_model_topology_compatibility(self, model_path: str) -> bool:
        """Validar compatibilidad entre modelo y topología actual"""
        try:
            # Asegurar que la topología esté cargada
            if not self.topology_bridge.current_topology:
                print("[INFO] Extrayendo topología del canvas para validación...")
                if self.canvas_widget:
                    topology = self.topology_bridge.extract_topology_from_canvas(self.canvas_widget)
                    if not topology:
                        print("[WARNING] No se pudo extraer topología del canvas, usando configuración por defecto")
                        # Usar topología por defecto para validación
                        self.topology_bridge.current_topology = self.topology_bridge._get_default_topology()
                else:
                    print("[WARNING] No hay canvas configurado, usando topología por defecto")
                    # Usar topología por defecto para validación
                    self.topology_bridge.current_topology = self.topology_bridge._get_default_topology()

            # Intentar cargar metadata del modelo
            metadata_path = model_path.replace('.zip', '_metadata.json')
            model_metadata = {}

            if os.path.exists(metadata_path):
                import json
                with open(metadata_path, 'r') as f:
                    model_metadata = json.load(f)
            else:
                print("[WARNING] No se encontró metadata del modelo, validación limitada")
                # Si no hay metadata, permitir carga (compatibilidad hacia atrás)
                print("[INFO] Permitiendo carga de modelo sin metadata (compatibilidad hacia atrás)")
                return True

            # Validar compatibilidad
            is_compatible, message = self.topology_bridge.validate_topology_compatibility(model_metadata)

            if not is_compatible:
                self.training_error.emit(f"Modelo incompatible: {message}")
                return False

            print(f"[OK] Modelo compatible: {message}")
            return True

        except Exception as e:
            error_msg = f"Error validando compatibilidad del modelo: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.training_error.emit(error_msg)
            return False

    def load_model(self, path: str, skip_validation: bool = False) -> bool:
        """
        Cargar modelo entrenado
        
        Args:
            path: Ruta del modelo a cargar
            
        Returns:
            True si se cargó exitosamente
        """
        if not NETPONPY_AVAILABLE:
            return False
        
        try:
            # Validar compatibilidad con topología actual (opcional)
            if not skip_validation:
                if not self.validate_model_topology_compatibility(path):
                    print("[WARNING] Validación de topología falló, pero continuando carga...")
                    # No retornar False, solo advertir
            else:
                print("[INFO] Saltando validación de topología")

            # Detectar algoritmo por el nombre del archivo o metadata
            # Simplificado: usar PPO por defecto
            self.model = PPO.load(path)
            print(f"[OK] Modelo cargado desde: {path}")
            return True
            
        except Exception as e:
            error_msg = f"Error cargando modelo: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.training_error.emit(error_msg)
            return False

    def save_model_with_topology_metadata(self, path: str) -> bool:
        """Guardar modelo con metadata de topología"""
        if not self.save_model(path):
            return False

        try:
            # Guardar metadata de topología
            metadata = self.topology_bridge.get_topology_metadata()
            metadata['algorithm'] = 'PPO'  # Por defecto
            metadata['model_path'] = path

            metadata_path = path.replace('.zip', '_metadata.json')

            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            print(f"[OK] Metadata de topología guardada: {metadata_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Error guardando metadata: {e}")
            return False

    def start_real_time_data_collection(self):
        """Iniciar captura de datos en tiempo real"""
        if not self.data_collector.start_collection():
            print("[ERROR] No se pudo iniciar captura de datos")
            return False
        return True

    def stop_real_time_data_collection(self):
        """Detener captura de datos en tiempo real"""
        self.data_collector.stop_collection()

    def get_real_time_charts_data(self) -> Dict[str, Any]:
        """Obtener datos formateados para gráficos en tiempo real"""
        return self.data_collector.get_formatted_data_for_charts()

    def get_topology_info(self) -> Dict[str, Any]:
        """Obtener información de la topología actual"""
        if self.topology_bridge.current_topology:
            return {
                'num_onus': self.topology_bridge.current_topology['num_onus'],
                'topology_hash': self.topology_bridge.topology_hash,
                'olt_config': self.topology_bridge.current_topology.get('olt_config', {})
            }
        return {}
    
    def _on_training_completed(self, model):
        """Callback cuando el entrenamiento se completa"""
        self.model = model
        self.is_training = False
        self.training_completed.emit(model)
        print("[OK] Entrenamiento completado")
    
    def cleanup(self):
        """Limpiar recursos"""
        self.stop_training()
        self.stop_real_time_data_collection()
        self.env = None
        self.model = None
        self.canvas_widget = None
        print("[OK] RLAdapter limpiado")


class TrainingThread(QThread):
    """Hilo para ejecutar entrenamiento RL sin bloquear la UI"""

    progress_updated = pyqtSignal(dict)
    training_completed = pyqtSignal(object)
    training_error = pyqtSignal(str)

    def __init__(self, model, params, data_collector=None):
        super().__init__()
        self.model = model
        self.params = params
        self.data_collector = data_collector
        self._stop_requested = False
    
    def run(self):
        """Ejecutar entrenamiento"""
        try:
            total_timesteps = self.params.get('total_timesteps', 100000)

            # Callback personalizado para actualizar progreso y capturar datos
            callback = TrainingCallback(self)

            # Ejecutar entrenamiento
            self.model.learn(
                total_timesteps=total_timesteps,
                callback=callback,
                progress_bar=False  # Desactivar barra de progreso de consola
            )

            if not self._stop_requested:
                self.training_completed.emit(self.model)
            
        except Exception as e:
            self.training_error.emit(str(e))
    
    def stop(self):
        """Solicitar detener entrenamiento"""
        self._stop_requested = True


class TrainingCallback:
    """Callback para actualizar progreso durante el entrenamiento"""
    
    def __init__(self, training_thread):
        self.training_thread = training_thread
        self.step_count = 0
    
    def __call__(self, locals_dict, globals_dict):
        """Callback llamado durante el entrenamiento"""
        self.step_count += 1

        # Extraer datos de entrenamiento
        reward = locals_dict.get('rewards', [0])[-1] if locals_dict.get('rewards') else 0
        episode = locals_dict.get('episode', 0)
        action = locals_dict.get('actions', [])

        # Actualizar data collector si está disponible
        if hasattr(self.training_thread, 'data_collector') and self.training_thread.data_collector:
            self.training_thread.data_collector.update_rl_metrics(reward, action, episode)

        # Actualizar progreso cada 100 pasos
        if self.step_count % 100 == 0:
            progress_data = {
                'step': self.step_count,
                'episode': episode,
                'reward': reward,
                'loss': locals_dict.get('loss', 0),
                'action': action
            }

            self.training_thread.progress_updated.emit(progress_data)

        # Verificar si se solicitó detener
        return not self.training_thread._stop_requested