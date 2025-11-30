from PyQt5.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QFont, QPainter, QColor, QLinearGradient
import os

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Create a larger pixmap to highlight the icon
        pixmap = QPixmap(800, 400)  # Larger for the icon
        pixmap.fill(QColor(43, 43, 43, 204))  # Background #2b2b2b with 80% transparency
        
        super().__init__(pixmap)
        
        # Window configuration
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Variables for animation
        self.opacity_effect = 0.0
        self.scale_factor = 1.0  # No zoom animation
        
        # Timer to control duration
        self.timer = QTimer()
        self.timer.timeout.connect(self.close_splash)
        
        # Opacity animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(800)  # 800ms to appear
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutCubic)
        
        self.setup_ui()
    
    def get_resource_path(self, relative_path):
        """Get the absolute path of the resource"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)
    
    def setup_ui(self):
        """Configure the splash screen interface"""
        # Load the icon
        self.icon_path = self.get_resource_path('resources/icons/app_icon_512x512.png')
        
    def paintEvent(self, event):
        """Draw the splash screen content"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Background with specified color and transparency
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(43, 43, 43, 204))  # #2b2b2b with 80% transparency
        gradient.setColorAt(1, QColor(43, 43, 43, 180))  # Slightly more transparent at the bottom
        painter.fillRect(self.rect(), gradient)
        
        # Draw the icon if it exists (much larger and to the left)
        if os.path.exists(self.icon_path):
            icon_pixmap = QPixmap(self.icon_path)
            
            # Even larger icon
            scaled_size = 260  # Even larger (before 220)
            icon_scaled = icon_pixmap.scaled(
                scaled_size, scaled_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            
            # Position the icon to the left
            icon_x = 40  # Reduce margin to give more space to the larger icon
            icon_y = (self.height() - icon_scaled.height()) // 2
            
            painter.drawPixmap(icon_x, icon_y, icon_scaled)
        
        # Draw the main title with the specified magenta color
        painter.setPen(QColor(226, 8, 215))  # Specified color #e208d7
        title_font = QFont("Segoe UI", 40, QFont.Bold)  # Larger and modern
        painter.setFont(title_font)
        
        # Position text to the right of the larger icon
        text_start_x = 340  # More space for the even larger icon
        
        title_text = "PonLab"
        title_rect = painter.fontMetrics().boundingRect(title_text)
        title_x = text_start_x
        title_y = (self.height() - 40) // 2  # Vertically centered
        
        painter.drawText(title_x, title_y, title_text)
        
        # Draw the "simulator" subtitle on the same line
        painter.setPen(QColor(180, 180, 180))  # Light gray for contrast
        subtitle_font = QFont("Segoe UI", 30, QFont.Normal)  # Proportionally larger
        painter.setFont(subtitle_font)
        
        # Calculate position after "PonLab"
        subtitle_text = "simulator"
        subtitle_x = title_x + title_rect.width() + 15  # Space
        subtitle_y = title_y
        
        painter.drawText(subtitle_x, subtitle_y, subtitle_text)
        
        # Draw description below the main title
        painter.setPen(QColor(160, 160, 160))
        desc_font = QFont("Segoe UI", 14)  # Larger
        painter.setFont(desc_font)
        
        desc_text = "Simulador Redes de Ópticas Pasivas"
        desc_x = text_start_x
        desc_y = title_y + 60  # Below the title
        
        painter.drawText(desc_x, desc_y, desc_text)
        
        # Draw version
        painter.setPen(QColor(120, 120, 120))
        version_font = QFont("Segoe UI", 12)
        painter.setFont(version_font)
        
        version_text = "Versión 2.1.0"
        version_x = text_start_x
        version_y = desc_y + 30
        
        painter.drawText(version_x, version_y, version_text)
        
        # Progress bar with the specified magenta color
        progress_width = 280  # Wider
        progress_height = 4   # Thicker
        progress_x = text_start_x
        progress_y = version_y + 30
        
        # More subtle bar background
        painter.fillRect(progress_x, progress_y, progress_width, progress_height, QColor(80, 80, 80))
        
        # Animated progress with the same magenta color as the title
        progress_fill = int(progress_width * self.opacity_effect)
        painter.fillRect(progress_x, progress_y, progress_fill, progress_height, QColor(226, 8, 215))  # #e208d7
    
    def show_splash(self, duration=2000):
        """Show the splash screen for the specified duration"""
        self.show()
        
        # Start appearance animation
        self.fade_animation.finished.connect(self.start_scale_animation)
        self.fade_animation.start()
        
        # Configure timer to close
        self.timer.start(duration)
    
    def start_scale_animation(self):
        """Start the icon scale animation"""
        # Create a timer to animate scale and progress
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(30)  # 30ms per frame
        
        self.animation_progress = 0.0
    
    def update_animation(self):
        """Update the animation frame by frame"""
        self.animation_progress += 0.02
        
        if self.animation_progress >= 1.0:
            self.animation_progress = 1.0
            self.animation_timer.stop()
        
        # Animate the icon scale (from 0.8 to 1.2 and back to 1.0)
        if self.animation_progress <= 0.5:
            self.scale_factor = 0.8 + (0.4 * self.animation_progress * 2)  # 0.8 -> 1.2
        else:
            self.scale_factor = 1.2 - (0.2 * (self.animation_progress - 0.5) * 2)  # 1.2 -> 1.0
        
        # Animate the progress
        self.opacity_effect = self.animation_progress
        
        self.update()
    
    def close_splash(self):
        """Close the splash screen with animation"""
        self.timer.stop()
        
        # Disappearance animation
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(500)  # 500ms to disappear
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.InOutCubic)
        fade_out.finished.connect(self.hide)
        fade_out.start()
        
        self.fade_out_animation = fade_out  # Keep reference
