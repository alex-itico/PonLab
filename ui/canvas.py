"""
Canvas (QGraphicsScene)
Canvas principal para diseñar la topología de red óptica
Cuadrícula infinita centrada con origen visual y información del mouse
"""

from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QWidget, 
                             QGraphicsEllipseItem, QGraphicsLineItem, 
                             QGraphicsTextItem, QGraphicsRectItem, QLabel,
                             QGraphicsItem, QMenu, QAction, QActionGroup, QShortcut)
from PyQt5.QtCore import Qt, QRectF, QPoint, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QCursor, QFont, QKeySequence
from utils.constants import DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT
from utils.project_manager import ProjectManager
from core import DeviceManager

class Canvas(QGraphicsView):
    """Clase de canvas con cuadrícula infinita centrada"""
    
    # Señales
    device_dropped = pyqtSignal(str, str, float, float)  # device_name, device_type, x, y
    device_selected = pyqtSignal(object)  # device object para mostrar propiedades
    device_deselected = pyqtSignal()  # cuando no hay dispositivo seleccionado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Variables de estado
        self.grid_visible = True
        self.origin_visible = True
        self.grid_size = 20  # Tamaño por defecto
        self.zoom_factor = 1.0
        self.dark_theme = False
        
        # Variables para pan con botón central
        self.pan_active = False
        self.last_pan_point = None
        self.last_context_pos = QPoint(0, 0)  # Para el menú contextual
        
        # Variables de visibilidad
        self.info_panel_visible = True
        
        # Variables para modo conexión
        self.connection_mode = False
        self.connection_source_device = None  # Primer dispositivo seleccionado para conexión
        self.original_cursor = self.cursor()
        
        # Configurar la escena
        scene_size = 10000  # Escena muy grande para simular infinito
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-scene_size/2, -scene_size/2, scene_size, scene_size)
        self.setScene(self.scene)
        
        # Inicializar gestor de dispositivos
        # Crear gestores principales
        self.device_manager = DeviceManager(self.scene)
        self.device_manager.set_canvas_reference(self)  # Pasar referencia al canvas
        
        # Inicializar gestor de conexiones
        from core.connection_manager import ConnectionManager
        self.connection_manager = ConnectionManager(self)
        
        # Inicializar gestor de proyectos con auto-save
        self.project_manager = ProjectManager()
        self.setup_project_manager()
        
        # Conectar señal para actualizar info panel
        self.device_manager.devices_changed.connect(self.update_device_info)
        
        # Conectar señal para actualizar posiciones de conexiones
        self.device_manager.devices_changed.connect(self.connection_manager.update_connections_positions)
        
        # Habilitar drag and drop
        self.setAcceptDrops(True)
        
        # Configurar canvas
        self.setup_canvas()
        self.setup_grid()
        self.setup_origin()
        
        # Centrar en el origen
        self.centerOn(0, 0)
        
        # Crear info panel
        self.setup_info_panel()
        
        # Configurar shortcuts globales
        self.setup_shortcuts()
    
    def setup_canvas(self):
        """Configurar propiedades básicas del canvas"""
        # Configurar renderizado balanceado (compromiso calidad-rendimiento)
        self.setup_rendering_quality()
        
        # Optimizaciones de caché y viewport
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        
        # Sin scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Configuración de transformación
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Modo de arrastre
        self.setDragMode(QGraphicsView.NoDrag)
    
    def setup_rendering_quality(self):
        """Configurar calidad de renderizado balanceada (compromiso calidad-rendimiento)"""
        # Balance entre calidad y rendimiento
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setRenderHint(QPainter.TextAntialiasing, True)
        self.setRenderHint(QPainter.SmoothPixmapTransform, False)  # Desactivado para mejor rendimiento
        # Solo algunas optimizaciones
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)
        self.setOptimizationFlag(QGraphicsView.DontSavePainterState, True)
        self.grid_quality = "medium"
        
        # Color de fondo
        self.update_background_color()
        
        # Cursor por defecto
        self.setCursor(QCursor(Qt.CrossCursor))
        
        # Configurar foco para recibir eventos de teclado
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Habilitar tracking del mouse para info panel
        self.setMouseTracking(True)
    
    def setup_info_panel(self):
        """Configurar panel de información en esquina inferior derecha"""
        self.info_label = QLabel(self)
        
        # Determinar colores según tema
        if hasattr(self, 'dark_theme') and self.dark_theme:
            bg_color = "rgba(40, 40, 40, 220)"
            text_color = "#FFFFFF"
            border_color = "#666666"
        else:
            bg_color = "rgba(255, 255, 255, 240)"
            text_color = "#2c2c2c"
            border_color = "#cccccc"
        
        self.info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 12px 16px;
                border: 2px solid {border_color};
                border-radius: 0px;
                font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif;
                font-size: 12px;
                font-weight: 500;
                line-height: 1.4;
            }}
        """)
        self.info_label.setAlignment(Qt.AlignLeft)
        self.update_info_panel(0, 0)
        self.position_info_panel()
        
        # Aplicar visibilidad inicial
        if self.info_panel_visible:
            self.info_label.show()
        else:
            self.info_label.hide()
    
    def setup_shortcuts(self):
        """Configurar shortcuts globales para el canvas"""
        # Shortcut para toggle del panel de información
        self.info_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        self.info_shortcut.activated.connect(self.toggle_info_panel)
        
        # Shortcut para centrar vista
        self.center_shortcut = QShortcut(QKeySequence("C"), self)
        self.center_shortcut.activated.connect(self.center_view)
        
        # Shortcut para reset vista
        self.reset_shortcut = QShortcut(QKeySequence("R"), self)
        self.reset_shortcut.activated.connect(self.reset_view)
        
        # Shortcuts para redimensionar dispositivos
        self.increase_size_shortcut = QShortcut(QKeySequence("+"), self)
        self.increase_size_shortcut.activated.connect(self.increase_selected_device_size)
        
        self.increase_size_shortcut2 = QShortcut(QKeySequence("="), self)
        self.increase_size_shortcut2.activated.connect(self.increase_selected_device_size)
        
        self.decrease_size_shortcut = QShortcut(QKeySequence("-"), self)
        self.decrease_size_shortcut.activated.connect(self.decrease_selected_device_size)
        
        # Shortcut para toggle modo conexión
        self.connection_shortcut = QShortcut(QKeySequence("L"), self)
        self.connection_shortcut.activated.connect(self.toggle_connection_mode_shortcut)
        
    
    def position_info_panel(self):
        """Posicionar el panel de información en la esquina inferior derecha"""
        if not self.info_panel_visible or not hasattr(self, 'info_label'):
            return
            
        # Asegurarse de que el label tenga el tamaño correcto
        self.info_label.adjustSize()
        
        # Posicionar en esquina inferior derecha con margen
        margin = 10
        new_x = self.width() - self.info_label.width() - margin
        new_y = self.height() - self.info_label.height() - margin
        
        self.info_label.move(new_x, new_y)
        
        # Asegurar que esté visible si debe estarlo
        if self.info_panel_visible:
            self.info_label.show()
            self.info_label.raise_()  # Traer al frente
    
    def update_info_panel(self, scene_x, scene_y):
        """Actualizar información del panel"""
        if not self.info_panel_visible:
            return
            
        # Calcular coordenadas de cuadrícula (relativas al origen)
        grid_x = int(scene_x / self.grid_size)
        grid_y = int(-scene_y / self.grid_size)  # Y invertido para coordenadas más naturales
        
        # Coordenadas del mundo (escena)
        world_x = int(scene_x)
        world_y = int(scene_y)
        
        # Obtener estadísticas de dispositivos
        device_stats = self.device_manager.get_device_stats()
        
        info_text = f"""Mouse - Cuadrícula: ({grid_x},{grid_y})
Mouse - Mundo: ({world_x},{world_y})
Zoom: {self.zoom_factor:.1f}x
Tamaño de cuadrícula: {self.grid_size}px

📦 Total de dispositivos: {device_stats['total_devices']}"""
        
        self.info_label.setText(info_text)
    
    def update_device_info(self):
        """Actualizar información de dispositivos en el panel (callback)"""
        # Obtener posición actual del mouse si está disponible
        if hasattr(self, 'last_mouse_scene_pos'):
            scene_pos = self.last_mouse_scene_pos
        else:
            scene_pos = self.mapToScene(self.mapFromGlobal(self.cursor().pos()))
        
        self.update_info_panel(scene_pos.x(), scene_pos.y())
    
    def update_background_color(self):
        """Actualizar color de fondo según el tema"""
        if self.dark_theme:
            self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        else:
            self.setBackgroundBrush(QBrush(QColor(250, 250, 250)))
    
    def setup_grid(self):
        """Configurar y dibujar la cuadrícula infinita"""
        if not self.grid_visible:
            return
        
        self.clear_grid()
        
        # Colores según tema
        if self.dark_theme:
            grid_color = QColor(60, 60, 60)
            major_grid_color = QColor(80, 80, 80)
        else:
            grid_color = QColor(220, 220, 220)
            major_grid_color = QColor(180, 180, 180)
        
        # Obtener área visible con configuración balanceada
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        
        # Configuración balanceada
        margin = self.grid_size * 5  # Balance
        max_lines = 200  # Balance
        start_x = int(visible_rect.left() - margin)
        end_x = int(visible_rect.right() + margin)
        start_y = int(visible_rect.top() - margin)
        end_y = int(visible_rect.bottom() + margin)
        
        # Alinear al grid
        start_x = start_x - (start_x % self.grid_size)
        start_y = start_y - (start_y % self.grid_size)
        
        # Optimización: limitar número máximo de líneas
        x_step = max(self.grid_size, (end_x - start_x) // max_lines)
        y_step = max(self.grid_size, (end_y - start_y) // max_lines)
        
        # Dibujar líneas verticales (optimizado)
        x = start_x
        line_count = 0
        while x <= end_x and line_count < max_lines:
            # Línea mayor cada 5 líneas
            is_major = (x % (self.grid_size * 5) == 0)
            color = major_grid_color if is_major else grid_color
            width = 1 if not is_major else 1
            
            # Crear línea sin borde (solo con el color de línea)
            pen = QPen(color, width)
            pen.setStyle(Qt.SolidLine)
            line = self.scene.addLine(x, start_y, x, end_y, pen)
            line.setZValue(-10)  # Muy al fondo
            x += x_step  # Usar step optimizado
            line_count += 1
        
        # Dibujar líneas horizontales (optimizado)
        y = start_y
        line_count = 0
        while y <= end_y and line_count < max_lines:
            # Línea mayor cada 5 líneas
            is_major = (y % (self.grid_size * 5) == 0)
            color = major_grid_color if is_major else grid_color
            width = 1 if not is_major else 1
            
            # Crear línea sin borde (solo con el color de línea)
            pen = QPen(color, width)
            pen.setStyle(Qt.SolidLine)
            line = self.scene.addLine(start_x, y, end_x, y, pen)
            line.setZValue(-10)  # Muy al fondo
            y += y_step  # Usar step optimizado
            line_count += 1
    
    def clear_grid(self):
        """Limpiar cuadrícula existente"""
        for item in self.scene.items():
            if hasattr(item, 'zValue') and item.zValue() == -10:
                self.scene.removeItem(item)
    
    def setup_origin(self):
        """Configurar origen en el centro (0,0)"""
        if not self.origin_visible:
            return
        
        self.clear_origin()
        
        # Colores según el tema
        origin_red = QColor(220, 50, 50)
        # Las flechas cambian de color según el tema
        axis_color = QColor(50, 50, 50) if not self.dark_theme else QColor(220, 220, 220)
        text_color = QColor(100, 100, 100) if not self.dark_theme else QColor(200, 200, 200)
        
        # 1. Línea eje X completa (de -30 a +30) - FONDO
        arrow_length = 30
        x_line = QGraphicsLineItem(-arrow_length, 0, arrow_length, 0)
        x_line.setPen(QPen(axis_color, 2))
        x_line.setZValue(-5)  # Detrás del cuadrado y círculo
        x_line.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(x_line)
        
        # Punta de flecha X positiva
        arrow_size = 4
        x_arrow1_pos = QGraphicsLineItem(arrow_length, 0, arrow_length-arrow_size, -arrow_size/2)
        x_arrow1_pos.setPen(QPen(axis_color, 2))
        x_arrow1_pos.setZValue(-5)
        x_arrow1_pos.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(x_arrow1_pos)
        
        x_arrow2_pos = QGraphicsLineItem(arrow_length, 0, arrow_length-arrow_size, arrow_size/2)
        x_arrow2_pos.setPen(QPen(axis_color, 2))
        x_arrow2_pos.setZValue(-5)
        x_arrow2_pos.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(x_arrow2_pos)
        
        # Punta de flecha X negativa
        x_arrow1_neg = QGraphicsLineItem(-arrow_length, 0, -arrow_length+arrow_size, -arrow_size/2)
        x_arrow1_neg.setPen(QPen(axis_color, 2))
        x_arrow1_neg.setZValue(-5)
        x_arrow1_neg.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(x_arrow1_neg)
        
        x_arrow2_neg = QGraphicsLineItem(-arrow_length, 0, -arrow_length+arrow_size, arrow_size/2)
        x_arrow2_neg.setPen(QPen(axis_color, 2))
        x_arrow2_neg.setZValue(-5)
        x_arrow2_neg.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(x_arrow2_neg)
        
        # 2. Línea eje Y completa (de -30 a +30) - FONDO
        y_line = QGraphicsLineItem(0, -arrow_length, 0, arrow_length)
        y_line.setPen(QPen(axis_color, 2))
        y_line.setZValue(-5)  # Detrás del cuadrado y círculo
        y_line.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(y_line)
        
        # Punta de flecha Y positiva (hacia arriba)
        y_arrow1_pos = QGraphicsLineItem(0, -arrow_length, -arrow_size/2, -arrow_length+arrow_size)
        y_arrow1_pos.setPen(QPen(axis_color, 2))
        y_arrow1_pos.setZValue(-5)
        y_arrow1_pos.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(y_arrow1_pos)
        
        y_arrow2_pos = QGraphicsLineItem(0, -arrow_length, arrow_size/2, -arrow_length+arrow_size)
        y_arrow2_pos.setPen(QPen(axis_color, 2))
        y_arrow2_pos.setZValue(-5)
        y_arrow2_pos.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(y_arrow2_pos)
        
        # Punta de flecha Y negativa (hacia abajo)
        y_arrow1_neg = QGraphicsLineItem(0, arrow_length, -arrow_size/2, arrow_length-arrow_size)
        y_arrow1_neg.setPen(QPen(axis_color, 2))
        y_arrow1_neg.setZValue(-5)
        y_arrow1_neg.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(y_arrow1_neg)
        
        y_arrow2_neg = QGraphicsLineItem(0, arrow_length, arrow_size/2, arrow_length-arrow_size)
        y_arrow2_neg.setPen(QPen(axis_color, 2))
        y_arrow2_neg.setZValue(-5)
        y_arrow2_neg.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(y_arrow2_neg)
        
        # 3. Cuadrado central rojo más pequeño - ADELANTE
        square_size = 4
        origin_square = QGraphicsRectItem(-square_size/2, -square_size/2, 
                                         square_size, square_size)
        origin_square.setPen(QPen(origin_red, 1))
        origin_square.setBrush(QBrush(origin_red))
        origin_square.setZValue(1)  # Adelante de las flechas
        origin_square.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(origin_square)
        
        # 4. Circunferencia roja alrededor - ADELANTE
        circle_radius = 8
        origin_circle = QGraphicsEllipseItem(-circle_radius, -circle_radius,
                                           circle_radius * 2, circle_radius * 2)
        origin_circle.setPen(QPen(origin_red, 1))
        origin_circle.setBrush(QBrush(Qt.transparent))
        origin_circle.setZValue(1)  # Adelante de las flechas
        origin_circle.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(origin_circle)
        
        # 5. Etiqueta (0,0) - mantener solo esta en la escena
        origin_label = QGraphicsTextItem("(0,0)")
        font = QFont("Arial", 8)
        origin_label.setFont(font)
        origin_label.setDefaultTextColor(text_color)
        # Posición fija relativa al origen
        origin_label.setPos(10, 5)
        origin_label.setZValue(2)  # Muy adelante
        origin_label.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.scene.addItem(origin_label)
        
        # 6. Crear etiquetas X e Y como widgets overlay (no en la escena)
        self.setup_axis_labels()
    
    def setup_axis_labels(self):
        """Configurar etiquetas de ejes como overlays fijos"""
        # Limpiar etiquetas anteriores si existen
        if hasattr(self, 'x_label_widget'):
            self.x_label_widget.setParent(None)
        if hasattr(self, 'y_label_widget'):
            self.y_label_widget.setParent(None)
        
        # Colores según tema
        axis_color = "#323232" if not self.dark_theme else "#DDDDDD"
        
        # Etiqueta X
        self.x_label_widget = QLabel("X", self)
        self.x_label_widget.setStyleSheet(f"""
            QLabel {{
                color: {axis_color};
                font-family: Arial;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)
        self.x_label_widget.setAlignment(Qt.AlignCenter)
        
        # Etiqueta Y
        self.y_label_widget = QLabel("Y", self)
        self.y_label_widget.setStyleSheet(f"""
            QLabel {{
                color: {axis_color};
                font-family: Arial;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)
        self.y_label_widget.setAlignment(Qt.AlignCenter)
        
        # Posicionar las etiquetas
        self.update_axis_labels_position()
        
        # Mostrar las etiquetas
        if self.origin_visible:
            self.x_label_widget.show()
            self.y_label_widget.show()
        else:
            self.x_label_widget.hide()
            self.y_label_widget.hide()
    
    def update_axis_labels_position(self):
        """Actualizar posición de las etiquetas de ejes"""
        if not hasattr(self, 'x_label_widget') or not hasattr(self, 'y_label_widget'):
            return
            
        # Obtener posición del origen en coordenadas de vista
        origin_scene = QPoint(0, 0)  # Origen en coordenadas de escena
        origin_view = self.mapFromScene(origin_scene)
        
        # Ajustar tamaño de las etiquetas
        self.x_label_widget.adjustSize()
        self.y_label_widget.adjustSize()
        
        # Posiciones fijas respecto al origen visual
        offset_x = 40  # Distancia del origen
        offset_y = 40
        
        # Posicionar etiqueta X (a la derecha del origen)
        x_pos = origin_view.x() + offset_x
        y_pos = origin_view.y() - self.x_label_widget.height() // 2
        self.x_label_widget.move(x_pos, y_pos)
        
        # Posicionar etiqueta Y (arriba del origen)  
        x_pos = origin_view.x() - self.y_label_widget.width() // 2
        y_pos = origin_view.y() - offset_y - self.y_label_widget.height()
        self.y_label_widget.move(x_pos, y_pos)
    
    def clear_origin(self):
        """Limpiar origen existente"""
        for item in self.scene.items():
            if hasattr(item, 'zValue'):
                z_val = item.zValue()
                # Limpiar elementos del origen (z-values -5, 1, y 2)
                if z_val == -5 or z_val == 1 or z_val == 2:
                    self.scene.removeItem(item)
        
        # Ocultar etiquetas overlay
        if hasattr(self, 'x_label_widget'):
            self.x_label_widget.hide()
        if hasattr(self, 'y_label_widget'):
            self.y_label_widget.hide()
    
    def create_context_menu(self, pos):
        """Crear menú contextual para el canvas"""
        context_menu = QMenu(self)
        
        # Obtener coordenadas del click
        scene_pos = self.mapToScene(pos)
        grid_x = int(scene_pos.x() / self.grid_size)
        grid_y = int(-scene_pos.y() / self.grid_size)
        world_x = int(scene_pos.x())
        world_y = int(scene_pos.y())
        
        # NAVEGACIÓN
        nav_label = QAction("🧭 Navegación:", self)
        nav_label.setEnabled(False)
        context_menu.addAction(nav_label)
        
        center_action = QAction("🎯 Centrar en Origen (C)", self)
        center_action.triggered.connect(self.center_view)
        context_menu.addAction(center_action)
        
        reset_action = QAction("🔄 Resetear Vista (R)", self)
        reset_action.triggered.connect(self.reset_view)
        context_menu.addAction(reset_action)
        
        context_menu.addSeparator()
        
        # CUADRÍCULA
        grid_label = QAction("📐 Cuadrícula:", self)
        grid_label.setEnabled(False)
        context_menu.addAction(grid_label)
        
        grid_text = f"{'🚫 Ocultar' if self.grid_visible else '👁️ Mostrar'} Cuadrícula (Ctrl+G)"
        grid_toggle_action = QAction(grid_text, self)
        # Usar el mismo método que el menubar para consistencia total
        grid_toggle_action.triggered.connect(self.toggle_grid)
        context_menu.addAction(grid_toggle_action)
        
        info_text = f"{'🚫 Ocultar' if self.info_panel_visible else '👁️ Mostrar'} Info Panel (Ctrl+I)"
        info_toggle_action = QAction(info_text, self)
        info_toggle_action.triggered.connect(self.toggle_info_panel)
        context_menu.addAction(info_toggle_action)
        
        # Submenu Tamaño de Cuadrícula
        grid_size_menu = context_menu.addMenu("📏 Tamaño Cuadrícula")
        grid_sizes = [1, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
        
        size_group = QActionGroup(self)
        for size in grid_sizes:
            size_action = QAction(f"{size}px", self)
            size_action.setCheckable(True)
            size_action.setChecked(self.grid_size == size)
            size_action.triggered.connect(lambda checked, s=size: self.set_grid_size(s))
            size_group.addAction(size_action)
            grid_size_menu.addAction(size_action)
        
        context_menu.addSeparator()
        
        # ZOOM
        zoom_label = QAction("🔍 Zoom:", self)
        zoom_label.setEnabled(False)
        context_menu.addAction(zoom_label)
        
        # Submenu Nivel de Zoom
        zoom_menu = context_menu.addMenu("🔎 Nivel de Zoom")
        zoom_levels = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
        
        zoom_group = QActionGroup(self)
        for zoom in zoom_levels:
            zoom_text = f"{zoom}x"
            if zoom == 1.0:
                zoom_text = "1x (Normal)"
            zoom_action = QAction(zoom_text, self)
            zoom_action.setCheckable(True)
            zoom_action.setChecked(abs(self.zoom_factor - zoom) < 0.1)
            zoom_action.triggered.connect(lambda checked, z=zoom: self.set_zoom_level(z))
            zoom_group.addAction(zoom_action)
            zoom_menu.addAction(zoom_action)
        
        context_menu.addSeparator()
        
        # INFORMACIÓN
        info_label = QAction("ℹ️ Información:", self)
        info_label.setEnabled(False)
        context_menu.addAction(info_label)
        
        grid_info = QAction(f"📍 Cuadrícula: ({grid_x}, {grid_y})", self)
        grid_info.setEnabled(False)
        context_menu.addAction(grid_info)
        
        world_info = QAction(f"🌍 Mundo: ({world_x}, {world_y})", self)
        world_info.setEnabled(False)
        context_menu.addAction(world_info)
        
        return context_menu
    
    def toggle_info_panel(self):
        """Alternar visibilidad del panel de información"""
        try:
            if not hasattr(self, 'info_label'):
                print("AVISO: info_label no existe")
                return
            
            self.info_panel_visible = not self.info_panel_visible
            
            if self.info_panel_visible:
                self.position_info_panel()
                self.info_label.show()
                self.info_label.raise_()
                print("Panel de informacion mostrado (QShortcut)")
            else:
                self.info_label.hide()
                print("Panel de informacion ocultado (QShortcut)")
                
        except Exception as e:
            print(f"ERROR en toggle_info_panel: {e}")
            import traceback
            traceback.print_exc()
    
    def set_grid_size(self, size):
        """Establecer tamaño de cuadrícula"""
        self.grid_size = size
        self.setup_grid()  # Redibujar cuadrícula con nuevo tamaño
    
    def set_zoom_level(self, zoom_level):
        """Establecer nivel de zoom específico"""
        # Calcular el factor necesario para llegar al zoom deseado
        scale_factor = zoom_level / self.zoom_factor
        self.zoom_factor = zoom_level
        
        # Aplicar transformación
        self.scale(scale_factor, scale_factor)
        
        # Actualizar elementos
        self.setup_grid()
        self.update_axis_labels_position()
        
        # Actualizar info panel
        scene_pos = self.mapToScene(self.last_context_pos)
        self.update_info_panel(scene_pos.x(), scene_pos.y())
    
    def set_theme(self, dark_theme):
        """Cambiar tema"""
        self.dark_theme = dark_theme
        self.update_background_color()
        if self.grid_visible:
            self.setup_grid()
        if self.origin_visible:
            self.setup_origin()
        
        # Actualizar colores de etiquetas de dispositivos
        self.device_manager.update_label_colors(dark_theme)
        
        # Actualizar colores de conexiones
        self.connection_manager.update_theme_colors(dark_theme)
        
        # Actualizar etiquetas de ejes
        if hasattr(self, 'x_label_widget'):
            self.setup_axis_labels()
        
        # Actualizar estilo del info panel con nuevo diseño
        if dark_theme:
            bg_color = "rgba(40, 40, 40, 220)"
            text_color = "#FFFFFF"
            border_color = "#666666"
        else:
            bg_color = "rgba(255, 255, 255, 240)"
            text_color = "#2c2c2c"
            border_color = "#cccccc"
            
        self.info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                padding: 12px 16px;
                border: 2px solid {border_color};
                border-radius: 0px;
                font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif;
                font-size: 12px;
                font-weight: 500;
                line-height: 1.4;
            }}
        """)
        
    def set_connection_mode(self, enabled):
        """Activar/desactivar modo conexión"""
        self.connection_mode = enabled
        self.connection_source_device = None  # Reset source
        
        if enabled:
            # Cambiar cursor a modo conexión
            self.setCursor(Qt.CrossCursor)
        else:
            # Restaurar cursor normal
            self.setCursor(self.original_cursor)
    
    def is_connection_mode_active(self):
        """Verificar si el modo conexión está activo"""
        return self.connection_mode
    
    def handle_device_click_for_connection(self, device):
        """Manejar click en dispositivo cuando está activo el modo conexión"""
        if not self.connection_mode:
            return False  # No estamos en modo conexión
            
        if self.connection_source_device is None:
            # Primer dispositivo seleccionado
            self.connection_source_device = device
            print(f"Conexion:")
            return True
        else:
            # Segundo dispositivo seleccionado - intentar crear conexión
            target_device = device
            source_device = self.connection_source_device
            
            # Reset source device
            self.connection_source_device = None
            
            # Intentar crear la conexión
            connection = self.connection_manager.create_connection(source_device, target_device)
            
            if connection:
                print(f"🔗 Conexión creada: {source_device.name} ↔ {target_device.name}")
            
            return True
    
    def toggle_connection_mode_shortcut(self):
        """Toggle del modo conexión via shortcut (tecla L)"""
        new_mode = not self.connection_mode
        self.set_connection_mode(new_mode)
        
        # Notificar al sidebar para actualizar estado visual
        try:
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'sidebar'):
                main_window = main_window.parent()
            
            if main_window and hasattr(main_window, 'sidebar'):
                sidebar = main_window.sidebar
                if hasattr(sidebar, 'connection_item') and sidebar.connection_item:
                    sidebar.connection_item.set_connection_mode(new_mode)
                    
        except Exception as e:
            print(f"Error en shortcut conexión: {e}")
    
    def notify_sidebar_connection_mode_change(self):
        """Notificar al sidebar que el modo conexión cambió desde el canvas"""
        try:
            # Buscar la ventana principal para acceder al sidebar
            main_window = self.parent()
            while main_window and not hasattr(main_window, 'sidebar'):
                main_window = main_window.parent()
            
            if main_window and hasattr(main_window, 'sidebar'):
                sidebar = main_window.sidebar
                if hasattr(sidebar, 'connection_item') and sidebar.connection_item:
                    sidebar.connection_item.set_connection_mode(False)
        except Exception as e:
            print(f"Error notificando al sidebar: {e}")

    def mousePressEvent(self, event):
        """Manejar clic del mouse"""
        # Asegurar que el canvas tome el foco para recibir eventos de teclado
        self.setFocus()
        
        if event.button() == Qt.MiddleButton:
            self.pan_active = True
            self.last_pan_point = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            event.accept()
        elif event.button() == Qt.RightButton:
            # Click derecho - mostrar menú contextual
            self.last_context_pos = event.pos()
            context_menu = self.create_context_menu(event.pos())
            context_menu.exec_(self.mapToGlobal(event.pos()))
            # Ocultar vértices al usar menú contextual
            self.device_manager.deselect_all()
            event.accept()
        elif event.button() == Qt.LeftButton:
            # Click izquierdo - detectar selección de dispositivo
            scene_pos = self.mapToScene(event.pos())
            device = self.device_manager.get_device_at_position(scene_pos.x(), scene_pos.y())
            
            if device:
                # Dispositivo encontrado - emitir señal de selección
                self.device_selected.emit(device)
            else:
                # Click en área vacía - deseleccionar
                self.device_deselected.emit()
            
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Manejar movimiento del mouse"""
        # Actualizar info panel con posición del mouse (throttled)
        scene_pos = self.mapToScene(event.pos())
        self.last_mouse_scene_pos = scene_pos  # Guardar para update_device_info
        
        # Solo actualizar info panel cada 10ms para evitar updates excesivos
        if not hasattr(self, '_last_info_update') or (
            hasattr(self, '_last_info_update') and 
            (event.timestamp() - self._last_info_update) > 10
        ):
            self.update_info_panel(scene_pos.x(), scene_pos.y())
            self._last_info_update = event.timestamp()
        
        if self.pan_active and self.last_pan_point:
            # Pan con botón central
            delta = event.pos() - self.last_pan_point
            self.last_pan_point = event.pos()
            
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            
            # Actualizar posición de etiquetas al hacer pan (throttled)
            if not hasattr(self, '_last_axis_update') or (
                hasattr(self, '_last_axis_update') and 
                (event.timestamp() - self._last_axis_update) > 50
            ):
                self.update_axis_labels_position()
                self._last_axis_update = event.timestamp()
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Manejar liberación del mouse"""
        if event.button() == Qt.MiddleButton and self.pan_active:
            self.pan_active = False
            self.last_pan_point = None
            self.setCursor(QCursor(Qt.CrossCursor))
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Manejar doble clic del mouse - abrir propiedades de dispositivo"""
        if event.button() == Qt.LeftButton:
            # Convertir posición a coordenadas de escena
            scene_pos = self.mapToScene(event.pos())
            
            # Buscar dispositivo en la posición del doble clic
            device = self.device_manager.get_device_at_position(scene_pos.x(), scene_pos.y())
            
            if device:
                # Abrir diálogo de propiedades
                self.open_device_properties(device)
                event.accept()
                return
        
        # Si no se hizo clic sobre un dispositivo, manejar normalmente
        super().mouseDoubleClickEvent(event)
    
    def open_device_properties(self, device):
        """Abrir ventana de propiedades para un dispositivo"""
        try:
            from .device_properties_dialog import DevicePropertiesDialog
            
            # Crear diálogo de propiedades
            dialog = DevicePropertiesDialog(device, self.connection_manager, self)
            
            # Conectar señal para actualizar propiedades
            dialog.properties_updated.connect(self.update_device_properties)
            
            # Mostrar diálogo modal
            dialog.exec_()
            
        except Exception as e:
            print(f"❌ Error abriendo propiedades del dispositivo: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", 
                              f"No se pudo abrir la ventana de propiedades:\n{str(e)}")
    
    def update_device_properties(self, device_id, new_properties):
        """Actualizar propiedades de un dispositivo"""
        try:
            # Actualizar dispositivo a través del DeviceManager
            if self.device_manager.update_device_properties(device_id, new_properties):
                print(f"✅ Propiedades actualizadas para dispositivo {device_id}")
                
                # Refrescar canvas para mostrar cambios
                self.update()
                
                # Actualizar auto-guardado
                self.auto_save_project()
                
            else:
                print(f"❌ Error actualizando propiedades del dispositivo {device_id}")
                
        except Exception as e:
            print(f"❌ Error en update_device_properties: {e}")
    
    def open_device_properties_by_id(self, device_id):
        """Abrir propiedades de dispositivo por ID (para uso desde sidebar)"""
        try:
            device = self.device_manager.get_device(device_id)
            if device:
                self.open_device_properties(device)
            else:
                print(f"❌ Dispositivo con ID '{device_id}' no encontrado")
        except Exception as e:
            print(f"❌ Error abriendo propiedades por ID: {e}")
    
    def wheelEvent(self, event):
        """Manejar zoom con rueda del mouse (optimizado)"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
            self.zoom_factor *= zoom_factor
        else:
            zoom_factor = zoom_out_factor  
            self.zoom_factor *= zoom_factor
        
        self.scale(zoom_factor, zoom_factor)
        
        # Throttle updates para mejor rendimiento durante zoom continuo
        if not hasattr(self, '_last_zoom_update') or (
            hasattr(self, '_last_zoom_update') and 
            (event.timestamp() - self._last_zoom_update) > 100
        ):
            # Actualizar cuadrícula después del zoom (throttled)
            self.setup_grid()
            
            # Actualizar posición de etiquetas después del zoom (throttled)
            self.update_axis_labels_position()
            
            self._last_zoom_update = event.timestamp()
        
        # Actualizar info panel (ligero)
        scene_pos = self.mapToScene(event.pos())
        self.update_info_panel(scene_pos.x(), scene_pos.y())
    
    def resizeEvent(self, event):
        """Manejar cambio de tamaño"""
        super().resizeEvent(event)
        self.position_info_panel()
        self.setup_grid()  # Redibujar cuadrícula con nuevo tamaño
        self.update_axis_labels_position()  # Actualizar posición de etiquetas
    
    def paintEvent(self, event):
        """Evento de pintado personalizado (optimizado)"""
        super().paintEvent(event)
        # Eliminar redibujado automático de grilla para mejor rendimiento
        # self.setup_grid()  # Comentado para evitar redibujados excesivos
    
    def refresh_layout(self):
        """Refrescar el layout del canvas después de cambios de configuración"""
        # Reposicionar elementos
        self.position_info_panel()
        self.setup_grid()
        self.update_axis_labels_position()
        
        # Asegurar visibilidad correcta del info panel
        if hasattr(self, 'info_label'):
            if self.info_panel_visible:
                self.info_label.show()
            else:
                self.info_label.hide()
    
    # Métodos públicos para control
    def center_view(self):
        """Centrar vista en el origen (atajo C)"""
        self.centerOn(0, 0)
        self.setup_grid()
        self.update_axis_labels_position()
    
    def reset_view(self):
        """Resetear vista original (atajo R)"""
        self.resetTransform()
        self.zoom_factor = 1.0
        self.centerOn(0, 0)
        self.setup_grid()
        self.update_axis_labels_position()
    
    def toggle_grid_and_origin(self):
        """Método principal para alternar cuadrícula y origen juntos"""
        # Cambiar estado de ambos elementos
        self.grid_visible = not self.grid_visible
        self.origin_visible = self.grid_visible  # Origen siempre sigue a la cuadrícula
        
        # Aplicar cambios
        if self.grid_visible:
            self.setup_grid()
            self.setup_origin()
        else:
            self.clear_grid()
            self.clear_origin()
    
    def toggle_grid(self):
        """Alternar solo cuadrícula (método heredado, redirige al principal)"""
        self.toggle_grid_and_origin()
    
    def toggle_origin(self):
        """Alternar visibilidad del origen"""
        self.origin_visible = not self.origin_visible
        if self.origin_visible:
            self.setup_origin()
            # Mostrar etiquetas overlay
            if hasattr(self, 'x_label_widget'):
                self.x_label_widget.show()
                self.y_label_widget.show()
        else:
            self.clear_origin()
    
    def toggle_sidebar_panel(self):
        """Alternar visibilidad del panel lateral"""
        # Buscar la ventana principal para alternar el panel lateral
        main_window = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'toggle_components'):
                main_window = parent
                break
            parent = parent.parent()
        
        if main_window and hasattr(main_window, 'toggle_components'):
            main_window.toggle_components()
        else:
            print("No se pudo encontrar el método toggle_components en la ventana principal")
    
    # Atajos de teclado (backup - los shortcuts QShortcut tienen prioridad)
    def keyPressEvent(self, event):
        """Manejar atajos de teclado como backup"""
        try:
            # Escape - ocultar vértices y desactivar modo conexión
            if event.key() == Qt.Key_Escape:
                print(f"Bloqueado:")
                self.device_manager.deselect_all()
                
                # Desactivar modo conexión si está activo
                if self.connection_mode:
                    self.set_connection_mode(False)
                    # Notificar al sidebar para que actualice su estado visual
                    self.notify_sidebar_connection_mode_change()
                
                event.accept()
            # Los QShortcut manejan estos, pero mantenemos como backup
            elif event.key() == Qt.Key_C and not (event.modifiers() & Qt.ControlModifier):
                print(f"Centro:")
                self.center_view()
                # Ocultar vértices al centrar (acción no relacionada con dispositivos)
                self.device_manager.deselect_all()
                event.accept()
            elif event.key() == Qt.Key_R and not (event.modifiers() & Qt.ControlModifier):
                print(f"Reset:")
                self.reset_view()
                # Ocultar vértices al resetear (acción no relacionada con dispositivos)
                self.device_manager.deselect_all()
                event.accept()
            elif event.key() == Qt.Key_I and event.modifiers() == Qt.ControlModifier:
                print(f"Reset:")
                self.toggle_info_panel()
                # Ocultar vértices al alternar panel info
                self.device_manager.deselect_all()
                event.accept()
            elif event.key() == Qt.Key_P and event.modifiers() == Qt.ControlModifier:
                print(f"Panel:")
                self.toggle_sidebar_panel()
                # Ocultar vértices al alternar panel lateral
                self.device_manager.deselect_all()
                event.accept()
            elif event.key() == Qt.Key_L and not (event.modifiers() & Qt.ControlModifier):
                self.toggle_connection_mode_shortcut()
                event.accept()
            elif event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                # Eliminar dispositivo seleccionado o conexiones seleccionadas
                deleted_something = False
                
                # Primero intentar eliminar dispositivos
                selected_device = self.device_manager.get_selected_device()
                if selected_device:
                    print(f"Eliminando:")
                    self.device_manager.remove_device(selected_device.id)
                    deleted_something = True
                
                # Luego intentar eliminar conexiones seleccionadas
                selected_connections = self.scene.selectedItems()
                connections_deleted = 0
                for item in selected_connections:
                    if hasattr(item, 'connection'):  # Es un ConnectionGraphicsItem
                        self.connection_manager.remove_connection(item.connection)
                        connections_deleted += 1
                        deleted_something = True
                
                if connections_deleted > 0:
                    print(f"Eliminando:")
                
                if deleted_something:
                    event.accept()
                else:
                    # Si no hay nada que eliminar, ocultar vértices
                    self.device_manager.deselect_all()
                    super().keyPressEvent(event)
            else:
                super().keyPressEvent(event)
                
        except Exception as e:
            print(f"ERROR en keyPressEvent: {e}")
            super().keyPressEvent(event)
    
    # ==========================================
    # DRAG & DROP FUNCTIONALITY
    # ==========================================
    
    def dragEnterEvent(self, event):
        """Manejar entrada de drag"""
        if event.mimeData().hasText():
            # Verificar si el texto contiene datos de dispositivo
            text_data = event.mimeData().text()
            if '|' in text_data:
                device_name, device_type = text_data.split('|', 1)
                if device_type in ['OLT', 'ONU']:
                    event.acceptProposedAction()
                    return
        
        event.ignore()
    
    def dragMoveEvent(self, event):
        """Manejar movimiento durante drag"""
        if event.mimeData().hasText():
            text_data = event.mimeData().text()
            if '|' in text_data:
                device_name, device_type = text_data.split('|', 1)
                if device_type in ['OLT', 'ONU']:
                    event.acceptProposedAction()
                    
                    # Actualizar cursor para indicar que se puede hacer drop
                    self.setCursor(Qt.CrossCursor)
                    return
        
        # Restaurar cursor normal si no se puede hacer drop
        self.setCursor(Qt.ForbiddenCursor)
        event.ignore()
    
    def dragLeaveEvent(self, event):
        """Manejar salida de drag"""
        # Restaurar cursor normal
        self.setCursor(Qt.CrossCursor)
        event.accept()
    
    def dropEvent(self, event):
        """Manejar drop de dispositivo"""
        if event.mimeData().hasText():
            text_data = event.mimeData().text()
            if '|' in text_data:
                try:
                    device_name, device_type = text_data.split('|', 1)
                    if device_type in ['OLT', 'ONU']:
                        # Convertir posición del drop a coordenadas de escena
                        scene_pos = self.mapToScene(event.pos())
                        x = scene_pos.x()
                        y = scene_pos.y()
                        
                        # Ajustar a cuadrícula si está visible
                        if self.grid_visible and self.grid_size > 0:
                            x = round(x / self.grid_size) * self.grid_size
                            y = round(y / self.grid_size) * self.grid_size
                        
                        # Agregar dispositivo usando el device manager
                        device = self.device_manager.add_device(device_type, x, y)
                        
                        if device:
                            print(f"✅ Dispositivo {device_type} agregado en ({x:.1f}, {y:.1f})")
                            # Emitir señal
                            self.device_dropped.emit(device_name, device_type, x, y)
                            event.acceptProposedAction()
                        else:
                            print(f"❌ Error agregando dispositivo {device_type}")
                            event.ignore()
                        
                        # Restaurar cursor
                        self.setCursor(Qt.CrossCursor)
                        return
                        
                except Exception as e:
                    print(f"Error en dropEvent: {e}")
        
        event.ignore()
    
    # ==========================================
    # DEVICE MANAGEMENT METHODS
    # ==========================================
    
    def get_device_manager(self):
        """Obtener gestor de dispositivos"""
        return self.device_manager
    
    def add_device_at_position(self, device_type, x, y, name=None):
        """Agregar dispositivo en posición específica (método público)"""
        return self.device_manager.add_device(device_type, x, y, name)
    
    def remove_device_by_id(self, device_id):
        """Remover dispositivo por ID"""
        return self.device_manager.remove_device(device_id)
    
    def get_all_devices(self):
        """Obtener todos los dispositivos"""
        return self.device_manager.get_all_devices()
    
    def clear_all_devices(self):
        """Limpiar todos los dispositivos"""
        self.device_manager.clear_all_devices()
    
    def snap_to_grid_position(self, x, y):
        """Ajustar coordenadas a la cuadrícula"""
        if self.grid_visible and self.grid_size > 0:
            snapped_x = round(x / self.grid_size) * self.grid_size
            snapped_y = round(y / self.grid_size) * self.grid_size
            return snapped_x, snapped_y
        return x, y
    
    # ==========================================
    # DEVICE RESIZE METHODS
    # ==========================================
    
    def increase_selected_device_size(self):
        """Aumentar tamaño del dispositivo seleccionado (tecla +)"""
        selected_device = self.device_manager.get_selected_device()
        if selected_device:
            current_size = selected_device.icon_size
            new_size = min(128, current_size + 8)  # Incremento de 8px, máximo 128px
            
            if new_size != current_size:
                selected_device.set_icon_size(new_size)
                print(f"Redimensionado:")
        else:
            print("Selecciona un dispositivo para redimensionar")
    
    def decrease_selected_device_size(self):
        """Disminuir tamaño del dispositivo seleccionado (tecla -)"""
        selected_device = self.device_manager.get_selected_device()
        if selected_device:
            current_size = selected_device.icon_size
            new_size = max(32, current_size - 8)  # Decremento de 8px, mínimo 32px
            
            if new_size != current_size:
                selected_device.set_icon_size(new_size)
                print(f"Redimensionado:")
        else:
            print("Selecciona un dispositivo para redimensionar")
    
    # ===== MÉTODOS DE GESTIÓN DE PROYECTOS =====
    
    def setup_project_manager(self):
        """Configurar el gestor de proyectos"""
        # Conectar señales para auto-save
        self.device_manager.devices_changed.connect(self.auto_save_project)
        self.connection_manager.connections_changed.connect(self.auto_save_project)
        
        # Conectar señal de carga de proyecto
        self.project_manager.project_loaded.connect(self.load_project_data)
        
        # NO cargar proyecto previo automáticamente
        # self.project_manager.load_auto_save()
        
        print("Gestor de proyectos inicializado (sin carga automática)")
    
    def auto_save_project(self):
        """Guardar automáticamente el estado actual del proyecto"""
        try:
            # Obtener datos actuales
            devices_data = self.device_manager.export_devices_data()
            connections_data = self.connection_manager.export_connections_data()
            canvas_data = {
                "zoom": self.zoom_factor,
                "grid_visible": self.grid_visible,
                "grid_size": self.grid_size
            }
            
            # Actualizar proyecto
            self.project_manager.update_project_data(devices_data, connections_data, canvas_data)
            
        except Exception as e:
            print(f"Error en auto-save del proyecto: {e}")
    
    def load_project_data(self, project_data: dict):
        """Cargar datos del proyecto en el canvas - solo dispositivos y conexiones"""
        try:
            print(f"Cargando:")
            
            # Limpiar canvas actual
            self.clear_canvas()
            
            # Cargar dispositivos
            devices_data = project_data.get("devices", {})
            if devices_data:
                self.device_manager.import_devices_data(devices_data)
                print(f"✅ Cargados {len(devices_data)} dispositivos")
            
            # Cargar conexiones
            connections_data = project_data.get("connections", {})
            if connections_data:
                self.connection_manager.load_from_data(connections_data)
                print(f"✅ Cargadas {len(connections_data)} conexiones")
            
            # Actualizar vista
            self.update()
            self.update_device_info()
            
            print("✅ Proyecto cargado exitosamente")
            
        except Exception as e:
            print(f"❌ Error cargando proyecto: {e}")
    
    def clear_canvas(self):
        """Limpiar completamente el canvas"""
        self.device_manager.clear_all_devices()
        self.connection_manager.cleanup()
        self.setup_grid()
    
    def has_unsaved_work(self) -> bool:
        """Verificar si hay trabajo sin guardar"""
        device_count = len(self.device_manager.devices)
        connection_count = len(self.connection_manager.connections)
        return device_count > 0 or connection_count > 0
    
    def save_project_as(self, file_path: str) -> bool:
        """Guardar proyecto en ruta específica"""
        return self.project_manager.save_as(file_path)
    
    def load_project_file(self, file_path: str) -> bool:
        """Cargar proyecto desde archivo"""
        return self.project_manager.load_project(file_path)
    
    def get_project_info(self) -> dict:
        """Obtener información del proyecto actual"""
        return self.project_manager.get_project_info()