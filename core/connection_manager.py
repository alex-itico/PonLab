"""
Gestor de conexiones entre dispositivos
"""

from PyQt5.QtWidgets import QMessageBox
from typing import List, Optional
from .connection import Connection
from .device import Device


class ConnectionManager:
    """Gestor principal de todas las conexiones entre dispositivos"""
    
    def __init__(self, canvas=None):
        """
        Inicializar el gestor de conexiones
        
        Args:
            canvas: Referencia al canvas para agregar/remover items gráficos
        """
        self.canvas = canvas
        self.connections: List[Connection] = []
        self.selected_connections: List[Connection] = []
        
    def set_canvas(self, canvas):
        """Establecer la referencia al canvas"""
        self.canvas = canvas
    
    def can_connect(self, device_a: Device, device_b: Device) -> tuple[bool, str]:
        """
        Verificar si dos dispositivos pueden conectarse
        
        Returns:
            tuple: (puede_conectarse, mensaje_error)
        """
        # Un dispositivo no puede conectarse a sí mismo
        if device_a == device_b:
            return False, "Un dispositivo no puede conectarse a sí mismo"
        
        # Verificar si ya existe una conexión entre estos dispositivos
        if self.get_connection_between(device_a, device_b):
            return False, f"Ya existe una conexión entre {device_a.name} y {device_b.name}"
        
        return True, ""
    
    def create_connection(self, device_a: Device, device_b: Device) -> Optional[Connection]:
        """
        Crear una nueva conexión entre dos dispositivos
        
        Returns:
            Connection creada o None si no se pudo crear
        """
        can_connect, error_message = self.can_connect(device_a, device_b)
        
        if not can_connect:
            # Mostrar mensaje de error
            self.show_connection_error(error_message)
            return None
        
        # Crear la conexión
        connection = Connection(device_a, device_b)
        
        # Crear el item gráfico
        graphics_item = connection.create_graphics_item()
        
        # Inicializar el tema de la nueva conexión si el canvas está disponible
        if self.canvas and hasattr(self.canvas, 'dark_theme'):
            graphics_item.update_theme_colors(self.canvas.dark_theme)
        
        # Agregar al canvas si está disponible
        if self.canvas:
            self.canvas.scene.addItem(graphics_item)
        
        # Agregar a la lista de conexiones
        self.connections.append(connection)
        
        print(f"✅ Conexión creada: {device_a.name} <-> {device_b.name}")
        return connection
    
    def remove_connection(self, connection: Connection):
        """Eliminar una conexión específica"""
        if connection in self.connections:
            # Remover del canvas
            if connection.graphics_item and self.canvas:
                self.canvas.scene.removeItem(connection.graphics_item)
            
            # Remover de las listas
            self.connections.remove(connection)
            if connection in self.selected_connections:
                self.selected_connections.remove(connection)
            
            print(f"🗑️ Conexión eliminada: {connection}")
    
    def remove_connections_for_device(self, device: Device):
        """Eliminar todas las conexiones que involucren un dispositivo específico"""
        connections_to_remove = []
        
        for connection in self.connections:
            if connection.contains_device(device):
                connections_to_remove.append(connection)
        
        for connection in connections_to_remove:
            self.remove_connection(connection)
            print(f"🔗💥 Conexión eliminada por borrar dispositivo: {connection}")
    
    def get_connection_between(self, device_a: Device, device_b: Device) -> Optional[Connection]:
        """Obtener la conexión existente entre dos dispositivos (si existe)"""
        for connection in self.connections:
            if ((connection.device_a == device_a and connection.device_b == device_b) or 
                (connection.device_a == device_b and connection.device_b == device_a)):
                return connection
        return None
    
    def get_connections_for_device(self, device: Device) -> List[Connection]:
        """Obtener todas las conexiones que involucren un dispositivo específico"""
        return [conn for conn in self.connections if conn.contains_device(device)]
    
    def update_connections_positions(self):
        """Actualizar las posiciones de todas las líneas de conexión"""
        for connection in self.connections:
            if connection.graphics_item:
                connection.graphics_item.update_line()
    
    def update_theme_colors(self, dark_theme):
        """Actualizar los colores de las conexiones según el tema"""
        for connection in self.connections:
            if connection.graphics_item:
                connection.graphics_item.update_theme_colors(dark_theme)
    
    def select_connection(self, connection: Connection):
        """Seleccionar una conexión específica"""
        if connection not in self.selected_connections:
            self.selected_connections.append(connection)
            connection.set_selected(True)
    
    def deselect_connection(self, connection: Connection):
        """Deseleccionar una conexión específica"""
        if connection in self.selected_connections:
            self.selected_connections.remove(connection)
            connection.set_selected(False)
    
    def deselect_all_connections(self):
        """Deseleccionar todas las conexiones"""
        for connection in self.selected_connections[:]:  # Copia de la lista
            self.deselect_connection(connection)
    
    def delete_selected_connections(self):
        """Eliminar todas las conexiones seleccionadas"""
        connections_to_delete = self.selected_connections[:]
        
        for connection in connections_to_delete:
            self.remove_connection(connection)
        
        print(f"🗑️ {len(connections_to_delete)} conexiones eliminadas")
    
    def show_connection_error(self, message: str):
        """Mostrar mensaje de error al usuario"""
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("Error de Conexión")
        msg_box.setText(message)
        msg_box.exec_()
    
    def get_connections_count(self) -> int:
        """Obtener el número total de conexiones"""
        return len(self.connections)
    
    def cleanup(self):
        """Limpiar todos los recursos del gestor"""
        # Remover todos los items gráficos del canvas
        if self.canvas:
            for connection in self.connections:
                if connection.graphics_item:
                    self.canvas.scene.removeItem(connection.graphics_item)
        
        # Limpiar listas
        self.connections.clear()
        self.selected_connections.clear()
        
        print("🧹 ConnectionManager limpiado")
    
    def get_connection_info(self) -> dict:
        """Obtener información resumida de las conexiones"""
        return {
            'total_connections': len(self.connections),
            'selected_connections': len(self.selected_connections),
            'connections': [str(conn) for conn in self.connections]
        }
