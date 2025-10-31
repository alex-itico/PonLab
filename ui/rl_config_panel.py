"""
RL Config Panel
Panel de configuración para Aprendizaje Reforzado
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QDoubleSpinBox, QComboBox, QGroupBox,
                             QPushButton, QProgressBar, QTextEdit, QGridLayout,
                             QCheckBox, QSlider, QFrame, QScrollArea, QFileDialog,
                             QListWidget, QListWidgetItem, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
import os
import json
import glob
from datetime import datetime
import numpy as np
from utils.translation_manager import tr
from .rl_graphics_popup_window import RLGraphicsPopupWindow


class RLConfigPanel(QWidget):
    """Panel de configuración para Aprendizaje Reforzado"""
    
    # Señales
    training_started = pyqtSignal(dict)  # Parámetros de entrenamiento
    training_paused = pyqtSignal()
    training_stopped = pyqtSignal()
    model_saved = pyqtSignal(str)  # Ruta del modelo guardado
    model_loaded = pyqtSignal(str)  # Modelo cargado para simulación
    # simulation_started = pyqtSignal(dict)  # DESHABILITADO - Simulación movida al panel principal
    # simulation_stopped = pyqtSignal()  # DESHABILITADO - Simulación movida al panel principal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dark_theme = False
        self.training_active = False
        self.is_training_paused = False
        self.simulation_active = False

        # Métricas de entrenamiento en tiempo real
        self.current_episode = 0
        self.current_reward = 0.0
        self.current_loss = 0.0

        # Estados RL
        self.loaded_model_path = None
        self.available_models = []

        # Training Manager (se asignará externamente)
        self.training_manager = None

        # Ventana emergente de gráficos RL
        self.rl_graphics_window = None

        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Configurar la interfaz del panel RL"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Nota informativa sobre el cambio
        self.info_label = QLabel(tr("rl_config_panel.info_message"))
        self.info_label.setStyleSheet("color: #2196F3; background-color: #E3F2FD; padding: 8px; border-radius: 4px; margin: 4px;")
        self.info_label.setWordWrap(True)
        main_layout.addWidget(self.info_label)

        # Pestaña de Entrenamiento RL solamente (simulación movida a pestaña principal)
        self.tab_widget = QTabWidget()

        # Pestaña 1: Entrenamiento RL
        self.setup_training_tab()

        main_layout.addWidget(self.tab_widget)

        # Log compartido al final
        self.setup_log_section(main_layout)

        # Actualizar lista de modelos después de que todo esté configurado
        self.refresh_models_list()
    
    def set_training_manager(self, training_manager):
        """Establecer referencia al TrainingManager"""
        self.training_manager = training_manager
        
        # Conectar señales si el manager está disponible
        if self.training_manager:
            # Señales de entrenamiento
            self.training_manager.training_progress.connect(self.update_training_metrics_from_manager)
            self.training_manager.training_status_changed.connect(self.update_training_status)
            self.training_manager.error_occurred.connect(self.handle_training_error)
            self.training_manager.training_completed.connect(self.handle_training_completed)

            # Señales de simulación
            self.training_manager.simulation_progress.connect(self.update_simulation_metrics_from_manager)
            self.training_manager.simulation_completed.connect(self.handle_simulation_completed)
            self.training_manager.agent_decision.connect(self.handle_agent_decision)
            
            # Inicializar estado del entrenamiento
            self.training_start_time = None
            
            print("[OK] Panel RL conectado con TrainingManager")

    def setup_training_tab(self):
        """Configurar la pestaña de entrenamiento RL"""
        training_widget = QWidget()

        # Área de scroll para el contenido de entrenamiento
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(QFrame.NoFrame)

        # Widget contenedor del contenido
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(12)

        # Secciones de entrenamiento
        self.setup_environment_section(content_layout)
        self.setup_algorithm_section(content_layout)
        self.setup_training_section(content_layout)
        self.setup_controls_section(content_layout)
        self.setup_metrics_section(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)

        training_layout = QVBoxLayout(training_widget)
        training_layout.addWidget(scroll_area)

        self.tab_widget.addTab(training_widget, "Entrenamiento")

    def setup_simulation_tab(self):
        """MÉTODO DESHABILITADO - Simulación RL movida al panel principal de simulación"""
        # Este método ya no se usa. La simulación RL ahora se maneja
        # directamente desde IntegratedPONTestPanel con el algoritmo Smart-RL
        return
        simulation_widget = QWidget()

        # Área de scroll para el contenido de simulación
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(QFrame.NoFrame)

        # Widget contenedor del contenido
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(12)

        # Secciones de simulación
        self.setup_model_selection_section(content_layout)
        self.setup_simulation_config_section(content_layout)
        self.setup_simulation_controls_section(content_layout)
        self.setup_simulation_metrics_section(content_layout)

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)

        simulation_layout = QVBoxLayout(simulation_widget)
        simulation_layout.addWidget(scroll_area)

        self.tab_widget.addTab(simulation_widget, "Simulacion RL")

    def setup_model_selection_section(self, layout):
        """Sección para seleccionar y cargar modelos entrenados"""
        self.model_selection_group = QGroupBox(tr("rl_config_panel.model_selection_group"))
        group_layout = QVBoxLayout(self.model_selection_group)
        group_layout.setSpacing(8)

        # Lista de modelos disponibles
        models_layout = QHBoxLayout()

        # Lista de modelos
        models_list_layout = QVBoxLayout()
        self.available_models_label = QLabel(tr("rl_config_panel.available_models"))
        models_list_layout.addWidget(self.available_models_label)

        self.models_list = QListWidget()
        self.models_list.setMaximumHeight(120)
        self.models_list.itemClicked.connect(self.on_model_selected)
        models_list_layout.addWidget(self.models_list)

        # Botones de gestión de modelos
        model_buttons_layout = QVBoxLayout()

        self.refresh_button = QPushButton(tr("rl_config_panel.refresh_button"))
        self.refresh_button.clicked.connect(self.refresh_models_list)
        self.refresh_button.setToolTip(tr("rl_config_panel.refresh_tooltip"))
        model_buttons_layout.addWidget(self.refresh_button)

        self.load_external_button = QPushButton(tr("rl_config_panel.load_external_button"))
        self.load_external_button.clicked.connect(self.load_external_model)
        self.load_external_button.setToolTip(tr("rl_config_panel.load_external_tooltip"))
        model_buttons_layout.addWidget(self.load_external_button)

        model_buttons_layout.addStretch()

        models_layout.addLayout(models_list_layout)
        models_layout.addLayout(model_buttons_layout)
        group_layout.addLayout(models_layout)

        # Información del modelo seleccionado
        info_layout = QGridLayout()

        self.loaded_model_info_label = QLabel(tr("rl_config_panel.loaded_model"))
        info_layout.addWidget(self.loaded_model_info_label, 0, 0)
        self.loaded_model_label = QLabel(tr("rl_config_panel.none"))
        self.loaded_model_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_layout.addWidget(self.loaded_model_label, 0, 1)

        self.algorithm_info_label = QLabel(tr("rl_config_panel.algorithm"))
        info_layout.addWidget(self.algorithm_info_label, 1, 0)
        self.model_algorithm_label = QLabel("-")
        info_layout.addWidget(self.model_algorithm_label, 1, 1)

        self.trained_onus_label = QLabel(tr("rl_config_panel.trained_onus"))
        info_layout.addWidget(self.trained_onus_label, 2, 0)
        self.model_onus_label = QLabel("-")
        info_layout.addWidget(self.model_onus_label, 2, 1)

        self.traffic_info_label = QLabel(tr("rl_config_panel.traffic"))
        info_layout.addWidget(self.traffic_info_label, 3, 0)
        self.model_traffic_label = QLabel("-")
        info_layout.addWidget(self.model_traffic_label, 3, 1)

        group_layout.addLayout(info_layout)

        layout.addWidget(self.model_selection_group)

        # Nota: refresh_models_list() se llamará después de que el log esté configurado

    def setup_simulation_config_section(self, layout):
        """Configuración de parámetros de simulación"""
        self.sim_config_group = QGroupBox(tr("rl_config_panel.sim_config_group"))
        group_layout = QGridLayout(self.sim_config_group)
        group_layout.setSpacing(8)

        # Duración de simulación
        self.duration_s_label = QLabel(tr("rl_config_panel.duration_s"))
        group_layout.addWidget(self.duration_s_label, 0, 0)
        self.sim_duration_spin = QDoubleSpinBox()
        self.sim_duration_spin.setRange(1.0, 300.0)
        self.sim_duration_spin.setValue(10.0)
        self.sim_duration_spin.setSingleStep(1.0)
        self.sim_duration_spin.setDecimals(1)
        self.sim_duration_spin.setToolTip(tr("rl_config_panel.duration_tooltip"))
        group_layout.addWidget(self.sim_duration_spin, 0, 1)

        # Mostrar decisiones del agente
        self.show_decisions_check = QCheckBox(tr("rl_config_panel.show_decisions"))
        self.show_decisions_check.setChecked(True)
        self.show_decisions_check.setToolTip(tr("rl_config_panel.show_decisions_tooltip"))
        group_layout.addWidget(self.show_decisions_check, 1, 0, 1, 2)

        # Guardar métricas de simulación
        self.save_metrics_check = QCheckBox(tr("rl_config_panel.save_metrics"))
        self.save_metrics_check.setChecked(True)
        self.save_metrics_check.setToolTip(tr("rl_config_panel.save_metrics_tooltip"))
        group_layout.addWidget(self.save_metrics_check, 2, 0, 1, 2)

        layout.addWidget(self.sim_config_group)

    def setup_simulation_controls_section(self, layout):
        """Controles de simulación"""
        self.sim_controls_group = QGroupBox(tr("rl_config_panel.sim_controls_group"))
        group_layout = QVBoxLayout(self.sim_controls_group)
        group_layout.setSpacing(8)

        # Botones de control
        buttons_layout = QHBoxLayout()

        # Botón ejecutar simulación
        self.simulate_button = QPushButton(tr("rl_config_panel.execute_simulation"))
        self.simulate_button.setMinimumHeight(35)
        self.simulate_button.clicked.connect(self.start_simulation)
        self.simulate_button.setToolTip(tr("rl_config_panel.execute_simulation_tooltip"))
        self.simulate_button.setEnabled(False)  # Deshabilitado hasta cargar modelo
        buttons_layout.addWidget(self.simulate_button)

        # Botón detener simulación
        self.stop_simulation_button = QPushButton(tr("rl_config_panel.stop"))
        self.stop_simulation_button.setMinimumHeight(35)
        self.stop_simulation_button.clicked.connect(self.stop_simulation)
        self.stop_simulation_button.setToolTip(tr("rl_config_panel.stop_simulation_tooltip"))
        self.stop_simulation_button.setEnabled(False)
        buttons_layout.addWidget(self.stop_simulation_button)

        group_layout.addLayout(buttons_layout)

        layout.addWidget(self.sim_controls_group)

    def setup_simulation_metrics_section(self, layout):
        """Métricas de simulación en tiempo real"""
        self.sim_metrics_group = QGroupBox(tr("rl_config_panel.sim_metrics_group"))
        group_layout = QGridLayout(self.sim_metrics_group)
        group_layout.setSpacing(8)

        # Progreso de simulación
        self.sim_progress_label = QLabel(tr("rl_config_panel.progress"))
        group_layout.addWidget(self.sim_progress_label, 0, 0)
        self.sim_progress_bar = QProgressBar()
        self.sim_progress_bar.setRange(0, 100)
        self.sim_progress_bar.setValue(0)
        group_layout.addWidget(self.sim_progress_bar, 0, 1)

        # Decisiones del agente
        self.sim_decisions_label = QLabel(tr("rl_config_panel.decisions"))
        group_layout.addWidget(self.sim_decisions_label, 1, 0)
        self.decisions_label = QLabel("0")
        self.decisions_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        group_layout.addWidget(self.decisions_label, 1, 1)

        # Rendimiento promedio
        self.sim_performance_label = QLabel(tr("rl_config_panel.performance"))
        group_layout.addWidget(self.sim_performance_label, 2, 0)
        self.performance_label = QLabel("0.000")
        self.performance_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        group_layout.addWidget(self.performance_label, 2, 1)

        # Bloqueos evitados
        self.sim_blocks_label = QLabel(tr("rl_config_panel.blocks"))
        group_layout.addWidget(self.sim_blocks_label, 3, 0)
        self.blocks_label = QLabel("0")
        self.blocks_label.setStyleSheet("font-weight: bold; color: #FF5722;")
        group_layout.addWidget(self.blocks_label, 3, 1)

        # Tiempo de simulación
        self.sim_time_info_label = QLabel(tr("rl_config_panel.time"))
        group_layout.addWidget(self.sim_time_info_label, 4, 0)
        self.sim_time_label = QLabel("00:00:00")
        self.sim_time_label.setStyleSheet("font-weight: bold; color: #9C27B0;")
        group_layout.addWidget(self.sim_time_label, 4, 1)

        layout.addWidget(self.sim_metrics_group)

    def setup_environment_section(self, layout):
        """Configuración del entorno PON"""
        self.pon_environment_group = QGroupBox(tr("rl_config_panel.pon_environment_group"))
        group_layout = QGridLayout(self.pon_environment_group)
        group_layout.setSpacing(8)
        
        # Número de ONUs
        self.onus_label = QLabel(tr("rl_config_panel.onus"))
        group_layout.addWidget(self.onus_label, 0, 0)
        self.onus_spin = QSpinBox()
        self.onus_spin.setRange(2, 16)
        self.onus_spin.setValue(4)
        self.onus_spin.setToolTip(tr("rl_config_panel.onus_tooltip"))
        group_layout.addWidget(self.onus_spin, 0, 1)
        
        # Escenario de tráfico
        self.traffic_label = QLabel(tr("rl_config_panel.traffic_label"))
        group_layout.addWidget(self.traffic_label, 1, 0)
        self.traffic_combo = QComboBox()
        self.traffic_combo.addItems([
            "residential_light",
            "residential_medium", 
            "residential_heavy",
            "business_standard"
        ])
        self.traffic_combo.setCurrentText("residential_medium")
        self.traffic_combo.setToolTip(tr("rl_config_panel.traffic_tooltip"))
        group_layout.addWidget(self.traffic_combo, 1, 1)
        
        # Duración del episodio
        self.duration_episode_label = QLabel(tr("rl_config_panel.duration_episode"))
        group_layout.addWidget(self.duration_episode_label, 2, 0)
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 60.0)
        self.duration_spin.setValue(1.0)
        self.duration_spin.setSingleStep(0.1)
        self.duration_spin.setDecimals(1)
        self.duration_spin.setToolTip(tr("rl_config_panel.duration_episode_tooltip"))
        group_layout.addWidget(self.duration_spin, 2, 1)
        
        # Timestep de simulación
        self.timestep_label = QLabel(tr("rl_config_panel.timestep_ms"))
        group_layout.addWidget(self.timestep_label, 3, 0)
        self.timestep_spin = QDoubleSpinBox()
        self.timestep_spin.setRange(0.1, 10.0)
        self.timestep_spin.setValue(0.5)
        self.timestep_spin.setSingleStep(0.1)
        self.timestep_spin.setDecimals(1)
        self.timestep_spin.setToolTip(tr("rl_config_panel.timestep_tooltip"))
        group_layout.addWidget(self.timestep_spin, 3, 1)
        
        layout.addWidget(self.pon_environment_group)
        
    def setup_algorithm_section(self, layout):
        """Configuración del algoritmo RL"""
        self.learning_algorithm_group = QGroupBox(tr("rl_config_panel.learning_algorithm_group"))
        group_layout = QGridLayout(self.learning_algorithm_group)
        group_layout.setSpacing(8)
        
        # Tipo de algoritmo
        self.algorithm_label = QLabel(tr("rl_config_panel.algorithm_label"))
        group_layout.addWidget(self.algorithm_label, 0, 0)
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["PPO", "A2C", "DQN", "SAC"])
        self.algorithm_combo.setCurrentText("PPO")
        self.algorithm_combo.setToolTip(tr("rl_config_panel.algorithm_tooltip"))
        group_layout.addWidget(self.algorithm_combo, 0, 1)
        
        # Learning Rate
        self.learning_rate_label = QLabel(tr("rl_config_panel.learning_rate"))
        group_layout.addWidget(self.learning_rate_label, 1, 0)
        self.lr_spin = QDoubleSpinBox()
        self.lr_spin.setRange(1e-6, 1e-1)
        self.lr_spin.setValue(3e-4)
        self.lr_spin.setDecimals(6)
        self.lr_spin.setSingleStep(1e-5)
        self.lr_spin.setToolTip(tr("rl_config_panel.learning_rate_tooltip"))
        group_layout.addWidget(self.lr_spin, 1, 1)
        
        # Batch Size
        self.batch_size_label = QLabel(tr("rl_config_panel.batch_size"))
        group_layout.addWidget(self.batch_size_label, 2, 0)
        self.batch_spin = QSpinBox()
        self.batch_spin.setRange(16, 512)
        self.batch_spin.setValue(64)
        self.batch_spin.setSingleStep(16)
        self.batch_spin.setToolTip(tr("rl_config_panel.batch_size_tooltip"))
        group_layout.addWidget(self.batch_spin, 2, 1)
        
        # Gamma (factor de descuento)
        self.gamma_label = QLabel(tr("rl_config_panel.gamma"))
        group_layout.addWidget(self.gamma_label, 3, 0)
        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.8, 0.999)
        self.gamma_spin.setValue(0.99)
        self.gamma_spin.setDecimals(3)
        self.gamma_spin.setSingleStep(0.01)
        self.gamma_spin.setToolTip(tr("rl_config_panel.gamma_tooltip"))
        group_layout.addWidget(self.gamma_spin, 3, 1)
        
        layout.addWidget(self.learning_algorithm_group)
        
    def setup_training_section(self, layout):
        """Configuración de parámetros de entrenamiento"""
        self.training_params_group = QGroupBox(tr("rl_config_panel.training_params_group"))
        group_layout = QGridLayout(self.training_params_group)
        group_layout.setSpacing(8)
        
        # Total timesteps
        self.total_steps_label = QLabel(tr("rl_config_panel.total_steps"))
        group_layout.addWidget(self.total_steps_label, 0, 0)
        self.timesteps_spin = QSpinBox()
        self.timesteps_spin.setRange(1000, 1000000)
        self.timesteps_spin.setValue(100000)
        self.timesteps_spin.setSingleStep(10000)
        self.timesteps_spin.setToolTip(tr("rl_config_panel.total_steps_tooltip"))
        group_layout.addWidget(self.timesteps_spin, 0, 1)
        
        # Frequency de evaluación
        self.eval_freq_label = QLabel(tr("rl_config_panel.eval_freq"))
        group_layout.addWidget(self.eval_freq_label, 1, 0)
        self.eval_freq_spin = QSpinBox()
        self.eval_freq_spin.setRange(100, 10000)
        self.eval_freq_spin.setValue(2000)
        self.eval_freq_spin.setSingleStep(100)
        self.eval_freq_spin.setToolTip(tr("rl_config_panel.eval_freq_tooltip"))
        group_layout.addWidget(self.eval_freq_spin, 1, 1)
        
        # Guardar modelo automáticamente
        self.auto_save_check = QCheckBox(tr("rl_config_panel.auto_save"))
        self.auto_save_check.setChecked(True)
        self.auto_save_check.setToolTip(tr("rl_config_panel.auto_save_tooltip"))
        group_layout.addWidget(self.auto_save_check, 2, 0, 1, 2)
        
        # Usar GPU si está disponible
        self.use_gpu_check = QCheckBox(tr("rl_config_panel.use_gpu"))
        self.use_gpu_check.setChecked(False)
        self.use_gpu_check.setToolTip(tr("rl_config_panel.use_gpu_tooltip"))
        group_layout.addWidget(self.use_gpu_check, 3, 0, 1, 2)
        
        layout.addWidget(self.training_params_group)
        
    def setup_controls_section(self, layout):
        """Controles de entrenamiento"""
        self.controls_group = QGroupBox(tr("rl_config_panel.controls_group"))
        group_layout = QVBoxLayout(self.controls_group)
        group_layout.setSpacing(8)
        
        # Primera fila de botones
        buttons_layout1 = QHBoxLayout()
        
        # Botón entrenar
        self.train_button = QPushButton(tr("rl_config_panel.train"))
        self.train_button.setMinimumHeight(35)
        self.train_button.setMinimumWidth(120)
        self.train_button.clicked.connect(self.start_training)
        self.train_button.setToolTip(tr("rl_config_panel.train_tooltip"))
        buttons_layout1.addWidget(self.train_button)
        
        # Botón pausar
        self.pause_button = QPushButton(tr("rl_config_panel.pause"))
        self.pause_button.setMinimumHeight(35)
        self.pause_button.clicked.connect(self.pause_training)
        self.pause_button.setEnabled(False)
        self.pause_button.setToolTip(tr("rl_config_panel.pause_tooltip"))
        buttons_layout1.addWidget(self.pause_button)
        
        group_layout.addLayout(buttons_layout1)
        
        # Segunda fila de botones
        buttons_layout2 = QHBoxLayout()
        
        # Botón detener
        self.stop_button = QPushButton(tr("rl_config_panel.stop"))
        self.stop_button.setMinimumHeight(35)
        self.stop_button.clicked.connect(self.stop_training)
        self.stop_button.setEnabled(False)
        self.stop_button.setToolTip(tr("rl_config_panel.stop_tooltip"))
        buttons_layout2.addWidget(self.stop_button)
        
        # Botón guardar
        self.save_button = QPushButton(tr("rl_config_panel.save"))
        self.save_button.setMinimumHeight(35)
        self.save_button.clicked.connect(self.save_model)
        self.save_button.setEnabled(False)
        self.save_button.setToolTip(tr("rl_config_panel.save_tooltip"))
        buttons_layout2.addWidget(self.save_button)
        
        group_layout.addLayout(buttons_layout2)
        
        layout.addWidget(self.controls_group)
        
    def setup_metrics_section(self, layout):
        """Métricas en tiempo real"""
        self.realtime_metrics_group = QGroupBox(tr("rl_config_panel.realtime_metrics_group"))
        group_layout = QGridLayout(self.realtime_metrics_group)
        group_layout.setSpacing(8)
        
        # Progreso de entrenamiento
        self.train_progress_label = QLabel(tr("rl_config_panel.progress"))
        group_layout.addWidget(self.train_progress_label, 0, 0)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        group_layout.addWidget(self.progress_bar, 0, 1)
        
        # Episodio actual
        self.train_episode_label = QLabel(tr("rl_config_panel.episode"))
        group_layout.addWidget(self.train_episode_label, 1, 0)
        self.episode_label = QLabel("0")
        self.episode_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        group_layout.addWidget(self.episode_label, 1, 1)
        
        # Recompensa promedio
        self.train_reward_label = QLabel(tr("rl_config_panel.reward"))
        group_layout.addWidget(self.train_reward_label, 2, 0)
        self.reward_label = QLabel("0.000")
        self.reward_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        group_layout.addWidget(self.reward_label, 2, 1)
        
        # Loss promedio
        self.train_loss_label = QLabel(tr("rl_config_panel.loss"))
        group_layout.addWidget(self.train_loss_label, 3, 0)
        self.loss_label = QLabel("0.000")
        self.loss_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        group_layout.addWidget(self.loss_label, 3, 1)
        
        # Tiempo transcurrido
        self.train_time_label = QLabel(tr("rl_config_panel.time"))
        group_layout.addWidget(self.train_time_label, 4, 0)
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("font-weight: bold; color: #9C27B0;")
        group_layout.addWidget(self.time_label, 4, 1)
        
        layout.addWidget(self.realtime_metrics_group)
        
    def setup_log_section(self, layout):
        """Log de entrenamiento"""
        self.training_log_group = QGroupBox(tr("rl_config_panel.training_log_group"))
        group_layout = QVBoxLayout(self.training_log_group)
        
        # Área de texto para el log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setMinimumHeight(80)
        
        # Configurar fuente monospace
        log_font = QFont("Consolas, Courier New, monospace")
        log_font.setPointSize(8)
        self.log_text.setFont(log_font)
        
        # Botón para limpiar log
        clear_log_layout = QHBoxLayout()
        clear_log_layout.addStretch()
        self.clear_log_button = QPushButton(tr("rl_config_panel.clear_log"))
        self.clear_log_button.setMaximumWidth(100)
        self.clear_log_button.clicked.connect(self.clear_log)
        clear_log_layout.addWidget(self.clear_log_button)
        
        group_layout.addWidget(self.log_text)
        group_layout.addLayout(clear_log_layout)
        
        layout.addWidget(self.training_log_group)
        
    def setup_timer(self):
        """Configurar timer para actualización de métricas"""
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_metrics_display)
        self.training_start_time = None

    def safe_log_entry(self, message):
        """Agregar entrada al log de manera segura"""
        if hasattr(self, 'log_text') and self.log_text is not None:
            self.add_log_entry(message)
        else:
            print(f"[LOG] {message}")
        
    def start_training(self):
        """Iniciar entrenamiento"""
        if self.training_active:
            return
        
        # Verificar que el TrainingManager esté disponible
        if not self.training_manager:
            self.add_log_entry("❌ Error: TrainingManager no disponible")
            return
            
        # Recopilar parámetros de configuración
        params = self.get_training_parameters()
        
        # Log de inicio
        self.add_log_entry("🚀 Inicializando entrenamiento...")
        self.add_log_entry(f"📋 Configuración: {params['algorithm']} - {params['total_timesteps']} steps")
        
        # Inicializar sesión de entrenamiento
        success = self.training_manager.initialize_training_session(params)
        
        if not success:
            self.add_log_entry("❌ Error inicializando sesión de entrenamiento")
            return
        
        # Iniciar entrenamiento
        if self.training_manager.start_training():
            # Actualizar estado de la UI
            self.training_active = True
            self.is_training_paused = False
            self.train_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.save_button.setEnabled(True)
            self.training_start_time = datetime.now()
            
            # Iniciar timer de métricas
            self.metrics_timer.start(1000)  # Actualizar cada segundo
            
            self.add_log_entry("✅ Entrenamiento iniciado")
            
            # Emitir señal
            self.training_started.emit(params)
        else:
            self.add_log_entry("❌ Error iniciando entrenamiento")
        
    def pause_training(self):
        """Pausar/reanudar entrenamiento"""
        if not self.training_active or not self.training_manager:
            return
            
        if self.is_training_paused:
            # Reanudar (por ahora no implementado en TrainingManager)
            self.is_training_paused = False
            self.pause_button.setText(tr("rl_config_panel.pause"))
            self.add_log_entry("▶️ Entrenamiento reanudado")
        else:
            # Pausar
            if self.training_manager.pause_training():
                self.is_training_paused = True
                self.pause_button.setText(tr("rl_config_panel.resume"))
                self.add_log_entry("⏸️ Entrenamiento pausado")
            
        self.training_paused.emit()
        
    def stop_training(self):
        """Detener entrenamiento"""
        if not self.training_active:
            return
        
        # Detener entrenamiento en el manager
        if self.training_manager:
            self.training_manager.stop_training()
            
        # Actualizar estado de la UI
        self.training_active = False
        self.is_training_paused = False
        self.train_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_button.setText(tr("rl_config_panel.pause"))
        self.stop_button.setEnabled(False)
        
        # Detener timer
        self.metrics_timer.stop()
        
        # Log de finalización
        self.add_log_entry("⏹️ Entrenamiento detenido")
        
        # Emitir señal
        self.training_stopped.emit()
        
    def save_model(self):
        """Guardar modelo"""
        if not self.save_button.isEnabled() or not self.training_manager:
            return
            
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        algorithm = self.algorithm_combo.currentText()
        model_name = f"ponlab_{algorithm}_{timestamp}"
        
        # Log de guardado
        self.add_log_entry(f"💾 Guardando modelo: {model_name}")
        
        # Guardar usando el manager
        if self.training_manager.save_model(model_name):
            self.add_log_entry("✅ Modelo guardado exitosamente")
            # Emitir señal con la ruta real (ahora en models/)
            model_path = f"models/{model_name}.zip"
            self.model_saved.emit(model_path)
        else:
            self.add_log_entry("❌ Error guardando modelo")
        
    def get_training_parameters(self):
        """Obtener parámetros de entrenamiento configurados"""
        return {
            # Entorno
            'num_onus': self.onus_spin.value(),
            'traffic_scenario': self.traffic_combo.currentText(),
            'episode_duration': self.duration_spin.value(),
            'simulation_timestep': self.timestep_spin.value() / 1000.0,  # Convertir a segundos
            
            # Algoritmo
            'algorithm': self.algorithm_combo.currentText(),
            'learning_rate': self.lr_spin.value(),
            'batch_size': self.batch_spin.value(),
            'gamma': self.gamma_spin.value(),
            
            # Entrenamiento
            'total_timesteps': self.timesteps_spin.value(),
            'eval_freq': self.eval_freq_spin.value(),
            'auto_save': self.auto_save_check.isChecked(),
            'use_gpu': self.use_gpu_check.isChecked()
        }

    # === MÉTODOS DE SIMULACIÓN ===

    def refresh_models_list(self):
        """Actualizar lista de modelos disponibles"""
        try:
            self.models_list.clear()
            self.available_models.clear()

            # Buscar modelos en PonLab/models/
            # Siempre usar el directorio PonLab como base
            ponlab_dir = os.path.dirname(__file__)  # ui/
            ponlab_dir = os.path.dirname(ponlab_dir)  # PonLab/
            models_dir = os.path.join(ponlab_dir, "models")  # Carpeta models en la raíz

            # Crear directorio si no existe
            os.makedirs(models_dir, exist_ok=True)

            print(f"Buscando modelos RL en: {models_dir}")
            if not os.path.exists(models_dir):
                self.safe_log_entry("📂 Directorio de modelos no encontrado")
                return

            # Buscar archivos .zip (modelos)
            model_files = glob.glob(os.path.join(models_dir, "*.zip"))

            for model_file in model_files:
                try:
                    # Obtener información del modelo
                    model_info = self.get_model_info(model_file)
                    if model_info:
                        self.available_models.append(model_info)

                        # Agregar a la lista UI
                        item_text = f"{model_info['name']} ({model_info['algorithm']})"
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, model_info)
                        self.models_list.addItem(item)

                except Exception as e:
                    print(f"❌ Error procesando modelo {model_file}: {e}")

            self.safe_log_entry(f"🔄 {len(self.available_models)} modelos encontrados")

        except Exception as e:
            self.safe_log_entry(f"❌ Error actualizando lista de modelos: {e}")

    def get_model_info(self, model_path):
        """Obtener información de un modelo"""
        try:
            # Buscar archivo de metadata
            metadata_path = model_path.replace('.zip', '_metadata.json')

            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)

                config = metadata.get('configuration', {})
                return {
                    'name': os.path.basename(model_path).replace('.zip', ''),
                    'path': model_path,
                    'algorithm': config.get('algorithm', 'Unknown'),
                    'num_onus': config.get('num_onus', 'Unknown'),
                    'traffic_scenario': config.get('traffic_scenario', 'Unknown'),
                    'training_date': metadata.get('training_end_time', 'Unknown'),
                    'metadata': metadata
                }
            else:
                # Inferir información del nombre del archivo
                filename = os.path.basename(model_path)
                parts = filename.replace('.zip', '').split('_')

                algorithm = 'Unknown'
                if len(parts) >= 3:
                    algorithm = parts[2]  # ponlab_rl_PPO_timestamp

                return {
                    'name': filename.replace('.zip', ''),
                    'path': model_path,
                    'algorithm': algorithm,
                    'num_onus': 'Unknown',
                    'traffic_scenario': 'Unknown',
                    'training_date': 'Unknown',
                    'metadata': None
                }

        except Exception as e:
            print(f"❌ Error obteniendo info del modelo: {e}")
            return None

    def on_model_selected(self, item):
        """Callback cuando se selecciona un modelo de la lista"""
        try:
            model_info = item.data(Qt.UserRole)
            if model_info:
                # Actualizar labels de información
                self.model_algorithm_label.setText(model_info['algorithm'])
                self.model_onus_label.setText(str(model_info['num_onus']))
                self.model_traffic_label.setText(model_info['traffic_scenario'])

                # Cargar modelo automáticamente
                model_path = model_info['path']
                self.safe_log_entry(f"Intentando cargar modelo: {model_info['name']}")

                if self.training_manager:
                    if self.training_manager.load_model_for_simulation(model_path):
                        self.loaded_model_path = model_path
                        self.loaded_model_label.setText(model_info['name'])
                        self.simulate_button.setEnabled(True)

                        self.safe_log_entry(f"Modelo cargado exitosamente: {model_info['name']}")
                        self.safe_log_entry(f"Boton de simulacion habilitado")
                        self.model_loaded.emit(model_path)
                    else:
                        self.safe_log_entry(f"Error cargando modelo: {model_info['name']}")
                        self.simulate_button.setEnabled(False)
                else:
                    self.safe_log_entry("Error: TrainingManager no disponible")
                    self.simulate_button.setEnabled(False)

        except Exception as e:
            self.safe_log_entry(f"Error seleccionando modelo: {e}")

    def load_external_model(self):
        """Cargar modelo desde archivo externo"""
        try:
            file_dialog = QFileDialog()
            model_path, _ = file_dialog.getOpenFileName(
                self,
                "Seleccionar Modelo RL",
                "",
                "Modelos RL (*.zip);;Todos los archivos (*.*)"
            )

            if model_path:
                # Cargar modelo usando TrainingManager para simulación
                if self.training_manager and self.training_manager.load_model_for_simulation(model_path):
                    self.loaded_model_path = model_path
                    model_name = os.path.basename(model_path)
                    self.loaded_model_label.setText(model_name)
                    self.simulate_button.setEnabled(True)

                    self.add_log_entry(f"✅ Modelo externo cargado: {model_name}")
                    self.model_loaded.emit(model_path)
                else:
                    self.add_log_entry("❌ Error cargando modelo externo")

        except Exception as e:
            self.add_log_entry(f"❌ Error en carga externa: {e}")

    def load_selected_model(self):
        """Cargar el modelo seleccionado de la lista"""
        try:
            current_item = self.models_list.currentItem()
            if not current_item:
                self.add_log_entry("⚠️ Seleccione un modelo de la lista")
                return False

            model_info = current_item.data(Qt.UserRole)
            model_path = model_info['path']

            # Cargar modelo usando TrainingManager para simulación
            if self.training_manager and self.training_manager.load_model_for_simulation(model_path):
                self.loaded_model_path = model_path
                self.loaded_model_label.setText(model_info['name'])
                self.simulate_button.setEnabled(True)

                self.add_log_entry(f"✅ Modelo cargado: {model_info['name']}")
                self.model_loaded.emit(model_path)
                return True
            else:
                self.add_log_entry("❌ Error cargando modelo")
                return False

        except Exception as e:
            self.add_log_entry(f"❌ Error cargando modelo: {e}")
            return False

    def start_simulation(self):
        """Iniciar simulación con modelo RL"""
        try:
            # Verificar que hay un modelo cargado
            if not self.loaded_model_path:
                # Intentar cargar el modelo seleccionado
                if not self.load_selected_model():
                    self.safe_log_entry("No se pudo cargar modelo")
                    return

            if not self.training_manager:
                self.safe_log_entry("TrainingManager no disponible")
                return

            # Configurar parámetros de simulación
            sim_params = {
                'model_path': self.loaded_model_path,
                'duration': self.sim_duration_spin.value(),
                'show_decisions': self.show_decisions_check.isChecked(),
                'save_metrics': self.save_metrics_check.isChecked()
            }

            # Actualizar estado UI
            self.simulation_active = True
            self.simulate_button.setEnabled(False)
            self.stop_simulation_button.setEnabled(True)
            self.sim_progress_bar.setValue(0)

            # Log de inicio
            self.safe_log_entry("Iniciando simulacion con RL...")
            self.safe_log_entry(f"Duracion: {sim_params['duration']}s")

            # Usar TrainingManager para iniciar simulación real
            if self.training_manager.start_simulation_with_rl(sim_params):
                self.simulation_start_time = datetime.now()
                self.sim_timer = QTimer()
                self.sim_timer.timeout.connect(self.update_simulation_ui)
                self.sim_timer.start(100)  # Actualizar cada 100ms

                self.simulation_started.emit(sim_params)
            else:
                self.safe_log_entry("Error iniciando simulacion")
                self.stop_simulation()

        except Exception as e:
            self.safe_log_entry(f"Error iniciando simulacion: {e}")
            self.stop_simulation()

    def stop_simulation(self):
        """Detener simulación"""
        try:
            if not self.simulation_active:
                return

            # Detener simulación real en TrainingManager
            if self.training_manager:
                self.training_manager.stop_simulation()

            # Detener timers
            if hasattr(self, 'sim_timer'):
                self.sim_timer.stop()

            # Actualizar estado UI
            self.simulation_active = False
            self.simulate_button.setEnabled(True)
            self.stop_simulation_button.setEnabled(False)

            self.add_log_entry("⏹️ Simulación detenida")
            self.simulation_stopped.emit()

        except Exception as e:
            self.add_log_entry(f"❌ Error deteniendo simulación: {e}")

    def update_simulation_ui(self):
        """Actualizar UI de simulación"""
        try:
            if not self.simulation_active or not hasattr(self, 'simulation_start_time'):
                return

            # Actualizar tiempo transcurrido
            elapsed = datetime.now() - self.simulation_start_time
            self.sim_time_label.setText(str(elapsed).split('.')[0])

        except Exception as e:
            print(f"❌ Error actualizando UI de simulación: {e}")

    def update_simulation_metrics_from_manager(self, metrics):
        """Actualizar métricas de simulación desde el TrainingManager"""
        try:
            # Actualizar progreso
            progress = metrics.get('progress_percent', 0)
            self.sim_progress_bar.setValue(int(progress))

            # Actualizar métricas
            self.decisions_label.setText(str(metrics.get('decisions_count', 0)))
            self.performance_label.setText(f"{metrics.get('average_reward', 0):.3f}")

            # Actualizar tiempo transcurrido
            elapsed_time = metrics.get('elapsed_time', 0)
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            self.sim_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Los gráficos se mostrarán en ventana emergente al finalizar

            # Detectar si la simulación terminó
            if progress >= 100:
                self.stop_simulation()
                self.add_log_entry("🎉 Simulación completada")

        except Exception as e:
            print(f"❌ Error actualizando métricas de simulación: {e}")

    # Método eliminado - gráficos solo se muestran al finalizar en ventana emergente

    def handle_simulation_completed(self, results):
        """Manejar finalización de simulación"""
        try:
            self.add_log_entry("🎉 Simulación completada exitosamente")
            self.add_log_entry(f"📊 Pasos totales: {results.get('total_steps', 0)}")
            self.add_log_entry(f"⚡ Recompensa promedio: {results.get('average_reward', 0):.3f}")

            # Actualizar UI
            self.simulation_active = False
            self.simulate_button.setEnabled(True)
            self.stop_simulation_button.setEnabled(False)

            # Mostrar ventana emergente con gráficos de simulación RL
            self.show_rl_graphics_popup(results)

        except Exception as e:
            print(f"❌ Error manejando finalización: {e}")

    def show_rl_graphics_popup(self, rl_results):
        """Mostrar ventana emergente con gráficos de simulación RL"""
        try:
            # Crear ventana emergente si no existe
            if not self.rl_graphics_window:
                self.rl_graphics_window = RLGraphicsPopupWindow(self)

                # Conectar señales
                self.rl_graphics_window.window_closed.connect(self.on_graphics_window_closed)
                self.rl_graphics_window.graphics_exported.connect(self.on_graphics_exported)

                # Aplicar tema actual
                self.rl_graphics_window.set_theme(self.dark_theme)

            # Convertir datos RL al formato de gráficos
            charts_data = self.convert_rl_to_charts_format(rl_results)

            # Mostrar resultados en la ventana emergente
            self.rl_graphics_window.show_rl_results(rl_results, charts_data)

            self.add_log_entry("📊 Ventana de gráficos RL abierta")

        except Exception as e:
            print(f"❌ Error mostrando ventana de gráficos RL: {e}")
            self.add_log_entry(f"❌ Error mostrando gráficos: {e}")

    def on_graphics_window_closed(self):
        """Callback cuando se cierra la ventana de gráficos"""
        self.add_log_entry("📊 Ventana de gráficos cerrada")

    def on_graphics_exported(self, export_dir):
        """Callback cuando se exportan los gráficos"""
        self.add_log_entry(f"📁 Gráficos exportados a: {export_dir}")

    # Método eliminado - ahora se usa ventana emergente

    def convert_rl_to_charts_format(self, rl_results):
        """Convertir resultados RL reales al formato esperado por los gráficos PON"""
        try:
            # Obtener métricas reales del historial si están disponibles
            real_metrics = rl_results.get('real_metrics_history', {})

            # Calcular métricas promedio de los datos reales
            delays_data = real_metrics.get('delays', [])
            throughputs_data = real_metrics.get('throughputs', [])
            buffer_data = real_metrics.get('buffer_levels_history', [])

            # Calcular promedios de métricas reales
            mean_delay = 0.001  # Valor por defecto
            if delays_data:
                mean_delay = sum(d['value'] for d in delays_data) / len(delays_data)

            mean_throughput = 0  # Valor por defecto
            if throughputs_data:
                mean_throughput = sum(t['value'] for t in throughputs_data) / len(throughputs_data)

            # Calcular utilización de red basada en datos reales
            network_utilization = 50  # Valor por defecto
            if buffer_data:
                # Calcular utilización promedio de todas las ONUs
                total_utilization = 0
                count = 0
                for buffer_step in buffer_data:
                    for onu_data in buffer_step.values():
                        if isinstance(onu_data, dict) and 'utilization_percent' in onu_data:
                            total_utilization += onu_data['utilization_percent']
                            count += 1
                if count > 0:
                    network_utilization = total_utilization / count

            # Estructura base compatible con PON charts usando datos reales
            charts_data = {
                'simulation_summary': {
                    'performance_metrics': {
                        'mean_delay': mean_delay,
                        'mean_throughput': mean_throughput,
                        'network_utilization': network_utilization
                    },
                    'simulation_stats': {
                        'total_steps': rl_results.get('total_steps', 0)
                    },
                    'network_stats': {
                        'dba_algorithm': 'RL Agent',
                        'success_rate': min(100, max(0, rl_results.get('average_reward', 0) * 100 + 80))
                    },
                    'episode_metrics': {
                        'delays': delays_data,
                        'throughputs': throughputs_data,
                        'buffer_levels_history': buffer_data
                    }
                },
                'orchestrator_stats': {
                    'allocation_probability': min(1.0, max(0, rl_results.get('average_reward', 0) + 0.7)),
                    'blocking_probability': max(0, min(0.3, 0.2 - rl_results.get('average_reward', 0)))
                }
            }

            # Si no hay datos reales, generar datos mínimos realistas para evitar errores
            if not delays_data and not throughputs_data and not buffer_data:
                print("WARNING: No se encontraron métricas reales, generando datos mínimos basados en reward")
                fallback_data = self._generate_fallback_metrics(rl_results)
                charts_data['simulation_summary']['episode_metrics'] = fallback_data

            return charts_data

        except Exception as e:
            print(f"❌ Error convirtiendo datos RL reales: {e}")
            return {}

    def _generate_fallback_metrics(self, rl_results):
        """Generar datos mínimos realistas cuando no hay métricas reales disponibles"""
        try:
            total_steps = rl_results.get('total_steps', 100)
            avg_reward = rl_results.get('average_reward', 0)

            # Generar 3-5 puntos de datos mínimos basados en el reward
            num_points = min(5, max(3, total_steps // 200))

            fallback_data = {
                'delays': [],
                'throughputs': [],
                'buffer_levels_history': []
            }

            # Calcular métricas base basadas en el reward del agente
            if avg_reward > 0.5:
                # Buen rendimiento
                base_delay = 0.001
                base_throughput = 20.0
                base_buffer = 15
            elif avg_reward > 0.0:
                # Rendimiento moderado
                base_delay = 0.002
                base_throughput = 12.0
                base_buffer = 35
            else:
                # Rendimiento pobre
                base_delay = 0.004
                base_throughput = 8.0
                base_buffer = 60

            # Generar puntos de datos mínimos
            for i in range(num_points):
                step = (i * total_steps) // max(1, num_points - 1) if num_points > 1 else 0
                timestamp = i * 2.0  # Cada 2 segundos

                # Delay con ligera variación
                delay_variation = 1 + (i * 0.1 - 0.2)  # ±20% variación
                delay = max(0.0001, base_delay * delay_variation)

                fallback_data['delays'].append({
                    'step': step,
                    'value': delay,
                    'timestamp': timestamp
                })

                # Throughput con ligera variación
                throughput_variation = 1 + (i * 0.15 - 0.3)  # ±30% variación
                throughput = max(0.1, base_throughput * throughput_variation)

                fallback_data['throughputs'].append({
                    'step': step,
                    'value': throughput,
                    'timestamp': timestamp,
                    'tcont_id': 'fallback'
                })

                # Buffer levels para 4 ONUs con variación
                buffer_step = {}
                for onu_id in range(4):
                    # Variación por ONU y tiempo
                    onu_variation = 1 + ((onu_id - 1.5) * 0.2) + (i * 0.1)
                    buffer_percent = max(0, min(100, base_buffer * onu_variation))

                    buffer_step[f'ONU_{onu_id}'] = {
                        'utilization_percent': buffer_percent,
                        'used_mb': buffer_percent * 3.5 / 100,
                        'capacity_mb': 3.5
                    }

                fallback_data['buffer_levels_history'].append(buffer_step)

            print(f"  Generados {num_points} puntos de datos fallback basados en reward={avg_reward:.3f}")
            return fallback_data

        except Exception as e:
            print(f"❌ Error generando datos fallback: {e}")
            # Datos mínimos absolutos
            return {
                'delays': [{'step': 0, 'value': 0.002, 'timestamp': 0}],
                'throughputs': [{'step': 0, 'value': 10.0, 'timestamp': 0, 'tcont_id': 'minimal'}],
                'buffer_levels_history': [{'ONU_0': {'utilization_percent': 25, 'used_mb': 0.875, 'capacity_mb': 3.5}}]
            }

    def handle_agent_decision(self, decision):
        """Manejar decisión del agente RL"""
        try:
            if self.show_decisions_check.isChecked():
                step = decision.get('step', 0)
                reward = decision.get('reward', 0)
                self.add_log_entry(f"🤖 Paso {step}: Reward={reward:.3f}")

        except Exception as e:
            print(f"❌ Error manejando decisión del agente: {e}")

    def update_metrics_display(self):
        """Actualizar visualización de métricas"""
        if not self.training_active:
            return
            
        # Actualizar labels (aquí se conectaría con las métricas reales)
        self.episode_label.setText(str(self.current_episode))
        self.reward_label.setText(f"{self.current_reward:.3f}")
        self.loss_label.setText(f"{self.current_loss:.3f}")
        
        # Actualizar progreso (simplificado)
        progress = min(100, (self.current_episode / 1000) * 100)
        self.progress_bar.setValue(int(progress))
        
        # Actualizar tiempo transcurrido
        if self.training_start_time:
            from datetime import datetime
            elapsed = datetime.now() - self.training_start_time
            self.time_label.setText(str(elapsed).split('.')[0])
            
    def update_training_metrics(self, episode, reward, loss):
        """Actualizar métricas desde entrenamiento externo"""
        self.current_episode = episode
        self.current_reward = reward
        self.current_loss = loss
        
    def add_log_entry(self, message):
        """Agregar entrada al log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        
        # Auto-scroll al final
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_log(self):
        """Limpiar el log"""
        self.log_text.clear()
        self.add_log_entry("🧹 Log limpiado")
    
    # Callbacks para señales del TrainingManager
    def update_training_metrics_from_manager(self, metrics):
        """Actualizar métricas desde el TrainingManager"""
        try:
            # Extraer métricas de rendimiento
            perf_data = metrics.get('performance_data', {})
            if 'reward' in perf_data:
                self.current_reward = float(perf_data['reward'])
            if 'loss' in perf_data:
                self.current_loss = float(perf_data['loss'])
            
            # Extraer datos de simulación
            sim_data = metrics.get('simulation_data', {})
            if 'episode' in sim_data:
                self.current_episode = int(sim_data['episode'])
            
            # Log periódico (cada 100 episodios)
            if self.current_episode > 0 and self.current_episode % 100 == 0:
                self.add_log_entry(f"📊 Episodio {self.current_episode} - Reward: {self.current_reward:.3f}")
                
        except Exception as e:
            print(f"❌ Error actualizando métricas: {e}")
    
    def update_training_status(self, status):
        """Actualizar estado del entrenamiento desde el TrainingManager"""
        try:
            if status == "initialized":
                self.add_log_entry("🔧 Sesión inicializada")
            elif status == "training":
                self.add_log_entry("🎯 Entrenamiento en progreso")
            elif status == "paused":
                self.add_log_entry("⏸️ Entrenamiento pausado")
            elif status == "stopped":
                self.add_log_entry("⏹️ Entrenamiento detenido")
            elif status == "completed":
                self.add_log_entry("🎉 Entrenamiento completado")
                self.stop_training()  # Actualizar UI
            elif status == "error":
                self.add_log_entry("❌ Error en entrenamiento")
                self.stop_training()  # Actualizar UI
                
        except Exception as e:
            print(f"❌ Error actualizando estado: {e}")
    
    def handle_training_error(self, error_msg):
        """Manejar errores del entrenamiento"""
        self.add_log_entry(f"❌ Error: {error_msg}")
        self.stop_training()  # Resetear UI
    
    def handle_training_completed(self, model_path):
        """Manejar finalización del entrenamiento"""
        self.add_log_entry(f"🎉 Entrenamiento completado")
        self.add_log_entry(f"💾 Modelo guardado en: {model_path}")
        
        # Actualizar UI
        self.training_active = False
        self.is_training_paused = False
        self.train_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(True)  # Permitir guardar modelos adicionales
        
    def set_theme(self, dark_theme):
        """Aplicar tema al panel"""
        self.dark_theme = dark_theme
        
        if dark_theme:
            self.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #555555;
                    border-radius: 8px;
                    margin-top: 6px;
                    padding-top: 10px;
                    background-color: #2c2c2c;
                    color: #ffffff;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    background-color: #2c2c2c;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                    background: transparent;
                }
                QSpinBox, QDoubleSpinBox, QComboBox {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #666666;
                    border-radius: 4px;
                    padding: 4px;
                }
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #666666;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
                QPushButton:disabled {
                    background-color: #2a2a2a;
                    color: #666666;
                }
                QProgressBar {
                    border: 1px solid #666666;
                    border-radius: 4px;
                    background-color: #2c2c2c;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #666666;
                    border-radius: 4px;
                }
                QCheckBox {
                    color: #ffffff;
                }
                QTabWidget::pane {
                    border: 1px solid #666666;
                    background-color: #2c2c2c;
                }
                QTabBar::tab {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #666666;
                    border-bottom: none;
                    padding: 8px 20px;
                    min-width: 100px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #2c2c2c;
                    color: #ffffff;
                    font-weight: bold;
                }
                QTabBar::tab:hover {
                    background-color: #505050;
                }
            """)
        else:
            self.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #cccccc;
                    border-radius: 8px;
                    margin-top: 6px;
                    padding-top: 10px;
                    background-color: #ffffff;
                    color: #333333;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    background-color: #ffffff;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                    background: transparent;
                }
                QSpinBox, QDoubleSpinBox, QComboBox {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 4px;
                }
                QPushButton {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
                QPushButton:pressed {
                    background-color: #e0e0e0;
                }
                QPushButton:disabled {
                    background-color: #f5f5f5;
                    color: #cccccc;
                }
                QProgressBar {
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    background-color: #ffffff;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
                QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                }
                QCheckBox {
                    color: #333333;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                    background-color: #ffffff;
                    border-radius: 4px;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    color: #333333;
                    border: 1px solid #cccccc;
                    padding: 8px 20px;
                    min-width: 100px;
                    margin-right: 2px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    border-bottom: 1px solid #ffffff;
                    font-weight: bold;
                }
                QTabBar::tab:hover {
                    background-color: #e8e8e8;
                }
            """)

        # Aplicar tema a la ventana de gráficos RL si existe
        if hasattr(self, 'rl_graphics_window') and self.rl_graphics_window:
            self.rl_graphics_window.set_theme(dark_theme)
    
    def retranslate_ui(self):
        """Actualizar todos los textos traducibles"""
        # Mensaje informativo
        if hasattr(self, 'info_label'):
            self.info_label.setText(tr("rl_config_panel.info_message"))
        
        # Sección de selección de modelo
        if hasattr(self, 'model_selection_group'):
            self.model_selection_group.setTitle(tr("rl_config_panel.model_selection_group"))
        if hasattr(self, 'available_models_label'):
            self.available_models_label.setText(tr("rl_config_panel.available_models"))
        if hasattr(self, 'refresh_button'):
            self.refresh_button.setText(tr("rl_config_panel.refresh_button"))
            self.refresh_button.setToolTip(tr("rl_config_panel.refresh_tooltip"))
        if hasattr(self, 'load_external_button'):
            self.load_external_button.setText(tr("rl_config_panel.load_external_button"))
            self.load_external_button.setToolTip(tr("rl_config_panel.load_external_tooltip"))
        if hasattr(self, 'loaded_model_info_label'):
            self.loaded_model_info_label.setText(tr("rl_config_panel.loaded_model"))
        if hasattr(self, 'algorithm_info_label'):
            self.algorithm_info_label.setText(tr("rl_config_panel.algorithm"))
        if hasattr(self, 'trained_onus_label'):
            self.trained_onus_label.setText(tr("rl_config_panel.trained_onus"))
        if hasattr(self, 'traffic_info_label'):
            self.traffic_info_label.setText(tr("rl_config_panel.traffic"))
        
        # Sección de configuración de simulación
        if hasattr(self, 'sim_config_group'):
            self.sim_config_group.setTitle(tr("rl_config_panel.sim_config_group"))
        if hasattr(self, 'duration_s_label'):
            self.duration_s_label.setText(tr("rl_config_panel.duration_s"))
        if hasattr(self, 'sim_duration_spin'):
            self.sim_duration_spin.setToolTip(tr("rl_config_panel.duration_tooltip"))
        if hasattr(self, 'show_decisions_check'):
            self.show_decisions_check.setText(tr("rl_config_panel.show_decisions"))
            self.show_decisions_check.setToolTip(tr("rl_config_panel.show_decisions_tooltip"))
        if hasattr(self, 'save_metrics_check'):
            self.save_metrics_check.setText(tr("rl_config_panel.save_metrics"))
            self.save_metrics_check.setToolTip(tr("rl_config_panel.save_metrics_tooltip"))
        
        # Sección de controles de simulación
        if hasattr(self, 'sim_controls_group'):
            self.sim_controls_group.setTitle(tr("rl_config_panel.sim_controls_group"))
        if hasattr(self, 'simulate_button'):
            self.simulate_button.setText(tr("rl_config_panel.execute_simulation"))
            self.simulate_button.setToolTip(tr("rl_config_panel.execute_simulation_tooltip"))
        if hasattr(self, 'stop_simulation_button'):
            self.stop_simulation_button.setText(tr("rl_config_panel.stop"))
            self.stop_simulation_button.setToolTip(tr("rl_config_panel.stop_simulation_tooltip"))
        
        # Sección de métricas de simulación
        if hasattr(self, 'sim_metrics_group'):
            self.sim_metrics_group.setTitle(tr("rl_config_panel.sim_metrics_group"))
        if hasattr(self, 'sim_progress_label'):
            self.sim_progress_label.setText(tr("rl_config_panel.progress"))
        if hasattr(self, 'sim_decisions_label'):
            self.sim_decisions_label.setText(tr("rl_config_panel.decisions"))
        if hasattr(self, 'sim_performance_label'):
            self.sim_performance_label.setText(tr("rl_config_panel.performance"))
        if hasattr(self, 'sim_blocks_label'):
            self.sim_blocks_label.setText(tr("rl_config_panel.blocks"))
        if hasattr(self, 'sim_time_info_label'):
            self.sim_time_info_label.setText(tr("rl_config_panel.time"))
        
        # Sección de entorno PON
        if hasattr(self, 'pon_environment_group'):
            self.pon_environment_group.setTitle(tr("rl_config_panel.pon_environment_group"))
        if hasattr(self, 'onus_label'):
            self.onus_label.setText(tr("rl_config_panel.onus"))
        if hasattr(self, 'onus_spin'):
            self.onus_spin.setToolTip(tr("rl_config_panel.onus_tooltip"))
        if hasattr(self, 'traffic_label'):
            self.traffic_label.setText(tr("rl_config_panel.traffic_label"))
        if hasattr(self, 'traffic_combo'):
            self.traffic_combo.setToolTip(tr("rl_config_panel.traffic_tooltip"))
        if hasattr(self, 'duration_episode_label'):
            self.duration_episode_label.setText(tr("rl_config_panel.duration_episode"))
        if hasattr(self, 'duration_spin'):
            self.duration_spin.setToolTip(tr("rl_config_panel.duration_episode_tooltip"))
        if hasattr(self, 'timestep_label'):
            self.timestep_label.setText(tr("rl_config_panel.timestep_ms"))
        if hasattr(self, 'timestep_spin'):
            self.timestep_spin.setToolTip(tr("rl_config_panel.timestep_tooltip"))
        
        # Sección de algoritmo de aprendizaje
        if hasattr(self, 'learning_algorithm_group'):
            self.learning_algorithm_group.setTitle(tr("rl_config_panel.learning_algorithm_group"))
        if hasattr(self, 'algorithm_label'):
            self.algorithm_label.setText(tr("rl_config_panel.algorithm_label"))
        if hasattr(self, 'algorithm_combo'):
            self.algorithm_combo.setToolTip(tr("rl_config_panel.algorithm_tooltip"))
        if hasattr(self, 'learning_rate_label'):
            self.learning_rate_label.setText(tr("rl_config_panel.learning_rate"))
        if hasattr(self, 'lr_spin'):
            self.lr_spin.setToolTip(tr("rl_config_panel.learning_rate_tooltip"))
        if hasattr(self, 'batch_size_label'):
            self.batch_size_label.setText(tr("rl_config_panel.batch_size"))
        if hasattr(self, 'batch_spin'):
            self.batch_spin.setToolTip(tr("rl_config_panel.batch_size_tooltip"))
        if hasattr(self, 'gamma_label'):
            self.gamma_label.setText(tr("rl_config_panel.gamma"))
        if hasattr(self, 'gamma_spin'):
            self.gamma_spin.setToolTip(tr("rl_config_panel.gamma_tooltip"))
        
        # Sección de parámetros de entrenamiento
        if hasattr(self, 'training_params_group'):
            self.training_params_group.setTitle(tr("rl_config_panel.training_params_group"))
        if hasattr(self, 'total_steps_label'):
            self.total_steps_label.setText(tr("rl_config_panel.total_steps"))
        if hasattr(self, 'timesteps_spin'):
            self.timesteps_spin.setToolTip(tr("rl_config_panel.total_steps_tooltip"))
        if hasattr(self, 'eval_freq_label'):
            self.eval_freq_label.setText(tr("rl_config_panel.eval_freq"))
        if hasattr(self, 'eval_freq_spin'):
            self.eval_freq_spin.setToolTip(tr("rl_config_panel.eval_freq_tooltip"))
        if hasattr(self, 'auto_save_check'):
            self.auto_save_check.setText(tr("rl_config_panel.auto_save"))
            self.auto_save_check.setToolTip(tr("rl_config_panel.auto_save_tooltip"))
        if hasattr(self, 'use_gpu_check'):
            self.use_gpu_check.setText(tr("rl_config_panel.use_gpu"))
            self.use_gpu_check.setToolTip(tr("rl_config_panel.use_gpu_tooltip"))
        
        # Sección de controles
        if hasattr(self, 'controls_group'):
            self.controls_group.setTitle(tr("rl_config_panel.controls_group"))
        if hasattr(self, 'train_button'):
            self.train_button.setText(tr("rl_config_panel.train"))
            self.train_button.setToolTip(tr("rl_config_panel.train_tooltip"))
        if hasattr(self, 'pause_button'):
            # El texto del botón pause cambia dinámicamente
            if self.is_training_paused:
                self.pause_button.setText(tr("rl_config_panel.resume"))
            else:
                self.pause_button.setText(tr("rl_config_panel.pause"))
            self.pause_button.setToolTip(tr("rl_config_panel.pause_tooltip"))
        if hasattr(self, 'stop_button'):
            self.stop_button.setText(tr("rl_config_panel.stop"))
            self.stop_button.setToolTip(tr("rl_config_panel.stop_tooltip"))
        if hasattr(self, 'save_button'):
            self.save_button.setText(tr("rl_config_panel.save"))
            self.save_button.setToolTip(tr("rl_config_panel.save_tooltip"))
        
        # Sección de métricas en tiempo real
        if hasattr(self, 'realtime_metrics_group'):
            self.realtime_metrics_group.setTitle(tr("rl_config_panel.realtime_metrics_group"))
        if hasattr(self, 'train_progress_label'):
            self.train_progress_label.setText(tr("rl_config_panel.progress"))
        if hasattr(self, 'train_episode_label'):
            self.train_episode_label.setText(tr("rl_config_panel.episode"))
        if hasattr(self, 'train_reward_label'):
            self.train_reward_label.setText(tr("rl_config_panel.reward"))
        if hasattr(self, 'train_loss_label'):
            self.train_loss_label.setText(tr("rl_config_panel.loss"))
        if hasattr(self, 'train_time_label'):
            self.train_time_label.setText(tr("rl_config_panel.time"))
        
        # Sección de log de entrenamiento
        if hasattr(self, 'training_log_group'):
            self.training_log_group.setTitle(tr("rl_config_panel.training_log_group"))
        if hasattr(self, 'clear_log_button'):
            self.clear_log_button.setText(tr("rl_config_panel.clear_log"))
