"""
MainWindow (Ventana Principal)
Ventana principal del simulador de redes pasivas ópticas
"""

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QMenuBar, QAction, QActionGroup, QMessageBox)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QIcon, QKeySequence, QPixmap, QPainter
import os
from utils.constants import (
    APP_NAME, 
    DEFAULT_WINDOW_WIDTH, 
    DEFAULT_WINDOW_HEIGHT,
    APP_VERSION
)
from utils.resource_manager import resource_manager
from utils.config_manager import config_manager
from .canvas import Canvas
from .sidebar_panel import SidebarPanel

class MainWindow(QMainWindow):
    """Clase de la ventana principal para el simulador de redes pasivas ópticas"""
    
    def __init__(self):
        super().__init__()
        
        # Cargar configuraciones guardadas
        self.components_visible = config_manager.get_setting('components_visible', True)
        self.grid_visible = config_manager.get_setting('grid_visible', True)
        self.simulation_visible = config_manager.get_setting('simulation_visible', True)
        # El origen siempre sigue el estado de la cuadrícula
        self.origin_visible = self.grid_visible
        self.dark_theme = config_manager.get_theme_settings()
        
        # Componentes principales
        self.canvas = None
        
        # Inicializar ventana principal
        self.setup_ui()
        self.setup_menubar()
        self.setup_window_properties()
        
        # Restaurar configuraciones del canvas
        if self.canvas:
            config_manager.restore_canvas_settings(self.canvas)
            # Refrescar el layout para asegurar posicionamiento correcto
            self.canvas.refresh_layout()
        
        # Aplicar tema guardado
        self.set_theme(self.dark_theme)
    
    def setup_ui(self):
        """Configurar la interfaz de usuario principal"""
        # Crear widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Crear layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Crear el sidebar panel
        self.sidebar = SidebarPanel()
        self.sidebar.device_selected.connect(self.on_device_selected)
        self.sidebar.connection_mode_toggled.connect(self.on_connection_mode_toggled)
        
        # Agregar sidebar al layout si está visible
        if self.components_visible:
            main_layout.addWidget(self.sidebar)
        
        # Crear el canvas principal
        self.canvas = Canvas()
        self.canvas.device_dropped.connect(self.on_device_dropped)
        main_layout.addWidget(self.canvas)
        
        # Establecer referencia del canvas en el sidebar para simulación
        self.sidebar.set_canvas_reference(self.canvas)
        
        # El canvas ocupa el espacio restante
    
    def setup_menubar(self):
        """Configurar la barra de menú"""
        menubar = self.menuBar()
        
        # Menú Archivo
        self.setup_file_menu(menubar)
        
        # Menú Ver
        self.setup_view_menu(menubar)
        
        # Menú Opciones
        self.setup_options_menu(menubar)
    
    def setup_file_menu(self, menubar):
        """Configurar menú Archivo"""
        file_menu = menubar.addMenu('&Archivo')
        
        # Abrir archivo
        open_action = QAction('&Abrir archivo...', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip('Abrir un archivo de proyecto')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        # Guardar archivo
        save_action = QAction('&Guardar archivo...', self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.setStatusTip('Guardar el proyecto actual')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Cerrar
        close_action = QAction('&Cerrar', self)
        close_action.setShortcut(QKeySequence.Quit)
        close_action.setStatusTip('Cerrar la aplicación')
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
    
    def setup_view_menu(self, menubar):
        """Configurar menú Ver"""
        view_menu = menubar.addMenu('&Ver')
        
        # Mostrar/Ocultar Componentes
        self.components_action = QAction('Mostrar/Ocultar &Componentes', self)
        self.components_action.setCheckable(True)
        self.components_action.setChecked(self.components_visible)
        self.components_action.setShortcut('Ctrl+P')
        self.components_action.setStatusTip('Mostrar u ocultar panel de componentes (Ctrl+P)')
        self.components_action.triggered.connect(self.toggle_components)
        view_menu.addAction(self.components_action)
        
        # Mostrar/Ocultar Cuadrícula (incluye el origen)
        self.grid_action = QAction('Mostrar/Ocultar &Cuadrícula', self)
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(self.grid_visible)
        self.grid_action.setShortcut('Ctrl+G')
        self.grid_action.setStatusTip('Mostrar u ocultar la cuadrícula y el origen del canvas')
        self.grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(self.grid_action)
        
        # Mostrar/Ocultar Simulación
        self.simulation_action = QAction('Mostrar/Ocultar &Simulación', self)
        self.simulation_action.setCheckable(True)
        self.simulation_action.setChecked(self.simulation_visible)
        self.simulation_action.setStatusTip('Mostrar u ocultar panel de simulación')
        self.simulation_action.triggered.connect(self.toggle_simulation)
        view_menu.addAction(self.simulation_action)
        
        view_menu.addSeparator()
        
        # Opciones de Vista (con atajos)
        center_view_action = QAction('&Centrar Vista (C)', self)
        center_view_action.setStatusTip('Centrar la vista en el origen')
        center_view_action.triggered.connect(self.center_view)
        view_menu.addAction(center_view_action)
        
        zoom_reset_action = QAction('&Resetear Vista (R)', self)
        zoom_reset_action.setStatusTip('Resetear zoom y centrar en origen')
        zoom_reset_action.triggered.connect(self.reset_view)
        view_menu.addAction(zoom_reset_action)
    
    def setup_options_menu(self, menubar):
        """Configurar menú Opciones"""
        options_menu = menubar.addMenu('&Opciones')
        
        # Submenú Tema
        theme_menu = options_menu.addMenu('&Tema')
        
        # Grupo de acciones para temas (solo una puede estar seleccionada)
        theme_group = QActionGroup(self)
        
        # Tema Claro
        light_theme_action = QAction('Tema &Claro', self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(not self.dark_theme)
        light_theme_action.setStatusTip('Aplicar tema claro')
        light_theme_action.triggered.connect(lambda: self.set_theme(False))
        theme_group.addAction(light_theme_action)
        theme_menu.addAction(light_theme_action)
        
        # Tema Oscuro
        dark_theme_action = QAction('Tema &Oscuro', self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(self.dark_theme)
        dark_theme_action.setStatusTip('Aplicar tema oscuro')
        dark_theme_action.triggered.connect(lambda: self.set_theme(True))
        theme_group.addAction(dark_theme_action)
        theme_menu.addAction(dark_theme_action)
        
        options_menu.addSeparator()
        
        # Acerca de
        about_action = QAction('&Acerca de...', self)
        about_action.setStatusTip('Información acerca de la aplicación')
        about_action.triggered.connect(self.mostrar_acerca_de)
        options_menu.addAction(about_action)
    
    # Métodos de manejo de eventos del menú
    def open_file(self):
        """Abrir archivo de proyecto"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        # Verificar si hay trabajo sin guardar antes de abrir
        if self.canvas and self.canvas.has_unsaved_work():
            reply = QMessageBox.question(
                self,
                'Trabajo sin guardar',
                'Tienes trabajo sin guardar. ¿Quieres continuar?\nSe perderá el trabajo actual.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        # Mostrar diálogo de abrir archivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Abrir proyecto PON',
            '',  # Directorio inicial
            'Archivos PON (*.pon);;Todos los archivos (*.*)'
        )
        
        # Si el usuario canceló el diálogo
        if not file_path:
            return
        
        # Intentar cargar el proyecto
        if self.canvas and self.canvas.load_project_file(file_path):
            self.statusBar().showMessage(f'Proyecto cargado: {file_path}', 4000)
            print(f"📂 Proyecto cargado desde: {file_path}")
        else:
            QMessageBox.warning(
                self,
                'Error al abrir',
                f'No se pudo abrir el archivo:\n{file_path}\n\nVerifica que sea un archivo PON válido.',
                QMessageBox.Ok
            )
    
    def save_file(self):
        """Guardar archivo de proyecto"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        # Verificar si hay contenido que guardar
        if not self.canvas or not self.canvas.has_unsaved_work():
            QMessageBox.information(
                self,
                'Sin contenido',
                'No hay dispositivos o conexiones para guardar.',
                QMessageBox.Ok
            )
            return
        
        # Mostrar diálogo de guardar archivo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Guardar proyecto PON',
            'mi_topologia.pon',  # Nombre por defecto
            'Archivos PON (*.pon);;Todos los archivos (*.*)'
        )
        
        # Si el usuario canceló el diálogo
        if not file_path:
            return
        
        # Asegurar extensión .pon
        if not file_path.lower().endswith('.pon'):
            file_path += '.pon'
        
        # Intentar guardar
        if self.canvas.save_project_as(file_path):
            self.statusBar().showMessage(f'Proyecto guardado: {file_path}', 4000)
            print(f"💾 Proyecto guardado en: {file_path}")
        else:
            QMessageBox.warning(
                self,
                'Error al guardar',
                f'No se pudo guardar el proyecto en:\n{file_path}\n\nVerifica los permisos de escritura.',
                QMessageBox.Ok
            )
    
    def toggle_components(self):
        """Alternar visibilidad del panel de componentes"""
        self.components_visible = not self.components_visible
        
        # Mostrar/ocultar sidebar
        if self.components_visible:
            self.sidebar.show()
        else:
            self.sidebar.hide()
        
        # Actualizar estado del menú
        self.components_action.setChecked(self.components_visible)
        
        print(f"Componentes {'mostrados' if self.components_visible else 'ocultos'}")
    
    def on_device_selected(self, device_name, device_type):
        """Manejar selección de dispositivo del sidebar"""
        self.statusBar().showMessage(f'Dispositivo seleccionado: {device_name} ({device_type}) - Arrastra al canvas', 3000)
        print(f"Dispositivo para arrastrar: {device_name} - {device_type}")
    
    def on_device_dropped(self, device_name, device_type, x, y):
        """Manejar drop de dispositivo en el canvas"""
        self.statusBar().showMessage(f'Dispositivo {device_type} agregado en ({x:.1f}, {y:.1f})', 4000)
        print(f"✅ {device_type} agregado en canvas en posición ({x:.1f}, {y:.1f})")
        
        # Actualizar información si es necesario
        device_count = self.canvas.get_device_manager().get_device_count()
        print(f"📊 Total de dispositivos en canvas: {device_count}")
    
    def on_connection_mode_toggled(self, enabled):
        """Manejar cambio de modo conexión"""
        if self.canvas:
            self.canvas.set_connection_mode(enabled)
            
            # Actualizar status bar
            if enabled:
                self.statusBar().showMessage("🔗 Modo Conexión ACTIVO - Selecciona dos dispositivos para conectar", 0)
            else:
                self.statusBar().showMessage("🔗 Modo Conexión DESACTIVADO", 2000)
    
    def toggle_grid(self):
        """Alternar visibilidad de la cuadrícula y el origen"""
        # Actualizar canvas si existe
        if self.canvas:
            # El canvas maneja todo internamente
            self.canvas.toggle_grid_and_origin()
            # Sincronizar estado con el canvas
            self.grid_visible = self.canvas.grid_visible
            self.origin_visible = self.canvas.origin_visible
            # Ocultar vértices al alternar cuadrícula
            self.canvas.device_manager.deselect_all()
        
        grid_status = "mostrada" if self.grid_visible else "oculta"
        self.statusBar().showMessage(f'Cuadrícula y origen {grid_status}', 2000)
        print(f"Cuadrícula y origen {grid_status}")
    
    # Método toggle_origin ya no es necesario ya que el origen se controla con la cuadrícula
    
    def reset_view(self):
        """Resetear vista original"""
        if self.canvas:
            self.canvas.reset_view()
            # Ocultar vértices al resetear vista
            self.canvas.device_manager.deselect_all()
            self.statusBar().showMessage('Vista reseteada', 2000)
    
    def center_view(self):
        """Centrar vista en el origen"""
        if self.canvas:
            self.canvas.center_view()
            # Ocultar vértices al centrar vista
            self.canvas.device_manager.deselect_all()
            self.statusBar().showMessage('Vista centrada', 2000)
    
    def toggle_simulation(self):
        """Alternar visibilidad del panel de simulación"""
        self.simulation_visible = not self.simulation_visible
        print(f"Simulación {'mostrada' if self.simulation_visible else 'oculta'}")
        # TODO: Implementar lógica para mostrar/ocultar simulación
    
    def set_theme(self, dark_mode):
        """Establecer tema de la aplicación"""
        self.dark_theme = dark_mode
        theme_name = "oscuro" if dark_mode else "claro"
        
        # Guardar configuración del tema
        config_manager.save_theme_settings(dark_mode)
        
        # Determinar el archivo de estilo
        if dark_mode:
            style_file = os.path.join("resources", "styles", "dark_theme.qss")
        else:
            style_file = os.path.join("resources", "styles", "light_theme.qss")
        
        # Aplicar el estilo
        try:
            with open(style_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
            
            # Actualizar tema del canvas si existe
            if self.canvas:
                self.canvas.set_theme(dark_mode)
            
            # Actualizar tema del sidebar si existe
            if hasattr(self, 'sidebar') and self.sidebar:
                self.sidebar.set_theme(dark_mode)
            
            # Actualizar mensaje en la barra de estado
            self.statusBar().showMessage(f'Tema {theme_name} aplicado', 2000)
            
        except FileNotFoundError:
            print(f"Error: No se pudo encontrar el archivo de estilo {style_file}")
            self.statusBar().showMessage(f'Error: Archivo de tema {theme_name} no encontrado', 3000)
        except Exception as e:
            print(f"Error al aplicar tema {theme_name}: {str(e)}")
            self.statusBar().showMessage(f'Error al aplicar tema {theme_name}', 3000)
    
    def get_resource_path(self, relative_path):
        """Obtener la ruta absoluta de un recurso"""
        base_path = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_path, relative_path)
    
    def mostrar_acerca_de(self):
        """Mostrar información acerca de la aplicación"""
        # Crear un QMessageBox personalizado
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle('Acerca de')
        
        # Aplicar el mismo estilo que la ventana principal
        window_bg = self.palette().color(self.palette().Window).name()
        text_color = self.palette().color(self.palette().WindowText).name()
        
        msg_box.setStyleSheet(f"""
            QMessageBox {{
                background-color: {window_bg};
                color: {text_color};
            }}
            QMessageBox QLabel {{
                background-color: transparent;
                color: {text_color};
            }}
            QMessageBox QPushButton {{
                background-color: #2563eb;
                color: white;
                border: 1px solid #1e40af;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QMessageBox QPushButton:hover {{
                background-color: #3b82f6;
                border-color: #2563eb;
            }}
            QMessageBox QPushButton:pressed {{
                background-color: #1d4ed8;
                border-color: #1e3a8a;
            }}
        """)
        
        # Configurar el icono personalizado con fondo adecuado
        icon_path = self.get_resource_path('resources/icons/app_icon_64x64.png')
        if os.path.exists(icon_path):
            # Crear un pixmap con fondo que se adapte al tema
            original_pixmap = QPixmap(icon_path)
            
            # Crear un nuevo pixmap con fondo del tema
            themed_pixmap = QPixmap(64, 64)
            themed_pixmap.fill(self.palette().color(self.palette().Window))
            
            # Dibujar el icono original sobre el fondo temático
            from PyQt5.QtGui import QPainter
            painter = QPainter(themed_pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            
            # Centrar el icono original en el nuevo pixmap
            x = (themed_pixmap.width() - original_pixmap.width()) // 2
            y = (themed_pixmap.height() - original_pixmap.height()) // 2
            painter.drawPixmap(x, y, original_pixmap)
            painter.end()
            
            msg_box.setIconPixmap(themed_pixmap)
        else:
            msg_box.setIcon(QMessageBox.Information)
        
        # Configurar el texto
        msg_box.setText(
            '''<h3>Simulador de Redes Pasivas Ópticas</h3>
            <p>Versión 1.0</p>
            <p>Una aplicación para simular y diseñar redes pasivas ópticas (PON).</p>
            
            <p><b>Características:</b></p>
            <ul>
            <li>Diseño de topologías PON</li>
            <li>Simulación de redes pasivas ópticas</li>
            <li>Análisis de rendimiento de fibra óptica</li>
            </ul>
            
            <hr>
            
            <p><b>Elaborado por:</b></p>
            <ul>
            <li>Alex Aravena Tapia</li>
            <li>Jesús Chaffe González</li>
            <li>Eduardo Maldonado Zamora</li>
            <li>Jorge Barrios Núñez</li>
            </ul>
            
            <p><b>Repositorio GitHub:</b><br>
            <a href="https://github.com/alex-itico/PonLab">https://github.com/alex-itico/PonLab</a><br>
            <i>(Repositorio oficial - próximamente actualizado)</i></p>
            
            <p>© 2025 - Desarrollado con PyQt5</p>'''
        )
        
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    
    def setup_window_properties(self):
        """Configurar propiedades de la ventana"""
        # Establecer título de la ventana
        self.setWindowTitle(APP_NAME)
        
        # Establecer icono de la aplicación usando el gestor de recursos
        app_icon = resource_manager.get_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
        
        # Restaurar tamaño y posición de la ventana desde configuraciones
        config_manager.restore_window_state(self)
        
        # Establecer tamaño mínimo
        self.setMinimumSize(800, 600)
        
        # Agregar barra de estado
        self.statusBar().showMessage('Listo')
    
    def center_window(self):
        """Centrar la ventana en la pantalla"""
        # Obtener el rectángulo de la ventana
        frame_geometry = self.frameGeometry()
        
        # Obtener el centro de la pantalla disponible
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        center_point = screen.center()
        
        # Mover el rectángulo al centro de la pantalla
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())
    
    def closeEvent(self, event):
        """Manejar el evento de cierre de la ventana"""
        # Verificar si hay trabajo sin guardar
        if self.canvas and self.canvas.has_unsaved_work():
            # Mostrar diálogo de confirmación
            reply = self.show_close_confirmation_dialog()
            
            if reply != QMessageBox.Yes:
                event.ignore()  # Cancelar cierre
                return
        
        # Guardar estado de la ventana
        config_manager.save_window_state(self)
        
        # Guardar configuraciones del canvas
        if self.canvas:
            config_manager.save_canvas_settings(self.canvas)
        
        # Guardar configuraciones de la UI
        config_manager.save_ui_settings(self)
        
        # Permitir el cierre de la ventana
        event.accept()
    
    def show_close_confirmation_dialog(self):
        """Mostrar diálogo de confirmación de cierre"""
        from PyQt5.QtWidgets import QMessageBox
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle('Confirmar cierre')
        msg_box.setText('Tienes trabajo sin guardar en el canvas.')
        msg_box.setInformativeText('¿Estás seguro de que quieres cerrar el programa?')
        msg_box.setDetailedText('Se perderán todos los dispositivos y conexiones creadas.')
        
        # Botones personalizados
        yes_button = msg_box.addButton('Sí, cerrar', QMessageBox.YesRole)
        no_button = msg_box.addButton('Cancelar', QMessageBox.NoRole)
        save_button = msg_box.addButton('Guardar', QMessageBox.AcceptRole)
        
        msg_box.setDefaultButton(no_button)
        
        msg_box.exec_()
        
        if msg_box.clickedButton() == yes_button:
            return QMessageBox.Yes
        elif msg_box.clickedButton() == save_button:
            # Implementar guardado rápido
            return self.save_and_close()
        else:
            return QMessageBox.No
    
    def save_and_close(self):
        """Guardar proyecto rápidamente y cerrar"""
        from PyQt5.QtWidgets import QFileDialog
        
        # Mostrar diálogo de guardar archivo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Guardar proyecto PON',
            'mi_topologia.pon',  # Nombre por defecto
            'Archivos PON (*.pon);;Todos los archivos (*.*)'
        )
        
        # Si el usuario canceló el diálogo
        if not file_path:
            return QMessageBox.No  # No cerrar
        
        # Asegurar extensión .pon
        if not file_path.lower().endswith('.pon'):
            file_path += '.pon'
        
        # Intentar guardar
        if self.canvas and self.canvas.save_project_as(file_path):
            self.statusBar().showMessage(f'Proyecto guardado: {file_path}', 3000)
            print(f"💾 Proyecto guardado en: {file_path}")
            return QMessageBox.Yes  # Proceder con el cierre
        else:
            # Si falla el guardado, preguntar qué hacer
            reply = QMessageBox.question(
                self, 
                'Error al guardar', 
                f'No se pudo guardar el proyecto en:\n{file_path}\n\n¿Quieres cerrar sin guardar?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return reply
