"""
Training Manager
Gestor de entrenamiento RL que coordina todos los componentes
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from .rl_adapter import RLAdapter
from .environment_bridge import EnvironmentBridge
from .metrics_converter import MetricsConverter
from .simulation_manager import SimulationManager


class TrainingManager(QObject):
    """
    Gestor principal que coordina el entrenamiento RL entre PonLab y netPONpy
    """
    
    # Señales principales
    training_status_changed = pyqtSignal(str)        # Estado del entrenamiento
    metrics_updated = pyqtSignal(dict)               # Métricas actualizadas
    training_progress = pyqtSignal(dict)             # Progreso de entrenamiento
    training_completed = pyqtSignal(str)             # Entrenamiento completado (ruta modelo)
    error_occurred = pyqtSignal(str)                 # Error durante operación

    # Señales de simulación
    simulation_started = pyqtSignal(dict)            # Simulación iniciada
    simulation_progress = pyqtSignal(dict)           # Progreso de simulación
    simulation_completed = pyqtSignal(dict)          # Simulación completada
    simulation_stopped = pyqtSignal()                # Simulación detenida
    agent_decision = pyqtSignal(dict)                # Decisión del agente RL
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Componentes principales
        self.rl_adapter = RLAdapter(self)
        self.env_bridge = EnvironmentBridge(self)
        self.metrics_converter = MetricsConverter()
        self.simulation_manager = SimulationManager(self)
        
        # Estado del manager
        self.is_training = False
        self.current_session_id = None
        self.training_start_time = None
        self.session_metrics = []
        
        # Configuración actual
        self.current_config = {}
        
        # Timer para actualización de métricas
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self._update_metrics)
        
        # Conectar señales de componentes
        self._setup_signal_connections()
        
        print("TrainingManager inicializado")
    
    def _setup_signal_connections(self):
        """Configurar conexiones de señales entre componentes"""
        
        # Señales del RL Adapter
        self.rl_adapter.environment_created.connect(self._on_environment_created)
        self.rl_adapter.training_progress.connect(self._on_training_progress)
        self.rl_adapter.training_completed.connect(self._on_training_completed)
        self.rl_adapter.training_error.connect(self._on_training_error)
        
        # Señales del Environment Bridge
        self.env_bridge.topology_updated.connect(self._on_topology_updated)
        self.env_bridge.metrics_updated.connect(self._on_bridge_metrics_updated)

        # Señales del Simulation Manager
        self.simulation_manager.simulation_started.connect(self.simulation_started.emit)
        self.simulation_manager.simulation_progress.connect(self.simulation_progress.emit)
        self.simulation_manager.simulation_completed.connect(self.simulation_completed.emit)
        self.simulation_manager.simulation_stopped.connect(self.simulation_stopped.emit)
        self.simulation_manager.agent_decision.connect(self.agent_decision.emit)
        self.simulation_manager.error_occurred.connect(self.error_occurred.emit)
        
        print("Conexiones de senales configuradas")
    
    def initialize_training_session(self, params: Dict[str, Any], canvas=None) -> bool:
        """
        Inicializar nueva sesión de entrenamiento
        
        Args:
            params: Parámetros de entrenamiento
            canvas: Referencia al canvas de PonLab (opcional)
            
        Returns:
            True si la inicialización fue exitosa
        """
        try:
            print("Inicializando sesion de entrenamiento...")
            
            # Verificar disponibilidad de netPONpy
            if not self.rl_adapter.is_available():
                self.error_occurred.emit("netPONpy RL no está disponible. Instale las dependencias.")
                return False
            
            # Generar ID de sesión
            self.current_session_id = self._generate_session_id()
            self.current_config = params.copy()
            self.training_start_time = datetime.now()
            
            # Configurar canvas si se proporciona
            if canvas:
                self.env_bridge.set_canvas_reference(canvas)
                
                # Sincronizar topología
                if not self.env_bridge.sync_topology_with_rl():
                    self.error_occurred.emit("Error sincronizando topología con RL")
                    return False
            
            # Crear entorno RL
            if not self.rl_adapter.create_environment(params):
                self.error_occurred.emit("Error creando entorno RL")
                return False
            
            # Crear modelo RL
            if not self.rl_adapter.create_model(params):
                self.error_occurred.emit("Error creando modelo RL")
                return False
            
            self.training_status_changed.emit("initialized")
            print(f"Sesion de entrenamiento inicializada: {self.current_session_id}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error inicializando sesión: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def start_training(self) -> bool:
        """
        Iniciar entrenamiento RL
        
        Returns:
            True si el entrenamiento se inició exitosamente
        """
        try:
            if self.is_training:
                print("WARNING: Entrenamiento ya esta en progreso")
                return False
            
            if not self.current_session_id:
                self.error_occurred.emit("No hay sesión inicializada")
                return False
            
            print("Iniciando entrenamiento RL...")
            
            # Iniciar entrenamiento en el adapter
            self.rl_adapter.start_training(self.current_config)
            
            # Actualizar estado
            self.is_training = True
            self.training_start_time = datetime.now()
            
            # Iniciar timer de métricas
            self.metrics_timer.start(2000)  # Actualizar cada 2 segundos
            
            self.training_status_changed.emit("training")
            print("Entrenamiento iniciado")
            
            return True
            
        except Exception as e:
            error_msg = f"Error iniciando entrenamiento: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def pause_training(self) -> bool:
        """
        Pausar entrenamiento RL
        
        Returns:
            True si se pausó exitosamente
        """
        try:
            if not self.is_training:
                return False
            
            # Por ahora, netPONpy no soporta pausa, así que detenemos las métricas
            self.metrics_timer.stop()
            self.training_status_changed.emit("paused")
            print("Entrenamiento pausado")
            
            return True
            
        except Exception as e:
            print(f"ERROR pausando entrenamiento: {e}")
            return False
    
    def stop_training(self) -> bool:
        """
        Detener entrenamiento RL
        
        Returns:
            True si se detuvo exitosamente
        """
        try:
            if not self.is_training:
                return False
            
            print("Deteniendo entrenamiento...")
            
            # Detener en el adapter
            self.rl_adapter.stop_training()
            
            # Actualizar estado
            self.is_training = False
            self.metrics_timer.stop()
            
            self.training_status_changed.emit("stopped")
            print("Entrenamiento detenido")
            
            return True
            
        except Exception as e:
            error_msg = f"Error deteniendo entrenamiento: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def save_model(self, custom_name: Optional[str] = None) -> bool:
        """
        Guardar modelo entrenado
        
        Args:
            custom_name: Nombre personalizado para el modelo
            
        Returns:
            True si se guardó exitosamente
        """
        try:
            # Generar nombre de archivo
            if custom_name:
                filename = f"{custom_name}.zip"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                algorithm = self.current_config.get('algorithm', 'unknown')
                filename = f"ponlab_rl_{algorithm}_{timestamp}.zip"
            
            # Crear directorio de modelos en la raíz de PonLab
            ponlab_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Subir tres niveles desde core/rl_integration/
            models_dir = os.path.join(ponlab_dir, "models")  # Carpeta models en la raíz
            os.makedirs(models_dir, exist_ok=True)

            # Ruta completa
            model_path = os.path.join(models_dir, filename)
            
            # Guardar modelo
            if self.rl_adapter.save_model(model_path):
                # Guardar metadata de la sesión
                self._save_session_metadata(model_path)
                
                self.training_completed.emit(model_path)
                print(f"Modelo guardado: {model_path}")
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"Error guardando modelo: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False
    
    def load_model(self, model_path: str) -> bool:
        """
        Cargar modelo pre-entrenado
        
        Args:
            model_path: Ruta del modelo a cargar
            
        Returns:
            True si se cargó exitosamente
        """
        try:
            if self.rl_adapter.load_model(model_path):
                print(f"Modelo cargado: {model_path}")
                self.training_status_changed.emit("model_loaded")
                return True
            
            return False
            
        except Exception as e:
            error_msg = f"Error cargando modelo: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    # === MÉTODOS DE SIMULACIÓN ===

    def load_model_for_simulation(self, model_path: str) -> bool:
        """
        Cargar modelo pre-entrenado para simulación

        Args:
            model_path: Ruta del modelo a cargar

        Returns:
            True si se cargó exitosamente
        """
        try:
            print(f"Iniciando carga de modelo para simulacion: {model_path}")

            # Cargar modelo en el adapter principal
            if self.rl_adapter.load_model(model_path):
                print("Modelo cargado en RL adapter")

                # También cargar en el simulation manager
                if self.simulation_manager.load_model_for_simulation(model_path):
                    print(f"Modelo cargado para simulacion: {os.path.basename(model_path)}")
                    return True
                else:
                    print("Error: No se pudo cargar en simulation manager")
            else:
                print("Error: No se pudo cargar en RL adapter")

            return False

        except Exception as e:
            error_msg = f"Error cargando modelo para simulación: {str(e)}"
            print(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def start_simulation_with_rl(self, params: Dict[str, Any], canvas=None) -> bool:
        """
        Iniciar simulación usando modelo RL cargado

        Args:
            params: Parámetros de simulación
            canvas: Referencia al canvas de PonLab

        Returns:
            True si se inició exitosamente
        """
        try:
            if self.is_training:
                self.error_occurred.emit("No se puede simular durante entrenamiento")
                return False

            # Verificar que hay un modelo cargado
            if not self.simulation_manager.loaded_model:
                self.error_occurred.emit("No hay modelo cargado para simulación")
                return False

            # Agregar configuración del entorno si no está presente
            if 'num_onus' not in params:
                params['num_onus'] = 4
            if 'traffic_scenario' not in params:
                params['traffic_scenario'] = 'residential_medium'
            if 'simulation_timestep' not in params:
                params['simulation_timestep'] = 0.0005

            # Iniciar simulación
            return self.simulation_manager.start_simulation(params, canvas)

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
        return self.simulation_manager.stop_simulation()

    def get_simulation_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de la simulación

        Returns:
            Diccionario con información de estado
        """
        return self.simulation_manager.get_simulation_status()

    def get_training_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual del entrenamiento
        
        Returns:
            Diccionario con información de estado
        """
        status = {
            'is_training': self.is_training,
            'session_id': self.current_session_id,
            'start_time': self.training_start_time.isoformat() if self.training_start_time else None,
            'duration_seconds': 0,
            'has_model': self.rl_adapter.model is not None,
            'has_environment': self.rl_adapter.env is not None,
            'netponpy_available': self.rl_adapter.is_available()
        }
        
        # Calcular duración si está entrenando
        if self.is_training and self.training_start_time:
            duration = datetime.now() - self.training_start_time
            status['duration_seconds'] = duration.total_seconds()
        
        return status
    
    def get_session_metrics(self) -> Dict[str, Any]:
        """
        Obtener métricas de la sesión actual
        
        Returns:
            Métricas agregadas de la sesión
        """
        try:
            if not self.session_metrics:
                return {}
            
            # Usar el convertidor de métricas para agregar datos
            aggregated = self.metrics_converter.aggregate_metrics_over_time(300)  # 5 minutos
            
            # Agregar información de sesión
            aggregated.update({
                'session_id': self.current_session_id,
                'total_samples': len(self.session_metrics),
                'configuration': self.current_config.copy()
            })
            
            return aggregated
            
        except Exception as e:
            print(f"❌ Error obteniendo métricas de sesión: {e}")
            return {}
    
    def _generate_session_id(self) -> str:
        """Generar ID único para la sesión"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ponlab_rl_session_{timestamp}"
    
    def _update_metrics(self):
        """Actualizar métricas periódicamente durante el entrenamiento"""
        try:
            if not self.is_training:
                return
            
            # Obtener métricas del canvas si está disponible
            canvas_metrics = self.env_bridge.get_canvas_metrics()
            
            # Obtener estado del entrenamiento
            training_status = self.get_training_status()
            
            # Combinar métricas
            combined_metrics = {
                'timestamp': datetime.now().isoformat(),
                'canvas_metrics': canvas_metrics,
                'training_status': training_status,
                'session_id': self.current_session_id
            }
            
            # Agregar al historial
            self.session_metrics.append(combined_metrics)
            self.metrics_converter.add_to_history(combined_metrics)
            
            # Emitir señal
            self.metrics_updated.emit(combined_metrics)
            
        except Exception as e:
            print(f"❌ Error actualizando métricas: {e}")
    
    def _save_session_metadata(self, model_path: str):
        """Guardar metadata de la sesión junto con el modelo"""
        try:
            import json
            
            metadata = {
                'session_id': self.current_session_id,
                'training_start_time': self.training_start_time.isoformat() if self.training_start_time else None,
                'training_end_time': datetime.now().isoformat(),
                'configuration': self.current_config,
                'model_path': model_path,
                'total_metrics_samples': len(self.session_metrics),
                'conversion_stats': self.metrics_converter.get_conversion_stats()
            }
            
            # Guardar en archivo JSON junto al modelo
            metadata_path = model_path.replace('.zip', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"📄 Metadata guardada: {metadata_path}")
            
        except Exception as e:
            print(f"WARNING: Error guardando metadata: {e}")
    
    # Callbacks para señales de componentes
    def _on_environment_created(self, env):
        """Callback cuando se crea el entorno"""
        self.env_bridge.set_rl_environment(env)
        print("🌍 Entorno RL conectado al bridge")
    
    def _on_training_progress(self, progress_data: Dict[str, Any]):
        """Callback para progreso de entrenamiento"""
        # Convertir métricas a formato PonLab
        ponlab_metrics = self.metrics_converter.convert_rl_metrics_to_ponlab(progress_data)
        
        # Agregar información de sesión
        ponlab_metrics['session_id'] = self.current_session_id
        
        # Emitir progreso
        self.training_progress.emit(ponlab_metrics)
        
        # Agregar al historial
        self.session_metrics.append(ponlab_metrics)
    
    def _on_training_completed(self, model):
        """Callback cuando se completa el entrenamiento"""
        self.is_training = False
        self.metrics_timer.stop()
        
        # Auto-guardar si está configurado
        if self.current_config.get('auto_save', True):
            self.save_model()
        
        self.training_status_changed.emit("completed")
        print("Entrenamiento completado")
    
    def _on_training_error(self, error_msg: str):
        """Callback para errores de entrenamiento"""
        self.is_training = False
        self.metrics_timer.stop()
        self.training_status_changed.emit("error")
        self.error_occurred.emit(error_msg)
    
    def _on_topology_updated(self, topology: Dict[str, Any]):
        """Callback cuando se actualiza la topología"""
        print(f"Topologia actualizada: {topology.get('onu_count', 0)} ONUs")
    
    def _on_bridge_metrics_updated(self, metrics: Dict[str, Any]):
        """Callback cuando se actualizan métricas del bridge"""
        # Convertir y emitir métricas
        if metrics:
            self.metrics_updated.emit(metrics)
    
    def cleanup(self):
        """Limpiar recursos del manager"""
        try:
            # Detener entrenamiento si está activo
            if self.is_training:
                self.stop_training()
            
            # Limpiar componentes
            self.rl_adapter.cleanup()
            self.env_bridge.clear_mapping()
            self.metrics_converter.clear_history()
            self.simulation_manager.cleanup()
            
            # Limpiar estado
            self.current_session_id = None
            self.session_metrics.clear()
            
            print("TrainingManager limpiado")
            
        except Exception as e:
            print(f"WARNING: Error durante cleanup: {e}")