"""
Integrated RL Manager
Gestor principal que integra todos los componentes de RL: topología, datos y entrenamiento
"""

import sys
import os
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import json
import time

from .rl_adapter import RLAdapter
from .topology_bridge import TopologyBridge
from .data_collector import RealTimeDataCollector
from .rl_data_bridge import RLDataBridge


class IntegratedRLManager(QObject):
    """
    Gestor principal que integra todos los componentes de aprendizaje reforzado
    """

    # Señales principales
    topology_status_changed = pyqtSignal(dict)      # Estado de topología
    training_progress_updated = pyqtSignal(dict)     # Progreso de entrenamiento
    real_time_data_available = pyqtSignal(dict)     # Datos en tiempo real
    simulation_completed = pyqtSignal(dict)         # Simulación completada
    error_occurred = pyqtSignal(str)                # Error ocurrido

    def __init__(self, parent=None):
        super().__init__(parent)

        # Componentes principales
        self.rl_adapter = RLAdapter()
        self.topology_bridge = TopologyBridge()
        self.data_collector = RealTimeDataCollector()
        self.data_bridge = RLDataBridge()  # NUEVO: Puente de datos reales

        # Estado del manager
        self.canvas_widget = None
        self.current_session = {
            'status': 'idle',  # idle, training, simulating, error
            'model_loaded': False,
            'topology_ready': False,
            'data_collection_active': False
        }

        # Configurar conexiones entre componentes
        self._setup_connections()

        # Timer para actualizaciones periódicas de estado
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # Cada segundo

    def _setup_connections(self):
        """Configurar conexiones entre componentes"""
        # Conexiones del RLAdapter
        self.rl_adapter.training_progress.connect(self._on_training_progress)
        self.rl_adapter.training_completed.connect(self._on_training_completed)
        self.rl_adapter.training_error.connect(self._on_error)
        self.rl_adapter.real_time_data.connect(self._on_real_time_data)

        # Conexiones del TopologyBridge
        self.topology_bridge.topology_extracted.connect(self._on_topology_extracted)
        self.topology_bridge.topology_validated.connect(self._on_topology_validated)

        # Conexiones del DataCollector
        self.data_collector.data_collected.connect(self._on_data_collected)

        # Conexiones del DataBridge (NUEVO)
        self.data_bridge.real_time_data_updated.connect(self._on_real_time_data_updated)
        self.data_bridge.charts_data_ready.connect(self._on_charts_data_ready)

    def setup_canvas_integration(self, canvas_widget):
        """
        Configurar integración con el canvas de PonLab

        Args:
            canvas_widget: Widget del canvas principal
        """
        try:
            self.canvas_widget = canvas_widget

            # Configurar en todos los componentes
            self.rl_adapter.setup_canvas_integration(canvas_widget)

            print("[OK] Canvas integrado al RL Manager")
            return True

        except Exception as e:
            error_msg = f"Error configurando canvas: {e}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def extract_and_validate_topology(self) -> bool:
        """
        Extraer y validar topología del canvas actual

        Returns:
            True si la topología es válida y está lista
        """
        try:
            # Extraer topología del canvas
            if not self.rl_adapter.extract_topology_from_canvas():
                self.error_occurred.emit("No se pudo extraer la topología del canvas")
                return False

            self.current_session['topology_ready'] = True

            # Emitir estado de topología
            topology_info = self.rl_adapter.get_topology_info()
            self.topology_status_changed.emit({
                'status': 'ready',
                'topology_info': topology_info,
                'message': f"Topología extraída: {topology_info.get('num_onus', 0)} ONUs"
            })

            return True

        except Exception as e:
            error_msg = f"Error extrayendo topología: {e}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def create_training_environment(self, params: Dict[str, Any]) -> bool:
        """
        Crear entorno de entrenamiento con la topología actual

        Args:
            params: Parámetros del entorno

        Returns:
            True si el entorno se creó correctamente
        """
        try:
            # Verificar que la topología está lista
            if not self.current_session['topology_ready']:
                if not self.extract_and_validate_topology():
                    return False

            # Asegurar que usamos la topología del canvas
            params['use_canvas_topology'] = True

            # Crear entorno
            if not self.rl_adapter.create_environment(params):
                return False

            # Configurar data collector
            if not self.rl_adapter.start_real_time_data_collection():
                print("[WARNING] Data collector no se pudo iniciar")

            self.current_session['data_collection_active'] = True
            print("[OK] Entorno de entrenamiento creado con topología del canvas")
            return True

        except Exception as e:
            error_msg = f"Error creando entorno de entrenamiento: {e}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def start_training(self, params: Dict[str, Any]) -> bool:
        """
        Iniciar entrenamiento con parámetros especificados

        Args:
            params: Parámetros de entrenamiento

        Returns:
            True si el entrenamiento se inició correctamente
        """
        try:
            # Crear entorno si no existe
            if not self.rl_adapter.env:
                if not self.create_training_environment(params):
                    return False

            # Crear modelo
            if not self.rl_adapter.create_model(params):
                return False

            # Iniciar entrenamiento
            self.rl_adapter.start_training(params)

            self.current_session['status'] = 'training'
            print("[OK] Entrenamiento iniciado")
            return True

        except Exception as e:
            error_msg = f"Error iniciando entrenamiento: {e}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def stop_training(self):
        """Detener entrenamiento actual"""
        try:
            self.rl_adapter.stop_training()
            self.current_session['status'] = 'idle'
            print("[OK] Entrenamiento detenido")
        except Exception as e:
            print(f"[ERROR] Error deteniendo entrenamiento: {e}")

    def load_model_for_simulation(self, model_path: str) -> bool:
        """
        Cargar modelo para simulación

        Args:
            model_path: Ruta del modelo a cargar

        Returns:
            True si el modelo se cargó correctamente y es compatible
        """
        try:
            # Verificar que la topología está lista
            if not self.current_session['topology_ready']:
                if not self.extract_and_validate_topology():
                    return False

            # Cargar modelo (incluye validación de compatibilidad)
            if not self.rl_adapter.load_model(model_path):
                return False

            self.current_session['model_loaded'] = True
            print(f"[OK] Modelo cargado para simulación: {model_path}")
            return True

        except Exception as e:
            error_msg = f"Error cargando modelo: {e}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def start_rl_simulation(self, params: Dict[str, Any]) -> bool:
        """
        Iniciar simulación con modelo RL con captura de datos reales

        Args:
            params: Parámetros de simulación

        Returns:
            True si la simulación se inició correctamente
        """
        try:
            # Verificar que hay modelo cargado
            if not self.current_session['model_loaded']:
                self.error_occurred.emit("No hay modelo cargado para simulación")
                return False

            # Verificar que la topología está lista
            if not self.current_session['topology_ready']:
                if not self.extract_and_validate_topology():
                    return False

            # Crear entorno de simulación si no existe
            if not self.rl_adapter.env:
                if not self.create_training_environment(params):
                    return False

            # CONECTAR DATA BRIDGE CON EL ENVIRONMENT RL (NUEVA FUNCIONALIDAD)
            if self.rl_adapter.env:
                success = self.data_bridge.connect_to_rl_environment(self.rl_adapter.env)
                if success:
                    # Iniciar captura de datos REALES
                    if self.data_bridge.start_real_time_capture():
                        self.current_session['data_collection_active'] = True
                        print("[OK] Captura de datos reales iniciada")
                    else:
                        print("[WARNING] No se pudo iniciar captura de datos reales")
                else:
                    print("[WARNING] No se pudo conectar DataBridge al environment")

            # Fallback: usar data collector original si el bridge no funciona
            if not self.current_session['data_collection_active']:
                if not self.rl_adapter.start_real_time_data_collection():
                    print("[WARNING] Data collector no se pudo iniciar")

            self.current_session['status'] = 'simulating'
            print("[OK] Simulación RL iniciada")

            # Aquí podrías agregar lógica adicional para ejecutar la simulación
            # Por ejemplo, ejecutar episodios con el modelo cargado

            return True

        except Exception as e:
            error_msg = f"Error iniciando simulación RL: {e}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def stop_rl_simulation(self):
        """Detener simulación RL actual"""
        try:
            # Detener captura de datos reales
            self.data_bridge.stop_real_time_capture()

            # Detener data collector original (fallback)
            self.rl_adapter.stop_real_time_data_collection()

            self.current_session['status'] = 'idle'
            self.current_session['data_collection_active'] = False
            print("[OK] Simulación RL detenida")
        except Exception as e:
            print(f"[ERROR] Error deteniendo simulación: {e}")

    def get_real_time_charts_data(self) -> Dict[str, Any]:
        """
        Obtener datos formateados para gráficos en tiempo real
        UTILIZA DATOS REALES capturados del PONOrchestrator

        Returns:
            Diccionario con datos para gráficos (formato compatible con PonLab existente)
        """
        # Priorizar datos del RLDataBridge (datos reales)
        charts_data = self.data_bridge.get_charts_data()

        if charts_data:
            print(f"[OK] Usando datos REALES del PONOrchestrator ({len(charts_data.get('timestamps', []))} puntos)")
            return charts_data

        # Fallback: usar data collector original
        try:
            fallback_data = self.data_collector.get_formatted_data_for_charts()
            if fallback_data:
                print("[WARNING] Usando datos del data collector original (fallback)")
                return fallback_data
        except:
            pass

        print("[WARNING] No hay datos disponibles")
        return {}

    def get_session_status(self) -> Dict[str, Any]:
        """
        Obtener estado actual de la sesión

        Returns:
            Diccionario con el estado actual
        """
        status = self.current_session.copy()

        # Añadir información adicional
        if self.rl_adapter.topology_bridge.current_topology:
            status['topology_info'] = self.rl_adapter.get_topology_info()

        if self.current_session['data_collection_active']:
            status['data_summary'] = self.data_collector.get_real_time_summary()

        return status

    def save_model_with_metadata(self, save_path: str) -> bool:
        """
        Guardar modelo actual con metadata de topología

        Args:
            save_path: Ruta donde guardar el modelo

        Returns:
            True si se guardó correctamente
        """
        try:
            return self.rl_adapter.save_model_with_topology_metadata(save_path)
        except Exception as e:
            error_msg = f"Error guardando modelo: {e}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def export_session_data(self, export_path: str) -> bool:
        """
        Exportar todos los datos de la sesión actual

        Args:
            export_path: Ruta de exportación

        Returns:
            True si se exportó correctamente
        """
        try:
            # Exportar datos del data collector
            data_success = self.data_collector.export_data(
                os.path.join(export_path, f"rl_session_data_{int(time.time())}.json")
            )

            # Exportar configuración de topología
            topology_success = self.topology_bridge.save_topology_config(
                os.path.join(export_path, f"topology_config_{int(time.time())}.json")
            )

            return data_success and topology_success

        except Exception as e:
            error_msg = f"Error exportando datos de sesión: {e}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
            return False

    def cleanup(self):
        """Limpiar recursos del manager"""
        try:
            self.rl_adapter.cleanup()
            self.data_collector.clear_history()
            self.data_bridge.clear_data()  # NUEVO: Limpiar datos del bridge
            self.current_session = {
                'status': 'idle',
                'model_loaded': False,
                'topology_ready': False,
                'data_collection_active': False
            }
            self.status_timer.stop()
            print("[OK] RL Manager limpiado")
        except Exception as e:
            print(f"[ERROR] Error limpiando RL Manager: {e}")

    # Callbacks internos
    def _on_training_progress(self, progress_data: Dict[str, Any]):
        """Callback para progreso de entrenamiento"""
        self.training_progress_updated.emit(progress_data)

    def _on_training_completed(self, model):
        """Callback cuando completa el entrenamiento"""
        self.current_session['status'] = 'idle'
        self.current_session['model_loaded'] = True

        # Obtener datos finales para gráficos
        charts_data = self.get_real_time_charts_data()

        completion_data = {
            'status': 'completed',
            'model': model,
            'charts_data': charts_data,
            'summary': self.data_collector.get_data_statistics()
        }

        self.simulation_completed.emit(completion_data)

    def _on_topology_extracted(self, topology: Dict[str, Any]):
        """Callback cuando se extrae topología"""
        self.current_session['topology_ready'] = True

    def _on_topology_validated(self, is_valid: bool, message: str):
        """Callback cuando se valida topología"""
        if not is_valid:
            self.error_occurred.emit(f"Topología inválida: {message}")

    def _on_real_time_data(self, data_point: Dict[str, Any]):
        """Callback para datos en tiempo real"""
        self.real_time_data_available.emit(data_point)

    def _on_data_collected(self, data_point: Dict[str, Any]):
        """Callback cuando se captura un punto de datos"""
        self.real_time_data_available.emit(data_point)

    def _on_error(self, error_message: str):
        """Callback para errores"""
        self.current_session['status'] = 'error'
        self.error_occurred.emit(error_message)

    def _update_status(self):
        """Actualizar estado periódicamente"""
        if self.current_session['status'] in ['training', 'simulating']:
            # Emitir datos en tiempo real si están disponibles
            if self.current_session['data_collection_active']:
                summary = self.data_collector.get_real_time_summary()
                if summary:
                    self.real_time_data_available.emit({
                        'type': 'summary',
                        'data': summary
                    })

    # NUEVOS CALLBACKS para el RLDataBridge
    def _on_real_time_data_updated(self, real_time_data: Dict[str, Any]):
        """
        Callback cuando el RLDataBridge captura datos reales nuevos

        Args:
            real_time_data: Datos reales capturados del PONOrchestrator
        """
        # Propagar datos reales a la UI
        self.real_time_data_available.emit({
            'type': 'real_time',
            'source': 'netPONpy_orchestrator',
            'data': real_time_data
        })

        # Si hay un modelo entrenándose, actualizar con métricas RL
        if 'reward' in real_time_data and 'action' in real_time_data:
            self.data_bridge.update_rl_state(
                reward=real_time_data.get('reward', 0.0),
                action=real_time_data.get('action', []),
                episode=real_time_data.get('episode', 0)
            )

    def _on_charts_data_ready(self, charts_data: Dict[str, Any]):
        """
        Callback cuando el RLDataBridge tiene datos de gráficos listos

        Args:
            charts_data: Datos formateados para gráficos
        """
        # Emitir datos de gráficos para la UI
        self.simulation_completed.emit({
            'status': 'data_ready',
            'source': 'real_data',
            'charts_data': charts_data,
            'summary': self.data_bridge.get_session_summary()
        })

    def get_real_data_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de datos reales capturados

        Returns:
            Diccionario con resumen de la captura de datos reales
        """
        return self.data_bridge.get_session_summary()