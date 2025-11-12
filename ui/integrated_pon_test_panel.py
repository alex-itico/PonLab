"""
Integrated PON Test Panel
Panel de prueba mejorado que usa el adaptador integrado y muestra gráficos automáticamente
"""

print("[VERSIÓN] Cargando integrated_pon_test_panel.py v2.0 - con método _update_rl_models_list stub")

import os

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QSpinBox, QTextEdit,
                             QGroupBox, QGridLayout, QSizePolicy, QProgressBar,
                             QCheckBox, QSlider, QSplitter, QFileDialog, QMessageBox,
                             QFrame, QDialog, QListView, QStyledItemDelegate)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QEvent, QThread, QModelIndex
from PyQt5.QtGui import QFont, QColor, QStandardItemModel, QStandardItem
from core import PONAdapter
from .pon_simulation_results_panel import PONResultsPanel
from .auto_graphics_saver import AutoGraphicsSaver
from .graphics_popup_window import GraphicsPopupWindow
from .saving_progress_widget import SavingProgressWidget

# Importar sistema de traducciones
from utils.translation_manager import translation_manager
tr = translation_manager.get_text

# Model Bridge no disponible - eliminado para independencia
MODEL_BRIDGE_AVAILABLE = False


class AlgorithmItemDelegate(QStyledItemDelegate):
    """Delegado personalizado para mostrar botones en algoritmos personalizados"""
    
    edit_clicked = pyqtSignal(str)  # Señal cuando se hace clic en Editar
    delete_clicked = pyqtSignal(str)  # Señal cuando se hace clic en Eliminar
    
    def __init__(self, parent=None, custom_algorithms=None):
        super().__init__(parent)
        self.custom_algorithms = custom_algorithms or []
        self.edit_buttons = {}
        self.delete_buttons = {}
    
    def paint(self, painter, option, index):
        """Pintar el item (delegamos al padre para items normales)"""
        super().paint(painter, option, index)
    
    def createEditor(self, parent, option, index):
        """No queremos edición de texto"""
        return None
    
    def sizeHint(self, option, index):
        """Tamaño del item"""
        size = super().sizeHint(option, index)
        algorithm = index.data(Qt.DisplayRole)
        
        # Si es algoritmo personalizado, aumentar altura para botones
        if algorithm in self.custom_algorithms:
            size.setHeight(35)
        return size


class CustomComboBoxView(QListView):
    """Vista personalizada para QComboBox que permite widgets personalizados"""
    
    edit_algorithm = pyqtSignal(str)
    delete_algorithm = pyqtSignal(str)
    
    def __init__(self, parent=None, custom_algorithms=None):
        super().__init__(parent)
        self.custom_algorithms = custom_algorithms or []
        self.button_widgets = {}
    
    def setModel(self, model):
        super().setModel(model)
        self._create_button_widgets()
    
    def retranslate(self):
        """Regenerar botones con traducciones actualizadas"""
        self._create_button_widgets()
    
    def _create_button_widgets(self):
        """Crear widgets con botones para algoritmos personalizados"""
        if not self.model():
            return
        
        for row in range(self.model().rowCount()):
            index = self.model().index(row, 0)
            algorithm = index.data(Qt.DisplayRole)
            
            if algorithm in self.custom_algorithms:
                # Crear widget con botones
                widget = QWidget()
                layout = QHBoxLayout(widget)
                layout.setContentsMargins(5, 2, 5, 2)
                layout.setSpacing(5)
                
                # Etiqueta del algoritmo
                label = QLabel(algorithm)
                layout.addWidget(label)
                layout.addStretch()
                
                # Botón Editar
                edit_btn = QPushButton(tr("integrated_pon_panel.edit_algorithm"))
                edit_btn.setMaximumSize(70, 22)
                edit_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3b82f6;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 2px 6px;
                        font-size: 9px;
                    }
                    QPushButton:hover {
                        background-color: #2563eb;
                    }
                """)
                edit_btn.clicked.connect(lambda checked, a=algorithm: self.edit_algorithm.emit(a))
                layout.addWidget(edit_btn)
                
                # Botón Eliminar
                delete_btn = QPushButton(tr("integrated_pon_panel.delete_algorithm"))
                delete_btn.setMaximumSize(70, 22)
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ef4444;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 2px 6px;
                        font-size: 9px;
                    }
                    QPushButton:hover {
                        background-color: #dc2626;
                    }
                """)
                delete_btn.clicked.connect(lambda checked, a=algorithm: self.delete_algorithm.emit(a))
                layout.addWidget(delete_btn)
                
                self.setIndexWidget(index, widget)
                self.button_widgets[algorithm] = widget


class SimulationWorker(QThread):
    """
    Worker thread para ejecutar simulación sin bloquear la UI
    """
    # Señales
    update_signal = pyqtSignal(str, dict)  # (event_type, data)
    finished_signal = pyqtSignal(bool, object)  # (success, result)

    def __init__(self, adapter, use_hybrid=True, duration=10, steps=1000):
        super().__init__()
        self.adapter = adapter
        self.use_hybrid = use_hybrid
        self.duration = duration
        self.steps = steps
        self._is_running = True

    def run(self):
        """Ejecutar simulación en thread separado"""
        try:
            if self.use_hybrid:
                # Simulación híbrida por eventos
                def callback(event_type, data):
                    if self._is_running:
                        self.update_signal.emit(event_type, data)

                success, result = self.adapter.run_hybrid_simulation(
                    duration_seconds=self.duration,
                    callback=callback
                )

                if self._is_running:
                    self.finished_signal.emit(success, result)
            else:
                # Simulación clásica por pasos
                def callback(event_type, data):
                    if self._is_running:
                        self.update_signal.emit(event_type, data)

                success = self.adapter.run_netsim_simulation(
                    timesteps=self.steps,
                    callback=callback
                )

                if self._is_running:
                    self.finished_signal.emit(success, None)

        except Exception as e:
            import traceback
            traceback.print_exc()
            if self._is_running:
                self.finished_signal.emit(False, str(e))

    def stop(self):
        """Detener la simulación"""
        self._is_running = False


class IntegratedPONTestPanel(QWidget):
    """Panel de prueba mejorado para la integración PON con visualización automática"""
    
    # Señales
    status_updated = pyqtSignal(str)
    simulation_finished = pyqtSignal()
    
    def __init__(self, training_manager=None):
        super().__init__()
        self.adapter = PONAdapter()
        self.training_manager = training_manager  # Referencia al TrainingManager para RL
        self.simulation_running = False
        self.step_count = 0
        self.canvas_reference = None  # Referencia al canvas para obtener topología
        
        # Panel de resultados integrado
        self.results_panel = None
        
        # Sistema de guardado automático y ventana emergente
        self.graphics_saver = AutoGraphicsSaver(use_compression=True)  # Habilitar compresión gzip
        self.graphics_saver.graphics_saved.connect(self._on_save_complete)  # Conectar señal de completado
        self.popup_window = None  # Se crea cuando se necesita

        # Widget de progreso de guardado incremental
        self.saving_progress_widget = None

        # Worker thread para simulación asíncrona
        self.simulation_worker = None

        # Variables para detectar cambios
        self.last_onu_count = 0
        self.last_algorithm = "FCFS"
        self.last_duration = 10
        self.orchestrator_initialized = False
        self.auto_initialize = True  # Habilitar inicialización automática
        self.rl_model_loaded = False  # Estado del modelo RL
        
        
        # Control de debug verbose
        self.verbose_debug = False  # Controla mensajes DEBUG repetitivos
        
        self.setup_ui()
        self.check_pon_status()
        
        # Inicializar estado de controles
        self.on_architecture_changed()
        
        # Realizar inicialización automática inicial si todo está listo
        if self.adapter.is_pon_available():
            QTimer.singleShot(1000, self.perform_initial_auto_initialization)
        
        # Agregar timer adicional para actualizar conteo de ONUs periódicamente
        self.onu_update_timer = QTimer()
        self.onu_update_timer.timeout.connect(self.periodic_onu_update)
        self.onu_update_timer.start(5000)  # Cada 5 segundos (reducir frecuencia)
    
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # Configurar política de tamaño del widget principal
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Solo mostrar panel de controles - los resultados se muestran en ventana emergente
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # Panel de controles únicamente
        controls_panel = self.create_controls_panel()
        main_layout.addWidget(controls_panel)
        
        # Crear panel de resultados oculto solo para generar gráficos
        self.results_panel = PONResultsPanel()
        self.results_panel.setVisible(False)  # Oculto - solo para procesamiento interno
        
        # Conectar señales
        self.results_panel.results_updated.connect(self.on_results_updated)
        
    def on_add_algorithm_clicked(self):
        """
        Abre dos ventanas:
        - Izquierda (solo lectura): core/algorithms/template_Algo_DBA.txt
        - Derecha (editable):      core/algorithms/algo_DBA_Nuevo.txt  (con Guardar)
        Ventanas top-level normales (Snap habilitado). Arrancan mitad izq/der del área útil.
        """
        try:
            import os
            from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
            from PyQt5.QtGui import QFont
            from PyQt5.QtCore import Qt, QTimer

            # --- Rutas ---
            ui_dir = os.path.dirname(os.path.abspath(__file__))
            algo_dir = os.path.abspath(os.path.join(ui_dir, "..", "core", "algorithms"))
            template_path = os.path.join(algo_dir, "template_Algo_DBA.txt")
            user_algo_path = os.path.join(algo_dir, "algo_DBA_Nuevo.txt")

            if not os.path.exists(template_path):
                QMessageBox.warning(self, "Archivo no encontrado",
                                    f"No se encontró el archivo de guía:\n{template_path}")
                return
            if not os.path.exists(user_algo_path):
                # si no existe, crear uno vacío basado en la guía
                with open(template_path, "r", encoding="utf-8") as f:
                    guide = f.read()
                with open(user_algo_path, "w", encoding="utf-8") as f:
                    f.write(guide + "\n\n# Escribe tu algoritmo aquí...")

            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            with open(user_algo_path, "r", encoding="utf-8") as f:
                user_content = f.read()

            # --- Geometría base (área útil) ---
            probe = QDialog(self)
            work = probe.screen().availableGeometry()
            
            # Calcular dimensiones dejando margen para botones y barra de tareas
            window_height = work.height() - 80  # Reducir 80px para ver botones
            window_width = work.width() // 2

            # =========================
            #  Ventana IZQUIERDA (RO)
            # =========================
            left = QDialog(None)
            left.setWindowTitle("Template de Algoritmo DBA (Guía)")
            left.setModal(False)
            left.setWindowFlags(Qt.Window | Qt.WindowTitleHint |
                                Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
            left.setAttribute(Qt.WA_DeleteOnClose, True)
            left.setStyleSheet("""
                QDialog { background-color: #1f1f1f; }
                QTextEdit {
                    background-color: #232629; color: #e0e0e0; border: none;
                    padding: 10px; selection-background-color: #3b82f6; selection-color: #ffffff;
                }
                QPushButton {
                    background-color: #2d3748; color: #e2e8f0; border: 1px solid #3a3f44;
                    border-radius: 6px; padding: 6px 10px;
                }
                QPushButton:hover { background-color: #3b495c; }
                QPushButton:pressed { background-color: #2a3341; }
            """)
            # mitad izquierda
            left.setGeometry(work.x(), work.y(), window_width, window_height)

            l_root = QVBoxLayout(left); l_root.setContentsMargins(8, 8, 8, 8); l_root.setSpacing(8)
            l_view = QTextEdit(); l_view.setReadOnly(True); l_view.setLineWrapMode(QTextEdit.NoWrap)
            l_view.setFont(QFont("Consolas", 10)); l_view.setPlainText(template_content)
            l_root.addWidget(l_view)

            l_btns = QHBoxLayout(); l_btns.addStretch(1)
            l_copy = QPushButton(tr("integrated_pon_panel.copy_all"))
            l_copy.clicked.connect(lambda: (l_view.selectAll(), l_view.copy(),
                                            QMessageBox.information(left, tr("integrated_pon_panel.copied_title"), 
                                                                   tr("integrated_pon_panel.template_copied"))))
            l_btns.addWidget(l_copy); l_root.addLayout(l_btns)

            # ajuste fino para que el frame quede pegado al borde superior/izq
            def snap_left():
                frame_tl = left.frameGeometry().topLeft(); geom_tl = left.geometry().topLeft()
                dx = frame_tl.x() - geom_tl.x(); dy = frame_tl.y() - geom_tl.y()
                left.move(work.x() - dx, work.y() - dy)

            # =========================
            #  Ventana DERECHA (RW)
            # =========================
            right = QDialog(None)
            right.setWindowTitle("Nuevo Algoritmo DBA (Editable)")
            right.setModal(False)
            right.setWindowFlags(Qt.Window | Qt.WindowTitleHint |
                                Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
            right.setAttribute(Qt.WA_DeleteOnClose, True)
            right.setStyleSheet(left.styleSheet())
            # mitad derecha
            right.setGeometry(work.x() + window_width, work.y(),
                            window_width, window_height)

            r_root = QVBoxLayout(right); r_root.setContentsMargins(8, 8, 8, 8); r_root.setSpacing(8)
            r_edit = QTextEdit(); r_edit.setLineWrapMode(QTextEdit.NoWrap)
            r_edit.setFont(QFont("Consolas", 10)); r_edit.setPlainText(user_content)
            r_root.addWidget(r_edit)

            r_btns = QHBoxLayout(); r_btns.addStretch(1)
            r_save = QPushButton(tr("integrated_pon_panel.save"))

            def _save():
                import re, ast, os
                try:
                    # 1) Guardar el texto del editor en algo_DBA_Nuevo.txt
                    with open(user_algo_path, "w", encoding="utf-8") as f:
                        f.write(r_edit.toPlainText())

                    code_text = r_edit.toPlainText()

                    # 2) Extraer el nombre del algoritmo (acepta -> str, -> Dict[..], etc.)
                    m_name = re.search(
                        r'def\s+get_algorithm_name\s*\([^)]*\)\s*(?:->\s*[A-Za-z_][A-Za-z0-9_\[\],\s]*)?\s*:[\s\S]*?return\s*[\'"]([^\'"]+)[\'"]',
                        code_text
                    )
                    if not m_name:
                        QMessageBox.warning(right, "No se detectó el nombre",
                                            "No se encontró 'return' en get_algorithm_name().")
                        return
                    algo_name = m_name.group(1).strip()

                    # 3) Extraer el nombre de la clase que hereda de DBAAlgorithmInterface
                    m_class = re.search(
                        r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*DBAAlgorithmInterface\s*\)\s*:',
                        code_text
                    )
                    if not m_class:
                        QMessageBox.warning(right, "No se detectó la clase",
                                            "No se encontró una clase que herede de DBAAlgorithmInterface.")
                        return
                    class_name = m_class.group(1).strip()

                    # 4) Ruta a pon_adapter.py
                    adapter_path = os.path.join(algo_dir, "..", "pon", "pon_adapter.py")
                    adapter_path = os.path.abspath(adapter_path)
                    if not os.path.exists(adapter_path):
                        QMessageBox.critical(right, "Error",
                                            f"No se encontró pon_adapter.py en:\n{adapter_path}")
                        return

                    with open(adapter_path, "r", encoding="utf-8") as f:
                        src = f.read()

                    # Backup previo de pon_adapter.py
                    try:
                        with open(adapter_path + ".bak", "w", encoding="utf-8") as fb:
                            fb.write(src)
                    except Exception:
                        pass

                    # 5) --- IMPORT: from ..algorithms.pon_dba import ( ... ) ---
                    imp_pat = re.compile(
                        r'(from\s+\.\.[^\n]*pon_dba\s+import\s*\(\s*)([^)]*)(\))',
                        re.DOTALL
                    )
                    m_imp = imp_pat.search(src)
                    if m_imp:
                        inner = m_imp.group(2)
                        # ¿Ya está la clase?
                        existing_ids = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', inner)
                        if class_name not in existing_ids:
                            lines = inner.splitlines()
                            # quitar líneas en blanco finales
                            while lines and not lines[-1].strip():
                                lines.pop()
                            # indentación de bloque
                            indent = "    "
                            for line in reversed(lines):
                                if line.strip():
                                    indent = re.match(r'\s*', line).group(0) or "    "
                                    break
                            # asegurar coma en la última entrada con contenido
                            if lines and not lines[-1].rstrip().endswith(','):
                                lines[-1] = lines[-1].rstrip() + ','
                            # añadir nuestra clase
                            lines.append(f"{indent}{class_name},")
                            new_inner = "\n".join(lines) + "\n"
                            src = src[:m_imp.start(2)] + new_inner + src[m_imp.end(2):]

                    # 6) --- LISTA DEL COMBO: algorithms = [ ... ] ---
                    list_pat = re.compile(r'(algorithms\s*=\s*\[)(.*?)(\])', re.DOTALL)
                    m_alglist = list_pat.search(src)
                    if m_alglist:
                        inner = m_alglist.group(2)
                        list_text = "[" + inner + "]"
                        try:
                            items = ast.literal_eval(list_text)
                            if not isinstance(items, list):
                                raise ValueError
                        except Exception:
                            items = re.findall(r'["\']([^"\']+)["\']', inner)

                        if algo_name not in items:
                            items.append(algo_name)
                            new_inner = ", ".join(f'"{x}"' for x in items)
                            src = src[:m_alglist.start(2)] + new_inner + src[m_alglist.end(2):]

                    # 7) --- DICCIONARIO FACTORY: asegurar inserción ANTES de la '}' y con sangría correcta ---
                    try:
                        # Localiza el inicio del diccionario:  algorithms = {
                        dict_head = re.search(r'algorithms\s*=\s*\{', src)
                        if dict_head:
                            start_idx = dict_head.end()  # posición después de la llave '{'

                            # Encuentra la línea de cierre '}' del diccionario (la primera llave de cierre en una línea)
                            close_m = re.search(r'\n([ \t]*)\}', src[start_idx:])
                            if close_m:
                                # Índice absoluto del cierre
                                close_abs = start_idx + close_m.start()
                                close_indent = close_m.group(1)          # sangría del '}' (normalmente 4 espacios)
                                entry_indent = close_indent + '    '     # sangría de las entradas dentro del dict

                                # Texto interior actual (sin la '}')
                                inner_text = src[start_idx:close_abs]

                                # ¿La clave ya existe?
                                if not re.search(r'["\']' + re.escape(algo_name) + r'["\']\s*:', inner_text):
                                    # Asegurar coma en la última entrada no vacía
                                    lines = inner_text.splitlines()
                                    k = len(lines) - 1
                                    while k >= 0 and not lines[k].strip():
                                        k -= 1
                                    if k >= 0 and not lines[k].rstrip().endswith(','):
                                        lines[k] = lines[k].rstrip() + ','
                                    inner_text = "\n".join(lines).rstrip()

                                    # Construir la nueva entrada bien alineada
                                    new_entry = f'\n{entry_indent}"{algo_name}": {class_name},'

                                    # Reconstruir src:   cabeza {  +  interior + nueva entrada  +  resto (incluyendo la } )
                                    src = src[:start_idx] + inner_text + new_entry + src[close_abs:]
                    except Exception as _:
                        pass


                    # 8) --- EXCEPT ImportError: agregar "Clase = None" de respaldo ---
                    # Buscamos el bloque entre 'except ImportError as e:' y la primera línea con '=lambda'
                    except_pat = re.compile(
                        r'(except\s+ImportError\s+as\s+e:\s*\n)(.*?)(\n\s*[A-Za-z_]\w+\s*=\s*lambda\b)',
                        re.DOTALL
                    )
                    m_exc = except_pat.search(src)
                    if m_exc:
                        exc_body = m_exc.group(2)
                        # si aún no existe la línea 'ClassName = None'
                        if not re.search(rf'^\s*{re.escape(class_name)}\s*=\s*None\s*$', exc_body, re.MULTILINE):
                            # localizar indentación de las asignaciones = None
                            assign_matches = list(re.finditer(r'^\s*[A-Za-z_]\w*\s*=\s*None\s*$', exc_body, re.MULTILINE))
                            if assign_matches:
                                last = assign_matches[-1]
                                indent = re.match(r'\s*', last.group(0)).group(0)
                                insert_pos = m_exc.start(2) + last.end()
                                insertion = f"\n{indent}{class_name} = None"
                                src = src[:insert_pos] + insertion + src[insert_pos:]

                    # 9) Guardar cambios en pon_adapter.py
                    with open(adapter_path, "w", encoding="utf-8") as fw:
                        fw.write(src)

                    # 10) --- Copiar implementación a core/algorithms/pon_dba.py ---
                    try:
                        block_pat = re.compile(
                            r'#\s*===\s*BEGIN\s+USER_ALGO:.*?===\s*\n(.*?)\n#\s*===\s*END\s+USER_ALGO:.*?===',
                            re.DOTALL | re.IGNORECASE
                        )
                        m_block = block_pat.search(code_text)
                        if not m_block:
                            QMessageBox.warning(
                                right, "Bloque de código no encontrado",
                                "No se encontró el bloque entre los marcadores BEGIN/END en el archivo editable."
                            )
                        else:
                            user_impl = m_block.group(1).strip("\n")

                            pon_dba_path = os.path.join(algo_dir, "pon_dba.py")
                            pon_dba_path = os.path.abspath(pon_dba_path)

                            if not os.path.exists(pon_dba_path):
                                QMessageBox.critical(
                                    right, "Archivo destino no encontrado",
                                    f"No se encontró core/algorithms/pon_dba.py en:\n{pon_dba_path}"
                                )
                            else:
                                with open(pon_dba_path, "r", encoding="utf-8") as f:
                                    pon_src = f.read()

                                # Evitar duplicados: si ya existe la clase, no volver a agregarla
                                if re.search(rf'\bclass\s+{re.escape(class_name)}\s*\(', pon_src):
                                    pass
                                else:
                                    try:
                                        with open(pon_dba_path + ".bak", "w", encoding="utf-8") as fb:
                                            fb.write(pon_src)
                                    except Exception:
                                        pass
                                    new_pon = pon_src.rstrip() + "\n\n" + user_impl.strip() + "\n"
                                    with open(pon_dba_path, "w", encoding="utf-8") as fw:
                                        fw.write(new_pon)
                    except Exception as ee:
                        QMessageBox.critical(right, "Error al copiar implementación", str(ee))

                    # 11) Mensaje final con opción de reinicio
                    msg = QMessageBox(right)
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle(tr("integrated_pon_panel.algorithm_created_title"))
                    msg.setText(tr("integrated_pon_panel.algorithm_created_text").format(algo_name))
                    
                    # Detalles formateados
                    details = tr("integrated_pon_panel.algorithm_created_details").format(class_name, algo_name)
                    msg.setInformativeText(details)
                    msg.setTextFormat(Qt.RichText)
                    
                    # Estilo personalizado para mejor legibilidad
                    msg.setStyleSheet("""
                        QMessageBox {
                            background-color: #f8f9fa;
                        }
                        QMessageBox QLabel {
                            color: #1a1a1a;
                            background-color: transparent;
                            font-size: 11pt;
                            padding: 8px;
                        }
                        QMessageBox QPushButton {
                            background-color: #0d6efd;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 8px 16px;
                            font-weight: bold;
                            min-width: 80px;
                        }
                        QMessageBox QPushButton:hover {
                            background-color: #0b5ed7;
                        }
                        QMessageBox QPushButton:pressed {
                            background-color: #0a58ca;
                        }
                    """)
                    
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                    
                    # Cerrar las ventanas sin confirmación
                    _closing_state["active"] = True
                    right.close()
                    left.close()
                    
                    # Reiniciar la aplicación
                    QTimer.singleShot(300, self._restart_application)

                except Exception as e:
                    QMessageBox.critical(right, "Error al guardar", str(e))
            # --- FIN DE FUNCIÓN _save() ---


            r_save.clicked.connect(_save)
            r_btns.addWidget(r_save)
            r_root.addLayout(r_btns)

            def snap_right():
                frame_tl = right.frameGeometry().topLeft(); geom_tl = right.geometry().topLeft()
                dx = frame_tl.x() - geom_tl.x(); dy = frame_tl.y() - geom_tl.y()
                right.move(work.x() + window_width - dx, work.y() - dy)

            # === CIERRE COORDINADO (una sola confirmación) ===
            # Usamos un flag compartido para evitar doble diálogo al cerrar la otra ventana.
            _closing_state = {"active": False}

            def _confirm_close():
                resp = QMessageBox.question(
                    None,
                    tr("integrated_pon_panel.close_without_saving_title"),
                    tr("integrated_pon_panel.close_without_saving_confirm"),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                return resp == QMessageBox.Yes

            def _left_close(ev):
                # Si ya estamos cerrando (por la otra ventana), no preguntar de nuevo.
                if _closing_state["active"]:
                    ev.accept()
                    return

                if _confirm_close():
                    _closing_state["active"] = True
                    try:
                        # Cerrar la otra SIN volver a preguntar
                        right.close()
                    finally:
                        ev.accept()
                else:
                    ev.ignore()

            def _right_close(ev):
                # Si ya estamos cerrando (por la otra ventana), no preguntar de nuevo.
                if _closing_state["active"]:
                    ev.accept()
                    return

                if _confirm_close():
                    _closing_state["active"] = True
                    try:
                        # Cerrar la otra SIN volver a preguntar
                        left.close()
                    finally:
                        ev.accept()
                else:
                    ev.ignore()

            left.closeEvent = _left_close
            right.closeEvent = _right_close
            # === FIN CIERRE COORDINADO ===


            # Mostrar ambas y ajustar
            left.show(); right.show()
            QTimer.singleShot(0, snap_left)
            QTimer.singleShot(0, snap_right)

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error",
                                f"Ocurrió un error al abrir/mostrar los editores:\n{e}")

        
    def create_controls_panel(self):
        """Crear panel de controles"""
        panel = QWidget()
        # Eliminar restricción de ancho - ahora usa todo el espacio del sidebar
        layout = QVBoxLayout(panel)
        layout.setSpacing(4)  # Reducir espaciado
        layout.setContentsMargins(6, 6, 6, 6)  # Reducir márgenes
        
        # Título
        self.title_label = QLabel(tr("integrated_pon_panel.title"))
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Estado
        self.status_group = QGroupBox(tr("integrated_pon_panel.status_group"))
        status_layout = QVBoxLayout(self.status_group)
        
        self.status_label = QLabel(tr("integrated_pon_panel.status_checking"))
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(self.status_group)
        
        # Configuración de simulación
        self.config_group = QGroupBox(tr("integrated_pon_panel.config_group"))
        config_layout = QGridLayout(self.config_group)
        
        # Número de ONUs conectadas (automático desde topología)
        self.onus_connected_label = QLabel(tr("integrated_pon_panel.onus_connected"))
        config_layout.addWidget(self.onus_connected_label, 0, 0)
        
        # Layout horizontal para el conteo y botón de actualización
        onu_layout = QHBoxLayout()
        self.onu_count_label = QLabel("0")
        self.onu_count_label.setStyleSheet("font-weight: bold; color: #2563eb; padding: 4px; background-color: #f0f4ff; border-radius: 4px;")
        self.onu_count_label.setToolTip(tr("integrated_pon_panel.onus_tooltip"))
        onu_layout.addWidget(self.onu_count_label)
        
        onu_widget = QWidget()
        onu_widget.setLayout(onu_layout)
        config_layout.addWidget(onu_widget, 0, 1)
        
        # Algoritmo DBA
        self.dba_label = QLabel(tr("integrated_pon_panel.dba"))
        config_layout.addWidget(self.dba_label, 1, 0)
        self.algorithm_combo = QComboBox()
        
        if self.adapter.is_pon_available():
            algorithms = self.adapter.get_available_algorithms()
            
            # Separar algoritmos convencionales y personalizados
            conventional = ["FCFS", "Priority", "RL-DBA", "SDN", "SP-MINSHARE", "IPACT", "GIANT", "3-Phases DBA"]
            self.custom_algorithms = [algo for algo in algorithms if algo not in conventional and algo not in ["Smart-RL", "Smart-RL-SDN"]]
            
            # Crear vista personalizada para el dropdown con botones
            self.custom_combo_view = CustomComboBoxView(custom_algorithms=self.custom_algorithms)
            self.custom_combo_view.edit_algorithm.connect(self.on_edit_custom_algorithm)
            self.custom_combo_view.delete_algorithm.connect(self.on_delete_custom_algorithm)
            self.algorithm_combo.setView(self.custom_combo_view)
            
            # Agregar header y algoritmos convencionales
            self.algorithm_combo.addItem(tr("integrated_pon_panel.algorithms_conventional"))
            model = self.algorithm_combo.model()
            item = model.item(self.algorithm_combo.count() - 1)
            item.setEnabled(False)  # Hacer que el header no sea seleccionable
            item.setFont(QFont("Arial", 9, QFont.Bold))
            item.setBackground(QColor(240, 240, 240, 50))
            
            for algo in algorithms:
                if algo in conventional:
                    self.algorithm_combo.addItem(algo)
            
            # Agregar Smart-RL si está disponible
            if "Smart-RL" in algorithms or "Smart-RL-SDN" in algorithms:
                for algo in algorithms:
                    if algo in ["Smart-RL", "Smart-RL-SDN"]:
                        self.algorithm_combo.addItem(algo)
            
            # Agregar header y algoritmos personalizados si existen
            if self.custom_algorithms:
                self.algorithm_combo.addItem(tr("integrated_pon_panel.algorithms_custom"))
                item = model.item(self.algorithm_combo.count() - 1)
                item.setEnabled(False)
                item.setFont(QFont("Arial", 9, QFont.Bold))
                item.setBackground(QColor(240, 240, 240, 50))
                
                for algo in self.custom_algorithms:
                    self.algorithm_combo.addItem(algo)
            
            # Agregar opción de agente RL si está disponible
            if MODEL_BRIDGE_AVAILABLE:
                self.algorithm_combo.addItem("RL Agent")
            
            # Actualizar los widgets de botones en la vista personalizada
            self.custom_combo_view._create_button_widgets()
            
            # Seleccionar FCFS por defecto (primer algoritmo real después del header)
            # Buscar el índice de FCFS en el ComboBox
            fcfs_index = self.algorithm_combo.findText("FCFS")
            if fcfs_index != -1:
                self.algorithm_combo.setCurrentIndex(fcfs_index)
                print("✅ Algoritmo FCFS seleccionado por defecto")
            else:
                # Si FCFS no está disponible, seleccionar el primer algoritmo válido
                for i in range(self.algorithm_combo.count()):
                    if self.algorithm_combo.model().item(i).isEnabled():
                        self.algorithm_combo.setCurrentIndex(i)
                        print(f"✅ Algoritmo '{self.algorithm_combo.currentText()}' seleccionado por defecto")
                        break
        
        self.algorithm_combo.currentTextChanged.connect(self.on_algorithm_changed)
        config_layout.addWidget(self.algorithm_combo, 1, 1)
        
        # --- Nuevo bloque: Botón "Agregar Algoritmo DBA" ---
        config_layout.addWidget(QLabel(""), 2, 0)

        # --- Botón "Agregar Algoritmo DBA" (mismo estilo que el bloque RL) ---
        algo_btns_layout = QVBoxLayout()
        algo_btns_layout.setSpacing(8)

        self.add_algorithm_btn = QPushButton(tr("integrated_pon_panel.add_custom_algorithm"))
        self.add_algorithm_btn.setToolTip(tr("integrated_pon_panel.add_custom_algorithm_tooltip"))
        self.add_algorithm_btn.setMinimumHeight(30)
        self.add_algorithm_btn.clicked.connect(self.on_add_algorithm_clicked)  # handler abajo
        algo_btns_layout.addWidget(self.add_algorithm_btn)

        algo_btns_frame = QFrame()
        algo_btns_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        algo_btns_frame.setLineWidth(1)
        algo_btns_frame.setLayout(algo_btns_layout)
        algo_btns_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(240, 240, 240, 0.1);
                border: 1px solid #ccc;
                border-radius: 8px;
                margin: 3px;
                padding: 8px;
            }
        """)

        config_layout.addWidget(algo_btns_frame, 2, 1)
        # --- fin bloque botón DBA ---

        
        
        # Selector de modelo RL (inicialmente oculto)
        self.rl_model_label = QLabel(tr("integrated_pon_panel.rl_model"))
        config_layout.addWidget(self.rl_model_label, 3, 0)
        
        # Layout vertical para organizar mejor los elementos RL
        rl_main_layout = QVBoxLayout()
        
        # Layout vertical para los botones con mejor espaciado
        rl_buttons_layout = QVBoxLayout()
        rl_buttons_layout.setSpacing(8)  # Espacio entre botones
        
        # Smart RL model loading
        self.load_rl_model_btn = QPushButton(tr("integrated_pon_panel.load_rl_model"))
        self.load_rl_model_btn.setToolTip(tr("integrated_pon_panel.load_rl_model_tooltip"))
        self.load_rl_model_btn.setMinimumHeight(30)  # Altura mínima para botones
        self.load_rl_model_btn.clicked.connect(self.load_smart_rl_model)
        rl_buttons_layout.addWidget(self.load_rl_model_btn)

        # Botón para desactivar RL
        self.unload_rl_model_btn = QPushButton(tr("integrated_pon_panel.unload_rl_model"))
        self.unload_rl_model_btn.setToolTip(tr("integrated_pon_panel.unload_rl_model_tooltip"))
        self.unload_rl_model_btn.setMinimumHeight(30)  # Altura mínima
        self.unload_rl_model_btn.clicked.connect(self.unload_rl_model)
        self.unload_rl_model_btn.setVisible(False)  # Inicialmente oculto
        rl_buttons_layout.addWidget(self.unload_rl_model_btn)
        
        
        # Frame para contener los botones con mejor presentación vertical
        rl_buttons_frame = QFrame()
        rl_buttons_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        rl_buttons_frame.setLineWidth(1)
        rl_buttons_frame.setLayout(rl_buttons_layout)
        rl_buttons_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(240, 240, 240, 0.1);
                border: 1px solid #ccc;
                border-radius: 8px;
                margin: 3px;
                padding: 8px;
            }
        """)
        
        # Agregar frame de botones al layout principal
        rl_main_layout.addWidget(rl_buttons_frame)

        # RL model status en una línea separada con margen
        self.rl_status_label = QLabel(tr("integrated_pon_panel.rl_status_no_model"))
        self.rl_status_label.setStyleSheet("color: #666; font-size: 8pt; margin-top: 5px;")
        rl_main_layout.addWidget(self.rl_status_label)

        # LÍNEA 162 MODIFICADA - NO DEBE HABER ERROR AQUÍ
        # Crear widget de RL y agregarlo al layout
        rl_widget = QWidget()
        rl_widget.setLayout(rl_main_layout)
        config_layout.addWidget(rl_widget, 3, 1)

        # RL model list update removed - use internal RL-DBA instead

        # Arquitectura de simulación (OCULTA - siempre híbrida event-driven)
        self.architecture_label = QLabel(tr("integrated_pon_panel.architecture"))
        self.architecture_label.setVisible(False)  # Ocultar etiqueta
        config_layout.addWidget(self.architecture_label, 5, 0)
        self.hybrid_checkbox = QCheckBox(tr("integrated_pon_panel.hybrid_architecture"))
        self.hybrid_checkbox.setChecked(True)  # Por defecto usar híbrida (siempre activo)
        self.hybrid_checkbox.setVisible(False)  # Ocultar checkbox
        self.hybrid_checkbox.setToolTip(tr("integrated_pon_panel.hybrid_tooltip"))
        self.hybrid_checkbox.toggled.connect(self.on_architecture_changed)
        config_layout.addWidget(self.hybrid_checkbox, 5, 1)

        # Tiempo de simulación (para arquitectura híbrida)
        self.time_label = QLabel(tr("integrated_pon_panel.time_seconds"))
        config_layout.addWidget(self.time_label, 6, 0)
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1, 120)
        self.duration_spinbox.setValue(10)
        self.duration_spinbox.setToolTip(tr("integrated_pon_panel.time_tooltip"))
        self.duration_spinbox.valueChanged.connect(self.on_duration_changed)
        config_layout.addWidget(self.duration_spinbox, 6, 1)

        # Pasos de simulación (OCULTOS - no se usan en arquitectura híbrida)
        self.steps_label = QLabel(tr("integrated_pon_panel.steps"))
        self.steps_label.setVisible(False)  # Ocultar etiqueta
        config_layout.addWidget(self.steps_label, 7, 0)
        self.steps_spinbox = QSpinBox()
        self.steps_spinbox.setRange(100, 10000)
        self.steps_spinbox.setValue(1000)
        self.steps_spinbox.setSingleStep(100)
        self.steps_spinbox.setVisible(False)  # Ocultar control
        self.steps_spinbox.setToolTip(tr("integrated_pon_panel.steps_tooltip"))
        config_layout.addWidget(self.steps_spinbox, 7, 1)
        
        layout.addWidget(self.config_group)
        
        # Controles de simulación
        self.sim_group = QGroupBox(tr("integrated_pon_panel.simulation_group"))
        sim_layout = QVBoxLayout(self.sim_group)
        
        # Botones principales
        buttons_layout = QGridLayout()
        
        self.init_btn = QPushButton(tr("integrated_pon_panel.manual_init"))
        self.init_btn.clicked.connect(self.initialize_simulation)
        self.init_btn.setToolTip(tr("integrated_pon_panel.manual_init_tooltip"))
        self.init_btn.setVisible(False)  # Ocultar por defecto - inicialización es automática
        buttons_layout.addWidget(self.init_btn, 0, 0)
        
        self.start_btn = QPushButton(tr("integrated_pon_panel.execute"))
        self.start_btn.clicked.connect(self.run_full_simulation)
        self.start_btn.setEnabled(False)
        buttons_layout.addWidget(self.start_btn, 0, 1)
        
        sim_layout.addLayout(buttons_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        sim_layout.addWidget(self.progress_bar)
        
        # Opciones adicionales
        options_layout = QVBoxLayout()
        
        self.popup_window_checkbox = QCheckBox(tr("integrated_pon_panel.show_popup"))
        self.popup_window_checkbox.setChecked(True)
        options_layout.addWidget(self.popup_window_checkbox)
        
        self.detailed_log_checkbox = QCheckBox(tr("integrated_pon_panel.detailed_logging"))
        self.detailed_log_checkbox.setChecked(True)
        self.detailed_log_checkbox.toggled.connect(self.toggle_detailed_logging)
        options_layout.addWidget(self.detailed_log_checkbox)
        
        self.auto_init_checkbox = QCheckBox(tr("integrated_pon_panel.auto_init"))
        self.auto_init_checkbox.setChecked(True)
        self.auto_init_checkbox.setToolTip(tr("integrated_pon_panel.auto_init_tooltip"))
        self.auto_init_checkbox.toggled.connect(self.toggle_auto_initialize)
        self.auto_init_checkbox.setVisible(False)  # Invisible pero siempre activo
        options_layout.addWidget(self.auto_init_checkbox)
        
        sim_layout.addLayout(options_layout)
        
        # Panel de información del agente RL (inicialmente oculto)
        self.rl_info_group = QGroupBox(tr("integrated_pon_panel.rl_agent_group"))
        self.rl_info_group.setVisible(False)
        rl_info_layout = QVBoxLayout(self.rl_info_group)
        
        self.rl_model_info_label = QLabel(tr("integrated_pon_panel.rl_model_info"))
        self.rl_model_info_label.setWordWrap(True)
        rl_info_layout.addWidget(self.rl_model_info_label)
        
        self.rl_decisions_label = QLabel(tr("integrated_pon_panel.rl_decisions").format(0))
        rl_info_layout.addWidget(self.rl_decisions_label)
        
        self.rl_last_action_label = QLabel(tr("integrated_pon_panel.rl_last_action"))
        self.rl_last_action_label.setWordWrap(True)
        rl_info_layout.addWidget(self.rl_last_action_label)
        
        sim_layout.addWidget(self.rl_info_group)
        
        # Información sobre visualización de resultados
        self.info_label = QLabel(tr("integrated_pon_panel.results_info"))
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #666; font-style: italic; padding: 4px;")
        sim_layout.addWidget(self.info_label)
        
        layout.addWidget(self.sim_group)
        
        
        layout.addStretch()
        
        return panel
    
    def check_pon_status(self):
        """Verificar estado del sistema PON"""
        if self.adapter.is_pon_available():
            self.status_label.setText(tr("integrated_pon_panel.status_available"))
            self.status_label.setStyleSheet("color: green;")
            
            # Configurar callback de logging
            self.adapter.set_log_callback(self.results_panel.add_log_message)
            
        else:
            self.status_label.setText(tr("integrated_pon_panel.status_unavailable"))
            self.status_label.setStyleSheet("color: red;")
            
            # Deshabilitar controles
            for widget in self.findChildren((QPushButton, QComboBox, QSpinBox)):
                widget.setEnabled(False)
    
    def auto_reinitialize(self, change_description="configuración"):
        """Reinicializar automáticamente cuando se detecten cambios"""
        if not self.auto_initialize or not self.adapter.is_pon_available():
            return
            
        self.status_label.setText(f"🔄 Auto-reinicializando por cambio en {change_description}...")
        self.status_label.setStyleSheet("color: blue;")
        
        # Pequeño delay para que el usuario vea el mensaje
        QTimer.singleShot(500, self.initialize_simulation)
    
    def get_onu_count_from_topology(self):
        """Obtener número de ONUs conectadas a OLTs desde la topología del canvas"""
        try:
            if not (self.canvas_reference and hasattr(self.canvas_reference, 'device_manager')):
                print(f"DEBUG Canvas reference: {self.canvas_reference}")
                if self.canvas_reference:
                    print(f"DEBUG Canvas tiene device_manager: {hasattr(self.canvas_reference, 'device_manager')}")
                return 0
            
            # Obtener estadísticas básicas
            device_stats = self.canvas_reference.device_manager.get_device_stats()
            total_devices = device_stats.get('total_devices', 0)
            olt_count = device_stats.get('olt_count', 0)
            total_onus = device_stats.get('onu_count', 0)
            
            # Si no hay conexiones, ninguna ONU está conectada
            if not hasattr(self.canvas_reference, 'connection_manager'):
                if getattr(self, 'verbose_debug', False):
                    print(f"DEBUG Canvas no tiene connection_manager")
                return 0
            
            connection_manager = self.canvas_reference.connection_manager
            
            # Obtener todas las ONUs y OLTs
            all_onus = self.canvas_reference.device_manager.get_devices_by_type("ONU")
            all_olts = self.canvas_reference.device_manager.get_devices_by_type("OLT")
            
            # Solo mostrar debug si hay cambios significativos en dispositivos
            current_total = len(all_olts) + len(all_onus)
            if not hasattr(self, '_last_device_count') or self._last_device_count != current_total:
                if getattr(self, 'verbose_debug', False):
                    print(f"DEBUG Dispositivos encontrados: {len(all_olts)} OLTs, {len(all_onus)} ONUs totales")
                self._last_device_count = current_total
            
            # Contar ONUs conectadas a cualquier OLT
            connected_onus = 0
            connected_onu_names = []
            
            for onu in all_onus:
                # Verificar si esta ONU está conectada a alguna OLT
                is_connected = False
                for olt in all_olts:
                    connection = connection_manager.get_connection_between(onu, olt)
                    if connection:
                        is_connected = True
                        connected_onu_names.append(f"{onu.name}↔{olt.name}")
                        break
                
                if is_connected:
                    connected_onus += 1
            
            # Solo mostrar estadísticas detalladas si hay cambios importantes
            if connected_onus != getattr(self, '_last_connected_count', -1):
                if getattr(self, 'verbose_debug', False):
                    print(f"DEBUG Estadísticas: Total={total_devices}, OLTs={olt_count}, ONUs totales={total_onus}, ONUs conectadas={connected_onus}")
                    if connected_onu_names:
                        print(f"DEBUG ONUs conectadas: {connected_onu_names}")
                self._last_connected_count = connected_onus
            
            return connected_onus
            
        except Exception as e:
            print(f"❌ Error obteniendo conteo de ONUs conectadas: {e}")
            if getattr(self, 'verbose_debug', False):
                import traceback
                traceback.print_exc()
            return 0
    
    def update_onu_count_display(self):
        """Actualizar la visualización del conteo de ONUs"""
        try:
            # Solo debug en modo verbose
            if getattr(self, 'verbose_debug', False):
                print("DEBUG Iniciando update_onu_count_display()")
                
            current_onus = self.get_onu_count_from_topology()
            
            # Solo mostrar debug si cambió el valor
            if not hasattr(self, '_last_debug_count') or self._last_debug_count != current_onus:
                if getattr(self, 'verbose_debug', False):
                    print(f"DEBUG Conteo obtenido: {current_onus}")
                self._last_debug_count = current_onus
            
            # Actualizar el texto del label
            self.onu_count_label.setText(str(current_onus))
            
            # Cambiar estilo según el número detectado (sin debug repetitivo)
            if current_onus == 0:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #dc2626; padding: 4px; background-color: #fef2f2; border-radius: 4px;")
                self.onu_count_label.setToolTip("No se detectaron ONUs conectadas a OLTs")
            elif current_onus < 2:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #f59e0b; padding: 4px; background-color: #fffbeb; border-radius: 4px;")
                self.onu_count_label.setToolTip(tr('integrated_pon_panel.onus_tooltip_insufficient'))
            else:
                self.onu_count_label.setStyleSheet("font-weight: bold; color: #059669; padding: 4px; background-color: #ecfdf5; border-radius: 4px;")
                self.onu_count_label.setToolTip(f"{current_onus} ONUs conectadas - listo para simular")
            
            # Detectar cambios y reinicializar si es necesario
            if self.orchestrator_initialized and current_onus != self.last_onu_count:
                # Solo log cuando realmente hay cambios importantes
                print(f"🔄 ONUs cambiaron: {self.last_onu_count} → {current_onus}")
                self.auto_reinitialize(f"número de ONUs (detectadas: {current_onus})")
            elif not self.orchestrator_initialized and current_onus >= 2:
                # Solo mostrar una vez cuando se detectan ONUs suficientes
                if not hasattr(self, '_onu_ready_logged') or not self._onu_ready_logged:
                    print(f"✅ Detectadas {current_onus} ONUs - listo para inicializar")
                    self._onu_ready_logged = True
                    
                # Intentar inicializar automáticamente si hay ONUs suficientes
                if self.auto_initialize:
                    QTimer.singleShot(500, self.initialize_simulation)
            
            self.last_onu_count = current_onus
            return current_onus
            
        except Exception as e:
            print(f"ERROR actualizando display de ONUs: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def on_algorithm_changed(self):
        """Manejar cambio de algoritmo DBA"""
        algorithm = self.algorithm_combo.currentText()
        
        # Ignorar si es un header (separador)
        if "━━━" in algorithm:
            # Restaurar el último algoritmo válido seleccionado
            if hasattr(self, 'last_algorithm') and self.last_algorithm:
                index = self.algorithm_combo.findText(self.last_algorithm)
                if index >= 0:
                    self.algorithm_combo.setCurrentIndex(index)
            return

        # Mostrar/ocultar controles de modelo RL
        is_rl_algorithm = (algorithm == "RL Agent")
        # RL model UI removed - functionality moved to internal RL-DBA
        self.rl_info_group.setVisible(is_rl_algorithm)

        if self.orchestrator_initialized and algorithm != self.last_algorithm:
            self.auto_reinitialize(f"algoritmo DBA ({algorithm})")
        self.last_algorithm = algorithm

    def on_duration_changed(self):
        """Manejar cambio de duración de simulación"""
        duration = self.duration_spinbox.value()
        if self.orchestrator_initialized and duration != self.last_duration:
            self.auto_reinitialize(f"tiempo de simulación ({duration}s)")
        self.last_duration = duration
    
    def on_edit_custom_algorithm(self, algorithm_name):
        """Editar un algoritmo personalizado - Abre editor dual"""
        try:
            import os
            import re
            from PyQt5.QtWidgets import QDialog, QTextEdit, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
            from PyQt5.QtGui import QFont
            from PyQt5.QtCore import Qt

            # --- Rutas ---
            ui_dir = os.path.dirname(os.path.abspath(__file__))
            algo_dir = os.path.abspath(os.path.join(ui_dir, "..", "core", "algorithms"))
            template_path = os.path.join(algo_dir, "template_Algo_DBA.txt")
            pon_dba_path = os.path.join(algo_dir, "pon_dba.py")

            if not os.path.exists(template_path):
                QMessageBox.warning(self, "Archivo no encontrado",
                                    f"No se encontró el archivo de guía:\n{template_path}")
                return
            
            if not os.path.exists(pon_dba_path):
                QMessageBox.warning(self, "Error", f"No se encontró el archivo:\n{pon_dba_path}")
                return

            # Leer el template
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
            
            # Leer pon_dba.py y extraer el código del algoritmo específico
            with open(pon_dba_path, "r", encoding="utf-8") as f:
                pon_dba_content = f.read()
            
            # Buscar la clase del algoritmo (nombre de clase, no nombre del algoritmo)
            # Primero necesitamos encontrar la clase que corresponde a este algoritmo
            # Buscar todas las clases y sus métodos get_algorithm_name
            class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*DBAAlgorithmInterface\s*\)\s*:(.*?)(?=\nclass\s|\Z)'
            classes = re.finditer(class_pattern, pon_dba_content, re.DOTALL)
            
            algorithm_code = None
            class_name_found = None
            
            for match in classes:
                class_name = match.group(1)
                class_body = match.group(2)
                
                # Buscar get_algorithm_name en esta clase
                name_match = re.search(
                    r'def\s+get_algorithm_name\s*\([^)]*\)\s*(?:->\s*[A-Za-z_][A-Za-z0-9_\[\],\s]*)?\s*:[\s\S]*?return\s*[\'"]([^\'"]+)[\'"]',
                    class_body
                )
                
                if name_match and name_match.group(1).strip() == algorithm_name:
                    # Encontramos la clase correcta
                    algorithm_code = match.group(0)
                    class_name_found = class_name
                    break
            
            if not algorithm_code:
                QMessageBox.warning(self, "Error", 
                    f"No se encontró el código del algoritmo '{algorithm_name}' en pon_dba.py")
                return

            # --- Geometría base (área útil) ---
            probe = QDialog(self)
            work = probe.screen().availableGeometry()
            
            # Calcular dimensiones dejando margen para botones y barra de tareas
            window_height = work.height() - 80  # Reducir 80px para ver botones
            window_width = work.width() // 2

            # =========================
            #  Ventana IZQUIERDA (Template - solo lectura)
            # =========================
            left = QDialog(None)
            left.setWindowTitle("Template de Algoritmo DBA (Guía)")
            left.setModal(False)
            left.setWindowFlags(Qt.Window | Qt.WindowTitleHint |
                                Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
            left.setAttribute(Qt.WA_DeleteOnClose, True)
            left.setStyleSheet("""
                QDialog { background-color: #1f1f1f; }
                QTextEdit {
                    background-color: #232629; color: #e0e0e0; border: none;
                    padding: 10px; selection-background-color: #3b82f6; selection-color: #ffffff;
                }
                QPushButton {
                    background-color: #2d3748; color: #e2e8f0; border: 1px solid #3a3f44;
                    border-radius: 6px; padding: 6px 10px;
                }
                QPushButton:hover { background-color: #3b495c; }
                QPushButton:pressed { background-color: #2a3341; }
            """)
            left.setGeometry(work.x(), work.y(), window_width, window_height)

            l_root = QVBoxLayout(left)
            l_root.setContentsMargins(8, 8, 8, 8)
            l_root.setSpacing(8)
            l_view = QTextEdit()
            l_view.setReadOnly(True)
            l_view.setLineWrapMode(QTextEdit.NoWrap)
            l_view.setFont(QFont("Consolas", 10))
            l_view.setPlainText(template_content)
            l_root.addWidget(l_view)

            l_btns = QHBoxLayout()
            l_btns.addStretch(1)
            l_copy = QPushButton(tr("integrated_pon_panel.copy_all"))
            l_copy.clicked.connect(lambda: (l_view.selectAll(), l_view.copy(),
                                            QMessageBox.information(left, tr("integrated_pon_panel.copied_title"), 
                                                                   tr("integrated_pon_panel.template_copied"))))
            l_btns.addWidget(l_copy)
            l_root.addLayout(l_btns)

            # =========================
            #  Ventana DERECHA (Algoritmo - editable)
            # =========================
            right = QDialog(None)
            right.setWindowTitle(f"Editando: {algorithm_name} (clase {class_name_found})")
            right.setModal(False)
            right.setWindowFlags(Qt.Window | Qt.WindowTitleHint |
                                Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
            right.setAttribute(Qt.WA_DeleteOnClose, True)
            right.setStyleSheet(left.styleSheet())
            right.setGeometry(work.x() + window_width, work.y(),
                            window_width, window_height)

            r_root = QVBoxLayout(right)
            r_root.setContentsMargins(8, 8, 8, 8)
            r_root.setSpacing(8)
            r_edit = QTextEdit()
            r_edit.setLineWrapMode(QTextEdit.NoWrap)
            r_edit.setFont(QFont("Consolas", 10))
            r_edit.setPlainText(algorithm_code)
            r_root.addWidget(r_edit)

            r_btns = QHBoxLayout()
            r_btns.addStretch(1)
            
            # === CIERRE COORDINADO (una sola confirmación) ===
            # Usamos un flag compartido para evitar doble diálogo al cerrar la otra ventana.
            _closing_state = {"active": False}

            def _confirm_close():
                resp = QMessageBox.question(
                    None,
                    tr("integrated_pon_panel.close_editor_title"),
                    tr("integrated_pon_panel.close_editor_confirm"),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                return resp == QMessageBox.Yes
            
            r_save = QPushButton(tr("integrated_pon_panel.save_changes"))

            def _save_edit():
                try:
                    new_code = r_edit.toPlainText()
                    
                    # Validar que sigue siendo la misma clase
                    new_class_match = re.search(r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*DBAAlgorithmInterface\s*\)\s*:', new_code)
                    if not new_class_match:
                        QMessageBox.warning(right, "Error de Sintaxis",
                            "No se encontró una clase que herede de DBAAlgorithmInterface")
                        return
                    
                    new_class_name = new_class_match.group(1)
                    
                    # Extraer el NUEVO nombre del algoritmo
                    new_name_match = re.search(
                        r'def\s+get_algorithm_name\s*\([^)]*\)\s*(?:->\s*[A-Za-z_][A-Za-z0-9_\[\],\s]*)?\s*:[\s\S]*?return\s*[\'"]([^\'"]+)[\'"]',
                        new_code
                    )
                    new_algorithm_name = new_name_match.group(1).strip() if new_name_match else algorithm_name
                    
                    # Reemplazar el código antiguo con el nuevo en pon_dba.py
                    updated_content = pon_dba_content.replace(algorithm_code, new_code)
                    
                    # Guardar en pon_dba.py
                    with open(pon_dba_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                    
                    # Actualizar pon_adapter.py si cambió el nombre de la clase o el nombre del algoritmo
                    modified_files = ["pon_dba.py"]
                    if new_class_name != class_name_found or new_algorithm_name != algorithm_name:
                        adapter_path = os.path.join(algo_dir, "..", "pon", "pon_adapter.py")
                        if os.path.exists(adapter_path):
                            with open(adapter_path, "r", encoding="utf-8") as f:
                                adapter_content = f.read()
                            
                            # 1. Reemplazar nombre de clase en imports si cambió
                            if new_class_name != class_name_found:
                                adapter_content = adapter_content.replace(class_name_found, new_class_name)
                            
                            # 2. Actualizar el nombre del algoritmo en la lista
                            if new_algorithm_name != algorithm_name:
                                # Reemplazar en la lista de algoritmos
                                list_pattern = rf'"{re.escape(algorithm_name)}"'
                                adapter_content = re.sub(list_pattern, f'"{new_algorithm_name}"', adapter_content)
                                
                                # Reemplazar la clave del diccionario
                                dict_pattern = rf'"{re.escape(algorithm_name)}"(\s*:\s*){re.escape(class_name_found if new_class_name == class_name_found else new_class_name)}'
                                adapter_content = re.sub(dict_pattern, f'"{new_algorithm_name}"\\1{new_class_name}', adapter_content)
                            
                            with open(adapter_path, "w", encoding="utf-8") as f:
                                f.write(adapter_content)
                            
                            modified_files.append("pon_adapter.py")
                    
                    # Mensaje final con opción de reinicio
                    msg = QMessageBox(right)
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle(tr("integrated_pon_panel.algorithm_edited_title"))
                    msg.setText(tr("integrated_pon_panel.algorithm_edited_text").format(algorithm_name))
                    
                    # Detalles formateados
                    files_list = "<br>".join(f"&nbsp;&nbsp;- {f}" for f in modified_files)
                    details = tr("integrated_pon_panel.algorithm_edited_details").format(new_class_name, files_list)
                    msg.setInformativeText(details)
                    msg.setTextFormat(Qt.RichText)
                    
                    # Estilo personalizado para mejor legibilidad
                    msg.setStyleSheet("""
                        QMessageBox {
                            background-color: #f8f9fa;
                        }
                        QMessageBox QLabel {
                            color: #1a1a1a;
                            background-color: transparent;
                            font-size: 11pt;
                            padding: 8px;
                        }
                        QMessageBox QPushButton {
                            background-color: #0d6efd;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 8px 16px;
                            font-weight: bold;
                            min-width: 80px;
                        }
                        QMessageBox QPushButton:hover {
                            background-color: #0b5ed7;
                        }
                        QMessageBox QPushButton:pressed {
                            background-color: #0a58ca;
                        }
                    """)
                    
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                    
                    # Cerrar sin confirmación después de guardar exitosamente
                    _closing_state["active"] = True
                    right.close()
                    left.close()
                    
                    # Reiniciar la aplicación
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(300, self._restart_application)
                    
                except Exception as e:
                    QMessageBox.critical(right, "Error al Guardar",
                        f"Error al guardar cambios: {str(e)}")

            r_save.clicked.connect(_save_edit)
            r_btns.addWidget(r_save)
            
            r_cancel = QPushButton(tr("integrated_pon_panel.cancel"))
            
            def _cancel_edit():
                # Activar el flag y cerrar ambas ventanas
                # Esto disparará _confirm_close() solo una vez
                if _confirm_close():
                    _closing_state["active"] = True
                    right.close()
                    left.close()
            
            r_cancel.clicked.connect(_cancel_edit)
            r_btns.addWidget(r_cancel)
            
            r_root.addLayout(r_btns)

            def _left_close(ev):
                # Si ya estamos cerrando (por la otra ventana), no preguntar de nuevo.
                if _closing_state["active"]:
                    ev.accept()
                    return

                if _confirm_close():
                    _closing_state["active"] = True
                    try:
                        # Cerrar la otra SIN volver a preguntar
                        right.close()
                    finally:
                        ev.accept()
                else:
                    ev.ignore()

            def _right_close(ev):
                # Si ya estamos cerrando (por la otra ventana), no preguntar de nuevo.
                if _closing_state["active"]:
                    ev.accept()
                    return

                if _confirm_close():
                    _closing_state["active"] = True
                    try:
                        # Cerrar la otra SIN volver a preguntar
                        left.close()
                    finally:
                        ev.accept()
                else:
                    ev.ignore()

            left.closeEvent = _left_close
            right.closeEvent = _right_close
            # === FIN CIERRE COORDINADO ===

            # Mostrar ventanas
            left.show()
            right.show()

            # Ajustar posición para snap
            def snap_windows():
                frame_tl = left.frameGeometry().topLeft()
                geom_tl = left.geometry().topLeft()
                dx = frame_tl.x() - geom_tl.x()
                dy = frame_tl.y() - geom_tl.y()
                left.move(work.x() - dx, work.y() - dy)
                right.move(work.x() + window_width - dx, work.y() - dy)

            QTimer.singleShot(100, snap_windows)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al editar algoritmo: {str(e)}")
            import traceback
            traceback.print_exc()

    
    def on_delete_custom_algorithm(self, algorithm_name):
        """Eliminar un algoritmo personalizado"""
        try:
            import os
            import re
            import sys
            
            # Confirmar eliminación
            reply = QMessageBox.question(
                self, 
                "Confirmar Eliminación",
                f"¿Estás seguro de que deseas eliminar el algoritmo '{algorithm_name}'?\n\n"
                f"Esta acción no se puede deshacer.\n"
                f"La aplicación se reiniciará automáticamente después de eliminar.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Obtener rutas
            ui_dir = os.path.dirname(os.path.abspath(__file__))
            algo_dir = os.path.abspath(os.path.join(ui_dir, "..", "core", "algorithms"))
            pon_dba_path = os.path.join(algo_dir, "pon_dba.py")
            adapter_path = os.path.join(algo_dir, "..", "pon", "pon_adapter.py")
            
            # =========================================================
            # PASO 1: Encontrar la clase correcta en pon_dba.py
            # =========================================================
            with open(pon_dba_path, "r", encoding="utf-8") as f:
                pon_dba_content = f.read()
            
            # Buscar la clase que corresponde a este algoritmo
            class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*DBAAlgorithmInterface\s*\)\s*:(.*?)(?=\nclass\s|\Z)'
            classes = re.finditer(class_pattern, pon_dba_content, re.DOTALL)
            
            class_name_found = None
            algorithm_code = None
            
            for match in classes:
                class_name = match.group(1)
                class_body = match.group(2)
                
                # Buscar get_algorithm_name en esta clase
                name_match = re.search(
                    r'def\s+get_algorithm_name\s*\([^)]*\)\s*(?:->\s*[A-Za-z_][A-Za-z0-9_\[\],\s]*)?\s*:[\s\S]*?return\s*[\'"]([^\'"]+)[\'"]',
                    class_body
                )
                
                if name_match and name_match.group(1).strip() == algorithm_name:
                    # Encontramos la clase correcta
                    algorithm_code = match.group(0)
                    class_name_found = class_name
                    break
            
            if not class_name_found:
                QMessageBox.warning(self, "Error", 
                    f"No se encontró la clase del algoritmo '{algorithm_name}' en pon_dba.py")
                return
            
            # =========================================================
            # PASO 2: Eliminar clase de pon_dba.py
            # =========================================================
            new_pon_dba_content = pon_dba_content.replace(algorithm_code, '')
            
            # Limpiar líneas en blanco múltiples (más de 2 líneas vacías → 2 líneas vacías)
            new_pon_dba_content = re.sub(r'\n{3,}', '\n\n', new_pon_dba_content)
            
            # Guardar pon_dba.py
            with open(pon_dba_path, "w", encoding="utf-8") as f:
                f.write(new_pon_dba_content)
            
            # =========================================================
            # PASO 3: Actualizar pon_adapter.py
            # =========================================================
            with open(adapter_path, "r", encoding="utf-8") as f:
                adapter_content = f.read()
            
            # 3.1 - ELIMINAR DEL IMPORT
            # Buscar el bloque de import completo
            import_match = re.search(
                r'(from\s+\.\.algorithms\.pon_dba\s+import\s+\(\s*)(.*?)(\s*\))',
                adapter_content,
                re.DOTALL
            )
            
            if import_match:
                import_prefix = import_match.group(1)
                import_body = import_match.group(2)
                import_suffix = import_match.group(3)
                
                # Dividir en líneas y procesar
                import_lines = import_body.split('\n')
                new_import_lines = []
                
                for line in import_lines:
                    # Verificar si esta línea contiene SOLO el nombre de clase a eliminar
                    # Buscar identificadores en la línea
                    identifiers = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\b', line)
                    
                    # Si la línea contiene el nombre de clase a eliminar, omitirla
                    if class_name_found not in identifiers:
                        new_import_lines.append(line)
                
                # Reconstruir el import
                new_import_body = '\n'.join(new_import_lines)
                
                # Limpiar comas problemáticas
                # Eliminar comas al inicio o final de líneas
                new_import_body = re.sub(r'^\s*,\s*', '', new_import_body, flags=re.MULTILINE)
                new_import_body = re.sub(r',\s*$', '', new_import_body, flags=re.MULTILINE)
                # Eliminar comas duplicadas
                new_import_body = re.sub(r',\s*,', ',', new_import_body)
                # Asegurar que cada entrada excepto la última tenga coma
                lines = [l.strip() for l in new_import_body.split('\n') if l.strip()]
                for i in range(len(lines) - 1):
                    if lines[i] and not lines[i].endswith(','):
                        lines[i] = lines[i] + ','
                new_import_body = '\n        '.join(lines)
                
                # Reemplazar en el contenido
                new_import_block = import_prefix + new_import_body + import_suffix
                adapter_content = adapter_content[:import_match.start()] + new_import_block + adapter_content[import_match.end():]
            
            # 3.2 - ELIMINAR DE LA LISTA algorithms = [...]
            # Buscar y modificar la lista
            list_match = re.search(
                r'(algorithms\s*=\s*\[)([^\]]*?)(\])',
                adapter_content,
                re.DOTALL
            )
            
            if list_match:
                list_prefix = list_match.group(1)
                list_body = list_match.group(2)
                list_suffix = list_match.group(3)
                
                # Eliminar el algoritmo de la lista
                # Buscar el patrón exacto: "algorithm_name" o 'algorithm_name' con posible coma
                list_body = re.sub(
                    rf'["\']' + re.escape(algorithm_name) + rf'["\'],?\s*',
                    '',
                    list_body
                )
                
                # Limpiar comas duplicadas y espacios
                list_body = re.sub(r',\s*,', ',', list_body)
                list_body = re.sub(r'\[\s*,', '[', list_body)
                list_body = re.sub(r',\s*\]', ']', list_body)
                
                # Reconstruir la lista
                new_list_block = list_prefix + list_body + list_suffix
                adapter_content = adapter_content[:list_match.start()] + new_list_block + adapter_content[list_match.end():]
            
            # 3.3 - ELIMINAR DEL DICCIONARIO algorithms = {...}
            # Buscar y modificar el diccionario
            dict_match = re.search(
                r'(algorithms\s*=\s*\{)([^\}]*?)(\})',
                adapter_content,
                re.DOTALL
            )
            
            if dict_match:
                dict_prefix = dict_match.group(1)
                dict_body = dict_match.group(2)
                dict_suffix = dict_match.group(3)
                
                # Eliminar la entrada del diccionario
                # Patrón: "algorithm_name": ClassName,
                dict_body = re.sub(
                    rf'["\']' + re.escape(algorithm_name) + rf'["\']\s*:\s*{re.escape(class_name_found)}\s*,?\s*\n?',
                    '',
                    dict_body
                )
                
                # Limpiar comas duplicadas
                dict_body = re.sub(r',\s*,', ',', dict_body)
                dict_body = re.sub(r'\{\s*,', '{', dict_body)
                dict_body = re.sub(r',\s*\}', '}', dict_body)
                
                # Reconstruir el diccionario
                new_dict_block = dict_prefix + dict_body + dict_suffix
                adapter_content = adapter_content[:dict_match.start()] + new_dict_block + adapter_content[dict_match.end():]
            
            # Guardar pon_adapter.py
            with open(adapter_path, "w", encoding="utf-8") as f:
                f.write(adapter_content)
            
            # =========================================================
            # PASO 4: Confirmar y reiniciar
            # =========================================================
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle(tr("integrated_pon_panel.algorithm_deleted_title"))
            msg.setText(tr("integrated_pon_panel.algorithm_deleted_text").format(algorithm_name))
            
            # Detalles formateados
            details = tr("integrated_pon_panel.algorithm_deleted_details").format(class_name_found)
            msg.setInformativeText(details)
            msg.setTextFormat(Qt.RichText)
            
            # Estilo personalizado para mejor legibilidad
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #f8f9fa;
                }
                QMessageBox QLabel {
                    color: #1a1a1a;
                    background-color: transparent;
                    font-size: 11pt;
                    padding: 8px;
                }
                QMessageBox QPushButton {
                    background-color: #0d6efd;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #0b5ed7;
                }
                QMessageBox QPushButton:pressed {
                    background-color: #0a58ca;
                }
            """)
            
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            # Reiniciar la aplicación
            QTimer.singleShot(500, lambda: self._restart_application())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar algoritmo: {str(e)}")
            import traceback
            traceback.print_exc()

    
    def _restart_application(self):
        """Reiniciar la aplicación"""
        try:
            import sys
            import os
            import subprocess
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer
            
            # Obtener el ejecutable de Python y el script principal
            python = sys.executable
            script = os.path.abspath(sys.argv[0])
            args = [python, script] + sys.argv[1:]
            
            # Función para iniciar nuevo proceso y cerrar actual
            def start_new_instance():
                # Iniciar nuevo proceso de forma independiente
                if sys.platform == 'win32':
                    # En Windows, usar DETACHED_PROCESS para independizar el proceso
                    DETACHED_PROCESS = 0x00000008
                    subprocess.Popen(args, creationflags=DETACHED_PROCESS)
                else:
                    # En Unix-like systems
                    subprocess.Popen(args, start_new_session=True)
                
                # Cerrar la aplicación actual completamente
                QApplication.instance().quit()
            
            # Dar un pequeño delay para asegurar que los archivos se guarden
            QTimer.singleShot(200, start_new_instance)
            
        except Exception as e:
            QMessageBox.critical(self, "Error al Reiniciar", 
                f"No se pudo reiniciar la aplicación automáticamente.\n\n"
                f"Por favor, reinicia manualmente.\n\nError: {str(e)}")


    def load_smart_rl_model(self):
        """Cargar modelo RL entrenado para Smart RL DBA"""
        # Diálogo para seleccionar archivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar modelo RL entrenado",
            "",
            "Modelos RL (*.zip);;Todos los archivos (*)"
        )

        if not file_path:
            return

        try:
            # Obtener parámetros del entorno actual
            env_params = {
                'num_onus': self.get_onu_count_from_topology(),
                'traffic_scenario': 'residential_medium',  # Escenario por defecto (se usa si ONU no tiene configuración)
                'episode_duration': self.duration_spinbox.value(),
                'simulation_timestep': 0.0005
            }

            # Cargar modelo usando PONAdapter
            success, message = self.adapter.load_rl_model(file_path, env_params)

            if success:
                # Actualizar UI
                model_name = os.path.basename(file_path)
                self.rl_status_label.setText(f"✅ {model_name}")
                self.rl_status_label.setStyleSheet("color: green; font-size: 8pt;")

                # Cuando se carga un modelo RL, permitir Smart-RL y Smart-RL-SDN
                self.algorithm_combo.clear()
                self.algorithm_combo.addItem("Smart-RL")
                self.algorithm_combo.addItem("Smart-RL-SDN")
                self.algorithm_combo.setCurrentText("Smart-RL")

                # Marcar que hay un modelo RL cargado
                self.rl_model_loaded = True

                # Mostrar botón de desactivar RL
                self.unload_rl_model_btn.setVisible(True)

                # Mostrar mensaje de éxito
                QMessageBox.information(
                    self,
                    "Modelo Cargado",
                    f"Modelo RL cargado exitosamente:\n{model_name}\n\nAlgoritmos disponibles: 'Smart-RL' y 'Smart-RL-SDN'."
                )

                # Log
                self.results_panel.add_log_message(f"[SMART-RL] Modelo cargado: {model_name}")

                # Auto-reinicializar si es necesario
                if self.orchestrator_initialized:
                    self.auto_reinitialize(f"modelo Smart-RL cargado")

            else:
                # Error cargando
                self.rl_status_label.setText("❌ Error cargando")
                self.rl_status_label.setStyleSheet("color: red; font-size: 8pt;")

                QMessageBox.warning(
                    self,
                    "Error",
                    f"Error cargando modelo RL:\n{message}"
                )

                self.results_panel.add_log_message(f"[ERROR] Error cargando modelo RL: {message}")

        except Exception as e:
            error_msg = f"Error inesperado cargando modelo: {str(e)}"
            self.rl_status_label.setText("❌ Error")
            self.rl_status_label.setStyleSheet("color: red; font-size: 8pt;")

            QMessageBox.critical(self, "Error", error_msg)
            self.results_panel.add_log_message(f"[ERROR] {error_msg}")

    def unload_rl_model(self):
        """Desactivar modelo RL y volver a algoritmos normales"""
        try:
            # Log estado inicial
            self.results_panel.add_log_message("[DEBUG] Iniciando desactivación RL...")

            # Verificar estado antes de desactivar
            if hasattr(self.adapter, 'smart_rl_algorithm'):
                has_smart_rl = self.adapter.smart_rl_algorithm is not None
                self.results_panel.add_log_message(f"[DEBUG] PONAdapter.smart_rl_algorithm antes: {has_smart_rl}")

            # Descargar modelo del adapter (PONAdapter system)
            if hasattr(self.adapter, 'unload_rl_model'):
                success, message = self.adapter.unload_rl_model()
                self.results_panel.add_log_message(f"[PON-ADAPTER] Desactivación: {message}")

                # Verificar estado después
                if hasattr(self.adapter, 'smart_rl_algorithm'):
                    has_smart_rl_after = self.adapter.smart_rl_algorithm is not None
                    self.results_panel.add_log_message(f"[DEBUG] PONAdapter.smart_rl_algorithm después: {has_smart_rl_after}")

            # Descargar modelo del training manager (TrainingManager system)
            if self.training_manager and hasattr(self.training_manager, 'simulation_manager'):
                if hasattr(self.training_manager.simulation_manager, 'loaded_model'):
                    had_model = self.training_manager.simulation_manager.loaded_model is not None
                    self.training_manager.simulation_manager.loaded_model = None
                    self.results_panel.add_log_message(f"[TRAINING-MANAGER] Modelo desactivado (tenía modelo: {had_model})")

            # Restaurar algoritmos DBA normales
            self.algorithm_combo.clear()
            if self.adapter.is_pon_available():
                algorithms = self.adapter.get_available_algorithms()
                self.results_panel.add_log_message(f"[DEBUG] Algoritmos disponibles después: {algorithms}")
                self.algorithm_combo.addItems(algorithms)

                # Volver a FCFS por defecto
                self.algorithm_combo.setCurrentText("FCFS")

                # CRÍTICO: Actualizar algoritmo en el adapter
                if hasattr(self.adapter, 'set_dba_algorithm'):
                    self.adapter.set_dba_algorithm("FCFS")
                    self.results_panel.add_log_message("[DEBUG] Algoritmo del adapter cambiado a FCFS")

            # Actualizar UI
            self.rl_status_label.setText(tr("integrated_pon_panel.rl_status_no_model"))
            self.rl_status_label.setStyleSheet("color: #666; font-size: 8pt;")

            # Ocultar botón de desactivar
            self.unload_rl_model_btn.setVisible(False)

            # Marcar que no hay modelo cargado
            self.rl_model_loaded = False

            # Log
            self.results_panel.add_log_message("[SMART-RL] Modelo RL desactivado - Volviendo a algoritmos normales")

            # Auto-reinicializar si es necesario
            if self.orchestrator_initialized:
                self.auto_reinitialize("modelo RL desactivado")

            # Mostrar confirmación
            QMessageBox.information(
                self,
                "RL Desactivado",
                "Simulación RL desactivada.\nAhora puede usar algoritmos DBA normales."
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Error desactivando modelo RL:\n{str(e)}"
            )

    def update_rl_status_display(self):
        """Actualizar visualización del estado del modelo RL"""
        if self.adapter.is_smart_rl_available():
            model_info = self.adapter.get_rl_model_info()
            if model_info:
                model_name = os.path.basename(model_info.get('model_path', 'Modelo'))
                decisions = model_info.get('decisions_made', 0)

                self.rl_status_label.setText(f"✅ {model_name} ({decisions} decisiones)")
                self.rl_status_label.setStyleSheet("color: green; font-size: 8pt;")
            else:
                self.rl_status_label.setText("✅ Modelo cargado")
                self.rl_status_label.setStyleSheet("color: green; font-size: 8pt;")
        else:
            self.rl_status_label.setText(tr("integrated_pon_panel.rl_status_no_model"))
            self.rl_status_label.setStyleSheet("color: #666; font-size: 8pt;")
    
    
    
    
    
    
    def on_architecture_changed(self):
        """Manejar cambio de arquitectura"""
        use_hybrid = self.hybrid_checkbox.isChecked()
        self.adapter.set_use_hybrid_architecture(use_hybrid)
        
        # Actualizar visibilidad de controles
        self.duration_spinbox.setEnabled(use_hybrid)
        self.steps_spinbox.setEnabled(not use_hybrid)
        
        arch_name = "híbrida event-driven" if use_hybrid else "clásica timesteps"
        
        # Si está inicializado, reinicializar automáticamente
        if self.orchestrator_initialized:
            self.auto_reinitialize(f"arquitectura ({arch_name})")
        
        self.results_panel.add_log_message(f"Arquitectura cambiada a: {arch_name}")
    
    def toggle_detailed_logging(self, enabled):
        """Activar/desactivar logging detallado"""
        self.adapter.set_detailed_logging(enabled)
    
    def toggle_auto_initialize(self, enabled):
        """Activar/desactivar inicialización automática"""
        self.auto_initialize = enabled
        
        # Mostrar/ocultar botón de inicialización manual según el estado
        self.init_btn.setVisible(not enabled)
        
        if enabled:
            self.results_panel.add_log_message("✅ Inicialización automática habilitada")
        else:
            self.results_panel.add_log_message("⚠️ Inicialización automática deshabilitada - usar botón manual")
            self.init_btn.setVisible(True)
    
    def perform_initial_auto_initialization(self):
        """Realizar inicialización automática inicial al cargar el panel"""
        if self.auto_initialize and not self.orchestrator_initialized:
            # Actualizar conteo de ONUs antes de inicializar
            self.update_onu_count_display()
            
            # Solo inicializar si hay ONUs suficientes
            onu_count = self.get_onu_count_from_topology()
            if onu_count >= 2:
                self.status_label.setText("🚀 Inicialización automática inicial...")
                self.status_label.setStyleSheet("color: blue;")
                self.results_panel.add_log_message(f"🎯 Iniciando configuración automática inicial con {onu_count} ONUs conectadas...")
                QTimer.singleShot(500, self.initialize_simulation)
            else:
                self.status_label.setText("⏳ Esperando topología válida...")
                self.status_label.setStyleSheet("color: orange;")
                self.results_panel.add_log_message(f"⏳ Esperando al menos 2 ONUs conectadas a OLTs (actual: {onu_count})")
    
    def initialize_simulation(self):
        """Inicializar simulación"""
        print("🚀 Inicializando simulación PON...")
        
        if not self.adapter.is_pon_available():
            if getattr(self, 'verbose_debug', False):
                print("DEBUG Adapter no disponible")
            return

        # Obtener configuración automática
        num_onus = self.get_onu_count_from_topology()
        scenario = 'residential_medium'  # Escenario por defecto (cada ONU tiene su configuración individual)
        algorithm = self.algorithm_combo.currentText()
        use_hybrid = self.hybrid_checkbox.isChecked()
        
        print(f"📊 Configuración: {num_onus} ONUs, Escenario: {scenario}, Algoritmo: {algorithm}, Híbrido: {use_hybrid}")
        
        # Validar que hay ONUs conectadas suficientes
        if num_onus < 2:
            if getattr(self, 'verbose_debug', False):
                print(f"DEBUG ONUs conectadas insuficientes: {num_onus} < 2")
            self.status_label.setText(tr('integrated_pon_panel.status_insufficient_onus'))
            self.status_label.setStyleSheet("color: red;")
            self.results_panel.add_log_message(tr('integrated_pon_panel.status_insufficient_topology').format(num_onus))
            return
        
        if use_hybrid:
            self.results_panel.add_log_message("🚀 Inicializando simulación híbrida...")
            
            # Usar topología del canvas si está disponible
            if self.canvas_reference:
                # Primero configurar el modo de simulación a "events"
                self.adapter.set_simulation_mode("events")
                # Luego inicializar desde la topología del canvas
                success, message = self.adapter.initialize_from_topology(
                    self.canvas_reference.device_manager
                )
            else:
                success, message = self.adapter.initialize_hybrid_simulator(
                    num_onus=num_onus,
                    traffic_scenario=scenario,
                    channel_capacity_mbps=1024.0
                )
        else:
            self.results_panel.add_log_message("🚀 Inicializando simulación clásica...")
            
            # Usar topología del canvas si está disponible
            if self.canvas_reference:
                success, message = self.adapter.initialize_orchestrator_from_topology(
                    self.canvas_reference.device_manager
                )
            else:
                success = self.adapter.initialize_orchestrator(num_onus)
                message = f"Orquestador inicializado con {num_onus} ONUs"
        
        if success:
            self.orchestrator_initialized = True
            self.last_onu_count = num_onus
            self.last_algorithm = algorithm
            
            # RL Agent no disponible - removido por independencia
            if algorithm == "RL Agent":
                self.results_panel.add_log_message("[ERROR] RL Agent externo no disponible. Use RL-DBA interno.")
            
            # Configurar algoritmo
            if use_hybrid:
                success_alg, msg_alg = self.adapter.set_hybrid_dba_algorithm(algorithm)
                if not success_alg:
                    self.results_panel.add_log_message(f"Warning: {msg_alg}")
            else:
                success_alg, msg_alg = self.adapter.set_dba_algorithm(algorithm)
                if not success_alg:
                    self.results_panel.add_log_message(f"Warning: {msg_alg}")
            
            arch_type_key = "integrated_pon_panel.arch_hybrid" if use_hybrid else "integrated_pon_panel.arch_classic"
            arch_type = tr(arch_type_key)
            self.status_label.setText(tr('integrated_pon_panel.status_initialized').format(arch_type))
            self.status_label.setStyleSheet("color: green;")
            
            self.start_btn.setEnabled(True)
            
            self.results_panel.add_log_message(f"✅ {message}")
            
        else:
            self.status_label.setText(f"❌ Error: {message if 'message' in locals() else 'Error desconocido'}")
            self.status_label.setStyleSheet("color: red;")
    
    def run_full_simulation(self):
        """Ejecutar simulación completa en thread separado (no bloquea UI)"""
        if not self.orchestrator_initialized:
            return

        use_hybrid = self.hybrid_checkbox.isChecked()

        # Deshabilitar botones durante simulación
        self.start_btn.setEnabled(False)
        self.simulation_running = True

        # Configurar barra de progreso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        if use_hybrid:
            # Simulación híbrida por tiempo
            duration = self.duration_spinbox.value()
            self.progress_bar.setRange(0, 100)
            self.results_panel.add_log_message(f"🏃 Ejecutando simulación híbrida: {duration}s (en background)...")

            # Crear worker thread
            self.simulation_worker = SimulationWorker(
                adapter=self.adapter,
                use_hybrid=True,
                duration=duration,
                steps=0
            )
        else:
            # Simulación clásica por pasos
            steps = self.steps_spinbox.value()
            self.progress_bar.setRange(0, steps)
            self.results_panel.add_log_message(f"🏃 Ejecutando simulación clásica: {steps} pasos (en background)...")

            # Crear worker thread
            self.simulation_worker = SimulationWorker(
                adapter=self.adapter,
                use_hybrid=False,
                duration=0,
                steps=steps
            )

        # Conectar señales del worker
        self.simulation_worker.update_signal.connect(self._on_simulation_update)
        self.simulation_worker.finished_signal.connect(self._on_simulation_finished_worker)

        # Iniciar simulación en thread separado
        self.simulation_worker.start()
        self.results_panel.add_log_message("✅ Simulación iniciada en thread separado (UI no se bloqueará)")

    def _on_simulation_update(self, event_type: str, data: dict):
        """Callback para actualizaciones de simulación desde worker thread"""
        use_hybrid = self.hybrid_checkbox.isChecked()

        if use_hybrid:
            # Simulación híbrida
            if event_type == "update":
                # Actualizar progreso basado en tiempo simulado
                duration = self.duration_spinbox.value()
                sim_time = data.get('sim_time', 0)
                progress = min(int((sim_time / duration) * 100), 100)
                self.progress_bar.setValue(progress)

                # Log eventos importantes
                if data.get('event_type') == 'polling_cycle':
                    cycle_num = data.get('data', {}).get('cycle_number', 0)
                    if cycle_num % 100 == 0:  # Log cada 100 ciclos
                        self.results_panel.add_log_message(f"Ciclo DBA: {cycle_num}")
                        # Actualizar dashboard SDN durante la simulación
                        sdn_metrics = self.adapter.get_sdn_metrics()
                        if sdn_metrics:
                            self.results_panel.add_log_message(f"📊 Actualizando métricas SDN (ciclo {cycle_num})")
                            self.parent().update_sdn_metrics(sdn_metrics)
                        else:
                            self.results_panel.add_log_message("⚠️ No hay métricas SDN disponibles")
        else:
            # Simulación clásica
            if event_type == "init":
                self.results_panel.add_log_message("Simulacion NetSim iniciada")

            elif event_type == "update":
                current_step = data.get('steps', 0)
                if current_step % 100 == 0:  # Actualizar cada 100 pasos
                    self.progress_bar.setValue(current_step)
                    # Actualizar métricas en tiempo real
                    self.update_realtime_metrics(data)

    def _on_simulation_finished_worker(self, success: bool, result):
        """Callback cuando el worker thread termina la simulación"""
        use_hybrid = self.hybrid_checkbox.isChecked()

        self.progress_bar.setValue(self.progress_bar.maximum())
        self.simulation_running = False

        if success:
            if use_hybrid:
                self.results_panel.add_log_message("✅ Simulación híbrida completada")
                self.process_hybrid_results(result)
            else:
                self.results_panel.add_log_message("✅ Simulación clásica completada")
        else:
            error_msg = str(result) if result else "Error desconocido"
            self.results_panel.add_log_message(f"❌ Error en simulación: {error_msg}")

        # Llamar al callback de finalización
        self.on_simulation_finished()
    
    def force_sdn_metrics_update(self, attempt_desc=""):
        """Forzar actualización de métricas SDN con múltiples intentos"""
        try:
            sdn_metrics = self.adapter.get_sdn_metrics()
            if sdn_metrics:
                self.results_panel.add_log_message(f"📊 {attempt_desc}: Obtenidas métricas SDN para {len(sdn_metrics.get('onu_metrics', {}))} ONUs")
                self.parent().update_sdn_metrics(sdn_metrics)
                return True
            else:
                self.results_panel.add_log_message(f"⚠️ {attempt_desc}: No hay métricas SDN disponibles")
                return False
        except Exception as e:
            self.results_panel.add_log_message(f"❌ {attempt_desc}: Error obteniendo métricas SDN: {e}")
            return False
            
    def process_hybrid_results(self, results):
        """Procesar resultados de simulación híbrida"""
        try:
            # Convertir formato de resultados híbridos al formato esperado por el panel de resultados
            if results and isinstance(results, dict):
                # El simulador híbrido devuelve resultados completos
                self.results_panel.update_simulation_results(results)
                self.results_panel.add_log_message("📊 Resultados procesados y gráficos generados")
                
                # Forzar actualización final del dashboard SDN con múltiples intentos
                # Intentar inmediatamente
                if not self.force_sdn_metrics_update("Primer intento"):
                    # Si falla, intentar 3 veces más con delays crecientes
                    delays = [500, 1000, 2000]  # 0.5s, 1s, 2s
                    for i, delay in enumerate(delays):
                        QTimer.singleShot(delay, lambda: self.force_sdn_metrics_update(f"Intento {i+2}"))
                
                # Mostrar ventana emergente si está habilitada
                if hasattr(self, 'show_popup_checkbox') and self.show_popup_checkbox.isChecked():
                    self.show_graphics_popup()
            else:
                self.results_panel.add_log_message("⚠️ No se recibieron resultados válidos")
                
        except Exception as e:
            self.results_panel.add_log_message(f"❌ Error procesando resultados híbridos: {str(e)}")
    
    
    
    def update_realtime_metrics(self, data):
        """Actualizar métricas en tiempo real"""
        steps = data.get('steps', 0)
        requests = data.get('total_requests_processed', 0)
        delay = data.get('mean_delay', 0)
        throughput = data.get('mean_throughput', 0)
        
        # Actualizar estado del agente RL si está activo
        self.update_rl_status_display()
        
        # Real-time metrics display removed
        # self.steps_label.setText(f"Pasos: {steps}")
        # self.requests_label.setText(f"Solicitudes: {requests}")
        # self.delay_label.setText(f"Delay: {delay:.6f}s")
        # self.throughput_label.setText(f"Throughput: {throughput:.2f} MB/s")
    
    def on_simulation_finished(self):
        """Callback cuando termina la simulación"""
        # Rehabilitar botones
        self.start_btn.setEnabled(False)  # Mantener deshabilitado hasta que termine todo

        # Ocultar barra de progreso
        self.progress_bar.setVisible(False)

        # Actualizar resultados finales
        self.results_panel.refresh_results()
        
        # NUEVO: Detectar y conectar OLT_SDN al dashboard si existe
        olt_sdn_instance = self.adapter.get_olt_sdn_instance()
        if olt_sdn_instance:
            self.results_panel.add_log_message("🔌 OLT_SDN detectado - Conectando al dashboard...")
            main_window = self.parent()
            if hasattr(main_window, 'connect_olt_sdn_to_dashboard'):
                main_window.connect_olt_sdn_to_dashboard(olt_sdn_instance)
                self.results_panel.add_log_message("✅ Dashboard SDN conectado y actualizado")
            else:
                self.results_panel.add_log_message("⚠️ Ventana principal no tiene método connect_olt_sdn_to_dashboard")
            
            # Habilitar botón de actualización de Dashboard SDN
            if hasattr(self.results_panel, 'enable_sdn_dashboard_button'):
                self.results_panel.enable_sdn_dashboard_button(True)
                self.results_panel.add_log_message("📊 Botón 'Actualizar Dashboard SDN' habilitado")
        
        # Múltiples intentos de actualizar el dashboard SDN (método antiguo como respaldo)
        max_attempts = 3
        for attempt in range(max_attempts):
            self.results_panel.add_log_message(f"📊 Intento {attempt + 1} de {max_attempts} de obtener métricas SDN...")
            sdn_metrics = self.adapter.get_sdn_metrics()
            if sdn_metrics:
                self.results_panel.add_log_message(f"📊 Dashboard SDN: Actualizando con {len(sdn_metrics.get('onu_metrics', {}))} ONUs")
                self.parent().update_sdn_metrics(sdn_metrics)
                self.results_panel.add_log_message("✅ Dashboard SDN actualizado exitosamente")
                break
            else:
                self.results_panel.add_log_message("⚠️ Intento fallido de obtener métricas SDN")
        else:
            self.results_panel.add_log_message("❌ No se pudieron obtener métricas SDN después de múltiples intentos")
        
        # Mostrar gráficos automáticamente en panel (siempre activo)
        self.results_panel.show_charts_on_simulation_end()
        
        # NUEVO: Guardar gráficos automáticamente y mostrar ventana emergente
        self.handle_automatic_graphics_processing()
        
        # Actualización final de estado RL
        self.update_rl_status_display()
        
        # Emitir señal
        self.simulation_finished.emit()

        # Rehabilitar botón ahora que todo terminó
        self.start_btn.setEnabled(True)

        self.results_panel.add_log_message("🎯 Simulación finalizada - Resultados y gráficos procesados")
    
    
    def handle_automatic_graphics_processing(self):
        """Manejar el procesamiento automático de gráficos al finalizar simulación"""
        try:
            # Obtener datos completos de la simulación
            simulation_data = self.adapter.get_simulation_summary()

            # Agregar datos adicionales
            simulation_data.update({
                'current_state': self.adapter.get_current_state(),
                'orchestrator_stats': self.adapter.get_orchestrator_stats()
            })

            # Recopilar información de la sesión
            session_info = {
                'num_onus': self.get_onu_count_from_topology(),
                'algorithm': self.algorithm_combo.currentText(),
                'traffic_scenario': 'residential_medium',  # Valor por defecto (cada ONU tiene configuración individual)
                'steps': self.steps_spinbox.value(),
                'detailed_logging': self.detailed_log_checkbox.isChecked()
            }

            # Guardar datos de simulación asíncronamente
            self._save_simulation_async(simulation_data, session_info)

            # Mostrar ventana emergente si está habilitada
            should_popup = self.popup_window_checkbox.isChecked()
            if should_popup:
                # El directorio será actualizado por el callback cuando termine el guardado
                self.show_graphics_popup_window(simulation_data, "", session_info)

        except Exception as e:
            self.results_panel.add_log_message(f"❌ Error en procesamiento automático: {e}")
            print(f"❌ Error en handle_automatic_graphics_processing: {e}")
    
    def _save_simulation_async(self, simulation_data: dict, session_info: dict):
        """Guardar datos de simulación usando QThread (verdaderamente asíncrono)"""
        try:
            # Deshabilitar botón de cargar simulación en el dashboard mientras se guarda
            main_window = self.parent()
            if hasattr(main_window, 'sdn_dashboard_tab'):
                main_window.sdn_dashboard_tab.set_load_button_enabled(False)

            # Mostrar widget de progreso de guardado
            self._show_saving_progress_widget_simple()

            # El método ahora retorna el directorio inmediatamente y guarda en background
            session_directory = self.graphics_saver.save_simulation_graphics_and_data(
                self.results_panel.charts_panel,
                simulation_data,
                session_info
            )

            if session_directory:
                # Actualizar ventana emergente con el directorio (antes de que termine el guardado)
                if self.popup_window:
                    self.popup_window.update_session_directory(session_directory)

                self.results_panel.add_log_message(f"💾 Guardando datos en segundo plano: {session_directory}")
            else:
                self.results_panel.add_log_message("❌ Error iniciando guardado")
                # Re-habilitar botón si hubo error
                if hasattr(main_window, 'sdn_dashboard_tab'):
                    main_window.sdn_dashboard_tab.set_load_button_enabled(True)
                # Cerrar widget de progreso
                if self.saving_progress_widget:
                    self.saving_progress_widget.close()

        except Exception as e:
            self.results_panel.add_log_message(f"❌ Error guardando datos: {e}")
            print(f"❌ Error en _save_simulation_async: {e}")

    def _show_saving_progress_widget_simple(self):
        """Mostrar widget de progreso de guardado en modo simple (sin estadísticas)"""
        try:
            # Cerrar widget anterior si existe
            if self.saving_progress_widget:
                self.saving_progress_widget.close()
                self.saving_progress_widget = None

            # Crear widget en modo simple
            self.saving_progress_widget = SavingProgressWidget(simple_mode=True)
            self.saving_progress_widget.setWindowTitle(tr('saving_progress.window_title'))
            self.saving_progress_widget.setWindowFlags(
                Qt.Window | Qt.WindowStaysOnTopHint
            )
            self.saving_progress_widget.resize(450, 250)  # Tamaño reducido para modo simple

            # Conectar señal de cerrar
            self.saving_progress_widget.close_requested.connect(
                self.saving_progress_widget.hide
            )

            # Mostrar widget y comenzar monitoreo en modo simple
            self.saving_progress_widget.show()
            self.saving_progress_widget.start_monitoring()  # No necesita adapter en modo simple

        except Exception as e:
            print(f"❌ Error mostrando widget de progreso: {e}")

    def _on_save_complete(self, session_directory: str):
        """Callback cuando el guardado se completa (conectado a graphics_saver.graphics_saved)"""
        self.results_panel.add_log_message(f"✅ Datos guardados completamente: {session_directory}")

        # Marcar widget de progreso como completado
        if self.saving_progress_widget:
            self.saving_progress_widget.set_completed()

        # Re-habilitar botón de cargar simulación en el dashboard
        main_window = self.parent()
        if hasattr(main_window, 'sdn_dashboard_tab'):
            main_window.sdn_dashboard_tab.set_load_button_enabled(True)
    
    def show_graphics_popup_window(self, 
                                 simulation_data: dict, 
                                 session_directory: str, 
                                 session_info: dict):
        """Mostrar ventana emergente con gráficos"""
        try:
            # Crear ventana emergente si no existe
            if not self.popup_window:
                self.popup_window = GraphicsPopupWindow(parent=self)
                
                # Conectar señales
                self.popup_window.window_closed.connect(self.on_popup_window_closed)
                self.popup_window.graphics_exported.connect(self.on_additional_graphics_exported)
            
            # Mostrar resultados en la ventana emergente
            self.popup_window.show_simulation_results(
                simulation_data, 
                session_directory, 
                session_info
            )
            
            self.results_panel.add_log_message("Ventana emergente de graficos mostrada")
            
        except Exception as e:
            self.results_panel.add_log_message(f"ERROR mostrando ventana emergente: {e}")
            print(f"ERROR en show_graphics_popup_window: {e}")
    
    def on_popup_window_closed(self):
        """Callback cuando se cierra la ventana emergente"""
        self.results_panel.add_log_message("Ventana emergente de graficos cerrada")
    
    def on_additional_graphics_exported(self, directory):
        """Callback cuando se exportan gráficos adicionales"""
        self.results_panel.add_log_message(f"Graficos adicionales exportados a: {directory}")
    
    def on_results_updated(self, results):
        """Callback cuando se actualizan los resultados"""
        # Aquí se pueden agregar acciones adicionales cuando se actualicen los resultados
        pass
    
    def set_canvas_reference(self, canvas):
        """Establecer referencia al canvas"""
        self.canvas_reference = canvas
        print(f"DEBUG Canvas reference establecida: {canvas}")
        
        # Actualizar inmediatamente el conteo de ONUs
        self.update_onu_count_display()
        
        # Conectar señal de cambios de dispositivos si no está conectada
        if canvas and hasattr(canvas, 'device_manager'):
            print("DEBUG Conectando señal devices_changed")
            # Desconectar señal anterior si existe para evitar duplicados
            try:
                canvas.device_manager.devices_changed.disconnect(self.on_devices_changed)
            except:
                pass  # No estaba conectada
            
            # Conectar nueva señal
            canvas.device_manager.devices_changed.connect(self.on_devices_changed)
        
        # También conectar señal de cambios de conexiones
        if canvas and hasattr(canvas, 'connection_manager'):
            print("DEBUG Conectando señal connections_changed")
            # Desconectar señal anterior si existe para evitar duplicados
            try:
                canvas.connection_manager.connections_changed.disconnect(self.on_connections_changed)
            except:
                pass  # No estaba conectada
            
            # Conectar nueva señal
            canvas.connection_manager.connections_changed.connect(self.on_connections_changed)
    
    def on_devices_changed(self):
        """Callback cuando cambian los dispositivos en el canvas"""
        # Solo log cuando sea relevante
        if getattr(self, 'verbose_debug', False):
            print("DEBUG Dispositivos cambiaron - actualizando conteo de ONUs")
        self.update_onu_count_display()
    
    def on_connections_changed(self):
        """Callback cuando cambian las conexiones en el canvas"""
        # Solo log cuando sea relevante  
        if getattr(self, 'verbose_debug', False):
            print("DEBUG Conexiones cambiaron - actualizando conteo de ONUs conectadas")
        self.update_onu_count_display()
    
    def periodic_onu_update(self):
        """Actualización periódica del conteo de ONUs y estado RL"""
        if self.canvas_reference:
            current_count = self.get_onu_count_from_topology()
            displayed_count = int(self.onu_count_label.text()) if self.onu_count_label.text().isdigit() else -1

            if current_count != displayed_count:
                print(f"DEBUG Actualizando conteo ONUs: {displayed_count} -> {current_count}")
                self.update_onu_count_display()

        # Actualizar estado del modelo RL
        self.update_rl_status_display()
    
    def force_onu_count_update(self):
        """Forzar actualización del conteo de ONUs"""
        print("🔄 Actualización manual de conteo de ONUs solicitada")
        self.update_onu_count_display()
        
        # Mostrar información detallada al usuario solo cuando se solicite manualmente
        if self.canvas_reference:
            all_devices = self.canvas_reference.device_manager.get_all_devices()
            all_onus = self.canvas_reference.device_manager.get_devices_by_type("ONU")
            connected_count = self.get_onu_count_from_topology()
            self.results_panel.add_log_message(f"🔍 Actualización manual: {connected_count} ONUs conectadas de {len(all_onus)} ONUs totales ({len(all_devices)} dispositivos)")
        else:
            self.results_panel.add_log_message("⚠️ No hay referencia al canvas para contar dispositivos")
    
    def update_topology_info(self):
        """Actualizar información de topología desde el canvas"""
        try:
            if self.canvas_reference:
                # Actualizar conteo de ONUs desde la topología
                self.update_onu_count_display()
                print("INFO Topologia actualizada desde canvas")
            else:
                print("WARNING Canvas reference no disponible para actualizar topologia")
        except Exception as e:
            print(f"ERROR actualizando topologia: {e}")
    
    def set_log_panel(self, log_panel):
        """Establecer referencia al panel de log externo"""
        self.log_panel_reference = log_panel
        print("INFO Log panel conectado al panel PON integrado")
    
    def reset_orchestrator(self):
        """Resetear el orquestador PON cuando cambia la topología"""
        try:
            if hasattr(self, 'adapter') and self.adapter:
                # Reset adapter internal state
                self.adapter.orchestrator = None
                self.adapter.netsim = None
                
                # Actualizar conteo de ONUs inmediatamente
                self.update_onu_count_display()
                
                # Si estaba inicializado, reinicializar automáticamente por cambio de topología
                if self.orchestrator_initialized:
                    self.auto_reinitialize("topología")
                
                print("INFO Orquestador PON reseteado por cambio de topologia")
            else:
                print("WARNING No hay adapter para resetear orquestador")
        except Exception as e:
            print(f"ERROR reseteando orquestador: {e}")
    
    def cleanup(self):
        """Limpiar recursos del panel"""
        try:
            # Parar timer de actualización de ONUs de forma segura
            if hasattr(self, 'onu_update_timer') and self.onu_update_timer:
                if self.onu_update_timer.isActive():
                    self.onu_update_timer.stop()
                self.onu_update_timer.deleteLater()
                self.onu_update_timer = None
                
            # Limpiar results_panel si existe
            if hasattr(self, 'results_panel') and self.results_panel:
                self.results_panel.cleanup()
            
            if hasattr(self, 'adapter') and self.adapter:
                # Limpiar adapter si es necesario
                pass
            
            if hasattr(self, 'popup_window') and self.popup_window:
                self.popup_window.close()
                self.popup_window = None

            # Limpiar widget de progreso de guardado
            if hasattr(self, 'saving_progress_widget') and self.saving_progress_widget:
                self.saving_progress_widget.stop_monitoring()
                self.saving_progress_widget.close()
                self.saving_progress_widget = None

            # REMOVED: Incremental writing disabled
            # if hasattr(self, 'saving_progress_widget') and self.saving_progress_widget:
            #     self.saving_progress_widget.stop_monitoring()
            #     self.saving_progress_widget.close()
            #     self.saving_progress_widget = None

            print("Panel PON integrado limpiado")
            
        except Exception as e:
            print(f"ERROR limpiando panel PON: {e}")
    
    def set_theme(self, dark_theme):
        """Aplicar tema al panel integrado PON"""
        # Aplicar tema al panel de resultados
        if hasattr(self, 'results_panel') and self.results_panel:
            self.results_panel.set_theme(dark_theme)
            
        # Aplicar tema a la ventana emergente si existe
        if hasattr(self, 'popup_window') and self.popup_window:
            self.popup_window.set_theme(dark_theme)

        # El estilo QSS se aplicará automáticamente desde la ventana principal

    def _update_rl_models_list(self):
        """Método stub - ya no usado pero requerido para compatibilidad"""
        # Este método fue eliminado en la refactorización a Smart RL interno
        # pero se mantiene como stub para evitar errores de atributo
        pass

    # REMOVED:     def _show_saving_progress_widget(self, use_hybrid: bool):
    # REMOVED:         """
    # REMOVED:         Mostrar widget de progreso de guardado incremental
    # REMOVED: 
    # REMOVED:         Args:
    # REMOVED:             use_hybrid: Si es simulación híbrida (para estimar snapshots)
    # REMOVED:         """
    # REMOVED:         try:
    # REMOVED:             # Crear widget de progreso si no existe
    # REMOVED:             if not self.saving_progress_widget:
    # REMOVED:                 self.saving_progress_widget = SavingProgressWidget()
    # REMOVED:                 self.saving_progress_widget.setWindowTitle(tr("saving_progress.window_title"))
    # REMOVED:                 self.saving_progress_widget.setMinimumWidth(450)
    # REMOVED:                 self.saving_progress_widget.setMinimumHeight(400)
    # REMOVED: 
    # REMOVED:                 # Conectar señal de cerrar
    # REMOVED:                 self.saving_progress_widget.close_requested.connect(
    # REMOVED:                     lambda: self.saving_progress_widget.hide()
    # REMOVED:                 )
    # REMOVED: 
    # REMOVED:             # Estimar número total de snapshots
    # REMOVED:             if use_hybrid:
    # REMOVED:                 duration = self.duration_spinbox.value()
    # REMOVED:                 # Cada ciclo = 125us, calcular cuántos ciclos en la duración
    # REMOVED:                 cycles_per_second = 1 / 125e-6  # ~8000 ciclos/segundo
    # REMOVED:                 total_snapshots = int(duration * cycles_per_second)
    # REMOVED:             else:
    # REMOVED:                 # Simulación clásica
    # REMOVED:                 total_snapshots = self.steps_spinbox.value()
    # REMOVED: 
    # REMOVED:             # Iniciar monitoreo
    # REMOVED:             self.saving_progress_widget.start_monitoring(self.adapter, total_snapshots)
    # REMOVED: 
    # REMOVED:             # Mostrar widget
    # REMOVED:             self.saving_progress_widget.show()
    # REMOVED:             self.saving_progress_widget.raise_()
    # REMOVED:             self.saving_progress_widget.activateWindow()
    # REMOVED: 
    # REMOVED:             self.results_panel.add_log_message(f"📊 Widget de progreso mostrado (estimando {total_snapshots:,} snapshots)")
    # REMOVED: 
    # REMOVED:         except Exception as e:
    # REMOVED:             self.results_panel.add_log_message(f"⚠️ Error mostrando widget de progreso: {e}")
    # REMOVED:             print(f"Error en _show_saving_progress_widget: {e}")

    def retranslate_ui(self):
        """Actualizar todos los textos traducibles del panel"""
        # Título
        if hasattr(self, 'title_label'):
            self.title_label.setText(tr("integrated_pon_panel.title"))
        
        # GroupBox titles
        if hasattr(self, 'status_group'):
            self.status_group.setTitle(tr("integrated_pon_panel.status_group"))
        if hasattr(self, 'config_group'):
            self.config_group.setTitle(tr("integrated_pon_panel.config_group"))
        if hasattr(self, 'sim_group'):
            self.sim_group.setTitle(tr("integrated_pon_panel.simulation_group"))
        if hasattr(self, 'rl_info_group'):
            self.rl_info_group.setTitle(tr("integrated_pon_panel.rl_agent_group"))
        
        # Labels de configuración
        if hasattr(self, 'onus_connected_label'):
            self.onus_connected_label.setText(tr("integrated_pon_panel.onus_connected"))
        if hasattr(self, 'onu_count_label'):
            self.onu_count_label.setToolTip(tr("integrated_pon_panel.onus_tooltip"))
        if hasattr(self, 'dba_label'):
            self.dba_label.setText(tr("integrated_pon_panel.dba"))
        if hasattr(self, 'rl_model_label'):
            self.rl_model_label.setText(tr("integrated_pon_panel.rl_model"))
        if hasattr(self, 'scenario_label'):
            self.scenario_label.setText(tr("integrated_pon_panel.scenario"))
        if hasattr(self, 'architecture_label'):
            self.architecture_label.setText(tr("integrated_pon_panel.architecture"))
        if hasattr(self, 'time_label'):
            self.time_label.setText(tr("integrated_pon_panel.time_seconds"))
        if hasattr(self, 'steps_label'):
            self.steps_label.setText(tr("integrated_pon_panel.steps"))
        
        # Botones
        if hasattr(self, 'load_rl_model_btn'):
            self.load_rl_model_btn.setText(tr("integrated_pon_panel.load_rl_model"))
            self.load_rl_model_btn.setToolTip(tr("integrated_pon_panel.load_rl_model_tooltip"))
        if hasattr(self, 'unload_rl_model_btn'):
            self.unload_rl_model_btn.setText(tr("integrated_pon_panel.unload_rl_model"))
            self.unload_rl_model_btn.setToolTip(tr("integrated_pon_panel.unload_rl_model_tooltip"))
        if hasattr(self, 'init_btn'):
            self.init_btn.setText(tr("integrated_pon_panel.manual_init"))
            self.init_btn.setToolTip(tr("integrated_pon_panel.manual_init_tooltip"))
        if hasattr(self, 'start_btn'):
            self.start_btn.setText(tr("integrated_pon_panel.execute"))
        
        # Checkboxes
        if hasattr(self, 'hybrid_checkbox'):
            self.hybrid_checkbox.setText(tr("integrated_pon_panel.hybrid_architecture"))
            self.hybrid_checkbox.setToolTip(tr("integrated_pon_panel.hybrid_tooltip"))
        if hasattr(self, 'popup_window_checkbox'):
            self.popup_window_checkbox.setText(tr("integrated_pon_panel.show_popup"))
        if hasattr(self, 'detailed_log_checkbox'):
            self.detailed_log_checkbox.setText(tr("integrated_pon_panel.detailed_logging"))
        if hasattr(self, 'auto_init_checkbox'):
            self.auto_init_checkbox.setText(tr("integrated_pon_panel.auto_init"))
            self.auto_init_checkbox.setToolTip(tr("integrated_pon_panel.auto_init_tooltip"))
        
        # Tooltips de spinboxes
        if hasattr(self, 'duration_spinbox'):
            self.duration_spinbox.setToolTip(tr("integrated_pon_panel.time_tooltip"))
        if hasattr(self, 'steps_spinbox'):
            self.steps_spinbox.setToolTip(tr("integrated_pon_panel.steps_tooltip"))
        
        # Actualizar combo de algoritmos (headers y botones)
        if hasattr(self, 'algorithm_combo'):
            # Actualizar headers del combo
            model = self.algorithm_combo.model()
            # Buscar y actualizar el header de algoritmos convencionales
            for i in range(self.algorithm_combo.count()):
                item = model.item(i)
                if item and not item.isEnabled():  # Es un header
                    text = item.text()
                    if "Convencional" in text or "Conventional" in text or "Konventionell" in text or "Conventionnel" in text:
                        item.setText(tr("integrated_pon_panel.algorithms_conventional"))
                    elif "Personalizado" in text or "Custom" in text or "Benutzerdefiniert" in text or "Personnalisé" in text:
                        item.setText(tr("integrated_pon_panel.algorithms_custom"))
            
            # Regenerar botones del dropdown con traducciones
            if hasattr(self, 'custom_combo_view'):
                self.custom_combo_view.retranslate()
        
        # Actualizar botón de agregar algoritmo
        if hasattr(self, 'add_algorithm_btn'):
            self.add_algorithm_btn.setText(tr("integrated_pon_panel.add_custom_algorithm"))
            self.add_algorithm_btn.setToolTip(tr("integrated_pon_panel.add_custom_algorithm_tooltip"))
        
        # Labels del panel de info RL
        if hasattr(self, 'rl_model_info_label'):
            self.rl_model_info_label.setText(tr("integrated_pon_panel.rl_model_info"))
        if hasattr(self, 'rl_last_action_label'):
            self.rl_last_action_label.setText(tr("integrated_pon_panel.rl_last_action"))
        
        # Label de información
        if hasattr(self, 'info_label'):
            self.info_label.setText(tr("integrated_pon_panel.results_info"))
        
        # Actualizar el status label con el estado actual si está inicializado
        if hasattr(self, 'status_label') and self.orchestrator_initialized:
            use_hybrid = self.hybrid_checkbox.isChecked()
            arch_type_key = "integrated_pon_panel.arch_hybrid" if use_hybrid else "integrated_pon_panel.arch_classic"
            arch_type = tr(arch_type_key)
            self.status_label.setText(tr('integrated_pon_panel.status_initialized').format(arch_type))
        
        # Actualizar el estado del modelo RL
        if hasattr(self, 'update_rl_status_display'):
            self.update_rl_status_display()
        
        # Actualizar ventana popup de gráficos si existe
        if hasattr(self, 'popup_window') and self.popup_window:
            self.popup_window.retranslate_ui()

        # Actualizar widget de progreso de guardado si existe
        if hasattr(self, 'saving_progress_widget') and self.saving_progress_widget:
            self.saving_progress_widget.retranslate_ui()

        # Recargar estado (si está disponible, mantiene el estado traducido)
        self.check_pon_status()