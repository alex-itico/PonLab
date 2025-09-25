"""
Gestor de conexiones entre dispositivos
"""

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
from typing import List, Optional
from .connection import Connection
from ..devices.device import Device


class ConnectionManager(QObject):
    """Gestor principal de todas las conexiones entre dispositivos"""
    
    # Señales
    connections_changed = pyqtSignal()  # Emitida cuando cambian las conexiones
    
    def __init__(self, canvas=None):
        """
        Inicializar el gestor de conexiones
        
        Args:
            canvas: Referencia al canvas para agregar/remover items gráficos
        """
        super().__init__()
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
        
        # ⚠️ VALIDACIÓN PON: Las ONUs solo pueden conectarse a OLTs
        if device_a.device_type == "ONU" and device_b.device_type == "ONU":
            return False, (
                "⚠️ Conexión no permitida: ONU ↔ ONU\n\n"
                "Las ONUs únicamente pueden conectarse a una OLT.\n"
                f"• {device_a.name} es una ONU\n"
                f"• {device_b.name} es una ONU\n\n"
                "Para conectar estos dispositivos necesitas:\n"
                "1. Un dispositivo OLT en la topología\n"
                "2. Conectar cada ONU al OLT por separado"
            )
        
        # ℹ️ VALIDACIÓN PON: Conexiones entre OLTs no son típicas en PON
        if device_a.device_type == "OLT" and device_b.device_type == "OLT":
            return False, (
                "ℹ️ Conexión no recomendada: OLT ↔ OLT\n\n"
                "Las conexiones entre OLTs no son típicas en redes PON.\n"
                f"• {device_a.name} es una OLT\n"
                f"• {device_b.name} es una OLT\n\n"
                "En una topología PON estándar:\n"
                "• Cada OLT gestiona sus propias ONUs\n"
                "• Las ONUs se conectan únicamente a su OLT"
            )
        
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
        
        # Emitir señal de cambio
        self.connections_changed.emit()
        
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
            
            # Emitir señal de cambio
            self.connections_changed.emit()
            
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
        
        # Configurar el tipo de mensaje según el contenido
        if "⚠️" in message and "ONU ↔ ONU" in message:
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("⚠️ Conexión PON no permitida")
        elif "ℹ️" in message and "OLT ↔ OLT" in message:
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("ℹ️ Conexión PON no recomendada")
        else:
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Error de Conexión")
        
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
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
        
        # Emitir señal de cambio
        self.connections_changed.emit()
        
        print("🧹 ConnectionManager limpiado")
    
    def get_connection_info(self) -> dict:
        """Obtener información resumida de las conexiones"""
        return {
            'total_connections': len(self.connections),
            'selected_connections': len(self.selected_connections),
            'connections': [str(conn) for conn in self.connections]
        }
    
    def export_connections_data(self) -> dict:
        """Exportar datos de conexiones para guardar en archivo"""
        connections_data = {}
        
        for i, connection in enumerate(self.connections):
            connection_id = f"connection_{i+1}"
            connections_data[connection_id] = {
                "device_a_id": connection.device_a.id,
                "device_b_id": connection.device_b.id,
                "device_a_name": connection.device_a.name,
                "device_b_name": connection.device_b.name,
                "distance": connection.calculate_distance()
            }
        
        return connections_data
    
    def load_from_data(self, connections_data: dict):
        """Cargar conexiones desde datos guardados"""
        try:
            # Limpiar conexiones existentes
            self.cleanup()
            
            if not self.canvas or not hasattr(self.canvas, 'device_manager'):
                print("❌ Canvas o device_manager no disponible para cargar conexiones")
                return
            
            device_manager = self.canvas.device_manager
            
            for connection_id, conn_data in connections_data.items():
                # Buscar dispositivos por ID
                device_a_id = conn_data.get("device_a_id")
                device_b_id = conn_data.get("device_b_id")
                
                device_a = device_manager.get_device(device_a_id)
                device_b = device_manager.get_device(device_b_id)
                
                if device_a and device_b:
                    # Crear conexión
                    connection = self.create_connection(device_a, device_b)
                    if connection:
                        print(f"✅ Conexión restaurada: {device_a.name} ↔ {device_b.name}")
                else:
                    print(f"⚠️ No se pudieron encontrar dispositivos para conexión: {connection_id}")
            
            print(f"📡 Cargadas {len(self.connections)} conexiones")
            
        except Exception as e:
            print(f"❌ Error cargando conexiones: {e}")
