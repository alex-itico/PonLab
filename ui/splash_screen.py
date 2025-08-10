from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QLinearGradient
import os

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Crear un pixmap en blanco para el splash screen
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor(45, 45, 45))  # Fondo gris oscuro
        
        super().__init__(pixmap)
        
        # Configuración de la ventana
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Variables para la animación
        self.opacity_effect = 0.0
        self.scale_factor = 0.8
        
        # Timer para controlar la duración
        self.timer = QTimer()
        self.timer.timeout.connect(self.close_splash)
        
        # Animación de opacidad
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(800)  # 800ms para aparecer
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        self.setup_ui()
    
    def get_resource_path(self, relative_path):
        """Obtener la ruta absoluta del recurso"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    
    def setup_ui(self):
        """Configurar la interfaz del splash screen"""
        # Cargar el icono
        self.icon_path = self.get_resource_path('resources/icons/app_icon_128x128.png')
        
    def paintEvent(self, event):
        """Dibujar el contenido del splash screen"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Fondo con gradiente
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(60, 60, 60))
        gradient.setColorAt(1, QColor(30, 30, 30))
        painter.fillRect(self.rect(), gradient)
        
        # Dibujar el icono si existe
        if os.path.exists(self.icon_path):
            icon_pixmap = QPixmap(self.icon_path)
            
            # Escalar el icono con la animación (tamaño aumentado)
            scaled_size = int(160 * self.scale_factor)  # Aumentado de 128 a 160
            icon_scaled = icon_pixmap.scaled(
                scaled_size, scaled_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Centrar el icono
            icon_x = (self.width() - icon_scaled.width()) // 2
            icon_y = (self.height() - icon_scaled.height()) // 2 - 50
            
            painter.drawPixmap(icon_x, icon_y, icon_scaled)
        
        # Dibujar el título
        painter.setPen(QColor(255, 255, 255))
        title_font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(title_font)
        
        title_rect = painter.fontMetrics().boundingRect("Simulador Redes de Acceso Óptica")
        title_x = (self.width() - title_rect.width()) // 2
        title_y = (self.height() + title_rect.height()) // 2 + 40
        
        painter.drawText(title_x, title_y, "Simulador Redes de Acceso Óptica")
        
        # Dibujar el subtítulo
        painter.setPen(QColor(200, 200, 200))
        subtitle_font = QFont("Arial", 12)
        painter.setFont(subtitle_font)
        
        subtitle_rect = painter.fontMetrics().boundingRect("Redes de Acceso Óptica")
        subtitle_x = (self.width() - subtitle_rect.width()) // 2
        subtitle_y = title_y + 35
        
        painter.drawText(subtitle_x, subtitle_y, "Redes de Acceso Óptica")
        
        # Dibujar versión
        painter.setPen(QColor(150, 150, 150))
        version_font = QFont("Arial", 10)
        painter.setFont(version_font)
        
        version_text = "Versión 1.0"
        version_rect = painter.fontMetrics().boundingRect(version_text)
        version_x = (self.width() - version_rect.width()) // 2
        version_y = subtitle_y + 30
        
        painter.drawText(version_x, version_y, version_text)
        
        # Barra de progreso simple
        progress_width = 200
        progress_height = 4
        progress_x = (self.width() - progress_width) // 2
        progress_y = version_y + 40
        
        # Fondo de la barra
        painter.fillRect(progress_x, progress_y, progress_width, progress_height, QColor(100, 100, 100))
        
        # Progreso animado
        progress_fill = int(progress_width * self.opacity_effect)
        painter.fillRect(progress_x, progress_y, progress_fill, progress_height, QColor(0, 150, 255))
    
    def show_splash(self, duration=2000):
        """Mostrar el splash screen por la duración especificada"""
        self.show()
        
        # Iniciar animación de aparición
        self.fade_animation.finished.connect(self.start_scale_animation)
        self.fade_animation.start()
        
        # Configurar timer para cerrar
        self.timer.start(duration)
    
    def start_scale_animation(self):
        """Iniciar la animación de escala del icono"""
        # Crear un timer para animar la escala y el progreso
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(30)  # 30ms por frame
        
        self.animation_progress = 0.0
    
    def update_animation(self):
        """Actualizar la animación frame por frame"""
        self.animation_progress += 0.02
        
        if self.animation_progress >= 1.0:
            self.animation_progress = 1.0
            self.animation_timer.stop()
        
        # Animar la escala del icono (de 0.8 a 1.2 y de vuelta a 1.0)
        if self.animation_progress <= 0.5:
            self.scale_factor = 0.8 + (0.4 * self.animation_progress * 2)  # 0.8 -> 1.2
        else:
            self.scale_factor = 1.2 - (0.2 * (self.animation_progress - 0.5) * 2)  # 1.2 -> 1.0
        
        # Animar el progreso
        self.opacity_effect = self.animation_progress
        
        self.update()
    
    def close_splash(self):
        """Cerrar el splash screen con animación"""
        self.timer.stop()
        
        # Animación de desaparición
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(500)  # 500ms para desaparecer
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InOutCubic)
        fade_out.finished.connect(self.hide)
        fade_out.start()
        
        self.fade_out_animation = fade_out  # Mantener referencia
