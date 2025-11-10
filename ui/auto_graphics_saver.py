"""
Auto Graphics Saver
Sistema de guardado automático de gráficos al finalizar simulación
"""

import os
import json
import gzip
import time
from datetime import datetime
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from .pon_metrics_charts import PONMetricsChartsPanel


class SaveDataThread(QThread):
    """Thread para guardar datos en segundo plano sin bloquear UI"""

    # Señales
    save_complete = pyqtSignal(str, float, float)  # (directorio, tiempo_guardado, tamaño_mb)
    save_error = pyqtSignal(str)     # Emite error si falla
    save_progress = pyqtSignal(str)  # Emite progreso (opcional)

    def __init__(self, session_dir: str, simulation_data: Dict[str, Any],
                 session_info: Optional[Dict[str, Any]] = None,
                 use_compression: bool = True):
        super().__init__()
        self.session_dir = session_dir
        self.simulation_data = simulation_data
        self.session_info = session_info
        self.use_compression = use_compression
        self.start_time = None
        self.file_size_mb = 0

    def run(self):
        """Ejecutar guardado en thread separado con medición de tiempo"""
        try:
            # Iniciar cronómetro
            self.start_time = time.time()

            # 1. Guardar JSON
            self.save_progress.emit("Guardando datos JSON...")
            data_file = self._save_json_data()

            # 2. Guardar resumen TXT
            self.save_progress.emit("Generando resumen...")
            self._save_summary(data_file)

            # 3. Guardar metadata
            self.save_progress.emit("Guardando metadata...")
            self._save_metadata()

            # Calcular tiempo total
            elapsed_time = time.time() - self.start_time

            # Emitir señal de completado con métricas
            self.save_complete.emit(self.session_dir, elapsed_time, self.file_size_mb)

        except Exception as e:
            self.save_error.emit(f"Error en thread de guardado: {e}")

    def _save_json_data(self) -> str:
        """Guardar datos JSON con compresión opcional y medición de tamaño"""
        try:
            if self.use_compression:
                # Guardar comprimido con gzip
                data_file = os.path.join(self.session_dir, "datos_simulacion.json.gz")
                with gzip.open(data_file, 'wt', encoding='utf-8') as f:
                    # Sin indent para reducir tamaño ~40%
                    json.dump(self.simulation_data, f, ensure_ascii=False, default=str)

                # Obtener tamaño del archivo
                self.file_size_mb = os.path.getsize(data_file) / (1024 * 1024)
                print(f"✅ Datos guardados (comprimidos): datos_simulacion.json.gz ({self.file_size_mb:.2f} MB)")
            else:
                # Guardar sin comprimir pero sin indent
                data_file = os.path.join(self.session_dir, "datos_simulacion.json")
                with open(data_file, 'w', encoding='utf-8') as f:
                    json.dump(self.simulation_data, f, ensure_ascii=False, default=str)

                # Obtener tamaño del archivo
                self.file_size_mb = os.path.getsize(data_file) / (1024 * 1024)
                print(f"✅ Datos guardados: datos_simulacion.json ({self.file_size_mb:.2f} MB)")

            return data_file

        except Exception as e:
            raise Exception(f"Error guardando JSON: {e}")

    def _save_summary(self, data_file: str):
        """Guardar archivo de resumen TXT"""
        try:
            summary_file = os.path.join(self.session_dir, "RESUMEN.txt")

            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("RESUMEN DE SIMULACION PON\n")
                f.write("=" * 60 + "\n\n")

                # Fecha
                f.write(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"📂 Directorio: {os.path.basename(self.session_dir)}\n\n")

                # Configuración
                if self.session_info:
                    f.write("⚙️ CONFIGURACIÓN:\n")
                    f.write("-" * 30 + "\n")
                    for key, value in self.session_info.items():
                        f.write(f"• {key}: {value}\n")
                    f.write("\n")

                # Métricas principales
                sim_summary = self.simulation_data.get('simulation_summary', {})
                sim_stats = sim_summary.get('simulation_stats', {})
                perf_metrics = sim_summary.get('performance_metrics', {})

                f.write("📊 RESULTADOS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"• Pasos: {sim_stats.get('total_steps', 0)}\n")
                f.write(f"• Tiempo simulado: {sim_stats.get('simulation_time', 0):.6f}s\n")
                f.write(f"• Delay promedio: {perf_metrics.get('mean_delay', 0):.6f}s\n")
                f.write(f"• Throughput promedio: {perf_metrics.get('mean_throughput', 0):.3f} MB/s\n")
                f.write(f"• Utilización: {perf_metrics.get('network_utilization', 0):.1f}%\n\n")

                # Archivos generados
                f.write("📁 ARCHIVOS GENERADOS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"• Datos completos: {os.path.basename(data_file)}\n")
                f.write(f"• Resumen: RESUMEN.txt\n")
                f.write(f"• Metadata: metadata.json\n")

            print(f"✅ Resumen guardado: RESUMEN.txt")

        except Exception as e:
            raise Exception(f"Error guardando resumen: {e}")

    def _save_metadata(self):
        """Guardar metadata de la sesión"""
        try:
            metadata_file = os.path.join(self.session_dir, "metadata.json")

            metadata = {
                'timestamp': datetime.now().isoformat(),
                'session_dir': os.path.basename(self.session_dir),
                'compression_used': self.use_compression,
                'data_file': 'datos_simulacion.json.gz' if self.use_compression else 'datos_simulacion.json'
            }

            if self.session_info:
                metadata.update(self.session_info)

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            print(f"✅ Metadata guardada: metadata.json")

        except Exception as e:
            raise Exception(f"Error guardando metadata: {e}")


class AutoGraphicsSaver(QObject):
    """Gestor de guardado automático de gráficos"""

    # Señales
    graphics_saved = pyqtSignal(str)  # Directorio donde se guardaron
    save_error = pyqtSignal(str)      # Error al guardar
    save_progress = pyqtSignal(str)   # Progreso del guardado

    def __init__(self, use_compression: bool = True):
        super().__init__()
        self.base_directory = "simulation_results"
        self.use_compression = use_compression  # Usar compresión gzip por defecto
        self.save_thread = None  # Thread actual de guardado
        self.ensure_base_directory()
        
    def ensure_base_directory(self):
        """Asegurar que existe el directorio base"""
        if not os.path.exists(self.base_directory):
            os.makedirs(self.base_directory)
            print(f"Directorio creado: {self.base_directory}")
    
    def create_session_directory(self) -> str:
        """Crear directorio único para esta sesión de simulación"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = os.path.join(self.base_directory, f"simulacion_{timestamp}")
        
        try:
            os.makedirs(session_dir, exist_ok=True)
            return session_dir
        except Exception as e:
            print(f"ERROR Error creando directorio de sesion: {e}")
            return self.base_directory
    
    def save_simulation_graphics_and_data(self,
                                        charts_panel: PONMetricsChartsPanel,
                                        simulation_data: Dict[str, Any],
                                        session_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Guardar automáticamente gráficos y datos de simulación usando QThread.
        El guardado se ejecuta en segundo plano sin bloquear la UI.

        Args:
            charts_panel: Panel de gráficos con los charts generados
            simulation_data: Datos completos de la simulación
            session_info: Información adicional de la sesión

        Returns:
            str: Directorio donde se guardará todo (retorna inmediatamente)
        """
        try:
            # Crear directorio de sesión
            session_dir = self.create_session_directory()
            print(f"📁 Directorio de sesión creado: {session_dir}")

            # DESACTIVADO: No guardar gráficos PNG automáticamente
            # if charts_panel and hasattr(charts_panel, 'charts'):
            #     self._save_graphics_as_images(charts_panel, session_dir)

            # Iniciar guardado de datos en THREAD SEPARADO
            print(f"🚀 Iniciando guardado en segundo plano...")
            self._start_async_save(session_dir, simulation_data, session_info)

            # Retornar directorio inmediatamente (el guardado continúa en background)
            return session_dir

        except Exception as e:
            error_msg = f"Error iniciando guardado: {e}"
            print(f"ERROR {error_msg}")
            self.save_error.emit(error_msg)
            return ""

    def _start_async_save(self, session_dir: str, simulation_data: Dict[str, Any],
                         session_info: Optional[Dict[str, Any]]):
        """Iniciar guardado asíncrono en thread separado"""
        # Si hay un thread anterior ejecutándose, esperar a que termine
        if self.save_thread and self.save_thread.isRunning():
            print("⚠️ Guardado anterior aún en progreso, esperando...")
            self.save_thread.wait()

        # Crear y configurar thread de guardado
        self.save_thread = SaveDataThread(
            session_dir,
            simulation_data,
            session_info,
            use_compression=self.use_compression
        )

        # Conectar señales
        self.save_thread.save_complete.connect(self._on_save_complete)
        self.save_thread.save_error.connect(self._on_save_error)
        self.save_thread.save_progress.connect(self._on_save_progress)

        # Iniciar thread
        self.save_thread.start()

    def _on_save_complete(self, session_dir: str, elapsed_time: float, file_size_mb: float):
        """Callback cuando el guardado se completa exitosamente"""
        print(f"✅ Guardado completado en segundo plano: {session_dir}")
        print(f"⏱️  Tiempo de guardado: {elapsed_time:.2f} segundos")
        print(f"💾 Tamaño del archivo: {file_size_mb:.2f} MB")
        print(f"📊 Velocidad: {file_size_mb/elapsed_time:.2f} MB/s")
        self.graphics_saved.emit(session_dir)

    def _on_save_error(self, error_msg: str):
        """Callback cuando hay un error en el guardado"""
        print(f"❌ Error en guardado asíncrono: {error_msg}")
        self.save_error.emit(error_msg)

    def _on_save_progress(self, progress_msg: str):
        """Callback para reportar progreso del guardado"""
        print(f"💾 {progress_msg}")
        self.save_progress.emit(progress_msg)
    
    def _save_graphics_as_images(self, charts_panel: PONMetricsChartsPanel, session_dir: str) -> Dict[str, str]:
        """Guardar todos los gráficos como imágenes PNG de alta calidad"""
        graphics_dir = os.path.join(session_dir, "graficos")
        os.makedirs(graphics_dir, exist_ok=True)
        
        saved_graphics = {}
        
        if not hasattr(charts_panel, 'charts') or not charts_panel.charts:
            print("WARNING No hay graficos para guardar")
            return saved_graphics
        
        # Mapeo de nombres técnicos a nombres amigables
        chart_names = {
            'delay': 'evolucion_delay',
            'throughput': 'evolucion_throughput', 
            'buffer': 'niveles_buffer_onu',
            'utilization': 'utilizacion_red',
            'algorithm': 'rendimiento_algoritmo_dba',
            'traffic': 'distribucion_trafico'
        }
        
        for chart_id, chart_widget in charts_panel.charts.items():
            try:
                friendly_name = chart_names.get(chart_id, chart_id)
                filename = os.path.join(graphics_dir, f"{friendly_name}.png")
                
                # Guardar con alta resolución de forma segura
                try:
                    chart_widget.fig.savefig(
                        filename, 
                        dpi=300, 
                        bbox_inches='tight',
                        facecolor='white',
                        edgecolor='none',
                        format='png',
                        pad_inches=0.1
                    )
                except Exception as save_error:
                    print(f"WARNING Error guardando {friendly_name}, intentando metodo alternativo: {save_error}")
                    # Método alternativo más seguro
                    chart_widget.fig.savefig(
                        filename, 
                        dpi=150,  # DPI menor para evitar errores de memoria
                        facecolor='white',
                        format='png'
                    )
                
                saved_graphics[chart_id] = filename
                print(f"Grafico guardado: {friendly_name}.png")
                
            except Exception as e:
                print(f"ERROR guardando grafico {chart_id}: {e}")
        
        return saved_graphics
    
    def _save_simulation_data(self, simulation_data: Dict[str, Any], session_dir: str) -> str:
        """Guardar datos completos de simulación como JSON"""
        try:
            data_file = os.path.join(session_dir, "datos_simulacion.json")
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(simulation_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Datos de simulacion guardados: datos_simulacion.json")
            return data_file
            
        except Exception as e:
            print(f"ERROR guardando datos de simulacion: {e}")
            return ""
    
    def _save_session_summary(self, 
                            session_dir: str, 
                            simulation_data: Dict[str, Any],
                            session_info: Optional[Dict[str, Any]],
                            graphics_saved: Dict[str, str],
                            data_file: str) -> str:
        """Crear archivo de resumen legible"""
        try:
            summary_file = os.path.join(session_dir, "RESUMEN.txt")
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("RESUMEN DE SIMULACION PON\n")
                f.write("=" * 60 + "\n\n")
                
                # Información de sesión
                f.write(f"📅 Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Directorio: {os.path.basename(session_dir)}\n\n")
                
                # Información de configuración
                if session_info:
                    f.write("⚙️ CONFIGURACIÓN:\n")
                    f.write("-" * 30 + "\n")
                    for key, value in session_info.items():
                        f.write(f"• {key}: {value}\n")
                    f.write("\n")
                
                # Métricas principales
                sim_summary = simulation_data.get('simulation_summary', {})
                sim_stats = sim_summary.get('simulation_stats', {})
                perf_metrics = sim_summary.get('performance_metrics', {})
                
                f.write("📈 RESULTADOS PRINCIPALES:\n")
                f.write("-" * 30 + "\n")
                f.write(f"• Pasos ejecutados: {sim_stats.get('total_steps', 0)}\n")
                f.write(f"• Tiempo simulado: {sim_stats.get('simulation_time', 0):.6f}s\n")
                f.write(f"• Solicitudes totales: {sim_stats.get('total_requests', 0)}\n")
                f.write(f"• Solicitudes exitosas: {sim_stats.get('successful_requests', 0)}\n")
                f.write(f"• Tasa de éxito: {sim_stats.get('success_rate', 0):.1f}%\n")
                f.write(f"• Delay promedio: {perf_metrics.get('mean_delay', 0):.6f}s\n")
                f.write(f"• Throughput promedio: {perf_metrics.get('mean_throughput', 0):.3f} MB/s\n")
                f.write(f"• Utilización de red: {perf_metrics.get('network_utilization', 0):.1f}%\n\n")
                
                # Archivos generados
                f.write("ARCHIVOS GENERADOS:\n")
                f.write("-" * 30 + "\n")
                f.write(f"Datos completos: {os.path.basename(data_file)}\n")
                f.write(f"Graficos ({len(graphics_saved)}):\n")
                
                for chart_id, filepath in graphics_saved.items():
                    filename = os.path.basename(filepath)
                    f.write(f"  - {filename} ({chart_id})\n")
                
                f.write(f"\n💡 CÓMO USAR:\n")
                f.write("-" * 30 + "\n")
                f.write("1. Abrir gráficos PNG con cualquier visor de imágenes\n")
                f.write("2. Importar datos_simulacion.json para análisis posterior\n")
                f.write("3. Usar este resumen para documentación\n")
            
            print(f"Resumen guardado: RESUMEN.txt")
            return summary_file
            
        except Exception as e:
            print(f"ERROR creando resumen: {e}")
            return ""
    
    def _save_metadata(self, 
                      session_dir: str, 
                      simulation_data: Dict[str, Any],
                      session_info: Optional[Dict[str, Any]]):
        """Guardar metadatos para procesamiento automático"""
        try:
            metadata_file = os.path.join(session_dir, ".metadata.json")
            
            orchestrator_stats = simulation_data.get('orchestrator_stats', {})
            orchestrator_info = orchestrator_stats.get('orchestrator_info', {})
            
            metadata = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'simulation_type': 'PON',
                'framework': 'netPONPy_integrated',
                'configuration': {
                    'num_onus': orchestrator_info.get('num_onus', 0),
                    'traffic_scenario': orchestrator_info.get('traffic_scenario', 'unknown'),
                    'episode_duration': orchestrator_info.get('episode_duration', 0),
                    'simulation_timestep': orchestrator_info.get('simulation_timestep', 0),
                    'algorithm': session_info.get('algorithm', 'unknown') if session_info else 'unknown'
                },
                'files': {
                    'data': 'datos_simulacion.json',
                    'summary': 'RESUMEN.txt',
                    'graphics_dir': 'graficos'
                },
                'session_info': session_info or {}
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"ERROR guardando metadatos: {e}")
    
    def get_latest_session_directory(self) -> Optional[str]:
        """Obtener el directorio de la sesión más reciente"""
        try:
            if not os.path.exists(self.base_directory):
                return None
            
            sessions = [d for d in os.listdir(self.base_directory) 
                       if d.startswith('simulacion_') and 
                       os.path.isdir(os.path.join(self.base_directory, d))]
            
            if not sessions:
                return None
            
            # Ordenar por fecha (el nombre contiene timestamp)
            sessions.sort(reverse=True)
            latest_session = os.path.join(self.base_directory, sessions[0])
            
            return latest_session
            
        except Exception as e:
            print(f"ERROR buscando sesion mas reciente: {e}")
            return None
    
    def list_saved_sessions(self) -> list:
        """Listar todas las sesiones guardadas con información básica"""
        sessions_list = []
        
        try:
            if not os.path.exists(self.base_directory):
                return sessions_list
            
            for session_name in os.listdir(self.base_directory):
                session_path = os.path.join(self.base_directory, session_name)
                
                if not os.path.isdir(session_path) or not session_name.startswith('simulacion_'):
                    continue
                
                # Leer metadatos si existen
                metadata_file = os.path.join(session_path, '.metadata.json')
                metadata = {}
                
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                # Información básica de la sesión
                session_info = {
                    'name': session_name,
                    'path': session_path,
                    'created_at': metadata.get('created_at', 'unknown'),
                    'configuration': metadata.get('configuration', {}),
                    'has_graphics': os.path.exists(os.path.join(session_path, 'graficos')),
                    'has_data': os.path.exists(os.path.join(session_path, 'datos_simulacion.json')),
                    'has_summary': os.path.exists(os.path.join(session_path, 'RESUMEN.txt'))
                }
                
                sessions_list.append(session_info)
            
            # Ordenar por fecha de creación (más reciente primero)
            sessions_list.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            print(f"ERROR listando sesiones: {e}")
        
        return sessions_list