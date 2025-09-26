from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QLinearGradient
import os

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Crear un pixmap más grande para destacar el icono
        pixmap = QPixmap(800, 400)  # Más grande para el icono
        pixmap.fill(QColor(43, 43, 43, 204))  # Fondo #2b2b2b con 80% transparencia
        
        super().__init__(pixmap)
        
        # Configuración de la ventana
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Variables para la animación
        self.opacity_effect = 0.0
        self.scale_factor = 1.0  # Sin animación de zoom
        
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
        self.icon_path = self.get_resource_path('resources/icons/app_icon_512x512.png')
        
    def paintEvent(self, event):
        """Dibujar el contenido del splash screen"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Fondo con el color especificado y transparencia
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(43, 43, 43, 204))  # #2b2b2b con 80% transparencia
        gradient.setColorAt(1, QColor(43, 43, 43, 180))  # Ligeramente más transparente abajo
        painter.fillRect(self.rect(), gradient)
        
        # Dibujar el icono si existe (mucho más grande y a la izquierda)
        if os.path.exists(self.icon_path):
            icon_pixmap = QPixmap(self.icon_path)
            
            # Icono aún más grande
            scaled_size = 260  # Aún más grande (antes 220)
            icon_scaled = icon_pixmap.scaled(
                scaled_size, scaled_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Posicionar el icono a la izquierda
            icon_x = 40  # Reducir margen para dar más espacio al icono más grande
            icon_y = (self.height() - icon_scaled.height()) // 2
            
            painter.drawPixmap(icon_x, icon_y, icon_scaled)
        
        # Dibujar el título principal con el color magenta especificado
        painter.setPen(QColor(226, 8, 215))  # Color #e208d7 especificado
        title_font = QFont("Segoe UI", 40, QFont.Bold)  # Más grande y moderna
        painter.setFont(title_font)
        
        # Posicionar texto a la derecha del icono más grande
        text_start_x = 340  # Más espacio para el icono aún más grande
        
        title_text = "PonLab"
        title_rect = painter.fontMetrics().boundingRect(title_text)
        title_x = text_start_x
        title_y = (self.height() - 40) // 2  # Centrado verticalmente
        
        painter.drawText(title_x, title_y, title_text)
        
        # Dibujar el subtítulo "simulator" en la misma línea
        painter.setPen(QColor(180, 180, 180))  # Gris claro para contraste
        subtitle_font = QFont("Segoe UI", 30, QFont.Normal)  # Proporcionalmente más grande
        painter.setFont(subtitle_font)
        
        # Calcular posición después de "PonLab"
        subtitle_text = "simulator"
        subtitle_x = title_x + title_rect.width() + 15  # Espacio
        subtitle_y = title_y
        
        painter.drawText(subtitle_x, subtitle_y, subtitle_text)
        
        # Dibujar descripción debajo del título principal
        painter.setPen(QColor(160, 160, 160))
        desc_font = QFont("Segoe UI", 14)  # Más grande
        painter.setFont(desc_font)
        
        desc_text = "Simulador Redes de Ópticas Pasivas"
        desc_x = text_start_x
        desc_y = title_y + 60  # Debajo del título
        
        painter.drawText(desc_x, desc_y, desc_text)
        
        # Dibujar versión
        painter.setPen(QColor(120, 120, 120))
        version_font = QFont("Segoe UI", 12)
        painter.setFont(version_font)
        
        version_text = "Versión 2.0.0"
        version_x = text_start_x
        version_y = desc_y + 30
        
        painter.drawText(version_x, version_y, version_text)
        
        # Barra de progreso con el color magenta especificado
        progress_width = 280  # Más ancha
        progress_height = 4   # Más gruesa
        progress_x = text_start_x
        progress_y = version_y + 30
        
        # Fondo de la barra más sutil
        painter.fillRect(progress_x, progress_y, progress_width, progress_height, QColor(80, 80, 80))
        
        # Progreso animado con el mismo color magenta del título
        progress_fill = int(progress_width * self.opacity_effect)
        painter.fillRect(progress_x, progress_y, progress_fill, progress_height, QColor(226, 8, 215))  # #e208d7
    
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
