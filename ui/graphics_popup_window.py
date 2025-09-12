"""
Graphics Popup Window
Ventana emergente que muestra automáticamente los gráficos al finalizar simulación
"""

import os
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QScrollArea, QWidget,
                             QGroupBox, QGridLayout, QTextEdit, QSplitter,
                             QFrame, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon

from .pon_metrics_charts import PONMetricsChartsPanel


class GraphicsPopupWindow(QDialog):
    """Ventana emergente que muestra gráficos de simulación automáticamente"""
    
    # Señales
    window_closed = pyqtSignal()
    graphics_exported = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 Resultados de Simulación PON - Gráficos")
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        self.resize(1200, 800)
        
        # Datos de la simulación
        self.simulation_data = {}
        self.session_directory = ""
        self.charts_panel = None
        
        # Configurar interfaz
        self.setup_ui()
        
        # Timer para auto-cerrar (opcional)
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header con información
        self.setup_header(layout)
        
        # Área principal con tabs
        self.setup_main_area(layout)
        
        # Footer con controles
        self.setup_footer(layout)
        
    def setup_header(self, layout):
        """Configurar header con información de la simulación"""
        header_frame = QFrame()
        header_frame.setObjectName("popup_header_frame")  # Identificador para QSS
        header_layout = QHBoxLayout(header_frame)
        
        # Título principal
        self.title_label = QLabel("🎉 ¡Simulación Completada Exitosamente!")
        self.title_label.setObjectName("popup_title_label")  # Identificador para QSS
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Información de sesión
        self.session_info_label = QLabel("📁 Guardado en: [pendiente]")
        self.session_info_label.setObjectName("popup_session_label")  # Identificador para QSS
        header_layout.addWidget(self.session_info_label)
        
        layout.addWidget(header_frame)
    
    def setup_main_area(self, layout):
        """Configurar área principal con tabs"""
        self.tabs = QTabWidget()
        self.tabs.setObjectName("popup_tabs")  # Identificador para QSS
        
        # Tab 1: Gráficos principales
        self.setup_graphics_tab()
        
        # Tab 2: Resumen de datos
        self.setup_summary_tab()
        
        # Tab 3: Archivos generados
        self.setup_files_tab()
        
        layout.addWidget(self.tabs)
    
    def setup_graphics_tab(self):
        """Configurar tab principal de gráficos"""
        # Crear panel de gráficos integrado
        self.charts_panel = PONMetricsChartsPanel()
        
        # Agregar scroll por si es necesario
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.charts_panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.tabs.addTab(scroll_area, "📊 Gráficos Interactivos")
    
    def setup_summary_tab(self):
        """Configurar tab de resumen de datos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Resumen textual
        summary_group = QGroupBox("📋 Resumen de Simulación")
        summary_group.setObjectName("popup_group")  # Identificador para QSS
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_text = QTextEdit()
        self.summary_text.setObjectName("popup_text_edit")  # Identificador para QSS
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        summary_layout.addWidget(self.summary_text)
        
        layout.addWidget(summary_group)
        
        # Métricas principales en grid
        metrics_group = QGroupBox("📈 Métricas Principales")
        metrics_group.setObjectName("popup_group")  # Identificador para QSS
        self.metrics_layout = QGridLayout(metrics_group)
        layout.addWidget(metrics_group)
        
        layout.addStretch()
        
        self.tabs.addTab(tab, "📋 Resumen")
    
    def setup_files_tab(self):
        """Configurar tab de archivos generados"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Información de archivos
        files_group = QGroupBox("📁 Archivos Generados")
        files_group.setObjectName("popup_group")  # Identificador para QSS
        files_layout = QVBoxLayout(files_group)
        
        self.files_text = QTextEdit()
        self.files_text.setObjectName("popup_text_edit")  # Identificador para QSS
        self.files_text.setReadOnly(True)
        self.files_text.setMaximumHeight(150)
        files_layout.addWidget(self.files_text)
        
        # Botones para abrir directorio
        buttons_layout = QHBoxLayout()
        
        self.open_folder_btn = QPushButton("📂 Abrir Carpeta")
        self.open_folder_btn.setObjectName("popup_button")  # Identificador para QSS
        self.open_folder_btn.clicked.connect(self.open_session_folder)
        buttons_layout.addWidget(self.open_folder_btn)
        
        self.open_graphics_btn = QPushButton("🖼️ Ver Gráficos Guardados")
        self.open_graphics_btn.setObjectName("popup_button")  # Identificador para QSS
        self.open_graphics_btn.clicked.connect(self.open_graphics_folder)
        buttons_layout.addWidget(self.open_graphics_btn)
        
        buttons_layout.addStretch()
        files_layout.addLayout(buttons_layout)
        
        layout.addWidget(files_group)
        
        # Instrucciones
        instructions_group = QGroupBox("💡 Instrucciones")
        instructions_group.setObjectName("popup_group")  # Identificador para QSS
        instructions_layout = QVBoxLayout(instructions_group)
        
        instructions = QLabel("""
        📊 <b>Gráficos Interactivos:</b> Usa la pestaña "Gráficos Interactivos" para zoom y análisis detallado
        
        📁 <b>Archivos Guardados:</b> Todos los gráficos se han guardado como PNG de alta resolución
        
        📄 <b>Datos JSON:</b> Los datos completos están en 'datos_simulacion.json' para análisis posterior
        
        📋 <b>Resumen:</b> El archivo 'RESUMEN.txt' contiene un resumen legible de los resultados
        
        🔍 <b>Comparación:</b> Guarda múltiples simulaciones para comparar diferentes algoritmos
        """)
        instructions.setObjectName("popup_instructions_label")  # Identificador para QSS
        instructions.setWordWrap(True)
        instructions_layout.addWidget(instructions)
        
        layout.addWidget(instructions_group)
        
        self.tabs.addTab(tab, "📁 Archivos")
    
    def setup_footer(self, layout):
        """Configurar footer con controles"""
        footer_layout = QHBoxLayout()
        
        # Botón de exportar adicional
        self.export_btn = QPushButton("💾 Exportar Gráficos Adicionales")
        self.export_btn.setObjectName("popup_button")  # Identificador para QSS
        self.export_btn.clicked.connect(self.export_additional_graphics)
        footer_layout.addWidget(self.export_btn)
        
        footer_layout.addStretch()
        
        # Botón de cerrar
        self.close_btn = QPushButton("✅ Cerrar")
        self.close_btn.setObjectName("popup_button")  # Identificador para QSS
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setDefault(True)
        footer_layout.addWidget(self.close_btn)
        
        layout.addLayout(footer_layout)
    
    def show_simulation_results(self, 
                               simulation_data: Dict[str, Any], 
                               session_directory: str,
                               session_info: Optional[Dict[str, Any]] = None):
        """
        Mostrar resultados de simulación en la ventana emergente
        
        Args:
            simulation_data: Datos completos de la simulación
            session_directory: Directorio donde se guardaron los archivos
            session_info: Información adicional de la sesión
        """
        self.simulation_data = simulation_data
        self.session_directory = session_directory
        
        # Actualizar header
        self.session_info_label.setText(f"📁 Guardado en: {session_directory}")
        
        # Actualizar gráficos interactivos
        if self.charts_panel:
            self.charts_panel.update_charts_with_data(simulation_data)
        
        # Actualizar resumen
        self.update_summary_display(simulation_data, session_info)
        
        # Actualizar información de archivos
        self.update_files_display(session_directory)
        
        # Mostrar ventana
        self.show()
        self.raise_()
        self.activateWindow()
        
        print(f"🎉 Ventana de resultados mostrada con gráficos desde: {session_directory}")
    
    def update_summary_display(self, simulation_data: Dict[str, Any], session_info: Optional[Dict[str, Any]]):
        """Actualizar display de resumen"""
        # Texto de resumen
        summary_text = self.generate_summary_text(simulation_data, session_info)
        self.summary_text.setPlainText(summary_text)
        
        # Métricas en grid
        self.update_metrics_grid(simulation_data)
    
    def generate_summary_text(self, simulation_data: Dict[str, Any], session_info: Optional[Dict[str, Any]]) -> str:
        """Generar texto de resumen legible"""
        sim_summary = simulation_data.get('simulation_summary', {})
        sim_stats = sim_summary.get('simulation_stats', {})
        perf_metrics = sim_summary.get('performance_metrics', {})
        
        summary_lines = [
            "🎯 SIMULACIÓN PON COMPLETADA EXITOSAMENTE",
            "=" * 50,
            "",
            f"⏱️ Pasos ejecutados: {sim_stats.get('total_steps', 0)}",
            f"🕐 Tiempo simulado: {sim_stats.get('simulation_time', 0):.6f} segundos",
            f"📊 Solicitudes totales: {sim_stats.get('total_requests', 0)}",
            f"✅ Solicitudes exitosas: {sim_stats.get('successful_requests', 0)}",
            f"📈 Tasa de éxito: {sim_stats.get('success_rate', 0):.1f}%",
            "",
            "🔍 MÉTRICAS DE RENDIMIENTO:",
            f"⚡ Delay promedio: {perf_metrics.get('mean_delay', 0):.6f} segundos",
            f"📶 Throughput promedio: {perf_metrics.get('mean_throughput', 0):.3f} MB/s",
            f"📊 Utilización de red: {perf_metrics.get('network_utilization', 0):.1f}%",
            f"💾 Capacidad total servida: {perf_metrics.get('total_capacity_served', 0):.3f} MB"
        ]
        
        if session_info:
            summary_lines.extend([
                "",
                "⚙️ CONFIGURACIÓN UTILIZADA:",
                f"🏠 ONUs: {session_info.get('num_onus', 'N/A')}",
                f"🔧 Algoritmo DBA: {session_info.get('algorithm', 'N/A')}",
                f"🌐 Escenario: {session_info.get('traffic_scenario', 'N/A')}"
            ])
        
        return "\n".join(summary_lines)
    
    def update_metrics_grid(self, simulation_data: Dict[str, Any]):
        """Actualizar grid de métricas principales"""
        # Limpiar grid existente
        for i in reversed(range(self.metrics_layout.count())): 
            self.metrics_layout.itemAt(i).widget().setParent(None)
        
        sim_summary = simulation_data.get('simulation_summary', {})
        perf_metrics = sim_summary.get('performance_metrics', {})
        sim_stats = sim_summary.get('simulation_stats', {})
        
        # Métricas para mostrar
        metrics = [
            ("📊 Pasos", f"{sim_stats.get('total_steps', 0)}", "#e3f2fd"),
            ("⚡ Delay", f"{perf_metrics.get('mean_delay', 0):.6f}s", "#fff3e0"), 
            ("📶 Throughput", f"{perf_metrics.get('mean_throughput', 0):.2f} MB/s", "#e8f5e8"),
            ("📈 Utilización", f"{perf_metrics.get('network_utilization', 0):.1f}%", "#fce4ec"),
            ("✅ Éxito", f"{sim_stats.get('success_rate', 0):.1f}%", "#f3e5f5"),
            ("💾 Datos", f"{perf_metrics.get('total_capacity_served', 0):.2f} MB", "#e0f2f1")
        ]
        
        # Agregar métricas al grid
        for i, (label_text, value_text, bg_color) in enumerate(metrics):
            row = i // 3
            col = i % 3
            
            # Crear widget de métrica
            metric_widget = self.create_metric_widget(label_text, value_text, bg_color)
            self.metrics_layout.addWidget(metric_widget, row, col)
    
    def create_metric_widget(self, label_text: str, value_text: str, bg_color: str) -> QWidget:
        """Crear widget individual para una métrica"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                margin: 2px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        
        # Etiqueta
        label = QLabel(label_text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(label)
        
        # Valor
        value = QLabel(value_text)
        value.setAlignment(Qt.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(12)
        value_font.setBold(True)
        value.setFont(value_font)
        value.setStyleSheet("color: #1976d2;")
        layout.addWidget(value)
        
        return widget
    
    def update_files_display(self, session_directory: str):
        """Actualizar display de archivos generados"""
        if not os.path.exists(session_directory):
            self.files_text.setPlainText("❌ Directorio no encontrado")
            return
        
        files_info = []
        files_info.append(f"📁 Directorio de sesión: {session_directory}")
        files_info.append("")
        
        # Listar archivos generados
        files_info.append("📄 ARCHIVOS GENERADOS:")
        
        for filename in os.listdir(session_directory):
            filepath = os.path.join(session_directory, filename)
            
            if filename.endswith('.json'):
                size_kb = os.path.getsize(filepath) / 1024
                files_info.append(f"  📊 {filename} ({size_kb:.1f} KB)")
            elif filename.endswith('.txt'):
                files_info.append(f"  📋 {filename}")
            elif os.path.isdir(filepath) and filename == 'graficos':
                # Contar gráficos
                graphics_count = len([f for f in os.listdir(filepath) if f.endswith('.png')])
                files_info.append(f"  🖼️ {filename}/ ({graphics_count} gráficos PNG)")
        
        self.files_text.setPlainText("\n".join(files_info))
    
    def open_session_folder(self):
        """Abrir carpeta de sesión en el explorador"""
        if not self.session_directory or not os.path.exists(self.session_directory):
            QMessageBox.warning(self, "Error", "Directorio de sesión no encontrado")
            return
        
        try:
            # Abrir en explorador según el OS
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(self.session_directory)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", self.session_directory])
            else:  # Linux
                subprocess.run(["xdg-open", self.session_directory])
                
            print(f"📂 Carpeta abierta: {self.session_directory}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la carpeta: {e}")
    
    def open_graphics_folder(self):
        """Abrir carpeta específica de gráficos"""
        graphics_dir = os.path.join(self.session_directory, "graficos")
        
        if not os.path.exists(graphics_dir):
            QMessageBox.warning(self, "Error", "Carpeta de gráficos no encontrada")
            return
        
        try:
            # Abrir carpeta de gráficos
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(graphics_dir)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", graphics_dir])
            else:  # Linux
                subprocess.run(["xdg-open", graphics_dir])
                
            print(f"🖼️ Carpeta de gráficos abierta: {graphics_dir}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir la carpeta de gráficos: {e}")
    
    def set_theme(self, dark_theme):
        """Aplicar tema QSS a la ventana de gráficos"""
        try:
            # Determinar el archivo de tema
            if dark_theme:
                theme_file = os.path.join("resources", "styles", "dark_theme.qss")
            else:
                theme_file = os.path.join("resources", "styles", "light_theme.qss")
            
            # Leer el archivo de tema
            with open(theme_file, 'r', encoding='utf-8') as f:
                theme_content = f.read()
            
            # Aplicar el tema a la ventana
            self.setStyleSheet(theme_content)
            
            # Aplicar tema al panel de gráficos si existe
            if hasattr(self, 'charts_panel') and self.charts_panel:
                self.charts_panel.set_theme(dark_theme)
            
        except Exception as e:
            print(f"Error aplicando tema a ventana de gráficos: {e}")
    
    def export_additional_graphics(self):
        """Exportar gráficos adicionales o en diferentes formatos"""
        if not self.charts_panel or not self.session_directory:
            QMessageBox.warning(self, "Error", "No hay gráficos para exportar")
            return
        
        try:
            # Crear directorio adicional
            additional_dir = os.path.join(self.session_directory, "graficos_adicionales")
            os.makedirs(additional_dir, exist_ok=True)
            
            # Exportar en diferentes formatos
            success = self.charts_panel.export_charts(additional_dir)
            
            if success:
                QMessageBox.information(
                    self, 
                    "Éxito", 
                    f"Gráficos adicionales exportados en:\n{additional_dir}"
                )
                self.graphics_exported.emit(additional_dir)
            else:
                QMessageBox.warning(self, "Error", "No se pudieron exportar los gráficos adicionales")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error exportando gráficos: {e}")
    
    def closeEvent(self, event):
        """Evento al cerrar la ventana"""
        self.window_closed.emit()
        super().closeEvent(event)