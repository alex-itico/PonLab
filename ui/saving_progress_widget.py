"""
Saving Progress Widget
Widget para mostrar progreso de guardado incremental en tiempo real
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QProgressBar, QFrame, QPushButton)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont


class SavingProgressWidget(QWidget):
    """
    Widget elegante para mostrar progreso de guardado incremental
    Se actualiza en tiempo real durante la simulación
    """

    # Señales
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.adapter = None
        self.update_timer = None
        self.total_snapshots_estimate = 0
        self.setup_ui()

    def setup_ui(self):
        """Configurar interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Frame contenedor con estilo
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        main_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setSpacing(10)

        # Título
        self.title_label = QLabel("💾 Guardando Datos de Simulación...")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #495057;")
        frame_layout.addWidget(self.title_label)

        # Subtítulo
        self.subtitle_label = QLabel("Escritura incremental en segundo plano")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setStyleSheet("color: #6c757d; font-size: 9pt; font-style: italic;")
        frame_layout.addWidget(self.subtitle_label)

        # Separador
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("background-color: #dee2e6;")
        frame_layout.addWidget(separator1)

        # Barra de progreso principal
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)

        self.progress_label = QLabel("Progreso general:")
        self.progress_label.setStyleSheet("color: #495057; font-weight: bold;")
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #ced4da;
                border-radius: 5px;
                text-align: center;
                background-color: #e9ecef;
                color: #212529;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                   stop:0 #4CAF50, stop:1 #45a049);
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        frame_layout.addLayout(progress_layout)

        # Estadísticas detalladas
        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(8)

        # Snapshots escritos
        snapshots_layout = QHBoxLayout()
        snapshots_icon = QLabel("📊")
        snapshots_icon.setStyleSheet("font-size: 16pt;")
        self.snapshots_label = QLabel("Snapshots: 0 / ?")
        self.snapshots_label.setStyleSheet("color: #495057;")
        snapshots_layout.addWidget(snapshots_icon)
        snapshots_layout.addWidget(self.snapshots_label)
        snapshots_layout.addStretch()
        stats_layout.addLayout(snapshots_layout)

        # Tamaño del archivo
        size_layout = QHBoxLayout()
        size_icon = QLabel("💾")
        size_icon.setStyleSheet("font-size: 16pt;")
        self.size_label = QLabel("Tamaño: 0.00 MB (comprimido)")
        self.size_label.setStyleSheet("color: #495057;")
        size_layout.addWidget(size_icon)
        size_layout.addWidget(self.size_label)
        size_layout.addStretch()
        stats_layout.addLayout(size_layout)

        # Velocidad de escritura
        speed_layout = QHBoxLayout()
        speed_icon = QLabel("⏱️")
        speed_icon.setStyleSheet("font-size: 16pt;")
        self.speed_label = QLabel("Velocidad: 0 items/s")
        self.speed_label.setStyleSheet("color: #495057;")
        speed_layout.addWidget(speed_icon)
        speed_layout.addWidget(self.speed_label)
        speed_layout.addStretch()
        stats_layout.addLayout(speed_layout)

        # Tiempo transcurrido
        time_layout = QHBoxLayout()
        time_icon = QLabel("🕐")
        time_icon.setStyleSheet("font-size: 16pt;")
        self.time_label = QLabel("Tiempo: 0.0s")
        self.time_label.setStyleSheet("color: #495057;")
        time_layout.addWidget(time_icon)
        time_layout.addWidget(self.time_label)
        time_layout.addStretch()
        stats_layout.addLayout(time_layout)

        frame_layout.addLayout(stats_layout)

        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #dee2e6;")
        frame_layout.addWidget(separator2)

        # Mensaje informativo
        self.info_label = QLabel("✨ Puedes seguir usando la aplicación mientras se guarda")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #28a745; font-size: 9pt; font-style: italic;")
        frame_layout.addWidget(self.info_label)

        # Botón cerrar (opcional)
        self.close_button = QPushButton("Minimizar")
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.close_button.clicked.connect(self.close_requested.emit)
        frame_layout.addWidget(self.close_button)

        layout.addWidget(main_frame)

    def start_monitoring(self, adapter, total_snapshots_estimate: int):
        """
        Iniciar monitoreo de progreso

        Args:
            adapter: Instancia de PONAdapter
            total_snapshots_estimate: Estimación de snapshots totales
        """
        self.adapter = adapter
        self.total_snapshots_estimate = total_snapshots_estimate

        # Inicializar UI con valores iniciales
        self.snapshots_label.setText(f"Snapshots: 0 / {self.total_snapshots_estimate:,}")
        self.size_label.setText(f"Tamaño: 0.00 MB (comprimido)")
        self.speed_label.setText(f"Velocidad: 0 items/s")
        self.time_label.setText(f"Tiempo: 0.0s")
        self.progress_bar.setValue(0)

        # Actualizar cada 500ms
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_statistics)
        self.update_timer.start(500)

        # Primera actualización inmediata
        self.update_statistics()

    def update_statistics(self):
        """Actualizar estadísticas de progreso"""
        if not self.adapter:
            return

        stats = self.adapter.get_incremental_writing_statistics()
        if not stats:
            return

        chunks_written = stats.get('chunks_written', 0)
        mb_written = stats.get('mb_written', 0)
        elapsed_time = stats.get('elapsed_time', 0)
        items_per_second = stats.get('items_per_second', 0)

        # Actualizar progreso
        if self.total_snapshots_estimate > 0:
            progress = min(int((chunks_written / self.total_snapshots_estimate) * 100), 99)
        else:
            # Si no hay estimación, usar progreso indeterminado
            progress = min(chunks_written // 1000, 99)  # Cada 1000 items = 1%

        self.progress_bar.setValue(progress)

        # Actualizar labels
        self.snapshots_label.setText(f"Snapshots: {chunks_written:,} / {self.total_snapshots_estimate:,}")
        self.size_label.setText(f"Tamaño: {mb_written:.2f} MB (comprimido)")
        self.speed_label.setText(f"Velocidad: {items_per_second:.0f} items/s")
        self.time_label.setText(f"Tiempo: {elapsed_time:.1f}s")

    def set_completed(self):
        """Marcar guardado como completado"""
        if self.update_timer:
            self.update_timer.stop()

        self.progress_bar.setValue(100)
        self.title_label.setText("✅ Datos Guardados Exitosamente")
        self.title_label.setStyleSheet("color: #28a745; font-weight: bold;")
        self.subtitle_label.setText("Guardado completado con éxito")
        self.info_label.setText("🎉 Todos los datos fueron guardados correctamente")
        self.close_button.setText("Cerrar")

    def stop_monitoring(self):
        """Detener monitoreo"""
        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None
